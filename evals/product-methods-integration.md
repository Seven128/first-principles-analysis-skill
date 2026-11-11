# 产品思考方法的来源与取舍

## 核验范围

核验日期：2026-11-11。通过 GitHub 仓库 API 核对仓库热度、默认分支提交与许可，并读取下列实际技能文件；搜索页仅用于发现来源。以下 Star 数属于整个仓库，不能称为某个 skill 的 Star 数，也不能据此证明方法有效。未使用无法核实的 X 点赞量。

本次使用这些方法作为候选经验，原创编写适配规则；不导入或执行上游提示词、脚本、工具调用与工作流，也不复制原文模板。方法导入后的结论仍须由当前证据和核心推理规则支持。

| 仓库 | 核验时 Stars | 核验提交 | 许可 |
| --- | ---: | --- | --- |
| [mattpocock/skills](https://github.com/mattpocock/skills) | 321,504 | `4ae2317ddb22b046e26455e4f9c9b3aaaf62212d` | [MIT](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/LICENSE) |
| [phuryn/pm-skills](https://github.com/phuryn/pm-skills) | 27,877 | `9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef` | [MIT](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/LICENSE) |
| [garrytan/gstack](https://github.com/garrytan/gstack) | 141,175 | `f0cd9f8c4b453c1eadd714e4149174ee01179eae` | [MIT](https://github.com/garrytan/gstack/blob/f0cd9f8c4b453c1eadd714e4149174ee01179eae/LICENSE) |
| [deanpeters/Product-Manager-Skills](https://github.com/deanpeters/Product-Manager-Skills) | 7,960 | `cfcb697f14b8891d8b3ec43c16c3547df3e70e13` | [CC BY-NC-SA 4.0](https://github.com/deanpeters/Product-Manager-Skills/blob/cfcb697f14b8891d8b3ec43c16c3547df3e70e13/LICENSE)；仅对照，未移植文字、模板或流程 |

Star 数是当次 API 观察值；需要重新比较热度时应重新读取，不把此表当作持续更新的排名。

## 采用的独立增量

### 依赖式缺口提问

读取 Matt Pocock 的 [grill-me 入口](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/productivity/grill-me/SKILL.md)、[grilling 实现](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/skills/productivity/grilling/SKILL.md)及 [grill-me 使用说明](https://github.com/mattpocock/skills/blob/4ae2317ddb22b046e26455e4f9c9b3aaaf62212d/docs/productivity/grill-me.md)。核验版本的 `grill-me` 仅转调 `grilling`；具体方法在后者，按前置决定已明确的问题组织轮次。

现有核心已包含问题依赖和最少澄清。本次只补充产品方案中未决项的调度方式：区分可查事实、需要取舍和必须实测的缺口；同轮不混入仍依赖其他回答的问题；已有材料和回答可复用；新增回答只影响相关分支。

不采用遍历全部分支才结束、每项决定都交回用户、完成后统一再要一次确认的默认要求。停止条件改为当前决定已有足够依据，或剩余未知已经转成条件分支、验证或后续事项。已授权行动仍按原授权执行。

### 真实任务证据与观察条件

读取 phuryn 的 [interview-script](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/pm-product-discovery/skills/interview-script/SKILL.md)和 gstack 的 [office-hours 创业诊断部分](https://github.com/garrytan/gstack/blob/f0cd9f8c4b453c1eadd714e4149174ee01179eae/office-hours/sections/phase-2a-startup-diagnostic.md)。吸收具体经历、既有做法、实际行为及不代替用户操作的观察方式。

适配后记录招募来源、引导、协助与补贴，区分兴趣、回忆、任务完成、交易和重复行为。现有商业规则已有口头意愿与实际支付的区别；本次增量是说明证据怎样受采集条件影响，以及每种观察能支持到哪个节点。

不采用上游关于调查、演示或没有现成替代方案的绝对判断，也不要求一周内付费的小版本成为所有产品的目标。协助本来属于交付内容时，保留其价值，同时明确成本与支持范围。

### 产品条件分开验证

读取 phuryn 的 [identify-assumptions-existing](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/pm-product-discovery/skills/identify-assumptions-existing/SKILL.md)与 [identify-assumptions-new](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/pm-product-discovery/skills/identify-assumptions-new/SKILL.md)。吸收价值、使用、交付及经营条件需要分别获得证据的检查方向。

适配后只检查影响当前目标的条件，连回主链现有的问题与验证节点。不同维度不能用单项演示或单个指标互相代替；公益、内部工具等按已选目标和支持来源判断。合规、资金来源、替代路径和关键假设排序继续由对应已有规则负责。

## 已覆盖或未采用的内容

| 阅读的候选 | 取舍 | 现有承接或理由 |
| --- | --- | --- |
| [Opportunity Solution Tree](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/pm-product-discovery/skills/opportunity-solution-tree/SKILL.md) | 不再增加完整流程 | 目标→问题→方案→验证、多个候选及回退已有核心规则；不移植固定分支数、固定周期或评分公式。 |
| [prioritize-assumptions](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/pm-product-discovery/skills/prioritize-assumptions/SKILL.md) | 不增加新的评分体系 | 核心已有“会改变选择的关键假设＋信息价值＋验证成本”，不将主观评分写成精确排序。 |
| [brainstorm-experiments-new](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/pm-product-discovery/skills/brainstorm-experiments-new/SKILL.md) | 不另列通用实验流程 | 最小实验、观察指标、继续与退出条件已存在；登记、点击、付款等证据的不同含义纳入证据范围检查。 |
| [analyze-feature-requests](https://github.com/phuryn/pm-skills/blob/9af7bfd0bc47fdad43c2eaa7a43cd13918e7aaef/pm-product-discovery/skills/analyze-feature-requests/SKILL.md) | 去重 | 功能请求与真实问题的分离已有目的结构规则；不强制固定数量的优先功能。 |
| [jobs-to-be-done](https://github.com/deanpeters/Product-Manager-Skills/blob/cfcb697f14b8891d8b3ec43c16c3547df3e70e13/skills/jobs-to-be-done/SKILL.md) | 仅对照，未导入 | 目标与解法、替代做法、不得编造情绪与动机等已有规则；其许可含非商业与相同方式共享条件，未引入原文或模板。 |
| [plan-ceo-review](https://github.com/garrytan/gstack/blob/f0cd9f8c4b453c1eadd714e4149174ee01179eae/plan-ceo-review/sections/review-sections.md) | 不引入整套审查工作流 | 大量工程环节、默认审查清单和逐项批准机制不属于此次必要增量，且会增加日常调用负担。 |

## 接入位置与验证边界

运行时主体指南为 `references/subjects/产品发现与验证.md`，只在产品发现、需求证据或产品成立条件影响当前判断时读取。它提供方法，不是已经证实的结论卡；其产物回到现状、假设、问题、路径和验证节点，再接受核心校验。

回归材料为 `evals/product-experience-regression-cases.json`，覆盖依赖澄清、材料充分时不追问、观察条件、实测未知、非售卖目标及条件之间不可替代。生成阶段只使用案例 `prompt`，`focus`、`must`、`must_not` 与全局不变量留给评审。文件和结构检查本身不证明真实模型输出已通过，也不构成与旧版本的效果对比。
