"""Compatibility tests using JSON fixtures."""

import json
from pathlib import Path

import pytest
from origin_protocol_core.manifest import ManifestV1
from origin_chain_verify import verify_chain

FIXTURES_DIR = Path(__file__).parent.parent.parent / "fixtures"


def load_chain(path: Path) -> list[ManifestV1]:
    with path.open() as fh:
        raw = json.load(fh)
    return [ManifestV1.from_dict(item) for item in raw]


def test_valid_two_step_fixture():
    chain = load_chain(FIXTURES_DIR / "valid" / "chain_two_steps.json")
    summary = verify_chain(chain)
    assert summary.passed, f"Chain verification failed: {summary}"


def test_invalid_broken_hash_chain_fixture():
    chain = load_chain(FIXTURES_DIR / "invalid" / "broken_hash_chain.json")
    summary = verify_chain(chain)
    assert not summary.passed
