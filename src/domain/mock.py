"""离线 Mock 策略：确定性规则，读取工具结果后选择下一步。

只用于无模型时验证循环、工具、护栏与 Trace；它是条件分支，不代表真实模型的决策能力。
"""
from __future__ import annotations

from ..core.llm import Observation


def _all(obs, *tools):
    return [o for o in obs if o.tool in tools]


def _ok(o):
    return o is not None and o.result.get("ok")


def _finish(note, status, plan=None, cost=0, saved=False, gaps=(), summary="", steps=()):
    return "finish", note, {"plan": plan or {"option_id": "", "script_id": "", "material_ids": []},
                            "steps": list(steps), "total_cost": cost, "saved": saved,
                            "task_status": status, "gaps": list(gaps), "summary": summary}


def mock_policy(payload: dict, obs: list[Observation]):
    missing = [n for k, n in (("budget", "预算"), ("deadline", "截止时间")) if payload.get(k) in (None, "")]
    if missing:
        return _finish("输入缺少硬约束，不能估算是否可行", "needs_input", gaps=[f"缺少{'、'.join(missing)}，请补充后重新提交"],
                       summary=f"缺少{'、'.join(missing)}，未开始规划。")

    states = _all(obs, "get_task_state")
    if not states:
        return "get_task_state", "先查看此请求是否已有进度，避免重复执行", {}
    state = states[-1].result if _ok(states[-1]) else {}
    topic = payload["topic"]

    if state.get("plan"):
        p = state["plan"]
        return _finish("此前已保存方案，直接复用，不重复执行", "completed",
                       {"option_id": p["option_id"], "script_id": p["script_id"], "material_ids": p["material_ids"]},
                       p["total_cost"], True, summary=f"方案 {p['plan_id']} 已存在（重复执行未新建），费用 {p['total_cost']}。")

    # 1. 素材
    material_ids = (state.get("materials") or {}).get("material_ids")
    if not material_ids:
        searches = _all(obs, "search_materials")
        hit = next((s for s in reversed(searches) if _ok(s) and s.result["count"] > 0), None)
        if hit:
            material_ids = [m["material_id"] for m in hit.result["materials"]]
        elif not searches:
            return "search_materials", f"检索主题“{topic}”的素材", {"topic": topic}
        elif len(searches) < 2:
            kw = payload.get("keywords") or [topic[-2:]]
            why = searches[-1].result.get("error") or "没有结果"
            return "search_materials", f"首次检索{why}，换关键词再试一次", {"topic": topic, "keywords": kw}
        else:
            return _finish("两次检索均无可用素材", "failed_partial", gaps=["没有可用素材，请补充素材或调整主题"],
                           summary="素材检索无结果，未生成方案。")

    # 2. 制作方式与估算：优先用户偏好，超限则换下一个
    estimates = dict(state.get("estimates") or {})
    estimates.update({o.result["option_id"]: o.result for o in _all(obs, "estimate_cost") if _ok(o)})
    lists = _all(obs, "list_production_options")
    if not lists:
        return "list_production_options", "查看可选制作方式，准备估算", {}
    options = [o["option_id"] for o in lists[-1].result.get("options", [])]
    pref = payload.get("preferred_option")
    order = ([pref] if pref in options else []) + [o for o in options if o != pref]
    chosen = None
    for oid in order:
        est = estimates.get(oid)
        if est is None:
            fails = [o for o in _all(obs, "estimate_cost") if o.args.get("option_id") == oid and not _ok(o)]
            if len(fails) >= 2:
                continue
            tried = [k for k in estimates]
            note = f"估算 {oid}" + (f"（已估 {tried} 均不满足约束）" if tried else "（用户偏好方案）" if oid == pref else "")
            return "estimate_cost", note, {"option_id": oid}
        if est["within_budget"] and est["within_deadline"]:
            chosen = est
            break
    if chosen is None:
        best = min(estimates.values(), key=lambda e: e["total_cost"]) if estimates else None
        gap = (f"最便宜的 {best['option_id']} 需 {best['total_cost']}，预算 {payload['budget']}，缺口 {best['budget_gap']}；"
               f"时间缺口 {best['time_gap_hours']:g} 小时") if best else "估算服务不可用"
        return _finish("所有制作方式都超出预算或截止时间", "infeasible", gaps=[gap], summary="没有满足约束的方案：" + gap)

    # 3. 脚本：失败重试一次，再失败改用模板
    script = state.get("script")
    if not script:
        gens, tpls = _all(obs, "generate_script"), _all(obs, "get_script_template")
        ok = next((o for o in reversed(gens + tpls) if _ok(o)), None)
        if ok:
            script = ok.result
        elif len(gens) < 2:
            note = "按所选方案生成脚本" if not gens else f"脚本生成失败（{gens[-1].result.get('error')}），重试一次"
            return "generate_script", note, {"topic": topic, "material_ids": material_ids}
        elif len(tpls) < 1:
            return "get_script_template", "定制脚本两次失败，改用模板脚本作为替代", {"topic": topic}
        else:
            return _finish("脚本生成与模板都不可用，保留已完成的素材与估算", "failed_partial",
                           {"option_id": chosen["option_id"], "script_id": "", "material_ids": material_ids},
                           chosen["total_cost"], False, gaps=["脚本步骤失败，可在服务恢复后重新提交同一请求续跑"],
                           summary="素材与估算已完成并保存进度，脚本失败，方案未保存。")

    # 4. 保存
    saves = _all(obs, "save_plan")
    ok = next((o for o in reversed(saves) if _ok(o)), None)
    plan = {"option_id": chosen["option_id"], "script_id": script["script_id"], "material_ids": material_ids}
    if ok is None:
        if len(saves) < 2 and (not saves or saves[-1].result.get("error_type") == "tool_failure"):
            note = f"{chosen['option_id']} 费用 {chosen['total_cost']} ≤ 预算 {payload['budget']}，保存方案"
            if saves:
                note = f"保存失败（{saves[-1].result.get('error')}），重试一次"
            return "save_plan", note, plan
        err = saves[-1].result.get("error") or "; ".join(saves[-1].result.get("errors", []))
        return _finish("保存失败，如实报告", "failed_partial", plan, chosen["total_cost"], False,
                       gaps=[f"方案保存失败：{err}"], summary="方案已生成但未保存：" + err)
    dedup = "（与已保存方案相同，未重复创建）" if ok.result.get("deduplicated") else ""
    return _finish("方案已保存，提交结果", "completed", plan, chosen["total_cost"], True,
                   summary=f"选用 {chosen['option_name']}，费用 {chosen['total_cost']}/{payload['budget']}，"
                           f"耗时 {chosen['total_hours']}h，方案 {ok.result['plan_id']} 已保存{dedup}。")
