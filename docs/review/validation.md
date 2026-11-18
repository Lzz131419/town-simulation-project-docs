# 本地文档验证记录

- 日期：2026-11-18；检查者：本轮Codex执行与静态复核，不是人工PR评审。
- 工作目录：仓库根目录。
- 命令：`python3 docs/tools/validate_docs.py`、`git diff --check`。
- 机制探针：Node.js v24.22.3，结果见[SP-01](../spike/atomic-replay-result.md)。

## 检查范围
检查Markdown本地链接、代码围栏、五模块七章、GWT结构、故事/边界引用、AC任务覆盖、任务八列、12份工单字段、六名成员、非作者Reviewer、分支模板、任务DAG和关键路径、初始人口/资金。

## 实际输出
```text
PASS: 58 Markdown files; 156 local links resolve
PASS: 5 modules; 20 unique GWT ACs; every story and boundary linked
PASS: 12 tasks; all ACs covered; owners/reviewers/Issue bodies/branch templates valid
PASS: DAG acyclic; T01 -> T04 -> T05 -> T02 -> T03 -> T12 = 15 working days; 27 person-days
PASS: fixtures match population and money; no production code in src/ or tests/
LIMIT: checks structure and references only, not semantic correctness, implementation, human review or GitHub status
```

`git diff --check`无输出，退出码0；机制探针5/5通过。原始文档检查输出见[validation-output](validation-output.txt)。

## 不覆盖的内容
脚本只证明结构与引用有效，不能自动证明每条业务规则合理。语义检查与修正见[baseline-review](baseline-review.md)。新Spec冷启动状态见[实际记录](../test/cold-start-01.md)；线上看板与人工评审需后续真实操作。业务实现、业务测试、性能与浏览器兼容性未验收。

## 冷启动证据复核
两轮输入与原始回答的SHA-256均匹配证据清单；归档输入中的完整Spec匹配各轮Spec哈希；两轮中立问题和执行约束完全一致；当前输入等于第二轮输入，当前M4文件匹配第二轮被测Spec。复测原始回答中的JSON可解析，ok=false、错误码与空events均符合预期。这些是证据完整性检查，不扩大冷启动覆盖范围。
