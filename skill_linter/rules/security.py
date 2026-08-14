"""R5 — Security defects: a skill can read the filesystem, call APIs and
operate git. 'Install-then-trust' is not sustainable (ClawHavoc took down
2,419 malicious skills). These checks flag the obvious danger patterns.
"""

from __future__ import annotations

from typing import List

from .base import (
    BYPASS_CMDS,
    DANGEROUS_CMDS,
    SECRET_PATTERNS,
    Finding,
    SkillContext,
    TIER_BEST_PRACTICE,
)


def r5_hardcoded_secrets(ctx: SkillContext) -> List[Finding]:
    text = ctx.body
    for pat in SECRET_PATTERNS:
        m = pat.search(text)
        if m:
            # don't echo the secret back into the report
            kind = "credential-looking value" if m.groups() else m.group(0)[:12] + "…"
            return [Finding("r5-hardcoded-secrets", TIER_BEST_PRACTICE, "error",
                            f"possible hardcoded secret found ({kind})",
                            fix_hint="reference secrets via environment variables, "
                                     "never hardcode them in SKILL.md")]
    return []


def r5_dangerous_commands(ctx: SkillContext) -> List[Finding]:
    hits = [c for c in DANGEROUS_CMDS if c in ctx.body]
    if hits:
        return [Finding("r5-dangerous-commands", TIER_BEST_PRACTICE, "warning",
                        f"destructive command(s) present: {', '.join(hits)}",
                        fix_hint="guard destructive actions behind explicit user "
                                 "confirmation; prefer reversible operations")]
    return []


def r5_safety_bypass(ctx: SkillContext) -> List[Finding]:
    hits = [c for c in BYPASS_CMDS if c in ctx.body]
    if hits:
        return [Finding("r5-safety-bypass", TIER_BEST_PRACTICE, "warning",
                        f"bypass/force flags present: {', '.join(hits)}",
                        fix_hint="removing safety checks inside a skill is a "
                                 "prompt-injection amplifier — avoid")]
    return []


def r5_suppress_errors(ctx: SkillContext) -> List[Finding]:
    """R5.5 suppress errors: hides failure, agents then 'succeed' confidently."""
    if "2>/dev/null" in ctx.body or "2>&1 >/dev/null" in ctx.body:
        return [Finding("r5-suppress-errors", TIER_BEST_PRACTICE, "warning",
                        "errors are suppressed (2>/dev/null) — failures become invisible",
                        fix_hint="let errors surface; the agent should see them as "
                                 "information and react")]
    return []


ALL_R5_RULES = [
    r5_hardcoded_secrets,
    r5_dangerous_commands,
    r5_safety_bypass,
    r5_suppress_errors,
]
