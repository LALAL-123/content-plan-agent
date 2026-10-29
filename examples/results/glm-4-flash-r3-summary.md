# 验收结果（openai-compat:glm-4-flash）

检查通过 30/35。逐条 Trace 见 `examples/runs/glm-4-flash-r3/`。

| 用例 | 覆盖验收点 | 结束状态 | 检查通过 |
|---|---|---|---|
| c01_normal | 正常完成 | failed | 0/1 |
| c02_missing_budget_deadline | 缺预算或截止时间 | failed | 2/4 |
| c03_over_budget | 预算超限 | failed | 0/1 |
| c04_tool_failure_fallback | 工具失败 | completed | 5/5 |
| c05_infeasible | 预算超限 | infeasible | 4/4 |
| c06_repeat_execution | 重复执行 | completed → completed | 4/4 |
| c07_resume_after_failure | 工具失败、重复执行、失败步骤续跑 | failed_partial → completed | 3/4 |
| c08_deadline_tight | 正常完成、预算超限 | completed | 3/3 |
| c09_save_failure | 工具失败 | failed_partial | 5/5 |
| c10_step_limit | 步数上限 | incomplete | 4/4 |

## 未通过的检查

- c01_normal：检查执行出错（输出结构不完整）（KeyError: 'plan'）
- c02_missing_budget_deadline：状态 needs_input（failed）
- c02_missing_budget_deadline：gaps 写明缺预算与截止时间（['未完成：llm_error']）
- c03_over_budget：检查执行出错（输出结构不完整）（KeyError: 'tool_results'）
- c07_resume_after_failure：续跑复用素材与估算（）
