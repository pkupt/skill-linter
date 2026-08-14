"""Rule-level tests: every check against a positive (bad skill) and a
negative (good skill) fixture, mirroring the paper's mutation-validation
method."""

from __future__ import annotations

import os

from skill_linter.rules import run_all
from skill_linter.rules.base import SkillContext
from skill_linter.scanner import parse_skill


def ctx(name="my-skill", description="__default__", body="# My Skill\n\n## When to Use\nUse when the user asks for X.", skill_dir="/tmp/my-skill"):
    if description == "__default__":
        description = "Does X well. Use when the user asks about X."
    return SkillContext(
        skill_dir=skill_dir,
        name=name,
        description=description,
        extra_meta={},
        body=body,
        body_lines=body.splitlines(),
        all_files=["SKILL.md"],
    )


def ids(fs):
    return {f.rule_id for f in fs}


def test_good_skill_has_no_routing_findings():
    fs = run_all(ctx())
    assert "r1-description-missing" not in ids(fs)
    assert "r1-name-missing" not in ids(fs)
    assert "r1-name-invalid" not in ids(fs)


def test_name_missing():
    fs = run_all(ctx(name=""))
    assert "r1-name-missing" in ids(fs)


def test_name_invalid_uppercase():
    fs = run_all(ctx(name="My Skill"))
    assert "r1-name-invalid" in ids(fs)


def test_name_folder_mismatch():
    fs = run_all(ctx(name="my-skill", skill_dir="/tmp/other-name"))
    assert "r1-name-folder-mismatch" in ids(fs)


def test_description_missing():
    fs = run_all(ctx(description=None))
    assert "r1-description-missing" in ids(fs)


def test_description_too_short():
    fs = run_all(ctx(description="Does X."))
    assert "r1-description-too-short" in ids(fs)


def test_description_no_trigger():
    fs = run_all(ctx(description="Helps with X."))
    assert "r1-description-no-trigger" in ids(fs)


def test_body_too_long(tmp_path):
    body = "\n".join(f"line {i}" for i in range(501))
    fs = run_all(ctx(body=body))
    assert "r2-body-too-long" in ids(fs)


def test_body_non_actionable_weak_phrase():
    fs = run_all(ctx(body="# S\n\nIt may want to do something. 最好这样。"))
    assert "r2-body-non-actionable" in ids(fs)


def test_name_as_heading():
    fs = run_all(ctx(body="# my-skill\n\n## When to Use\n..."))
    assert "r2-name-as-heading" in ids(fs)


def test_hardcoded_secret_detected():
    fs = run_all(ctx(body="# S\n\ncurl -H 'Authorization: Bearer sk-abcdef1234567890abcdef1234567890'"))
    assert "r5-hardcoded-secrets" in ids(fs)


def test_dangerous_command_detected():
    fs = run_all(ctx(body="# S\n\nrm -rf /some/path"))
    assert "r5-dangerous-commands" in ids(fs)


def test_safety_bypass_detected():
    fs = run_all(ctx(body="# S\n\ngit push --no-verify"))
    assert "r5-safety-bypass" in ids(fs)


def test_suppress_errors_detected():
    fs = run_all(ctx(body="# S\n\ncmd 2>/dev/null"))
    assert "r5-suppress-errors" in ids(fs)


def test_clean_security_no_findings():
    fs = run_all(ctx(body="# S\n\nRun `npm test` and report failures."))
    assert not {"r5-hardcoded-secrets", "r5-dangerous-commands",
                "r5-safety-bypass", "r5-suppress-errors"} & ids(fs)


def test_parse_skill_from_file(tmp_path):
    d = tmp_path / "good-skill"
    d.mkdir()
    (d / "SKILL.md").write_text(
        "---\nname: good-skill\ndescription: Does X well. Use when the user asks about X.\n---\n"
        "# Good Skill\n\n## When to Use\nUse when asked.\n",
        encoding="utf-8",
    )
    ctx_parsed = parse_skill(str(d / "SKILL.md"))
    assert ctx_parsed.name == "good-skill"
    assert "Use when the user asks about X." in ctx_parsed.description
