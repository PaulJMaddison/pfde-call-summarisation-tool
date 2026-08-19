from __future__ import annotations


class CallSummariserError(Exception):
    """Base exception for expected call-summariser failures."""


class ConfigurationError(CallSummariserError):
    """Raised when required runtime configuration is invalid or missing."""


class TranscriptParseError(CallSummariserError, ValueError):
    """Raised when input text does not contain a usable transcript."""


class SummaryValidationError(CallSummariserError, ValueError):
    """Raised when a generated summary violates the output contract."""


class SummaryGenerationError(CallSummariserError, RuntimeError):
    """Raised when repeated generation attempts cannot produce a valid summary."""
