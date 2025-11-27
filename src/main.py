import os
import json
import subprocess
import shutil
import tempfile
import traceback  # 用于打印详细报错

# --- 配置文件路径 ---
CONFIG_FILE = "repos.json"

# --- 目录结构 ---
DIR_TXT = "./rules-txt"
DIR_JSON = "./rules-json"
DIR_SRS = "./rules-srs"

def list_directory_tree(startpath):
    """
    调试工具：像 tree 命令一样打印目录结构
    """
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
    """
    拉取阶段：增加 Git 输出捕捉和目录检查
    """
    print(">>> [第一阶段] 开始同步远程规则源...")
    
    if not os.path.exists(CONFIG_FILE):
        print(f"❌ 致命错误: 找不到配置文件 {CONFIG_FILE}")
        exit(1) # 直接退出

    try:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            repo_list = json.load(f)
            print(f"✅ 成功读取 repos.json，共 {len(repo_list)} 个任务。")
    except json.JSONDecodeError as e:
        print(f"❌ JSON 格式错误: {e}")
        print("请检查是否有中文引号，或者最后一行多余的逗号。")
        exit(1)

    # 清空目录
    if os.path.exists(DIR_TXT):
        shutil.rmtree(DIR_TXT)
    os.makedirs(DIR_TXT)

    for item in repo_list:
        name = item.get('name', 'Unknown')
        url = item['url']
        remote_tgt = item['remote_path']
        local_sub = item['local_subdir']

        print(f"▶ 正在处理: [{name}]")
        print(f"  - 仓库: {url}")
        print(f"  - 目标路径: {remote_tgt}")
        print(f"  - 本地存放: {local_sub}")

        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # 修改：允许打印 git 的错误信息
                subprocess.run(
                    ["git", "clone", "--depth", "1", url, temp_dir], 
                    check=True, 
                    stdout=subprocess.PIPE, 
                    stderr=subprocess.PIPE
                )
                print("  - Git Clone 成功")

                # 调试：检查一下下载下来的仓库里有没有那个文件夹
                full_remote_path = os.path.join(temp_dir, remote_tgt)
                if not os.path.exists(full_remote_path):
                    print(f"  ❌ 错误: 在远程仓库中找不到路径 '{remote_tgt}'")
                    print("  - 远程仓库根目录包含以下文件:")
                    print(os.listdir(temp_dir)) # 打印根目录看看有什么
                    continue

                # 复制
                dst_path = os.path.join(DIR_TXT, local_sub)
                if os.path.isdir(full_remote_path):
                    shutil.copytree(full_remote_path, dst_path, dirs_exist_ok=True)
                else:
                    os.makedirs(dst_path, exist_ok=True)
                    shutil.copy2(full_remote_path, dst_path)
                
                print(f"  ✅ 同步成功 -> {dst_path}")

            except subprocess.CalledProcessError as e:
                print(f"  ❌ Git Clone 失败，错误信息:\n{e.stderr.decode()}")
            except Exception as e:
                print(f"  ❌ 发生未知错误: {e}")
                traceback.print_exc()

    # --- 关键调试：打印处理完后的文件树 ---
    list_directory_tree(DIR_TXT)

def parse_domains(file_path):
    domains = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for line in lines:
            c = line.strip()
            if not c or c.startswith("#") or c.startswith("//"): continue
            c = c.replace("'", "").replace('"', "")
            if c.startswith("-"): c = c.lstrip("-").strip()
            if c: domains.append(c)
    except UnicodeDecodeError:
        print(f"  ! 跳过非文本文件 (编码错误): {os.path.basename(file_path)}")
    except Exception as e:
        print(f"  ! 读取文件错误: {e}")
    return domains

def convert_and_compile():
    print("\n>>> [第二阶段] 开始转换与编译...")

    # 检查 sing-box
    try:
        v = subprocess.check_output(["sing-box", "version"], stderr=subprocess.STDOUT).decode()
        print(f"Sing-box 检测正常:\n{v.splitlines()[0]}")
    except Exception as e:
        print(f"❌ 找不到 sing-box: {e}")
        exit(1)

    # 清空输出
    for d in [DIR_JSON, DIR_SRS]:
        if os.path.exists(d): shutil.rmtree(d)
        os.makedirs(d)

    success_count = 0
    fail_count = 0

    # 遍历
    has_files = False
    for root, dirs, files in os.walk(DIR_TXT):
        rel_path = os.path.relpath(root, DIR_TXT)
        if rel_path == ".": rel_path = ""
        
        # 为这个子目录创建对应的输出目录
        if files:
             os.makedirs(os.path.join(DIR_JSON, rel_path), exist_ok=True)
             os.makedirs(os.path.join(DIR_SRS, rel_path), exist_ok=True)

        for file in files:
            has_files = True
            src_file = os.path.join(root, file)

            # 宽松的后缀检查，或者输出为什么跳过
            valid_exts = (".txt", ".list", ".yaml", ".conf", ".json")
            if not file.lower().endswith(valid_exts):
                print(f"[跳过] 文件后缀不支持: {file}")
                continue

            base_name = os.path.splitext(file)[0]
            dst_json = os.path.join(DIR_JSON, rel_path, f"{base_name}.json")
            dst_srs = os.path.join(DIR_SRS, rel_path, f"{base_name}.srs")

            print(f"处理文件: {os.path.join(rel_path, file)}")

            # 1. 提取
            domains = parse_domains(src_file)
            if not domains:
                print(f"  -> [警告] 未提取到有效域名，跳过")
                continue

            # 2. 写入 JSON
            try:
                data = {"version": 1, "rules": [{"domain_suffix": domains}]}
                with open(dst_json, 'w', encoding='utf-8') as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"  ❌ JSON 写入失败: {e}")
                fail_count += 1
                continue

            # 3. 编译 SRS
            try:
                # 使用 capture_output=True 来捕获报错信息
                res = subprocess.run(
                    ["sing-box", "rule-set", "compile", dst_json, "-o", dst_srs],
                    capture_output=True,
                    text=True
                )
                if res.returncode != 0:
                    print(f"  ❌ 编译失败 STDERR:\n{res.stderr}")
                    fail_count += 1
                else:
                    # print(f"  ✅ 编译成功")
                    success_count += 1
            except Exception as e:
                print(f"  ❌ 调用 sing-box 失败: {e}")
                fail_count += 1

    if not has_files:
        print("\n❌ [警告] DIR_TXT 文件夹为空，没有找到任何文件！请检查第一阶段的日志。")
    else:
        print(f"\n>>> 全部完成。成功: {success_count}, 失败: {fail_count}")

if __name__ == "__main__":
    # 使用 Unbuffered 模式运行，防止日志丢失
    try:
        sync_remote_repos()
        convert_and_compile()
    except Exception as e:
        print("❌ 主程序发生未捕获异常:")
        traceback.print_exc()
        exit(1)
