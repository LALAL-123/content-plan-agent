# c03_over_budget：预算超限（参考实例）：P-A 估算 12 > 10，改选 P-B 估算 8 后保存（运行 1/1）

- 模型：`mock:scripted-policy`
- 结束状态：`completed`（model_finished）
- 决策轮数：8；业务工具调用：7

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
| 1 | `get_task_state` | {} | {"request_id": "PLAN-C03", "pending_steps": ["material_search", "cost_estimate", "script_writing", "plan_save"], "plan_saved": false, "materials": null, "estimates": {}, "script": null, "plan": null, "hint": "非空字段是此前已成功的步骤结果，可直接复用；pending_steps 是仍需完成的步骤", "ok": true} | 先查看此请求是否已有进度，避免重复执行 |
| 2 | `search_materials` | {"topic": "冬季露营"} | {"query": ["冬季露营"], "count": 3, "materials": [{"material_id": "A01", "topic": "冬季露营", "type": "图片", "title": "雪地帐篷实拍 12 张", "tags": ["露营", "冬季", "帐篷", "户外"], "license": "自有"}, {"material_id": "A02", "topic": "冬季露营", "type": "视频", "title": "篝火与星空延时 40 秒", "tags": ["露营", "冬季", "夜景"], "license": "自有"}, {"material_id": "A03", "topic": "冬季露营", "type": "UGC", "tit… | 检索主题“冬季露营”的素材 |
| 3 | `list_production_options` | {} | {"options": [{"option_id": "P-A", "name": "达人合拍 + 精剪", "desc": "邀请垂类达人出镜，专业剪辑"}, {"option_id": "P-B", "name": "自制口播 + 模板剪辑", "desc": "团队成员出镜口播，套用剪辑模板"}, {"option_id": "P-C", "name": "图文轮播", "desc": "用现有图片做 6 页图文"}], "note": "费用和耗时请用 estimate_cost 估算", "ok": true} | 查看可选制作方式，准备估算 |
| 4 | `estimate_cost` | {"option_id": "P-A"} | {"option_id": "P-A", "total_cost": 12, "budget": 10, "within_budget": false, "total_hours": 51, "hours_until_deadline": 129.0, "within_deadline": true, "budget_gap": 2, "time_gap_hours": 0, "option_name": "达人合拍 + 精剪", "breakdown": [{"item": "素材检索与授权整理", "cost": 1, "hours": 1}, {"item": "脚本撰写", "cost": 2, "hours": 2}, {"item": "达人合拍 + 精剪", "cost": 9, "hours":… | 估算 P-A（用户偏好方案） |
| 5 | `estimate_cost` | {"option_id": "P-B"} | {"option_id": "P-B", "total_cost": 8, "budget": 10, "within_budget": true, "total_hours": 23, "hours_until_deadline": 129.0, "within_deadline": true, "budget_gap": 0, "time_gap_hours": 0, "option_name": "自制口播 + 模板剪辑", "breakdown": [{"item": "素材检索与授权整理", "cost": 1, "hours": 1}, {"item": "脚本撰写", "cost": 2, "hours": 2}, {"item": "自制口播 + 模板剪辑", "cost": 5, "hours… | 估算 P-B（已估 ['P-A'] 均不满足约束） |
| 6 | `generate_script` | {"topic": "冬季露营", "material_ids": ["A01", "A02", "A03"]} | {"script_id": "S-578aca", "source": "generator", "topic": "冬季露营", "material_ids": ["A01", "A02", "A03"], "outline": ["开场：雪地帐篷实拍 12 张 引出“冬季露营”", "段落：围绕《篝火与星空延时 40 秒》展开", "段落：围绕《用户露营故事 5 条（已获授权）》展开", "结尾：引导关注与互动"], "ok": true} | 按所选方案生成脚本 |
| 7 | `save_plan` | {"option_id": "P-B", "script_id": "S-578aca", "material_ids": ["A01", "A02", "A03"]} | {"plan_id": "PLAN-d023ce67", "version": 1, "content_hash": "0ecc2a23414f", "option_id": "P-B", "script_id": "S-578aca", "material_ids": ["A01", "A02", "A03"], "total_cost": 8, "total_hours": 23, "deduplicated": false, "ok": true} | P-B 费用 8 ≤ 预算 10，保存方案 |
| 8 | `finish` | status=completed | 护栏校正 0 处 | 方案已保存，提交结果 |

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
    "plan_id": "PLAN-d023ce67"
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
      "detail": "P-A=12；P-B=8"
    },
    {
      "step": "script_writing",
      "status": "done",
      "detail": "S-578aca"
    },
    {
      "step": "plan_save",
      "status": "done",
      "detail": "PLAN-d023ce67"
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
  "summary": "选用 自制口播 + 模板剪辑，费用 8/10，耗时 23h，方案 PLAN-d023ce67 已保存。"
}
```
