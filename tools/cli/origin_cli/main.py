"""CLI entry point for origin-verify."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from origin_chain_verify import ChainVerificationSummary, verify_chain
from origin_protocol_core.manifest import ManifestV1


def _load_chain(path: Path) -> list[ManifestV1]:
    with path.open() as fh:
        raw = json.load(fh)
    if not isinstance(raw, list):
        raise ValueError(f"Expected a JSON array in {path}, got {type(raw).__name__}")
    return [ManifestV1.from_dict(item) for item in raw]


def _print_report(summary: ChainVerificationSummary) -> None:
    status_sym = "✓" if summary.passed else "✗"
    print(f"\n{status_sym} Chain verification: {summary.status.value}")
    print(f"  Run ID : {summary.run_id}")
    print(f"  Steps  : {len(summary.step_reports)}")

    for report in summary.step_reports:
        step_sym = "✓" if report.passed else "✗"
        print(f"\n  Step {report.step_index}: {step_sym}")
        for result in report.results:
            sym = "  ✓" if result.passed else "  ✗"
            msg = f" — {result.message}" if result.message else ""
            print(f"    {sym} [{result.check}]{msg}")

    if summary.chain_results:
        print("\n  Chain-level checks:")
        for result in summary.chain_results:
            sym = "  ✓" if result.passed else "  ✗"
            msg = f" — {result.message}" if result.message else ""
            print(f"    {sym} [{result.check}]{msg}")


def cmd_verify(args: argparse.Namespace) -> int:
    chain_path = Path(args.chain_file)
    if not chain_path.exists():
        print(f"Error: file not found: {chain_path}", file=sys.stderr)
        return 1

    try:
        manifests = _load_chain(chain_path)
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        print(f"Error loading chain: {exc}", file=sys.stderr)
        return 1

    summary = verify_chain(manifests)
    _print_report(summary)
    return 0 if summary.passed else 2


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="origin-verify",
        description="Verify a manifest chain from a JSON file.",
    )
    sub = parser.add_subparsers(dest="command")

    verify_parser = sub.add_parser("verify", help="Verify a chain JSON file")
    verify_parser.add_argument("chain_file", help="Path to chain JSON file")

    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        sys.exit(0)

    sys.exit(cmd_verify(args))


if __name__ == "__main__":
    main()
