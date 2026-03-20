# Contributing

## Running tests
Run the test suite from the repository root:

```bash
python -m pytest -q
```

## Adding fixtures
Add new fixture files under `fixtures/` in the matching category (for example `fixtures/valid/`, `fixtures/invalid/`, `fixtures/chains/`, or `fixtures/attestations/`) and then add or update tests that load them.

## Protocol change rule
Any protocol change must include corresponding updates in `specs/` and automated tests in `tests/`.

Local package-to-package dependencies (for example `origin-protocol-core`) do not resolve automatically unless you install packages in editable mode or adopt a workspace tool. For now, the root pytest `pythonpath` setup is enough for development.
