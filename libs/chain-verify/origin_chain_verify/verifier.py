"""Top-level verify_chain() function."""

from __future__ import annotations

from origin_protocol_core.manifest import ManifestV1

from .reports import ChainVerificationSummary, StepVerificationReport
from .validators_chain import run_chain_validators
from .validators_step import run_step_validators


def verify_chain(manifests: list[ManifestV1]) -> ChainVerificationSummary:
    """Verify a sequence of manifests as a hash chain.

    Returns a :class:`ChainVerificationSummary` that describes every check
    performed and whether the chain passes overall.
    """
    run_id = manifests[0].run_id if manifests else "unknown"

    step_reports: list[StepVerificationReport] = []
    for i, manifest in enumerate(manifests):
        results = run_step_validators(manifest, expected_index=i)
        step_reports.append(StepVerificationReport(step_index=i, results=results))

    chain_results = run_chain_validators(manifests)

    return ChainVerificationSummary(
        run_id=run_id,
        step_reports=step_reports,
        chain_results=chain_results,
    )
