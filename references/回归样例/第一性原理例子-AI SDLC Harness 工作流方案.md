# AI SDLC Harness 工作流方案

# AI SDLC Harness 工作流方案

## 一、最终目的

设计一套面向 AI Agent 的需求全链路 Harness 工作流，提高 Agent 在需求各阶段的完成效率。

这里的效率不是单次代码生成速度，而是 Agent 在复杂项目中完成阶段目标、产出阶段交付物、衔接上下游信息、处理需求变更和通过交付约束的整体效率。

这套工作流主要降低三类成本：

- 阶段执行成本：通过阶段角色 Skill、模板和上下文约束，让 Agent 在对应阶段更快产出符合预期的交付物。

- 阶段衔接成本：通过统一事实源、文档索引、任务状态和变更协议，减少阶段切换、产物同步和重新理解的成本。

- 阶段交付成本：通过把质量检查、Review 清单、测试与发布检查固定为阶段完成条件，减少每次交付时重新组织约束的心智成本。

## 二、当前现状与要解决的问题

### 2\.1 稍有复杂度的软件项目天然需要多阶段软件工程

现状： 只要项目超过 demo、脚本或一次性页面的复杂度，就不能长期只靠“想到什么就让 Agent 写什么”的方式推进。软件工程本身要求需求被拆成多个阶段，例如需求收集、产品方案、技术方案、开发实现、Review、测试、发布和需求变更。每个阶段都有独立目标，也会形成对应交付产物。

需求收集 \-\> 原始需求记录、问题澄清、需求边界

产品方案 \-\> PRD、用户场景、验收标准、Out of Scope

技术方案 \-\> 架构设计、接口契约、数据结构、任务拆分

开发实现 \-\> 代码、测试、实现记录、提交记录

Review \-\> Review 报告、风险清单、重构建议

测试验证 \-\> 测试计划、测试矩阵、回归记录

发布上线 \-\> Release Note、部署检查、回滚方案

需求变更 \-\> RFC、影响范围、任务回退或增量计划

要解决的问题： 需要把每个阶段的目标、输入、输出和完成条件固定下来，让 Agent 在正确阶段完成正确交付物，而不是把需求、方案、开发、Review 和测试混成一段连续聊天。否则项目复杂度上升后，容易出现需求边界不清、方案和实现偏移、Review 缺少依据、测试缺少覆盖目标、变更无法回溯等问题。

### 2\.2 阶段产物分散，跨阶段衔接存在切换成本和理解成本

现状： 在没有统一到同一个 Agent 客户端或同一套项目工作区的情况下，不同阶段的产物容易分散在不同位置：产品文档可能在 Web AI、Notion、飞书、Confluence 或 Google Docs 中生成；技术方案可能在 IDE Agent 对话里生成；开发过程发生在 coding agent 中；Review 准则可能是临时 prompt；测试策略可能靠人工补充。

这种分散会带来两类成本：

- 切换成本：人需要在多个工具、文档、会话和代码仓库之间复制、同步、解释和校对。

- 理解成本：Agent 进入新阶段时，无法天然继承上一阶段的产物、边界、取舍和未解决问题，需要重新读取、总结和对齐。
需求变更是这个问题的典型放大场景。需求变化后，受影响的通常不是单个代码点，而是 PRD、技术方案、接口契约、任务计划、实现代码、测试用例、Review 结论和实现文档组成的一整条链。阶段产物越分散，Agent 越容易漏改受影响内容，或误改未受影响的稳定内容。
要解决的问题： 需要把阶段产物统一到一套可寻址、可引用、可版本化的项目事实源中，并建立阶段之间的连续链路。Agent 进入下一阶段时，应能明确读取上一阶段产物；需求变更时，应通过 RFC、影响范围分析、局部补丁、任务回退或增量计划，把变更限制在受影响链路内，而不是重新理解或重写整个项目。

### 2\.3 单阶段主要依靠 vibe 推进，但阶段 Skill 与交付硬约束需要固定进工作流

现状： 在单个阶段内部，Agent 的主要工作方式仍然是 vibe：人给出目标，Agent 结合上下文进行生成、修改、总结、补充和修正。阶段角色 Skill 不替代 vibe，而是沉淀该阶段的最佳实践，用来提高 vibe 的效率和稳定性。

不同阶段需要不同 Skill：PM 阶段需要需求澄清、边界定义和验收标准；架构阶段需要模块拆分、接口契约和风险识别；开发阶段需要按任务落地、控制修改范围和补测试；Review 阶段需要只读审查、风险分级和需求一致性检查；测试阶段需要边界条件、回归范围和覆盖矩阵。

但从阶段开始到阶段交付完成，不能只依赖 Agent 自我声明完成。为了保证产物质量，交付环节通常需要硬约束，例如 Lint、typecheck、unit test、integration test、build、coverage、review checklist、release smoke test 等。这些约束可能通过本地插件、脚本、Makefile、npm script、Agent 工具调用执行；团队协作时，也可能放在 CI/CD、GitHub Actions、GitLab CI、分支保护、PR check 或部署流水线中执行。执行形式不同，但本质上都属于阶段交付条件。

要解决的问题： 需要把阶段 Skill 和交付硬约束都固定进工作流。Skill 负责提高单阶段 vibe 的产出效率；硬约束负责保证阶段交付质量。硬约束不一定由 Harness 自己执行，但必须被声明为阶段完成和状态流转的判断依据。Agent 可以触发脚本、修复失败、记录结果，但不能绕过这些约束直接推进状态。

## 三、采用的方案

### 3\.1 总体思路

AI SDLC Harness 不替代 Agent，也不把软件工程完全自动化。它在仓库中固定一套工作流骨架：

阶段定义

\-\> 阶段产物

\-\> 阶段 Skill

\-\> 阶段事实源

\-\> 阶段交付硬约束

\-\> 阶段流转规则

\-\> 需求变更回退规则

Agent 在单阶段内部仍然以 vibe 方式执行；Harness 负责规定当前阶段、应读内容、应写产物、应使用 Skill、完成前必须通过的 gate，以及需求变更时如何局部修正链路。

### 3\.2 核心设计原则

- 阶段契约化：每个阶段都有输入、输出、Skill、gate 和下一阶段入口。

- 产物仓库化：关键产物进入 \.docs/、\.harness/ 或同一工作区，成为可寻址、可版本化事实源。

- 语义切片化：阶段文档按业务能力、技术主题、任务、风险或变更事件切片，避免长文档被固定 chunk 检索时丢失边界信息。

- Skill 阶段化：每个 Skill 只沉淀一个阶段或动作的 SOP，不写成巨型 prompt。

- Gate 声明化：lint、typecheck、test、build、review checklist、release smoke test 等硬约束必须作为阶段完成条件。

- 变更补丁化：需求变化先进入 RFC，再做影响分析、局部补丁、任务回退或增量任务。

- 实现文档增量化：技术方案是计划，implementation doc 是开发后的事实。

- 派生视图自动化：overview\.html 由脚本生成，只用于浏览，不作为事实源。

- Checkpoint 条件触发：长任务、中断、gate failure、BLOCKED 或上下文压缩风险出现时，写任务内执行快照。

### 3\.3 事实源与派生产物

真正的事实源是：

- \.harness/state/\*\.yaml

- \.harness/policies/\*\.yaml

- \.agents/skills/\*/SKILL\.md

- \.docs/\*\*/\*\.md

- \.docs/INDEX\.md

- Makefile

- tools/\*\.py
派生产物是：

- \.docs//overview\.html
overview\.html 由 tools/build\_doc\_overviews\.py 生成。它把某阶段 Markdown slices 合成 HTML 总览，方便人类浏览和阶段交接，但需求引用、Review、测试和变更影响分析仍应引用原始 Markdown slice。

## 四、仓库结构

推荐模板结构如下：

/project\-root

├── AGENTS\.md

├── Makefile

├── README\.md

│

├── \.docs/

│ ├── INDEX\.md

│ ├── 00\_raw/

│ ├── 01\_product/

│ ├── 02\_architecture/

│ ├── 03\_tech\_plan/

│ ├── 04\_implementation/

│ ├── 05\_decisions/

│ ├── 06\_review/

│ ├── 07\_test/

│ ├── 08\_release/

│ └── rfc/

│

├── \.harness/

│ ├── state/

│ │ ├── lifecycle\.yaml

│ │ ├── tasks\.yaml

│ │ ├── tasks\.draft\.yaml

│ │ ├── gate\_results\.log

│ │ ├── checkpoints/

│ │ └── memory\.md

│ ├── policies/

│ │ ├── phase\_contracts\.yaml

│ │ ├── gates\.yaml

│ │ ├── allowed\_paths\.yaml

│ │ └── risk\_matrix\.yaml

│ ├── templates/

│ └── archive/

│

├── \.agents/skills/

├── tools/

├── \.github/workflows/

└── src/ or services/

### 关键目录说明：

- AGENTS\.md：Agent 全局协议，包含事实源、工作规则、提示词语言契约、checkpoint 和 overview 规则。

- \.docs/：阶段产物事实源。每个阶段目录可包含多个 Markdown slice 和一个 generated overview\.html。

- \.harness/state/：当前状态源，包括生命周期、任务、gate 结果、checkpoint 和项目记忆。

- \.harness/policies/：阶段契约、gate、路径约束和风险矩阵。

- \.harness/templates/：PRD、技术方案、任务、实现文档、Review、测试、RFC、Release、Checkpoint 等模板。

- \.agents/skills/：阶段角色 Skill。

- tools/：确定性脚本和校验工具。

- Makefile：统一命令入口。

## 五、生命周期与阶段契约

### 5\.1 生命周期状态

\.harness/state/lifecycle\.yaml 只记录当前项目处于哪个阶段，不记录所有任务细节。核心字段：

project\_name: "ProjectTemplate"

version: "v0\.1"

current\_phase: "REQUIREMENT\_GATHERING"

active\_role: "pm"

active\_skill: "pm\_prd"

current\_milestone: "MVP"

allowed\_next\_phases:

- "ARCHITECTING"
history: \[\]

### 阶段枚举：

- IDLE

- REQUIREMENT\_GATHERING

- ARCHITECTING

- SPRINTING

- REVIEWING

- TESTING

- RELEASING

- COMPLETED

- RFC\_RECALIBRATION

- BLOCKED
阶段流转不手改 lifecycle\.yaml，使用：

python3 tools/transition\.py \-\-to

### 5\.2 阶段契约

阶段契约写在 \.harness/policies/phase\_contracts\.yaml。核心关系如下：

阶段

Skill

主要输入

主要输出

出口 Gate

下一阶段

REQUIREMENT\_GATHERING

pm\_prd

\.docs/00\_raw/

\.docs/01\_product/, \.docs/INDEX\.md

make validate\-pm

ARCHITECTING

ARCHITECTING

architect\_design

PRD、现有架构、代码结构

架构文档、技术方案、tasks\.draft\.yaml

make validate\-design

SPRINTING

SPRINTING

dev\_sprint

tasks\.yaml、PRD、技术方案

代码、测试、implementation docs、gate 记录

make validate\-dev

REVIEWING

REVIEWING

reviewer

PRD、技术方案、实现文档、git diff

Review report

make validate\-review

TESTING

TESTING

tester

PRD、技术方案、实现文档、Review

Test plan、测试矩阵、回归记录

make validate\-test

RELEASING

RELEASING

release\_manager

测试结果、build artifacts

Release note、smoke result、rollback plan

make validate\-release

COMPLETED

RFC\_RECALIBRATION

rfc\_recalibrate

RFC、PRD、技术方案、任务状态

局部补丁、任务回退或增量任务

make validate\-rfc

原阶段或 SPRINTING

## 六、文档切片与阶段产物

### 6\.1 为什么要语义切片

RAG 能减少一次性塞进上下文的内容，但固定 chunk 和余弦召回存在信息损失。对 README 这类说明文档，RAG 损失通常可以接受；对需求边界、否定约束、接口契约、测试矩阵、RFC 影响范围等执行约束，不能只依赖 RAG。

所以 \.docs/ 采用粗粒度语义切片：

- 小到足以被稳定检索和引用。

- 大到保持一个完整语义单元。

- 不按固定 token 或段落机械切。

### 6\.2 各阶段切片责任

文档切片不是统一由 pm\_prd 完成，而是谁生成阶段产物，谁负责按该阶段语义边界切片。

目录

负责 Skill

切片边界

\.docs/00\_raw/

pm\_prd

一次会议、一段用户输入、一份外部需求文档或一次聊天记录

\.docs/01\_product/

pm\_prd

业务能力、用户场景、验收边界、Out of Scope

\.docs/02\_architecture/

architect\_design

领域边界、子系统、跨模块架构问题、关键技术风险

\.docs/03\_tech\_plan/

architect\_design

可实现范围、接口契约、数据模型、模块方案、任务组

\.docs/04\_implementation/

implementation\_doc

已完成任务、真实实现模块、核心数据流

\.docs/05\_decisions/

architect\_design

单个架构决策，一份 ADR 对应一个 durable decision

\.docs/06\_review/

reviewer

一次 Review 批次、一个 PR、一个里程碑、一个模块或一个风险主题

\.docs/07\_test/

tester

测试计划、测试矩阵、回归批次、领域测试范围

\.docs/08\_release/

release\_manager

版本、发布批次、hotfix、rollback plan

\.docs/rfc/

rfc\_recalibrate

一次可独立评估、实现和回归的需求变更

如果文档变化没有改变语义边界，更新原 slice；如果新增独立场景、拆分模块、合并流程或 RFC 改变影响范围，应新增、拆分、合并或废弃 slice，并更新 \.docs/INDEX\.md。

### 6\.3 overview\.html

每个 \.docs// 目录生成一个 overview\.html：

make docs\-overview

make validate\-doc\-overviews

规则：

- overview\.html 不手写。

- Markdown slices 和 \.docs/INDEX\.md 才是事实源。

- 任意 \.docs//\*\*/\*\.md 变化后，运行 make docs\-overview。

- make validate\-harness 会检查 overview 是否最新。

## 七、任务状态与开发循环

### 7\.1 tasks\.yaml

\.harness/state/tasks\.yaml 是开发阶段的机器可读任务事实源。典型任务字段：

current\_phase: "SPRINTING"

current\_task\_id: "DEV\-003"

tasks:

- id: "DEV\-003"
title: "实现登录失败次数限制"
status: "pending"
priority: "P1"
docs:
product:
\- "\.docs/01\_product/auth/security\.md"
tech\_plan:
\- "\.docs/03\_tech\_plan/auth/rate\_limit\.md"
rfc: \[\]
allowed\_paths:

    - "src/auth/\*\*"

    - "tests/auth/\*\*"
    required\_gates:

    - "make lint"

    - "make test\-current\-domain"
    implementation\_doc: "\.docs/04\_implementation/auth/login\_rate\_limit\_impl\.md"
    checkpoint\_required: false
    checkpoint: "\.harness/state/checkpoints/DEV\-003\.md"
    gate\_result: ""
    commit: ""

### 任务状态：

- pending

- in\_progress

- done

- blocked

- pending\_revision

- cancelled

- archived

### 7\.2 开发阶段循环

开发阶段不是反复重写整个 Sprint 计划，而是：

读取 current\_task

\-\> 基于技术方案和任务上下文生成当前任务局部 plan

\-\> 执行代码和测试

\-\> 运行 required\_gates

\-\> 写 implementation doc

\-\> 更新 tasks\.yaml

\-\> 刷新 overview\.html

\-\> 选择下一个 pending task

只有这些情况才回到 RFC 或架构阶段重新规划：

- 技术方案被实现证明不可行。

- 当前任务暴露新的架构风险或跨模块边界变化。

- 需求发生变化。

- allowed\_paths 无法覆盖必要修改。

- gate 失败不是普通代码问题，而是设计、基建或环境阻塞。

### 7\.3 Checkpoint Protocol

Checkpoint 是 task 内部执行快照，用来降低上下文压缩、中断、新开对话或多人交接时的信息损失。它不是 PRD、不是技术方案、不是正式任务拆分，也不是完成后的 implementation doc。

层级关系：

PRD

\-\> tech plan

\-\> tasks\.yaml 中的 task

\-\> 当前 task 的局部 plan

\-\> checkpoint

触发条件满足任一项时写 checkpoint：

- 当前 task 预计无法在一个连续工作回合内完成。

- 修改文件数超过 5 个。

- 出现 gate failure。

- 出现 BLOCKED 候选原因。

- 发现技术方案和真实实现明显偏移。

- 用户要求暂停、切换对话或继续前保存现场。

- Agent 判断上下文可能接近压缩。
触发后：

1. 在当前 task 中设置 checkpoint\_required: true。

2. 设置 checkpoint: "\.harness/state/checkpoints/\.md"。

3. 按 \.harness/templates/CHECKPOINT\_TEMPLATE\.md 写 checkpoint。

4. 同步更新 \.harness/state/checkpoints/latest\.md。

5. 运行 make validate\-checkpoint。
任务完成并写入 implementation doc 后，可以把 checkpoint\_required 改回 false；历史 checkpoint 可保留用于恢复。

## 八、阶段 Skill

每个 Skill 只负责一个阶段或动作。

Skill

负责内容

manager

读取 lifecycle/tasks/index，路由 /status、/next、/advance、/rfc、/checkpoint，执行阶段切换

pm\_prd

原始需求归档、PRD 切片、验收标准、Out of Scope、Open Questions

architect\_design

架构设计、技术方案、接口契约、任务草案、ADR

dev\_sprint

按 current\_task\_id 执行开发、控制 allowed\_paths、运行 required\_gates

implementation\_doc

记录真实实现结构、数据流、测试覆盖和方案偏移

reviewer

只读 Review，输出 findings、风险、重构建议和测试入口结论

tester

生成 test matrix、补测试、记录回归和覆盖缺口

release\_manager

Release note、build artifacts、smoke test、deployment checklist、rollback plan

rfc\_recalibrate

RFC 影响分析、局部补丁、任务回退或增量任务

### 提示词语言契约：

- 面向人阅读的说明、规则、SOP、检查清单使用中文。

- 机器契约保持英文，包括字段名、路径、命令、阶段枚举、状态枚举、脚本参数。

- 不翻译 current\_phase、active\_skill、allowed\_paths、required\_gates、implementation\_doc 等字段名。

- 不翻译 REQUIREMENT\_GATHERING、SPRINTING、done、pending\_revision 等枚举。

- 后续更新提示词时运行 make validate\-harness。

## 九、Gate 与命令入口

### 9\.1 常用命令

make status

make docs\-overview

make validate\-doc\-overviews

make validate\-checkpoint

make validate\-harness

make validate\-current

make validate\-pm

make validate\-design

make validate\-dev

make validate\-review

make validate\-test

make validate\-release

make validate\-rfc

### 9\.2 阶段 gate

- validate\-pm：检查 PRD、验收标准、Out of Scope、Open Questions。

- validate\-design：检查架构、技术方案和 tasks\.draft\.yaml。

- validate\-dev：检查任务状态、路径约束、checkpoint、lint、测试和 implementation docs。

- validate\-review：检查 Review report。

- validate\-test：检查 test plan、test matrix、回归和覆盖缺口。

- validate\-release：检查 release note、smoke result 和 rollback plan。

- validate\-rfc：检查 RFC、影响范围和回归要求。

### 9\.3 CI/CD

团队协作时，Makefile gate 可以映射到 GitHub Actions、GitLab CI、PR check 或分支保护。当前模板提供 \.github/workflows/harness\.yml，默认运行 validate\-harness，也可手动选择其它 gate。

## 十、需求变更机制

### 10\.1 RFC 原则

需求变更不能直接改 PRD、技术方案、任务或代码。先写 RFC，再影响分析，再局部补丁。

RFC 必须包含：

- 变更背景

- 变更内容

- Product impact

- Technical impact candidates

- Acceptance Criteria

- Regression Requirements

- Status: DRAFT / APPLIED / VERIFIED / ARCHIVED

### 10\.2 开发中途变更

触发条件：tasks\.yaml 中仍有 pending 或 in\_progress 任务。

处理流程：

进入 RFC\_RECALIBRATION

\-\> 局部修改 PRD / 技术方案

\-\> 标记受影响 done 任务为 pending\_revision

\-\> 未完成但受影响任务追加 revision notes

\-\> 恢复 SPRINTING

\-\> 重新执行受影响任务

\-\> 运行回归测试

### 10\.3 封版后变更

触发条件：当前里程碑已完成或准备新版本。

处理流程：

归档旧 tasks\.yaml

\-\> 新建增量 tasks

\-\> 局部修改文档

\-\> 执行增量任务

\-\> 全局回归测试

\-\> 新版本归档

### 10\.4 影响分析边界

影响分析不能假定绝对精确。推荐组合：

- LLM 语义识别：找业务入口和概念入口。

- 静态分析：从导入关系、调用关系、测试引用生成候选范围。

- 回归测试：验证未变更模块没有被破坏。

## 十一、宏指令协议

宏指令由 manager 根据生命周期路由：

宏指令

作用

/status

读取 lifecycle、tasks、gate 结果，报告当前状态

/next

根据当前阶段调用对应 Skill

/advance

运行当前阶段出口 gate，通过后流转

/rfc

挂起当前流程，进入 RFC 变更处理

/syncdocs

归档/切分长文档，更新 \.docs/INDEX\.md

/overview

运行 make docs\-overview

/checkpoint

写入或更新 \.harness/state/checkpoints/latest\.md

/review

进入只读 Review

/test

进入测试计划和验证流程

## 十二、Codex 适配方式

Codex 不需要真实“模式切换”：

- 阶段由 lifecycle\.yaml 决定。

- 角色由 active\_skill 决定。

- 阶段切换由 transition\.py 完成。

- 切换裁决由 Makefile / Hook / CI 完成。
新对话或上下文压缩后的恢复入口：

1. 读取 AGENTS\.md。

2. 运行 make status。

3. 读取 \.harness/state/lifecycle\.yaml。

4. 读取 \.harness/state/tasks\.yaml。

5. 如果存在 \.harness/state/checkpoints/latest\.md，先读取 checkpoint。

6. 根据 active\_skill 进入当前阶段。

## 十三、最小可落地版本

最小闭环可以先保留：

/project\-root

├── AGENTS\.md

├── Makefile

├── \.docs/

│ ├── INDEX\.md

│ ├── 01\_product/

│ ├── 03\_tech\_plan/

│ ├── 04\_implementation/

│ └── rfc/

├── \.harness/state/

│ ├── lifecycle\.yaml

│ ├── tasks\.yaml

│ └── checkpoints/

├── \.agents/skills/

│ ├── manager/

│ ├── dev\_sprint/

│ ├── implementation\_doc/

│ └── rfc\_recalibrate/

└── tools/

├── build\_doc\_overviews\.py

├── transition\.py

├── validate\_checkpoint\.py

├── validate\_tasks\.py

└── validate\_task\_docs\.py

最小命令：

- /status

- /next

- /advance

- /rfc

- /overview

- /checkpoint
最小任务完成标准：

1. 代码已修改。

2. 相关检查已通过。

3. implementation doc 已生成。

4. \.docs/INDEX\.md 已更新。

5. overview\.html 已刷新。

6. 如触发 checkpoint，checkpoint 已生成并通过校验。

7. tasks\.yaml 已记录状态。

## 十四、完整工作流示例

场景：新增“登录失败 5 次后锁定账号 10 分钟”功能。

1. 需求进入系统：

- 保存原始需求到 \.docs/00\_raw/。

- 生成 \.docs/01\_product/auth/account\_lock\.md。

- 记录 Open Questions，例如管理员解锁是否需要审计日志。

- 更新 \.docs/INDEX\.md 和 overview\.html。

2. 进入架构阶段：

- 运行 make validate\-pm。

- transition\.py \-\-to ARCHITECTING。

- 生成架构文档、技术方案和 tasks\.draft\.yaml。

3. 进入开发阶段：

- 确认任务后进入 SPRINTING。

- dev\_sprint 读取当前 task、PRD 和技术方案。

- 在 allowed\_paths 内修改代码和测试。

- 运行 required\_gates。

- 如果任务过长或 gate 失败，写 checkpoint。

4. 任务完成：

- gate 通过后调用 implementation\_doc。

- 写 \.docs/04\_implementation/auth/account\_lock\_impl\.md。

- 更新 \.docs/INDEX\.md、overview\.html 和 tasks\.yaml。

5. Review、测试、发布：

- reviewer 输出 Review report。

- tester 生成 test matrix 并跑回归。

- release\_manager 输出 release note、smoke result 和 rollback plan。

6. 后续变更：

- 新需求写入 \.docs/rfc/RFC\_\*\.md。

- rfc\_recalibrate 做影响分析。

- 受影响任务标记为 pending\_revision 或生成增量任务。

- 执行回归测试。

## 十五、新旧方式对比

### 15\.1 单纯 vibe coding

- 优点：Agent 能快速生成局部代码、修复局部 bug、补测试、解释代码。

- 瓶颈：阶段产物、任务状态、交付约束和需求变更记录没有统一固定下来。

- 风险：项目越长，越依赖人类手动同步上下文；需求变更时容易漏改或误改。

### 15\.2 AI SDLC Harness

- 新增机制：阶段契约、统一事实源、阶段 Skill、任务状态、交付 gate、实现文档、RFC、overview、checkpoint。

- 改变层级：不是提升 Agent 单次生成能力，而是提升 Agent 参与复杂软件工程时的阶段衔接和交付可验证性。

- 收益来源：降低阶段执行成本、阶段衔接成本和阶段交付成本。

## 十六、总结

AI SDLC Harness 是面向 AI Agent 的需求全链路工作流骨架。它把阶段目标、阶段产物、阶段 Skill、任务状态、交付 gate、实现文档、语义切片、派生总览、checkpoint 和 RFC 变更协议固定进仓库。

Agent 仍然以 vibe 方式完成单阶段任务；Harness 负责让整个项目保持阶段连续、事实可寻址、交付可验证、变更可回溯。

