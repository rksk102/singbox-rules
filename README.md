# 🚀 Sing-box 自用规则集

![Auto Build](https://github.com/rksk102/singbox-rules/actions/workflows/manager.yml/badge.svg)

本项目由自动化工作流维护，定时拉取上游规则并编译为 Sing-box 兼容格式。
所有规则均已编译为 **SRS (Sing-box Rule Set)** 二进制格式，以获得最佳性能。

## 📂 规则列表
> 点击下方链接可直接复制使用。

| 规则名称 | 📝 JSON (Source) | 🚀 SRS (Binary) |
| :--- | :---: | :---: |
| **rulesets/block/domain/rksk102** / all-adblock | [JSON](https://github.com/rksk102/singbox-rules/raw/main/rules-json/rulesets/block/domain/rksk102/all-adblock.json) | [SRS](https://github.com/rksk102/singbox-rules/raw/main/rules-srs/rulesets/block/domain/rksk102/all-adblock.srs) |
| **rulesets/block/domain/Loyalsoldier** / reject | [JSON](https://github.com/rksk102/singbox-rules/raw/main/rules-json/rulesets/block/domain/Loyalsoldier/reject.json) | [SRS](https://github.com/rksk102/singbox-rules/raw/main/rules-srs/rulesets/block/domain/Loyalsoldier/reject.srs) |
| **rulesets/block/domain/Loyalsoldier** / win-extra | [JSON](https://github.com/rksk102/singbox-rules/raw/main/rules-json/rulesets/block/domain/Loyalsoldier/win-extra.json) | [SRS](https://github.com/rksk102/singbox-rules/raw/main/rules-srs/rulesets/block/domain/Loyalsoldier/win-extra.srs) |
| **rulesets/block/domain/Loyalsoldier** / win-spy | [JSON](https://github.com/rksk102/singbox-rules/raw/main/rules-json/rulesets/block/domain/Loyalsoldier/win-spy.json) | [SRS](https://github.com/rksk102/singbox-rules/raw/main/rules-srs/rulesets/block/domain/Loyalsoldier/win-spy.srs) |
| **rulesets/proxy/domain/rksk102** / all-proxy | [JSON](https://github.com/rksk102/singbox-rules/raw/main/rules-json/rulesets/proxy/domain/rksk102/all-proxy.json) | [SRS](https://github.com/rksk102/singbox-rules/raw/main/rules-srs/rulesets/proxy/domain/rksk102/all-proxy.srs) |
| **rulesets/proxy/domain/Loyalsoldier** / gfw | [JSON](https://github.com/rksk102/singbox-rules/raw/main/rules-json/rulesets/proxy/domain/Loyalsoldier/gfw.json) | [SRS](https://github.com/rksk102/singbox-rules/raw/main/rules-srs/rulesets/proxy/domain/Loyalsoldier/gfw.srs) |
| **rulesets/proxy/domain/gh-proxy.com** / category-ai-!cn | [JSON](https://github.com/rksk102/singbox-rules/raw/main/rules-json/rulesets/proxy/domain/gh-proxy.com/category-ai-!cn.json) | [SRS](https://github.com/rksk102/singbox-rules/raw/main/rules-srs/rulesets/proxy/domain/gh-proxy.com/category-ai-!cn.srs) |
| **rulesets/direct/ipcidr/rksk102** / all-cnip | [JSON](https://github.com/rksk102/singbox-rules/raw/main/rules-json/rulesets/direct/ipcidr/rksk102/all-cnip.json) | [SRS](https://github.com/rksk102/singbox-rules/raw/main/rules-srs/rulesets/direct/ipcidr/rksk102/all-cnip.srs) |
| **rulesets/direct/ipcidr/Loyalsoldier** / lancidr | [JSON](https://github.com/rksk102/singbox-rules/raw/main/rules-json/rulesets/direct/ipcidr/Loyalsoldier/lancidr.json) | [SRS](https://github.com/rksk102/singbox-rules/raw/main/rules-srs/rulesets/direct/ipcidr/Loyalsoldier/lancidr.srs) |
| **rulesets/direct/domain/Loyalsoldier** / apple-cn | [JSON](https://github.com/rksk102/singbox-rules/raw/main/rules-json/rulesets/direct/domain/Loyalsoldier/apple-cn.json) | [SRS](https://github.com/rksk102/singbox-rules/raw/main/rules-srs/rulesets/direct/domain/Loyalsoldier/apple-cn.srs) |
| **rulesets/direct/domain/Loyalsoldier** / direct-list | [JSON](https://github.com/rksk102/singbox-rules/raw/main/rules-json/rulesets/direct/domain/Loyalsoldier/direct-list.json) | [SRS](https://github.com/rksk102/singbox-rules/raw/main/rules-srs/rulesets/direct/domain/Loyalsoldier/direct-list.srs) |
| **rulesets/direct/domain/Loyalsoldier** / private | [JSON](https://github.com/rksk102/singbox-rules/raw/main/rules-json/rulesets/direct/domain/Loyalsoldier/private.json) | [SRS](https://github.com/rksk102/singbox-rules/raw/main/rules-srs/rulesets/direct/domain/Loyalsoldier/private.srs) |
| **rulesets/direct/domain/MetaCubeX** / geolocation-cn | [JSON](https://github.com/rksk102/singbox-rules/raw/main/rules-json/rulesets/direct/domain/MetaCubeX/geolocation-cn.json) | [SRS](https://github.com/rksk102/singbox-rules/raw/main/rules-srs/rulesets/direct/domain/MetaCubeX/geolocation-cn.srs) |
| **rulesets/direct/domain/github.com** / microsoft-cn | [JSON](https://github.com/rksk102/singbox-rules/raw/main/rules-json/rulesets/direct/domain/github.com/microsoft-cn.json) | [SRS](https://github.com/rksk102/singbox-rules/raw/main/rules-srs/rulesets/direct/domain/github.com/microsoft-cn.srs) |

## ⚙️ 自动化配置
- 自动更新时间: 每天
- 包含规则总数: 14 个
- Powered by Github Actions & Sing-box