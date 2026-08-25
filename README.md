# skill-linter

> **The eslint of Agent Skills.** Before publishing `SKILL.md` to the skills ecosystem, check its spec compliance, quality, and security—because most skills today are broken.

[![Python](https://img.shields.io/badge/python-3.9%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green)](./LICENSE)
[![Tests](https://img.shields.io/badge/tests-20%2F20%20passing-brightgreen)](#运行测试)
[![Version](https://img.shields.io/badge/version-0.1.0-blue)](#)

[Agent Skills](https://agentskills.io) is the new npm—and like early npm, most published skills are broken. An ecosystem-scale study (covering **138,133 public SKILL.md files**) found: **89.3% violate the official spec**, **91.8% have at least one defect** ([arXiv:2608.08453](https://arxiv.org/abs/2608.08453)). The most common and most fatal defect is **routing**—a skill whose `description` cannot be discovered by an agent is effectively nonexistent.

`skill-lint` turns this research into a runnable tool. It is a **purely static, deterministic checker**: no model calls, sub-second feedback, CI-friendly.

[English version / 英文版](./README_EN.md)

## 目录

- [为什么需要](#为什么需要)
- [功能特性](#功能特性)
- [安装](#安装)
- [使用](#使用)
- [参数](#参数)
- [规则](#规则)
- [退出码与 CI](#退出码与-ci)
- [开发](#开发)
- [路线图](#路线图)
- [背景与来源](#背景与来源)
- [许可证](#许可证)

## 为什么需要

| 没有 `skill-lint` | 用了 `skill-lint` |
|---|---|
| 发布一个技能，智能体从来不触发它（`description` 写错） | 在发布前抓出路由缺陷 |
| 硬编码的 API key 泄露进公开包 | 标出密钥、危险命令、安全绕过 |
| "在我机器上能用"的质量漂移 | 确定性的、可共享的质量闸门 |
| 人工审查根本扩不到 13.8 万个技能 | 一条命令，每次变更都在 CI 里跑 |

## 功能特性

- **懂规范**——对齐官方 [agentskills.io](https://agentskills.io) 规范。
- **两级严重度**——`spec`（违反规范）对比 `best-practice`（同行建议），所以你能只把真正重要的挡在 CI 门外。
- **安全规则**——抓硬编码密钥、危险命令、以及权限/安全绕过。
- **可执行的检查结果**——每条 finding 都带一个 `fix_hint`，告诉你*改什么*，而不只是*哪里错了*。
- **零模型调用**——纯静态分析；即时、确定性、哪里都能廉价跑。
- **CI 友好**——JSON 或人读输出，带一个能让你构建失败退出的退出码。

## 安装

`skill-linter` 还没上 PyPI，从源码安装：

```bash
# 先 clone，然后：
pip install -e .

# 或直接装 GitHub 上的版本
pip install git+https://github.com/pkupt/skill-linter.git
```

> 上 PyPI（`pip install skill-linter`）在路线图上。

需要 **Python 3.9+** 和 `pyyaml`。

## 使用

```bash
skill-lint .                       # 检查当前目录（递归）
skill-lint my-skill                # 检查单个技能文件夹
skill-lint . --format json        # 机器可读输出
skill-lint . --fail-on warning    # 连 warning 也视为失败
skill-lint --version              # 0.1.0
```

### 输出示例

```text
$ skill-lint my-skill
my-skill/SKILL.md
  [error]   r1-name-invalid: `name` 必须是小写字母/数字/连字符；实际是 'My Demo Skill'
  [error]   r5-hardcoded-secrets: 发现疑似硬编码密钥
  [warning] r1-description-no-trigger: description 里没有触发词

=== 1 skill(s), 2 error(s), 9 finding(s) ===   # 退出码 1 -> CI 失败
```

### JSON 输出

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

## 参数

| 参数 | 取值 | 默认 | 含义 |
|---|---|---|---|
| `path` | 目录 / 文件 | `.` | 要检查的对象（目录则递归） |
| `--format` | `text`, `json` | `text` | 输出格式 |
| `--fail-on` | `error`, `warning`, `info` | `error` | 触发失败（设置退出码）的最低严重度 |
| `--version` | - | - | 打印版本并退出 |

## 规则

规则对应论文的两级分类法。**Tier `spec`** = 违反官方 agentskills.io 规范；**tier `best-practice`** = 同行评审 / 行业建议。

### R1 - 路由（发现的杀手）

| 规则 | tier | 触发条件 |
|---|---|---|
| `r1-name-missing` | spec | frontmatter 里没有 `name` |
| `r1-name-invalid` | spec | name 不是小写/数字/连字符，或长度 > 64 |
| `r1-name-folder-mismatch` | spec | name != 文件夹名（安装器会改，坑队友） |
| `r1-description-missing` | spec | 没有 `description`（这是唯一的路由信号） |
| `r1-description-too-short` | spec | < 40 字符，承载不了触发上下文 |
| `r1-description-no-trigger` | spec | 没有触发词（"Use when..."），智能体不知道*何时*用 |

### R2 - 正文

| 规则 | tier | 触发条件 |
|---|---|---|
| `r2-body-too-long` | spec | 正文 > 500 行（遵循度下降、加载慢） |
| `r2-body-non-actionable` | best-practice | 智能体无法验证的模糊措辞（"validate properly"、"best"） |
| `r2-name-as-heading` | best-practice | 正文把技能名又当标题写了一遍 |
| `r2-description-duplicated` | best-practice | description 被原样复制进正文 |

### R5 - 安全（装完就信任是不可持续的）

| 规则 | tier | 触发条件 |
|---|---|---|
| `r5-hardcoded-secrets` | best-practice | 技能里出现 API key / token / 凭据 |
| `r5-dangerous-commands` | best-practice | `rm -rf`、`mkfs`、`:(){:|:&};:` 这类命令 |
| `r5-safety-bypass` | best-practice | `--no-verify`、`--force`、`bypassPermissions` |
| `r5-suppress-errors` | best-practice | `2>/dev/null` 把本该反应的失败藏起来 |

每条 finding 都是可执行的：每条都带一个 `fix_hint` 告诉作者**改什么**。

## 退出码与 CI

退出码：`0` 干净 - `1` 出现达到/高于 `--fail-on` 级别（默认 `error`）的 finding。

```yaml
# .github/workflows/lint.yml
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
  with:
    python-version: "3.11"
- run: pip install git+https://github.com/pkupt/skill-linter.git
- run: skill-lint . --fail-on error
```

用 `--format json` 把 finding 接入你自己的审查流水线或看板。

## 开发

### 环境搭建

```bash
git clone https://github.com/pkupt/skill-linter.git
cd skill-linter
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

> 如果你的 Python 环境混了多个版本、遇到 `iniconfig`/pytest 冲突，在一个干净的虚拟环境里跑测试（`python -m venv .venv && .venv/Scripts/activate && pip install -e ".[dev]" && pytest`）。

### 新增一条规则

1. 在 `skill_linter/rules/base.py` 里继承 `Rule`，实现 `check(context) -> List[Finding]`。
2. 把类放进对应模块（`routing.py`、`body.py`、`security.py`）。
3. 在 `skill_linter/rules/__init__.py` 里注册（加进 `run_all` 的集合）。
4. 在 `tests/test_rules.py` 里加一个正向 fixture 和一个负向 fixture。

Finding 字段：`rule`、`tier`（`spec` | `best-practice`）、`severity`（`error` | `warning` | `info`）、`message`、`fix_hint`。

## 路线图

- [x] **v0.1** - 规则引擎 + R1/R2/R5（14 个检查）、JSON/text 输出、CI 退出码
- [ ] 上 PyPI（`pip install skill-linter`）
- [ ] `--fix` 自动修复（补 frontmatter、拆分 `references/`）
- [ ] 路由压力测试模式（BM25 下界探针：干净的技能真的能被检索到吗？）
- [ ] 插件化规则、GitHub Action、VS Code 扩展
- [ ] 面向技能市场的质量信号（eval 通过率、采用度）

## 背景与来源

- **What Keeps Agent Skills from Being Reusable? Evidence from 138K SKILL.md Files** - arXiv:[2608.08453](https://arxiv.org/abs/2608.08453)（Agent Skills 首届研讨会，2026-05-26）：两级缺陷分类法（7 类、31 项检查）、路由压力测试、以及 12 条有证据支撑的写作指南。
- [agentskills.io](https://agentskills.io) - 开放的 Agent Skills 规范（Anthropic → 开放标准，2025-12）。
- [ClawHavoc, 2026-02](https://digitalapplied.com/blog/agent-skill-packs-package-ecosystem-supply-chain-risk) - 从 ClawHub 扒出的 2,419 个恶意技能：为什么安全规则重要。

## 许可证

[MIT](./LICENSE)

---

主理人：pkupt · 项目启动：2026-08-14 · [English](./README_EN.md)
