import os
import urllib.parse

# --- 配置 ---
# 你的规则存放目录
DIR_JSON = "rules-json"
DIR_SRS = "rules-srs"
OUTPUT_FILE = "README.md" # 或者叫 RULES.md

# 这是一个 Markdown 模板头部
HEADER = """# 🚀 Sing-box 规则集索引

自动更新时间: {date}

## 📖 使用说明

在 Sing-box 配置中，建议使用 **SRS (Binary)** 格式，性能更好。

```json
{{
  "route": {{
    "rule_set": [
      {{
        "tag": "geosite-cn",
        "type": "remote",
        "format": "binary", 
        "url": "在此处填写下表中的 SRS 链接",
        "download_detour": "proxy"
      }}
    ]
  }}
}}
