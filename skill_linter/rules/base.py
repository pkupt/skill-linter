"""Rule framework: every check is a Rule with an id, tier and severity.

Design principles (mirroring the ecosystem's own lessons):
- Fail-closed: unknown constructs default to suspicious, never to pass.
- Each rule must be verifiable against a positive and a negative fixture.
- Output must be actionable: tell the author *what* to fix, not just *that*
  something is wrong.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Protocol

# Tiers from the paper's two-tier defect taxonomy
TIER_SPEC = "spec"        # violates the official specification
TIER_BEST_PRACTICE = "best-practice"  # peer-reviewed / industry best practice


@dataclass
class Finding:
    rule_id: str
    tier: str
    severity: str          # "error" | "warning" | "info"
    message: str
    line: Optional[int] = None
    # structured key so machines (and the future --fix) can act on it
    fix_hint: Optional[str] = None

    def to_dict(self) -> Dict:
        d = {
            "rule": self.rule_id,
            "tier": self.tier,
            "severity": self.severity,
            "message": self.message,
            "line": self.line,
        }
        if self.fix_hint:
            d["fix_hint"] = self.fix_hint
        return d


class Rule(Protocol):
    id: str
    tier: str
    severity: str

    def check(self, ctx: "SkillContext") -> List[Finding]:
        ...


@dataclass
class SkillContext:
    """Everything a rule needs to inspect one SKILL.md."""
    skill_dir: str
    name: str                     # frontmatter name (raw, may be invalid)
    description: Optional[str]    # frontmatter description
    extra_meta: Dict              # remaining frontmatter fields
    body: str                     # markdown body
    body_lines: List[str]         # body split by lines
    all_files: List[str]          # files in the skill directory (relative)


# --- shared helpers ---------------------------------------------------------

NAME_RE = re.compile(r"^[a-z0-9-]+$")
TRIGGER_WORDS = (
    "use when", "when the user", "when asked", "trigger", "use for",
    "when you", "run before", "apply when",
)
# weak / non-actionable instructions (paper: R2.2 "non-actionable body")
WEAK_PHRASES = (
    "建议", "一般来说", "视情况而定", "may want to", "consider trying",
    "最好", "try to", "it might be a good idea", "酌情",
)
DANGEROUS_CMDS = (
    "rm -rf", "mkfs.", ":(){:|:&};:", "shutdown", "reboot",
    "dd if=/dev/zero", "chmod -R 777 /", "git push --force",
)
BYPASS_CMDS = ("--no-verify", "--force", "-f --force", "bypassPermissions")
SECRET_PATTERNS = (
    re.compile(r"(?i)\b(sk-[a-zA-Z0-9]{20,})\b"),
    re.compile(r"(?i)\b(api[_-]?key|secret|token|password|passwd)\b\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]"),
    re.compile(r"(?i)\b(github_pat_|ghp_|gho_|xoxb-|AKIA[0-9A-Z]{16})\b"),
    re.compile(r"(?i)\bAIza[0-9A-Za-z\-_]{35}\b"),
)
