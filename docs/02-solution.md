# 02 方案

## 调用流程

```
用户请求 ──► ReActAgent.run
              │
        ┌──► 模型选择动作 + decision_note
        │     ├─ 业务工具 ──► ToolRegistry（参数检查、故障注入、异常转观察）
        │     │                 └─ 成功结果同时写入任务台账（按 request_id）
        │     └─ finish ──► guard：步骤状态/费用/保存结果按工具事实校正
        └── 未 finish 且未超限：下一轮；超限 ──► incomplete + 已成功步骤
```

工具（`src/domain/tools.py`）：

| 工具 | 作用 |
|---|---|
| `get_task_state` | 读取本请求此前已成功的步骤（素材、估算、脚本、方案），用于续跑和防重复 |
| `search_materials` | 按主题/关键词检索素材 |
| `list_production_options` | 列出制作方式（不含费用） |
| `estimate_cost` | 估算某方式总费用、总耗时，并与预算和截止时间比较，给出缺口 |
| `generate_script` | 生成定制脚本 |
| `get_script_template` | 替代方案：通用模板脚本 |
| `save_plan` | 保存方案；服务端复核已估算、不超约束、脚本属于本请求；同一请求幂等 |

## 动态决策点

| 观察 | 可选动作 |
|---|---|
| 输入缺 `budget` / `deadline` | 不调用任何业务工具，`needs_input` |
| `get_task_state` 有已保存方案 | 直接复用，不重做、不重复保存 |
| `get_task_state` 有部分成功步骤 | 跳过这些步骤，只补做缺失部分（续跑） |
| `search_materials.count = 0` | 换关键词再检索，或报告缺口 |
| `estimate_cost.within_budget/within_deadline = false` | 改估其他方式；都不满足则 `infeasible` 并写缺口 |
| `generate_script` 失败 | 重试一次，或改用 `get_script_template` |
| `save_plan` 失败 | 重试或如实报告 `failed_partial` |

对照路径：c01（预算 15）P-A 直接可行；c03（预算 10）P-A 超预算 → 改 P-B；c08（截止 10 小时后）P-A、P-B 超期 → 改 P-C；c05（预算 4）全部超出 → 返回缺口。

## 状态与续跑

- **任务台账**（`runtime/.../ledger.json`）由工具在成功时写入，键为 `request_id`。失败的调用不会写入，所以台账里只有“真正成功”的结果。
- **续跑**：c07 第一次脚本与模板都失败 → `failed_partial`，台账里有素材与估算；第二次提交同一请求，`get_task_state` 返回这些结果，模型只补做脚本和保存。
- **防重复**：`save_plan` 内容相同返回已有方案（`deduplicated=true`），内容变化同一 `plan_id` 升版本。

## 结束护栏

`finish` 后，`guard` 用本轮工具记录和台账重算：每一步的真实状态（done/reused/failed/not_run）、所选方式的估算费用、是否保存、`task_status` 和缺口。模型把失败步骤写成 done、费用与估算不符、选了超预算方式、虚报保存，都会被校正并写入 `guard_corrections`。

## 技术取舍

| 选择 | 理由 | 代价 |
|---|---|---|
| 原生循环，不用框架 | 步数上限、finish 校验、Trace 字段可精确控制，便于解释 | 没有现成的图编排和持久化 |
| 台账由工具写、不由模型写 | 成功与否是工具事实，模型无法把失败写成成功 | 台账只记录成功，失败原因在本轮 Trace 里 |
| 估算工具同时给出约束比较和缺口 | 模型能直接据此重规划，无需自己算 | 约束逻辑放在工具里，换约束要改工具 |
| 脚本与制作方式解耦 | 换方案时脚本结果可保留 | 脚本不针对方式定制 |
| 模板脚本作为显式替代工具 | “选替代方案”是模型可见的动作，而不是隐藏的自动降级 | 模板质量较低，需在步骤说明里标注 |
| OpenAI 兼容接口 + `decision_note` + `finish` 工具 | 同题 1：一份代码切换多家模型；决策依据随动作产生；结果结构化可校验 | 各家 function calling 细节不同 |
