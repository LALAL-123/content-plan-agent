# c02_missing_budget_deadline：缺预算和截止时间：不猜测，请求补充（运行 1/1）

- 模型：`mock:scripted-policy`
- 结束状态：`needs_input`（model_finished）
- 决策轮数：1；业务工具调用：0

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
| 1 | `finish` | status=needs_input | 护栏校正 0 处 | 输入缺少硬约束，不能估算是否可行 |

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
    "缺少预算、截止时间，请补充后重新提交"
  ],
  "summary": "缺少预算、截止时间，未开始规划。"
}
```
