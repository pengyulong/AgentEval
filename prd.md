# AgentEval — Agent 效果评估与使用诊断产品设计文档

**版本**: v0.3 草案  
**状态**: 产品方向收敛中，待继续讨论适配与实现细节  
**作者**: pengyulong  
**最后更新**: 2026-06-02

---

## 1. 产品一句话定位

AgentEval 是面向重度 Agent 编程用户的本地 Agent 效果评估与使用诊断工具。

它从 Claude Code、OpenClaw 等 Agent 的会话数据出发，评估 Agent 是否理解并满足用户需求、最终输出是否可用、执行过程是否跑偏，并结合工具调用、人工介入、模型与 token 等过程证据，给出可追踪的诊断报告和改进建议。

---

## 2. 背景与问题

AI Agent 已经开始承担真实研发任务，但用户仍缺少一套系统化方法来回答这些问题：

1. **Agent 到底有没有满足我的需求？**  
   任务看似完成了，但是否遗漏了约束、做了无关工作、输出是否真正可用，并不容易判断。

2. **Agent 为什么慢、贵或失败？**  
   一次任务可能包含多轮推理、工具调用、文件读取、测试运行和用户纠偏，失败原因分散在会话上下文中。

3. **我如何更好地使用 Agent？**  
   用户可能没有意识到自己经常给出不完整需求、频繁中断、重复审批，或没有让 Agent 先规划和验证。

4. **不同模型或不同 Agent 的效果如何对比？**  
   如果缺少模型、token、人工介入、最终输出质量等结构化记录，后续无法做模型选择和优化。

5. **团队和企业如何持续评估 Agent？**  
   中小企业级 Agent 团队需要持续评估、回归检测、成本分析和团队级报告，但这些能力应建立在个人本地评估能力之上。

---

## 3. 核心产品判断

### 3.1 AgentEval 不只是日志分析器

如果 AgentEval 只统计工具调用、耗时和错误，它的价值会偏弱。真正有价值的是把过程证据用于回答：

- Agent 是否偏离用户需求；
- 最终输出是否是用户需要的；
- 执行路径是否与任务相关；
- 是否存在减少工具调用、token 和耗时的空间；
- 用户应该如何调整自己的 Agent 使用方式。

因此 AgentEval v0 必须包含语义效果评估，而不是只做过程诊断。

### 3.2 过程诊断是证据层，效果评估是价值层

AgentEval 的评估分两层：

1. **过程证据层**  
   记录工具调用、错误、耗时、模型、token、人工介入、测试结果、重复行为等事实。

2. **语义效果层**  
   基于用户原始需求、最终输出和过程证据，判断需求贴合度、最终输出质量和执行相关性。

语义判断必须带证据和置信度，不能只给主观分数。

### 3.3 先服务个人，再走向企业

产品路径：

1. **MVP / 开源版**：面向个人重度 Agent 编程用户，提供本地 CLI + JSON 评估报告。
2. **增强版 / 商业版**：面向中小企业级 Agent 团队，提供高级效果评估、团队报告、回归评估、模型对比和 dashboard。

---

## 4. 目标用户

### 4.1 MVP 核心用户

MVP 首先服务 **Agent 重度个人开发者**：

- 高频使用 Claude Code、OpenClaw 或类似 coding agent；
- 希望复盘单次任务为什么成功、失败、慢或贵；
- 希望知道自己在某个项目中如何更好地使用 Agent；
- 可以接受 CLI 工具和本地 JSON 报告；
- 重视隐私，不希望默认上传完整会话内容。

### 4.2 后续用户

后续扩展到：

- 中小企业内部 Agent 团队；
- AI 产品原型开发者；
- Agent 框架或平台开发者；
- 需要持续评估、回归测试、模型对比和团队管理的企业用户。

---

## 5. MVP 范围

### 5.1 MVP 做什么

MVP 聚焦 5 件事：

1. **Claude Code + OpenClaw 双适配**  
   支持解析 Claude Code 本地 session 和 OpenClaw session/API 数据。

2. **三级诊断粒度**
   - 单 session 诊断；
   - 当前项目全部 sessions 诊断；
   - 当前用户全部 sessions 诊断。

3. **最小统一 Trace**  
   将不同 Agent 的原始会话归一到 AgentEval 内部数据结构。

4. **语义效果评估 P0**
   - Requirement Alignment；
   - Final Output Quality；
   - Execution Relevance；
   - Evidence；
   - Judge Confidence。

5. **CLI + JSON 输出**
   - CLI 文本报告用于人类阅读；
   - JSON 输出用于后续 dashboard、CI 和企业能力扩展。

### 5.2 MVP 不做什么

MVP 暂不做：

- SaaS 平台；
- 团队/组织空间；
- Web dashboard；
- 完整 benchmark 任务集；
- 公开 AgentTrace Protocol 标准；
- LangChain、Cursor、Windsurf 等更多适配；
- token 估算；
- 企业级权限、审计和团队对比。

---

## 6. 免费开源与商业边界

### 6.1 免费开源 MVP

免费开源版解决个人用户的核心问题：

> 看清一次或一组 Agent 任务的质量，并获得可执行改进建议。

开源版包含：

- Claude Code / OpenClaw 基础适配；
- session / project / user 三级诊断；
- 过程证据层；
- 语义效果评估 P0；
- CLI 报告；
- JSON 导出。

### 6.2 后续商业能力

商业版面向中小企业和企业级 Agent 团队，可包括：

- 高级效果评估；
- 效率优化空间评估；
- 用户满意风险评估；
- Project/User 级语义抽样；
- 任务类型专属 rubric；
- Agent 版本回归评估；
- 团队级 dashboard；
- 多用户、多项目、多模型对比；
- 成本 ROI 分析；
- 人工反馈与标注校准；
- 私有化部署和企业数据治理。

---

## 7. 评估体系

AgentEval 的评估体系分为语义效果评估和过程诊断评估。

### 7.1 语义效果评估 P0

MVP 先实现 3 个核心语义指标和 2 个可信度字段。

#### 7.1.1 Requirement Alignment

**目标**：评估 Agent 是否满足用户原始需求。

关注点：

- 是否满足明确需求；
- 是否遗漏关键要求；
- 是否违反用户约束；
- 是否做了用户不需要且无助于目标的额外工作；
- 最终输出是否回应了用户真正关心的问题。

输出：

```text
score: 0-10
missed_requirements[]
violated_constraints[]
unsupported_extra_work[]
evidence[]
confidence
```

#### 7.1.2 Final Output Quality

**目标**：评估最终回答、代码、文档或结果是否可用、完整、可信。

对 coding 任务关注：

- 是否解决问题；
- 是否通过测试或构建；
- 是否遵守项目约束；
- 是否引入无关改动；
- 是否说明改动和验证结果。

对分析/设计任务关注：

- 结论是否清晰；
- 证据是否充分；
- 是否回答问题；
- 是否区分事实和推测；
- 是否给出可执行下一步。

输出：

```text
score: 0-10
strengths[]
quality_issues[]
missing_evidence[]
confidence
```

#### 7.1.3 Execution Relevance

**目标**：评估 Agent 的执行过程是否围绕任务目标展开。

关注点：

- 工具调用是否与任务相关；
- 文件读取是否相关；
- 搜索是否相关；
- 是否进入无关探索；
- 是否在同一错误上循环；
- 是否做了不必要的重构或扩展。

输出：

```text
score: 0-10
off_track_actions[]
unnecessary_actions[]
repeated_actions[]
evidence[]
confidence
```

#### 7.1.4 Evidence

每个语义判断都必须带证据。

证据可以来自：

- 用户原始需求；
- 最终输出；
- 工具调用步骤；
- 测试结果；
- 人工介入事件；
- 错误日志；
- 文件修改摘要。

错误示例：

```text
Final Output Quality: 6/10
回答质量一般。
```

正确示例：

```text
Final Output Quality: 6/10
证据：最终回答说明了修改内容，但没有说明是否运行测试；用户原始需求要求“修复并验证”，验证部分缺失。
```

#### 7.1.5 Judge Confidence

所有语义评估都需要标注：

- judge model；
- confidence；
- 是否基于完整 trace；
- 是否缺失关键数据。

### 7.2 语义总分

MVP 可以提供 `Effectiveness Score`，但不应过度突出。

建议计算方式：

```text
Effectiveness Score =
  Requirement Alignment 40%
+ Final Output Quality  40%
+ Execution Relevance   20%
```

效率优化空间和用户满意风险暂不进入 MVP P0，可作为后续商业增强。

### 7.3 过程诊断指标

过程诊断为语义评估提供证据，也帮助用户定位问题。

P0 指标：

- session_count；
- completion_status；
- duration；
- model_name；
- tool_call_count；
- tool_success_rate；
- tool_error_count；
- human_intervention_count；
- intervention_by_type；
- data_completeness_score；
- top_findings；
- coaching_suggestions。

P1 指标：

- repeated_file_reads；
- repeated_commands；
- redundant_step_rate；
- completion_rate_by_model；
- intervention_rate_by_model；
- project_level_trends；
- user_level_usage_profile。

---

## 8. 数据模型

### 8.1 核心对象

AgentEval v0 使用内部最小 Trace Schema，不急于发布公开协议。

核心对象：

```text
SessionTrace       # 单次 Agent 会话
ProjectTraceSet    # 同一项目目录下的 sessions 集合
UserTraceSet       # 当前用户下所有 sessions 集合
```

### 8.2 SessionTrace

```text
SessionTrace:
  session_id
  source                # claude_code / openclaw
  project_path
  user_id               # 本地可匿名化
  started_at
  ended_at
  duration_ms

  model
  task_intent
  final_output
  status                # completed / failed / interrupted / unknown

  steps[]
  human_interventions[]
  token_usage
  cost
  effectiveness_evaluation
  summary
  data_completeness_score
  raw_reference
```

### 8.3 TaskIntent

```text
TaskIntent:
  original_request
  explicit_requirements[]
  implicit_expectations[]
  constraints[]
  expected_outputs[]
  success_criteria[]
  confidence
```

### 8.4 ModelInfo

需要记录实际使用模型，便于后续模型对比。

```text
ModelInfo:
  provider              # anthropic / openai / deepseek / local / unknown
  model_name
  model_version
  model_role            # primary / fast / judge / fallback
  source                # measured / configured / inferred / unavailable
  confidence
```

如果一个 session 中出现多个模型，应支持 step 级模型记录。

### 8.5 TokenUsage

MVP 只展示精确可获取的 token 数据，不默认估算。

```text
TokenUsage:
  input_tokens
  output_tokens
  reasoning_tokens
  cache_creation_input_tokens
  cache_read_input_tokens
  total_tokens
  source                # measured / unavailable
  confidence
```

如果日志或 API 拿不到精确 token，则显示 `unavailable`。

### 8.6 HumanIntervention

人工介入是 Agent 自主性、需求理解和用户体验的重要信号。

```text
HumanIntervention:
  intervention_id
  timestamp
  type
  trigger_step_id
  resolved_step_id
  description
  severity
```

介入类型：

```text
permission_approval       # 权限审批
requirement_clarification # 需求确认
user_correction           # 用户纠偏
user_interrupt            # 用户中断
manual_instruction        # 用户追加指令
tool_permission_denied    # 工具权限被拒绝
environment_help          # 用户手动处理环境问题
```

### 8.7 Step

MVP 先分 3 类 step。

```text
MessageStep:
  step_id
  timestamp
  role
  content_preview
  content_length
  token_usage
  model

ToolCallStep:
  step_id
  timestamp
  tool_name
  tool_category
  input_preview
  output_preview
  status
  error_type
  duration_ms
  token_usage
  model

SystemEventStep:
  step_id
  timestamp
  event_type
  detail_preview
```

### 8.8 数据隐私策略

MVP 默认不复制完整原始日志。

默认保存：

- 原始日志路径；
- session id；
- step 摘要；
- preview；
- 聚合指标；
- 评估结果。

默认 JSON 导出应脱敏：

- 工具输入/输出只保留 preview；
- 长文本截断；
- 敏感路径和内容后续可配置脱敏。

只有用户显式指定 `--include-raw` 时才导出完整 trace，并需要在 CLI 中提示风险。

---

## 9. 报告结构

MVP 输出 CLI 文本报告和 JSON 报告。

### 9.1 CLI 报告结构

CLI 报告建议分为 7 段：

1. Summary；
2. Effectiveness Review；
3. Key Findings；
4. Coaching Suggestions；
5. Metrics；
6. Engineering Audit；
7. Data Quality。

### 9.2 示例结构

```text
AgentEval Project Report

Scope: project
Source: claude_code
Project: /workspace/foo
Sessions: 128
Time Range: 2026-05-01 ~ 2026-06-02
Health: Good 82/100
Data Completeness: 78/100

Effectiveness Review
- Effectiveness Score: 76/100
- Requirement Alignment: 8/10
- Final Output Quality: 7/10
- Execution Relevance: 7/10
- Judge Model: deepseek-v4-pro
- Confidence: 0.82

Key Findings
1. 37% 的 session 出现用户追加需求，说明初始需求经常不够完整。
2. Bash 工具失败率偏高，主要集中在测试命令。
3. 部分任务最终回答缺少验证结果。

Coaching Suggestions
1. 发起 coding 任务时，建议明确目标文件、期望行为和验收命令。
2. 对复杂任务，建议先要求 Agent 输出计划，再允许它修改代码。
3. 如果信任当前项目，可调整权限策略减少重复 Bash 审批。

Metrics
- Completion Rate: 74%
- Avg Duration: 12m 31s
- Tool Success Rate: 88%
- Avg Human Interventions / Session: 1.7
- Model: claude-sonnet-4-6
- Token Usage: unavailable

Engineering Audit
- Bash: 18 failures
- Edit: 5 failures
- High-friction sessions: 7

Data Quality
Available:
- tool calls
- tool status
- timestamps
- model name
- human interventions

Unavailable:
- exact input tokens
- exact output tokens
- reasoning tokens
- cost
```

### 9.3 JSON 输出

CLI 统一支持 JSON 输出：

```bash
agenteval diagnose project --json
```

JSON 顶层结构：

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

---

## 10. CLI 产品形态

### 10.1 三个核心入口

```bash
agenteval diagnose session <session-id-or-path>
agenteval diagnose project [--path PATH]
agenteval diagnose user
```

### 10.2 通用参数

```bash
--source claude-code|openclaw|auto
--json
--since 7d
--limit 100
--judge-model MODEL
--output report.json
--include-raw
```

### 10.3 默认行为

- `diagnose session` 默认进行语义效果评估；
- `diagnose project` 默认全量做过程诊断，并对高风险或抽样 session 做语义评估；
- `diagnose user` 默认聚合用户级使用画像，并对代表性 session 做语义评估；
- 默认不估算 token；
- 默认不导出完整原始日志；
- 默认输出人类可读 CLI 报告；
- judge 模型需要用户配置 API key 或本地模型，未配置时仍可输出过程诊断和待评估项。

---

## 11. 适配策略

### 11.1 Claude Code 适配

Claude Code 是 MVP 的重点适配对象。

需要调研和确认：

- session 日志实际路径和命名规则；
- 单个 session 的 JSON/日志结构；
- 工具调用记录；
- 工具输入输出；
- 工具状态和错误；
- 时间戳；
- 模型名称；
- token 数据是否可得；
- 用户中断、审批、追加消息等人工介入事件；
- Todo 状态变化；
- 不同 Claude Code 版本的格式差异。

Claude Code 专属关注指标：

- Todo 完成率；
- Bash 成功率；
- 文件操作分布；
- 权限审批次数；
- 用户纠偏次数；
- 子 Agent 使用情况；
- 测试运行和验证证据。

### 11.2 OpenClaw 适配

OpenClaw 用于验证自有 Agent 体系和通用抽象。

优先数据来源：

- sessions_history API；
- session_status API；
- 工具调用记录；
- 模型和 token usage；
- 子 Agent、memory、skill 等内部工具调用。

OpenClaw 专属关注指标：

- Skill 命中情况；
- 子 Agent 协作；
- 工具审批；
- Memory 使用；
- NO_REPLY 或无效回复；
- 模型使用和 token 统计。

### 11.3 内部 Trace 优先，不急于公开协议

MVP 的统一 Trace 是 AgentEval 内部归一化格式。

只有当 Claude Code 和 OpenClaw 两个适配器跑通，并验证字段稳定后，再考虑抽象为公开 AgentTrace Protocol。

---

## 12. Project/User 级诊断

### 12.1 Project 级诊断

Project 级诊断评估同一项目目录下所有 sessions。

回答问题：

- 这个项目中 Agent 使用是否健康；
- 哪些工具最容易失败；
- 哪些任务经常需要人工介入；
- 是否经常出现重复探索；
- 哪些 session 语义效果较差；
- 用户在这个项目中应该如何改进 Agent 使用方式。

### 12.2 User 级诊断

User 级诊断评估当前用户下所有 sessions。

回答问题：

- 用户整体使用 Agent 的质量如何；
- 哪些项目最常出问题；
- 常用模型和 Agent 分布；
- 人工介入是否偏多；
- 是否善用计划、测试、上下文和验证；
- 用户有哪些长期使用习惯可以优化。

### 12.3 Project/User 级语义评估策略

Project/User 级不应默认对所有 session 做昂贵 judge。

建议策略：

1. 全量做过程诊断；
2. 对高风险 session 做语义评估；
3. 支持代表性抽样；
4. 报告中明确语义评估覆盖率。

高风险 session 包括：

- failed；
- interrupted；
- 多次人工纠偏；
- 工具错误多；
- 重复调用多；
- duration 异常长；
- 最终状态 unknown。

---

## 13. 数据可信度原则

AgentEval 必须明确标注数据来源和置信度。

字段来源：

```text
measured      # 直接从日志/API 获取
calculated    # 从其他 measured 字段计算
unavailable   # 数据不可用
```

MVP 不默认使用 estimated。

关键原则：

- 拿不到精确 token 就显示 unavailable；
- 不用假数据填充报告；
- 语义评估必须带 judge model、evidence 和 confidence；
- Project/User 聚合语义结论必须显示覆盖率；
- 数据完整度本身也应作为报告指标。

---

## 14. 路线图

### 14.1 MVP / v0

目标：开源个人版，打通本地评估闭环。

范围：

- Claude Code 基础适配；
- OpenClaw 基础适配；
- 内部最小 Trace Schema；
- session/project/user 三级诊断；
- 语义效果评估 P0；
- 过程证据指标；
- CLI 文本报告；
- JSON 导出。

### 14.2 v0.1

目标：增强诊断质量和可用性。

可能范围：

- 更稳定的 Claude Code 日志解析；
- Project/User 级语义抽样策略优化；
- 重复行为检测；
- 模型对比初版；
- 更好的 coaching suggestions；
- 隐私脱敏配置。

### 14.3 v1

目标：从个人工具走向团队工具。

可能范围：

- HTML 本地 dashboard；
- benchmark 任务集；
- 回归评估；
- CI 集成；
- 多模型质量/成本对比；
- 用户反馈闭环。

### 14.4 商业版

目标：服务中小企业级 Agent 团队。

可能范围：

- 企业 dashboard；
- 团队级报告；
- 多用户/多项目对比；
- 私有 rubric；
- Agent 版本回归；
- 成本 ROI；
- 人工标注校准；
- 私有化部署。

---

## 15. 当前待继续讨论的问题

后续需要继续对齐：

1. Claude Code 实际 session 数据结构和可采集字段；
2. OpenClaw API 数据结构和字段完整度；
3. judge model 的默认选择和成本控制；
4. 语义评估 prompt/rubric 如何设计；
5. Effectiveness Score 的具体评分细则；
6. Project/User 级高风险 session 选择策略；
7. CLI 报告的最终样式；
8. 隐私脱敏和敏感信息处理策略；
9. 免费开源与商业能力的最终边界。

---

## 16. 关键设计决策记录

| 决策点 | 当前选择 | 原因 |
| --- | --- | --- |
| 首个用户 | Agent 重度个人开发者 | 需求清晰，容易本地验证 |
| 产品切入 | 效果评估 + 使用诊断 | 只做过程诊断价值不足 |
| MVP 适配 | Claude Code + OpenClaw | 兼顾外部用户和自有验证 |
| 输出形态 | CLI + JSON | 快速验证，便于后续扩展 |
| 语义评估 | v0 纳入 P0 | 产品核心价值所在 |
| token 策略 | 只展示精确可得数据 | 保持可信，不默认估算 |
| 数据隐私 | 默认不导出完整原始日志 | 降低敏感数据风险 |
| 商业路径 | MVP 开源，高级企业能力收费 | 先获取个人用户，再服务企业 |
| Trace 标准 | 先内部归一，后公开协议 | 避免过早标准化 |

---

## 17. 产品原则

1. **先评效果，再看过程**  
   过程指标服务于效果判断，而不是产品终点。

2. **所有判断必须有证据**  
   不输出无法追溯原因的分数。

3. **宁可 unavailable，不伪造完整性**  
   拿不到精确数据就明确说明。

4. **先个人，后企业**  
   先让个人用户觉得有用，再扩展到团队和商业场景。

5. **本地优先，隐私优先**  
   默认本地分析，不上传完整会话内容。

6. **内部 Schema 先行，公开协议后置**  
   从真实适配中提炼标准，而不是凭空设计标准。
