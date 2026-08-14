"""Scan a directory tree for Agent Skills and parse each SKILL.md."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

import yaml

from .rules.base import SkillContext

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n?", re.DOTALL)


@dataclass
class SkillFile:
    path: str
    skill_dir: str
    context: Optional[SkillContext] = None
    error: Optional[str] = None


def _parse_frontmatter(text: str):
    m = FRONTMATTER_RE.match(text)
    if not m:
        return {}, ""
    try:
        meta = yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as e:
        # don't crash on bad YAML; surface as a finding later
        return {"__yaml_error__": str(e)}, text[m.end():]
    if not isinstance(meta, dict):
        return {}, text[m.end():]
    return meta, text[m.end():]


def parse_skill(path: str) -> SkillContext:
    with open(path, "r", encoding="utf-8") as f:
        text = f.read()

    meta, body = _parse_frontmatter(text)
    name = str(meta.get("name", "") or "").strip()
    description = meta.get("description")
    description = str(description).strip() if description is not None else None

    extra = {k: v for k, v in meta.items() if k not in ("name", "description")}
    if "__yaml_error__" in extra:
        # represent parse error as a finding via description? no — keep it in
        # extra and let the yaml-error rule (added by caller) handle it.
        pass

    all_files = []
    d = os.path.dirname(path)
    for root, _, files in os.walk(d):
        for fn in files:
            rel = os.path.relpath(os.path.join(root, fn), d)
            all_files.append(rel.replace(os.sep, "/"))

    return SkillContext(
        skill_dir=d,
        name=name,
        description=description,
        extra_meta=extra,
        body=body,
        body_lines=body.splitlines(),
        all_files=all_files,
    )


def find_skills(root: str) -> List[SkillFile]:
    """Walk root, collect every SKILL.md, parse it."""
    skills: List[SkillFile] = []
    for dirpath, dirnames, filenames in os.walk(root):
        # skip common noise
        dirnames[:] = [d for d in dirnames if d not in (".git", "node_modules", ".venv", "__pycache__")]
        if "SKILL.md" in filenames:
            p = os.path.join(dirpath, "SKILL.md")
            try:
                ctx = parse_skill(p)
                skills.append(SkillFile(path=p, skill_dir=ctx.skill_dir, context=ctx))
            except Exception as e:
                skills.append(SkillFile(path=p, skill_dir=dirpath, error=str(e)))
    return skills
