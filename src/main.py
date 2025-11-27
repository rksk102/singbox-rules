import os
import json
import subprocess
import shutil
import tempfile
import traceback
import re

# --- 配置文件路径 ---
CONFIG_FILE = "repos.json"

# --- 目录结构 ---
DIR_TXT = "./rules-txt"
DIR_JSON = "./rules-json"
DIR_SRS = "./rules-srs"

def list_directory_tree(startpath):
    print(f"\n[DEBUG] 正在检查目录内容: {startpath}")
    if not os.path.exists(startpath):
        print(f"  ! 目录不存在: {startpath}")
        return
    count = 0
    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, '').count(os.sep)
        indent = ' ' * 4 * (level)
        print(f"{indent}|-- {os.path.basename(root)}/")
        subindent = ' ' * 4 * (level + 1)
        for f in files:
            print(f"{subindent}|-- {f}")
            count += 1
    print(f"[DEBUG] 目录检查结束，共有 {count} 个文件。\n")

def sync_remote_repos():
    print(">>> [第一阶段] 开始同步远程规则源...")
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ 致命错误: 找不到配置文件 {CONFIG_FILE}")
        exit(1)

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            repo_list = json.load(f)
            print(f"✅ 成功读取 repos.json，共 {len(repo_list)} 个任务。")
    except Exception as e:
        print(f"❌ JSON 格式错误: {e}")
        exit(1)

    if os.path.exists(DIR_TXT): shutil.rmtree(DIR_TXT)
    os.makedirs(DIR_TXT)

    for item in repo_list:
        name = item.get('name', 'Unknown')
        url = item['url']
        remote_tgt = item['remote_path']
        local_sub = item['local_subdir']

        print(f"▶ 正在处理: [{name}]")

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                subprocess.run(["git", "clone", "--depth", "1", url, temp_dir], 
                               check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                full_remote_path = os.path.join(temp_dir, remote_tgt)
                dst_path = os.path.join(DIR_TXT, local_sub)

                if os.path.exists(full_remote_path):
                    if os.path.isdir(full_remote_path):
                        shutil.copytree(full_remote_path, dst_path, dirs_exist_ok=True)
                    else:
                        os.makedirs(dst_path, exist_ok=True)
                        shutil.copy2(full_remote_path, dst_path)
                    print(f"  ✅ 同步成功")
                else:
                    print(f"  ❌ 远程路径不存在: {remote_tgt}")

            except Exception as e:
                print(f"  ❌ Git 失败: {e}")

def parse_content(file_path):
    """
    读取文件，去除注释，返回有效行列表
    """
    lines_content = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            # 去除注释和空格
            c = line.split('#')[0].split('//')[0].strip()
            if not c: continue
            # 去除可能的引号
            c = c.replace("'", "").replace('"', "").replace(",", "")
            # payload: 格式的兼容
            if c.startswith("payload:"): continue
            if c.startswith("-"): c = c.lstrip("-").strip()
            
            if c: lines_content.append(c)
    except UnicodeDecodeError:
        print(f"  ! 编码错误跳过: {os.path.basename(file_path)}")
    return lines_content

def detect_rule_type(content_list, filename):
    """
    智能判断规则类型：
    1. 优先看文件名 (geoip-xxx -> ip, geosite-xxx -> domain)
    2. 其次检查内容格式 (有 / 数字 -> ip_cidr)
    """
    fname = filename.lower()
    
    # 1. 文件名强制规则
    if "ip" in fname and "domain" not in fname:
        return "ip_cidr"
    if "domain" in fname or "site" in fname:
        return "domain_suffix"

    # 2. 内容采样检测 (检查前 20 行)
    ip_cidr_pattern = re.compile(r'^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(/\d+)?$|:') # IPv4 CIDR or IPv6
    
    ip_count = 0
    domain_count = 0
    
    sample = content_list[:20] 
    for line in sample:
        if ip_cidr_pattern.match(line):
            ip_count += 1
        else:
            domain_count += 1

    # 如果大部分像是 IP
    if ip_count > domain_count:
        return "ip_cidr"
    else:
        return "domain_suffix"

def convert_and_compile():
    print("\n>>> [第二阶段] 开始智能转换与编译...")
    
    # 检查 sing-box
    try:
        subprocess.check_output(["sing-box", "version"], stderr=subprocess.STDOUT)
    except:
        print("❌ 错误: 未找到 sing-box")
        exit(1)

    if os.path.exists(DIR_JSON): shutil.rmtree(DIR_JSON)
    if os.path.exists(DIR_SRS): shutil.rmtree(DIR_SRS)
    os.makedirs(DIR_JSON)
    os.makedirs(DIR_SRS)

    success_count = 0
    
    for root, dirs, files in os.walk(DIR_TXT):
        rel_path = os.path.relpath(root, DIR_TXT)
        if rel_path == ".": rel_path = ""
        
        if files:
             os.makedirs(os.path.join(DIR_JSON, rel_path), exist_ok=True)
             os.makedirs(os.path.join(DIR_SRS, rel_path), exist_ok=True)

        for file in files:
            # 过滤后缀
            valid_exts = (".txt", ".list", ".yaml", ".conf", ".json", "")
            if not file.lower().endswith(valid_exts) and "." in file:
                continue

            src_file = os.path.join(root, file)
            base_name = os.path.splitext(file)[0]
            
            print(f"处理文件: {os.path.join(rel_path, file)}")

            # 1. 解析内容
            content = parse_content(src_file)
            if not content:
                print(f"  -> 内容为空，跳过")
                continue

            # 2. 智能识别类型
            rule_type = detect_rule_type(content, file)
            print(f"  -> 识别为: {rule_type} (包含 {len(content)} 条规则)")

            # 3. 生成 JSON 结构
            # sing-box 1.8+ 推荐的 headless rule 结构
            data = {
                "version": 1,
                "rules": [
                    {
                        rule_type: content
                    }
                ]
            }

            dst_json = os.path.join(DIR_JSON, rel_path, f"{base_name}.json")
            dst_srs = os.path.join(DIR_SRS, rel_path, f"{base_name}.srs")

            try:
                with open(dst_json, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"  ❌ JSON 写入失败: {e}")
                continue

            # 4. 编译 SRS
            try:
                res = subprocess.run(
                    ["sing-box", "rule-set", "compile", dst_json, "-o", dst_srs],
                    capture_output=True, text=True
                )
                if res.returncode != 0:
                    print(f"  ❌ 编译失败: {res.stderr.strip()}")
                else:
                    success_count += 1
            except Exception as e:
                print(f"  ❌ 调用 sing-box 失败: {e}")

    print(f"\n>>> 全部完成。成功生成 {success_count} 个规则集。")

if __name__ == "__main__":
    sync_remote_repos()
    convert_and_compile()
    # 调试完可以注释掉下面这行，不打印目录树
    # list_directory_tree(DIR_TXT)
