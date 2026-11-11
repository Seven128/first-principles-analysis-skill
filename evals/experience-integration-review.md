# 已知经验、关键论点与自然表达：本轮验证记录

日期：2026-11-11。改动基线为 `f2677f1ba1e7cedebdd32f55dd6b9c419655739e`。本记录只报告实际完成的检查，不把案例文件存在或结构校验通过当作模型质量证明。

## 改动与案例范围

新增两个按需主体指南：产品发现与验证、商业化与合规。关键论点检查细化最小命题、实质影响门槛、一轮最低检查、共享前提复用和停止条件；自然表达修复进入既有成文检查。

新增回归定义共 23 个：关键节点 7 个、产品经验 6 个、商业化合规 6 个、局部成文 4 个。节点套件现为 13 个案例，局部成文套件现为 37 个案例。定义覆盖不等于全部案例已运行模型生成。

## 结构与工具验证

以下命令在最终运行规则修改后均成功退出：

```bash
python3 scripts/validate_skill.py
python3 scripts/validate_intent_routing.py
python3 scripts/validate_node_reasoning.py
python3 scripts/validate_purpose_structure.py
python3 scripts/validate_writing.py
python3 scripts/validate_writing_density.py
python3 scripts/validate_reader_structure.py
python3 scripts/validate_conclusions.py
python3 scripts/lint_language.py --strict
python3 -m unittest discover -s tests -p 'test_*.py'
git diff --check
```

结果：40 项单元测试通过；10 项历史来源哈希未改变；9 份主体指南、6 张结论卡及相关专项案例结构通过。另使用技能创建工具包的 `quick_validate.py` 检查入口元数据，结果为 `Skill is valid!`。这些结果只说明所列结构、工具和数据契约满足检查。

## 独立生成与独立评阅

原始输入、输出、生成上下文说明及运行文件摘要保存在 [experience-integration-run.json](experience-integration-run.json)。每份输出由新的子代理上下文生成，使用 `fork_turns=none`，仅收到运行规则路径和任务材料，没有评审字段、改动对照或其他输出。模型与推理设置继承会话，未另行覆盖。

最初六份输出由评阅代理 `review_forward_outputs` 在另一个独立上下文中，按对应案例的 `must`、`must_not` 或 `evaluation`，结合推理与成文评分表评阅；没有读取改动或来源取舍记录。以下是实际输出的结果，不是构造的标准答案：

| 案例 | 结果 | 输出中可核对的依据 |
| --- | --- | --- |
| `compound-premises-need-separate-checks` | pass | 分开兴趣、独立使用、付费、许可、交付及盈亏；现有积极信号未被当成整体可扩大投放的证明。 |
| `shared-premise-distinct-branches` | pass | 复用合同材料，分别判断 V1 图表展示、原始数据转卖与未来 V2；限制和未决只影响相应分支。 |
| `natural-preserve-author-voice` | pass | 只修复句间连接，保留第一人称、二十分钟、雨天改路线与“也许”；没有补造经历或检测报告。 |
| `quantitative-pivot-and-sensitivity` | pass | 识别每单贡献 15 元及 400 单保本，给出正确利润公式和有条件的订单量敏感性。 |
| `general-rule-without-technical-template` | pass | 从读书会入口难找推出最小信息补充和效果观察，没有套入产品、技术或商业化清单。 |
| `product-known-context-skips-interrogation` | pass | 直接比较已给成本与时间数据，没有重复访谈或加入收费目标；保持样本零差错与真实错误率的区别。 |

### 审查后补测

独立集成审查发现两处歧义：一是“置信度变化”缺少实质影响门槛，二是维护规则对技术文章中性口吻的要求没有限定新写文章。已统一核心、入口、维护说明和回归定义，并经同一审查者复核，确认问题消除。

最初六份输出及其 33 个运行文件摘要保持原记录。修正影响运行时的文件只有 `SKILL.md` 和关键节点 `04a`；后续运行以 `post_review_run.runtime_sha256_overrides` 覆盖这两个摘要，其余沿用初始快照。没有把最初六份输出重新标记成最终规则生成。

补测 `all-decisive-claims-not-top-three` 同时覆盖五项决定性条件与不影响事实的标题换词、编辑信心微增。输出保留“尚不具备执行条件”，明确电力未验收与消防通道受阻，且不因换词要求全量重查。同一独立评阅代理追加评阅为 **pass**，未发现严重错误。它在读取补测记录时也看到了 `reason` 元数据，因此这次补评不声称与修正说明隔离，更不称为盲评；没有读取 diff、重新生成或重复评阅原六份。

## 结论边界

本轮只有所存样本的单版本独立生成和独立评阅，没有完整模型回归、重复采样、新旧版本盲评、真实读者测试或耗时基准。不能据此宣称整体质量优于旧版，或承诺具体调用时长。

规则层面用按需加载、逐命题最低检查、共享前提复用和定向补证控制重复工作；实际时长与稳定性仍需另行测量。产品与合规专项中未抽到的场景，目前只有案例定义和结构校验。
