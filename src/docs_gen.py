import os
from datetime import datetime, timezone, timedelta

# ================= 配置区域 =================
BRANCH = "main"
OUTPUT_FILE = "README.md"
DIR_JSON = "./rules-json"
DIR_SRS = "./rules-srs"

# 官方 Logo 地址
LOGO_URL = "https://raw.githubusercontent.com/SagerNet/sing-box/dev/docs/assets/logo.svg"

def get_beijing_time():
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
    return bj_dt.strftime("%Y-%m-%d %H:%M")

def create_button_group(repo, branch, file_path):
    """
    生成“按钮风格”的链接组
    GitHub 的 Markdown 渲染 <code> 标签时会带有灰色背景和边框，
    配合 <a> 标签可以做成类似按钮的效果。
    """
    raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"
    
    # 加速源定义
    # 注意：这里使用 HTML 语法而不是 Markdown，以确保对齐和样式控制
    url_ghproxy = f"https://ghproxy.net/{raw_url}"
    url_gitmirror = f"https://raw.gitmirror.com/{repo}/{branch}/{file_path}"
    
    # 样式逻辑：
    # 原始链接用普通文本，加速链接用“代码块按钮”突出显示
    html = (
        f"<a href='{url_ghproxy}'><code>🚀 GhProxy</code></a>&nbsp;" 
        f"<a href='{url_gitmirror}'><code>🛸 Mirror</code></a>&nbsp;"
        f"<br>"
        f"<a href='{raw_url}' style='font-size:12px; color: gray;'>Original Source</a>"
    )
    return html

def generate_markdown():
    repo_slug = os.getenv("GITHUB_REPOSITORY", "User/Repo")
    update_time = get_beijing_time()

    # 顶部徽章
    badges = [
        f"![Build Status](https://img.shields.io/github/actions/workflow/status/{repo_slug}/manager.yml?style=flat-square&logo=github&color=4c1 )",
        f"![Rule Count](https://img.shields.io/badge/Rules-Dynamic-blue?style=flat-square&logo=sing-box)",
        f"![Repo Size](https://img.shields.io/github/repo-size/{repo_slug}?style=flat-square&color=orange)"
    ]

    content_lines = [
        f"<div align='center'>",
        f"",
        f"<img src='{LOGO_URL}' width='100' alt='Sing-box Logo'>",
        f"",
        f"# Sing-box 规则集仓库",
        f"",
        f"{' '.join(badges)}",
        f"",
        f"<p>每天 <strong>{update_time}</strong> (北京时间) 自动更新</p>",
        f"<p>提供 <strong>多源加速接口</strong>，适配各类网络环境</p>",
        f"",
        f"</div>",
        f"",
        f"## ⚡ 快速开始",
        f"",
        f"<details>",
        f"<summary><strong>点此展开：如何配置 config.json</strong></summary>",
        f"",
        f"> 💡 **提示**: 请直接复制下方表格中 `🚀 GhProxy` 按钮对应的链接。",
        f"",
        f"```json",
        f"{{",
        f'  "route": {{',
        f'    "rule_set": [',
        f'      {{',
        f'        "type": "remote",',
        f'        "tag": "geosite-google",',
        f'        "format": "binary",',
        f'        "url": "https://ghproxy.net/https://raw.githubusercontent.com/...",',
        f'        "download_detour": "proxy"',
        f"      }}",
        f"    ]",
        f"  }}",
        f"}}",
        f"```",
        f"</details>",
        f"",
        f"## 📦 规则下载列表",
        f"",
        f"| 规则名称 | 🚀 SRS (二进制 - 推荐) | 📄 JSON (源码) |",
        f"| :--- | :--- | :--- |"
    ]

    file_count = 0
    if not os.path.exists(DIR_JSON):
        print(f"❌ 错误: 找不到 {DIR_JSON} 目录")
        return

    for root, dirs, files in os.walk(DIR_JSON):
        files.sort()
        rel_path = os.path.relpath(root, DIR_JSON)
        if rel_path == ".": rel_path = ""

        for file in files:
            if not file.endswith(".json"): continue
            
            file_name = os.path.splitext(file)[0]
            
            # 路径处理
            path_json = os.path.join(rel_path, file).replace("\\", "/")
            path_srs = os.path.join(rel_path, f"{file_name}.srs").replace("\\", "/")
            
            # 名称美化
            # 如果有子目录，用小字体显示目录名，粗体显示文件名
            if rel_path:
                display_name = f"<sub>📂 {rel_path}</sub><br><strong>{file_name}</strong>"
            else:
                display_name = f"<strong>{file_name}</strong>"

            # 链接生成
            html_json = create_button_group(repo_slug, BRANCH, path_json)
            
            srs_abs_path = os.path.join(DIR_SRS, path_srs)
            if os.path.exists(srs_abs_path):
                html_srs = create_button_group(repo_slug, BRANCH, path_srs)
            else:
                html_srs = "🚫 <i>Pending</i>"

            content_lines.append(f"| {display_name} | {html_srs} | {html_json} |")
            file_count += 1

    content_lines.append("")
    content_lines.append("---")
    content_lines.append(f"<div align='center'><sub>Based on GitHub Actions & Sing-box · 共包含 {file_count} 个规则</sub></div>")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(content_lines))
    
    print(f"✅ 高颜值 README 已生成 (包含按钮样式)")

if __name__ == "__main__":
    generate_markdown()
