# Tool Decision Guide

<context>When to use Science-Superpowers vs SC Commands vs Agent-Deck vs Experiment Pipeline.</context>

## Rule of Thumb

| System | Role | Think of it as... |
|--------|------|-------------------|
| **Science-Superpowers** | Research/methodology skills | HOW you approach a task |
| **SC commands** | Execution skills | Tools to DO specific things |
| **Agent-deck** | Orchestration | Managing multiple agents/sessions |

<rule>When both could apply: Science-Superpowers first (sets the process), then SC tools within that process.</rule>

## Decision Tree

| Task | Use | Why |
|------|-----|-----|
| Framing a research question | Science-Superpowers `framing-research-questions` | Sharpen the question before any data |
| Checking prior work | Science-Superpowers `surveying-prior-work` | Maybe the literature already answers it |
| Planning the analysis | Science-Superpowers `designing-the-analysis` | Concrete plan before fitting any model |
| Locking a hypothesis | Science-Superpowers `preregistering-analysis` | Fix predictions + decision rules before seeing outcomes |
| Reproducible workspace | Science-Superpowers `setting-up-reproducible-analysis` | Pinned env, fixed seeds, immutable raw data |
| Executing the analysis | Science-Superpowers `executing-analysis` | Step-by-step with review checkpoints |
| Writing code (in workflow) | `sc:implement` | Targeted coding tool |
| Running tests (one-off) | `sc:test` | Quick execution |
| Investigating a surprising/failed result | Science-Superpowers `investigating-anomalous-results` | Hypothesis-driven, before adjusting anything |
| Verifying before you claim it | Science-Superpowers `verifying-results-before-claiming` | Run fresh, read the output, evidence before claims |
| Peer / adversarial review | Science-Superpowers `requesting-red-team-review` / `receiving-critical-review` | Structured process |
| Reporting & archiving | Science-Superpowers `reporting-and-archiving-findings` | Reproducible write-up |
| Code analysis | `sc:analyze` | Comprehensive |
| Documentation | `sc:document` | Direct generation |
| Git operations | `sc:git` | Commit, branch, PR |
| Web research | `sc:research` | Search and synthesis |
| Agent management | Agent-deck CLI | Never Science-Superpowers/SC |
| Parallel tasks | Agent-deck (spawn) | Cross-agent orchestration |

<critical name="anti-patterns">
- Don't double-invoke `sc:brainstorm` AND Science-Superpowers `framing-research-questions` — pick Science-Superpowers
- Don't use `sc:troubleshoot` when Science-Superpowers `investigating-anomalous-results` exists
- Don't spawn agent-deck sessions for simple single-agent tasks
- Don't use Science-Superpowers for one-shot actions (tests, docs) — SC is faster
- Don't use SC/Science-Superpowers for orchestration — agent-deck only
</critical>

## Common Workflows

<reference>
**New analysis:** framing-research-questions → surveying-prior-work → designing-the-analysis → preregistering-analysis → executing-analysis (with sc:implement) → verifying-results-before-claiming → requesting-red-team-review → reporting-and-archiving-findings

**Anomalous result:** investigating-anomalous-results → sc:implement → sc:test

**Experiment pipeline:** Design → Red Team Brief → /experiment-preflight → /experiment-pipeline → /harvest-and-report → handoff → review

**Key:** Don't wait for user to invoke commands. `experiments.md` tells you when to trigger each phase. The Science-Superpowers process skills map directly onto the pipeline — `framing-research-questions`/`surveying-prior-work` ↔ DESIGN, `preregistering-analysis`/`requesting-red-team-review` ↔ REDTEAM, `verifying-results-before-claiming` ↔ VALIDATE, `reporting-and-archiving-findings` ↔ REVIEW.
</reference>
