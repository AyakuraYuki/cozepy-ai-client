# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, Dict, Generator, List

import httpx

from .base_client import BaseClientMixin
from .exceptions import StreamError
from .models import SSEEvent, PromptItem, build_prompt_list


class CozepyAiClient(BaseClientMixin):
    """
    Low-level synchronous Coze AI clients.

    Manages an :pymod:`httpx` connection pool and an exposes helpers for
    streaming (SSE) requests.
    """

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
        BaseClientMixin.__init__(
            self,
            api_key=api_key,
            api_url=api_url,
            project_id=project_id,
            timeout=timeout,
            max_retries=max_retries,
            retry_delay=retry_delay,
            enable_logging=enable_logging,
        )
        self._client = httpx.Client(
            timeout=httpx.Timeout(timeout, connect=10.0),
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def close(self):
        """Close the underlying HTTP connection pool."""
        if hasattr(self, "_client"):
            self._client.close()

    def _send_stream_request(
            self,
            method: str,
            body: Dict[str, Any] | None = None,
            **kwargs: Any,
    ) -> Generator[SSEEvent, None, None]:
        """
        Send a streaming request and yield parsed :class:`SSEEvent` objects.`

        This uses ``httpx.Client.stream`` so that bytes are consumed
        incrementally. Each ``data:`` line is parsed as JSON and wrapped in an
        :class:`SSEEvent`.
        """
        headers = self._get_headers(stream=True)

        if self.enable_logging:
            self.logger.info(f"Sending streaming {method} request to {self.api_url}")

        with self._client.stream(
                method, self.api_url, headers=headers, json=body, **kwargs,
        ) as response:
            if response.status_code >= 400:
                # Need to read the body to get error info.
                response.read()
                self._handle_error_response(response)

            for line in response.iter_lines():
                if not line or not line.startswith("data:"):
                    continue
                raw = line[len("data:"):].strip()
                if not raw:
                    continue
                try:
                    yield SSEEvent.from_json(raw)
                except Exception as exc:
                    raise StreamError(f"Failed to parse SSE data frame: {raw}") from exc


class ChatClient(CozepyAiClient):
    """
    High-level synchronous Coze AI clients.

    Wraps the low-level :class:`CozepyAiClient` and provides ergonomic methods
    for sending queries and iterating over streamed responses.

    Usage::

        with ChatClient(
            api_key="<JWT_TOKEN>",
            api_url="https://x.coze.site/stream_run",
            project_id="<PROJECT_ID>",
        ) as chat:
            for event in chat.stream_message("你好"):
                pass  # do something with event
    """

    def stream_message(
            self,
            query: str | List[PromptItem],
            *,
            session_id: str = None,
            message_type: str = "query",
            extra_payload: Dict[str, Any] | None = None,
    ) -> Generator[SSEEvent, None, None]:
        """
        Send a chat message and yield SSE events lazily.
        """
        payload: Dict[str, Any] = {
            "content": {
                "query": {
                    "prompt": build_prompt_list(query),
                }
            },
            "type": message_type,
            "project_id": self.project_id,
        }
        if session_id:
            payload["session_id"] = session_id
        if extra_payload:
            payload.update(extra_payload)

        yield from self._send_stream_request(method="POST", body=payload)
