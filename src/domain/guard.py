"""结束护栏：步骤状态、费用合计、保存结果一律以工具返回为准。

模型决定执行顺序和是否换方案；护栏只校正与事实不符的结论：
失败步骤写成 done、费用与估算不符、选了超预算方案、虚报已保存。
"""
from __future__ import annotations

from ..core.agent import ToolRecord

STEPS = ["material_search", "cost_estimate", "script_writing", "plan_save"]
STEP_NAMES = {"material_search": "素材检索", "cost_estimate": "成本估算", "script_writing": "脚本撰写", "plan_save": "方案保存"}


def _feasible(est: dict | None) -> bool:
    return bool(est and est.get("within_budget") and est.get("within_deadline"))


def _err(rs: list[ToolRecord]) -> str:
    r = rs[-1]
    return r.result.get("error") or "; ".join(r.result.get("errors", [])) or "无结果"


def truth(records: list[ToolRecord]) -> dict:
    state = next((r.result for r in reversed(records) if r.tool == "get_task_state" and r.ok), {}) or {}
    by = lambda *tools: [r for r in records if r.tool in tools]

    steps, data = {}, {}
    search = by("search_materials")
    hits = [r for r in search if r.ok and r.result.get("count", 0) > 0]
    if hits:
        data["material_ids"] = [m["material_id"] for m in hits[-1].result["materials"]]
        steps["material_search"] = ("done", f"{len(data['material_ids'])} 条素材")
    elif state.get("materials"):
        data["material_ids"] = state["materials"]["material_ids"]
        steps["material_search"] = ("reused", "复用此前检索结果")
    elif search:
        steps["material_search"] = ("failed", _err(search) if not search[-1].ok else "没有匹配素材")
    else:
        steps["material_search"] = ("not_run", "")

    est_runs = by("estimate_cost")
    estimates = dict(state.get("estimates") or {})
    estimates.update({r.result["option_id"]: r.result for r in est_runs if r.ok})
    data["estimates"] = estimates
    if any(r.ok for r in est_runs):
        steps["cost_estimate"] = ("done", "；".join(f"{k}={v['total_cost']}" for k, v in estimates.items()))
    elif estimates:
        steps["cost_estimate"] = ("reused", "复用此前估算")
    elif est_runs:
        steps["cost_estimate"] = ("failed", _err(est_runs))
    else:
        steps["cost_estimate"] = ("not_run", "")

    scr = by("generate_script", "get_script_template")
    scr_ok = [r for r in scr if r.ok]
    if scr_ok:
        data["script"] = scr_ok[-1].result
        fallback = "（定制脚本失败，改用模板）" if scr_ok[-1].tool == "get_script_template" else ""
        steps["script_writing"] = ("done", data["script"]["script_id"] + fallback)
    elif state.get("script"):
        data["script"] = state["script"]
        steps["script_writing"] = ("reused", "复用此前脚本 " + state["script"]["script_id"])
    elif scr:
        steps["script_writing"] = ("failed", _err(scr))
    else:
        steps["script_writing"] = ("not_run", "")

    saves = by("save_plan")
    save_ok = [r for r in saves if r.ok]
    if save_ok:
        data["plan"] = save_ok[-1].result
        steps["plan_save"] = ("done", data["plan"]["plan_id"] + ("（重复保存，已去重）" if data["plan"].get("deduplicated") else ""))
    elif state.get("plan"):
        data["plan"] = state["plan"]
        steps["plan_save"] = ("reused", "此前已保存 " + state["plan"]["plan_id"])
    elif saves:
        steps["plan_save"] = ("failed", _err(saves))
    else:
        steps["plan_save"] = ("not_run", "")
    data["steps"] = [{"step": s, "status": steps[s][0], "detail": steps[s][1]} for s in STEPS]
    return data


def guard(args: dict, records: list[ToolRecord], payload: dict) -> tuple[dict, list[str]]:
    if not isinstance(args.get("steps"), list):
        raise ValueError("finish.steps 必须是数组")
    fixes: list[str] = []
    t = truth(records)
    claimed = {s.get("step"): s.get("status") for s in args["steps"] if isinstance(s, dict)}
    for s in t["steps"]:
        c = claimed.get(s["step"])
        if c in ("done", "reused") and s["status"] not in ("done", "reused"):
            fixes.append(f"{s['step']}：模型记为 {c}，工具结果为 {s['status']}")

    plan_args = args.get("plan") or {}
    option = plan_args.get("option_id") or None
    saved_plan = t.get("plan")
    if saved_plan and option != saved_plan["option_id"]:
        if option:
            fixes.append(f"方案以已保存的 {saved_plan['option_id']} 为准（模型填 {option}）")
        option = saved_plan["option_id"]
    est = t["estimates"].get(option) if option else None
    if option and est is None:
        fixes.append(f"方案 {option} 没有估算记录，撤销")
        option = None
    elif option and not _feasible(est) and not saved_plan:
        fixes.append(f"方案 {option} 超预算或超截止时间，不能作为结果")
        option, est = None, None
    total = est["total_cost"] if est else 0
    if args.get("total_cost") != total:
        fixes.append(f"total_cost 以估算为准：{args.get('total_cost')} → {total}")

    saved = bool(saved_plan)
    if bool(args.get("saved")) != saved:
        fixes.append(f"保存状态以工具结果为准：saved={saved}")

    missing = [k for k in ("budget", "deadline") if payload.get(k) in (None, "")]
    gaps = list(args.get("gaps") or [])
    feasible_any = any(_feasible(e) for e in t["estimates"].values())
    if missing:
        status = "needs_input"
        # 只认中文说明：模型写 "budget" 这类字段名时用户看不懂，补一条可读的缺口
        unnamed = [m for m in missing if {"budget": "预算", "deadline": "截止"}[m] not in "".join(gaps)]
        if unnamed:
            gaps.append("缺少：" + "、".join({"budget": "预算", "deadline": "截止时间"}[m] for m in unnamed))
    elif saved:
        status = "completed"
    elif t["estimates"] and not feasible_any:
        status = "infeasible"
        best = min(t["estimates"].values(), key=lambda e: (e["budget_gap"] or 0) + (e["time_gap_hours"] or 0) / 100)
        auto = f"最接近的 {best['option_id']}：预算缺口 {best['budget_gap']}，时间缺口 {best['time_gap_hours']:g} 小时"
        if not any(best["option_id"] in g for g in gaps):
            gaps.append(auto)
    else:
        status = "failed_partial"
        gaps += [f"{STEP_NAMES[s['step']]}失败：{s['detail']}" for s in t["steps"] if s["status"] == "failed"
                 and not any(s["step"] in g or STEP_NAMES[s["step"]] in g for g in gaps)]
    if args.get("task_status") != status:
        fixes.append(f"task_status 由 {args.get('task_status')} 校正为 {status}")

    script = t.get("script")
    final = {
        "plan": {"option_id": option, "option_name": est["option_name"] if est else None,
                 "script_id": script["script_id"] if (script and option) else None,
                 "material_ids": t.get("material_ids", []),
                 "plan_id": saved_plan["plan_id"] if saved_plan else None},
        "steps": t["steps"],
        "tool_results": {"estimates": {k: {"total_cost": v["total_cost"], "total_hours": v["total_hours"],
                                           "within_budget": v["within_budget"], "within_deadline": v["within_deadline"]}
                                       for k, v in t["estimates"].items()},
                         "script": script},
        "total_cost": total,
        "budget": payload.get("budget"),
        "saved": saved,
        "deduplicated": bool(saved_plan and saved_plan.get("deduplicated")),
        "task_status": status,
        "gaps": gaps,
        "summary": str(args.get("summary") or ""),
    }
    return final, fixes


def on_incomplete(records: list[ToolRecord], payload: dict, reason: str) -> dict:
    t = truth(records)
    return {"steps": t["steps"], "material_ids": t.get("material_ids", []),
            "estimates": {k: v["total_cost"] for k, v in t["estimates"].items()},
            "saved": bool(t.get("plan")), "gaps": [f"未完成：{reason}"],
            "summary": "达到执行上限，已成功步骤已写入台账，重新提交同一请求可续跑。"}
