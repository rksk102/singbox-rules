import os
from datetime import datetime, timezone, timedelta

# --- 配置区域 ---
BRANCH = "main"
OUTPUT_FILE = "README.md"
DIR_JSON = "./rules-json"
DIR_SRS = "./rules-srs"

# 加速镜像前缀 (你可以根据需要换成其他的，比如 https://fastgh.yyyy.bi/)
# 使用 ghproxy.net 是比较通用的方案
PROXY_PREFIX = "https://ghproxy.net/"

def get_beijing_time():
    utc_dt = datetime.utcnow().replace(tzinfo=timezone.utc)
    bj_dt = utc_dt.astimezone(timezone(timedelta(hours=8)))
    return bj_dt.strftime("%Y-%m-%d %H:%M:%S")

def generate_markdown():
    repo_slug = os.getenv("GITHUB_REPOSITORY", "User/Repo")
    
    # 基础 Raw 地址 (官方)
    # 格式: https://raw.githubusercontent.com/User/Repo/main
    base_raw_url = f"https://raw.githubusercontent.com/{repo_slug}/{BRANCH}"

    # 徽章链接
    badge_build = f"https://img.shields.io/github/actions/workflow/status/{repo_slug}/manager.yml?style=flat-square&logo=github&label=Build"
    badge_size = f"https://img.shields.io/github/repo-size/{repo_slug}?style=flat-square&label=Size&color=orange"
    
    content_lines = [
        "<div align='center'>",
        "",
        "# 🚀 Sing-box Rule Sets",
        "",
        f"![Build Status]({badge_build}) ![Repo Size]({badge_size})",
        "",
        "**自动同步与编译脚本 · 每日更新 · 多源加速**",
        "",
        "</div>",
        "",
        "## 📖 简介",
        "本项目基于 GitHub Actions 自动拉取上游规则，并编译为 **Sing-box SRS** 二进制格式。支持 GitHub 原生链接与加速镜像链接，方便不同网络环境使用。",
        "",
        "<details>",
        "<summary><strong>🛠️ 如何在 Sing-box 中使用？(点击展开)</strong></summary>",
        "",
        "### 远程规则集配置示例",
        "在 `config.json` 的 `route` -> `rule_set` 中添加：",
        "",
        "```json",
        "{",
        '  "type": "remote",',
        '  "tag": "geosite-google",',
        '  "format": "binary",',
        '  "url": "复制下方的 SRS 加速链接",',
        '  "download_detour": "select" // 用于下载规则的代理出站',
        "}",
        "```",
        "</details>",
        "",
        "## 📂 规则列表",
        "",
        "| 规则路径 / 名称 | 📄 Source (JSON) | 🚀 Binary (SRS) |",
        "| :--- | :--- | :--- |"
    ]

    if not os.path.exists(DIR_JSON):
        print(f"❌ 错误: 找不到 {DIR_JSON} 目录")
        return

    count = 0
    for root, dirs, files in os.walk(DIR_JSON):
        files.sort()
        rel_path = os.path.relpath(root, DIR_JSON)
        if rel_path == ".": rel_path = ""

        for file in files:
            if not file.endswith(".json"): continue
            
            file_name = os.path.splitext(file)[0]
            
            # 显示名称优化
            if rel_path:
                # 文件夹加粗，看起来更有层次
                display_name = f"📂 **{rel_path}**<br>└─ `{file_name}`"
                full_rel_path = f"{rel_path}/{file_name}"
            else:
                display_name = f"`{file_name}`"
                full_rel_path = file_name

            # 路径处理 (统一为 Web 路径 /)
            # 注意：URL 编码最好做一下，不过简单的文件名通常没事
            path_with_ext_json = f"{DIR_JSON}/{full_rel_path}.json".replace("\\", "/").replace("./", "")
            path_with_ext_srs = f"{DIR_SRS}/{full_rel_path}.srs".replace("\\", "/").replace("./", "")

            # 1. 构造 JSON 链接
            url_json_raw = f"{base_raw_url}/{path_with_ext_json}"
            url_json_proxy = f"{PROXY_PREFIX}{url_json_raw}"
            
            # 2. 构造 SRS 链接
            srs_local_check = os.path.join(DIR_SRS, rel_path, f"{file_name}.srs")
            
            if os.path.exists(srs_local_check):
                url_srs_raw = f"{base_raw_url}/{path_with_ext_srs}"
                url_srs_proxy = f"{PROXY_PREFIX}{url_srs_raw}"
                
                # 使用 HTML <br> 换行，上面放加速链接，下面放官方链接
                link_json_cell = f"[⚡ **加速下载**]({url_json_proxy})<br><br>[🐈 Github]({url_json_raw})"
                link_srs_cell = f"[⚡ **加速下载**]({url_srs_proxy})<br><br>[🐈 Github]({url_srs_raw})"
            else:
                link_json_cell = f"[Github]({url_json_raw})"
                link_srs_cell = "⚠️ 编译失败"

            # 添加表格行
            content_lines.append(f"| {display_name} | {link_json_cell} | {link_srs_cell} |")
            count += 1

    # 底部统计
    update_time = get_beijing_time()
    content_lines.append("")
    content_lines.append("---")
    content_lines.append(f"<div align='center'>")
    content_lines.append(f"<strong>统计:</strong> 共包含 {count} 个规则集 &nbsp;|&nbsp; ")
    content_lines.append(f"<strong>最后更新 (北京时间):</strong> {update_time}")
    content_lines.append(f"</div>")

    # 写入
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write("\n".join(content_lines))
    
    print(f"✅ 美化版 README.md 已生成，包含 {count} 条规则。")

if __name__ == "__main__":
    generate_markdown()
