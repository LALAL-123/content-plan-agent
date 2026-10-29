# c07_resume_after_failure：失败续跑（加分项）：首次脚本与模板都失败；服务恢复后再次提交，只补做失败步骤（运行 2/2）

- 模型：`mock:scripted-policy`
- 结束状态：`completed`（model_finished）
- 决策轮数：5；业务工具调用：4

## 输入

```json
{
  "request_id": "PLAN-C07",
  "topic": "冬季露营",
  "budget": 10,
  "deadline": "2026-11-08 18:00",
  "preferred_option": "P-A"
}
```

## 执行记录

| 步骤 | 动作 | 参数 | 返回摘要 | 决策依据 |
|---|---|---|---|---|
| 1 | `get_task_state` | {} | {"request_id": "PLAN-C07", "pending_steps": ["script_writing", "plan_save"], "plan_saved": false, "materials": {"material_ids": ["A01", "A02", "A03"], "count": 3}, "estimates": {"P-A": {"option_id": "P-A", "total_cost": 12, "budget": 10, "within_budget": false, "total_hours": 51, "hours_until_deadline": 129.0, "within_deadline": true, "budget_gap": 2, "time_… | 先查看此请求是否已有进度，避免重复执行 |
| 2 | `list_production_options` | {} | {"options": [{"option_id": "P-A", "name": "达人合拍 + 精剪", "desc": "邀请垂类达人出镜，专业剪辑"}, {"option_id": "P-B", "name": "自制口播 + 模板剪辑", "desc": "团队成员出镜口播，套用剪辑模板"}, {"option_id": "P-C", "name": "图文轮播", "desc": "用现有图片做 6 页图文"}], "note": "费用和耗时请用 estimate_cost 估算", "ok": true} | 查看可选制作方式，准备估算 |
| 3 | `generate_script` | {"topic": "冬季露营", "material_ids": ["A01", "A02", "A03"]} | {"script_id": "S-578aca", "source": "generator", "topic": "冬季露营", "material_ids": ["A01", "A02", "A03"], "outline": ["开场：雪地帐篷实拍 12 张 引出“冬季露营”", "段落：围绕《篝火与星空延时 40 秒》展开", "段落：围绕《用户露营故事 5 条（已获授权）》展开", "结尾：引导关注与互动"], "ok": true} | 按所选方案生成脚本 |
| 4 | `save_plan` | {"option_id": "P-B", "script_id": "S-578aca", "material_ids": ["A01", "A02", "A03"]} | {"plan_id": "PLAN-c4864720", "version": 1, "content_hash": "0ecc2a23414f", "option_id": "P-B", "script_id": "S-578aca", "material_ids": ["A01", "A02", "A03"], "total_cost": 8, "total_hours": 23, "deduplicated": false, "ok": true} | P-B 费用 8 ≤ 预算 10，保存方案 |
| 5 | `finish` | status=completed | 护栏校正 0 处 | 方案已保存，提交结果 |

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
    "plan_id": "PLAN-c4864720"
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
      "status": "done",
      "detail": "S-578aca"
    },
    {
      "step": "plan_save",
      "status": "done",
      "detail": "PLAN-c4864720"
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
      ],
      "ok": true
    }
  },
  "total_cost": 8,
  "budget": 10,
  "saved": true,
  "deduplicated": false,
  "task_status": "completed",
  "gaps": [],
  "summary": "选用 自制口播 + 模板剪辑，费用 8/10，耗时 23h，方案 PLAN-c4864720 已保存。"
}
```
