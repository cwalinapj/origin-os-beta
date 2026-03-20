"""Per-step validators for ManifestV1."""

from __future__ import annotations

from origin_protocol_core.manifest import ManifestV1

from .reports import ValidationResult


def validate_required_fields(manifest: ManifestV1) -> ValidationResult:
    """Check that essential string fields are non-empty."""
    for attr in ("run_id", "agent_id", "action", "timestamp_utc"):
        if not getattr(manifest, attr, "").strip():
            return ValidationResult.fail(
                "required_fields", f"Field '{attr}' is empty on step {manifest.step_index}"
            )
    return ValidationResult.ok("required_fields")


def validate_step_index(manifest: ManifestV1, expected_index: int) -> ValidationResult:
    """Check that step_index matches the expected position in the chain."""
    if manifest.step_index != expected_index:
        return ValidationResult.fail(
            "step_index",
            f"Expected step_index={expected_index}, got {manifest.step_index}",
        )
    return ValidationResult.ok("step_index")


def validate_first_step_has_no_previous(manifest: ManifestV1) -> ValidationResult:
    """The first step (index 0) must have previous_step_digest=None."""
    if manifest.step_index == 0 and manifest.previous_step_digest is not None:
        return ValidationResult.fail(
            "first_step_no_previous",
            "Step 0 must have previous_step_digest=None",
        )
    return ValidationResult.ok("first_step_no_previous")


def validate_subsequent_step_has_previous(manifest: ManifestV1) -> ValidationResult:
    """Steps after index 0 must have a non-None previous_step_digest."""
    if manifest.step_index > 0 and manifest.previous_step_digest is None:
        return ValidationResult.fail(
            "subsequent_step_has_previous",
            f"Step {manifest.step_index} must have a previous_step_digest",
        )
    return ValidationResult.ok("subsequent_step_has_previous")


def run_step_validators(manifest: ManifestV1, expected_index: int) -> list[ValidationResult]:
    """Run all per-step validators and return the list of results."""
    return [
        validate_required_fields(manifest),
        validate_step_index(manifest, expected_index),
        validate_first_step_has_no_previous(manifest),
        validate_subsequent_step_has_previous(manifest),
    ]
