# 验收结果（openai-compat:glm-4-flash）

检查通过 13/13。逐条 Trace 见 `examples/runs/glm-4-flash-r3-rerun/`。

| 用例 | 覆盖验收点 | 结束状态 | 检查通过 |
|---|---|---|---|
| c01_normal | 正常完成 | completed | 5/5 |
| c02_missing_budget_deadline | 缺预算或截止时间 | needs_input | 4/4 |
| c03_over_budget | 预算超限 | completed | 4/4 |

## 未通过的检查

无
