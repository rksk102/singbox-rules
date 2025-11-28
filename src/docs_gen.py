import os
from datetime import datetime, timezone, timedelta

# ================= 核心配置 (Configuration) =================
# 路径自动识别
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except:
    BASE_DIR = os.getcwd()

PROJECT_ROOT = os.path.dirname(BASE_DIR) if os.path.basename(BASE_DIR) == "src" else BASE_DIR

DIR_JSON = os.path.join(PROJECT_ROOT, "rules-json")
DIR_SRS = os.path.join(PROJECT_ROOT, "rules-srs")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "README.md")
BRANCH = "main"
REPO = os.getenv("GITHUB_REPOSITORY", "rksk102/singbox-rules") # 默认值可修改

# Logo 图片 (Sing-box 官方图标)
LOGO_URL = "https://sing-box.sagernet.org/assets/icon.svg"

# ================= 样式生成函数 =================

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
    """
    生成极简风格的类型徽章
    """
    fname = filename.lower()
    # 使用 Shields.io 静态徽章，保证视觉一致性，不会因为 CSS 被过滤而变丑
    if "ip" in fname and "domain" not in fname:
        return "![IP](https://img.shields.io/badge/IP-CIDR-3498db?style=flat-square)"
    elif "domain" in fname or "site" in fname:
        return "![Domain](https://img.shields.io/badge/DOMAIN-List-9b59b6?style=flat-square)"
    else:
        return "![Rule](https://img.shields.io/badge/RULE-Set-95a5a6?style=flat-square)"

def generate_download_badges(repo, path, branch, is_srs=True):
    """
    生成下载按钮组，强制使用 &emsp; 分隔
    """
    # 1. 定义 URL 模板
    url_ghproxy = f"https://ghproxy.net/https://raw.githubusercontent.com/{repo}/{branch}/{path}"
    url_kgithub = f"https://raw.kgithub.com/{repo}/{branch}/{path}"
    # url_jsdelivr = f"https://cdn.jsdelivr.net/gh/{repo}@{branch}/{path}"
    url_raw = f"https://raw.githubusercontent.com/{repo}/{branch}/{path}"

    # 2. 定义徽章图片 (Badge Images)
    # 主按钮：绿色，显著
    img_main = "https://img.shields.io/badge/🚀_Fast_Install-GhProxy-2ecc71?style=flat-square" 
    # 备用按钮：灰色/橙色，扁平
    img_kgh = "https://img.shields.io/badge/KGitHub-orange?style=flat-square"
    img_raw = "https://img.shields.io/badge/Source-black?style=flat-square&logo=github"

    # 3. 组装 HTML (关键：使用 &nbsp; 或 &emsp; 进行强制分隔)
    if is_srs:
        # SRS 布局：上面大按钮，下面小按钮
        html = (
            f"<div align='center'>"
            f"<a href='{url_ghproxy}'><img src='{img_main}' height='25'></a>" # 主按钮加大一点
            f"<br>"
            f"<div style='margin-top: 5px;'>" # 垂直间距
            f"<a href='{url_kgithub}'><img src='{img_kgh}'></a>"
            f"&emsp;" # <--- 强制水平间距 (约两个空格宽)
            f"<a href='{url_raw}'><img src='{img_raw}'></a>"
            f"</div>"
            f"</div>"
        )
    else:
        # JSON 布局：单行排列
        html = (
            f"<div align='center'>"
            f"<a href='{url_raw}'><img src='{img_raw}'></a>"
            f"&emsp;" # 强制间距
            f"<a href='{url_kgithub}'><img src='{img_kgh}'></a>"
            f"</div>"
        )
    return html

def generate_markdown():
    update_time = get_beijing_time()
    
    # 顶部统计徽章
    badge_build = f"https://img.shields.io/github/actions/workflow/status/{REPO}/manager.yml?style=flat-square&logo=github"
    badge_last_update = f"https://img.shields.io/badge/Updated-{update_time.replace(' ', '_')}-blue?style=flat-square"
    
    lines = []

    # ================= 1. 现代化 Header (极简风格) =================
    lines.append(f"<div align='center'>")
    lines.append(f"<img src='{LOGO_URL}' width='100' alt='Sing-box Logo'>")
    lines.append(f"<h1>Sing-box Rule Sets</h1>")
    lines.append(f"<p><strong>Automated Build & Sync Service</strong></p>")
    lines.append(f"<p>{badge_build} {badge_last_update}</p>")
    lines.append(f"</div>")
    lines.append(f"")
    
    # 插入折叠的配置说明 (避免占用太多视觉空间)
    lines.append(f"<details>")
    lines.append(f"<summary><strong>🛠️ Click to view <code>config.json</code> setup config (点击查看配置示例)</strong></summary>")
    lines.append(f"")
    lines.append(f"```json")
    lines.append(f"{{")
    lines.append(f'  "route": {{')
    lines.append(f'    "rule_set": [')
    lines.append(f"      {{")
    lines.append(f'        "tag": "geosite-example",')
    lines.append(f'        "type": "remote",')
    lines.append(f'        "format": "binary",')
    lines.append(f'        "url": "Paste the GhProxy Link here (粘贴下方的加速链接)",')
    lines.append(f'        "download_detour": "proxy" ')
    lines.append(f"      }}")
    lines.append(f"    ]")
    lines.append(f"  }}")
    lines.append(f"}}")
    lines.append(f"```")
    lines.append(f"</details>")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # ================= 数据收集 =================
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
                    "folder": rel_dir, # 文件夹名，用作分类
                    "p_json": p_json,
                    "p_srs": p_srs,
                    "size_json": format_size(abs_json),
                    "size_srs": format_size(abs_srs),
                    "has_srs": os.path.exists(abs_srs)
                })
        # 排序：先按文件夹排，再按文件名排
        file_data.sort(key=lambda x: (x["folder"], x["name"]))

    # ================= 2. SRS 列表 (优化版) =================
    lines.append(f"## 🚀 SRS Binary Rules")
    # 表头样式优化：居中对齐
    lines.append(f"| Category / Name | Type | Size | <div align='center'>Fast Download & Mirrors</div> |")
    lines.append(f"| :--- | :---: | :---: | :---: |")

    srs_count = 0
    for item in file_data:
        if not item["has_srs"]: continue
        
        # 名称列：优化层级显示
        if item["folder"]:
            # 文件夹加粗，文件名代码样式
            display_name = f"**{item['folder']}** / `{item['name']}`"
        else:
            display_name = f"`{item['name']}`"
        
        # 类型徽章
        badge_type = get_type_badge(item["name"])
        
        # 下载列
        action_html = generate_download_badges(REPO, item["p_srs"], BRANCH, is_srs=True)

        lines.append(f"| {display_name} | {badge_type} | `{item['size_srs']}` | {action_html} |")
        srs_count += 1
    
    lines.append(f"")
    lines.append(f"")

    # ================= 3. JSON 列表 (优化版) =================
    lines.append(f"## 📄 JSON Source Rules")
    lines.append(f"| Category / Name | Type | Size | <div align='center'>Source Code</div> |")
    lines.append(f"| :--- | :---: | :---: | :---: |")

    json_count = 0
    for item in file_data:
        if item["folder"]:
            display_name = f"**{item['folder']}** / `{item['name']}`"
        else:
            display_name = f"`{item['name']}`"
            
        badge_type = get_type_badge(item["name"])
        action_html = generate_download_badges(REPO, item["p_json"], BRANCH, is_srs=False)

        lines.append(f"| {display_name} | {badge_type} | `{item['size_json']}` | {action_html} |")
        json_count += 1

    # ================= Footer =================
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"<div align='center'>")
    lines.append(f"<p><sub>Powered by GitHub Actions · Generated at {update_time}</sub></p>")
    lines.append(f"</div>")

    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"✅ Markdown Generated: SRS[{srs_count}] / JSON[{json_count}]")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    generate_markdown()
