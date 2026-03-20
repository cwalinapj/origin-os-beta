# Chain Fixtures

This directory contains JSON fixture files representing manifest chains used in compatibility tests.

- `valid/` — well-formed chains that must pass `verify_chain()`.
- `invalid/` — intentionally broken chains that must fail `verify_chain()`.

These fixtures are part of the protocol stability guarantee. Do not modify existing fixtures without a corresponding protocol version bump.
