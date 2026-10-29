# c06_repeat_execution：重复执行：同一请求执行两次，只保存一份方案、不重做已成功步骤（运行 2/2）

- 模型：`mock:scripted-policy`
- 结束状态：`completed`（model_finished）
- 决策轮数：2；业务工具调用：1

## 输入

```json
{
  "request_id": "PLAN-C06",
  "topic": "冬季露营",
  "budget": 10,
  "deadline": "2026-11-08 18:00",
  "preferred_option": "P-A"
}
```

## 执行记录

| 步骤 | 动作 | 参数 | 返回摘要 | 决策依据 |
|---|---|---|---|---|
| 1 | `get_task_state` | {} | {"request_id": "PLAN-C06", "pending_steps": [], "plan_saved": true, "materials": {"material_ids": ["A01", "A02", "A03"], "count": 3}, "estimates": {"P-A": {"option_id": "P-A", "total_cost": 12, "budget": 10, "within_budget": false, "total_hours": 51, "hours_until_deadline": 129.0, "within_deadline": true, "budget_gap": 2, "time_gap_hours": 0, "option_name": … | 先查看此请求是否已有进度，避免重复执行 |
| 2 | `finish` | status=completed | 护栏校正 0 处 | 此前已保存方案，直接复用，不重复执行 |

## 最终输出

```json
{
  "plan": {
    "option_id": "P-B",
    "option_name": "自制口播 + 模板剪辑",
    "script_id": "S-578aca",
    "material_ids": [
      "A01",
      "A02",
      "A03"
    ],
    "plan_id": "PLAN-bfa6616e"
  },
  "steps": [
    {
      "step": "material_search",
      "status": "reused",
      "detail": "复用此前检索结果"
    },
    {
      "step": "cost_estimate",
      "status": "reused",
      "detail": "复用此前估算"
    },
    {
      "step": "script_writing",
      "status": "reused",
      "detail": "复用此前脚本 S-578aca"
    },
    {
      "step": "plan_save",
      "status": "reused",
      "detail": "此前已保存 PLAN-bfa6616e"
    }
  ],
  "tool_results": {
    "estimates": {
      "P-A": {
        "total_cost": 12,
        "total_hours": 51,
        "within_budget": false,
        "within_deadline": true
      },
      "P-B": {
        "total_cost": 8,
        "total_hours": 23,
        "within_budget": true,
        "within_deadline": true
      }
    },
    "script": {
      "script_id": "S-578aca",
      "source": "generator",
      "topic": "冬季露营",
      "material_ids": [
        "A01",
        "A02",
        "A03"
      ],
      "outline": [
        "开场：雪地帐篷实拍 12 张 引出“冬季露营”",
        "段落：围绕《篝火与星空延时 40 秒》展开",
        "段落：围绕《用户露营故事 5 条（已获授权）》展开",
        "结尾：引导关注与互动"
      ]
    }
  },
  "total_cost": 8,
  "budget": 10,
  "saved": true,
  "deduplicated": false,
  "task_status": "completed",
  "gaps": [],
  "summary": "方案 PLAN-bfa6616e 已存在（重复执行未新建），费用 8。"
}
```
