# Repository Instructions

本仓库是一个第一性原理分析 Skill，同时承载文章生成规则与回归基线。

修改前必须：

1. 读取 `references/第一性原理分析逻辑.md`；
2. 读取 `references/第一性原理分析提示词.md`；
3. 根据变更范围读取 `evals/regression-cases.json` 与相关样例。

约束：

- 《第一性原理分析逻辑》是方法最高权威；提示词只能细化，不能覆盖主干。
- 不为单个失败案例硬编码答案，应修复可泛化的根因。
- `references/回归样例/` 中的原始样例默认保持不变。
- `references/经验/` 中的内容是候选论据，不是无条件公理。
- 更新受来源清单管理的文件时，同步更新 `references/source-manifest.json` 的 SHA-256。
- 提交前运行 `python3 scripts/validate_skill.py`。
