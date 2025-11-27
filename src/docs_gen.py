import os
from datetime import datetime, timezone, timedelta

# ================= 配置区域 =================
BRANCH = "main"
OUTPUT_FILE = "README.md"
DIR_JSON = "./rules-json"
DIR_SRS = "./rules-srs"

def get_beijing_time():
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
    return bj_dt.strftime("%Y-%m-%d %H:%M")

def create_link_block(repo, branch, file_path):
    """
    生成一个链接块：包含原始链接和多个加速链接
    """
    # 1. 原始 Github 链接
    raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"
    
    # 2. 加速链接生成
    # (1) GhProxy (通用代理)
    url_ghproxy = f"https://ghproxy.net/{raw_url}"
    
    # (2) KGithub (以前的 fastgit)
    # 格式: raw.kgithub.com/user/repo/branch/file
    url_kgithub = f"https://raw.kgithub.com/{repo}/{branch}/{file_path}"
    
    # (3) GitMirror (很稳的 CDN)
    # 格式: raw.gitmirror.com/user/repo/branch/file
    url_gitmirror = f"https://raw.gitmirror.com/{repo}/{branch}/{file_path}"

    # 3. 构建 HTML 输出
    # 使用 <br> 换行，让原始链接和加速链接分开
    # 使用 &nbsp; 增加间距
    html = (
        f"<b>🌍 Original:</b> <a href='{raw_url}'>Github Raw</a><br>"
        f"<b>🚀 Mirrors:</b> "
        f"<a href='{url_ghproxy}' title='GhProxy'>GhProxy</a> &nbsp;·&nbsp; "
        f"<a href='{url_gitmirror}' title='GitMirror'>GitMirror</a> &nbsp;·&nbsp; "
        f"<a href='{url_kgithub}' title='KGithub'>KGithub</a>"
    )
    return html

def generate_markdown():
    repo_slug = os.getenv("GITHUB_REPOSITORY", "User/Repo")
    update_time = get_beijing_time()

    # 徽章
    badges = [
        f"![Build](https://img.shields.io/github/actions/workflow/status/{repo_slug}/manager.yml?style=flat-square&logo=github&label=Build)",
        f"![Size](https://img.shields.io/github/repo-size/{repo_slug}?style=flat-square&label=Size&color=success)",
        f"![Rules](https://img.shields.io/badge/Rules-Sing--box-blueviolet?style=flat-square&logo=sing-box)"
    ]

    content_lines = [
        "<div align='center'>",
        "",
        "# 🦄 Sing-box Rule Sets",
        "",
        " ".join(badges),
        "",
        "**每日自动更新 · 包含 IP 与 域名规则 · 全球多源加速**",
        "",
        f"`更生时间: {update_time} (北京时间)`",
        "",
        "</div>",
        "",
        "## 📖 使用说明",
        "<details>",
        "<summary><strong>👇 点此查看 Sing-box 配置示例</strong></summary>",
        "",
        "### 1. 远程引用 (推荐)",
        "请在下方表格中复制 `GhProxy` 或 `GitMirror` 的链接，填入 configuration:",
        "```json",
        "{",
        '  "route": {',
        '    "rule_set": [',
        '      {',
        '        "type": "remote",',
        '        "tag": "my-rule",',
        '        "format": "binary",',
        '        "url": "https://ghproxy.net/https://raw.githubusercontent.com/...",',
        '        "download_detour": "proxy"',
        "      }",
        "    ]",
        "  }",
        "}",
        "```",
        "</details>",
        "",
        "---",
        "",
        "## 📂 规则下载",
        "",
        "> 💡 **提示**: 表格中第一行是官方源，第二行是国内加速源。",
        "",
        "| 规则名称 (Name) | 🚀 SRS (二进制/Binary) | 📄 JSON (源码/Source) |",
        "| :--- | :--- | :--- |"
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
            
            # 1. 左侧文件名美化
            if rel_path:
                display_name = f"📂 <b>{rel_path}</b><br>└─ `{file_name}`"
            else:
                display_name = f"📄 **{file_name}**"

            # 2. 生成 JSON 链接块
            html_json = create_link_block(repo_slug, BRANCH, path_json)

            # 3. 生成 SRS 链接块 (如果存在)
            srs_abs_path = os.path.join(DIR_SRS, path_srs)
            if os.path.exists(srs_abs_path):
                html_srs = create_link_block(repo_slug, BRANCH, path_srs)
            else:
                html_srs = "⚠️ <i>Pending</i>"

            content_lines.append(f"| {display_name} | {html_srs} | {html_json} |")
            file_count += 1

    content_lines.append("")
    content_lines.append("---")
    content_lines.append(f"<div align='center'><sub>Project maintained by Actions · Total {file_count} rules</sub></div>")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(content_lines))
    
    print(f"✅ 旗舰版 README 已生成")

if __name__ == "__main__":
    generate_markdown()
