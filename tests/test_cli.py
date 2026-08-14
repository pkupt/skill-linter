"""End-to-end CLI tests: scan a real fixture tree, check report + exit codes."""

from __future__ import annotations

import json

from skill_linter.cli import main


def _write_skill(root, folder, name, description, body):
    d = root / folder
    d.mkdir(parents=True, exist_ok=True)
    (d / "SKILL.md").write_text(
        f"---\nname: {name}\ndescription: {description}\n---\n{body}", encoding="utf-8"
    )
    return d


def test_lint_clean_skill_exits_zero(tmp_path, capsys):
    _write_skill(tmp_path, "good-skill", "good-skill",
                 "Does X well. Use when the user asks about X.",
                 "# Good\n\n## When to Use\nUse when asked.\n")
    code = main([str(tmp_path), "--format", "text"])
    out = capsys.readouterr().out
    assert code == 0
    assert "✓ no findings" in out


def test_lint_bad_skill_exits_one(tmp_path, capsys):
    _write_skill(tmp_path, "Bad Skill", "Bad Skill",
                 "Helps.",
                 "# S\n\ncurl -H 'Authorization: Bearer sk-abc1234567890abcdef1234567890'\nrm -rf /tmp/x\n")
    code = main([str(tmp_path), "--format", "text"])
    assert code == 1


def test_lint_json_output(tmp_path, capsys):
    _write_skill(tmp_path, "Bad Skill", "Bad Skill", "Helps.", "# S\n")
    code = main([str(tmp_path), "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert code == 1
    assert isinstance(data, list)
    assert data[0]["error_count"] >= 1
    assert all("rule" in f for r in data for f in r["findings"])


def test_lint_warning_fail_on(tmp_path, capsys):
    # fully clean skill: name matches folder, long trigger-rich description
    _write_skill(tmp_path, "ok-skill", "ok-skill",
                 "Does X very well. Use when the user asks about X and needs a detailed answer.",
                 "# S\n\n## When to Use\nUse when asked about X.\n")
    # clean skill -> 0 even with --fail-on warning
    assert main([str(tmp_path), "--format", "text", "--fail-on", "warning"]) == 0
