"""Report formatting: JSON (machine) + human-readable + exit codes (CI)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Dict, List

from .rules.base import Finding

SEVERITY_ORDER = {"error": 0, "warning": 1, "info": 2}


@dataclass
class SkillReport:
    skill: str
    findings: List[Finding] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return sum(1 for f in self.findings if f.severity == "error")

    @property
    def total(self) -> int:
        return len(self.findings)

    def to_dict(self) -> Dict:
        return {
            "skill": self.skill,
            "error_count": self.error_count,
            "total": len(self.findings),
            "findings": [f.to_dict() for f in self.findings],
        }


def build_reports(results: Dict[str, List[Finding]]) -> List[SkillReport]:
    return [SkillReport(skill=s, findings=fs) for s, fs in sorted(results.items())]


def to_json(reports: List[SkillReport]) -> str:
    return json.dumps([r.to_dict() for r in reports], ensure_ascii=False, indent=2)


def to_human(reports: List[SkillReport]) -> str:
    lines = []
    for r in reports:
        lines.append(f"\n{r.skill}")
        if not r.findings:
            lines.append("  ✓ no findings")
            continue
        ordered = sorted(r.findings, key=lambda f: SEVERITY_ORDER.get(f.severity, 9))
        for f in ordered:
            loc = f" line {f.line}" if f.line else ""
            lines.append(f"  [{f.severity}] {f.rule_id}{loc}: {f.message}")
            if f.fix_hint:
                lines.append(f"           fix: {f.fix_hint}")
    return "\n".join(lines)


def exit_code_for(reports: List[SkillReport], fail_on: str = "error") -> int:
    """CI-friendly exit code: 0 = clean, 1 = findings at or above fail_on."""
    if fail_on == "error":
        for r in reports:
            if r.error_count > 0:
                return 1
    elif fail_on in ("warning", "info"):
        for r in reports:
            if r.findings:
                return 1
    return 0
