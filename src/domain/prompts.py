SYSTEM_PROMPT = """你是运营团队的“内容任务规划”助手。目标：在预算和截止时间内，为给定主题产出一份可执行的内容活动方案并保存；做不到时说明缺口。

工作方式：每一轮根据已有工具结果选择下一个动作。
1. 预算（budget）或截止时间（deadline）缺失：不要猜，直接 finish，task_status=needs_input，在 gaps 里写明缺什么。
2. 先调用 get_task_state：此前已成功的步骤（素材、估算、脚本、已保存方案）直接复用，不要重做；plan_saved=true 时不要重复保存。pending_steps 列出仍需完成的步骤，必须把它们做完（或确认无法完成）才能 finish；plan_saved=false 时不能声称已保存。
3. search_materials 检索素材；没有结果可以换关键词再试一次，仍没有就说明缺口。
4. list_production_options 查看制作方式，用 estimate_cost 估算。优先估算用户的 preferred_option；若超预算或超截止时间，改估其他方式，选一个两者都满足的。都不满足时 task_status=infeasible，并写清最接近方案的预算缺口/时间缺口。
5. generate_script 生成脚本；失败可以重试一次，仍失败可改用 get_script_template（在 steps 中说明是替代方案）。
6. save_plan 保存方案；失败时如实报告，不能说已保存。
7. 调用 finish。steps 中每一步的 status 只能按工具实际结果填写：done / failed / not_run / reused；失败的步骤不能写成 done。
total_cost 必须等于所选方式 estimate_cost 返回的 total_cost。不要编造工具没有返回的数字。"""

_STEP = {
    "type": "object",
    "properties": {
        "step": {"type": "string", "enum": ["material_search", "cost_estimate", "script_writing", "plan_save"]},
        "status": {"type": "string", "enum": ["done", "failed", "not_run", "reused"]},
        "detail": {"type": "string"},
    },
    "required": ["step", "status"],
}

FINISH_PARAMETERS = {
    "type": "object",
    "properties": {
        "plan": {"type": "object", "properties": {
            "option_id": {"type": "string", "description": "所选制作方式；没有可行方式填空字符串"},
            "script_id": {"type": "string"},
            "material_ids": {"type": "array", "items": {"type": "string"}},
        }},
        "steps": {"type": "array", "items": _STEP},
        "total_cost": {"type": "number", "description": "所选方式的估算总费用；无方案填 0"},
        "saved": {"type": "boolean"},
        "task_status": {"type": "string", "enum": ["completed", "needs_input", "infeasible", "failed_partial"]},
        "gaps": {"type": "array", "items": {"type": "string"}, "description": "未完成原因或缺口"},
        "summary": {"type": "string"},
    },
    "required": ["plan", "steps", "total_cost", "saved", "task_status", "summary"],
}
