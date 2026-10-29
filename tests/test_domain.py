"""题 2 业务工具与护栏测试。"""
from pathlib import Path

import pytest

from src import domain
from src.core.agent import ToolRecord
from src.core.llm import ScriptedLLM
from src.core.runner import check_case, load_case, run_case
from src.domain.tools import build_tools

CASES = sorted((Path(__file__).resolve().parent.parent / "examples" / "cases").glob("*.json"))
REQ = {"request_id": "T", "topic": "冬季露营", "budget": 10, "deadline": "2026-11-08 18:00"}


def tools(tmp_path, request=REQ, env=None):
    return {t.name: t.fn for t in build_tools(request=request, env=env or {}, store_dir=tmp_path)}


def test_estimates_match_reference_example(tmp_path):
    t = tools(tmp_path)
    a, b = t["estimate_cost"]("P-A"), t["estimate_cost"]("P-B")
    assert (a["total_cost"], a["within_budget"], a["budget_gap"]) == (12, False, 2)
    assert (b["total_cost"], b["within_budget"]) == (8, True)


def test_deadline_is_checked(tmp_path):
    t = tools(tmp_path, {**REQ, "deadline": "2026-11-03 19:00"})
    assert t["estimate_cost"]("P-B")["within_deadline"] is False
    assert t["estimate_cost"]("P-C")["within_deadline"] is True


def test_save_plan_validates_and_is_idempotent(tmp_path):
    t = tools(tmp_path)
    s = t["generate_script"]("冬季露营", ["A01"])
    assert t["save_plan"]("P-A", s["script_id"], ["A01"])["ok"] is False  # 未估算
    t["estimate_cost"]("P-A")
    assert "超出预算" in t["save_plan"]("P-A", s["script_id"], ["A01"])["errors"][0]
    t["estimate_cost"]("P-B")
    first = t["save_plan"]("P-B", s["script_id"], ["A01"])
    again = tools(tmp_path)["save_plan"]("P-B", s["script_id"], ["A01"])  # 新进程再次提交
    assert first["plan_id"] == again["plan_id"] and again["deduplicated"] is True


def test_save_plan_requires_budget_and_deadline(tmp_path):
    t = tools(tmp_path, {"request_id": "T2", "topic": "冬季露营"})
    assert t["save_plan"]("P-C", "x", [])["errors"][0].startswith("缺少预算")


def test_ledger_keeps_successful_steps_for_resume(tmp_path):
    t = tools(tmp_path)
    t["search_materials"]("冬季露营")
    t["estimate_cost"]("P-B")
    state = tools(tmp_path)["get_task_state"]()
    assert state["materials"]["count"] == 3 and "P-B" in state["estimates"] and state["script"] is None


def rec(tool, args, result, ok=True):
    return ToolRecord(1, tool, args, {"ok": ok, **result})


def test_guard_rejects_failed_step_marked_done_and_fake_save():
    records = [rec("search_materials", {}, {"count": 1, "materials": [{"material_id": "A01"}]}),
               rec("estimate_cost", {}, {"option_id": "P-B", "total_cost": 8, "total_hours": 23, "within_budget": True,
                                         "within_deadline": True, "budget_gap": 0, "time_gap_hours": 0, "option_name": "B"}),
               rec("generate_script", {}, {"error": "503"}, ok=False)]
    args = {"plan": {"option_id": "P-B"}, "total_cost": 7, "saved": True, "task_status": "completed", "summary": "",
            "steps": [{"step": "script_writing", "status": "done"}]}
    final, fixes = domain.guard(args, records, REQ)
    assert final["saved"] is False and final["task_status"] == "failed_partial"
    assert final["total_cost"] == 8
    assert next(s for s in final["steps"] if s["step"] == "script_writing")["status"] == "failed"
    assert len(fixes) >= 3


def test_guard_refuses_over_budget_choice():
    records = [rec("estimate_cost", {}, {"option_id": "P-A", "total_cost": 12, "total_hours": 51, "within_budget": False,
                                         "within_deadline": True, "budget_gap": 2, "time_gap_hours": 0, "option_name": "A"})]
    args = {"plan": {"option_id": "P-A"}, "total_cost": 12, "saved": False, "task_status": "completed", "summary": "", "steps": []}
    final, _ = domain.guard(args, records, REQ)
    assert final["plan"]["option_id"] is None and final["task_status"] == "infeasible"
    assert any("缺口 2" in g for g in final["gaps"])


@pytest.mark.parametrize("path", CASES, ids=lambda p: p.stem)
def test_case_acceptance_with_offline_mock(path, tmp_path):
    case = load_case(path)
    outputs = run_case(case, domain, ScriptedLLM(domain.mock_policy), tmp_path)
    checks = check_case(case, domain, [r for _, r in outputs], tmp_path)
    assert checks and all(c["ok"] for c in checks), [c for c in checks if not c["ok"]]


def test_guard_rewrites_field_name_gaps_into_readable_text():
    # 第 2 轮 GLM-4-Flash 在 c02 只写了 ["budget", "deadline"]
    req = {"request_id": "T", "topic": "冬季露营"}
    args = {"plan": {}, "total_cost": 0, "saved": False, "task_status": "needs_input", "summary": "",
            "steps": [], "gaps": ["budget", "deadline"]}
    final, _ = domain.guard(args, [], req)
    assert any("预算" in g and "截止时间" in g for g in final["gaps"])
