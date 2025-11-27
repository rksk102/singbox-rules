import os
from datetime import datetime, timezone, timedelta

# ================= 配置区域 =================
BRANCH = "main"
OUTPUT_FILE = "README.md"
DIR_JSON = "./rules-json"
DIR_SRS = "./rules-srs"

# 修复 Logo: 使用 Sing-box 官网的 Logo 资源
LOGO_URL = "https://sing-box.sagernet.org/assets/icon.svg"

def get_beijing_time():
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
    return bj_dt.strftime("%Y-%m-%d %H:%M")

def create_button_group(repo, branch, file_path):
    """保留你喜欢的按钮样式"""
    raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"
    url_ghproxy = f"https://ghproxy.net/{raw_url}"
    url_gitmirror = f"https://raw.gitmirror.com/{repo}/{branch}/{file_path}"
    
    html = (
        f"<a href='{url_ghproxy}'><code>🚀 GhProxy</code></a>&nbsp;" 
        f"<a href='{url_gitmirror}'><code>🛸 Mirror</code></a><br>"
        f"<a href='{raw_url}' style='font-size:12px; color: #8b949e;'>Original Source</a>"
    )
    return html

def generate_markdown():
    repo_slug = os.getenv("GITHUB_REPOSITORY", "User/Repo")
    update_time = get_beijing_time()

    # 徽章 (使用 unified 风格)
    badges = [
        f"![Build](https://img.shields.io/github/actions/workflow/status/{repo_slug}/manager.yml?style=flat-square&logo=github&label=Build&color=2ea44f)",
        f"![Size](https://img.shields.io/github/repo-size/{repo_slug}?style=flat-square&label=Size&color=0969da)",
        f"![License](https://img.shields.io/github/license/{repo_slug}?style=flat-square&color=orange)"
    ]

    content_lines = [
        # --- 头部 Hero 区域 ---
        f"<div align='center'>",
        f"",
        f"<img src='{LOGO_URL}' width='120' height='120' alt='Logo'>",
        f"",
        f"# Sing-box Rule Sets",
        f"",
        f"{' '.join(badges)}",
        f"",
        f"<h3>🚀 专为 Sing-box 打造的自动化规则仓库</h3>",
        f"<p style='color: #57606a;'>每日自动拉取上游资源 • 编译二进制 SRS • 全球 CDN 加速</p>",
        f"",
        f"</div>",
        f"",
        # --- 仪表盘特性区 (表格布局) ---
        f"| 🤖 **全自动维护** | 🏎️ **极速下载** | 🛡️ **多格式兼容** |",
        f"| :---: | :---: | :---: |",
        f"| 每小时通过 Actions<br>自动同步上游源 | 集成 `GhProxy` 等<br>国内高速镜像 | 提供 **Pre-complied SRS**<br>与原始 JSON |",
        f"",
        f"---",
        f"",
        # --- 使用说明区 ---
        f"## ⚙️ 配置指南",
        f"",
        f"> 💡 **新手提示**: 推荐使用二进制规则集 (`.srs`)，加载速度更快，内存占用更有优势。",
        f"",
        f"<details>",
        f"<summary><strong>📝 点击展开 `config.json` 参考配置</strong></summary>",
        f"",
        f"请复制下方表格中 `🚀 GhProxy` 按钮对应的链接，填入 `url` 字段：",
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
        f'        "download_detour": "proxy-out" // ⚠️ 确保你有这个出站 tag',
        f"      }}",
        f"    ]",
        f"  }}",
        f"}}",
        f"```",
        f"</details>",
        f"",
        f"---",
        f"",
        # --- 规则列表区 ---
        f"## 📥 规则下载汇编",
        f"",
        f"<div align='right'>📅 <strong>最后更新:</strong> {update_time} (北京时间)</div>",
        f"",
        f"| 规则集名称 (Name) | 🚀 SRS (二进制) | 📄 JSON (源码) |",
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
            
            # --- 美化名称显示 ---
            # 使用 HTML 标签控制颜色和大小
            if rel_path:
                # 文件夹用灰色，文件名用加粗黑色/白色
                display_name = f"<span style='color: #57606a; font-size: 0.85em;'>📂 {rel_path} /</span><br><strong>{file_name}</strong>"
            else:
                display_name = f"<strong>{file_name}</strong>"

            html_json = create_button_group(repo_slug, BRANCH, path_json)
            
            srs_abs_path = os.path.join(DIR_SRS, path_srs)
            if os.path.exists(srs_abs_path):
                html_srs = create_button_group(repo_slug, BRANCH, path_srs)
            else:
                html_srs = "<span style='color: #cf222e;'>⚠️ Missing</span>"

            content_lines.append(f"| {display_name} | {html_srs} | {html_json} |")
            file_count += 1

    content_lines.append("")
    content_lines.append("<br>")
    content_lines.append(f"<div align='center'><sub>Crafted with ❤️ by GitHub Actions · Total {file_count} Rules</sub></div>")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(content_lines))
    
    print(f"✅ 终极美化版 README 已生成")

if __name__ == "__main__":
    generate_markdown()
