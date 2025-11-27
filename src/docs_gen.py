import os
from datetime import datetime, timezone, timedelta

# ================= 配置 =================
DIR_JSON = "./rules-json"
DIR_SRS = "./rules-srs"
DIR_TXT = "./rules-txt" # 仅用于辅助检查，可忽略
BRANCH = "main"
OUTPUT_FILE = "README.md"
LOGO_URL = "https://sing-box.sagernet.org/assets/icon.svg"
# =======================================

def get_beijing_time():
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
    return bj_dt.strftime("%Y-%m-%d %H:%M")

def format_size(path):
    if not os.path.exists(path): return "-"
    size = os.path.getsize(path)
    if size < 1024: return f"{size} B"
    if size < 1024 * 1024: return f"{size/1024:.1f} KB"
    return f"{size/(1024*1024):.2f} MB"

def get_tags(filename):
    """生成精致的类型标签"""
    fname = filename.lower()
    # 标签样式：使用 HTML span 实现胶囊效果
    style_base = "display:inline-block; padding:1px 6px; border-radius:4px; font-size:10px; font-weight:600; border:1px solid"
    
    if "ip" in fname and "domain" not in fname:
        # 蓝色边框 + 蓝色文字
        return f"<span style='{style_base} #2196f3; color:#2196f3; background:#e3f2fd;'>IP-CIDR</span>"
    elif "domain" in fname or "site" in fname:
        # 紫色边框 + 紫色文字
        return f"<span style='{style_base} #9c27b0; color:#9c27b0; background:#f3e5f5;'>DOMAIN</span>"
    
    # 默认灰色
    return f"<span style='{style_base} #9e9e9e; color:#757575; background:#f5f5f5;'>RULE</span>"

def generate_markdown():
    repo = os.getenv("GITHUB_REPOSITORY", "User/Repo")
    update_time = get_beijing_time()

    # Header 区域
    lines = [
        f"<div align='center'>",
        f"<img src='{LOGO_URL}' width='80' alt='Logo'>",
        f"<h1>Sing-box Rule Sets</h1>",
        f"<p>Daily Updates · Multi-Mirror · High Performance</p>",
        f"</div>",
        f"",
        f"---",
        f"",
        f"### ⚡ 快速配置 (Quick Start)",
        f"<details>",
        f"<summary><strong>点击展开 `config.json` 能够使用的代码段</strong></summary>",
        f"",
        f"```json",
        f"{{",
        f'  "route": {{',
        f'    "rule_set": [',
        f"      {{",
        f'        "type": "remote",',
        f'        "tag": "rule-tag",',
        f'        "format": "binary",',
        f'        "url": "https://ghproxy.net/https://raw.githubusercontent.com/{repo}/{BRANCH}/rules-srs/geosite-google.srs",',
        f'        "download_detour": "proxy"',
        f"      }}",
        f"    ]",
        f"  }}",
        f"}}",
        f"```",
        f"</details>",
        f"",
        f"### 📦 规则列表 (Rules Collection)",
        f"<div align='right'>📅 Last Update: <code>{update_time}</code></div>",
        f"",
        f"| 规则名称 (Name) | 类型 (Type) | 大小 (Size) | 下载通道 (Download) |",
        f"| :--- | :--- | :--- | :--- |"
    ]

    count = 0
    if not os.path.exists(DIR_JSON): return

    # 获取文件列表并包含目录信息
    file_list = []
    for root, dirs, files in os.walk(DIR_JSON):
        files.sort()
        rel_path = os.path.relpath(root, DIR_JSON)
        if rel_path == ".": rel_path = ""

        for file in files:
            if not file.endswith(".json"): continue
            file_list.append((rel_path, file))
    
    # 排序：先按目录排，目录内按文件名排
    file_list.sort(key=lambda x: (x[0], x[1]))

    for rel_path, file in file_list:
        name = os.path.splitext(file)[0]
        
        # 路径相关
        p_json = os.path.join(rel_path, file).replace("\\", "/")
        p_srs = os.path.join(rel_path, f"{name}.srs").replace("\\", "/")
        srs_abs = os.path.join(DIR_SRS, p_srs)
        
        # 1. Name 列: 强化结构感
        # 如果有子目录，用灰色小字显示目录
        if rel_path:
            display_name = f"<span style='color:#8395a7;font-size:11px'>📂 {rel_path} /</span><br><strong>{name}</strong>"
        else:
            display_name = f"<strong>{name}</strong>"

        # 2. Type 列
        tag_html = get_tags(name)

        # 3. Size 列
        size_str = format_size(srs_abs)
        size_html = f"<code>{size_str}</code>" if os.path.exists(srs_abs) else "-"

        # 4. Download 列 (核心 UI 优化)
        raw_base = f"https://raw.githubusercontent.com/{repo}/{BRANCH}"
        
        # 链接定义
        link_ghproxy = f"https://ghproxy.net/{raw_base}/{p_srs}"
        link_mirror = f"https://raw.gitmirror.com/{repo}/{BRANCH}/{p_srs}"
        link_raw = f"{raw_base}/{p_srs}"
        link_source = f"{raw_base}/{p_json}"

        if os.path.exists(srs_abs):
            # HTML 样式按钮
            # 第一行：主要下载按钮 (GhProxy)
            # 第二行：备用链接 + 源码链接 (小字)
            action_html = (
                f"<a href='{link_ghproxy}'>"
                f"<img src='https://img.shields.io/badge/🚀_Fast_Download-GhProxy-009688?style=flat-square&logo=rocket' alt='Download'>"
                f"</a><br>"
                f"<span style='font-size:11px; color:gray;'>"
                f"<a href='{link_mirror}'>CDN Mirror</a> • "
                f"<a href='{link_raw}'>Raw SRS</a> • "
                f"<a href='{link_source}'>Source</a>"
                f"</span>"
            )
        else:
            action_html = "⚠️ Compile Failed"

        lines.append(f"| {display_name} | {tag_html} | {size_html} | {action_html} |")
        count += 1

    lines.append("")
    lines.append("---")
    lines.append(f"<div align='center'><sub>Total {count} rules · Automated by GitHub Actions</sub></div>")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("✅ 现代版 README 已生成")

if __name__ == "__main__":
    generate_markdown()
