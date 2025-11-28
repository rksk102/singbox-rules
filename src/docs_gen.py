import os
from datetime import datetime, timezone, timedelta

# ================= 配置区域 (Configuration) =================
DIR_JSON = "./rules-json"
DIR_SRS = "./rules-srs"
BRANCH = "main"
OUTPUT_FILE = "README.md"
LOGO_URL = "https://sing-box.sagernet.org/assets/icon.svg"

# 定义加速镜像源 (可以按需添加)
# {repo} 会自动替换为 "用户名/仓库名", {branch} 为分支, {path} 为文件路径
CDN_PROVIDERS = [
    {
        "name": "GhProxy",
        "url": "https://ghproxy.net/https://raw.githubusercontent.com/{repo}/{branch}/{path}",
        "badge": "https://img.shields.io/badge/Download-GhProxy-009688?style=flat-square&logo=rocket"
    },
    {
        "name": "KGitHub",
        "url": "https://raw.kgithub.com/{repo}/{branch}/{path}",
        "badge": "https://img.shields.io/badge/Download-KGitHub-orange?style=flat-square&logo=thunder"
    },
    {
        "name": "JSDelivr",
        "url": "https://cdn.jsdelivr.net/gh/{repo}@{branch}/{path}",
        "badge": "https://img.shields.io/badge/Download-JSDelivr-ff5252?style=flat-square&logo=jsdelivr"
    },
    {
        "name": "GitHub Raw",
        "url": "https://raw.githubusercontent.com/{repo}/{branch}/{path}",
        "badge": "https://img.shields.io/badge/Source-GitHub_Raw-181717?style=flat-square&logo=github"
    }
]
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

def get_tags(filename):
    fname = filename.lower()
    style_base = "display:inline-block; padding:1px 6px; border-radius:4px; font-size:10px; font-weight:600; border:1px solid"
    if "ip" in fname and "domain" not in fname:
        return f"<span style='{style_base} #2196f3; color:#2196f3; background:#e3f2fd;'>IP-CIDR</span>"
    elif "domain" in fname or "site" in fname:
        return f"<span style='{style_base} #9c27b0; color:#9c27b0; background:#f3e5f5;'>DOMAIN</span>"
    return f"<span style='{style_base} #9e9e9e; color:#757575; background:#f5f5f5;'>RULE</span>"

def generate_links_html(repo, path):
    """生成多个 CDN 的下载链接徽章"""
    links = []
    for cdn in CDN_PROVIDERS:
        url = cdn["url"].format(repo=repo, branch=BRANCH, path=path)
        # 使用 HTML a 标签包裹 shields.io 图片
        link_html = f"<a href='{url}' title='{cdn['name']}'><img src='{cdn['badge']}' alt='{cdn['name']}'></a>"
        links.append(link_html)
    return "<br>".join(links)

def generate_markdown():
    repo = os.getenv("GITHUB_REPOSITORY", "User/Repo")
    update_time = get_beijing_time()
    
    badge_build = f"https://img.shields.io/github/actions/workflow/status/{repo}/manager.yml?style=flat-square&logo=github&label=Build"
    badge_size = f"https://img.shields.io/github/repo-size/{repo}?style=flat-square&label=Repo%20Size&color=orange"
    badge_last = f"https://img.shields.io/badge/Updated-{update_time.replace(' ', '%20')}-blue?style=flat-square&logo=time"

    lines = []

    # --- Header ---
    lines.append(f"<div align='center'>")
    lines.append(f"<a href='https://github.com/{repo}'><img src='{LOGO_URL}' width='100' height='100' alt='Logo'></a>")
    lines.append(f"<h1>Sing-box Rule Sets</h1>")
    lines.append(f"<p>{badge_build} {badge_size} {badge_last}</p>")
    lines.append(f"<p>自动构建 · 全球加速 · 格式分离</p>")
    lines.append(f"</div>")
    lines.append(f"")
    
    lines.append(f"| 🚀 **SRS Binary** | 📄 **JSON Source** | ⚙️ **Auto Build** |")
    lines.append(f"| :---: | :---: | :---: |")
    lines.append(f"| 预编译二进制格式<br>加载极快，省内存 | 标准 Source 格式<br>可读性强，方便编辑 | 每小时同步上游<br>自动生成多 CDN 链接 |")
    lines.append(f"")
    
    # --- Data Collection ---
    file_data = [] # 存储所有文件信息的列表
    if os.path.exists(DIR_JSON):
        for root, dirs, files in os.walk(DIR_JSON):
            files.sort()
            rel_path = os.path.relpath(root, DIR_JSON)
            if rel_path == ".": rel_path = ""
            for file in files:
                if not file.endswith(".json"): continue
                
                name = os.path.splitext(file)[0]
                p_json = os.path.join(rel_path, file).replace("\\", "/") # json 相对路径
                p_srs = os.path.join(rel_path, f"{name}.srs").replace("\\", "/") # srs 相对路径
                
                abs_json = os.path.join(DIR_JSON, p_json)
                abs_srs = os.path.join(DIR_SRS, p_srs)
                
                file_data.append({
                    "name": name,
                    "folder": rel_path,
                    "rel_json": p_json,
                    "rel_srs": p_srs,
                    "abs_json": abs_json,
                    "abs_srs": abs_srs,
                    "has_srs": os.path.exists(abs_srs)
                })
        # 排序
        file_data.sort(key=lambda x: (x["folder"], x["name"]))

    # --- SECTION 1: SRS 列表 ---
    lines.append(f"## 🚀 SRS Binary Rules (Recommended)")
    lines.append(f"> [!TIP]")
    lines.append(f"> **SRS (Sing-box Rule Set)** 是编译后的二进制格式，推荐在 Sing-box 客户端直接使用。")
    lines.append(f"")
    lines.append(f"| Name | Tags | Size | Download Mirrors (Multi-CDN) |")
    lines.append(f"| :--- | :--- | :--- | :--- |")
    
    srs_count = 0
    for item in file_data:
        if not item["has_srs"]: continue
        
        # 名字展示
        display_name = f"<strong>{item['name']}</strong>"
        if item["folder"]:
            display_name = f"<span style='color:#8395a7;font-size:11px'>{item['folder']} /</span><br>{display_name}"
            
        tags = get_tags(item["name"])
        size = format_size(item["abs_srs"])
        links = generate_links_html(repo, item["rel_srs"]) # 生成 SRS 链接
        
        lines.append(f"| {display_name} | {tags} | <code>{size}</code> | {links} |")
        srs_count += 1

    lines.append(f"") 
    lines.append(f"---")
    lines.append(f"")

    # --- SECTION 2: JSON 列表 ---
    lines.append(f"## 📄 JSON Source Rules")
    lines.append(f"> [!NOTE]")
    lines.append(f"> JSON 格式适合阅读规则内容或用于不支持 SRS 的旧版本环境。")
    lines.append(f"")
    lines.append(f"| Name | Tags | Size | Source Links |")
    lines.append(f"| :--- | :--- | :--- | :--- |")
    
    json_count = 0
    for item in file_data:
        # 名字展示
        display_name = f"<strong>{item['name']}</strong>"
        if item["folder"]:
            display_name = f"<span style='color:#8395a7;font-size:11px'>{item['folder']} /</span><br>{display_name}"
            
        tags = get_tags(item["name"])
        size = format_size(item["abs_json"]) # 计算 JSON 文件大小
        links = generate_links_html(repo, item["rel_json"]) # 生成 JSON 链接
        
        lines.append(f"| {display_name} | {tags} | <code>{size}</code> | {links} |")
        json_count += 1

    # --- Footer ---
    lines.append(f"")
    lines.append(f"<div align='center'>")
    lines.append(f"<p><strong>Statistics:</strong> {srs_count} SRS Files | {json_count} JSON Files</p>")
    lines.append(f"<p><a href='#sing-box-rule-sets'>🔼 Back to Top</a></p>")
    lines.append(f"<br>")
    lines.append(f"<sub>Generated by GitHub Actions at {update_time}</sub>")
    lines.append(f"</div>")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"✅ 生成完成: {srs_count} SRS, {json_count} JSON")

if __name__ == "__main__":
    generate_markdown()
