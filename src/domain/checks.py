"""验收检查：只看最终结果、工具调用事实和任务台账，不绑定执行路径；Mock 与真实模型共用。"""
from __future__ import annotations

import json
from pathlib import Path


def _ledger(store: Path, key: str) -> dict:
    p = store / "ledger.json"
    return (json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}).get(key, {})


def _step(res, name):
    return next((s["status"] for s in res.final.get("steps", []) if s["step"] == name), None)


def _called(res, tool, **match):
    return [r for r in res.records if r.tool == tool and all(r.arguments.get(k) == v for k, v in match.items())]


def _no_false_done(res):
    """失败步骤不能记为成功：凡是 done 的步骤，本轮必须有对应的成功工具记录。"""
    tools = {"material_search": ["search_materials"], "cost_estimate": ["estimate_cost"],
             "script_writing": ["generate_script", "get_script_template"], "plan_save": ["save_plan"]}
    bad = [s["step"] for s in res.final.get("steps", []) if s["status"] == "done"
           and not any(r.ok for t in tools[s["step"]] for r in _called(res, t))]
    return ("没有把失败步骤记为成功", not bad, str(bad))


def c01(results, store):
    r = results[0]
    led = _ledger(store, "PLAN-C01")
    return [
        ("状态 completed 且已保存", r.status == "completed" and r.final["saved"], r.status),
        ("选用偏好方案 P-A，费用 12", r.final["plan"]["option_id"] == "P-A" and r.final["total_cost"] == 12, str(r.final["plan"])),
        ("费用不超预算", r.final["total_cost"] <= 15, ""),
        ("台账中有方案", bool(led.get("plan")), ""),
        _no_false_done(r),
    ]


def c02(results, store):
    r = results[0]
    return [
        ("状态 needs_input", r.status == "needs_input", r.status),
        ("gaps 写明缺预算与截止时间", any("预算" in g for g in r.final["gaps"]) and any("截止" in g for g in r.final["gaps"]), str(r.final["gaps"])),
        ("未保存方案", not r.final["saved"] and not _ledger(store, "PLAN-C02").get("plan"), ""),
        ("未调用生成/保存类工具", not _called(r, "generate_script") and not _called(r, "save_plan"), ""),
    ]


def c03(results, store):
    r = results[0]
    est = r.final["tool_results"]["estimates"]
    return [
        ("先估算了偏好方案 P-A 并发现超预算", est.get("P-A", {}).get("total_cost") == 12 and est["P-A"]["within_budget"] is False, str(est.get("P-A"))),
        ("改选 P-B，费用 8", r.final["plan"]["option_id"] == "P-B" and r.final["total_cost"] == 8, str(r.final["plan"])),
        ("已保存且状态 completed", r.final["saved"] and r.status == "completed", r.status),
        _no_false_done(r),
    ]


def c04(results, store):
    r = results[0]
    st = {s["step"]: s for s in r.final["steps"]}
    return [
        ("脚本生成失败后改用模板", bool(_called(r, "get_script_template")) and (r.final["tool_results"]["script"] or {}).get("source") == "template", ""),
        ("素材与估算结果保留", st["material_search"]["status"] == "done" and st["cost_estimate"]["status"] == "done", ""),
        ("最终方案已保存，费用不超预算", r.final["saved"] and r.final["total_cost"] <= 10, str(r.final["total_cost"])),
        ("步骤说明标注替代方案", "模板" in st["script_writing"]["detail"], st["script_writing"]["detail"]),
        _no_false_done(r),
    ]


def c05(results, store):
    r = results[0]
    return [
        ("状态 infeasible", r.status == "infeasible", r.status),
        ("未保存", not r.final["saved"] and not _ledger(store, "PLAN-C05").get("plan"), ""),
        ("gaps 写明预算缺口", any("缺口" in g for g in r.final["gaps"]), str(r.final["gaps"])),
        ("没有选中任何方案", not r.final["plan"]["option_id"] and r.final["total_cost"] == 0, ""),
    ]


def c06(results, store):
    a, b = results
    led = _ledger(store, "PLAN-C06")
    return [
        ("两次都 completed", a.status == b.status == "completed", f"{a.status}/{b.status}"),
        ("同一方案 ID", a.final["plan"]["plan_id"] == b.final["plan"]["plan_id"], ""),
        ("台账中方案版本为 1", led.get("plan", {}).get("version") == 1, ""),
        ("第二次未重做脚本与检索", not _called(b, "generate_script") and not _called(b, "search_materials"), ""),
    ]


def c07(results, store):
    a, b = results
    led = _ledger(store, "PLAN-C07")
    return [
        ("首次失败但保留成功步骤", a.status == "failed_partial" and _step(a, "material_search") == "done" and _step(a, "cost_estimate") == "done", a.status),
        ("首次脚本步骤记为 failed", _step(a, "script_writing") == "failed", str(_step(a, "script_writing"))),
        ("续跑复用素材与估算", not _called(b, "search_materials") and not _called(b, "estimate_cost"), ""),
        ("续跑只补做脚本并保存", bool(_called(b, "generate_script")) and b.status == "completed" and bool(led.get("plan")), b.status),
    ]


def c08(results, store):
    r = results[0]
    est = r.final["tool_results"]["estimates"]
    return [
        ("偏好方案因超期被放弃", est.get("P-A", {}).get("within_deadline") is False, ""),
        ("选择满足截止时间的 P-C", r.final["plan"]["option_id"] == "P-C" and est["P-C"]["within_deadline"], str(r.final["plan"])),
        ("已保存", r.final["saved"] and r.status == "completed", r.status),
    ]


def c09(results, store):
    r = results[0]
    return [
        ("状态 failed_partial", r.status == "failed_partial", r.status),
        ("saved=false，plan_save 记为 failed", not r.final["saved"] and _step(r, "plan_save") == "failed", ""),
        ("其他步骤结果保留", _step(r, "script_writing") == "done" and _step(r, "cost_estimate") == "done", ""),
        ("gaps 写明保存失败", any("保存" in g for g in r.final["gaps"]), str(r.final["gaps"])),
        _no_false_done(r),
    ]


def c10(results, store):
    r = results[0]
    return [
        ("返回明确未完成状态", r.status == "incomplete" and r.final.get("stop_reason") == "step_limit_reached", r.status),
        ("决策轮数不超过上限", r.steps <= 3, str(r.steps)),
        ("已成功步骤写入结果", any(s["status"] == "done" for s in r.final["steps"]), str(r.final["steps"])),
        ("未保存方案", not r.final["saved"], ""),
    ]


CHECKS = {
    "c01_normal": c01, "c02_missing_budget_deadline": c02, "c03_over_budget": c03,
    "c04_tool_failure_fallback": c04, "c05_infeasible": c05, "c06_repeat_execution": c06,
    "c07_resume_after_failure": c07, "c08_deadline_tight": c08, "c09_save_failure": c09, "c10_step_limit": c10,
}
