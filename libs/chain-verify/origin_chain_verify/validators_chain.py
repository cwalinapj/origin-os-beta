"""Cross-step chain validators."""

from __future__ import annotations

from origin_protocol_core.manifest import ManifestV1

from .reports import ValidationResult


def validate_hash_linkage(
    previous: ManifestV1, current: ManifestV1
) -> ValidationResult:
    """Verify that current.previous_step_digest == digest(previous)."""
    expected = previous.digest()
    actual = current.previous_step_digest
    if actual != expected:
        return ValidationResult.fail(
            "hash_linkage",
            f"Step {current.step_index}: previous_step_digest mismatch. "
            f"Expected {expected!r}, got {actual!r}.",
        )
    return ValidationResult.ok("hash_linkage")


def validate_run_id_consistency(manifests: list[ManifestV1]) -> ValidationResult:
    """All steps in a chain must share the same run_id."""
    run_ids = {m.run_id for m in manifests}
    if len(run_ids) > 1:
        return ValidationResult.fail(
            "run_id_consistency",
            f"Multiple run_ids found in chain: {sorted(run_ids)}",
        )
    return ValidationResult.ok("run_id_consistency")


def validate_chain_not_empty(manifests: list[ManifestV1]) -> ValidationResult:
    """A chain must contain at least one manifest."""
    if not manifests:
        return ValidationResult.fail("chain_not_empty", "Chain contains no manifests")
    return ValidationResult.ok("chain_not_empty")


def run_chain_validators(manifests: list[ManifestV1]) -> list[ValidationResult]:
    """Run all chain-level validators and return the list of results."""
    results = [
        validate_chain_not_empty(manifests),
        validate_run_id_consistency(manifests),
    ]
    for i in range(1, len(manifests)):
        results.append(validate_hash_linkage(manifests[i - 1], manifests[i]))
    return results
