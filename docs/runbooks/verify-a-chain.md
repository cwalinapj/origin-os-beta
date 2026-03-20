# Runbook: Verify a Chain

## Prerequisites

- Python 3.11+
- `origin-verify` CLI installed (`pip install -e tools/cli`)

## Steps

1. Export your chain to a JSON file (array of manifest objects).
2. Run: `origin-verify verify path/to/chain.json`
3. Review the output report.

## Interpreting Results

- `PASS` — all steps are valid and the chain is intact.
- `FAIL` — one or more steps failed validation; see step-level errors.
