"""Errors raised by origin-protocol-core."""


class OriginError(Exception):
    """Base error for all Origin OS errors."""


class ManifestValidationError(OriginError):
    """Raised when a manifest fails structural validation."""


class DigestMismatchError(OriginError):
    """Raised when a computed digest does not match an expected digest."""


class ChainStoreError(OriginError):
    """Raised for chain-store backend errors."""
