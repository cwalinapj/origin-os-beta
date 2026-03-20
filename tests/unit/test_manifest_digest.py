"""Tests for manifest digest determinism."""

import pytest
from origin_protocol_core.manifest import ManifestV1


def make_manifest(**kwargs) -> ManifestV1:
    defaults = {
        "run_id": "run-test",
        "step_index": 0,
        "agent_id": "agent-test",
        "action": "do_thing",
        "inputs": {"x": 1},
        "outputs": {"y": 2},
        "timestamp_utc": "2026-01-01T00:00:00Z",
        "previous_step_digest": None,
        "metadata": {},
    }
    defaults.update(kwargs)
    return ManifestV1(**defaults)


def test_digest_is_deterministic():
    m1 = make_manifest()
    m2 = make_manifest()
    assert m1.digest() == m2.digest()


def test_digest_changes_when_field_changes():
    m1 = make_manifest(action="do_thing")
    m2 = make_manifest(action="do_other")
    assert m1.digest() != m2.digest()


def test_digest_is_hex_string():
    m = make_manifest()
    d = m.digest()
    assert isinstance(d, str)
    assert len(d) == 64
    assert all(c in "0123456789abcdef" for c in d)


def test_from_dict_roundtrip():
    m = make_manifest()
    d = m.to_dict()
    m2 = ManifestV1.from_dict(d)
    assert m2.digest() == m.digest()


def test_from_dict_missing_field():
    from origin_protocol_core.errors import ManifestValidationError

    with pytest.raises(ManifestValidationError):
        ManifestV1.from_dict({"run_id": "x"})
