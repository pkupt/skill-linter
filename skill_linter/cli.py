"""CLI entry point: `skill-lint [path] [--format json|text] [--fail-on level]`."""

from __future__ import annotations

import argparse
import sys
from typing import Dict, List

from .rules.base import Finding
from .rules import run_all
from .scanner import find_skills
from .report import build_reports, exit_code_for, to_human, to_json


def lint_path(path: str) -> Dict[str, List[Finding]]:
    results: Dict[str, List[Finding]] = {}
    for skill in find_skills(path):
        if skill.error:
            results[skill.path] = [
                Finding("scanner-error", "internal", "error",
                        f"failed to parse: {skill.error}")
            ]
            continue
        results[skill.path] = run_all(skill.context)
    return results


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="skill-lint",
        description="Lint Agent Skills (SKILL.md) for spec compliance, quality and security.",
    )
    parser.add_argument("path", nargs="?", default=".",
                        help="directory or file to lint (default: current dir)")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--fail-on", choices=["error", "warning", "info"], default="error",
                        help="minimum severity that fails the run (CI exit code)")
    parser.add_argument("--version", action="version", version="skill-lint 0.1.0")
    args = parser.parse_args(argv)

    results = lint_path(args.path)
    reports = build_reports(results)

    if args.format == "json":
        print(to_json(reports))
    else:
        print(to_human(reports))
        total = sum(r.total for r in reports)
        errors = sum(r.error_count for r in reports)
        print(f"\n=== {len(reports)} skill(s), {errors} error(s), {total} finding(s) ===")

    return exit_code_for(reports, fail_on=args.fail_on)


if __name__ == "__main__":
    sys.exit(main())
