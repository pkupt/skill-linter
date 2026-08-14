# skill-linter

> **The eslint for Agent Skills.** Lint `SKILL.md` files for spec compliance, quality and security.

Agent skills are the new npm — and like early npm, most of what's published is broken. An ecosystem-scale study of **138,133 public SKILL.md files** found **89.3% violate the official specification** and **91.8% contain at least one defect** (arXiv:2608.08453). The most common defects are also the most harmful: **routing defects** — a skill whose `description` can't be discovered by the agent might as well not exist.

`skill-lint` operationalizes that research into a runnable tool. It's a pure, deterministic checker: no model calls, instant feedback, CI-friendly.

## Quick start

```bash
pip install -e .          # or: pip install skill-linter
skill-lint .              # lint the current directory
skill-lint my-skill --format json
```

```text
$ skill-lint my-skill
my-skill/SKILL.md
  [error] r1-name-invalid: `name` must be lowercase letters/digits/hyphens; got 'My Demo Skill'
  [error] r5-hardcoded-secrets: possible hardcoded secret found
  [warning] r1-description-no-trigger: description has no trigger language
  ...
=== 1 skill(s), 2 error(s), 9 finding(s) ===   # exit code 1 → CI fails
```

## Rules

Rules mirror the paper's two-tier taxonomy. Tier **spec** = violates the official agentskills.io specification; tier **best-practice** = peer-reviewed / industry guidance.

### R1 — Routing (the discovery killer)
| rule | tier | fires when |
|---|---|---|
| `r1-name-missing` | spec | no `name` in frontmatter |
| `r1-name-invalid` | spec | name not lowercase/digits/hyphens, or >64 chars |
| `r1-name-folder-mismatch` | spec | name ≠ folder name (installers sanitize — surprises teammates) |
| `r1-description-missing` | spec | no `description` (the ONLY routing signal) |
| `r1-description-too-short` | spec | < 40 chars, can't carry trigger context |
| `r1-description-no-trigger` | spec | no trigger language ("Use when…") — agent can't tell WHEN |

### R2 — Body
| rule | tier | fires when |
|---|---|---|
| `r2-body-too-long` | spec | body > 500 lines (adherence drops, loads slow) |
| `r2-body-non-actionable` | best-practice | vague wording the agent can't verify ("validate properly", "最好") |
| `r2-name-as-heading` | best-practice | body re-heads the skill name |
| `r2-description-duplicated` | best-practice | description copy-pasted into body |

### R5 — Security (install-then-trust is not sustainable)
| rule | tier | fires when |
|---|---|---|
| `r5-hardcoded-secrets` | best-practice | API keys / tokens / credentials in the skill |
| `r5-dangerous-commands` | best-practice | `rm -rf`, `mkfs`, `:(){:|:&};:` and friends |
| `r5-safety-bypass` | best-practice | `--no-verify`, `--force`, `bypassPermissions` |
| `r5-suppress-errors` | best-practice | `2>/dev/null` hides failures the agent should react to |

Every finding is actionable: each carries a `fix_hint` telling the author **what** to change, not just that something is wrong.

## CI

```yaml
- run: pip install skill-linter
- run: skill-lint . --fail-on error
```

Exit codes: `0` clean · `1` findings at/above `--fail-on` level (default `error`). Use `--format json` to post findings to your own review pipeline.

## Roadmap

- [x] **v0.1** — rule engine + R1/R2/R5 (14 checks), JSON/text output, CI exit codes
- [ ] `--fix` auto-repair (fill frontmatter, split `references/`)
- [ ] routing stress-test mode (BM25 lower-bound probe: do clean skills actually get retrieved?)
- [ ] plugin rules, GitHub Action, VS Code extension
- [ ] quality signals (eval pass rate, adoption) for skill marketplaces

## Background & sources

- **What Keeps Agent Skills from Being Reusable? Evidence from 138K SKILL.md Files** — arXiv:2608.08453 (First Workshop on Agent Skills, 2026-05-26): two-tier defect taxonomy (7 categories, 31 checks), the routing stress test, and 12 evidence-based authoring guidelines.
- [agentskills.io](https://agentskills.io) — the open Agent Skills specification (Anthropic → open standard, 2025-12).
- [ClawHavoc, 2026-02](https://digitalapplied.com/blog/agent-skill-packs-package-ecosystem-supply-chain-risk) — 2,419 malicious skills pulled from ClawHub: why security rules matter.

## License

MIT
