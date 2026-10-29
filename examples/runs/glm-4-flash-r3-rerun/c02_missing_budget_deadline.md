# c02_missing_budget_deadline：缺预算和截止时间：不猜测，请求补充（运行 1/1）

- 模型：`openai-compat:glm-4-flash`
- 结束状态：`needs_input`（model_finished）
- 决策轮数：2；业务工具调用：1

## 输入

```json
{
  "request_id": "PLAN-C02",
  "topic": "冬季露营",
  "preferred_option": "P-A"
}
```

## 执行记录

| 步骤 | 动作 | 参数 | 返回摘要 | 决策依据 |
|---|---|---|---|---|
| 1 | `get_task_state` | {} | {"request_id": "PLAN-C02", "pending_steps": ["material_search", "cost_estimate", "script_writing", "plan_save"], "plan_saved": false, "materials": null, "estimates": {}, "script": null, "plan": null, "hint": "非空字段是此前已成功的步骤结果，可直接复用；pending_steps 是仍需完成的步骤", "ok": true} | 查看之前是否已经完成了任何步骤。 |
| 2 | `finish` | status=needs_input | 护栏校正 0 处 | 任务开始，初始化任务状态。 |

## 最终输出

```json
{
  "plan": {
    "option_id": null,
    "option_name": null,
    "script_id": null,
    "material_ids": [],
    "plan_id": null
  },
  "steps": [
    {
      "step": "material_search",
      "status": "not_run",
      "detail": ""
    },
    {
      "step": "cost_estimate",
      "status": "not_run",
      "detail": ""
    },
    {
      "step": "script_writing",
      "status": "not_run",
      "detail": ""
    },
    {
      "step": "plan_save",
      "status": "not_run",
      "detail": ""
    }
  ],
  "tool_results": {
    "estimates": {},
    "script": null
  },
  "total_cost": 0,
  "budget": null,
  "saved": false,
  "deduplicated": false,
  "task_status": "needs_input",
  "gaps": [
    "budget",
    "deadline",
    "缺少：预算、截止时间"
  ],
  "summary": "任务初始化完成，等待输入预算和截止时间。"
}
```
