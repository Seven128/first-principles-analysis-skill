# First Principles Analysis Skill

一个用于生成和迭代第一性原理分析文章的独立 Skill。

它有两种用途：

1. **直接分析**：把用户的主题、目标、已有结论或材料转换成明确问题，按严密因果链生成分析文章。
2. **迭代回归**：修改分析逻辑或提示词时，使用既有分析样例和结构性不变量检查是否发生退化。

## 核心原则

```text
确定问题与最终目的
→ 选择正确时间基线
→ 分析状态转变所需条件
→ 找到基线与必要条件之间的缺口
→ 形成根问题
→ 逐项正向推出方案与机制
→ 验证是否达到最终目的
```

其中：

- 目标求解型问题使用当下基线。
- 原理还原型问题使用对象尚未形成时的形成前基线。
- “现状与要解决的问题”只承载事实、条件、缺口和根问题。
- 具体方案与实现机制必须在后文由问题逐项正向推出。
- 内部推演脚手架不应泄漏到面向读者的正文。

## 安装

仓库根目录本身就是一个 Skill 目录，包含必需的 `SKILL.md` 和可选的 `references/`、`scripts/`、`agents/`。

可克隆到用户级 Skill 目录：

```bash
git clone https://github.com/Seven128/first-principles-analysis-skill.git \
  "$HOME/.agents/skills/first-principles-analysis"
```

也可以把仓库目录软链接到 `$HOME/.agents/skills/first-principles-analysis`，便于持续迭代。

## 使用

### 直接生成文章

```text
$first-principles-analysis
请从第一性原理分析：我怎样才能找到前端开发工程师的工作？
```

```text
$first-principles-analysis
我知道 Agent 大致是基于大模型的任务执行应用，但不知道为什么会有 Agent、为什么形成当前这种形态。请写一篇原理文章。
```

### 迭代 Skill

```text
$first-principles-analysis
这次输出把详细方案写进了“现状与要解决的问题”。请定位规则失效原因，修改 Skill，并运行相关回归。
```

## 权威关系

```text
用户任务契约与事实材料
└── 决定本次分析的目标、范围与事实边界

references/第一性原理分析逻辑.md
└── 分析方法最高权威

references/第一性原理分析提示词.md
└── 对分析逻辑的可执行展开

references/回归样例/
└── 结构、行文和退化检查样例，不是普遍事实库

references/经验/
└── 可复用候选论据，使用前必须重新验证适用范围
```

提示词中的任何细节都不能覆盖或打乱《第一性原理分析逻辑》。样例与经验不能替代当前命题的事实证据。

## 仓库结构

```text
.
├── SKILL.md
├── AGENTS.md
├── agents/
│   └── openai.yaml
├── references/
│   ├── 第一性原理分析逻辑.md
│   ├── 第一性原理分析提示词.md
│   ├── source-manifest.json
│   ├── 经验/
│   └── 回归样例/
├── evals/
│   ├── README.md
│   └── regression-cases.json
└── scripts/
    └── validate_skill.py
```

## 回归原则

回归不是比较逐字输出，而是检查以下结构性能力是否保持：

- 能否找对分析问题和问题类型；
- 能否选择正确时间基线；
- 最终目的是否简短；
- 现状部分是否停留在条件、缺口和根问题层；
- 是否逐项正向推出机制；
- 是否保持主体与抽象层级一致；
- 是否只在必要时讨论版本差异；
- 是否删除对读者无价值的内部脚手架；
- 事实、推断和待验证项是否分开。

详见 [`evals/README.md`](evals/README.md)。

## 校验

```bash
python3 scripts/validate_skill.py
```

校验会检查 Skill 元数据、必需文件、来源文件哈希和回归清单引用。
