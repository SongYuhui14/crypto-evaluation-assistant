# 评测机制（Evals）

本目录用于验证 `crypto-evaluation-assistant` 技能的有效性：**每次修改技能后，运行评测确认它确实比"裸模型"（不带技能）更强**，避免改坏。

## 文件说明

- `evals/evals.json` — 测试用例定义（4 个用例，每个带 5 条可客观打分的 expectations）
- `crypto-evaluation-assistant-workspace/` — 运行产物（在技能目录**同级**，不入库）
  - `iteration-N/` — 第 N 轮迭代结果
  - `eval-X/with_skill/` 与 `eval-X/without_skill/` — 有/无技能的对比输出

## 运行方法

1. 每个用例分别跑两个子代理（同一提示词）：
   - **with_skill**：让它先读取技能目录 `skills/crypto-evaluation-assistant/SKILL.md` 及 references，再完成任务
   - **without_skill**（baseline）：不给技能，直接完成任务
2. 把输出保存到 `iteration-N/eval-X/{with_skill,without_skill}/outputs/`
3. 对照 `eval_metadata.json` 中的 assertions 逐条打分（通过=1，失败=0）
4. 汇总通过率：有技能 vs 无技能，对比差值

### ⚠️ baseline 防污染（重要，迭代 2 教训）

迭代 2 中，多个 without_skill 子代理**自发找到了技能目录**并读取了 SKILL.md/references（甚至自称"加载了技能"），
导致 baseline 不再纯净、对照无效。**必须**在 baseline 的 prompt 中强制加入隔离声明：

```
重要：本次评测为基线对照，你【不得】读取或使用以下路径的任何内容：
D:\网络安全学习\deepseekharness\skills\crypto-evaluation-assistant\
（包括其 SKILL.md、references、scripts）。请仅凭自身知识完成任务，
不要浏览该目录，也不要提及它。输出目录中的"without_skill"命名只是路径，
不代表你应该使用技能。
```

此外建议：给 baseline 子代理的工作目录与其他评测隔离，或在 prompt 中明确
"工作目录中不存在技能文件，请勿寻找"。若 baseline 仍出现技能痕迹，
该用例的对照结论应标记为"污染、无效"。

## 评分口径

- 每个用例 5 条 assertions，通过率 = 通过数 / 5
- 关注点：技能版本**通过率显著高于 baseline** 才有价值；两者都高说明用例不具区分度，需要换更难/更具体的用例
- 同时观察：with_skill 是否多花了时间/token（成本权衡），以及是否有"多做事但没用"的浪费

## 迭代规则

- 第 1 轮：初版技能 → 跑评测 → 找出失败的 assertions → 改进 SKILL.md / references / scripts
- 第 2+ 轮：改进后再跑，对比 `iteration-N-1`，确认通过率上升
- 停止条件：用户满意 或 反馈全部通过 或 改进不再带来提升

## 已识别的高区分度用例方向

- 行业垂直清单（金融/政务/能源）：baseline 通常给不出行业特有项（支付清算、纵向加密装置等）
- 符合率计算：baseline 容易漏掉"不适用剔除分母"或"部分符合折算"的规则说明
- 红线问题整改：baseline 容易给空泛建议（"加强管理"），技能应给出具体可落地措施
