import os

# --- 配置 ---
BRANCH = "main"
OUTPUT_FILE = "README.md" # <--- 修改为 README.md
DIR_JSON = "./rules-json"
DIR_SRS = "./rules-srs"

def generate_markdown():
    repo_slug = os.getenv("GITHUB_REPOSITORY", "your_name/your_repo")
    base_url = f"https://github.com/{repo_slug}/raw/{BRANCH}"
    
    # 这里定义 README 的头部内容，你可以随意修改文字
    content_lines = [
        "# 🚀 Sing-box 自用规则集",
        "",
        f"![Auto Build](https://github.com/{repo_slug}/actions/workflows/manager.yml/badge.svg)",
        "",
        "本项目由自动化工作流维护，定时拉取上游规则并编译为 Sing-box 兼容格式。",
        "所有规则均已编译为 **SRS (Sing-box Rule Set)** 二进制格式，以获得最佳性能。",
        "",
        "## 📂 规则列表",
        "> 点击下方链接可直接复制使用。",
        "",
        "| 规则名称 | 📝 JSON (Source) | 🚀 SRS (Binary) |",
        "| :--- | :---: | :---: |"
    ]

    if not os.path.exists(DIR_JSON):
        print(f"错误: 找不到 {DIR_JSON} 目录")
        return

    count = 0
    for root, dirs, files in os.walk(DIR_JSON):
        files.sort()
        rel_path = os.path.relpath(root, DIR_JSON)
        if rel_path == ".": rel_path = ""

        for file in files:
            if not file.endswith(".json"): continue
            
            file_name = os.path.splitext(file)[0]
            
            if rel_path:
                display_name = f"**{rel_path}** / {file_name}"
                full_rel_path = os.path.join(rel_path, file_name)
            else:
                display_name = file_name
                full_rel_path = file_name

            # 构造链接
            # 替换反斜杠以适配 Windows/Linux 路径差异
            path_json = f"{DIR_JSON}/{full_rel_path}.json".replace("\\", "/").replace("./", "")
            path_srs = f"{DIR_SRS}/{full_rel_path}.srs".replace("\\", "/").replace("./", "")

            link_json = f"[JSON]({base_url}/{path_json})"
            
            # 检查 SRS 是否存在
            srs_local_path = os.path.join(DIR_SRS, rel_path, f"{file_name}.srs")
            if os.path.exists(srs_local_path):
                link_srs = f"[SRS]({base_url}/{path_srs})"
            else:
                link_srs = "Wait building..."

            content_lines.append(f"| {display_name} | {link_json} | {link_srs} |")
            count += 1

    # 添加底部说明
    content_lines.append("")
    content_lines.append("## ⚙️ 自动化配置")
    content_lines.append(f"- 自动更新时间: 每天")
    content_lines.append(f"- 包含规则总数: {count} 个")
    content_lines.append("- Powered by Github Actions & Sing-box")

    # 写入 README.md
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(content_lines))
    
    print(f"✅ README.md 已更新，包含 {count} 条规则。")

if __name__ == "__main__":
    generate_markdown()
