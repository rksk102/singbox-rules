import os
from datetime import datetime, timezone, timedelta

# ================= 核心配置 (保持不变) =================
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except:
    BASE_DIR = os.getcwd()

PROJECT_ROOT = os.path.dirname(BASE_DIR) if os.path.basename(BASE_DIR) == "src" else BASE_DIR

DIR_JSON = os.path.join(PROJECT_ROOT, "rules-json")
DIR_SRS = os.path.join(PROJECT_ROOT, "rules-srs")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "README.md")
BRANCH = "main"
REPO = os.getenv("GITHUB_REPOSITORY", "rksk102/singbox-rules") 

LOGO_URL = "https://sing-box.sagernet.org/assets/icon.svg"
BADGE_WIDTH = "120"
# ===================================================

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

# ================= 列表样式逻辑 (严格保持原样) =================

def get_type_badge(filename):
    fname = filename.lower()
    if "ip" in fname and "domain" not in fname:
        return "![IP](https://img.shields.io/badge/IP-CIDR-3498db?style=flat-square)"
    elif "domain" in fname or "site" in fname:
        return "![Domain](https://img.shields.io/badge/DOMAIN-List-9b59b6?style=flat-square)"
    else:
        return "![Rule](https://img.shields.io/badge/RULE-Set-95a5a6?style=flat-square)"

def generate_source_badge(repo, path):
    url = f"https://github.com/{repo}/blob/{BRANCH}/{path}"
    img = "https://img.shields.io/badge/View_Source-181717?style=flat-square&logo=github"
    return f"<div align='center'><a href='{url}'><img src='{img}' width='{BADGE_WIDTH}' alt='Source'></a></div>"

def generate_cdn_badges_vertical(repo, path):
    url_ghproxy = f"https://ghproxy.net/https://raw.githubusercontent.com/{repo}/{BRANCH}/{path}"
    url_kgithub = f"https://raw.kgithub.com/{repo}/{BRANCH}/{path}"
    url_jsdelivr = f"https://cdn.jsdelivr.net/gh/{repo}@{BRANCH}/{path}"

    img_gh = "https://img.shields.io/badge/Install-GhProxy-2ecc71?style=flat-square&logo=rocket"
    img_kg = "https://img.shields.io/badge/Install-KGitHub-orange?style=flat-square&logo=thunder"
    img_js = "https://img.shields.io/badge/Install-jsDelivr-ff5252?style=flat-square&logo=jsdelivr&logoColor=white"

    btn_style = f"width='{BADGE_WIDTH}'" 
    div_style = "margin-bottom: 5px;" 

    html = (
        f"<div align='center'>"
        f"<div style='{div_style}'><a href='{url_ghproxy}'><img src='{img_gh}' {btn_style}></a></div>"
        f"<div style='{div_style}'><a href='{url_kgithub}'><img src='{img_kg}' {btn_style}></a></div>"
        f"<div><a href='{url_jsdelivr}'><img src='{img_js}' {btn_style}></a></div>"
        f"</div>"
    )
    return html

def generate_json_badges_vertical(repo, path):
    url_k = f"https://raw.kgithub.com/{REPO}/{BRANCH}/{path}"
    url_j = f"https://cdn.jsdelivr.net/gh/{REPO}@{BRANCH}/{path}"
    
    img_k = "https://img.shields.io/badge/Mirror-KGitHub-orange?style=flat-square&logo=thunder"
    img_j = "https://img.shields.io/badge/Mirror-jsDelivr-ff5252?style=flat-square&logo=jsdelivr&logoColor=white"

    btn_style = f"width='{BADGE_WIDTH}'" 
    div_style = "margin-bottom: 5px;" 
    
    html = (
        f"<div align='center'>"
        f"<div style='{div_style}'><a href='{url_k}'><img src='{img_k}' {btn_style}></a></div>"
        f"<div><a href='{url_j}'><img src='{img_j}' {btn_style}></a></div>"
        f"</div>"
    )
    return html

# ================= 主生成逻辑 (优化了Header/Config/Footer) =================

def generate_markdown():
    update_time = get_beijing_time()
    
    # 顶部状态徽章
    badge_build = f"https://img.shields.io/github/actions/workflow/status/{REPO}/manager.yml?style=flat-square&logo=github&label=Build"
    badge_stars = f"https://img.shields.io/github/stars/{REPO}?style=flat-square&logo=github&color=yellow"
    
    lines = []

    # ================= 1. 全新设计的 Header =================
    lines.append(f"<div align='center'>")
    lines.append(f"  <a href='https://github.com/{REPO}'>")
    lines.append(f"    <img src='{LOGO_URL}' width='120' height='120' alt='Sing-box Logo'>")
    lines.append(f"  </a>")
    lines.append(f"  <h1 style='margin-top: 10px;'>Sing-box Rule Sets</h1>")
    lines.append(f"  <p style='font-size: 1.1em; color: #666;'>")
    lines.append(f"    🚀 <strong>Automated Build</strong> &middot; ")
    lines.append(f"    🌍 <strong>Global CDN</strong> &middot; ")
    lines.append(f"    📦 <strong>Optimized Binary</strong>")
    lines.append(f"  </p>")
    lines.append(f"  <p>")
    lines.append(f"    <img src='{badge_build}' alt='Build'>")
    lines.append(f"    <img src='{badge_stars}' alt='Stars'>")
    lines.append(f"  </p>")
    lines.append(f"</div>")
    lines.append(f"")

    # ================= 2. 特性栅格 (Feature Grid) =================
    # 这是一个无边框的表格，用来展示特性
    lines.append(f"| ⚡ **Lightning Fast** | 🔄 **Always Up-to-Date** | 🛠️ **Developer Friendly** |")
    lines.append(f"| :---: | :---: | :---: |")
    lines.append(f"| Pre-compiled `.srs` binary rules<br>Low memory & CPU usage | Auto-synced with upstream<br>Every hour updates | Standard JSON format included<br>Ready for secondary dev |")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # ================= 3. 优化后的配置引导 (Config Guide) =================
    lines.append(f"## ⚙️ Configuration Guide")
    lines.append(f"")
    # GitHub 原生 Alert 语法
    lines.append(f"> [!TIP]")
    lines.append(f"> **Quick Start**: Select a rule from the table below, right-click the **[ Install-GhProxy ]** button to copy the link, and paste it into your configuration.")
    lines.append(f"")
    
    lines.append(f"<details>")
    lines.append(f"<summary><strong>📝 Click to expand `config.json` example (点击展开配置模版)</strong></summary>")
    lines.append(f"")
    lines.append(f"```json")
    lines.append(f"{{")
    lines.append(f'  "route": {{')
    lines.append(f'    "rule_set": [')
    lines.append(f"      {{")
    lines.append(f'        "tag": "geosite-google",')
    lines.append(f'        "type": "remote",')
    lines.append(f'        "format": "binary",')
    lines.append(f'        "url": "https://ghproxy.net/...",')
    lines.append(f'        "download_detour": "proxy"')
    lines.append(f"      }}")
    lines.append(f"    ]")
    lines.append(f"  }}")
    lines.append(f"}}")
    lines.append(f"```")
    lines.append(f"</details>")
    lines.append(f"")
    lines.append(f"<br>")

    # ================= Data Collection (不变) =================
    file_data = []
    if os.path.exists(DIR_JSON):
        for root, dirs, files in os.walk(DIR_JSON):
            files.sort()
            rel_dir = os.path.relpath(root, DIR_JSON)
            if rel_dir == ".": rel_dir = ""
            for file in files:
                if not file.endswith(".json"): continue
                name = os.path.splitext(file)[0]
                p_json = os.path.join(rel_dir, file).replace("\\", "/")
                p_srs = os.path.join(rel_dir, f"{name}.srs").replace("\\", "/")
                abs_json = os.path.join(DIR_JSON, p_json)
                abs_srs = os.path.join(DIR_SRS, p_srs)
                file_data.append({
                    "name": name,
                    "folder": rel_dir,
                    "p_json": p_json, "p_srs": p_srs,
                    "size_json": format_size(abs_json), "size_srs": format_size(abs_srs),
                    "has_srs": os.path.exists(abs_srs)
                })
        file_data.sort(key=lambda x: (x["folder"], x["name"]))

    # ================= SRS SECTION (列表保持原样) =================
    lines.append(f"## 🚀 SRS Binary Rules")
    lines.append(f"")
    columns = f"| Rule Name | Type | Size | <div align='center'>GitHub Source</div> | <div align='center'>CDN Downloads</div> |"
    lines.append(columns)
    lines.append(f"| :--- | :---: | :---: | :---: | :---: |")

    srs_count = 0
    for item in file_data:
        if not item["has_srs"]: continue
        if item["folder"]:
            display_name = f"<span style='font-size:11px;color:#95a5a6'>📂 {item['folder']} /</span> <b>{item['name']}</b>"
        else:
            display_name = f"<b>{item['name']}</b>"
        badge_type = get_type_badge(item["name"])
        size = f"`{item['size_srs']}`"
        source_col = generate_source_badge(REPO, item["p_json"])
        cdn_col = generate_cdn_badges_vertical(REPO, item["p_srs"])
        lines.append(f"| {display_name} | {badge_type} | {size} | {source_col} | {cdn_col} |")
        srs_count += 1
    
    lines.append(f"")
    
    # ================= JSON SECTION (列表保持原样) =================
    lines.append(f"## 📄 JSON Source Rules")
    lines.append(f"")
    lines.append(columns)
    lines.append(f"| :--- | :---: | :---: | :---: | :---: |")

    json_count = 0
    for item in file_data:
        if item["folder"]:
            display_name = f"<span style='font-size:11px;color:#95a5a6'>📂 {item['folder']} /</span> <b>{item['name']}</b>"
        else:
            display_name = f"<b>{item['name']}</b>"
        badge_type = get_type_badge(item["name"])
        source_col = generate_source_badge(REPO, item["p_json"])
        cdn_col = generate_json_badges_vertical(REPO, item["p_json"])
        lines.append(f"| {display_name} | {badge_type} | `{item['size_json']}` | {source_col} | {cdn_col} |")
        json_count += 1

    # ================= 4. 美化后的 Footer =================
    lines.append(f"")
    lines.append(f"<br>")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"<div align='center'>")
    lines.append(f"  <p><strong>📊 Statistics</strong>: SRS Files: <code>{srs_count}</code> | JSON Files: <code>{json_count}</code></p>")
    lines.append(f"  <p>🕒 Last Updated: <code>{update_time} (Beijing Time)</code></p>")
    lines.append(f"  <p><a href='#sing-box-rule-sets'>🔼 Back to Top</a></p>")
    lines.append(f"  <br>")
    lines.append(f"  <sub>Built with ❤️ by <a href='https://github.com/{REPO}'>GitHub Actions</a></sub>")
    lines.append(f"</div>")

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"✅ README Updated: Layout optimized (Header/Features/Footer).")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_markdown()
