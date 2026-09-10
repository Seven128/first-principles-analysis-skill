# 问题归纳、直接表达与独立对照

## 使用范围

日常分析、文章生成继续使用原有 Skill。这里的案例与脚本只在修改 Skill、排查退化或用户要求比较时使用，不增加每次写作的模型调用、订阅、API Key 或独立评审前置条件。

`failure-excerpts.md` 保存用户文章的失败片段及来源边界；`cases.json` 分离生成输入和评审要求；`review.md` 记录本次实际验证到哪一步。历史来源与旧自查记录保持原样。

## 分开测试问题归纳与成文

`analysis` 案例从相同事实和请求出发，检查主要缺口、父子关系、限制覆盖、目的结构及方案来源。`writing` 案例使用相同的分析定稿，只比较表达，不在写作时补造事实或重建问题。

12 个案例覆盖 Agent 原失败、仓库迁移、并行条件、工具标题、记忆与上下文、沙箱范围、必要否定、动机未知、保留原句、完整因果、成本问题及简单定义。评审沿用 `evals/rubric.md` 和 `evals/writing-rubric.md`，不新增一套分数。比较结论可以为 A、B、相当或两者都不合格。

名称标题与紧邻正文共同检查：标题准确定位方案，正文保留作用和必要因果，就可以通过。不要因名称不是完整句而扣分，也不要把只有模块目录的文章判为成功。短名称漏掉独立机制、删除必要否定、把所有多轮任务写成跨会话任务，都属于内容错误。

## 四种证据分别记录

| 证据 | 能说明什么 |
| --- | --- |
| 结构与脚本测试 | 文件、输入提取、盲化及记录校验按预期工作 |
| 同一助手自查 | 已知材料下，作者发现或修复了哪些具体问题 |
| 独立上下文生成 | 各版本在隔离的生成上下文中实际产生了输出 |
| 独立盲评 | 未见版本对应关系的独立评审者比较了实际输出 |

同一对话换一个角色不产生独立上下文。不同模型名称也不自动证明上下文隔离。隔离可以使用同一模型的不同干净上下文；仍须记录同模型偏差与评审者限制。少量偏好结果不证明稳定提升，模型评审也不能替代真实读者的阅读时间或理解实测。

## 固定版本和输入

使用已解析的提交 SHA，避免生成过程中 `main` 或分支移动。两版必须使用同一组运行材料、同一任务及尽可能相同的模型设置。分析案例读取脚本中的 `ANALYSIS` 文件集及案例 `guides`；纯成文案例读取 `WRITING` 文件集。完整分析和写作正文继续分工。

规则包格式：

```json
{
  "revision": "40字符的真实提交SHA",
  "files": {
    "references/core/05-输出与表达规则.md": "该提交下的完整文件内容"
  }
}
```

以上仅示意格式，不能省略运行文件。脚本会检查文件集合一致、必要材料存在，并拒绝 `evals/`、历史样例或评审记录混入规则包。相同路径的文件内容必须来自对应提交；脚本只计算所供文本的哈希，来源真实性仍由导出者负责。

本地 Git 工作区可以按指定案例导出两个完整规则包：

```bash
python3 - OLD_REF NEW_REF tool-heading <<'PY'
import json, subprocess, sys
from pathlib import Path
from scripts.compare_skill_outputs import ANALYSIS, WRITING, get_case
case = get_case(sys.argv[3])
paths = sorted(set(ANALYSIS if case['stage'] == 'analysis' else WRITING) | set(case.get('guides', [])))
for label, ref in zip(('before', 'after'), sys.argv[1:3]):
    sha = subprocess.check_output(['git', 'rev-parse', '--verify', ref + '^{commit}'], text=True).strip()
    files = {p: subprocess.check_output(['git', 'show', sha + ':' + p]).decode('utf-8') for p in paths}
    with Path(label + '.json').open('x', encoding='utf-8') as f:
        json.dump({'revision': sha, 'files': files}, f, ensure_ascii=False, indent=2)
PY
```

本次修改前版本为 `753abadcdd30ade6ab79bceea383aafb8c9e8323`；修改后使用实际待评审提交。不要把已知失败文章重新贴给两版模型，再将定向修稿当作从同一任务独立生成。

## 准备与生成

```bash
python3 scripts/compare_skill_outputs.py input tool-heading
python3 scripts/compare_skill_outputs.py prepare \
  --before before.json --after after.json \
  --case tool-heading --out /tmp/fp-comparison/tool-heading --repeats 1
```

`input` 只导出 `request` 和 `material`。`prepare` 只生成材料，不调用任何模型。默认每版一份用于小规模检查；需要观察波动时再增加重复次数，不能把默认数量当作稳定性的证明。

每个 `generation/<job_id>.json` 独立交给一个生成上下文。不要发送整个运行目录、`private/`、其他候选输出、案例评审条件或此处的失败片段。分析案例先完成分析定稿再按请求交付；纯成文案例直接使用锁定材料。保存原始最终输出为 `outputs/<job_id>.md`，不要先人工润色再冒充原始生成。

操作者另存 `outputs/<job_id>.json`：

```json
{
  "actor": "实际调用工具或操作者",
  "model": "实际模型名称或界面可确认的型号",
  "settings": {"reasoning": "实际设置；不可见则明确记录 unknown"},
  "origin": "external",
  "context_id": "可追踪的独立上下文标识",
  "run_id": "实际运行记录标识",
  "isolation": "fresh",
  "packet_sha256": "本次 generation 文件的 SHA256"
}
```

`origin` 可为 `external`、`self`、`synthetic`；`isolation` 可为 `fresh`、`shared`、`unknown`。自查使用 `self`，脚本测试用 `synthetic`；无法确认隔离时使用 `unknown`。不要让模型虚构其不可见的上下文标识、模型参数或工具运行证据。

## 盲评与汇总

```bash
python3 scripts/compare_skill_outputs.py blind /tmp/fp-comparison/tool-heading
```

脚本检查全部真实输出及其对应输入，随机分配 A/B，只在 `private/blind.json` 保存版本映射。`review/` 中只有共同材料、统一评审要求和匿名候选，不包含生成者信息与版本标签。评审者只能接收单份 review 文件；组织者见过映射时不能同时自称盲评者。文字风格仍可能让人猜到版本，因此这里只能控制显式标签与材料泄漏。

评审先回答 `questions`，按原有推理和成文标准检查实质错误，再比较表达；有严重事实、因果或范围错误的候选不能只因更短而胜出。两者都存在严重错误时选 `neither`，各有优劣且无足够差异时可选 `tie`。逐字相似度不参与评审。

保存 `judgments/<review_id>.json`：

```json
{
  "packet_sha256": "本次 review 文件的 SHA256",
  "saw_mapping": false,
  "verdict": "A",
  "reason": "基于实际输出的比较理由，包含严重错误检查",
  "answers": ["逐一回答该案例的理解问题"],
  "evidence": {"A": "A 中实际出现的短引文", "B": "B 中实际出现的短引文"},
  "metadata": {
    "actor": "实际独立评审者", "model": "实际模型或 human",
    "settings": {}, "origin": "external", "isolation": "fresh",
    "context_id": "不同于生成上下文的真实标识", "run_id": "真实评审记录标识"
  }
}
```

然后运行：

```bash
python3 scripts/compare_skill_outputs.py report /tmp/fp-comparison/tool-heading
```

缺少输出或评审时报告待完成；自查、测试数据、共享上下文、已见映射或模型设置不一致时，不标成独立受控对照。输入、输出、元数据或评审材料在盲化后改变会被拒绝。修复后需要建立新运行，保留旧失败记录，不能只留下成功样本。

`declared_independent_comparison_complete` 只表示文件齐全且操作者报告了独立条件。脚本无法证明供应商实际隔离了上下文，也无法自动判断语义评分正确。报告只汇总这些样本的偏好，不给出未测的阅读时间、成功率或稳定提升幅度。

## Web GPT 的使用路径

日常仍然让 Web GPT 读取仓库的 `SKILL.md` 及对应运行材料即可，不要求 Python、API 或独立评审。

迭代时，有 GitHub 读取和文件执行工具的 Web GPT 可以按两个固定提交读取文件，导出上面的规则包，运行准备、盲化和汇总脚本。没有本地 Git 不影响按提交读取；没有脚本执行工具时，可按相同文件格式人工组织，但应记录哪些检查未运行。

实际生成与独立评审由宿主能力决定。有支持隔离上下文的模型或子 Agent 工具时，使用真实独立调用；没有时，可由操作者在不同干净对话中分别运行。会自动带入项目历史、记忆或父对话的环境，要先确认实际隔离；不能确认就记录 `unknown`。不得把同一对话内的角色切换当作替代，也不能因为 Skill 写了指令就宣称已获得新的工具权限。

如果本轮没有独立调用能力，仍可提交规则修复、案例和脚本，但必须明确写“真实独立生成与盲评未执行”，并保留待验证项。不要把评测准备完成写成文章质量已经稳定改善。
