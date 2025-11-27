import os
import urllib.parse
from datetime import datetime, timezone, timedelta

# ================= 配置区域 =================
BRANCH = "main"
OUTPUT_FILE = "README.md"
DIR_JSON = "./rules-json"
DIR_SRS = "./rules-srs"

# 🌏 定义加速镜像源 (你可以按需添加更多)
# key: 显示的名称 (Emoji + 文字)
# url_prefix: 镜像前缀
MIRRORS = [
    {
        "name": "🚀 GhProxy",
        "prefix": "https://ghproxy.net/https://raw.githubusercontent.com"
    },
    {
        "name": "🛸 GitMirror",
        "prefix": "https://raw.gitmirror.com"
    },
    {
        "name": "⚡ 404 Lab",
        "prefix": "https://raw.kgithub.com"
    }
]
# ===========================================

def get_beijing_time():
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
    return bj_dt.strftime("%Y-%m-%d %H:%M")

def generate_link_group(repo_slug, file_path, is_srs=False):
    """
    生成一组链接 (官方 + 所有镜像)
    返回 HTML 字符串
    """
    # 1. 官方链接 (Git Raw)
    raw_url = f"https://raw.githubusercontent.com/{repo_slug}/{BRANCH}/{file_path}"
    
    # 构建 HTML 链接组
    links_html = []
    
    # 添加官方源
    links_html.append(f'<a href="{raw_url}">🏠 Github</a>')
    
    # 添加镜像源
    for mirror in MIRRORS:
        # 拼接 URL: 镜像前缀 + /用户名/仓库/分支/文件路径
        # 注意: 有些镜像代理直接拼接完整 URL，有些是拼接路径。
        # 这里处理常见的 "https://ghproxy.net/https://raw..." 和 "https://raw.fastgit..." 两种情况
        
        if mirror["prefix"].startswith("https://ghproxy"):
            # GhProxy 风格: prefix + full_raw_url
            mirror_url = f"{mirror['prefix']}/{raw_url}"
        else:
            # GitMirror/FastGit 风格: prefix / user / repo / branch / file
            mirror_url = f"{mirror['prefix']}/{repo_slug}/{BRANCH}/{file_path}"
            
        links_html.append(f'<a href="{mirror_url}">{mirror["name"]}</a>')
    
    # 用 " | " 分隔，或者换行
    return " &nbsp;|&nbsp; ".join(links_html)

def generate_markdown():
    repo_slug = os.getenv("GITHUB_REPOSITORY", "User/Repo")
    update_time = get_beijing_time()

    # 徽章列表
    badges = [
        f"![Build](https://img.shields.io/github/actions/workflow/status/{repo_slug}/manager.yml?style=flat-square&logo=github&label=Build)",
        f"![Size](https://img.shields.io/github/repo-size/{repo_slug}?style=flat-square&label=Size&color=success)",
        f"![Last Commit](https://img.shields.io/github/last-commit/{repo_slug}?style=flat-square&label=Last%20Update&color=blue)",
        f"![Rules](https://img.shields.io/badge/Rules-Sing--box-blueviolet?style=flat-square&logo=sing-box)"
    ]

    content_lines = [
        "<div align='center'>",
        "",
        "# 🦄 Sing-box Rule Sets Collection",
        "",
        " ".join(badges),
        "",
        "**自动化构建 · 每日更新 · 全球加速**",
        "",
        f"`最后更新于: {update_time} (北京时间)`",
        "",
        "</div>",
        "",
        "## ✨ 简介",
        "本项目旨在提供 **高质量、高可用** 的 Sing-box 规则集。通过 GitHub Actions 定时从上游同步规则，并编译为二进制 (`.srs`) 格式，专为低性能设备和追求极致速度的用户设计。",
        "",
        "> 💡 **提示**: 移动端或部分网络环境也是可以直接访问下方加速链接的。",
        "",
        "<details>",
        "<summary><h3>🛠️ 如何在 Sing-box 中使用 (配置示例)</h3></summary>",
        "",
        "在你的 Sing-box `config.json` 的 `route` 部分配置如下：",
        "",
        "```json",
        "{",
        '  "route": {',
        '    "rule_set": [',
        '      {',
        '        "type": "remote",',
        '        "tag": "geosite-google",',
        '        "format": "binary",',
        '        "url": "请复制下方表格中的【🚀 GhProxy】链接",',
        '        "download_detour": "select" // 务必确保你有这个出站代理',
        "      }",
        "    ]",
        "  }",
        "}",
        "```",
        "</details>",
        "",
        "---",
        "",
        "## 📂 规则下载列表",
        "",
        "# ⚠️ 移动端请【向左滑动】查看完整下载链接",
        "",
        "| 📁 规则名称 | 🚀 SRS (二进制 / 推荐) | 📄 JSON (文本 / 源码) |",
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
            
            # 1. 处理显示名称 (美化)
            if rel_path:
                # 替换 meta-geo -> Geo 等 (如果需要更高级改名逻辑可以在这写)
                # 这里做个简单的图标展示
                display_name = f"📂 <b>{rel_path}</b><br>└─ 📄 `{file_name}`"
            else:
                display_name = f"📄 **{file_name}**"

            # 2. 生成链接 HTML
            links_json = generate_link_group(repo_slug, path_json, is_srs=False)
            
            # 检查 SRS 是否存在
            srs_abs_path = os.path.join(DIR_SRS, path_srs)
            if os.path.exists(srs_abs_path):
                links_srs = generate_link_group(repo_slug, path_srs, is_srs=True)
            else:
                links_srs = "⚠️ <i>编译失败或未生成</i>"

            # 虽然 Markdown 表格里不能直接换行，但 <br> 标签是有效的
            # 为了表格紧凑，我们允许链接换行，或者保持一行
            content_lines.append(f"| {display_name} | {links_srs} | {links_json} |")
            file_count += 1

    content_lines.append("")
    content_lines.append("---")
    content_lines.append(f"<div align='center'><sub>本项目共包含 {file_count} 个规则集 · 自动构建脚本 Powered by Python</sub></div>")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(content_lines))
    
    print(f"✅ 豪华版 README.md 已生成！")

if __name__ == "__main__":
    generate_markdown()
