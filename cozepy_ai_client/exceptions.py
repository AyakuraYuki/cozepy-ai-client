# -*- coding: utf-8 -*-

from typing import Any, Dict


class CozepyAiClientError(Exception):
    """Base exception for all Coze AI client errors."""

    def __init__(
            self,
            message: str,
            status_code: int | None = None,
            response: Dict[str, Any] | None = None,
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response


class APIError(CozepyAiClientError):
    """Raised when the API returns an error response."""

    def __init__(
            self,
            message: str,
            status_code: int | None = None,
            response: Dict[str, Any] | None = None,
    ):
        super().__init__(message, status_code, response)
        self.status_code = status_code


class AuthenticationError(CozepyAiClientError):
    """Raised when authentication fails."""
    pass


class RateLimitError(CozepyAiClientError):
    """Raised when rate limit is exceeded."""

    def __init__(
            self,
            message: str = "Rate limit exceeded",
            retry_after: int | None = None
    ):
        super().__init__(message)
        self.retry_after = retry_after


class MaxRetriesExceededError(CozepyAiClientError):
    """Raised when max retries exceeded."""

    def __init__(
            self,
            message: str = "Request failed after retries"
    ):
        super().__init__(message)


class ValidationError(CozepyAiClientError):
    """Raised when request validation fails."""
    pass


class NetworkError(CozepyAiClientError):
    """Raised when network-related errors occur."""
    pass


class ClientTimeoutError(CozepyAiClientError):
    """Raised when request times out."""
    pass


class StreamError(CozepyAiClientError):
    """Raised when SSE stream parsing fails."""
    pass
