# c03_over_budget：预算超限（参考实例）：P-A 估算 12 > 10，改选 P-B 估算 8 后保存（运行 1/1）

- 模型：`openai-compat:glm-4-flash`
- 结束状态：`failed`（llm_error）
- 决策轮数：1；业务工具调用：0

## 输入

```json
{
  "request_id": "PLAN-C03",
  "topic": "冬季露营",
  "budget": 10,
  "deadline": "2026-11-08 18:00",
  "preferred_option": "P-A"
}
```

## 执行记录

| 步骤 | 动作 | 参数 | 返回摘要 | 决策依据 |
|---|---|---|---|---|
| 1 | llm_error | — | Connection error. | — |
| 1 | **停止** | — | failed：llm_error | 达到执行上限或模型服务异常 |

## 最终输出

```json
{
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
  "material_ids": [],
  "estimates": {},
  "saved": false,
  "gaps": [
    "未完成：llm_error"
  ],
  "summary": "达到执行上限，已成功步骤已写入台账，重新提交同一请求可续跑。",
  "task_status": "failed",
  "stop_reason": "llm_error"
}
```
