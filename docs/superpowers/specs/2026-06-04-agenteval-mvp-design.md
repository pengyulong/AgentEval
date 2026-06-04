# AgentEval MVP 设计文档

## 背景

AgentEval MVP 面向重度 Agent 编程个人用户，提供本地 CLI 和 JSON 报告，用于诊断 Claude Code 与 OpenClaw 会话的效果、过程质量和使用问题。

当前仓库基本为空项目，只有 `prd.md` 和项目指令文件，因此 MVP 需要从 Python 项目骨架开始实现。

## 目标

MVP 优先交付一个可运行的本地 CLI，并尽量适配真实数据：

- Claude Code：优先解析本机真实 session 数据，也支持直接传入 session 文件路径。
- OpenClaw：当前机器没有安装 OpenClaw，因此先支持从其他机器拷贝或导出的 session 文件与目录。
- 输出：支持人类可读 CLI 报告和稳定 JSON 报告。
- 评估：过程诊断必须可用；语义效果评估在 DeepSeek 环境变量可用时启用，不可用时降级为待评估状态。
- 隐私：默认不导出完整原始日志，只导出 preview、摘要、指标和原始引用。

## 非目标

MVP 不实现：

- SaaS 平台。
- Web dashboard。
- 团队/组织空间。
- OpenClaw API 直连。
- 完整 benchmark 任务集。
- LangChain、Cursor、Windsurf 等更多适配器。
- token 估算。
- 企业权限、审计、团队对比或成本 ROI。

## 推荐方案

采用 Python CLI + 分层模块架构：

```text
agenteval/
  cli/             # 命令行入口：diagnose session/project/user
  adapters/        # 原始数据适配：claude_code / openclaw
  trace/           # 内部统一 SessionTrace schema
  diagnostics/     # 过程诊断指标与聚合
  judge/           # 语义效果评估，DeepSeek 可选接入
  reports/         # CLI 文本报告与 JSON 输出
  privacy/         # preview、截断、include-raw 控制
```

关键原则：

1. 适配器只负责读取原始数据并归一化为内部 Trace。
2. 诊断、judge 和报告层只依赖内部 Trace，不依赖具体 Agent 日志格式。
3. Judge 是可选能力；未配置模型时仍输出过程诊断。
4. 默认隐私优先，不复制或导出完整 raw 内容。
5. Project/User 聚合默认全量做过程诊断，只对高风险或代表性 session 做语义评估。

## CLI 设计

实现三个核心入口：

```bash
agenteval diagnose session <session-id-or-path>
agenteval diagnose project [--path PATH]
agenteval diagnose user
```

通用参数：

```bash
--source claude-code|openclaw|auto
--json
--output report.json
--since 7d
--limit 100
--judge-model MODEL
--include-raw
```

行为：

- `diagnose session` 支持传入单个 session 文件路径，或由适配器解析 session id。
- `diagnose project` 默认诊断当前目录关联 sessions。
- `diagnose user` 诊断当前用户下可发现 sessions。
- `--json` 输出稳定 JSON；配合 `--output` 写入文件。
- 未设置 `--json` 时输出人类可读文本报告。

## Adapter 设计

定义统一接口：

```text
BaseAdapter
  discover_sessions(scope, path, since, limit)
  load_session(session_ref)
  to_trace(raw_session)
```

### ClaudeCodeAdapter

职责：

- 自动查找 Claude Code 本地 session 目录。
- 支持按项目路径过滤。
- 支持直接传 session 文件路径。
- 从 JSONL 中尽量提取用户消息、assistant 最终输出、工具调用、模型、时间戳、错误信息。
- 拿不到的字段标记为 `unavailable`。

### OpenClawAdapter

职责：

- 支持读取 OpenClaw session store：`~/.openclaw/agents/<agentId>/sessions/sessions.json`。
- 支持读取 OpenClaw transcript：`~/.openclaw/agents/<agentId>/sessions/<sessionId>.jsonl`。
- 支持读取从其他机器拷贝来的 sessions 目录。
- 支持读取 `sessions_history(includeTools=true)` 导出的 JSON 文件。
- 不要求本机安装 OpenClaw。

公开文档依据：OpenClaw session 索引位于 `~/.openclaw/agents/<agentId>/sessions/sessions.json`，transcript 位于同目录 `<sessionId>.jsonl`；也可通过 `openclaw sessions --json` 和 `sessions_history` 获取会话数据。

后续可以新增 `OpenClawApiAdapter`，但不进入 MVP。

## Trace Schema

MVP 使用 Pydantic v2 定义内部 schema，原因：

- JSON 输出稳定。
- 适合后续 dashboard/API 复用。
- 对外部日志解析中的缺失和脏数据有清晰校验边界。

核心对象：

```text
SessionTrace
TaskIntent
ModelInfo
TokenUsage
HumanIntervention
MessageStep
ToolCallStep
SystemEventStep
EvaluationResult
```

字段遵循 PRD 中的最小 Trace Schema。无法获得的 token、cost、模型版本等字段使用 `unavailable`，不做默认估算。

## 数据流

整体流程：

```text
CLI args
  ↓
SessionDiscovery
  ↓
Adapter.load_session()
  ↓
Adapter.to_trace()
  ↓
DiagnosticsEngine
  ↓
Optional SemanticJudge
  ↓
ReportBuilder
  ↓
TextReporter / JsonReporter
```

### session 诊断

```text
session id/path
  ↓
根据 --source 或 auto 选择 adapter
  ↓
解析为单个 SessionTrace
  ↓
生成过程指标
  ↓
如果 judge 可用，执行语义评估
  ↓
输出文本或 JSON
```

### project 诊断

```text
--path，默认 cwd
  ↓
adapter.discover_sessions(scope=project, path=...)
  ↓
按 project_path 过滤 sessions
  ↓
受 --since / --limit 控制
  ↓
逐个解析 SessionTrace
  ↓
全量做过程诊断
  ↓
挑选高风险 sessions 做语义评估
  ↓
聚合为项目报告
```

高风险 session 规则：

- status 为 `failed`、`interrupted` 或 `unknown`。
- tool_error_count > 0。
- human_intervention_count >= 2。
- duration 明显长。
- final_output 缺失。
- data_completeness_score 偏低。

### user 诊断

```text
agenteval diagnose user
  ↓
adapter.discover_sessions(scope=user)
  ↓
读取当前用户所有可发现 sessions
  ↓
按 --since / --limit 控制
  ↓
聚合项目、模型、状态、工具失败、人工介入等维度
  ↓
对代表性或高风险 session 做可选 judge
  ↓
输出用户级报告
```

### OpenClaw 迁移输入

当前机器未安装 OpenClaw 时，用户可以从其他机器拷贝 sessions 目录：

```bash
scp -r other-machine:~/.openclaw/agents/<agentId>/sessions ./openclaw-sessions
agenteval diagnose project --source openclaw --path ./openclaw-sessions
```

或诊断单个 transcript：

```bash
agenteval diagnose session ./openclaw-sessions/<sessionId>.jsonl --source openclaw
```

## Diagnostics 设计

过程诊断 P0 指标：

- session_count
- completion_status
- duration
- model_name
- tool_call_count
- tool_success_rate
- tool_error_count
- human_intervention_count
- intervention_by_type
- data_completeness_score
- top_findings
- coaching_suggestions

这些指标既服务于人类诊断，也作为语义评估 evidence 输入。

## Judge 设计

语义评估包含三项：

- Requirement Alignment
- Final Output Quality
- Execution Relevance

每项输出：

```text
score
confidence
evidence[]
issues / strengths
```

Judge 输入只使用：

- 用户原始需求。
- 最终输出。
- 工具调用摘要。
- 错误摘要。
- 测试或验证相关 evidence。
- 人工介入摘要。

默认不发送完整原始日志。DeepSeek 环境变量可用时启用 judge：

- `DEEPSEEK_API_KEY`
- `DEEPSEEK_MODEL_NAME`
- `DEEPSEEK_FAST_MODEL_NAME`

未配置时输出 `judge_status: unavailable`，不影响过程诊断。

## Reporter 设计

### TextReporter

文本报告分为七段：

1. Summary
2. Effectiveness Review
3. Key Findings
4. Coaching Suggestions
5. Metrics
6. Engineering Audit
7. Data Quality

### JsonReporter

JSON 顶层保持稳定：

```json
{
  "scope": "project",
  "source": "claude_code",
  "summary": {},
  "effectiveness_review": {},
  "key_findings": [],
  "coaching_suggestions": [],
  "metrics": {},
  "engineering_audit": {},
  "data_quality": {}
}
```

## 错误处理

1. 文件不存在或 source 不匹配：CLI 输出明确错误，JSON 模式输出结构化 error。
2. 字段缺失：不终止诊断，字段标记为 `unavailable`，并记录到 `data_quality.unavailable[]`。
3. 日志格式无法识别：跳过该 session，在报告中记录 skipped session 数和原因。
4. Judge 不可用：保留过程诊断，记录 judge 状态或错误。
5. `--include-raw`：仅显式传入时导出 raw，并在 CLI 层提示隐私风险。

## 测试设计

测试优先覆盖行为，不测内部实现细节。

### 单元测试

- `test_claude_code_adapter.py`
  - 从 fixture JSONL 解析用户需求、最终输出、工具调用。
  - 缺失 token 时输出 unavailable。
  - 工具失败时记录 error。

- `test_openclaw_adapter.py`
  - 解析 `sessions.json`。
  - 解析 OpenClaw transcript JSONL。
  - 解析 `sessions_history` 导出 JSON。
  - 缺失字段不崩溃。

- `test_diagnostics.py`
  - 计算 tool_success_rate。
  - 计算 human_intervention_count。
  - 生成 data_completeness_score。
  - 识别高风险 session。

- `test_reporters.py`
  - JSON 输出包含稳定顶层字段。
  - 文本报告包含 Summary / Metrics / Data Quality 等段落。

- `test_cli.py`
  - `diagnose session fixture --json` 正常输出 JSON。
  - `diagnose project --path fixture-dir` 聚合多个 session。
  - judge 未配置时命令仍成功。

### Fixture

```text
tests/fixtures/
  claude_code/
    sample-session.jsonl
  openclaw/
    sessions.json
    sample-session.jsonl
    sessions-history-export.json
```

### 人工验证命令

```bash
conda activate base
python -m pytest
python -m agenteval diagnose session tests/fixtures/claude_code/sample-session.jsonl --source claude-code --json
python -m agenteval diagnose project --path tests/fixtures/openclaw --source openclaw
```

## 扩展路径

后续扩展不应破坏 MVP 核心分层：

- 新 Agent：新增 adapter，输出 `SessionTrace`。
- Dashboard：复用 `JsonReporter` 输出结构。
- CI：新增机器可读 exit code 和阈值配置。
- 企业版：在 report 聚合层增加团队、项目、模型、用户维度。
- 高级评估：新增 judge rubric，不改变 adapter 和 diagnostics 基础接口。

## 验收标准

MVP 设计完成后的实现应满足：

- CLI 可运行 `diagnose session/project/user`。
- Claude Code fixture 可解析并输出 JSON/文本报告。
- OpenClaw 导出目录或文件 fixture 可解析并输出 JSON/文本报告。
- 未配置 DeepSeek 时过程诊断仍可成功。
- JSON 顶层结构稳定。
- 默认不导出完整 raw 内容。
- pytest 全部通过。
