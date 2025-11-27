import os
import json
import subprocess
import shutil
import tempfile

# --- 配置文件路径 ---
CONFIG_FILE = "repos.json"

# --- 目录结构 ---
DIR_TXT = "./rulesets"    # 下载后的原始存放区
DIR_JSON = "./rules-json"  # 转换中间区
DIR_SRS = "./rules-srs"    # 最终产物区

def sync_remote_repos():
    """
    读取 repos.json，拉取远程仓库的指定目录，整合到 DIR_TXT
    """
    print(">>> [第一阶段] 开始同步远程规则源...")
    
    # 1. 读取配置
    if not os.path.exists(CONFIG_FILE):
        print(f"错误: 找不到配置文件 {CONFIG_FILE}")
        exit(1)
        
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        repo_list = json.load(f)

    # 2. 清空 DIR_TXT (保证干净同步，删除上游已删除的文件)
    if os.path.exists(DIR_TXT):
        shutil.rmtree(DIR_TXT)
    os.makedirs(DIR_TXT)

    # 3. 循环处理每个仓库
    for item in repo_list:
        name = item.get('name', 'Unknown')
        url = item['url']
        remote_tgt = item['remote_path']  # 远程仓库里的子目录
        local_sub = item['local_subdir']  # 本地存放的子目录名

        print(f"正在拉取: [{name}] -> {url}")

        # 创建临时目录用于 clone
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Clone 仓库 (只拉取一层 depth=1，速度快)
                subprocess.run(["git", "clone", "--depth", "1", url, temp_dir], check=True, stdout=subprocess.DEVNULL)
                
                # 构建源路径和目标路径
                src_path = os.path.join(temp_dir, remote_tgt)
                dst_path = os.path.join(DIR_TXT, local_sub)

                # 检查远程路径是否存在
                if not os.path.exists(src_path):
                    print(f"  [!] 警告: 远程仓库中找不到路径: {remote_tgt}，跳过。")
                    continue

                # 复制文件夹内容
                # 如果是文件夹
                if os.path.isdir(src_path):
                    shutil.copytree(src_path, dst_path, dirs_exist_ok=True)
                # 如果是单个文件
                else:
                    os.makedirs(dst_path, exist_ok=True)
                    shutil.copy2(src_path, dst_path)

                print(f"  [√] 已提取 {remote_tgt} 到 {local_sub}")

            except subprocess.CalledProcessError:
                print(f"  [!] Git Clone 失败: {url}")
            except Exception as e:
                print(f"  [!] 处理出错: {e}")

def parse_domains(file_path):
    """简单的 TXT/YAML 清洗逻辑"""
    domains = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            c = line.strip()
            if not c or c.startswith("#") or c.startswith("//"): continue
            # 清洗 '- "xxx"' 格式
            c = c.replace("'", "").replace('"', "")
            if c.startswith("-"): c = c.lstrip("-").strip()
            if c: domains.append(c)
    except: pass
    return domains

def convert_and_compile():
    """
    遍历 DIR_TXT，生成 JSON 和 SRS
    """
    print("\n>>> [第二阶段] 开始转换与编译 SRS (使用最新内核)...")
    
    # 清空输出目录
    for d in [DIR_JSON, DIR_SRS]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)

    # 检查 Sing-box
    try:
        subprocess.run(["sing-box", "version"], stdout=subprocess.DEVNULL, check=True)
    except:
        print("错误: 找不到 sing-box，请检查 Action 安装步骤。")
        exit(1)

    count = 0
    for root, dirs, files in os.walk(DIR_TXT):
        rel_path = os.path.relpath(root, DIR_TXT)
        if rel_path == ".": rel_path = ""

        path_json = os.path.join(DIR_JSON, rel_path)
        path_srs = os.path.join(DIR_SRS, rel_path)
        os.makedirs(path_json, exist_ok=True)
        os.makedirs(path_srs, exist_ok=True)

        for file in files:
            if file.endswith((".txt", ".list", ".yaml")):
                src_file = os.path.join(root, file)
                base_name = os.path.splitext(file)[0]
                
                dst_json = os.path.join(path_json, f"{base_name}.json")
                dst_srs = os.path.join(path_srs, f"{base_name}.srs")

                # 1. 提取域名
                domains = parse_domains(src_file)
                if not domains: continue

                # 2. 写 JSON
                data = {"version": 1, "rules": [{"domain_suffix": domains}]}
                with open(dst_json, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)

                # 3. 编译 SRS
                try:
                    subprocess.run(["sing-box", "rule-set", "compile", dst_json, "-o", dst_srs], check=True, stdout=subprocess.DEVNULL)
                    # print(f"  处理: {base_name}.srs") # 减少日志刷屏，可注释掉
                    count += 1
                except:
                    print(f"  [X] 编译失败: {src_file}")
    
    print(f"\n>>> 全部完成！共生成 {count} 个规则集。")

if __name__ == "__main__":
    sync_remote_repos()
    convert_and_compile()
