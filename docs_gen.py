import os

# --- 配置 ---
# 你的主分支名字 (通常是 main 或 master)
BRANCH = "main"
# 输出的文件名
OUTPUT_FILE = "RULESETS.md"

# 目录配置
DIR_JSON = "./rules-json"
DIR_SRS = "./rules-srs"

def generate_markdown():
    # 从 GitHub Environment 获取仓库信息 (格式: 用户名/仓库名)
    # 如果在本地测试，默认使用占位符
    repo_slug = os.getenv("GITHUB_REPOSITORY", "your_name/your_repo")
    
    # 基础 URL 前缀
    # 使用 github.com/raw 格式，这是最稳定的下载链接格式
    base_url = f"https://github.com/{repo_slug}/raw/{BRANCH}"

    content_lines = [
        "# 📜 Sing-box Rule Sets",
        f"> 自动生成于: {os.getenv('GITHUB_SERVER_URL', 'https://github.com')}/{repo_slug}",
        "",
        "这里列出了本仓库包含的所有规则集。点击链接可直接复制使用。",
        "",
        "| 类别 / 名称 | 📝 JSON (Source) | 🚀 SRS (Binary) |",
        "| :--- | :---: | :---: |"
    ]

    # 遍历 rules-json 目录 (以此为基准)
    # 假设 srs 目录结构通过之前的脚本已经完全对齐
    if not os.path.exists(DIR_JSON):
        print(f"错误: 找不到 {DIR_JSON} 目录")
        return

    for root, dirs, files in os.walk(DIR_JSON):
        # 排序文件，美观一点
        files.sort()
        
        # 计算相对路径 (例如: meta-geo)
        rel_path = os.path.relpath(root, DIR_JSON)
        if rel_path == ".": rel_path = ""

        for file in files:
            if not file.endswith(".json"):
                continue
            
            file_name = os.path.splitext(file)[0]
            
            # 构造显示名称 (类别/文件)
            if rel_path:
                display_name = f"**{rel_path}** / {file_name}"
                full_rel_path = os.path.join(rel_path, file_name)
            else:
                display_name = file_name
                full_rel_path = file_name

            # 构造链接 (注意 URL 路径分隔符必须是 /)
            path_json = f"{DIR_JSON}/{full_rel_path}.json".replace("\\", "/").replace("./", "")
            path_srs = f"{DIR_SRS}/{full_rel_path}.srs".replace("\\", "/").replace("./", "")

            link_json = f"[JSON]({base_url}/{path_json})"
            link_srs = f"[SRS]({base_url}/{path_srs})"

            # 检查 SRS 文件是否存在 (也许有的只生成了 JSON 没成功生成 SRS)
            if not os.path.exists(os.path.join(DIR_SRS, rel_path, f"{file_name}.srs")):
                link_srs = "❌"

            # 添加表格行
            content_lines.append(f"| {display_name} | {link_json} | {link_srs} |")

    # 写入文件
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(content_lines))
    
    print(f"✅ 文档已生成: {OUTPUT_FILE}")

if __name__ == "__main__":
    generate_markdown()
