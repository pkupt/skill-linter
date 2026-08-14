"""R1 — Routing defects: the description is the routing engine, and most
skills get routing wrong. A skill that can't be discovered doesn't exist.

Backed by arXiv 2608.08453: routing defects (missing/short/non-functional
descriptions, name/folder mismatch) are the most common and most harmful —
a routing-stress test shows R1-clean skills are retrieved far more reliably.
"""

from __future__ import annotations

import os
import re
from typing import List

from .base import (
    NAME_RE,
    TRIGGER_WORDS,
    Finding,
    SkillContext,
    TIER_SPEC,
)

# floor for a description that can carry a trigger; 40 chars ≈ one short clause
MIN_DESCRIPTION_CHARS = 40
MAX_NAME_LEN = 64


def r1_name_missing(ctx: SkillContext) -> List[Finding]:
    if not ctx.name:
        return [Finding("r1-name-missing", TIER_SPEC, "error",
                        "frontmatter `name` is required (lowercase letters, digits, hyphens, ≤64 chars)",
                        fix_hint="add `name: my-skill` to the YAML frontmatter")]
    return []


def r1_name_invalid(ctx: SkillContext) -> List[Finding]:
    if not ctx.name:
        return []
    if not NAME_RE.match(ctx.name):
        return [Finding("r1-name-invalid", TIER_SPEC, "error",
                        f"`name` must be lowercase letters/digits/hyphens; got {ctx.name!r}",
                        fix_hint="rename to a clean lowercase-hyphen form, e.g. 'my-skill'")]
    if len(ctx.name) > MAX_NAME_LEN:
        return [Finding("r1-name-invalid", TIER_SPEC, "error",
                        f"`name` exceeds {MAX_NAME_LEN} chars")]
    return []


def r1_name_folder_mismatch(ctx: SkillContext) -> List[Finding]:
    """The spec requires name to match the folder name (sanitized)."""
    if not ctx.name:
        return []
    folder = os.path.basename(ctx.skill_dir.rstrip("/\\"))
    if folder and folder != ctx.name:
        return [Finding(
            "r1-name-folder-mismatch", TIER_SPEC, "warning",
            f"`name` ({ctx.name!r}) does not match folder name ({folder!r}); "
            "installers sanitize names and this can surprise teammates",
            fix_hint=f"rename folder to '{ctx.name}' or set name: '{folder}'")]
    return []


def r1_description_missing(ctx: SkillContext) -> List[Finding]:
    if not ctx.description or not ctx.description.strip():
        return [Finding("r1-description-missing", TIER_SPEC, "error",
                        "`description` is required — it is the ONLY thing the agent "
                        "sees before deciding to load this skill",
                        fix_hint="add `description: <what it does> + <when to use it>`")]
    return []


def r1_description_too_short(ctx: SkillContext) -> List[Finding]:
    if ctx.description and 0 < len(ctx.description.strip()) < MIN_DESCRIPTION_CHARS:
        return [Finding("r1-description-too-short", TIER_SPEC, "warning",
                        f"description is only {len(ctx.description.strip())} chars "
                        f"(< {MIN_DESCRIPTION_CHARS}) — too short to carry trigger context",
                        fix_hint="include what it does AND when to use it (trigger phrases)")]
    return []


def r1_description_no_trigger(ctx: SkillContext) -> List[Finding]:
    """R1.6 routing misplacement: description without trigger language means
    the skill is rarely (or wrongly) retrieved."""
    if not ctx.description:
        return []
    d = ctx.description.lower()
    if not any(w in d for w in TRIGGER_WORDS):
        return [Finding("r1-description-no-trigger", TIER_SPEC, "warning",
                        "description has no trigger language — the agent can't tell "
                        "WHEN to use this skill",
                        fix_hint="add 'Use when …' / trigger scenarios to the description")]
    return []


ALL_R1_RULES = [
    r1_name_missing,
    r1_name_invalid,
    r1_name_folder_mismatch,
    r1_description_missing,
    r1_description_too_short,
    r1_description_no_trigger,
]
