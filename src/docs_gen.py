import os
from datetime import datetime, timezone, timedelta

# ================= 配置 =================
DIR_JSON = "./rules-json"
DIR_SRS = "./rules-srs"
BRANCH = "main"
OUTPUT_FILE = "README.md"
# ---------------------------------------

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
    """返回极简的类型标记"""
    fname = filename.lower()
    if "ip" in fname and "domain" not in fname:
        # 蓝色代码块代表 IP
        return "<code>IP-CIDR</code>"
    elif "domain" in fname or "site" in fname:
        # 默认灰色代码块代表 域名
        return "<code>DOMAIN</code>"
    return "<code>RULE</code>"

def generate_markdown():
    repo = os.getenv("GITHUB_REPOSITORY", "User/Repo")
    
    # 头部：极简风格
    lines = [
        f"# Sing-box 规则集",
        f"",
        f"> 自动同步 · 全球加速 · 极简体验",
        f"",
        f"📅 **最后更新**: `{get_beijing_time()}`",
        f"",
        f"## 🚀 规则列表",
        f"",
        f"| 规则名称 | 类型 & 大小 | 下载地址 (加速 / 官方) |",
        f"| :--- | :--- | :--- |"
    ]

    if not os.path.exists(DIR_JSON): return

    for root, dirs, files in os.walk(DIR_JSON):
        files.sort()
        rel_path = os.path.relpath(root, DIR_JSON)
        if rel_path == ".": rel_path = ""

        for file in files:
            if not file.endswith(".json"): continue
            name = os.path.splitext(file)[0]

            # 路径计算
            p_json = f"{rel_path}/{file}".strip("/").replace("\\", "/")
            p_srs = f"{rel_path}/{name}.srs".strip("/").replace("\\", "/")
            
            # 1. 名称列 (显示目录结构，但颜色变淡)
            if rel_path:
                col_name = f"<span style='color:gray'>{rel_path}/</span>**{name}**"
            else:
                col_name = f"**{name}**"

            # 2. 类型 & 大小列
            srs_local = os.path.join(DIR_SRS, p_srs)
            file_size = format_size(srs_local)
            type_badge = get_type_badge(name)
            col_info = f"{type_badge}<br><span style='font-size:12px;color:gray'>{file_size}</span>"

            # 3. 下载链接列 (核心部分)
            # Raw URL
            raw = f"https://raw.githubusercontent.com/{repo}/{BRANCH}"
            url_srs = f"{raw}/{p_srs}"
            url_json = f"{raw}/{p_json}"
            
            # Mirrors
            proxy_gh = f"https://ghproxy.net/{url_srs}"
            proxy_git = f"https://raw.gitmirror.com/{repo}/{BRANCH}/{p_srs}"

            if os.path.exists(srs_local):
                # 样式设计：
                # 第一行：两个强力的加速源 (加粗显示)
                # 第二行：原始 JSON 链接 (小字)
                links = (
                    f"⚡ **SRS**: [GhProxy]({proxy_gh}) , [GitMirror]({proxy_git})<br>"
                    f"📄 **Src**: [GitHub Raw]({url_json})"
                )
            else:
                links = "⚠️ <i>编译失败</i>"

            lines.append(f"| {col_name} | {col_info} | {links} |")

    # 尾部
    lines.append("")
    lines.append(f"---")
    lines.append(f"<sub>总计包含 {len(lines)-9} 条规则 · Powered by Actions</sub>")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("✅ 极简版 README 已生成")

if __name__ == "__main__":
    generate_markdown()
