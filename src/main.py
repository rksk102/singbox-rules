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

# --- 尝试导入 Rich 库 ---
try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn, TimeElapsedColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    from rich import print as rprint
except ImportError:
    print("Error: Please install rich (pip install rich)")
    sys.exit(1)

# 全局配置
console = Console(record=True) # 开启录制以备导出
ROOT_DIR = Path.cwd()
CONFIG_FILE = ROOT_DIR / "repos.json"
DIR_TXT = ROOT_DIR / "rules-txt"
DIR_JSON = ROOT_DIR / "rules-json"
DIR_SRS = ROOT_DIR / "rules-srs"
MAX_WORKERS = 4

# --- 统计数据类 ---
class WorkflowStats:
    def __init__(self):
        self.start_time = time.time()
        self.sync_success = 0
        self.sync_total = 0
        self.compile_success = 0
        self.compile_fail = 0
        self.total_rules = 0
        self.details = [] # 存储编译详情 [(name, type, count), ...]
        self.status = "✅ 成功"

    @property
    def duration(self):
        return str(timedelta(seconds=int(time.time() - self.start_time)))

stats = WorkflowStats()

# --- 辅助函数 ---

def write_github_summary():
    """生成 GitHub Actions 页面可见的 Markdown 摘要"""
    if "GITHUB_STEP_SUMMARY" not in os.environ:
        return

    md_content = f"""
# 🚀 构建报告: {stats.status}

| 指标 | 结果 |
| :--- | :--- |
| ⏱️ 耗时 | {stats.duration} |
| 🔄 同步仓库 | {stats.sync_success} / {stats.sync_total} |
| 🔨 编译文件 | {stats.compile_success} (失败: {stats.compile_fail}) |
| 📊 规则总条数 | **{stats.total_rules:,}** |

### 📂 编译详情 (Top 20)
| 文件名 | 类型 | 规则数 |
| :--- | :--- | :---: |
"""
    # 按规则数量倒序排列
    sorted_details = sorted(stats.details, key=lambda x: x[2], reverse=True)[:20]
    
    for name, rtype, count in sorted_details:
        icon = "🌐" if rtype == "domain_suffix" else "📡"
        md_content += f"| {name} | {icon} `{rtype}` | {count:,} |\n"

    if len(stats.details) > 20:
        md_content += f"| ... 以及其他 {len(stats.details)-20} 个文件 | | |\n"

    with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
        f.write(md_content)

def handle_error(phase, error_msg):
    """统一错误处理"""
    stats.status = f"❌ 失败于 {phase}"
    console.print(f"\n[bold red]⛔ 致命错误 - {phase}[/bold red]")
    console.print(Panel(str(error_msg), style="red", title="错误详情"))
    write_github_summary()
    sys.exit(1)

# --- 核心任务函数 ---

def init_workspace():
    """初始化目录"""
    console.rule("[bold blue]阶段 1: 初始化[/bold blue]")
    try:
        dirs = [DIR_TXT, DIR_JSON, DIR_SRS]
        created = []
        for d in dirs:
            if d.exists(): shutil.rmtree(d)
            d.mkdir(parents=True)
            created.append(d.name)
        
        console.print(f"[green]✅ 已重置目录: {', '.join(created)}[/green]")
    except Exception as e:
        handle_error("初始化", e)

def run_sync_phase():
    """同步阶段"""
    console.rule("[bold blue]阶段 2: 同步远程源[/bold blue]")
    
    if not CONFIG_FILE.exists():
        handle_error("配置读取", f"找不到 {CONFIG_FILE}")

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            repo_list = json.load(f)
            stats.sync_total = len(repo_list)
    except Exception as e:
        handle_error("配置解析", e)

    # 绘制同步表格
    sync_table = Table(box=box.SIMPLE_HEAD)
    sync_table.add_column("仓库", style="cyan")
    sync_table.add_column("目标路径", style="dim")
    sync_table.add_column("状态", justify="right")

    for item in repo_list:
        name = item.get('name', 'Unknown')
        
        # 实时显示正在处理
        with console.status(f"[bold yellow]⬇️ 正在拉取: {name}...[/bold yellow]"):
            try:
                # 执行 Git 操作
                url = item.get('url')
                remote_tgt = item.get('remote_path')
                local_sub = item.get('local_subdir', 'misc')
                dest_dir = DIR_TXT / local_sub
                dest_dir.mkdir(parents=True, exist_ok=True)

                with tempfile.TemporaryDirectory() as temp_dir:
                    subprocess.run(["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", url, temp_dir],
                                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                    subprocess.run(["git", "sparse-checkout", "set", remote_tgt],
                                   cwd=temp_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                    subprocess.run(["git", "checkout"],
                                   cwd=temp_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
                    
                    full_remote_path = Path(temp_dir) / remote_tgt
                    if full_remote_path.is_dir():
                        shutil.copytree(full_remote_path, dest_dir, dirs_exist_ok=True)
                    elif full_remote_path.is_file():
                        shutil.copy2(full_remote_path, dest_dir)
                    else:
                        raise FileNotFoundError("远程文件未找到")
                
                stats.sync_success += 1
                sync_table.add_row(name, remote_tgt, "[green]OK[/green]")
            except Exception as e:
                sync_table.add_row(name, str(e), "[red]FAIL[/red]")
                console.print(sync_table) # 先打印已完成的
                handle_error("同步: " + name, e)

    console.print(sync_table)
    
    # 阶段总结 Panel
    summary = f"""[bold]仓库总数[/bold]: {stats.sync_total}
[bold]同步成功[/bold]: [green]{stats.sync_success}[/green]
[bold]存储位置[/bold]: {DIR_TXT}"""
    console.print(Panel(summary, title="📊 同步阶段总结", border_style="blue", expand=False))

def compile_file_worker(args):
    """单一文件编译逻辑"""
    file_path, rel_path = args
    if not file_path.name.lower().endswith(('.txt', '.list', '.yaml', '.conf', '.json', '')):
        return None

    # 读取清洗
    rules = set()
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                c = line.split('#')[0].split('//')[0].strip()
                if not c or c.startswith("payload:") or "repo" in c: continue
                c = c.replace("'", "").replace('"', "").replace(",", "").lstrip("-").strip()
                if c: rules.add(c)
    except:
        return None # 忽略二进制或坏文件

    if not rules: return None
    rules_list = list(rules)

    # 识别类型
    fname = file_path.name.lower()
    if "ip" in fname and "domain" not in fname: 
        rtype = "ip_cidr"
    elif "domain" in fname or "site" in fname:
        rtype = "domain_suffix"
    else:
        # 采样
        sample = rules_list[:10]
        ip_cnt = sum(1 for x in sample if re.match(r'^\d+\.|:', x))
        rtype = "ip_cidr" if ip_cnt > len(sample)/2 else "domain_suffix"

    # 生成文件
    out_dir_json = DIR_JSON / rel_path.parent
    out_dir_srs = DIR_SRS / rel_path.parent
    out_dir_json.mkdir(parents=True, exist_ok=True)
    out_dir_srs.mkdir(parents=True, exist_ok=True)

    json_path = out_dir_json / f"{file_path.stem}.json"
    srs_path = out_dir_srs / f"{file_path.stem}.srs"

    data = {"version": 1, "rules": [{rtype: rules_list}]}
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    res = subprocess.run(["sing-box", "rule-set", "compile", str(json_path), "-o", str(srs_path)],
                         capture_output=True, text=True)
    
    if res.returncode != 0:
        raise RuntimeError(f"{file_path.name}: {res.stderr.strip()}")

    return (file_path.name, rtype, len(rules_list))

def run_build_phase():
    """编译阶段"""
    console.rule("[bold blue]阶段 3: 编译 (.srs)[/bold blue]")

    files = [(p, p.relative_to(DIR_TXT)) for p in DIR_TXT.rglob("*") if p.is_file()]
    if not files:
        console.print("[yellow]⚠️ 没有文件需要编译[/yellow]")
        return

    # 进度条
    with Progress(
        SpinnerColumn(),
        TextColumn("[bold blue]{task.description}"),
        BarColumn(bar_width=None),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]编译进度...", total=len(files))
        
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(compile_file_worker, f): f for f in files}
            
            for future in as_completed(futures):
                try:
                    res = future.result()
                    if res:
                        stats.compile_success += 1
                        stats.total_rules += res[2]
                        stats.details.append(res)
                    progress.advance(task)
                except Exception as e:
                    stats.compile_fail += 1
                    # 立即停止
                    progress.stop()
                    handle_error("编译文件", e)

    # 阶段总结
    sum_panel = f"""[bold]编译成功[/bold]: [green]{stats.compile_success}[/green]
[bold]规则总数[/bold]: [cyan]{stats.total_rules:,}[/cyan]
[bold]输出目录[/bold]: {DIR_SRS}"""
    console.print(Panel(sum_panel, title="🔨 编译阶段总结", border_style="green", expand=False))

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
