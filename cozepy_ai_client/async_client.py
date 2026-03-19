# -*- coding: utf-8 -*-

from __future__ import annotations

from typing import Any, AsyncGenerator, Dict, List

import httpx

from .base_client import BaseClientMixin
from .exceptions import StreamError
from .models import SSEEvent, PromptItem, build_prompt_list


class AsyncCozepyAiClient(BaseClientMixin):
    """
    Low-level asynchronous Coze AI clients.
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
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout, connect=10.0),
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    async def close(self):
        if hasattr(self, "_client"):
            await self._client.aclose()

    async def _send_stream_request(
            self,
            method: str,
            body: Dict[str, Any] | None = None,
            **kwargs: Any,
    ) -> AsyncGenerator[SSEEvent, None]:
        headers = self._get_headers(stream=True)

        if self.enable_logging:
            self.logger.info(f"Sending streaming {method} request to {self.api_url}")

        async with self._client.stream(
                method, self.api_url, headers=headers, json=body, **kwargs
        ) as response:
            if response.status_code >= 400:
                await response.aread()
                self._handle_error_response(response)

            async for line in response.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                raw = line[len("data:"):].strip()
                if not raw:
                    continue
                try:
                    yield SSEEvent.from_json(raw)
                except Exception as exc:
                    raise StreamError(f"Failed to parse SSE data frame: {raw}") from exc


class AsyncChatClient(AsyncCozepyAiClient):
    """
    High-level asynchronous Coze AI clients.

    Usage::

        with AsyncChatClient(
            api_key="<JWT_TOKEN>",
            api_url="https://x.coze.site/stream_run",
            project_id="<PROJECT_ID>",
        ) as chat:
            async for event in chat.stream_message("你好"):
                pass  # do something with event
    """

    async def stream_message(
            self,
            query: str | List[PromptItem],
            *,
            session_id: str = None,
            message_type: str = "query",
            extra_payload: Dict[str, Any] | None = None,
    ) -> AsyncGenerator[SSEEvent, None]:
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

        async for event in self._send_stream_request(
                method="POST", body=payload
        ):
            yield event
