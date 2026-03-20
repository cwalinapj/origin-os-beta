"""Shared protocol-core types and verification result models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Callable

JsonDict = dict[str, Any]
Digest = str  # hex-encoded SHA-256


class ResultStatus(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"


@dataclass
class ValidationResult:
    """Outcome of a single validation check."""

    check: str
    status: ResultStatus
    message: str = ""

    @property
    def passed(self) -> bool:
        return self.status == ResultStatus.PASS

    @classmethod
    def ok(cls, check: str, message: str = "") -> "ValidationResult":
        return cls(check=check, status=ResultStatus.PASS, message=message)

    @classmethod
    def fail(cls, check: str, message: str) -> "ValidationResult":
        return cls(check=check, status=ResultStatus.FAIL, message=message)


@dataclass
class StepVerificationReport:
    """Aggregated verification results for a single step."""

    step_index: int
    results: list[ValidationResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return all(r.passed for r in self.results)


@dataclass
class ChainVerificationSummary:
    """Top-level result of verify_chain()."""

    run_id: str
    step_reports: list[StepVerificationReport] = field(default_factory=list)
    chain_results: list[ValidationResult] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        steps_ok = all(s.passed for s in self.step_reports)
        chain_ok = all(r.passed for r in self.chain_results)
        return steps_ok and chain_ok

    @property
    def status(self) -> ResultStatus:
        return ResultStatus.PASS if self.passed else ResultStatus.FAIL


if TYPE_CHECKING:
    from .manifest import ManifestV1

Validator = Callable[..., ValidationResult]
ChainValidator = Callable[..., ValidationResult]
