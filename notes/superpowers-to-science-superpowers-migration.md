# 迁移计划：用 science-superpowers 替换 obra/superpowers
把 RACA 包里对 **Superpowers**（`obra/superpowers`，经 `superpowers@claude-plugins-official` 安装）的引用， 替换为 **Science-Superpowers**（`K-Dense-AI/science-superpowers`，插件名 `science-superpowers@science-superpowers-dev`）。

* * *
## 现状结论（已核查）
| 项目 | 状态 |
|---|---|
| `science-superpowers@science-superpowers-dev` | **已安装（user scope）且已启用**，本会话已生效（SessionStart 引导词就来自它） |
| `superpowers@claude-plugins-official` | 仅为**另一个项目**（`cancer_summer_school_papers`）的 project-scope 安装；在 RACA 里**未启用** |
| `superpowers@claude-plugins-official` 的真实来源 | `marketplace.json` 指向 `https://github.com/obra/superpowers.git`（pinned sha） |

**结论：插件运行层不需要改。** science-superpowers 已经是当前生效的那一个。 要改的只是 RACA 包**自己的文档与参考文件**——它们仍在向用户和 Claude 推荐、并在概念上依赖 `obra/superpowers`。

* * *
## 关键难点：两个包的技能集不同
不是简单的字符串替换。两套技能面向不同工作流：

| `obra/superpowers`（工程流） | `science-superpowers`（科研流） |
|---|---|
| `brainstorming` | `framing-research-questions` |
| `writing-plans` | `designing-the-analysis` |
| `executing-plans` | `executing-analysis` |
| `subagent-driven-development` | `subagent-driven-analysis` |
| `TDD`（先写测试再写实现） | `preregistering-analysis`（看数据前先锁定假设与判定规则） |
| `systematic-debugging` | `investigating-anomalous-results` |
| `requesting/receiving-code-review` | `requesting-red-team-review` / `receiving-critical-review` |
| —（无对应） | `surveying-prior-work`（查先前文献） |
| —（无对应） | `verifying-results-before-claiming`（下结论前先验证） |
| —（无对应） | `setting-up-reproducible-analysis`（可复现环境） |
| —（无对应） | `reporting-and-archiving-findings`（汇报与归档） |

科研流其实比工程流**更贴合** RACA 的实验流水线： `framing-research-questions` ↔ DESIGN、`surveying-prior-work` ↔ "查文献"、 `preregistering-analysis` + `requesting-red-team-review` ↔ `red_team_brief` / `/raca:experiment-preflight`、 `verifying-results-before-claiming` ↔ VALIDATE / `data-validator`、 `reporting-and-archiving-findings` ↔ REVIEW / HF 上传。

* * *
## 需要决策：替换深度（请在这里选）
{==**方案 A：完整概念重映射（推荐）**==}{>>这是我的推荐。请确认选 A 还是 B。<<}{id="c1" by="user" at="2026-06-09T17:09:28.794Z"}

不仅换安装命令，还把工作流引用按上表重映射到 science-superpowers 真实存在的技能名。

- 优点：引用全部可用、与 RACA 科研定位一致、流水线衔接更顺。
  
- 代价：`tool-decision-guide.md` 的技能表需要重写（非机械替换）。
  

**方案 B：仅机械替换安装推荐（轻量）**

只把 6 个文件里的安装命令/链接从 `superpowers@claude-plugins-official` 换成 `science-superpowers@science-superpowers-dev`， 保留 `brainstorming` / `writing-plans` / `TDD` 等旧技能名。

- 风险：这些技能名在 science-superpowers **不存在**，会留下指向空技能的"悬空引用"，反而误导 Claude 和用户。**不推荐。**
  

> 下面的实施清单按**方案 A** 编写。若选 B，则只做第 1、2、4、6 项的"换命令/换链接"部分，跳过技能表重写。

* * *
## 实施清单（方案 A）
涉及 6 个文件，全部在 RACA 包内，无需改任何 `~/.claude` 运行时配置。
### 1. `README.md`（第 87 行）
- 把 `**[Superpowers](https://github.com/anthropics/claude-code-plugins)** — structured planning, proactive design questions`
  
- 改为指向 `https://github.com/K-Dense-AI/science-superpowers`，描述改为科研流（research framing / pre-registration / red-team review）。
  
### 2. `.claude/references/compute/plugins/recommended_plugins.md`（第 3–19 行）
- 标题 `## Superpowers` → `## Science-Superpowers`。
  
- 安装命令 `/plugin install superpowers@claude-plugins-official` → `/plugin install science-superpowers@science-superpowers-dev` （首次使用前需 `/plugin marketplace add K-Dense-AI/science-superpowers`，会在文档中补一行说明）。
  
- "Key skills" 列表替换为 science-superpowers 实际技能（framing-research-questions、designing-the-analysis、preregistering-analysis、investigating-anomalous-results、requesting-red-team-review …）。
  
### 3. `.claude/references/tool-decision-guide.md`（核心改动）
- 全文把 `Superpowers` 概念替换为 `Science-Superpowers`。
  
- 重写"Decision Tree"表与"Common Workflows"，按上面的映射表把任务对应到新技能名。
  
- 示例工作流改写为科研流： `framing-research-questions → surveying-prior-work → designing-the-analysis → preregistering-analysis → executing-analysis → verifying-results-before-claiming → reporting-and-archiving-findings`。
  
- 反模式（anti-patterns）一节同步更新技能名。
  
### 4. `.claude/commands/raca/experiment-tutorial.md`（第 53、59–63 行）
- Intro 推荐语 "Superpowers (research workflows)" → "Science-Superpowers (research methodology)"。
  
- 安装命令同第 2 项。
  
### 5. `.claude/skills/experiment-management/SKILL.md`（第 16、25、26 行）
- `superpowers:brainstorming` → `science-superpowers:framing-research-questions`。
  
- `docs/superpowers/specs/`（旧包默认产物路径）→ 改为 science-superpowers 的等价说法，或泛化为"设计技能的默认产物位置"。
  
- 第 26 行的 `writing-plans` → `designing-the-analysis`。
  
### 6. `docs/blog/RELEASE.md`（第 63、83 行）
- 叙事里的 `SuperPowers` / `Superpowers` → `Science-Superpowers`，链接指向 `K-Dense-AI/science-superpowers`。
  
- 第 83 行描述微调为科研流口吻（仍强调"让 Claude 在设计阶段更主动地提问"）。
  

* * *
## 不在范围内（除非你要求）
- **不**卸载 / 禁用 `superpowers@claude-plugins-official`：它属于另一个项目的 project-scope 安装，与 RACA 无关。 若你确认全局都不再用 obra/superpowers，可另行 `/plugin uninstall`，但本次不动。
  
- **不**改 `~/.claude/settings.json`、`installed_plugins.json` 等运行时文件：science-superpowers 已启用。
  
- **不**改任何实验数据 / 制品 / dashboard。
  

* * *
## 校验方式
实施后：

```bash
grep -rin "superpower" . | grep -v node_modules | grep -vi "science-superpower"
```

预期：仅剩"不在范围内"中刻意保留的内容（理想情况下为 0 行）。 再人工抽查 `tool-decision-guide.md` 的技能名是否都真实存在于 science-superpowers。

* * *
## 请你做的事
1. 在上面 {#c1} 处确认选 {==**方案 A**==}{>>选这个<<}{id="c2" by="user" at="2026-06-09T17:10:58.144Z"} 还是 **方案 B**。
  
2. 对任意条目有疑问/想改，直接在本文档里用批注或建议标出。
  
3. 点 "Done Reviewing" 后我按确认后的方案逐文件实施，并在每次写文件后做一次 `grep` 自检。
