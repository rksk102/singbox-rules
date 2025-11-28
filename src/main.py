import os
import json
import shutil
import tempfile
import re
import sys
import time
import subprocess
from datetime import timedelta
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Set, Optional, Tuple

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
except ImportError:
    print("Error: Please install rich (pip install rich)")
    sys.exit(1)

console = Console(record=True)
ROOT_DIR = Path.cwd()
CONFIG_FILE = ROOT_DIR / "repos.json"
DIR_TXT = ROOT_DIR / "rules-txt"
DIR_JSON = ROOT_DIR / "rules-json"
DIR_SRS = ROOT_DIR / "rules-srs"
MAX_WORKERS = 4

FLATTEN_TARGETS = {"rulesets", "ruleset"}

REGEX_IP = re.compile(r'^(?:(?:[0-9]{1,3}\.){3}[0-9]{1,3}(?:/\d+)?)|(?:.*:.*)$')

class WorkflowStats:
    def __init__(self):
        self.start_time = time.time()
        self.sync_success = 0
        self.sync_total = 0
        self.compile_success = 0
        self.compile_fail = 0
        self.total_rules = 0
        self.details: List[Tuple[str, str, int]] = [] 
        self.status = "✅ 成功"

    @property
    def duration(self) -> str:
        return str(timedelta(seconds=int(time.time() - self.start_time)))

stats = WorkflowStats()

def write_github_summary():
    if "GITHUB_STEP_SUMMARY" not in os.environ: return
    sorted_details = sorted(stats.details, key=lambda x: x[2], reverse=True)[:20]
    rows = []
    for name, rtype, count in sorted_details:
        icon = "🌐" if rtype == "domain_suffix" else "📡"
        rows.append(f"| {name} | {icon} `{rtype}` | {count:,} |")
    table_content = "\n".join(rows)
    
    md_content = f"""
# 🚀 构建报告: {stats.status}

| 指标 | 结果 |
| :--- | :--- |
| ⏱️ 耗时 | {stats.duration} |
| 🔄 同步仓库 | {stats.sync_success} / {stats.sync_total} |
| 🔨 编译文件 | {stats.compile_success} (失败: {stats.compile_fail}) |
| 📊 规则总条数 | **{stats.total_rules:,}** |

### 📂 Top 20 文件
| 文件名 | 类型 | 规则数 |
| :--- | :--- | :---: |
{table_content}
"""
    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f: f.write(md_content)

def handle_error(phase: str, error_msg: Exception | str):
    stats.status = f"❌ 失败于 {phase}"
    console.print(f"\n[bold red]⛔ 致命错误 - {phase}[/bold red]")
    console.print(Panel(str(error_msg), style="red"))
    write_github_summary()
    sys.exit(1)

def flatten_directory(target_dir: Path):
    """暴力去除多余层级 (如 rulesets)"""
    for item in list(target_dir.iterdir()): 
        if item.is_dir() and item.name.lower() in FLATTEN_TARGETS:
            for sub_item in item.iterdir():
                dst_path = target_dir / sub_item.name
                if dst_path.exists():
                    if dst_path.is_dir(): shutil.rmtree(dst_path)
                    else: dst_path.unlink()
                shutil.move(str(sub_item), str(dst_path))
                dst_path.touch()
            shutil.rmtree(item)

def git_sparse_clone(url: str, remote_tgt: str, temp_dir: str):
    try:
        common_args = {"check": True, "stdout": subprocess.DEVNULL, "stderr": subprocess.PIPE}
        subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", url, temp_dir], **common_args)
        subprocess.run(["git", "sparse-checkout", "set", remote_tgt], cwd=temp_dir, **common_args)
        subprocess.run(["git", "checkout"], cwd=temp_dir, **common_args)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"Git Error: {e.stderr.decode().strip()}")

def init_workspace():
    console.rule("[bold blue]阶段 1: 暴力清理旧文件[/bold blue]")
    dirs = [DIR_TXT, DIR_JSON, DIR_SRS]
    for d in dirs:
        if d.exists():
            console.print(f"[dim]  🔥 正在焚毁旧目录用: {d.name}...[/dim]")
            shutil.rmtree(d)
        d.mkdir(parents=True)
        console.print(f"[green]  ✅ 已重建空目录: {d.name}[/green]")
    print()

def run_sync_phase():
    console.rule("[bold blue]阶段 2: 同步远程源[/bold blue]")
    if not CONFIG_FILE.exists(): handle_error("配置读取", f"找不到 {CONFIG_FILE}")

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            repo_list = json.load(f)
            stats.sync_total = len(repo_list)
    except Exception as e:
        handle_error("配置解析", e)

    sync_table = Table(box=box.SIMPLE_HEAD)
    sync_table.add_column("仓库", style="cyan")
    sync_table.add_column("状态", justify="right")

    for item in repo_list:
        name = item.get('name', 'Unknown')
        with console.status(f"[bold yellow]⬇️ 正在拉取: {name}...[/bold yellow]"):
            try:
                url = item.get('url')
                remote_tgt = item.get('remote_path')
                local_sub = item.get('local_subdir', '') 
                dest_dir = DIR_TXT / local_sub
                dest_dir.mkdir(parents=True, exist_ok=True)

                with tempfile.TemporaryDirectory() as temp_dir:
                    git_sparse_clone(url, remote_tgt, temp_dir)
                    full_remote_path = Path(temp_dir) / remote_tgt

                    if full_remote_path.is_dir():
                        for src_file in full_remote_path.rglob("*"):
                            if src_file.is_file():
                                rel = src_file.relative_to(full_remote_path)
                                dst = dest_dir / rel
                                dst.parent.mkdir(parents=True, exist_ok=True)
                                shutil.copy2(src_file, dst)
                                dst.touch()
                    elif full_remote_path.is_file():
                        shutil.copy2(full_remote_path, dest_dir)
                        (dest_dir / full_remote_path.name).touch()
                    else:
                        raise FileNotFoundError(f"远程路径不存在: {remote_tgt}")
                
                flatten_directory(dest_dir)
                stats.sync_success += 1
                sync_table.add_row(name, "[green]OK[/green]")
            except Exception as e:
                sync_table.add_row(name, "[red]FAIL[/red]")
                handle_error(f"同步 [{name}]", e)
    console.print(sync_table)

def compile_file_worker(args) -> Optional[Tuple[str, str, int]]:
    file_path, rel_path = args
    if not file_path.name.lower().endswith(('.txt', '.list', '.yaml', '.conf', '.json', '')):
        return None

    rules: Set[str] = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                c = line.split('#')[0].split('//')[0].strip()
                if not c or c.startswith("payload:") or "repo" in c: continue
                c = c.replace("'", "").replace('"', "").replace(",", "").lstrip("-").strip()
                if c: rules.add(c)
    except:
        return None
    
    if not rules: return None
    rules_list = list(rules)

    fname = file_path.name.lower()
    if "ip" in fname and "domain" not in fname: rtype = "ip_cidr"
    elif "domain" in fname or "site" in fname: rtype = "domain_suffix"
    else:
        sample = rules_list[:10]
        ip_cnt = sum(1 for x in sample if re.match(r'^\d+\.|:', x))
        rtype = "ip_cidr" if ip_cnt > len(sample)/2 else "domain_suffix"

    final_rules = []
    if rtype == "ip_cidr":
        for r in rules_list:
            if REGEX_IP.match(r) and "inverse" not in r and "arpa" not in r:
                final_rules.append(r)
    else:
        final_rules = rules_list

    final_rules.sort()

    if not final_rules: return None

    path_parts = rel_path.parts
    if path_parts[0] in FLATTEN_TARGETS:
        clean_rel_path = Path(*path_parts[1:]) 
    else:
        clean_rel_path = rel_path

    out_dir_json = DIR_JSON / clean_rel_path.parent
    out_dir_srs = DIR_SRS / clean_rel_path.parent
    out_dir_json.mkdir(parents=True, exist_ok=True)
    out_dir_srs.mkdir(parents=True, exist_ok=True)

    json_path = out_dir_json / f"{file_path.stem}.json"
    srs_path = out_dir_srs / f"{file_path.stem}.srs"
    
    data = {"version": 1, "rules": [{rtype: final_rules}]}
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    res = subprocess.run(["sing-box", "rule-set", "compile", str(json_path), "-o", str(srs_path)],
                         capture_output=True, text=True)
    
    if res.returncode != 0:
        raise RuntimeError(f"{file_path.name}: {res.stderr.strip()}")

    json_path.touch()
    srs_path.touch()

    return (file_path.name, rtype, len(final_rules))

def run_build_phase():
    console.rule("[bold blue]阶段 3: 编译 (.srs)[/bold blue]")
    files = [(p, p.relative_to(DIR_TXT)) for p in DIR_TXT.rglob("*") if p.is_file()]
    if not files:
        console.print("[yellow]⚠️ 没有文件需要编译[/yellow]")
        return

    with Progress(
        SpinnerColumn(), TextColumn("[bold blue]{task.description}"), 
        BarColumn(), TaskProgressColumn(), TimeElapsedColumn(), console=console
    ) as progress:
        task = progress.add_task("[cyan]正在编译...", total=len(files))
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(compile_file_worker, f): f for f in files}
            for future in as_completed(futures):
                try:
                    res = future.result()
                    if res:
                        stats.compile_success += 1
                        stats.total_rules += res[2]
                        stats.details.append(res)
                        progress.update(task, description=f"[cyan]编译: {res[0]}")
                    progress.advance(task)
                except Exception as e:
                    stats.compile_fail += 1
                    progress.stop()
                    handle_error("编译文件", e)

    msg = f"[bold]编译成功[/bold]: [green]{stats.compile_success}[/green]\n[bold]规则总数[/bold]: [cyan]{stats.total_rules:,}[/cyan]"
    console.print(Panel(msg, title="🔨 编译阶段总结", border_style="green", expand=False))

def main():
    try:
        init_workspace()
        run_sync_phase()
        run_build_phase()
        console.rule("[bold green]✨ 全部完成 ✨[/bold green]")
        write_github_summary()
    except KeyboardInterrupt:
        handle_error("用户中断", "操作已取消")
    except Exception as e:
        handle_error("未捕获异常", e)

if __name__ == "__main__":
    main()
