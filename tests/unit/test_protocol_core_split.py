"""Tests for protocol-core split symbols."""

from datetime import timezone

from origin_protocol_core import GENESIS, is_hex_sha256, parse_rfc3339, sha256_bytes
from origin_protocol_core.types import ChainValidator, ValidationResult, Validator


def test_genesis_constant_is_none():
    assert GENESIS is None


def test_sha256_bytes_and_hex_check():
    digest = sha256_bytes("abc")
    assert isinstance(digest, str)
    assert is_hex_sha256(digest)


def test_parse_rfc3339_z():
    dt = parse_rfc3339("2026-01-01T00:00:00Z")
    assert dt.tzinfo == timezone.utc


def test_validator_aliases_are_callable_types():
    assert Validator is not None
    assert ChainValidator is not None
    result = ValidationResult.ok("x")
    assert result.passed
