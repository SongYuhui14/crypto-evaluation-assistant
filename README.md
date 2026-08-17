# crypto-evaluation-assistant（密评检测辅助）

DeepSeek Harness / Claude 技能（Skill）：辅助开展**商用密码应用安全性评估（密评）**的检测、分析、报告与学习工作。

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

## 目录结构

```
crypto-evaluation-assistant/
├── SKILL.md                     # 技能主文件（frontmatter + 指令）
├── README.md                    # 本文件
├── LICENSE                      # MIT 协议
└── references/
    ├── checklist.md             # 密评检测检查清单（含取证方式）
    ├── report-template.md       # 测评报告模板（含撰写要点）
    ├── crypto-basics.md         # 国密算法速查与常见误用
    └── common-issues.md         # 高频问题与整改建议
```

## 依据标准

- GB/T 39786-2021《信息安全技术 信息系统密码应用基本要求》
- GM/T 0115-2021《信息系统密码应用测评要求》
- GM/T 0116-2021《信息系统密码应用测评过程指南》

> 具体测评项编号、权重与判定阈值以标准官方文本为准，本技能提供框架与工作流。

## 许可

[MIT](LICENSE)
