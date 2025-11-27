import os
from datetime import datetime, timezone, timedelta

# ================= 配置区域 =================
BRANCH = "main"
OUTPUT_FILE = "README.md"
DIR_JSON = "./rules-json"
DIR_SRS = "./rules-srs"
LOGO_URL = "https://sing-box.sagernet.org/assets/icon.svg"

def get_beijing_time():
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
    return bj_dt.strftime("%Y-%m-%d %H:%M")

def get_file_size(path):
    """获取文件大小并格式化为 KB/MB"""
    if not os.path.exists(path): return "0 KB"
    size = os.path.getsize(path)
    if size < 1024:
        return f"{size} B"
    elif size < 1024 * 1024:
        return f"{size / 1024:.1f} KB"
    else:
        return f"{size / (1024 * 1024):.2f} MB"

def get_rule_tag(filename):
    """根据文件名生成漂亮的 HTML 标签 (IP/Domain)"""
    fname = filename.lower()
    if "ip" in fname and "domain" not in fname:
        return "<span style='background-color: #0969da; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold;'>IP-CIDR</span>"
    elif "domain" in fname or "site" in fname:
        return "<span style='background-color: #8a2be2; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold;'>DOMAIN</span>"
    else:
        return "<span style='background-color: #6e7681; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: bold;'>RULE</span>"

def create_button_group(repo, branch, file_path):
    raw_url = f"https://raw.githubusercontent.com/{repo}/{branch}/{file_path}"
    url_ghproxy = f"https://ghproxy.net/{raw_url}"
    url_gitmirror = f"https://raw.gitmirror.com/{repo}/{branch}/{file_path}"
    
    # 更加紧凑的布局，只有一行，节省空间
    html = (
        f"<a href='{url_ghproxy}' title='国内加速推荐'><code>🚀 Proxy</code></a> " 
        f"<a href='{url_gitmirror}' title='CDN 加速'><code>🛸 Mirror</code></a> "
        f"<a href='{raw_url}' title='官方直连'><code>🏠 Raw</code></a>"
    )
    return html

def generate_markdown():
    repo_slug = os.getenv("GITHUB_REPOSITORY", "User/Repo")
    update_time = get_beijing_time()

    # 1. 扫描并分组数据
    if not os.path.exists(DIR_JSON):
        print(f"❌ 错误: 找不到 {DIR_JSON} 目录")
        return

    # 数据结构: { "目录名": [文件信息列表] }
    groups = {}
    total_count = 0

    for root, dirs, files in os.walk(DIR_JSON):
        files.sort()
        rel_path = os.path.relpath(root, DIR_JSON)
        if rel_path == ".": rel_path = "Root (根目录)"
        
        # 规范化分类名称 (可以把 geo, steam 等作为分类)
        category = rel_path.replace("\\", "/")
        
        if category not in groups: groups[category] = []

        for file in files:
            if not file.endswith(".json"): continue
            
            file_name = os.path.splitext(file)[0]
            
            # 路径
            path_json = os.path.join(os.path.relpath(root, DIR_JSON), file).replace("\\", "/")
            path_srs = os.path.join(os.path.relpath(root, DIR_JSON), f"{file_name}.srs").replace("\\", "/")
            srs_abs_path = os.path.join(DIR_SRS, path_srs)
            
            srs_exists = os.path.exists(srs_abs_path)
            file_size = get_file_size(srs_abs_path) if srs_exists else "N/A"

            groups[category].append({
                "name": file_name,
                "path_json": path_json,
                "path_srs": path_srs,
                "srs_exists": srs_exists,
                "size": file_size
            })
            total_count += 1

    # 删除空组
    groups = {k: v for k, v in groups.items() if v}

    # 2. 开始构建 Markdown
    badges = [
        f"![Build](https://img.shields.io/github/actions/workflow/status/{repo_slug}/manager.yml?style=flat-square&logo=github&color=2ea44f)",
        f"![Count](https://img.shields.io/badge/Rules-{total_count}-blue?style=flat-square&logo=sing-box)",
        f"![Size](https://img.shields.io/github/repo-size/{repo_slug}?style=flat-square&color=orange)"
    ]

    content = []
    
    # --- Header ---
    content.append(f"<div align='center'>")
    content.append(f"<img src='{LOGO_URL}' width='100' alt='Logo'>")
    content.append(f"# Sing-box Rule Sets")
    content.append(f"{' '.join(badges)}")
    content.append(f"<br><h3>🚀 每日自动构建 · 极速多源镜像 · 智能分类</h3>")
    content.append(f"</div>")
    content.append(f"")

    # --- Navigation (快速跳转) ---
    content.append(f"## ⚡ 快速导航")
    nav_badges = []
    for cat in sorted(groups.keys()):
        # 生成锚点链接
        anchor = cat.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("/", "")
        nav_badges.append(f"[{cat}](#-folder-{anchor})")
    
    # 使用类似按钮的排版
    content.append(f"> {' &nbsp;•&nbsp; '.join(nav_badges)}")
    content.append(f"")
    content.append(f"---")
    content.append(f"")

    # --- Loop Categories ---
    for cat in sorted(groups.keys()):
        # 创建锚点
        anchor = cat.lower().replace(" ", "-").replace("(", "").replace(")", "").replace("/", "")
        content.append(f"<h3 id='-folder-{anchor}'>📂 folder: {cat}</h3>")
        content.append(f"")
        content.append(f"| 🏷️ 规则名称 | 💾 SRS 下载 (推荐) | 📝 源码 | 📊 体积 |")
        content.append(f"| :--- | :--- | :--- | :--- |")

        for item in groups[cat]:
            # 1. 名称一栏：加上 Tag
            type_tag = get_rule_tag(item['name'])
            display_name = f"{type_tag} <strong>{item['name']}</strong>"

            # 2. 链接生成
            if item['srs_exists']:
                link_srs = create_button_group(repo_slug, BRANCH, item['path_srs'])
                size_display = f"<code>{item['size']}</code>"
            else:
                link_srs = "🚫 Missing"
                size_display = "-"

            link_json = f"[View JSON](https://github.com/{repo_slug}/blob/{BRANCH}/{DIR_JSON}/{item['path_json']})"
            
            content.append(f"| {display_name} | {link_srs} | {link_json} | {size_display} |")
        
        content.append(f"")
        content.append(f"<div align='right'><a href='#sing-box-rule-sets'>🔼 Back to Top</a></div>") # 回到顶部
        content.append(f"")

    # --- Footer ---
    content.append(f"---")
    content.append(f"<div align='center'>")
    content.append(f"<p>Last Update: {update_time} (Beijing Time)</p>")
    content.append(f"</div>")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(content))
    
    print(f"✅ 旗舰优化版 README 已生成，包含分组导航与文件大小。")

if __name__ == "__main__":
    generate_markdown()
