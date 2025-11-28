import os
from datetime import datetime, timezone, timedelta

# ================= 配置区域 (Configuration) =================
# 1. 路径自动识别 (兼容 src/ 目录或根目录运行)
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except:
    BASE_DIR = os.getcwd()

PROJECT_ROOT = os.path.dirname(BASE_DIR) if os.path.basename(BASE_DIR) == "src" else BASE_DIR

DIR_JSON = os.path.join(PROJECT_ROOT, "rules-json")
DIR_SRS = os.path.join(PROJECT_ROOT, "rules-srs")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "README.md")
BRANCH = "main"

LOGO_URL = "https://sing-box.sagernet.org/assets/icon.svg"

# ================= 2. 徽章与链接配置 =================
# 可以在这里调整徽章的颜色 (color) 和图标 (logo)
CDN_CONFIG = {
    "ghproxy": {
        "url": "https://ghproxy.net/https://raw.githubusercontent.com/{repo}/{branch}/{path}",
        "badge": "https://img.shields.io/badge/☁_GhProxy-Install-00b894?style=flat-square&logo=rocket"
    },
    "kgithub": {
        "url": "https://raw.kgithub.com/{repo}/{branch}/{path}",
        "badge": "https://img.shields.io/badge/⚡_KGitHub-Orange?style=flat-square&logo=thunder"
    },
    "jsdelivr": {
        "url": "https://cdn.jsdelivr.net/gh/{repo}@{branch}/{path}",
        "badge": "https://img.shields.io/badge/🔴_JSDelivr-Red?style=flat-square&logo=jsdelivr"
    },
    "raw": {
        "url": "https://raw.githubusercontent.com/{repo}/{branch}/{path}",
        "badge": "https://img.shields.io/badge/🏴_GitHub-Source-2d3436?style=flat-square&logo=github"
    }
}
# ==========================================================

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

def get_tag_html(filename):
    """莫兰迪色系标签"""
    fname = filename.lower()
    base_style = "display:inline-block; padding:2px 6px; border-radius:6px; font-size:10px; font-weight:bold; font-family: sans-serif; vertical-align: middle; margin-left: 8px;"
    
    if "ip" in fname and "domain" not in fname:
        return f"<span style='{base_style} color:#0984e3; background:#dff9fb; border:1px solid #74b9ff;'>IP-CIDR</span>"
    elif "domain" in fname or "site" in fname:
        return f"<span style='{base_style} color:#6c5ce7; background:#e0d7ff; border:1px solid #a29bfe;'>DOMAIN</span>"
    else:
        return f"<span style='{base_style} color:#636e72; background:#f1f2f6; border:1px solid #b2bec3;'>RULE</span>"

def make_badge(cdn_key, repo, path):
    """生成带间距的徽章HTML"""
    cfg = CDN_CONFIG[cdn_key]
    url = cfg["url"].format(repo=repo, branch=BRANCH, path=path)
    # margin-right: 4px 用于防止按钮靠太近
    return f"<a href='{url}' style='margin-right: 4px; display:inline-block;'><img src='{cfg['badge']}' alt='{cdn_key}'></a>"

def generate_srs_links(repo, path):
    """SRS 下载列：主次分层布局"""
    # 第一行：主下载 (GhProxy)
    main_btn = make_badge("ghproxy", repo, path)
    
    # 第二行：备用源 (KGitHub, JSDelivr, Raw)
    mirrors = [
        make_badge("kgithub", repo, path),
        make_badge("jsdelivr", repo, path),
        make_badge("raw", repo, path)
    ]
    
    return (
        f"{main_btn}<br>"
        f"<div style='margin-top:4px; white-space:nowrap;'>" # 这一行防止换行并增加上方间距
        f"{''.join(mirrors)}"
        f"</div>"
    )

def generate_json_links(repo, path):
    """JSON 下载列：只需要源码链接"""
    # 对于 JSON，我们提供 GitHub Raw 和 加速查看(KGitHub)
    btn1 = make_badge("raw", repo, path)
    btn2 = make_badge("kgithub", repo, path)
    return f"{btn1} {btn2}"

def generate_markdown():
    repo = os.getenv("GITHUB_REPOSITORY", "User/Repo")
    update_time = get_beijing_time()
    
    badge_build = f"https://img.shields.io/github/actions/workflow/status/{repo}/manager.yml?style=flat-square&logo=github&label=Build"
    badge_size = f"https://img.shields.io/github/repo-size/{repo}?style=flat-square&label=Size&color=orange"
    
    lines = []

    # --- Header ---
    lines.append(f"<div align='center'>")
    lines.append(f"<a href='https://github.com/{repo}'>")
    lines.append(f"<img src='{LOGO_URL}' width='80' height='80' alt='Logo'>")
    lines.append(f"</a>")
    lines.append(f"<h2>Sing-box Rule Sets</h2>")
    lines.append(f"<p>{badge_build} {badge_size}</p>")
    lines.append(f"<p>Automatic Updates · Multi-CDN Support</p>")
    lines.append(f"</div>")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # --- Data Collection ---
    file_data = []
    if os.path.exists(DIR_JSON):
        for root, dirs, files in os.walk(DIR_JSON):
            files.sort()
            rel_dir = os.path.relpath(root, DIR_JSON)
            if rel_dir == ".": rel_dir = ""
            
            for file in files:
                if not file.endswith(".json"): continue
                
                name = os.path.splitext(file)[0]
                # 核心路径逻辑
                p_json = os.path.join(rel_dir, file).replace("\\", "/")
                p_srs = os.path.join(rel_dir, f"{name}.srs").replace("\\", "/")
                
                abs_json = os.path.join(DIR_JSON, p_json)
                abs_srs = os.path.join(DIR_SRS, p_srs)
                
                file_data.append({
                    "name": name,
                    "folder": rel_dir,
                    "rel_json": p_json, # 相对路径用于URL生成
                    "rel_srs": p_srs,   # 相对路径用于URL生成
                    "abs_json": abs_json,
                    "abs_srs": abs_srs,
                    "has_srs": os.path.exists(abs_srs)
                })
        # Sort by folder then name
        file_data.sort(key=lambda x: (x["folder"], x["name"]))

    # --- SECTION 1: SRS Rules ---
    lines.append(f"### 🚀 SRS Binary Rules")
    lines.append(f"> <small>Recommended for Sing-box. Compiled binary format.</small>")
    lines.append(f"")
    lines.append(f"| Rule Set | Size | Download Mirrors (Multi-CDN) |")
    lines.append(f"| :--- | :---: | :--- |")
    
    srs_count = 0
    for item in file_data:
        if not item["has_srs"]: continue
        
        # Name & Tag
        name_display = f"<code>{item['name']}</code>"
        tag_html = get_tag_html(item['name'])
        if item["folder"]:
            display_name = f"<span style='color:#b2bec3;font-size:10px'>📂 {item['folder']} / </span>{name_display} {tag_html}"
        else:
            display_name = f"{name_display} {tag_html}"
            
        # Size
        size_display = format_size(item["abs_srs"])
        
        # Badges
        action_html = generate_srs_links(repo, item["rel_srs"])

        lines.append(f"| {display_name} | {size_display} | {action_html} |")
        srs_count += 1

    lines.append(f"")
    
    # --- SECTION 2: JSON Rules ---
    lines.append(f"### 📄 JSON Source Rules")
    lines.append(f"> <small>Source code format. Useful for editing or non-binary usage.</small>")
    lines.append(f"")
    lines.append(f"| Rule Set | Size | Source View |")
    lines.append(f"| :--- | :---: | :--- |")
    
    json_count = 0
    for item in file_data:
        # Name & Tag (Same logic)
        name_display = f"<code>{item['name']}</code>"
        tag_html = get_tag_html(item['name'])
        if item["folder"]:
            display_name = f"<span style='color:#b2bec3;font-size:10px'>📂 {item['folder']} / </span>{name_display} {tag_html}"
        else:
            display_name = f"{name_display} {tag_html}"
            
        # Size (JSON size)
        size_display = format_size(item["abs_json"])
        
        # Badges (JSON links)
        action_html = generate_json_links(repo, item["rel_json"])

        lines.append(f"| {display_name} | {size_display} | {action_html} |")
        json_count += 1

    # --- Footer ---
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"<div align='center'>")
    lines.append(f"<p><sub style='color:#b2bec3'>Last updated: {update_time} (Beijing Time)</sub></p>")
    lines.append(f"</div>")

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"✅ README Generated: SRS[{srs_count}] / JSON[{json_count}]")
    except Exception as e:
        print(f"❌ Write Error: {e}")

if __name__ == "__main__":
    generate_markdown()
