# Recommended Claude Code Plugins

## Science-Superpowers

Computational-science methodology skills: research framing, prior-work survey, analysis design,
pre-registration, reproducible setup, anomaly investigation, and red-team review.

**Install (inside Claude Code):**
```
/plugin marketplace add K-Dense-AI/science-superpowers
/plugin install science-superpowers@science-superpowers-dev
```

No restart needed. Skills are immediately available.

**Key skills:**
- `framing-research-questions` — turn a fuzzy idea into a sharp, testable question before touching data
- `surveying-prior-work` — check whether the literature already answers it
- `designing-the-analysis` — concrete analysis plan before fitting any model
- `preregistering-analysis` — lock predictions and decision rules before seeing outcomes
- `investigating-anomalous-results` — hypothesis-driven debugging of surprising/failed results
- `requesting-red-team-review` — adversarial review before committing compute

## Agent Deck

Run multiple Claude Code sessions in parallel. Essential for:
- Installing packages on multiple clusters simultaneously
- Running experiments while doing other work
- Managing long-running jobs in background sessions

**Install (from terminal):**
```bash
curl -fsSL https://raw.githubusercontent.com/asheshgoplani/agent-deck/main/install.sh | bash
```

Or use the helper script (also creates a session):
```bash
bash tools/setup-agent-deck.sh
```

**Start Agent Deck:**
```bash
agent-deck
```

This opens a session manager. Create sessions, each runs its own Claude Code instance.

**Essential keybindings:**
- `Ctrl+Q` — back to main window (session keeps running)
- `q` / `Ctrl+C` — exit Agent Deck to terminal
- `Enter` / arrow keys — select and enter a session
- `n` — create new session
- `?` — show all keybindings

**Note:** Exit your current Claude Code session first, then launch `agent-deck` which manages Claude sessions for you.

Full docs: https://github.com/asheshgoplani/agent-deck
