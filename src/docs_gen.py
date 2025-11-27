import os
from datetime import datetime, timezone, timedelta

# ================= 配置 =================
DIR_JSON = "./rules-json"
DIR_SRS = "./rules-srs"
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
    """(保持原有逻辑) 生成精致的类型标签"""
    fname = filename.lower()
    style_base = "display:inline-block; padding:1px 6px; border-radius:4px; font-size:10px; font-weight:600; border:1px solid"
    if "ip" in fname and "domain" not in fname:
        return f"<span style='{style_base} #2196f3; color:#2196f3; background:#e3f2fd;'>IP-CIDR</span>"
    elif "domain" in fname or "site" in fname:
        return f"<span style='{style_base} #9c27b0; color:#9c27b0; background:#f3e5f5;'>DOMAIN</span>"
    return f"<span style='{style_base} #9e9e9e; color:#757575; background:#f5f5f5;'>RULE</span>"

def generate_markdown():
    repo = os.getenv("GITHUB_REPOSITORY", "User/Repo")
    update_time = get_beijing_time()
    
    # 徽章组配置
    badge_build = f"https://img.shields.io/github/actions/workflow/status/{repo}/manager.yml?style=flat-square&logo=github&label=Build"
    badge_size = f"https://img.shields.io/github/repo-size/{repo}?style=flat-square&label=Repo%20Size&color=orange"
    badge_last = f"https://img.shields.io/badge/Updated-{update_time.replace(' ', '%20')}-blue?style=flat-square&logo=time"

    lines = []

    # ================= 1. 现代化 Hero (头部) =================
    lines.append(f"<div align='center'>")
    lines.append(f"<a href='https://github.com/{repo}'>")
    lines.append(f"<img src='{LOGO_URL}' width='100' height='100' alt='SIng-box Logo'>")
    lines.append(f"</a>")
    lines.append(f"")
    lines.append(f"# Sing-box Rule Sets")
    lines.append(f"")
    lines.append(f"![Build Status]({badge_build}) ![Repo Size]({badge_size}) ![Update]({badge_last})")
    lines.append(f"")
    lines.append(f"<p style='font-size: 1.1em; color: #57606a;'>")
    lines.append(f"🚀 <strong>全自动构建</strong> · 🌏 <strong>全球 CDN 加速</strong> · 🎯 <strong>精准分类</strong>")
    lines.append(f"</p>")
    lines.append(f"</div>")
    lines.append(f"")
    
    # ================= 2. 特性仪表盘 (Feature Grid) =================
    # 使用 Markdown 表格布局，看起来像产品介绍页
    lines.append(f"| 🤖 **Automated** | ⚡ **High Speed** | 📦 **Standardized** |")
    lines.append(f"| :---: | :---: | :---: |")
    lines.append(f"| 每小时同步上游规则<br>自动编译为 SRS 二进制 | 集成 GhProxy/GitMirror<br>国内环境极速拉取 | 标准化 JSON/SRS 输出<br>完美适配 Sing-box |")
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")

    # ================= 3. 现代化配置引导 (Alerts) =================
    lines.append(f"## ⚙️ 配置指南 (Setup)")
    lines.append(f"")
    # 使用 GitHub 原生 Alert 语法: > [!TIP] 或 > [!IMPORTANT]
    lines.append(f"> [!TIP]")
    lines.append(f"> 推荐使用 **SRS (二进制)** 格式，相比 JSON 格式，它能显著降低内存占用并提升加载速度。")
    lines.append(f"")
    
    lines.append(f"<details>")
    lines.append(f"<summary><strong>📝 点击展开 `config.json` 配置示例</strong></summary>")
    lines.append(f"")
    lines.append(f"请在下方列表中选择需要的规则，点击 `🚀 Fast Download` 按钮复制链接，填入 `url` 字段：")
    lines.append(f"")
    lines.append(f"```json")
    lines.append(f"{{")
    lines.append(f'  "route": {{')
    lines.append(f'    "rule_set": [')
    lines.append(f"      {{")
    lines.append(f'        "type": "remote",')
    lines.append(f'        "tag": "geosite-google",')
    lines.append(f'        "format": "binary",')
    lines.append(f'        "url": "https://ghproxy.net/...",')
    lines.append(f'        "download_detour": "proxy-out" // 💡 确保你有这个出站 tag')
    lines.append(f"      }}")
    lines.append(f"    ]")
    lines.append(f"  }}")
    lines.append(f"}}")
    lines.append(f"```")
    lines.append(f"</details>")
    lines.append(f"")

    # ================= 4. 规则列表 (保持你的列表样式) =================
    lines.append(f"## 📥 规则下载 (Downloads)")
    lines.append(f"")
    # 在这里添加一个搜索提示，增加易用性
    lines.append(f"> [!NOTE]")
    lines.append(f"> 移动端用户可向左滑动表格查看完整下载选项。使用 `Ctrl + F` 可快速查找规则。")
    lines.append(f"")
    
    lines.append(f"| 规则名称 (Name) | 类型 (Type) | 大小 (Size) | 下载通道 (Download) |")
    lines.append(f"| :--- | :--- | :--- | :--- |")

    count = 0
    if os.path.exists(DIR_JSON):
        file_list = []
        for root, dirs, files in os.walk(DIR_JSON):
            files.sort()
            rel_path = os.path.relpath(root, DIR_JSON)
            if rel_path == ".": rel_path = ""
            for file in files:
                if not file.endswith(".json"): continue
                file_list.append((rel_path, file))
        
        file_list.sort(key=lambda x: (x[0], x[1]))

        for rel_path, file in file_list:
            name = os.path.splitext(file)[0]
            
            p_json = os.path.join(rel_path, file).replace("\\", "/")
            p_srs = os.path.join(rel_path, f"{name}.srs").replace("\\", "/")
            srs_abs = os.path.join(DIR_SRS, p_srs)
            
            # 列表样式保持不变
            if rel_path:
                display_name = f"<span style='color:#8395a7;font-size:11px'>📂 {rel_path} /</span><br><strong>{name}</strong>"
            else:
                display_name = f"<strong>{name}</strong>"

            tag_html = get_tags(name)
            size_str = format_size(srs_abs)
            size_html = f"<code>{size_str}</code>" if os.path.exists(srs_abs) else "-"

            raw_base = f"https://raw.githubusercontent.com/{repo}/{BRANCH}"
            link_ghproxy = f"https://ghproxy.net/{raw_base}/{p_srs}"
            link_mirror = f"https://raw.gitmirror.com/{repo}/{BRANCH}/{p_srs}"
            link_raw = f"{raw_base}/{p_srs}"
            link_source = f"{raw_base}/{p_json}"

            if os.path.exists(srs_abs):
                # 保持你喜欢的 Button + Sub-links 组合
                action_html = (
                    f"<a href='{link_ghproxy}'>"
                    f"<img src='https://img.shields.io/badge/🚀_Fast_Download-GhProxy-009688?style=flat-square&logo=rocket' alt='btn'>"
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

    # ================= 5. 现代化页脚 =================
    lines.append(f"")
    lines.append(f"---")
    lines.append(f"")
    lines.append(f"<div align='center'>")
    lines.append(f"<p><strong>Total Rule Sets:</strong> <code>{count}</code></p>")
    # 增加回到顶部链接
    lines.append(f"<p><a href='#sing-box-rule-sets'>🔼 Back to Top</a></p>")
    lines.append(f"<br>")
    lines.append(f"<sub>Powered by <a href='https://github.com/actions'>GitHub Actions</a> & <a href='https://sing-box.sagernet.org'>Sing-box</a></sub>")
    lines.append(f"</div>")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("✅ 现代化 README (样式增强版) 已生成")

if __name__ == "__main__":
    generate_markdown()
