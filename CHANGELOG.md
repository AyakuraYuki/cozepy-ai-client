## 0.1.0

### Features

**Client**

- `ChatClient`: synchronous client with context-manager (`with`) support.
- `AsyncChatClient`: asynchronous client with async context-manager (`async with`) support.
- `stream_message()` method on both clients for SSE streaming requests; accepts a plain string or a `List[TextPrompt]` as the query.
- Multi-turn conversation support via the `session_id` parameter.
- `extra_payload` parameter to merge arbitrary fields into the request body.
- Configurable `timeout` (default 600 s), `max_retries` (default 3), and `retry_delay` (default 1 s).
- Exponential back-off retry logic for network errors and timeouts.
- Optional structured logging via the `enable_logging` flag.
- HTTP/2 support through `httpx[http2]`.

**SSE response models** (parsed from `data:` frames)

- `SSEEvent` — primary event object yielded on each iteration; carries convenience properties `is_answer`, `answer_text`, `is_message_start`, and `is_message_end`.
- `EventType` — string enum: `MESSAGE_START`, `ANSWER`, `TOOL_REQUEST`, `TOOL_RESPONSE`, `MESSAGE_END`, `ERROR`.
- `EventContent` — union container for all event payloads.
- `MessageStartContent` — start-of-stream metadata (`local_msg_id`, `msg_id`, `execute_id`).
- `MessageEndContent` — end-of-stream summary including `token_cost` and `time_cost_ms`.
- `TokenCost` — token usage statistics (`input_tokens`, `output_tokens`, `total_tokens`).
- `ErrorContent` — error payload (`code`, `error_msg`).
- `ToolRequestContent` — tool-call request payload (`tool_name`, `parameters`, parallel/index metadata).
- `ToolResponseContent` — tool-call result payload (`result`, `code`, `time_cost_ms`).

**Request helpers**

- `TextPrompt` — Pydantic model serializing to the API's `{"type": "text", "content": {"text": "..."}}` format.
- `build_prompt_list()` — normalizes a plain string or a list of `PromptItem` instances into the API list format.

**Exception hierarchy**

- `CozepyAiClientError` — base class for all library exceptions.
- `APIError` — non-2xx HTTP response.
- `AuthenticationError` — HTTP 401 (invalid or missing API key).
- `RateLimitError` — HTTP 429; exposes `retry_after` from the `Retry-After` response header.
- `ValidationError` — HTTP 422 (request validation failure).
- `MaxRetriesExceededError` — all retry attempts exhausted.
- `NetworkError` — underlying network connectivity failure.
- `ClientTimeoutError` — request timed out.
- `StreamError` — SSE frame parsing failure.
