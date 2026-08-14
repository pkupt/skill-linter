"""R2 — Body defects: instructions that are too long, non-actionable or
self-defeating. The delta principle: only write what the base model gets
wrong; every token of instruction competes with task reasoning.
"""

from __future__ import annotations

from typing import List

from .base import WEAK_PHRASES, Finding, SkillContext, TIER_BEST_PRACTICE, TIER_SPEC

MAX_BODY_LINES = 500


def r2_body_too_long(ctx: SkillContext) -> List[Finding]:
    n = len(ctx.body_lines)
    if n > MAX_BODY_LINES:
        return [Finding("r2-body-too-long", TIER_SPEC, "warning",
                        f"body is {n} lines (recommended ≤ {MAX_BODY_LINES}) — long "
                        "bodies reduce adherence and slow loading",
                        fix_hint="move detail into references/, keep the body a router")]
    return []


def r2_body_non_actionable(ctx: SkillContext) -> List[Finding]:
    """R2.2 non-actionable body: vague directives can't be verified by the
    agent, so it can't confirm whether it obeyed."""
    hits = [w for w in WEAK_PHRASES if w in ctx.body.lower()]
    if hits:
        return [Finding(
            "r2-body-non-actionable", TIER_BEST_PRACTICE, "warning",
            f"vague wording found: {', '.join(hits[:4])} — the agent can't verify "
            "whether it followed these instructions",
            fix_hint="replace vague guidance with explicit checks "
                     "(e.g. 'verify name is non-empty' instead of 'validate properly')")]
    return []


def r2_name_as_heading(ctx: SkillContext) -> List[Finding]:
    """R2.4 name as heading: wastes body space, the frontmatter already names it."""
    if ctx.name:
        for i, line in enumerate(ctx.body_lines[:5], start=1):
            if line.strip().lstrip("#").strip() == ctx.name:
                return [Finding("r2-name-as-heading", TIER_BEST_PRACTICE, "info",
                                f"body heading repeats the skill name (line {i})",
                                fix_hint="drop the redundant heading, start with '## When to Use'")]
    return []


def r2_description_duplicated(ctx: SkillContext) -> List[Finding]:
    """R2.5 description duplicated in body: red herring for routing."""
    if ctx.description:
        d = ctx.description.strip().lower()
        if len(d) > 20 and any(d[:30] in line.lower() for line in ctx.body_lines):
            return [Finding("r2-description-duplicated", TIER_BEST_PRACTICE, "info",
                            "description text duplicated in the body",
                            fix_hint="remove the copy; the description already lives "
                                     "in frontmatter for routing")]
    return []


ALL_R2_RULES = [
    r2_body_too_long,
    r2_body_non_actionable,
    r2_name_as_heading,
    r2_description_duplicated,
]
