# 内容任务规划 Agent（题 2）

帮运营人员在**预算与截止时间内**做出一份内容活动方案：检索素材 → 估算制作方式 → 超预算/超期就换方案 → 生成脚本（失败则重试或改用模板）→ 保存方案。每个成功步骤写入任务台账，同一请求再次执行时复用已成功步骤、只补做失败部分，且不会重复保存。

原生 Python 实现 ReAct 循环（模型选动作 → 执行工具 → 观察 → 再决策或结束），模型走 OpenAI 兼容接口；另有离线 Mock 入口，用于在无模型时验证流程。

## 评审入口

```bash
pip install -r requirements.txt
python -m pytest -q                                   # 内核 + 业务 + 10 个验收用例（离线）
python -m src.cli eval --llm mock                     # 跑全部用例，写出 Trace 与汇总
python -m src.cli run examples/cases/c03_over_budget.json --llm mock --fresh    # 参考实例
```

真实模型（任一 OpenAI 兼容服务；本仓库结果用智谱 GLM-4-Flash 免费版）：

```bash
cp .env.example .env        # 填 LLM_API_KEY、LLM_BASE_URL、LLM_MODEL
python -m src.cli eval --llm openai
```

| 想看什么 | 文件 |
|---|---|
| 验收汇总（Mock） | [examples/results/mock-summary.md](examples/results/mock-summary.md) |
| 参考实例：P-A 估算 12 > 预算 10 → 改选 P-B（8） | [examples/runs/mock/c03_over_budget.md](examples/runs/mock/c03_over_budget.md) |
| 预算充足时直接用 P-A（对照路径） | [examples/runs/mock/c01_normal.md](examples/runs/mock/c01_normal.md) |
| 脚本工具持续失败 → 改用模板 | [examples/runs/mock/c04_tool_failure_fallback.md](examples/runs/mock/c04_tool_failure_fallback.md) |
| 失败后续跑，只补做脚本 | [run1](examples/runs/mock/c07_resume_after_failure_run1.md) / [run2](examples/runs/mock/c07_resume_after_failure_run2.md) |
| 真实模型三轮结果（GLM-4-Flash） | [第 1 轮](examples/results/glm-4-flash-r1-summary.md) / [第 2 轮](examples/results/glm-4-flash-r2-summary.md) / [第 3 轮](examples/results/glm-4-flash-r3-summary.md) + [重跑](examples/results/glm-4-flash-r3-rerun-summary.md)，分析见 [docs/03-evaluation.md](docs/03-evaluation.md) |
| 真实模型：P-A 超预算 → 改选 P-B | [examples/runs/glm-4-flash-r2/c03_over_budget.md](examples/runs/glm-4-flash-r2/c03_over_budget.md) |
| 真实模型：脚本 503 → 改用模板 | [examples/runs/glm-4-flash-r3/c04_tool_failure_fallback.md](examples/runs/glm-4-flash-r3/c04_tool_failure_fallback.md) |
| 真实模型：失败续跑 | [run1](examples/runs/glm-4-flash-r3/c07_resume_after_failure_run1.md) / [run2](examples/runs/glm-4-flash-r3/c07_resume_after_failure_run2.md) |
| 测试输出 | [examples/results/pytest.txt](examples/results/pytest.txt) |

## 环境

- Python 3.10+（开发环境 3.13.4，Windows 11）
- 依赖：`openai`（仅真实模型需要）、`pytest`
- 环境变量见 [.env.example](.env.example)；Mock 模式无需配置

## 验收点与用例

| 验收点 | 用例（`examples/cases/`） |
|---|---|
| 正常完成 | `c01_normal`、`c08_deadline_tight`（预算够但超期，换 P-C） |
| 缺预算或截止时间 | `c02_missing_budget_deadline` |
| 工具失败 | `c04_tool_failure_fallback`（改用模板）、`c09_save_failure`（保存失败） |
| 预算超限 | `c03_over_budget`（参考实例）、`c05_infeasible`（无可行方案，返回缺口） |
| 重复执行 | `c06_repeat_execution` |
| 失败步骤续跑（加分项） | `c07_resume_after_failure` |
| 步数上限 | `c10_step_limit` |

自己出题：复制用例改 `budget` / `deadline` / `preferred_option`，或在 `env.option_overrides` 里改某方案的费用、在 `faults` 里让任一工具失败。

## 目录

```
src/core/      与业务无关的 ReAct 内核：模型接入、循环、工具注册/故障注入、Trace、用例运行
src/domain/    本题业务：工具与任务台账、提示词、结束护栏、离线 Mock 策略、验收检查
src/cli.py     命令行入口
data/          合成素材库、费用与耗时表
examples/      cases/ 输入；runs/ 实际输出与 Trace；results/ 汇总与测试输出
tests/         内核测试、业务测试、全部用例的验收测试
docs/          需求、方案、评估、AI 使用说明、复盘
```

## 已知限制

- `examples/runs/mock/` 是离线 Mock 的记录，只证明流程、工具、护栏打通；真实模型的决策效果以 `--llm openai` 的运行记录为准。
- 费用只按“固定步骤 + 一种制作方式”线性相加，没有组合方案（如两种制作方式混搭）和不确定性区间。
- 台账存为本地 JSON 文件，没有并发保护。
