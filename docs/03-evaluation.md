# 03 评估

## 测试结构

| 层次 | 文件 | 内容 |
|---|---|---|
| 内核 | `tests/test_core.py` | 步数/调用上限、finish 同轮拒绝、工具异常转观察、故障注入、模型异常、非法 finish 退回 |
| 业务 | `tests/test_domain.py` | 参考实例估算值、截止时间判断、保存复核与幂等、缺约束拒绝保存、台账续跑、护栏校正 |
| 验收 | `tests/test_domain.py::test_case_acceptance_with_offline_mock` | 10 个用例逐条跑验收检查 |
| 评估 | `python -m src.cli eval --llm mock|openai` | 同一套检查用于 Mock 与真实模型 |

验收检查（`src/domain/checks.py`）只看最终结果、工具调用事实和台账，不比对步骤顺序。其中“没有把失败步骤记为成功”一条对每个 done 步骤反查本轮是否有成功的工具记录。

## 用例：预期与实际（离线 Mock）

全部结果：[examples/results/mock-summary.md](../examples/results/mock-summary.md)，测试输出：[examples/results/pytest.txt](../examples/results/pytest.txt)。

| 用例 | 预期 | 实际 | Trace |
|---|---|---|---|
| c01 正常完成 | 预算 15，P-A（12）可行，保存 | 一致，5/5 | [c01](../examples/runs/mock/c01_normal.md) |
| c02 缺预算与截止 | needs_input，gaps 写明两项，不调用生成/保存 | 一致，4/4 | [c02](../examples/runs/mock/c02_missing_budget_deadline.md) |
| c03 预算超限（参考实例） | P-A 估 12 > 10 → 改估 P-B 得 8 → 保存，completed | 一致，4/4 | [c03](../examples/runs/mock/c03_over_budget.md) |
| c04 工具失败 | 脚本两次失败 → 模板替代 → 保存；素材与估算保留 | 一致，5/5 | [c04](../examples/runs/mock/c04_tool_failure_fallback.md) |
| c05 无可行方案 | infeasible，写明缺口，不保存 | 一致，4/4 | [c05](../examples/runs/mock/c05_infeasible.md) |
| c06 重复执行 | 两次同一方案 ID、版本 1，第二次不重做检索与脚本 | 一致，4/4 | [run1](../examples/runs/mock/c06_repeat_execution_run1.md) / [run2](../examples/runs/mock/c06_repeat_execution_run2.md) |
| c07 失败续跑 | 首次 failed_partial、脚本 failed、素材与估算 done；第二次只补做脚本与保存 | 一致，4/4 | [run1](../examples/runs/mock/c07_resume_after_failure_run1.md) / [run2](../examples/runs/mock/c07_resume_after_failure_run2.md) |
| c08 截止时间紧 | P-A、P-B 超期 → P-C | 一致，3/3 | [c08](../examples/runs/mock/c08_deadline_tight.md) |
| c09 保存失败 | failed_partial，plan_save=failed，其余步骤保留 | 一致，5/5 | [c09](../examples/runs/mock/c09_save_failure.md) |
| c10 步数上限 | 3 轮后 incomplete，带已成功步骤，不保存 | 一致，4/4 | [c10](../examples/runs/mock/c10_step_limit.md) |

Mock 运行中护栏校正次数为 0；护栏拦截能力由 `test_guard_*` 单测验证（失败步骤记为 done、费用不符、虚报保存、选超预算方案）。

## 真实模型

模型：智谱 GLM-4-Flash（免费版，OpenAI 兼容接口，temperature=0）。每轮跑全部 10 个用例（12 次运行），与 Mock 共用同一套检查。

| 轮次 | 代码 | 检查通过 | 护栏校正 | 汇总 | Trace |
|---|---|---|---|---|---|
| 第 1 轮 | 初版 | 40/42 | 9 | [r1 汇总](../examples/results/glm-4-flash-r1-summary.md) | [glm-4-flash-r1/](../examples/runs/glm-4-flash-r1/) |
| 第 2 轮 | 按第 1 轮问题修改 | 40/42 | 1 | [r2 汇总](../examples/results/glm-4-flash-r2-summary.md) | [glm-4-flash-r2/](../examples/runs/glm-4-flash-r2/) |
| 第 3 轮 | 修正 gaps 表述 | 28/29（7 个用例）+ 重跑 13/13（3 个用例）= 41/42 | 1 | [r3 汇总](../examples/results/glm-4-flash-r3-summary.md)、[重跑汇总](../examples/results/glm-4-flash-r3-rerun-summary.md) | [glm-4-flash-r3/](../examples/runs/glm-4-flash-r3/)、[glm-4-flash-r3-rerun/](../examples/runs/glm-4-flash-r3-rerun/) |

第 3 轮的 c01–c03 在第 1 步调用模型时返回 `Connection error.`（与另一个项目的评估同时发起，免费接口并发受限），模型没有做出任何决策；智能体按设计返回 failed / llm_error。这三条原始记录保留在 `glm-4-flash-r3/`，同一份代码单独重跑的记录在 `glm-4-flash-r3-rerun/`。

### 每轮的问题与修改

| 现象 | 修改（在下一轮运行前完成） |
|---|---|
| 第 1 轮 c07 第二次执行：模型调用 `get_task_state` 后直接 finish，自报已保存；护栏按台账改为 saved=false、failed_partial | 第 2 轮：`get_task_state` 返回 `pending_steps` 与 `plan_saved`，提示词要求做完 pending_steps 才能结束 |
| 第 1 轮 c09：gaps 里写的是英文步骤名 `plan_save 失败` | 第 2 轮：护栏补写的失败步骤用中文名 |
| 模型把调用写成文本 | 第 2 轮：内核恢复写明工具名和 JSON 参数的文本调用，Trace 标注 |
| 第 2 轮 c02：模型 gaps 只写 `["budget", "deadline"]`，护栏把英文字段名当成已说明，没有补中文 | 第 3 轮：护栏只认“预算”“截止”的中文说明，否则补一条“缺少：预算、截止时间” |

第 2 轮的修改直接见效：[第 2 轮 c07 第二次执行](../examples/runs/glm-4-flash-r2/c07_resume_after_failure_run2.md) 从 failed_partial 变为 completed：模型按 pending_steps 补做脚本并保存，不再虚报已保存。

### 仍未通过：续跑时重做已成功步骤（c07）

第 2、3 轮 c07 第二次执行中，`get_task_state` 已返回 `pending_steps=["script_writing", "plan_save"]`，模型仍重新调用了 `search_materials` 与 `estimate_cost`，然后补做脚本并保存（[第 3 轮 run2](../examples/runs/glm-4-flash-r3/c07_resume_after_failure_run2.md)）。结果正确（completed，费用 8，方案只保存一份），但违背“只补做失败步骤”。检素材和估算是只读操作，重做没有副作用；若这两步昂贵或有配额，应在工具层面直接返回台账中的结果并标 `reused`，不依赖模型自觉。

### 体现“根据工具结果调整”的真实模型路径

| 路径 | 工具结果 | 模型的调整 |
|---|---|---|
| [c03 预算超限（参考实例）](../examples/runs/glm-4-flash-r2/c03_over_budget.md) | `estimate_cost(P-A)` 返回 total_cost=12、within_budget=false | 改估 P-B 得 8，选 P-B 生成脚本并保存 |
| [c08 截止时间紧](../examples/runs/glm-4-flash-r3/c08_deadline_tight.md) | P-A、P-B 都 within_deadline=false | 继续估 P-C（9 小时 < 10 小时），选 P-C 保存 |
| [c04 工具失败](../examples/runs/glm-4-flash-r3/c04_tool_failure_fallback.md) | `generate_script` 返回 503 | 改用 `get_script_template`，用模板脚本保存 |
| [c06 重复执行](../examples/runs/glm-4-flash-r3/c06_repeat_execution_run2.md) | `get_task_state` 返回 plan_saved=true、pending_steps 为空 | 不再调用任何业务工具，直接返回已保存的方案 |

### 结论

- 三轮都在 40/42 以上；决策依据是结构化字段（`within_budget`、`within_deadline`、`pending_steps`），这一档免费模型也能稳定使用。
- 护栏校正从第 1 轮 9 处降到第 2、3 轮各 1 处：提示词和工具返回补齐之后，模型自己给出的结论多数已与事实一致；剩下的 1 处，第 2 轮是 c07 首次执行的费用合计（模型填 0，按估算改为 8），第 3 轮是 c07 首次执行脚本与模板都失败时自报 completed（改为 failed_partial）。
- 剩余缺陷是续跑时重做只读步骤，见上文；下一步在工具层面复用台账结果。

## 失败与限制

- 离线 Mock 是条件分支，它通过只说明流程与检查闭合，不证明真实模型的重规划能力。
- c01 要求选偏好方案 P-A；若真实模型在预算充足时主动选更便宜的方案，该条会失败——这反映模型没有尊重用户偏好，保留为严格项。
- c06 要求第二次执行不调用 `search_materials` / `generate_script`；真实模型若不先查台账就会失败，这正是要暴露的问题。
- 未覆盖：工具超时、估算数据本身错误、多个请求并发写台账。
