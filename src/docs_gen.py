import os
from datetime import datetime, timezone, timedelta

# 获取脚本所在绝对路径，防止路径错误
try:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
except:
    BASE_DIR = os.getcwd()

# 如果脚本在 src 目录下，向上寻找根目录
PROJECT_ROOT = os.path.dirname(BASE_DIR) if os.path.basename(BASE_DIR) == "src" else BASE_DIR

DIR_JSON = os.path.join(PROJECT_ROOT, "rules-json")
DIR_SRS = os.path.join(PROJECT_ROOT, "rules-srs")
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "README.md")
BRANCH = "main"

LOGO_URL = "https://sing-box.sagernet.org/assets/icon.svg"

# 配置：主加速源 (显示为大按钮)
PRIMARY_CDN = {
    "name": "GhProxy",
    "url": "https://ghproxy.net/https://raw.githubusercontent.com/{repo}/{branch}/{path}",
    "badge": "https://img.shields.io/badge/🚀_Fast_Install-GhProxy-00b894?style=flat-square"
}

# 配置：备用源 (显示为下方小链接)
MIRROR_SOURCES = [
    {"name": "KGitHub", "url": "https://raw.kgithub.com/{repo}/{branch}/{path}"},
    {"name": "JSDelivr", "url": "https://cdn.jsdelivr.net/gh/{repo}@{branch}/{path}"},
    {"name": "Raw", "url": "https://raw.githubusercontent.com/{repo}/{branch}/{path}"},
]

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
    """
    生成莫兰迪色系的精美标签
    """
    fname = filename.lower()
    # 基础样式：无边框，圆角，稍微加一点内边距，字体变小
    base_style = "display:inline-block; padding:2px 6px; border-radius:6px; font-size:10px; font-weight:bold; font-family: sans-serif; vertical-align: middle; margin-left: 8px;"
    
    if "ip" in fname and "domain" not in fname:
        # 蓝色系 (IP)
        return f"<span style='{base_style} color:#0984e3; background:#dff9fb; border:1px solid #74b9ff;'>IP-CIDR</span>"
    elif "domain" in fname or "site" in fname:
        # 紫色系 (域名)
        return f"<span style='{base_style} color:#6c5ce7; background:#e0d7ff; border:1px solid #a29bfe;'>DOMAIN</span>"
    else:
        # 灰色系 (普通)
        return f"<span style='{base_style} color:#636e72; background:#f1f2f6; border:1px solid #b2bec3;'>RULE</span>"

def generate_action_cell(repo, path, is_primary_only=False):
    """
    生成 '主按钮 + 备用链' 的组合 HTML
    """
    # 1. 生成主按钮
    primary_url = PRIMARY_CDN["url"].format(repo=repo, branch=BRANCH, path=path)
    primary_html = f"<a href='{primary_url}'><img src='{PRIMARY_CDN['badge']}' alt='Fast Download'></a>"
    
    if is_primary_only:
        return primary_html

    # 2. 生成备用链接行
    mirrors_html = []
    for m in MIRROR_SOURCES:
        url = m["url"].format(repo=repo, branch=BRANCH, path=path)
        # 使用简单的文字链接，看起来更干净
        mirrors_html.append(f"<a href='{url}' style='color:#636e72;text-decoration:none;'>{m['name']}</a>")
    
    # 用点号连接
    mirrors_str = " • ".join(mirrors_html)
    
    # 组合：上面是按钮，中间空隙，下面是小字的备用链
    final_html = (
        f"{primary_html}<br>"
        f"<span style='font-size:10px; color:#b2bec3; line-height: 1.8;'>Mirrors: </span>"
        f"<sub style='font-size:10px;'>{mirrors_str}</sub>"
    )
    return final_html

def generate_markdown():
    repo = os.getenv("GITHUB_REPOSITORY", "User/Repo")
    update_time = get_beijing_time()
    
    # 顶部徽章
    badge_build = f"https://img.shields.io/github/actions/workflow/status/{repo}/manager.yml?style=flat-square&logo=github&label=Build"
    badge_size = f"https://img.shields.io/github/repo-size/{repo}?style=flat-square&label=Size&color=orange"
    
    lines = []

    # ================= 1. Header =================
    lines.append(f"<div align='center'>")
    lines.append(f"<a href='https://github.com/{repo}'>")
    lines.append(f"<img src='{LOGO_URL}' width='80' height='80' alt='Logo'>")
    lines.append(f"</a>")
    lines.append(f"<h2>Sing-box Rules Auto-Build</h2>")
    lines.append(f"<p>{badge_build} {badge_size}</p>")
    lines.append(f"<p style='color: #636e72; font-size: 14px;'>🔄 Automatic Updates · ⚡ Multi-CDN · 📦 Binary & Source</p>")
    lines.append(f"</div>")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # 收集文件数据
    file_data = []
    if os.path.exists(DIR_JSON):
        for root, dirs, files in os.walk(DIR_JSON):
            files.sort()
            rel_path = os.path.relpath(root, DIR_JSON)
            if rel_path == ".": rel_path = ""
            for file in files:
                if not file.endswith(".json"): continue
                
                name = os.path.splitext(file)[0]
                p_json = os.path.join(rel_path, file).replace("\\", "/")
                p_srs = os.path.join(rel_path, f"{name}.srs").replace("\\", "/")
                
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
        file_data.sort(key=lambda x: (x["folder"], x["name"]))

    # ================= 2. SRS 列表 (美化版) =================
    lines.append(f"### 🚀 SRS Binary Rules")
    lines.append(f"> <small>推荐使用。二进制格式加载速度更快，内存占用更低。</small>")
    lines.append(f"")
    # 表头：只有3列，更宽敞
    lines.append(f"| Rule Set | Size | Fast Download |")
    lines.append(f"| :--- | :---: | :--- |")
    
    srs_count = 0
    for item in file_data:
        if not item["has_srs"]: continue
        
        # 1. 名称列：文件夹 + 文件名 + 标签
        # 使用 <code> 标签包裹文件名，让它看起来像技术参数
        name_html = f"<code>{item['name']}</code>"
        tag_html = get_tag_html(item['name'])
        
        if item["folder"]:
            # 如果有子目录，显示为小灰字
            display_name = f"<span style='color:#b2bec3;font-size:10px'>📂 {item['folder']} / </span>{name_html} {tag_html}"
        else:
            display_name = f"{name_html} {tag_html}"

        # 2. 大小列
        size = format_size(item["abs_srs"])
        
        # 3. 下载列 (组合样式)
        action_html = generate_action_cell(repo, item["rel_srs"])

        lines.append(f"| {display_name} | {size} | {action_html} |")
        srs_count += 1

    lines.append(f"")
    lines.append(f"<br>")

    # ================= 3. JSON 列表 (简洁版) =================
    lines.append(f"### 📄 JSON Source Rules")
    lines.append(f"> <small>源码格式。仅用于查看规则内容或二次开发。</small>")
    lines.append(f"")
    lines.append(f"| Rule Set | Size | Source |")
    lines.append(f"| :--- | :---: | :--- |")
    
    json_count = 0
    for item in file_data:
        name_html = f"<code>{item['name']}</code>"
        tag_html = get_tag_html(item['name'])
        
        if item["folder"]:
            display_name = f"<span style='color:#b2bec3;font-size:10px'>📂 {item['folder']} / </span>{name_html} {tag_html}"
        else:
            display_name = f"{name_html} {tag_html}"

        size = format_size(item["abs_json"])
        
        # JSON 只需要一个简单的 raw 链接即可，不需要那么多加速
        raw_url = f"https://raw.githubusercontent.com/{repo}/{BRANCH}/{item['rel_json']}"
        action_html = f"<a href='{raw_url}'>View Source</a>"

        lines.append(f"| {display_name} | {size} | {action_html} |")
        json_count += 1

    # ================= 4. Footer =================
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"<div align='center'>")
    lines.append(f"<p><sub style='color:#b2bec3'>Last updated: {update_time} (Beijing Time)</sub></p>")
    lines.append(f"</div>")

    # 写文件
    try:
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        print(f"✅ README 更新成功: SRS[{srs_count}] / JSON[{json_count}]")
    except Exception as e:
        print(f"❌ 写入文件失败: {e}")

if __name__ == "__main__":
    generate_markdown()
