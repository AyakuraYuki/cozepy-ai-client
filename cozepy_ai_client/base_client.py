# -*- coding: utf-8 -*-


try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec

import logging
import time
from typing import Callable, Dict

import httpx

from .exceptions import (
    APIError,
    AuthenticationError,
    MaxRetriesExceededError,
    NetworkError,
    RateLimitError,
    ValidationError,
)
from .version import VERSION

P = ParamSpec("P")


class BaseClientMixin:
    """Mixin class providing common functionality for Coze AI clients."""

    def __init__(
            self,
            api_key: str,
            api_url: str,
            project_id: str,
            timeout: float = 600.0,
            max_retries: int = 3,
            retry_delay: float = 1.0,
            enable_logging: bool = False,
    ):
        """
        Initialize the base client.

        :param api_key: Bearer token for the Coze API
        :param api_url: Coze AI Agent/Workflow API url
        :param project_id: Coze AI Agent/Workflow project id
        :param timeout: Request timeout in seconds
        :param max_retries: Maximum number of retry attempts
        :param retry_delay: Delay between retries in seconds (exponential backoff)
        :param enable_logging: Enable detailed logging
        """
        if not api_key:
            raise ValueError("api_key is required")
        if not api_url:
            raise ValueError("api_url is required")
        if not project_id:
            raise ValueError("project_id is required")

        self.api_key = api_key
        self.api_url = api_url.rstrip("/")
        self.project_id = project_id
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        self.logger = logging.getLogger(
            f"cozepy_ai_client.{self.__class__.__name__.lower()}"
        )
        if enable_logging and not self.logger.handlers:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            handler = logging.StreamHandler()
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
        self.enable_logging = enable_logging

    def _get_headers(self, *, stream: bool = False) -> Dict[str, str]:
        """Build common request headers."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "User-Agent": f"coze-client-python/{VERSION}",
        }
        if stream:
            headers["Accept"] = "text/event-stream"
        return headers

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Raise typed exceptions for HTTP error status codes."""
        if response.status_code < 400:
            return

        try:
            error_data = response.json()
            message = error_data.get("message", f"HTTP {response.status_code}")
        except (ValueError, KeyError):
            error_data = None
            message = f"HTTP {response.status_code}"

        if self.enable_logging:
            self.logger.error(f"API error: {response.status_code} - {message}")

        if response.status_code == 401:
            raise AuthenticationError(message, response.status_code, error_data)
        elif response.status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(message, int(retry_after) if retry_after else None)
        elif response.status_code == 422:
            raise ValidationError(message, response.status_code, error_data)
        else:
            raise APIError(message, response.status_code, error_data)

    def _retry_request(
            self,
            request_func: Callable[P, httpx.Response],
            request_context: str | None = None,
            *args: P.args,
            **kwargs: P.kwargs,
    ) -> httpx.Response:
        """Retry a request with exponential backoff."""
        last_exception: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = request_func(*args, **kwargs)
                return response
            except (httpx.NetworkError, httpx.TimeoutException) as e:
                last_exception = e
                ctx = f" {request_context}" if request_context else ""

                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    self.logger.warning(
                        f"Request failed{ctx} (attempt {attempt + 1}/"
                        f"{self.max_retries + 1}): {e}. "
                        f"Retrying in {delay:.2f}s …"
                    )
                    time.sleep(delay)
                else:
                    self.logger.error(
                        f"Request failed{ctx} after "
                        f"{self.max_retries + 1} attempts: {e}"
                    )
                    if isinstance(e, httpx.TimeoutException):
                        raise TimeoutError(
                            f"Request timed out after {self.max_retries} retries{ctx}"
                        ) from e
                    raise NetworkError(
                        f"Network error after {self.max_retries} retries{ctx}: {e}"
                    ) from e

        if last_exception:
            raise last_exception
        raise MaxRetriesExceededError()
