import requests
import json
import os

# 配置你的源： '文件名' : '远程TXT链接'
SOURCES = {
    "win-extra": "https://raw.githubusercontent.com/your-username/repo/main/win-extra.txt",
    "reject-list": "https://example.com/reject.txt",
    # 在这里添加更多源...
}

OUTPUT_DIR = "./rule-sets"

def download_and_convert():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    for name, url in SOURCES.items():
        print(f"正在处理: {name}...")
        try:
            # 1. 下载内容
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            content = response.text
            
            # 2. 清洗数据 (假设是每行一个域名)
            domains = []
            for line in content.splitlines():
                line = line.strip()
                # 跳过空行和注释
                if not line or line.startswith("#") or line.startswith("//"):
                    continue
                domains.append(line)

            if not domains:
                print(f"  警告: {name} 为空，跳过。")
                continue

            # 3. 构建 Sing-box JSON 结构
            data = {
                "version": 1,
                "rules": [{"domain_suffix": domains}]
            }

            # 4. 保存为 JSON
            json_path = os.path.join(OUTPUT_DIR, f"{name}.json")
            with open(json_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            print(f"  已生成 JSON: {json_path} (包含 {len(domains)} 条规则)")

        except Exception as e:
            print(f"  处理 {name} 失败: {e}")

if __name__ == "__main__":
    download_and_convert()
