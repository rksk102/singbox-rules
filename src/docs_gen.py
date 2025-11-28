import os
from datetime import datetime, timezone, timedelta

# ================= 核心配置 =================
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
# ===========================================

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

def get_type_badge(filename):
    """类型徽章"""
    fname = filename.lower()
    if "ip" in fname and "domain" not in fname:
        return "![IP](https://img.shields.io/badge/IP-CIDR-3498db?style=flat-square)"
    elif "domain" in fname or "site" in fname:
        return "![Domain](https://img.shields.io/badge/DOMAIN-List-9b59b6?style=flat-square)"
    else:
        return "![Rule](https://img.shields.io/badge/RULE-Set-95a5a6?style=flat-square)"

def generate_source_badge(repo, path):
    """
    第四列：单独的 GitHub 源文件链接
    """
    url = f"https://github.com/{repo}/blob/{BRANCH}/{path}"
    # 黑色徽章，代表 Github 官方
    img = "https://img.shields.io/badge/View_Source-181717?style=flat-square&logo=github"
    return f"<div align='center'><a href='{url}'><img src='{img}'></a></div>"

def generate_cdn_badges(repo, path):
    """
    第五列：CDN 加速下载组 (GhProxy + KGitHub + jsDelivr)
    """
    # URL 定义
    url_ghproxy = f"https://ghproxy.net/https://raw.githubusercontent.com/{repo}/{BRANCH}/{path}"
    url_kgithub = f"https://raw.kgithub.com/{repo}/{BRANCH}/{path}"
    url_jsdelivr = f"https://cdn.jsdelivr.net/gh/{repo}@{BRANCH}/{path}"

    # 徽章图片
    # 1. GhProxy (主): 绿色
    img_main = "https://img.shields.io/badge/🚀_Fast_Install-GhProxy-2ecc71?style=flat-square"
    # 2. KGitHub (备): 橙色
    img_kgh = "https://img.shields.io/badge/KGitHub-orange?style=flat-square"
    # 3. jsDelivr (备): 红色
    img_jsd = "https://img.shields.io/badge/jsDelivr-ft5252?style=flat-square&logo=jsdelivr&logoColor=white"

    # 布局构造：
    # 第一行：GhProxy (大)
    # 第二行：KGitHub + jsDelivr (并在中间加宽间距)
    html = (
        f"<div align='center'>"
        f"<a href='{url_ghproxy}'><img src='{img_main}' height='24'></a>" #稍微高一点突显主次
        f"<br>"
        f"<div style='margin-top: 6px;'>" # 垂直间距
        f"<a href='{url_kgithub}'><img src='{img_kgh}'></a>"
        f"&emsp;" # <--- 关键：全角空格，强制水平间距
        f"<a href='{url_jsdelivr}'><img src='{img_jsd}'></a>"
        f"</div>"
        f"</div>"
    )
    return html

def generate_markdown():
    update_time = get_beijing_time()
    
    badge_build = f"https://img.shields.io/github/actions/workflow/status/{REPO}/manager.yml?style=flat-square&logo=github"
    badge_repo_size = f"https://img.shields.io/github/repo-size/{REPO}?style=flat-square&color=orange"
    
    lines = []

    # ================= Header =================
    lines.append(f"<div align='center'>")
    lines.append(f"<img src='{LOGO_URL}' width='100' alt='Sing-box Logo'>")
    lines.append(f"<h1>Sing-box Rule Sets</h1>")
    lines.append(f"<p>{badge_build} {badge_repo_size}</p>")
    lines.append(f"<p>Updated: <code>{update_time} (Beijing Time)</code></p>")
    lines.append(f"</div>")
    lines.append(f"")
    
    lines.append(f"<details>")
    lines.append(f"<summary><strong>🛠️ <code>config.json</code> Configuration Example (配置示例)</strong></summary>")
    lines.append(f"")
    lines.append(f"```json")
    lines.append(f"{{")
    lines.append(f'  "route": {{')
    lines.append(f'    "rule_set": [')
    lines.append(f"      {{")
    lines.append(f'        "tag": "geosite-example",')
    lines.append(f'        "type": "remote",')
    lines.append(f'        "format": "binary",')
    lines.append(f'        "url": "Paste the GhProxy Link here (复制表格中的加速链接)",')
    lines.append(f'        "download_detour": "proxy"')
    lines.append(f"      }}")
    lines.append(f"    ]")
    lines.append(f"  }}")
    lines.append(f"}}")
    lines.append(f"```")
    lines.append(f"</details>")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # ================= Data Collection =================
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
                    "p_json": p_json,
                    "p_srs": p_srs,
                    "size_json": format_size(abs_json),
                    "size_srs": format_size(abs_srs),
                    "has_srs": os.path.exists(abs_srs)
                })
        file_data.sort(key=lambda x: (x["folder"], x["name"]))

    # ================= SRS SECTION =================
    lines.append(f"## 🚀 SRS Binary Rules")
    lines.append(f"> Recommended for Sing-box. Optimized binary format.")
    lines.append(f"")
    # 5 列结构
    lines.append(f"| Rule Name | Type | Size | <div align='center'>GitHub Source</div> | <div align='center'>CDN Downloads</div> |")
    lines.append(f"| :--- | :---: | :---: | :---: | :---: |")

    srs_count = 0
    for item in file_data:
        if not item["has_srs"]: continue
        
        # Col 1: Name
        if item["folder"]:
            display_name = f"**{item['folder']}** / `{item['name']}`"
        else:
            display_name = f"`{item['name']}`"
        
        # Col 2: Type Badge
        badge_type = get_type_badge(item["name"])
        
        # Col 3: Size
        size = f"`{item['size_srs']}`"
        
        # Col 4: Source Badge (Independent)
        # 这里指向 .json 源码，因为 SRS 是二进制没法看
        source_col = generate_source_badge(REPO, item["p_json"])
        
        # Col 5: CDN Badges (SRS)
        cdn_col = generate_cdn_badges(REPO, item["p_srs"])

        lines.append(f"| {display_name} | {badge_type} | {size} | {source_col} | {cdn_col} |")
        srs_count += 1
    
    lines.append(f"")
    
    # ================= JSON SECTION =================
    lines.append(f"## 📄 JSON Source Rules")
    lines.append(f"| Rule Name | Type | Size | <div align='center'>GitHub Source</div> | <div align='center'>CDN Mirror</div> |")
    lines.append(f"| :--- | :---: | :---: | :---: | :---: |")

    json_count = 0
    for item in file_data:
        if item["folder"]:
            display_name = f"**{item['folder']}** / `{item['name']}`"
        else:
            display_name = f"`{item['name']}`"
            
        badge_type = get_type_badge(item["name"])
        
        # Col 4: Source Link
        source_col = generate_source_badge(REPO, item["p_json"])
        
        # Col 5: CDN for JSON
        # JSON 不需要 "Install" 按钮，我们提供简单的镜像 Raw 链接
        url_k = f"https://raw.kgithub.com/{REPO}/{BRANCH}/{item['p_json']}"
        url_j = f"https://cdn.jsdelivr.net/gh/{REPO}@{BRANCH}/{item['p_json']}"
        img_k = "https://img.shields.io/badge/KGitHub-orange?style=flat-square"
        img_j = "https://img.shields.io/badge/jsDelivr-red?style=flat-square&logo=jsdelivr&logoColor=white"
        
        cdn_col = (
            f"<div align='center'>"
            f"<a href='{url_k}'><img src='{img_k}'></a>"
            f"&emsp;"
            f"<a href='{url_j}'><img src='{img_j}'></a>"
            f"</div>"
        )

        lines.append(f"| {display_name} | {badge_type} | `{item['size_json']}` | {source_col} | {cdn_col} |")
        json_count += 1

    # ================= Footer =================
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"<div align='center'>")
    lines.append(f"<p><sub>SRS Files: {srs_count} | JSON Files: {json_count}</sub></p>")
    lines.append(f"</div>")

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"✅ README Updated: 5-Column Layout with jsDelivr.")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_markdown()
