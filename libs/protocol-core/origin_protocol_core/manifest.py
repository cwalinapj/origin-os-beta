"""ManifestV1 — the core execution step record."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .canonical import canonical_digest, canonical_json
from .errors import ManifestValidationError
from .types import Digest, JsonDict

_REQUIRED_FIELDS = frozenset(
    {"run_id", "step_index", "agent_id", "action", "inputs", "outputs", "timestamp_utc"}
)


@dataclass
class ManifestV1:
    """A single agent execution step.

    *previous_step_digest* is ``None`` for the first step in a chain and the
    SHA-256 hex digest of the previous step's canonical JSON for all subsequent
    steps.
    """

    run_id: str
    step_index: int
    agent_id: str
    action: str
    inputs: JsonDict
    outputs: JsonDict
    timestamp_utc: str
    previous_step_digest: Digest | None = None
    metadata: JsonDict = field(default_factory=dict)

    # ------------------------------------------------------------------
    # Serialisation
    # ------------------------------------------------------------------

    def to_canonical_dict(self) -> JsonDict:
        """Return the canonical dict used for digest computation.

        All fields are included; keys will be sorted by :func:`canonical_json`.
        """
        return {
            "run_id": self.run_id,
            "step_index": self.step_index,
            "agent_id": self.agent_id,
            "action": self.action,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "timestamp_utc": self.timestamp_utc,
            "previous_step_digest": self.previous_step_digest,
            "metadata": self.metadata,
        }

    def to_dict(self) -> JsonDict:
        """Return a plain dict representation (same as canonical dict)."""
        return self.to_canonical_dict()

    def digest(self) -> Digest:
        """Return the SHA-256 hex digest of this manifest's canonical JSON."""
        return canonical_digest(self.to_canonical_dict())

    def canonical_json(self) -> str:
        """Return the canonical JSON string for this manifest."""
        return canonical_json(self.to_canonical_dict())

    # ------------------------------------------------------------------
    # Deserialisation
    # ------------------------------------------------------------------

    @classmethod
    def from_dict(cls, data: JsonDict) -> "ManifestV1":
        """Construct a :class:`ManifestV1` from a plain dictionary.

        Raises :exc:`ManifestValidationError` if required fields are missing or
        have incorrect types.
        """
        missing = _REQUIRED_FIELDS - data.keys()
        if missing:
            raise ManifestValidationError(
                f"Missing required fields: {', '.join(sorted(missing))}"
            )
        if not isinstance(data["step_index"], int):
            raise ManifestValidationError("step_index must be an integer")
        if data["step_index"] < 0:
            raise ManifestValidationError("step_index must be >= 0")

        return cls(
            run_id=str(data["run_id"]),
            step_index=int(data["step_index"]),
            agent_id=str(data["agent_id"]),
            action=str(data["action"]),
            inputs=dict(data["inputs"]),
            outputs=dict(data["outputs"]),
            timestamp_utc=str(data["timestamp_utc"]),
            previous_step_digest=data.get("previous_step_digest"),
            metadata=dict(data.get("metadata") or {}),
        )
