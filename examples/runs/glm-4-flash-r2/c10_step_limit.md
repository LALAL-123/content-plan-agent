# c10_step_limit：执行上限：3 轮内无法完成，返回未完成并保留已成功步骤（运行 1/1）

- 模型：`openai-compat:glm-4-flash`
- 结束状态：`incomplete`（step_limit_reached）
- 决策轮数：3；业务工具调用：3

## 输入

```json
{
  "request_id": "PLAN-C10",
  "topic": "冬季露营",
  "budget": 10,
  "deadline": "2026-11-08 18:00",
  "preferred_option": "P-A"
}
```

## 执行记录

| 步骤 | 动作 | 参数 | 返回摘要 | 决策依据 |
|---|---|---|---|---|
| 1 | `get_task_state` | {} | {"request_id": "PLAN-C10", "pending_steps": ["material_search", "cost_estimate", "script_writing", "plan_save"], "plan_saved": false, "materials": null, "estimates": {}, "script": null, "plan": null, "hint": "非空字段是此前已成功的步骤结果，可直接复用；pending_steps 是仍需完成的步骤", "ok": true} | 查看之前是否已有成功步骤，避免重复工作。 |
| 2 | `search_materials` | {"topic": "冬季露营"} | {"query": ["冬季露营"], "count": 3, "materials": [{"material_id": "A01", "topic": "冬季露营", "type": "图片", "title": "雪地帐篷实拍 12 张", "tags": ["露营", "冬季", "帐篷", "户外"], "license": "自有"}, {"material_id": "A02", "topic": "冬季露营", "type": "视频", "title": "篝火与星空延时 40 秒", "tags": ["露营", "冬季", "夜景"], "license": "自有"}, {"material_id": "A03", "topic": "冬季露营", "type": "UGC", "tit… | 检索与冬季露营相关的素材。 |
| 3 | `list_production_options` | {} | {"options": [{"option_id": "P-A", "name": "达人合拍 + 精剪", "desc": "邀请垂类达人出镜，专业剪辑"}, {"option_id": "P-B", "name": "自制口播 + 模板剪辑", "desc": "团队成员出镜口播，套用剪辑模板"}, {"option_id": "P-C", "name": "图文轮播", "desc": "用现有图片做 6 页图文"}], "note": "费用和耗时请用 estimate_cost 估算", "ok": true} | 列出制作方式选项。 |
| 3 | **停止** | — | incomplete：step_limit_reached | 达到执行上限或模型服务异常 |

## 最终输出

```json
{
  "steps": [
    {
      "step": "material_search",
      "status": "done",
      "detail": "3 条素材"
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
  "material_ids": [
    "A01",
    "A02",
    "A03"
  ],
  "estimates": {},
  "saved": false,
  "gaps": [
    "未完成：step_limit_reached"
  ],
  "summary": "达到执行上限，已成功步骤已写入台账，重新提交同一请求可续跑。",
  "task_status": "incomplete",
  "stop_reason": "step_limit_reached"
}
```
