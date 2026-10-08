# 推理一致性与入口整理：修改与验证记录

## 修改范围

本次以 `84ffe10d827073571a10e8d803dc457672eda082` 为基线；实际对照的规则提交为 `2d378f62e8a07fe75caf209dd04cadc6088a53ca`。后续提交只保存本记录、固定输入、原始输出和评审材料。

保留问题建模、目的适用性判断、解释与行动两条路线、主体指南、条件化结论卡、关键节点校验，以及长文的分析定稿和文章契约。入口仍保留原有 13 步，原 53 项输出检查与 43 项禁止事项的归属见 [coverage.md](coverage.md)。

### 修正局部命题与示例

- 单个成功案例不足以证明普遍规律；同范围真实反例对严格全称命题的作用，沿用既有节点规则。概率结论另按其命题类型判断。
- 收入、现金流与净收益分别判断，正净收益和实际到账要求只在对应目标下适用。
- 功能上的逻辑重建与历史动机判断分开；非目的对象的历史转折继续使用非目的解释链。
- 完成标准先用于判断差距，正文中的标准细节按相应方案与验证节点展开。
- “格式正确”的改写保留业务正确性与授权状态的未知，不据此增加已经实施的检查。Offer 条件化选择同时保留偏好与选项相对优势的前提。

### 统一入口和回归口径

重复细则回指既有规则文件，完整条件、例外与检查继续执行。写作示例与回归不再强制固定 Agent 比较分节、长父标题、段首粗体或内部长问题句。

短回答与长文交接的适用范围单独澄清：所有任务先完成分析并锁定已校验的语义结果；长文再形成交接定稿与文章契约。只读审查、仅运行回归、修改 Skill 的执行范围分别按用户请求确定。这些范围澄清不全部计作纯去重。

新增 5 个定向回归，覆盖真实反例、收入与净收益目标、无统一目的的演化、只读审查，以及保义改写。既有验证器保留相应必需案例，并检查写作密度文件对文章契约的引用及契约内的完整要求。

实际对照沿用 `scripts/compare_skill_outputs.py`。其运行文件白名单补入本来就属于运行材料的 `references/conclusions/`；新增两项测试，确认结论卡可用、路径不能越界到评审答案。

## 文本量

统计 UTF-8 解码后的字符数，包含空白、标点与路径。这里不把字符数当作 token、延迟或阅读效率。

| 范围 | 基线 | 修改后 | 变化 |
| --- | ---: | ---: | ---: |
| `SKILL.md` 字符 | 16,733 | 9,560 | −42.9% |
| `SKILL.md` 行数 | 678 | 248 | −63.4% |
| 单一解释路线的入口与必读核心，8 个文件 | 46,346 | 39,308 | −15.2% |
| 上述路线加长文规则，15 个文件 | 75,590 | 68,777 | −9.0% |

单一解释路线包括入口、核心 00、01、01a、02、04a、04、05；长文另加核心 06 与 6 份写作规则。没有计入按需主体指南、结论卡、用户材料与仓库维护指令。文件读取条件没有因此减少。

## 结构与脚本验证

[validation.json](validation.json) 保存实际命令、退出状态与原始输出。

- 9 项既有验证命令通过，含严格语言检查。
- 40 个单元测试通过。
- `git diff --check` 通过。
- 10 份原始来源的哈希保持一致，7 份主体指南未修改。
- 规则提交的 GitHub Actions `validate` 已通过：[执行记录](https://github.com/Seven128/first-principles-analysis-skill/actions/runs/37733436582/job/113167543243)。

这些检查验证结构、文件与评测流程，不自动判断模型回答的语义质量。

## 实际输出对照

[固定输入](cases.json) 包含 3 组任务：独立短问题、完整系统原理文章、两段短文字改写。每组两版各生成一次，共 6 份原始回答。题材使用受控假设事实；生成端只得到固定任务和该提交的完整运行材料，没有得到评审标准、旧输出、版本标签或审计诊断。

每份生成与每份评审分别调用 `collaboration.spawn_agent`，使用 `fork_turns="none"`，不指定模型覆盖。评审端只得到一份随机 A/B 对照材料、任务与评审条件，未提供版本映射。对应上下文标识、输入哈希、原始输出、逐项回答与引文均保存。

模型按宿主声明记录为继承的 GPT-6 Astra Pro；API 模型 ID、温度和推理档位未暴露，记录为 unknown。各调用没有显式覆盖设置；脚本中的“同模型和设置”表示这些记录一致，不构成供应商参数完全一致的独立证明。

| 固定任务 | 评审判定 | 主要检查结果 |
| --- | --- | --- |
| 独立短问题与证据边界 | 相当（tie） | 两版均正确处理全称反例、收入与净收益、功能重建和无目的形成。 |
| 完整系统原理文章 | 相当（tie） | 两版均保留目的、完成标准、差距与机制、恢复与去重，以及证据边界。 |
| 短段改写 | 相当（tie） | 两版均保留业务与授权未知，Offer 选择均有明确的比较条件。 |

3 组评审均未识别出实质优劣或本次样本中的语义退化。结果支持本次受控任务中的保义检查，不证明修改后具有稳定质量优势。

原始材料按案例保存在 [runs](runs/)。`comparison-summary.json` 汇总文件绑定检查与判定。上下文隔离依据实际工具调用与操作者记录，脚本只校验文件绑定、元数据和原文引文；它不能单独证明服务端隔离或语义判断一定正确。

这些是每组一次的小样本、同模型评审。它们可用于发现本次样本中的回归，不能据此推断稳定成功率、真实读者理解速度或生产使用效果。只读审查的实际工具执行行为没有单独进行模型端到端测试，其覆盖来自规则复核与新增回归定义；完整既有模型案例集也没有逐个重跑。

## 重建生成输入并复核记录

提交中保存输入模板、固定提交和哈希，避免重复存放多份完整运行规则。以下命令在包含上述两个提交的本仓库检出中，将实际生成任务包重建到临时目录，并校验其字节哈希及完整比较记录。它不重新调用模型，也不会改写已经记录的原始回答。

~~~bash
python3 - <<'PY'
import json
import shutil
import subprocess
import tempfile
from pathlib import Path
from scripts.compare_skill_outputs import digest, report

source = Path("evals/reasoning-consistency/runs")
target = Path(tempfile.mkdtemp(prefix="fp-reasoning-review-"))

def encoded(value):
    return (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf-8")

for item in sorted(source.iterdir()):
    if not item.is_dir():
        continue
    run = target / item.name
    shutil.copytree(item, run)
    manifest = json.loads((run / "private/manifest.json").read_text())
    template = json.loads((run / "generation-template.json").read_text())
    policies = {}
    for variant, revision in manifest["revisions"].items():
        files = {
            path: subprocess.check_output(
                ["git", "show", revision + ":" + path]
            ).decode("utf-8")
            for path in template["policy_paths"]
        }
        bundle = {"revision": revision, "files": files}
        assert digest(encoded(bundle)) == manifest["bundle_sha256"][variant]
        policies[variant] = files
    (run / "generation").mkdir()
    for job in manifest["jobs"]:
        packet = {
            "job_id": job["id"],
            "instruction": template["instruction"],
            "stage": template["stage"],
            "policy": policies[job["variant"]],
            "task": template["task"],
        }
        data = encoded(packet)
        assert digest(data) == job["packet_sha256"]
        (run / "generation" / (job["id"] + ".json")).write_bytes(data)
    result = report(run)
    assert result["declared_independent_comparison_complete"]
    print(item.name, json.dumps(result, ensure_ascii=False))

print("Reconstructed records:", target)
PY
~~~
