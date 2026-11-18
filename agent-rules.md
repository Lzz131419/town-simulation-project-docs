# 雾河镇 AI 协作规则

## 1. 开始任务前
阅读 context.md → 对应 spec → docs/architecture.md 与相关 ADR → plans/mvp1-plan.md 的任务条目。agent-rules.md 是跨工具约定，需由调用方显式提供，不宣称所有工具自动加载。

## 2. 修改边界
- 第6–9周文档基线保留在main提交03c9856。2026-11-18用户明确要求继续完成项目工程，现进入正式实现阶段，按任务白名单编写src/与tests/。
- 每个实现任务先有 Issue，再有一个任务分支。分支用 feature/issue-{真实编号}-{slug} 等规范；不得把 T01 当 GitHub Issue 号。
- 只修改该任务文件白名单。新增公共接口先更新 Spec/ADR 与依赖任务，不临时绕过契约。
- 文档重建可以修改 README、context、agent-rules、spec、adr、plans、docs、.github；本次不改历史 HTML 探针，也不提交原始课程 PDF。
- 不引入 context 禁止的第三方依赖；不自动改变成员权限、仓库保护规则或对外可见性。

## 3. 编码与事实约束
- ES modules；变量 const/let，不使用 var；规则模块不得访问 DOM、网络、Date.now 或 Math.random。
- 资源/资金使用非负安全整数，0–100 指标统一 clamp；显示文本用 textContent，禁止把导入字符串写入 innerHTML。
- 不在前端或仓库保存密钥。只用虚构人物测试。
- 错误结果必须匹配 Spec 错误码；失败不修改世界，不追加成功事件，诊断独立于快照。
- 不把“计划”“探针通过”“AI理解通过”写成正式功能验收通过。
- 不编造真人评审、GitHub Issue/PR号、看板状态或冷启动原始回答。

## 4. 验证与提交
文档检查执行 `python3 docs/tools/validate_docs.py`，探针按 docs/spike/plan.md 的独立命令执行。实现阶段使用 Node.js 22+ `node --test tests/*.test.mjs`；测试状态只能按实际执行结果记录。

PR 必须关联真实 Issue、Spec/AC、变更摘要、AI使用说明、验证证据、文件范围、风险与回滚；至少一名非作者人工评审。AI评审不代替人工签字。详情见 [PR准入清单](docs/review/pr-checklist.md)。

发现歧义先修订 Spec；若 Spec 已明确而实现错误，应修复实现，不得降低 AC 来掩盖错误。接口、模块边界、依赖方向变化新增 ADR；单纯内部重构不必新增 ADR。

## 5. 本轮交付状态
本轮已完成本地重建和检查，用户现已授权 GitHub 提交。提交前保留原 Git 历史；不强制推送、不虚构课堂 PR 演练。未来看板是任务进度真相源，本地计划是可审核的任务基线，不能把本地任务清单当成已建线上看板。

## 6. 实现阶段补充
允许按依赖建立堆叠任务分支与PR，避免伪造人工批准；每个PR只包含该任务增量。集成分支可以运行全部代码，但人工评审前任务保持Review、不关闭工单。工程脚本、CI、阶段说明及验证器由启动文档PR维护。用户授权开发不等于全组ADR签字。
