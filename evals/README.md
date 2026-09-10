# 回归方法

## 目的

推理回归检查问题与因果是否成立，成文回归检查经过校验的分析能否转成容易理解的文章。专项案例定位入口、目的、关键节点、标题、段落、局部结论等具体错误，不增加新的读者输出模式。

日常分析和写作只运行 Skill 的必要自查。这里的独立生成和比较仅在迭代、排查退化或用户要求时执行；Web GPT 的日常使用不以 API、Python 或独立评测为前提。

## 推理回归

### 通用推理

使用 `evals/regression-cases.json` 与 `evals/rubric.md`，检查问题结构、定义与分类、技术及非技术形成解释、目标求解、比较选择、混合问题和未示范主体迁移。事实、用户观点、目标、限制与评价标准分开，经验和结论卡须重新验证。

### 复杂输入与意图路由

使用 `evals/intent-routing-regression-cases.json`，沿用推理评分表。按独立结果提取问题，区分核心、支撑和独立问题；结合对象状态、行动主体、用户角色、时间方向和真实未知路由，不只看疑问词。补全自包含的实际分析问题，并在新证据改变路线时同步修正。

当前明确要求优先于历史上下文；高影响歧义用最少澄清，共享主线可以先回答共同部分。暂定意图不能写成已确认事实。

### 关键节点校验

使用 `evals/node-validation-regression-cases.json`，检查必要、充分、促进、具体路径与伴随关系，区分逆否命题和否命题，检查反例、替代路径、反向因果与共同原因。严格命题和概率性关系分别处理；发现问题要修复节点，不能只附一句存在例外。

历史纵轴、横向对照、多视角和跨领域借解的回归见 `evals/supplementary-analysis-regression-cases.json`。补充方法按需启用，不能替代主链，也不能让每个问题都变成历史研究。

### 目的结构

使用 `evals/purpose-structure-regression-cases.json`，检查目的、现状、缺失条件、方案、新状态与验证的语义关系。

目标求解型目的写外部结果，原理还原型可以写对象稳定角色或目标状态；完成标准与实现分别处理。当前状态只承载事实、能力、限制与未知。每项方案有问题来源，方案后出现的新问题继续推演，不把具体实现误当唯一必要条件。定义、自然、群体涌现和自动情绪不虚构统一目的；历史动机须有材料支持。

## 成文回归

使用 `evals/writing-regression-cases.json`、`evals/writing-rubric.md` 和 `evals/writing-style-pairs.json`，检查技术原理、完整方案、普通读者解释、决策备忘录、经营报告及技术演进说明。

先确认问题建模、目的结构、事实、因果与关键节点校验已经完成，锁定分析定稿，再评价成文。分析定稿包括内部完整分析任务、问题结构、核心结论、关键因果、适用目的节点、必须覆盖项、证据边界与不得推断项。文章契约确定类型、读者任务、范围、视角、详细程度和已知载体。

标题后先呈现简短读者可见问题；目的型文章保留最终目的、当前状态与要解决的问题、采用的方案。正文不暴露“用户当前材料”等生成上下文。成文不临时重新识别问题或添加结论。

### 读者问题、目的层级与标题

使用 `evals/reader-structure-regression-cases.json`。内部完整任务不能原样变成开头长问句，目的不吸收后续要求；标题、层级与父子章节分别承担职责。

问题和判断可用结论标题，方案可用准确名称或动作标题。名称标题与紧邻正文共同检查，不能强求每个标题都是完整判断句；空泛标签和只有模块目录的文章仍不合格。比较材料不应自动变成每篇原理文章的主问题。

### 信息密度

使用 `evals/writing-density-regression-cases.json` 与原有六维成文评分表。检查同一论点跨段、例子首次出现位置、场景增量复用、真实展示与证据边界、图文互补和载体边界。

防止逐句碎段、复杂论证强塞长段、每个小点举例、普通文字代码块和跨章节完整重复。允许有用回指及真实并列。细节来自必要事实、因果和取舍，不来自固定行宽、图片数量或留白。

固定材料只做成文。可以提取单例输入：

```bash
python3 scripts/validate_writing_density.py --case example-before-abstraction
```

命令只导出材料与请求，不调用模型。无固定材料的旧自由题先完成分析定稿；空材料不构成编造事实的许可。生成时不发送 focus、must、must_not、评分字段、成对答案和评审记录。已有自查证据见 `evals/writing-density-review.md`。

### 局部结论选择

使用 `evals/local-conclusion-regression-cases.json`，按输出规则第 5 节和现有成文维度检查当前职责、主要答案、必要限定和展开程度。覆盖同材料的定义、目的、问题、原因、机制，以及未示范对象、保留原句、未知、独立短点和完整因果。

```bash
python3 - <<'PY'
import json
from scripts.validate_writing import load_json, local_conclusion_input
suite = load_json("evals/local-conclusion-regression-cases.json")
print(json.dumps(local_conclusion_input(suite, "meeting-definition"), ensure_ascii=False, indent=2))
PY
```

这仍是输入提取，不是模型回归。不同职责分别在隔离上下文生成，不发送 evaluation 或其他案例答案。全文得分不能掩盖关键定位错误；字数、措辞相似度和是否发生改写不能代替语义判断。历史记录 `evals/local-conclusion-review.md` 是自查，不改写成独立测试。

### 问题归纳与直接表达

新增套件 `evals/directness/cases.json` 包含 12 个受控案例。分析案例检查主要缺口、父子关系、成本等限制覆盖和非技术迁移；成文案例固定分析结果，检查准确短标题、必要否定、机制区别和完整因果。

具体执行、Web GPT 使用路径与数据格式见 `evals/directness/README.md`；用户失败片段见 `evals/directness/failure-excerpts.md`；本次执行证据见 `evals/directness/review.md`。

可执行工具 `scripts/compare_skill_outputs.py` 提供 input、prepare、blind、report：提取输入，按固定版本生成独立任务包，匿名化实际输出，核对材料和评审记录，再汇总结果。工具不自动调用模型；未有真实独立生成与盲评时，明确记为未执行。

## 成对样本

`evals/writing-style-pairs.json` 的 unit_role 区分结论句、解释段和文章开头。解释段的必要展开不是所有结论句都应扩写的依据；准确定位句可保持不变。原有成对改写要求 before 和 after 不同，不代表实际文章必须改写。

读者结构及信息密度套件中的 style_pairs 校准标题、目的、跨段论证、例子和重复。after 不是逐字标准答案，应检查 must_preserve 与 must_not_infer。构造的 before/after 只是示范，不是新旧模型真实输出。

## 执行步骤

1. 入口建模或路由改变时，运行意图路由专项，并抽查定义、解释、行动、选择与混合通用案例。
2. 目的、现状、问题或方案改变时，运行目的专项并抽查技术、情绪、自然、市场和决策，防止强套结构。
3. 核心推理改变时运行通用推理和关键节点套件；局部主体指南改变时运行相关案例及至少两个迁移案例。
4. 成文规则改变时运行文章、读者结构、信息密度与局部结论套件，并抽查至少三个对应推理案例；本次直接表达规则还运行 directness 套件。
5. 分析阶段记录事实、观点、限制、问题关系、路线及适用目的节点。对关键节点检查关系、反例、替代、强度和证据，形成语义定稿，不保存逐步思考记录作为文章。
6. 成文阶段只接收必要规则、固定定稿及文章请求；生成过程不接收案例评审字段、版本对照、其他候选输出或评审记录。
7. 输出冻结后，按对应的 global_invariants、must、must_not 或 evaluation 评审。推理用 `evals/rubric.md`，成文再用 `evals/writing-rubric.md`。
8. 定位失败发生在问题归纳、父子关系、路由、因果、证据、局部结论、名称与作用分工、段落、例子、载体还是整体阅读。先修复上游通用原因，再用同一输入重跑。
9. 保留失败与成功输出，报告全部实际执行范围。结构通过不代替模型输出质量；未执行层次明确记录，不以时间不足或工具缺失静默缩小后宣称全通过。

## 同推演多版本测试

默认比较旧规则与新规则两版，固定相同任务、材料、文件集合、模型与可见设置。纯成文比较冻结同一分析定稿；问题归纳比较使用同一组事实并允许各自形成分析结果。不要把两个阶段混测后把差异全部归为写作。

使用解析后的提交 SHA 防止分支变化。每份输出在独立上下文生成；评审在另外的上下文进行，先隐藏版本与生成者信息，再按同一标准评审。极度压缩、更多碎段等额外版本只在定位具体问题时按需加入，不默认要求四版。

先检查事实、因果、条件与必须覆盖项是否保留，再比较表达偏好。相当或两者均不合格是有效结果。要验证稳定性需适当重复、迁移题和更广覆盖；少量胜出样本不能直接推广。

真实读者测试可以另外记录正确复述、误解、阅读时间、回读位置、主观难度和文风偏好。没有实际执行就不报告这些指标。自动可读性、句长、术语数、标题句法与固定行宽不能替代理解测试。

## 最低通过条件

### 推理套件

建议各通用案例不少于 16/20，没有 `evals/rubric.md` 的严重错误，旧核心案例不出现明显退化；新增主体和迁移案例达到标准。专项满足各自 must 且不出现 must_not。技术与行动建立目的链；定义、自然、市场和情绪不强套。正文不暴露内部路由和检查表，结论卡仅在条件成立时使用。

### 成文套件

建议各案例不少于 10/12，没有 `evals/writing-rubric.md` 的严重错误。标准文章不退化为研究记录、压缩报告或模块百科；详细方案保留用户点名机制。已证明依赖和并行条件保持原关系，关键限定与证据靠近判断。

局部结论回答当前职责；方案名称与紧邻正文共同清楚，既不强迫长标题，也不只列目录。段落按阅读任务分组，复杂论点可跨段；不强塞长段或机械碎段，不逐段强制加粗。例子及时且有用途，假设、演示和证据分开；普通文字不进代码块，必要图文、简短回指与场景增量可以保留。

## 评分记录

模板为 `evals/score-template.json` 和 `evals/writing-score-template.json`。

```bash
python3 scripts/eval_report.py scores.json
python3 scripts/eval_report.py writing-scores.json --suite writing
```

新旧独立对照另保存原始输出、输入哈希、版本、真实模型/上下文信息、匿名映射和评审证据。`scripts/compare_skill_outputs.py report` 只汇总所提供记录，不证明声明的上下文隔离真实发生，也不把工具校验当作语义质量评分。

## 结构校验

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
```

这些检查覆盖仓库结构、历史来源哈希、规则入口、案例字段、成对样本、生成字段分离和工具协议。新增单元测试验证独立对照的准备、盲化、数据绑定与报告；使用合成数据，不代表真实模型运行。

报告始终区分结构测试、同一助手自查、独立上下文生成和独立盲评。同一对话换角色仍属自查。无实际独立调用能力时，可交付规则、案例和工具，但须明确真实对照尚未执行；日常 Web GPT 使用不受此限制。
