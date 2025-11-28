import os
import json
import subprocess
import shutil
import tempfile
import re
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

# --- 配置部分 ---
ROOT_DIR = Path.cwd() # 获取当前脚本运行的根目录
CONFIG_FILE = ROOT_DIR / "repos.json"

# 定义输出目录
DIR_TXT = ROOT_DIR / "rules-txt"
DIR_JSON = ROOT_DIR / "rules-json"
DIR_SRS = ROOT_DIR / "rules-srs"

# 并发线程数 (根据机器性能调整，GitHub Actions 通常 2-4 核)
MAX_WORKERS = 4

def setup_directories():
    """初始化目录结构"""
    for d in [DIR_TXT, DIR_JSON, DIR_SRS]:
        if d.exists():
            # 注意：这里选择清理 txt 和 josn/srs，
            # 如果你想保留历史 txt，可以注释掉下面这行 shutil.rmtree(DIR_TXT)
            if d == DIR_TXT: 
                shutil.rmtree(d)
                d.mkdir(parents=True)
            else:
                # 编译目录建议每次清空
                shutil.rmtree(d)
                d.mkdir(parents=True)
        else:
            d.mkdir(parents=True)
    print(f"✅ 目录初始化完成: \n  - {DIR_TXT}\n  - {DIR_JSON}\n  - {DIR_SRS}")

def sync_repo_task(item):
    """单个仓库同步任务"""
    name = item.get('name', 'Unknown')
    url = item.get('url')
    branch = item.get('branch', None) # 可选分支
    remote_tgt = item.get('remote_path')
    local_sub = item.get('local_subdir', 'misc') # 默认存入 rules-txt/misc

    if not url or not remote_tgt:
        return f"❌ [{name}] 配置缺失 url 或 remote_path"

    print(f"⬇️ [{name}] 正在拉取...")
    
    # 目标本地路径
    dest_dir = DIR_TXT / local_sub
    dest_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory() as temp_dir:
        try:
            cmd = ["git", "clone", "--depth", "1", "--filter=blob:none", "--sparse", url, temp_dir]
            if branch:
                cmd.extend(["-b", branch])
            
            # 1. 稀疏拉取 (只拉取 .git 信息)
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 2. 设置稀疏检出目录
            subprocess.run(["git", "sparse-checkout", "set", remote_tgt], cwd=temp_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            # 3. 检出文件
            subprocess.run(["git", "checkout"], cwd=temp_dir, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

            # 4. 移动文件
            full_remote_path = Path(temp_dir) / remote_tgt
            
            if full_remote_path.is_dir():
                # 如果是文件夹，遍历复制
                shutil.copytree(full_remote_path, dest_dir, dirs_exist_ok=True)
            elif full_remote_path.is_file():
                # 如果是文件，直接复制
                shutil.copy2(full_remote_path, dest_dir)
            else:
                return f"⚠️ [{name}] 远程路径未找到文件: {remote_tgt}"
            
            return f"✅ [{name}] 同步成功 -> {local_sub}"
        
        except subprocess.CalledProcessError:
            return f"❌ [{name}] Git 拉取失败"
        except Exception as e:
            return f"❌ [{name}] 未知错误: {str(e)}"

def parse_and_clean_content(file_path):
    """读取、去重、清洗"""
    cleaned_lines = set() # 使用 set 自动去重
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                # 移除注释
                line = line.split('#')[0].split('//')[0].strip()
                if not line: continue
                
                # 移除常见的引号和 payload 前缀
                line = line.replace("'", "").replace('"', "").replace(",", "")
                if line.startswith("payload:"): continue
                if line.startswith("-"): line = line.lstrip("-").strip()
                
                if line:
                    cleaned_lines.add(line)
    except:
        return []
    return list(cleaned_lines)

def detect_rule_type(content_sample, filename):
    """识别规则类型"""
    fname = filename.lower()
    if "ip" in fname and "domain" not in fname: return "ip_cidr"
    if "domain" in fname or "site" in fname: return "domain_suffix"
    
    # 内容采样
    ip_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(/\d+)?$|:')
    ip_count = sum(1 for x in content_sample if ip_pattern.match(x))
    return "ip_cidr" if ip_count > len(content_sample) / 2 else "domain_suffix"

def compile_worker(file_info):
    """单个文件编译任务 (用于多线程)"""
    file_path, rel_path = file_info
    
    # 过滤非规则文件
    if file_path.suffix not in ['.txt', '.list', '.yaml', '.conf', '.json', '']:
        return None

    # 1. 解析
    content = parse_and_clean_content(file_path)
    if not content: return None

    # 2. 识别
    rule_type = detect_rule_type(content[:20], file_path.name)
    
    # 3. 构造 JSON
    data = {"version": 1, "rules": [{rule_type: content}]}
    
    base_name = file_path.stem
    target_subdir = rel_path.parent
    
    # 准备输出目录
    json_dir = DIR_JSON / target_subdir
    srs_dir = DIR_SRS / target_subdir
    json_dir.mkdir(parents=True, exist_ok=True)
    srs_dir.mkdir(parents=True, exist_ok=True)
    
    json_out = json_dir / f"{base_name}.json"
    srs_out = srs_dir / f"{base_name}.srs"
    
    # 4. 写入 JSON
    try:
        with open(json_out, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        return f"❌ JSON 写错: {file_path.name} - {e}"

    # 5. 调用 Sing-box 编译
    try:
        proc = subprocess.run(
            ["sing-box", "rule-set", "compile", str(json_out), "-o", str(srs_out)],
            capture_output=True, text=True
        )
        if proc.returncode != 0:
            return f"❌ SRS 编译失败: {file_path.name} -> {proc.stderr.strip()}"
    except Exception as e:
        return f"❌ Sing-box 调用失败: {e}"

    return f"✨ 完成: {rel_path} ({len(content)} rules) -> {rule_type}"

def main():
    if not CONFIG_FILE.exists():
        print(f"❌ 错误: 未找到配置文件 {CONFIG_FILE}")
        exit(1)

    print(">>> [步骤 1] 初始化与同步...")
    setup_directories()
    
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        repo_list = json.load(f)

    # 串行拉取（Git 并发容易锁文件，建议串行或限制低并发）
    for item in repo_list:
        print(sync_repo_task(item))

    print("\n>>> [步骤 2] 编译规则集 (并发处理)...")
    
    # 收集待处理文件
    all_files = []
    for p in DIR_TXT.rglob("*"):
        if p.is_file():
            # 计算相对于 DIR_TXT 的路径，保持目录结构
            all_files.append((p, p.relative_to(DIR_TXT)))

    # 使用线程池并发编译
    success_cnt = 0
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        results = executor.map(compile_worker, all_files)
        for res in results:
            if res:
                print(res)
                if "❌" not in res: success_cnt += 1

    print(f"\n🎉 全部处理完成! 成功生成 {success_cnt} 个 SRS 规则集。")

if __name__ == "__main__":
    main()
