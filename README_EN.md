# skill-linter

> **The eslint for Agent Skills.** Lint `SKILL.md` files for spec compliance, quality and security — before you publish them to an ecosystem where most skills are broken.

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![Tests](https://img.shields.io/badge/tests-20%2F20%20passing-brightgreen)](#running-tests)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](#)

Agent skills are the new npm — and like early npm, most of what gets published is broken. An ecosystem-scale study of **138,133 public SKILL.md files** found **89.3% violate the official specification** and **91.8% contain at least one defect** ([arXiv:2608.08453](https://arxiv.org/abs/2608.08453)). The most common defects are also the most harmful: **routing defects** — a skill whose `description` can't be discovered by the agent might as well not exist.

`skill-lint` turns that research into a runnable tool. It's a **pure, deterministic checker**: no model calls, sub-second feedback, CI-friendly.

[中文版 / Chinese version](./README.md)

## Contents

- [Why](#why)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [Options](#options)
- [Rules](#rules)
- [Exit codes & CI](#exit-codes--ci)
- [Development](#development)
- [Roadmap](#roadmap)
- [Background & sources](#background--sources)
- [License](#license)

## Why

| Without `skill-lint` | With `skill-lint` |
|---|---|
| Ship a skill, agents never trigger it (bad `description`) | Catch routing defects before publish |
| Hardcoded API keys leak into a public pack | Flag secrets, dangerous commands, safety bypasses |
| "It works on my machine" quality drift | Deterministic, shareable quality gate |
| Manual review doesn't scale to 138K skills | One command, runs in CI on every change |

## Features

- **Spec-aware** — mirrors the official [agentskills.io](https://agentskills.io) specification.
- **Two-tier severity** — `spec` (violates the spec) vs `best-practice` (peer guidance), so you can gate CI on what actually matters.
- **Security rules** — catches hardcoded secrets, dangerous commands, and permission/safety bypasses.
- **Actionable findings** — every finding carries a `fix_hint` telling you *what* to change, not just *that* something is wrong.
- **Zero model calls** — pure static analysis; instant, deterministic, cheap to run anywhere.
- **CI-ready** — JSON or human output, with an exit code you can fail a build on.

## Installation

`skill-linter` is not yet on PyPI; install from source:

```bash
# clone, then:
pip install -e .

# or install directly from GitHub
pip install git+https://github.com/pkupt/skill-linter.git
```

> PyPI publish (`pip install skill-linter`) is on the roadmap.

Requires **Python 3.9+** and `pyyaml`.

## Usage

```bash
skill-lint .                       # lint the current directory (recursive)
skill-lint my-skill                # lint a single skill folder
skill-lint . --format json        # machine-readable output
skill-lint . --fail-on warning    # fail the run on warnings too
skill-lint --version              # 0.1.0
```

### Example output

```text
$ skill-lint my-skill
my-skill/SKILL.md
  [error]   r1-name-invalid: `name` must be lowercase letters/digits/hyphens; got 'My Demo Skill'
  [error]   r5-hardcoded-secrets: possible hardcoded secret found
  [warning] r1-description-no-trigger: description has no trigger language

=== 1 skill(s), 2 error(s), 9 finding(s) ===   # exit code 1 -> CI fails
```

### JSON output

```bash
skill-lint my-skill --format json
```

```json
[
  {
    "path": "my-skill/SKILL.md",
    "findings": [
      {
        "rule": "r1-name-invalid",
        "tier": "spec",
        "severity": "error",
        "message": "name must be lowercase letters/digits/hyphens; got 'My Demo Skill'",
        "fix_hint": "rename to lowercase-hyphenated, e.g. 'my-skill'"
      }
    ]
  }
]
```

## Options

| flag | values | default | meaning |
|---|---|---|---|
| `path` | directory / file | `.` | what to lint (recursive for directories) |
| `--format` | `text`, `json` | `text` | output format |
| `--fail-on` | `error`, `warning`, `info` | `error` | minimum severity that fails the run (sets exit code) |
| `--version` | - | - | print version and exit |

## Rules

Rules mirror the paper's two-tier taxonomy. **Tier `spec`** = violates the official agentskills.io specification; **tier `best-practice`** = peer-reviewed / industry guidance.

### R1 - Routing (the discovery killer)

| rule | tier | fires when |
|---|---|---|
| `r1-name-missing` | spec | no `name` in frontmatter |
| `r1-name-invalid` | spec | name not lowercase/digits/hyphens, or > 64 chars |
| `r1-name-folder-mismatch` | spec | name != folder name (installers sanitize - surprises teammates) |
| `r1-description-missing` | spec | no `description` (the ONLY routing signal) |
| `r1-description-too-short` | spec | < 40 chars, can't carry trigger context |
| `r1-description-no-trigger` | spec | no trigger language ("Use when...") - agent can't tell WHEN |

### R2 - Body

| rule | tier | fires when |
|---|---|---|
| `r2-body-too-long` | spec | body > 500 lines (adherence drops, loads slow) |
| `r2-body-non-actionable` | best-practice | vague wording the agent can't verify ("validate properly", "best") |
| `r2-name-as-heading` | best-practice | body re-heads the skill name |
| `r2-description-duplicated` | best-practice | description copy-pasted into body |

### R5 - Security (install-then-trust is not sustainable)

| rule | tier | fires when |
|---|---|---|
| `r5-hardcoded-secrets` | best-practice | API keys / tokens / credentials in the skill |
| `r5-dangerous-commands` | best-practice | `rm -rf`, `mkfs`, `:(){:|:&};:` and friends |
| `r5-safety-bypass` | best-practice | `--no-verify`, `--force`, `bypassPermissions` |
| `r5-suppress-errors` | best-practice | `2>/dev/null` hides failures the agent should react to |

Every finding is actionable: each carries a `fix_hint` telling the author **what** to change.

## Exit codes & CI

Exit codes: `0` clean - `1` findings at/above the `--fail-on` level (default `error`).

```yaml
# .github/workflows/lint.yml
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
  with:
    python-version: "3.11"
- run: pip install git+https://github.com/pkupt/skill-linter.git
- run: skill-lint . --fail-on error
```

Use `--format json` to post findings into your own review pipeline or dashboard.

## Development

### Setup

```bash
git clone https://github.com/pkupt/skill-linter.git
cd skill-linter
pip install -e ".[dev]"
```

### Running tests

```bash
pytest
```

> If you hit an `iniconfig`/pytest conflict from a mixed Python environment, run tests inside a clean virtualenv (`python -m venv .venv && .venv/Scripts/activate && pip install -e ".[dev]" && pytest`).

### Adding a rule

1. Subclass `Rule` in `skill_linter/rules/base.py` and implement `check(context) -> List[Finding]`.
2. Drop the class into the relevant module (`routing.py`, `body.py`, `security.py`).
3. Register it in `skill_linter/rules/__init__.py` (the `run_all` collection).
4. Add a positive and a negative fixture in `tests/test_rules.py`.

Finding fields: `rule`, `tier` (`spec` | `best-practice`), `severity` (`error` | `warning` | `info`), `message`, `fix_hint`.

## Roadmap

- [x] **v0.1** - rule engine + R1/R2/R5 (14 checks), JSON/text output, CI exit codes
- [ ] publish to PyPI (`pip install skill-linter`)
- [ ] `--fix` auto-repair (fill frontmatter, split `references/`)
- [ ] routing stress-test mode (BM25 lower-bound probe: do clean skills actually get retrieved?)
- [ ] plugin rules, GitHub Action, VS Code extension
- [ ] quality signals (eval pass rate, adoption) for skill marketplaces

## Background & sources

- **What Keeps Agent Skills from Being Reusable? Evidence from 138K SKILL.md Files** - arXiv:[2608.08453](https://arxiv.org/abs/2608.08453) (First Workshop on Agent Skills, 2026-05-26): two-tier defect taxonomy (7 categories, 31 checks), the routing stress test, and 12 evidence-based authoring guidelines.
- [agentskills.io](https://agentskills.io) - the open Agent Skills specification (Anthropic -> open standard, 2025-12).
- [ClawHavoc, 2026-02](https://digitalapplied.com/blog/agent-skill-packs-package-ecosystem-supply-chain-risk) - 2,419 malicious skills pulled from ClawHub: why security rules matter.

## License

[MIT](./LICENSE)

---

Maintainer: pkupt · Initiated: 2026-08-14 · [中文](./README.md)
