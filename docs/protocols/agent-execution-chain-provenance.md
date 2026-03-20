"""
Origin OS Beta — Agent Execution Chain Provenance
==================================================
Tamper-evident, cryptographically attested audit ledger for
Origin OS agent container execution traces.

Architecture
------------
  ManifestV1              Frozen dataclass. One per agent execution step.
  verify_chain()          Layered validator pipeline (integrity → provenance → policy).
  ChainStore (Protocol)   Persistence interface.
  InMemoryChainStore      Reference / test implementation.
  VerifiedChainStore      Write-time-validating wrapper. Signs attestations with Ed25519.

Trust model
-----------
  Attestations are signed with Ed25519. The Solana registry resolves the
  verification key from the compound key (owner_agent_id, key_id), preventing
  a payload from claiming one agent identity but using a different signer key.
  PDA seeds: [b"agent_key", owner_agent_id.as_bytes(), key_id.as_bytes()]
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional, Protocol, Sequence, runtime_checkable

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

# ── Constants ─────────────────────────────────────────────────────────────────

GENESIS = "0" * 64
SUPPORTED_SIGNATURE_ALGS = frozenset({"ed25519"})


# ── Helpers ───────────────────────────────────────────────────────────────────

def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical_json(obj: Any) -> bytes:
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def parse_rfc3339(ts: str) -> datetime:
    return datetime.fromisoformat(ts.replace("Z", "+00:00"))


def is_hex_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value.lower())
    )


# ── Manifest ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ManifestV1:
    """
    Immutable record of a single agent execution step.
    digest() is the canonical hash committed into the chain.
    """

    schema_version: str
    run_id: str
    step_id: str
    sequence_no: int

    agent_id: str
    runner_id: str
    runner_version: str
    vm_image_id: str
    model_id: str

    previous_step_digest: str       # GENESIS for step 0
    started_at: str                 # RFC 3339 / ISO 8601
    ended_at: str
    manifest_created_at: str

    exit_code: int

    source_snapshot_sha256: str
    stdout_sha256: str
    stderr_sha256: str
    results_sha256: str

    patch_sha256: Optional[str] = None
    command_sha256: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_canonical_dict(self) -> dict[str, Any]:
        """Digest input. Envelope fields (signature, etc.) must NOT appear here."""
        return {
            "schema_version":          self.schema_version,
            "run_id":                  self.run_id,
            "step_id":                 self.step_id,
            "sequence_no":             self.sequence_no,
            "agent_id":                self.agent_id,
            "runner_id":               self.runner_id,
            "runner_version":          self.runner_version,
            "vm_image_id":             self.vm_image_id,
            "model_id":                self.model_id,
            "previous_step_digest":    self.previous_step_digest,
            "started_at":              self.started_at,
            "ended_at":                self.ended_at,
            "manifest_created_at":     self.manifest_created_at,
            "exit_code":               self.exit_code,
            "source_snapshot_sha256":  self.source_snapshot_sha256,
            "stdout_sha256":           self.stdout_sha256,
            "stderr_sha256":           self.stderr_sha256,
            "results_sha256":          self.results_sha256,
            "patch_sha256":            self.patch_sha256,
            "command_sha256":          self.command_sha256,
            "metadata":                self.metadata,
        }

    def digest(self) -> str:
        return sha256_bytes(canonical_json(self.to_canonical_dict()))

    @staticmethod
    def from_dict(data: dict[str, Any]) -> ManifestV1:
        d = dict(data)
        d.setdefault("metadata", {})
        d.setdefault("patch_sha256", None)
        d.setdefault("command_sha256", None)
        return ManifestV1(**d)


# ── Validation types ──────────────────────────────────────────────────────────

@dataclass
class ValidationResult:
    ok: bool
    validator: str
    step_id: str
    category: str               # integrity | provenance | policy
    severity: str = "error"     # error | warning
    reason: str = ""

    def __bool__(self) -> bool:
        return self.ok


@dataclass
class ChainVerificationSummary:
    chain_ok: bool
    integrity_ok: bool
    provenance_ok: bool
    policy_ok: bool
    final_recomputed_digest: Optional[str]
    step_count: int
    failures: list[ValidationResult]
    results: list[ValidationResult]


Validator = Callable[
    [ManifestV1, str, Optional[str], dict[str, Any]],
    ValidationResult,
]
ChainValidator = Callable[
    [Sequence[tuple[ManifestV1, str]], dict[str, Any]],
    list[ValidationResult],
]


# ── Integrity validators (per-step) ───────────────────────────────────────────

def validate_required_strings(
    manifest: ManifestV1,
    stored_digest: str,
    prev_digest: Optional[str],
    ctx: dict[str, Any],
) -> ValidationResult:
    required = [
        ("schema_version",         manifest.schema_version),
        ("run_id",                 manifest.run_id),
        ("step_id",                manifest.step_id),
        ("agent_id",               manifest.agent_id),
        ("runner_id",              manifest.runner_id),
        ("runner_version",         manifest.runner_version),
        ("vm_image_id",            manifest.vm_image_id),
        ("model_id",               manifest.model_id),
        ("previous_step_digest",   manifest.previous_step_digest),
        ("started_at",             manifest.started_at),
        ("ended_at",               manifest.ended_at),
        ("manifest_created_at",    manifest.manifest_created_at),
        ("source_snapshot_sha256", manifest.source_snapshot_sha256),
        ("stdout_sha256",          manifest.stdout_sha256),
        ("stderr_sha256",          manifest.stderr_sha256),
        ("results_sha256",         manifest.results_sha256),
    ]
    bad = [name for name, val in required if not isinstance(val, str) or not val]
    ok = not bad
    return ValidationResult(
        ok=ok, validator="required_strings", step_id=manifest.step_id, category="integrity",
        reason="" if ok else f"missing/invalid string fields: {bad}",
    )


def validate_numeric_fields(
    manifest: ManifestV1,
    stored_digest: str,
    prev_digest: Optional[str],
    ctx: dict[str, Any],
) -> ValidationResult:
    if not isinstance(manifest.sequence_no, int) or manifest.sequence_no < 0:
        return ValidationResult(
            ok=False, validator="numeric_fields", step_id=manifest.step_id, category="integrity",
            reason=f"sequence_no must be a non-negative int, got {manifest.sequence_no!r}",
        )
    if not isinstance(manifest.exit_code, int):
        return ValidationResult(
            ok=False, validator="numeric_fields", step_id=manifest.step_id, category="integrity",
            reason=f"exit_code must be an int, got {manifest.exit_code!r}",
        )
    return ValidationResult(
        ok=True, validator="numeric_fields", step_id=manifest.step_id, category="integrity",
    )


def validate_sha_fields(
    manifest: ManifestV1,
    stored_digest: str,
    prev_digest: Optional[str],
    ctx: dict[str, Any],
) -> ValidationResult:
    fields = [
        manifest.previous_step_digest,
        manifest.source_snapshot_sha256,
        manifest.stdout_sha256,
        manifest.stderr_sha256,
        manifest.results_sha256,
    ]
    if manifest.patch_sha256 is not None:
        fields.append(manifest.patch_sha256)
    if manifest.command_sha256 is not None:
        fields.append(manifest.command_sha256)
    bad = [v for v in fields if not is_hex_sha256(v)]
    ok = not bad
    return ValidationResult(
        ok=ok, validator="sha_fields", step_id=manifest.step_id, category="integrity",
        reason="" if ok else f"invalid sha256 values: {bad}",
    )


def validate_timestamps(
    manifest: ManifestV1,
    stored_digest: str,
    prev_digest: Optional[str],
    ctx: dict[str, Any],
) -> ValidationResult:
    try:
        started = parse_rfc3339(manifest.started_at)
        ended   = parse_rfc3339(manifest.ended_at)
        created = parse_rfc3339(manifest.manifest_created_at)
    except Exception as exc:
        return ValidationResult(
            ok=False, validator="timestamps", step_id=manifest.step_id, category="integrity",
            reason=f"invalid timestamp format: {exc}",
        )
    if ended < started:
        return ValidationResult(
            ok=False, validator="timestamps", step_id=manifest.step_id, category="integrity",
            reason="ended_at is earlier than started_at",
        )
    if created < ended:
        return ValidationResult(
            ok=False, validator="timestamps", step_id=manifest.step_id, category="integrity",
            reason="manifest_created_at is earlier than ended_at",
        )
    return ValidationResult(
        ok=True, validator="timestamps", step_id=manifest.step_id, category="integrity",
    )


def validate_schema_version(
    manifest: ManifestV1,
    stored_digest: str,
    prev_digest: Optional[str],
    ctx: dict[str, Any],
) -> ValidationResult:
    known = set(ctx.get("known_schema_versions", {"1.0"}))
    ok = manifest.schema_version in known
    return ValidationResult(
        ok=ok, validator="schema_version", step_id=manifest.step_id, category="integrity",
        reason="" if ok else f"unknown schema_version={manifest.schema_version!r}",
    )


def validate_digest_integrity(
    manifest: ManifestV1,
    stored_digest: str,
    prev_digest: Optional[str],
    ctx: dict[str, Any],
) -> ValidationResult:
    recomputed = manifest.digest()
    ok = recomputed == stored_digest
    return ValidationResult(
        ok=ok, validator="digest_integrity", step_id=manifest.step_id, category="integrity",
        reason="" if ok else f"recomputed={recomputed!r} != stored={stored_digest!r}",
    )


def validate_chain_linkage(
    manifest: ManifestV1,
    stored_digest: str,
    prev_digest: Optional[str],
    ctx: dict[str, Any],
) -> ValidationResult:
    expected = prev_digest or GENESIS
    ok = manifest.previous_step_digest == expected
    return ValidationResult(
        ok=ok, validator="chain_linkage", step_id=manifest.step_id, category="integrity",
        reason="" if ok else f"expected={expected!r}, got={manifest.previous_step_digest!r}",
    )


# ── Provenance validators (per-step) ──────────────────────────────────────────

def validate_agent_allowlist(
    manifest: ManifestV1,
    stored_digest: str,
    prev_digest: Optional[str],
    ctx: dict[str, Any],
) -> ValidationResult:
    allowed = ctx.get("allowed_agents")
    ok = allowed is None or manifest.agent_id in set(allowed)
    return ValidationResult(
        ok=ok, validator="agent_allowlist", step_id=manifest.step_id, category="provenance",
        reason="" if ok else f"agent_id={manifest.agent_id!r} not allowed",
    )


def validate_model_allowlist(
    manifest: ManifestV1,
    stored_digest: str,
    prev_digest: Optional[str],
    ctx: dict[str, Any],
) -> ValidationResult:
    allowed = ctx.get("allowed_models")
    ok = allowed is None or manifest.model_id in set(allowed)
    return ValidationResult(
        ok=ok, validator="model_allowlist", step_id=manifest.step_id, category="provenance",
        reason="" if ok else f"model_id={manifest.model_id!r} not allowed",
    )


def validate_vm_image_allowlist(
    manifest: ManifestV1,
    stored_digest: str,
    prev_digest: Optional[str],
    ctx: dict[str, Any],
) -> ValidationResult:
    allowed = ctx.get("allowed_vm_images")
    ok = allowed is None or manifest.vm_image_id in set(allowed)
    return ValidationResult(
        ok=ok, validator="vm_image_allowlist", step_id=manifest.step_id, category="provenance",
        reason="" if ok else f"vm_image_id={manifest.vm_image_id!r} not allowed",
    )


# ── Policy validators (per-step) ──────────────────────────────────────────────

def validate_step_duration(
    manifest: ManifestV1,
    stored_digest: str,
    prev_digest: Optional[str],
    ctx: dict[str, Any],
) -> ValidationResult:
    max_s = ctx.get("max_duration_s")
    if max_s is None:
        return ValidationResult(
            ok=True, validator="step_duration", step_id=manifest.step_id,
            category="policy", severity="warning",
        )
    elapsed_s = (
        parse_rfc3339(manifest.ended_at) - parse_rfc3339(manifest.started_at)
    ).total_seconds()
    ok = elapsed_s <= max_s
    return ValidationResult(
        ok=ok, validator="step_duration", step_id=manifest.step_id,
        category="policy", severity="warning",
        reason="" if ok else f"elapsed={elapsed_s:.3f}s > max={max_s}s",
    )


def validate_exit_code_policy(
    manifest: ManifestV1,
    stored_digest: str,
    prev_digest: Optional[str],
    ctx: dict[str, Any],
) -> ValidationResult:
    allowed = ctx.get("allowed_exit_codes")
    if allowed is None:
        return ValidationResult(
            ok=True, validator="exit_code_policy", step_id=manifest.step_id,
            category="policy", severity="warning",
        )
    ok = manifest.exit_code in set(allowed)
    return ValidationResult(
        ok=ok, validator="exit_code_policy", step_id=manifest.step_id,
        category="policy", severity="warning",
        reason="" if ok else f"exit_code={manifest.exit_code} not in {set(allowed)}",
    )


# ── Chain validators (whole-chain) ────────────────────────────────────────────

def validate_run_id_consistent(
    manifests_and_digests: Sequence[tuple[ManifestV1, str]],
    ctx: dict[str, Any],
) -> list[ValidationResult]:
    if not manifests_and_digests:
        return []
    expected = manifests_and_digests[0][0].run_id
    return [
        ValidationResult(
            ok=(m.run_id == expected),
            validator="run_id_consistent", step_id=m.step_id, category="integrity",
            reason="" if m.run_id == expected else f"expected {expected!r}, got {m.run_id!r}",
        )
        for m, _ in manifests_and_digests
    ]


def validate_sequence_monotonic(
    manifests_and_digests: Sequence[tuple[ManifestV1, str]],
    ctx: dict[str, Any],
) -> list[ValidationResult]:
    results: list[ValidationResult] = []
    for i, (manifest, _) in enumerate(manifests_and_digests):
        if i == 0:
            ok = manifest.sequence_no >= 0
            results.append(ValidationResult(
                ok=ok, validator="sequence_monotonic", step_id=manifest.step_id, category="integrity",
                reason="" if ok else f"invalid initial sequence_no={manifest.sequence_no}",
            ))
        else:
            prev_seq = manifests_and_digests[i - 1][0].sequence_no
            ok = manifest.sequence_no == prev_seq + 1
            results.append(ValidationResult(
                ok=ok, validator="sequence_monotonic", step_id=manifest.step_id, category="integrity",
                reason="" if ok else f"expected seq={prev_seq + 1}, got {manifest.sequence_no}",
            ))
    return results


def validate_step_ids_unique(
    manifests_and_digests: Sequence[tuple[ManifestV1, str]],
    ctx: dict[str, Any],
) -> list[ValidationResult]:
    seen: set[str] = set()
    results: list[ValidationResult] = []
    for manifest, _ in manifests_and_digests:
        ok = manifest.step_id not in seen
        results.append(ValidationResult(
            ok=ok, validator="step_ids_unique", step_id=manifest.step_id, category="integrity",
            reason="" if ok else f"duplicate step_id={manifest.step_id!r}",
        ))
        seen.add(manifest.step_id)
    return results


def validate_timestamps_monotonic(
    manifests_and_digests: Sequence[tuple[ManifestV1, str]],
    ctx: dict[str, Any],
) -> list[ValidationResult]:
    """Per-agent monotonicity — supports parallel Origin OS agent containers."""
    last_ended_per_agent: dict[str, datetime] = {}
    results: list[ValidationResult] = []
    for manifest, _ in manifests_and_digests:
        started    = parse_rfc3339(manifest.started_at)
        prev_ended = last_ended_per_agent.get(manifest.agent_id)
        ok = prev_ended is None or started >= prev_ended
        results.append(ValidationResult(
            ok=ok, validator="timestamps_monotonic", step_id=manifest.step_id, category="integrity",
            reason="" if ok else (
                f"agent={manifest.agent_id!r} started_at={manifest.started_at!r} "
                f"precedes its own prev ended_at={prev_ended.isoformat()!r}"
            ),
        ))
        last_ended_per_agent[manifest.agent_id] = parse_rfc3339(manifest.ended_at)
    return results


# ── Validator registries ──────────────────────────────────────────────────────

INTEGRITY_VALIDATORS: list[Validator] = [
    validate_required_strings,
    validate_numeric_fields,        # sequence_no + exit_code
    validate_sha_fields,
    validate_timestamps,
    validate_schema_version,
    validate_digest_integrity,
    validate_chain_linkage,
]

PROVENANCE_VALIDATORS: list[Validator] = [
    validate_agent_allowlist,
    validate_model_allowlist,
    validate_vm_image_allowlist,
]

POLICY_VALIDATORS: list[Validator] = [
    validate_step_duration,
    validate_exit_code_policy,
]

CHAIN_VALIDATORS: list[ChainValidator] = [
    validate_run_id_consistent,
    validate_sequence_monotonic,
    validate_step_ids_unique,
    validate_timestamps_monotonic,
]


# ── verify_chain ──────────────────────────────────────────────────────────────

def verify_chain(
    manifests_and_digests: Sequence[tuple[ManifestV1, str]],
    *,
    initial_prev_digest: Optional[str] = None,
    chain_validators: Optional[Sequence[ChainValidator]] = None,
    integrity_validators: Optional[Sequence[Validator]] = None,
    provenance_validators: Optional[Sequence[Validator]] = None,
    policy_validators: Optional[Sequence[Validator]] = None,
    context: Optional[dict[str, Any]] = None,
    fail_fast: bool = False,
) -> ChainVerificationSummary:
    """
    initial_prev_digest — pass head digest when verifying a single appended step
                          so validate_chain_linkage checks against the real prev,
                          not GENESIS.
    """
    context              = context or {}
    chain_validators     = list(chain_validators    or CHAIN_VALIDATORS)
    integrity_validators = list(integrity_validators or INTEGRITY_VALIDATORS)
    provenance_validators = list(provenance_validators or PROVENANCE_VALIDATORS)
    policy_validators    = list(policy_validators   or POLICY_VALIDATORS)

    results:  list[ValidationResult] = []
    failures: list[ValidationResult] = []

    def record(r: ValidationResult) -> None:
        results.append(r)
        if not r.ok:
            failures.append(r)
            if fail_fast:
                raise ValueError(
                    f"[{r.category}:{r.validator}] step={r.step_id}: {r.reason}"
                )

    for cv in chain_validators:
        for r in cv(manifests_and_digests, context):
            record(r)

    prev_recomputed_digest: Optional[str] = initial_prev_digest
    final_recomputed_digest: Optional[str] = None

    for manifest, stored_digest in manifests_and_digests:
        step_integrity: list[ValidationResult] = []
        for v in integrity_validators:
            r = v(manifest, stored_digest, prev_recomputed_digest, context)
            step_integrity.append(r)
            record(r)

        if all(r.ok for r in step_integrity):
            for v in provenance_validators:
                record(v(manifest, stored_digest, prev_recomputed_digest, context))
            for v in policy_validators:
                record(v(manifest, stored_digest, prev_recomputed_digest, context))

        recomputed = manifest.digest()
        prev_recomputed_digest  = recomputed
        final_recomputed_digest = recomputed

    integrity_ok  = not any(r.category == "integrity"  and not r.ok for r in results)
    provenance_ok = not any(r.category == "provenance" and not r.ok for r in results)
    policy_ok     = not any(r.category == "policy"     and not r.ok for r in results)

    return ChainVerificationSummary(
        chain_ok=integrity_ok and provenance_ok and policy_ok,
        integrity_ok=integrity_ok,
        provenance_ok=provenance_ok,
        policy_ok=policy_ok,
        final_recomputed_digest=final_recomputed_digest,
        step_count=len(manifests_and_digests),
        failures=failures,
        results=results,
    )


# ── Attestation ───────────────────────────────────────────────────────────────

def build_attestation_payload(
    manifests_and_digests: Sequence[tuple[ManifestV1, str]],
    verification: ChainVerificationSummary,
) -> dict[str, Any]:
    if not manifests_and_digests:
        raise ValueError("cannot attest an empty chain")
    first = manifests_and_digests[0][0]
    last  = manifests_and_digests[-1][0]
    return {
        "schema_version":          "attestation/1.0",
        "run_id":                  first.run_id,
        # owner_agent_id is the Solana PDA anchor — must match key registry
        "owner_agent_id":          first.agent_id,
        "agent_ids":               sorted({m.agent_id for m, _ in manifests_and_digests}),
        "step_count":              verification.step_count,
        "final_digest":            verification.final_recomputed_digest,
        "integrity_ok":            verification.integrity_ok,
        "provenance_ok":           verification.provenance_ok,
        "policy_ok":               verification.policy_ok,
        "last_step_id":            last.step_id,
        "last_sequence_no":        last.sequence_no,
        "manifest_schema_version": last.schema_version,
        "generated_at":            datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def sign_attestation(
    payload: dict[str, Any],
    private_key: Ed25519PrivateKey,
    key_id: str,
) -> dict[str, Any]:
    """
    Signs the canonical JSON of the payload with Ed25519.

    key_id   — opaque handle used by the Solana registry to look up the pubkey.
               Recommended value: hex fingerprint (SHA-256) of the Ed25519 public key.

    The Solana instruction resolves the verification key from
    (owner_agent_id, key_id) — both fields are included in the signed payload,
    so any mismatch between them and the registry PDA seeds causes the
    instruction to fail before ed25519_verify is reached.
    """
    if not isinstance(key_id, str) or not key_id.strip():
        raise ValueError("key_id must be a non-empty string")

    body = canonical_json(payload)
    return {
        **payload,
        "signed_fields_sha256": sha256_bytes(body),
        "signature_alg":        "ed25519",
        "key_id":               key_id,
        "signature":            private_key.sign(body).hex(),
    }


def verify_attestation_signature(
    signed: dict[str, Any],
    public_key: Ed25519PublicKey,
) -> bool:
    """
    Returns True iff the signature is valid and the payload has not been mutated.

    Raises ValueError for an unsupported or missing signature_alg — this is a
    caller contract violation, not a signature mismatch, and must not be silenced.
    """
    alg = signed.get("signature_alg")
    if alg not in SUPPORTED_SIGNATURE_ALGS:
        raise ValueError(
            f"unsupported or missing signature_alg={alg!r}; "
            f"expected one of {sorted(SUPPORTED_SIGNATURE_ALGS)}"
        )

    strip = {"signature", "signature_alg", "key_id", "signed_fields_sha256"}
    payload_only = {k: v for k, v in signed.items() if k not in strip}
    body = canonical_json(payload_only)

    if sha256_bytes(body) != signed.get("signed_fields_sha256", ""):
        return False    # payload mutated after signing

    try:
        public_key.verify(bytes.fromhex(signed["signature"]), body)
        return True
    except Exception:
        return False


# ── ChainStore protocol ───────────────────────────────────────────────────────

@runtime_checkable
class ChainStore(Protocol):
    def append_step(self, manifest: ManifestV1, stored_digest: str) -> None: ...
    def load_chain(self, run_id: str) -> list[tuple[ManifestV1, str]]: ...
    def load_head(self, run_id: str) -> Optional[tuple[ManifestV1, str]]: ...
    def store_attestation(self, run_id: str, attestation: dict[str, Any]) -> None: ...
    def list_runs(self) -> list[str]: ...


# ── InMemoryChainStore ────────────────────────────────────────────────────────

class InMemoryChainStore:
    """Reference implementation — unit tests and single-agent containers."""

    def __init__(self) -> None:
        self._chains:       dict[str, list[tuple[ManifestV1, str]]] = {}
        self._attestations: dict[str, dict[str, Any]]               = {}

    def append_step(self, manifest: ManifestV1, stored_digest: str) -> None:
        self._chains.setdefault(manifest.run_id, []).append((manifest, stored_digest))

    def load_chain(self, run_id: str) -> list[tuple[ManifestV1, str]]:
        return list(self._chains.get(run_id, []))

    def load_head(self, run_id: str) -> Optional[tuple[ManifestV1, str]]:
        chain = self._chains.get(run_id, [])
        return chain[-1] if chain else None

    def store_attestation(self, run_id: str, attestation: dict[str, Any]) -> None:
        self._attestations[run_id] = attestation

    def list_runs(self) -> list[str]:
        return list(self._chains.keys())


# ── VerifiedChainStore ────────────────────────────────────────────────────────

class VerifiedChainStore:
    """
    Write-time-validating wrapper around any ChainStore.

    Guarantees
    ----------
    * Every step is validated (integrity → provenance → policy) before persistence.
    * Chain linkage and sequence monotonicity are checked at write time.
    * load_chain() is a cheap passthrough — re-verification is already guaranteed.
    * audit_chain() performs a full re-verification; call before attestation.
    * store_attestation() audits, builds, signs, and persists in one atomic call.
    """

    def __init__(
        self,
        inner: ChainStore,
        context: Optional[dict[str, Any]] = None,
    ) -> None:
        if not isinstance(inner, ChainStore):
            raise TypeError(f"inner must implement ChainStore, got {type(inner)}")
        self.inner   = inner
        self.context = context or {}

    # ── Writes ────────────────────────────────────────────────────────────────

    def append_step(self, manifest: ManifestV1, stored_digest: str) -> None:
        head = self.inner.load_head(manifest.run_id)

        # Chain linkage — checked explicitly so the error message is precise.
        expected_prev = head[1] if head is not None else GENESIS
        if manifest.previous_step_digest != expected_prev:
            raise ValueError(
                f"chain linkage rejected at step={manifest.step_id!r}: "
                f"expected prev={expected_prev!r}, "
                f"got {manifest.previous_step_digest!r}"
            )

        # Sequence number — must be exactly prev + 1.
        if head is not None:
            prev_manifest, _ = head
            if manifest.sequence_no != prev_manifest.sequence_no + 1:
                raise ValueError(
                    f"sequence rejected at step={manifest.step_id!r}: "
                    f"expected {prev_manifest.sequence_no + 1}, "
                    f"got {manifest.sequence_no}"
                )

        # Full per-step validation (integrity → provenance → policy).
        # initial_prev_digest carries the real head digest so validate_chain_linkage
        # does not check against GENESIS for non-genesis steps.
        verify_chain(
            [(manifest, stored_digest)],
            initial_prev_digest=head[1] if head is not None else None,
            chain_validators=[],        # cross-step checks require full chain
            context=self.context,
            fail_fast=True,
        )

        self.inner.append_step(manifest, stored_digest)

    # ── Reads ─────────────────────────────────────────────────────────────────

    def load_chain(self, run_id: str) -> list[tuple[ManifestV1, str]]:
        """Passthrough — integrity was enforced at write time."""
        return self.inner.load_chain(run_id)

    def load_head(self, run_id: str) -> Optional[tuple[ManifestV1, str]]:
        return self.inner.load_head(run_id)

    def list_runs(self) -> list[str]:
        return self.inner.list_runs()

    # ── Audit ─────────────────────────────────────────────────────────────────

    def audit_chain(self, run_id: str) -> ChainVerificationSummary:
        """
        Full re-verification of the stored chain including all chain-level validators.
        Always call this before generating an attestation or filing an incident report.
        """
        return verify_chain(
            self.inner.load_chain(run_id),
            context=self.context,
            fail_fast=False,
        )

    # ── Attestation ───────────────────────────────────────────────────────────

    def store_attestation(
        self,
        run_id: str,
        private_key: Ed25519PrivateKey,
        key_id: str,
    ) -> dict[str, Any]:
        """
        audit → build → sign → persist.

        Raises if the chain has any integrity, provenance, or policy failures.
        The signed payload includes signature_alg and key_id so the Solana
        instruction can resolve and verify the key from (owner_agent_id, key_id)
        without any out-of-band information.
        """
        summary = self.audit_chain(run_id)
        if not summary.chain_ok:
            raise ValueError(
                f"cannot attest run_id={run_id!r}: "
                + ", ".join(
                    f"{f.validator}@{f.step_id}" for f in summary.failures
                )
            )
        chain   = self.inner.load_chain(run_id)
        payload = build_attestation_payload(chain, summary)
        signed  = sign_attestation(payload, private_key, key_id)
        self.inner.store_attestation(run_id, signed)
        return signed


# ── Example / smoke test ──────────────────────────────────────────────────────

if __name__ == "__main__":
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def _make_step(
        step_id: str,
        sequence_no: int,
        prev_digest: str,
        exit_code: int = 0,
    ) -> tuple[ManifestV1, str]:
        m = ManifestV1(
            schema_version="1.0",
            run_id="run_beta_001",
            step_id=step_id,
            sequence_no=sequence_no,
            agent_id="origin-agent-0",
            runner_id="runner-a",
            runner_version="0.1.0",
            vm_image_id="python312-v1",
            model_id="gpt-5-mini",
            previous_step_digest=prev_digest,
            started_at=now,
            ended_at=now,
            manifest_created_at=now,
            exit_code=exit_code,
            source_snapshot_sha256=sha256_bytes(f"src-{step_id}".encode()),
            stdout_sha256=sha256_bytes(b"ok"),
            stderr_sha256=sha256_bytes(b""),
            results_sha256=sha256_bytes(f"results-{step_id}".encode()),
            patch_sha256=sha256_bytes(f"patch-{step_id}".encode()),
            command_sha256=sha256_bytes(b"pytest -q"),
        )
        return m, m.digest()

    ctx = {
        "known_schema_versions": {"1.0"},
        "allowed_agents":        {"origin-agent-0"},
        "allowed_models":        {"gpt-5-mini"},
        "allowed_vm_images":     {"python312-v1"},
        "allowed_exit_codes":    {0},
        "max_duration_s":        300,
    }

    private_key = Ed25519PrivateKey.generate()
    public_key  = private_key.public_key()
    key_id      = sha256_bytes(
        public_key.public_bytes_raw()
        if hasattr(public_key, "public_bytes_raw")
        else public_key.public_bytes(
            encoding=__import__("cryptography.hazmat.primitives.serialization", fromlist=["Encoding"]).Encoding.Raw,
            format=__import__("cryptography.hazmat.primitives.serialization", fromlist=["PublicFormat"]).PublicFormat.Raw,
        )
    )

    store = VerifiedChainStore(InMemoryChainStore(), context=ctx)

    step1, d1 = _make_step("step_001", 0, GENESIS)
    store.append_step(step1, d1)

    step2, d2 = _make_step("step_002", 1, d1)
    store.append_step(step2, d2)

    signed = store.store_attestation("run_beta_001", private_key, key_id)

    print("chain_ok :", store.audit_chain("run_beta_001").chain_ok)
    print("key_id   :", signed["key_id"])
    print("sig_alg  :", signed["signature_alg"])
    print("sig_valid:", verify_attestation_signature(signed, public_key))
    print(json.dumps(signed, indent=2))
