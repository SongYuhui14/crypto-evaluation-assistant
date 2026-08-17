# crypto-evaluation-assistant（密评检测辅助）

> 📦 仓库地址：https://github.com/SongYuhui14/crypto-evaluation-assistant

DeepSeek Harness / Claude 技能（Skill）：辅助开展**商用密码应用安全性评估（密评）**的检测、分析、报告与学习工作。

面向**密评工程师 / 实习生 / 备考者**：从检查清单生成到符合率计算再到报告初稿，形成一条完整的**"检测 → 判定 → 报告"工具链**。

## ✨ 特色

| 特色 | 说明 |
|---|---|
| 🏭 **工具链闭环** | 3 个零依赖 Python 脚本：生成清单 → 算符合率 → 出报告初稿 |
| 🏦 **行业垂直清单** | 金融 / 政务 / 能源行业特有检查点（密钥分散、支付报文、纵向加密装置等）|
| 🛡️ **准确性护栏** | 强制"测评项编号以官方文本为准"，不编造编号、权重、阈值 |
| 🧪 **评测认证** | 三轮 50 项断言全部通过（含基线对比），见 [evals/](evals/) |
| 📚 **学习模式** | 备考辅助：标准体系梳理、考点总结、易错点、速记卡 |

## 功能

- 密评框架梳理：物理和环境安全、网络和通信安全、设备和计算安全、应用和数据安全 + 密钥管理、安全管理
- 算法 / 密码产品 / 密钥管理合规性核查（SM2 / SM3 / SM4 / SM9 / ZUC 等）
- 合规性、正确性、有效性三维度判定工作流，含现场取证方法
- 检测检查清单、测评报告模板、高频问题整改库、国密算法速查
- 密评学习与备考辅助模式

## 安装（DeepSeek Harness / Claude Code）

1. 把本目录（或整个 `skills/` 目录）放到你的技能目录，例如：

   - DeepSeek Harness：`~/.ohdsh/skills/`
   - Claude Code：`~/.claude/skills/` 或项目内 `.claude/skills/`

2. 新会话中，当任务匹配技能描述时会自动触发。

## 使用示例

对话中直接描述你的密评任务，例如：

- "帮我按 GB/T 39786 梳理这个系统的密评检查项"
- "写一份密评测评报告的框架"
- "核查这套系统的密钥管理是否合规"
- "这个结论应该判符合还是基本符合？"
- "SM2、SM3、SM4 的用途怎么区分？"（学习模式）

## 工具链（scripts/）

需要 Python 3（标准库即可，零依赖）。三个脚本形成闭环：

```bash
# 1. 按等级+行业生成检查清单
python scripts/gen_checklist.py --level 3 --industry finance

# 2. 按测评项判定计算符合率与结论
python scripts/calc_conformance.py --json results.json

# 3. 从测评结果生成报告初稿
python scripts/gen_report.py --json input.json -o report.md
```

> 脚本用于提效与计算辅助，最终判定与报告结论必须人工核实标准原文后确认。

## 目录结构

```
crypto-evaluation-assistant/
├── SKILL.md                     # 技能主文件（frontmatter + 指令）
├── README.md                    # 本文件
├── LICENSE                      # MIT 协议
├── evals/                       # 评测机制（三轮评测 25/25 达标）
│   ├── evals.json               # 测试用例（含基线对比断言）
│   └── README.md                # 评测运行方法
├── scripts/                     # 零依赖 Python 工具
│   ├── gen_checklist.py         # 按等级+行业生成检查清单
│   ├── calc_conformance.py      # 符合率计算与结论判定
│   └── gen_report.py            # 从测评结果生成报告初稿
└── references/
    ├── standards-map.md         # 密评标准体系对照表
    ├── checklist.md             # 通用密评检测检查清单
    ├── checklist/               # 行业垂直清单
    │   ├── finance.md           # 金融行业
    │   ├── government.md        # 政务行业
    │   └── energy.md            # 能源行业
    ├── report-template.md       # 测评报告模板（含撰写要点）
    ├── crypto-basics.md         # 国密算法速查与常见误用
    └── common-issues.md         # 高频问题与整改建议
```

## 依据标准

- GB/T 39786-2021《信息安全技术 信息系统密码应用基本要求》
- GM/T 0115-2021《信息系统密码应用测评要求》
- GM/T 0116-2021《信息系统密码应用测评过程指南》
- 行业参考：JR/T 0269（金融）、GM/T 0045（金融数据密码机）等（见行业清单）

> 具体测评项编号、权重与判定阈值以标准官方文本为准，本技能提供框架与工作流。

## 评测与质量

本技能经过 **3 轮迭代评测**（50 条断言，含"带技能 vs 不带技能"基线对比）：

- 带技能配置：**50/50 全部通过**
- 不带技能基线：48/50（最典型的差距：符合率手算易错，脚本计算准确且产物可审计）
- 评测机制与结果详见 [evals/](evals/) 与技能工作区

## 许可

[MIT](LICENSE)
