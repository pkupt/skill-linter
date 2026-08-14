"""All built-in rules, aggregated for the runner."""

from __future__ import annotations

from typing import List

from .base import Finding, SkillContext
from .body import ALL_R2_RULES
from .routing import ALL_R1_RULES
from .security import ALL_R5_RULES

# order matters: routing first (most actionable), security always on
ALL_RULES = ALL_R1_RULES + ALL_R2_RULES + ALL_R5_RULES


def run_all(ctx: SkillContext) -> List[Finding]:
    findings: List[Finding] = []
    for rule in ALL_RULES:
        try:
            findings.extend(rule(ctx))
        except Exception as e:  # a rule must never crash the lint
            findings.append(Finding(
                f"internal-{rule.__name__}", "internal", "error",
                f"rule failed: {e}",
            ))
    return findings
