# c05_infeasible：无可行方案：预算 4 低于最便宜方案 5，返回未完成及缺口（运行 1/1）

- 模型：`mock:scripted-policy`
- 结束状态：`infeasible`（model_finished）
- 决策轮数：7；业务工具调用：6

## 输入

```json
{
  "request_id": "PLAN-C05",
  "topic": "冬季露营",
  "budget": 4,
  "deadline": "2026-11-08 18:00",
  "preferred_option": "P-A"
}
```

## 执行记录

| 步骤 | 动作 | 参数 | 返回摘要 | 决策依据 |
|---|---|---|---|---|
| 1 | `get_task_state` | {} | {"request_id": "PLAN-C05", "pending_steps": ["material_search", "cost_estimate", "script_writing", "plan_save"], "plan_saved": false, "materials": null, "estimates": {}, "script": null, "plan": null, "hint": "非空字段是此前已成功的步骤结果，可直接复用；pending_steps 是仍需完成的步骤", "ok": true} | 先查看此请求是否已有进度，避免重复执行 |
| 2 | `search_materials` | {"topic": "冬季露营"} | {"query": ["冬季露营"], "count": 3, "materials": [{"material_id": "A01", "topic": "冬季露营", "type": "图片", "title": "雪地帐篷实拍 12 张", "tags": ["露营", "冬季", "帐篷", "户外"], "license": "自有"}, {"material_id": "A02", "topic": "冬季露营", "type": "视频", "title": "篝火与星空延时 40 秒", "tags": ["露营", "冬季", "夜景"], "license": "自有"}, {"material_id": "A03", "topic": "冬季露营", "type": "UGC", "tit… | 检索主题“冬季露营”的素材 |
| 3 | `list_production_options` | {} | {"options": [{"option_id": "P-A", "name": "达人合拍 + 精剪", "desc": "邀请垂类达人出镜，专业剪辑"}, {"option_id": "P-B", "name": "自制口播 + 模板剪辑", "desc": "团队成员出镜口播，套用剪辑模板"}, {"option_id": "P-C", "name": "图文轮播", "desc": "用现有图片做 6 页图文"}], "note": "费用和耗时请用 estimate_cost 估算", "ok": true} | 查看可选制作方式，准备估算 |
| 4 | `estimate_cost` | {"option_id": "P-A"} | {"option_id": "P-A", "total_cost": 12, "budget": 4, "within_budget": false, "total_hours": 51, "hours_until_deadline": 129.0, "within_deadline": true, "budget_gap": 8, "time_gap_hours": 0, "option_name": "达人合拍 + 精剪", "breakdown": [{"item": "素材检索与授权整理", "cost": 1, "hours": 1}, {"item": "脚本撰写", "cost": 2, "hours": 2}, {"item": "达人合拍 + 精剪", "cost": 9, "hours": … | 估算 P-A（用户偏好方案） |
| 5 | `estimate_cost` | {"option_id": "P-B"} | {"option_id": "P-B", "total_cost": 8, "budget": 4, "within_budget": false, "total_hours": 23, "hours_until_deadline": 129.0, "within_deadline": true, "budget_gap": 4, "time_gap_hours": 0, "option_name": "自制口播 + 模板剪辑", "breakdown": [{"item": "素材检索与授权整理", "cost": 1, "hours": 1}, {"item": "脚本撰写", "cost": 2, "hours": 2}, {"item": "自制口播 + 模板剪辑", "cost": 5, "hours… | 估算 P-B（已估 ['P-A'] 均不满足约束） |
| 6 | `estimate_cost` | {"option_id": "P-C"} | {"option_id": "P-C", "total_cost": 5, "budget": 4, "within_budget": false, "total_hours": 9, "hours_until_deadline": 129.0, "within_deadline": true, "budget_gap": 1, "time_gap_hours": 0, "option_name": "图文轮播", "breakdown": [{"item": "素材检索与授权整理", "cost": 1, "hours": 1}, {"item": "脚本撰写", "cost": 2, "hours": 2}, {"item": "图文轮播", "cost": 2, "hours": 6}], "ok": t… | 估算 P-C（已估 ['P-A', 'P-B'] 均不满足约束） |
| 7 | `finish` | status=infeasible | 护栏校正 0 处 | 所有制作方式都超出预算或截止时间 |

## 最终输出

```json
{
  "plan": {
    "option_id": null,
    "option_name": null,
    "script_id": null,
    "material_ids": [
      "A01",
      "A02",
      "A03"
    ],
    "plan_id": null
  },
  "steps": [
    {
      "step": "material_search",
      "status": "done",
      "detail": "3 条素材"
    },
    {
      "step": "cost_estimate",
      "status": "done",
      "detail": "P-A=12；P-B=8；P-C=5"
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
        "within_budget": false,
        "within_deadline": true
      },
      "P-C": {
        "total_cost": 5,
        "total_hours": 9,
        "within_budget": false,
        "within_deadline": true
      }
    },
    "script": null
  },
  "total_cost": 0,
  "budget": 4,
  "saved": false,
  "deduplicated": false,
  "task_status": "infeasible",
  "gaps": [
    "最便宜的 P-C 需 5，预算 4，缺口 1；时间缺口 0 小时"
  ],
  "summary": "没有满足约束的方案：最便宜的 P-C 需 5，预算 4，缺口 1；时间缺口 0 小时"
}
```
