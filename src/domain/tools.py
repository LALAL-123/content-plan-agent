"""业务工具（本地函数 + 合成数据）：任务进度、素材检索、制作方式、成本估算、脚本生成、方案保存。

每个成功的步骤都写入按 request_id 建键的任务台账（ledger）。同一请求再次执行时，
get_task_state 返回已成功的步骤，模型可以跳过它们只补做失败的部分（续跑），
save_plan 对同一请求幂等（重复执行不产生第二份方案）。
"""
from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime
from pathlib import Path

from ..core.tools import Tool, ToolError

DATA = Path(__file__).resolve().parents[2] / "data"
FMT = "%Y-%m-%d %H:%M"


def load_json(name: str):
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def request_key(request: dict) -> str:
    if request.get("request_id"):
        return request["request_id"]
    body = json.dumps({k: request.get(k) for k in ("topic", "budget", "deadline")}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(body.encode()).hexdigest()[:12]


class Ledger:
    def __init__(self, store_dir: Path, key: str):
        self.path = Path(store_dir) / "ledger.json"
        self.key = key

    def _all(self) -> dict:
        return json.loads(self.path.read_text(encoding="utf-8")) if self.path.exists() else {}

    def get(self) -> dict:
        return self._all().get(self.key, {"materials": None, "estimates": {}, "script": None, "plan": None})

    def put(self, entry: dict) -> None:
        data = self._all()
        data[self.key] = entry
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)


def estimate(option: dict, table: dict, budget, deadline: str | None) -> dict:
    breakdown = table["fixed_steps"] + [{"item": option["name"], "cost": option["cost"], "hours": option["hours"]}]
    cost = sum(b["cost"] for b in breakdown)
    hours = sum(b["hours"] for b in breakdown)
    hours_left = None
    if deadline:
        hours_left = (datetime.strptime(deadline, FMT) - datetime.strptime(table["now"], FMT)).total_seconds() / 3600
    # 关键结论字段放前面，Trace 摘要截断时也能看到
    return {
        "option_id": option["option_id"], "total_cost": cost, "budget": budget,
        "within_budget": None if budget is None else cost <= budget,
        "total_hours": hours, "hours_until_deadline": hours_left,
        "within_deadline": None if hours_left is None else hours <= hours_left,
        "budget_gap": None if budget is None else max(0, cost - budget),
        "time_gap_hours": None if hours_left is None else max(0, hours - hours_left),
        "option_name": option["name"], "breakdown": breakdown,
    }


def build_tools(request: dict, env: dict, store_dir: Path) -> list[Tool]:
    materials = copy.deepcopy(load_json("materials.json")) + env.get("extra_materials", [])
    materials = [m for m in materials if m["material_id"] not in set(env.get("remove_materials", []))]
    table = load_json("cost_table.json")
    for oid, patch in env.get("option_overrides", {}).items():
        for o in table["production_options"]:
            if o["option_id"] == oid:
                o.update(patch)
    options = {o["option_id"]: o for o in table["production_options"]}
    budget, deadline = request.get("budget"), request.get("deadline")
    ledger = Ledger(store_dir, request_key(request))

    def get_task_state():
        st = ledger.get()
        feasible = any(e["within_budget"] and e["within_deadline"] for e in st["estimates"].values())
        pending = [name for name, done in (("material_search", st["materials"]), ("cost_estimate", feasible),
                                           ("script_writing", st["script"]), ("plan_save", st["plan"])) if not done]
        return {"request_id": ledger.key, "pending_steps": pending, "plan_saved": bool(st["plan"]),
                "materials": st["materials"], "estimates": st["estimates"], "script": st["script"], "plan": st["plan"],
                "hint": "非空字段是此前已成功的步骤结果，可直接复用；pending_steps 是仍需完成的步骤"}

    def search_materials(topic: str, keywords: list | None = None):
        words = [topic] + list(keywords or [])
        hits = [m for m in materials
                if any(w and (w in m["topic"] or w in m["title"] or w in m["tags"]) for w in words)]
        result = {"query": words, "count": len(hits), "materials": hits}
        if hits:
            st = ledger.get()
            st["materials"] = {"material_ids": [m["material_id"] for m in hits], "count": len(hits)}
            ledger.put(st)
        return result

    def list_production_options():
        return {"options": [{"option_id": o["option_id"], "name": o["name"], "desc": o["desc"]} for o in options.values()],
                "note": "费用和耗时请用 estimate_cost 估算"}

    def estimate_cost(option_id: str):
        if option_id not in options:
            raise ValueError(f"未知方案 {option_id}，可选 {sorted(options)}")
        est = estimate(options[option_id], table, budget, deadline)
        st = ledger.get()
        st["estimates"][option_id] = est
        ledger.put(st)
        return est

    def _store_script(script: dict) -> dict:
        st = ledger.get()
        st["script"] = script
        ledger.put(st)
        return script

    def generate_script(topic: str, material_ids: list):
        known = {m["material_id"]: m for m in materials}
        bad = [i for i in material_ids if i not in known]
        if not material_ids or bad:
            raise ValueError(f"素材 ID 无效：{bad or '空'}")
        sid = "S-" + hashlib.sha256(f"{topic}{sorted(material_ids)}".encode()).hexdigest()[:6]
        outline = [f"开场：{known[material_ids[0]]['title']} 引出“{topic}”",
                   *[f"段落：围绕《{known[i]['title']}》展开" for i in material_ids[1:]],
                   "结尾：引导关注与互动"]
        return _store_script({"script_id": sid, "source": "generator", "topic": topic,
                              "material_ids": list(material_ids), "outline": outline})

    def get_script_template(topic: str):
        sid = "TPL-" + hashlib.sha256(topic.encode()).hexdigest()[:6]
        return _store_script({"script_id": sid, "source": "template", "topic": topic, "material_ids": [],
                              "outline": ["开场：痛点提问", "中段：三条要点", "结尾：引导互动"],
                              "note": "通用模板脚本，质量低于定制脚本，需人工润色"})

    def save_plan(option_id: str, script_id: str, material_ids: list):
        if budget is None or not deadline:
            return {"ok": False, "error_type": "validation_failed", "errors": ["缺少预算或截止时间，不能保存方案"]}
        st = ledger.get()
        errors = []
        est = st["estimates"].get(option_id)
        if est is None:
            errors.append(f"方案 {option_id} 尚未估算")
        elif not (est["within_budget"] and est["within_deadline"]):
            errors.append(f"方案 {option_id} 超出预算或截止时间（费用 {est['total_cost']}/{budget}，耗时 {est['total_hours']}h）")
        if not st["script"] or st["script"]["script_id"] != script_id:
            errors.append(f"脚本 {script_id} 不存在或不是本请求生成的")
        if errors:
            return {"ok": False, "error_type": "validation_failed", "errors": errors}
        content = {"option_id": option_id, "script_id": script_id, "material_ids": sorted(material_ids),
                   "total_cost": est["total_cost"], "total_hours": est["total_hours"]}
        digest = hashlib.sha256(json.dumps(content, sort_keys=True).encode()).hexdigest()[:12]
        old = st["plan"]
        if old and old["content_hash"] == digest:
            return {**old, "deduplicated": True, "note": "同一请求的相同方案已保存，未重复创建"}
        plan = {"plan_id": old["plan_id"] if old else "PLAN-" + hashlib.sha256(ledger.key.encode()).hexdigest()[:8],
                "version": old["version"] + 1 if old else 1, "content_hash": digest, **content}
        st["plan"] = plan
        try:
            ledger.put(st)
        except OSError as exc:
            raise ToolError(f"方案存储写入失败：{exc}") from exc
        return {**plan, "deduplicated": False}

    obj = {"type": "object"}
    return [
        Tool("get_task_state", "查看本请求此前已成功的步骤（素材、估算、脚本、已保存方案）。开始时先调用，用于续跑与防重复执行。",
             {**obj, "properties": {}}, get_task_state),
        Tool("search_materials", "按主题和关键词检索合成素材库。count=0 表示没有可用素材。",
             {**obj, "properties": {"topic": {"type": "string"}, "keywords": {"type": "array", "items": {"type": "string"}}},
              "required": ["topic"]}, search_materials),
        Tool("list_production_options", "列出可选的制作方式（不含费用）。", {**obj, "properties": {}}, list_production_options),
        Tool("estimate_cost", "按费用与耗时表估算某个制作方式的总费用、总耗时，并与本请求的预算和截止时间比较。",
             {**obj, "properties": {"option_id": {"type": "string"}}, "required": ["option_id"]}, estimate_cost),
        Tool("generate_script", "基于素材生成定制脚本大纲。", {**obj, "properties": {
            "topic": {"type": "string"}, "material_ids": {"type": "array", "items": {"type": "string"}}},
            "required": ["topic", "material_ids"]}, generate_script),
        Tool("get_script_template", "脚本生成不可用时的替代：取通用模板脚本（质量较低，需人工润色）。",
             {**obj, "properties": {"topic": {"type": "string"}}, "required": ["topic"]}, get_script_template),
        Tool("save_plan", "保存活动方案。服务端复核：已估算且不超预算/截止时间、脚本属于本请求。同一请求重复保存相同内容不会新建。",
             {**obj, "properties": {"option_id": {"type": "string"}, "script_id": {"type": "string"},
                                    "material_ids": {"type": "array", "items": {"type": "string"}}},
              "required": ["option_id", "script_id", "material_ids"]}, save_plan),
    ]
