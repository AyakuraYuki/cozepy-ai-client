# cozepy-ai-client

> This is a community-made package.

A Python client library for interacting with Coze Agent/Workflow APIs. Supports both synchronous and asynchronous usage with Server-Sent Events (SSE) streaming.

## Requirements

- Python 3.10+

## Installation

```bash
pip install cozepy-ai-client
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv pip install cozepy-ai-client
```

## Quick Start

### Synchronous

```python
from cozepy_ai_client import ChatClient

with ChatClient(
    api_key="your-api-key",
    api_url="https://your-coze-agent-endpoint",
    project_id="your-project-id",
) as chat:
    for event in chat.stream_message(query="Hello"):
        if event.is_answer:
            print(event.answer_text, end="", flush=True)
        elif event.is_message_end:
            break
```

### Asynchronous

```python
import asyncio
from cozepy_ai_client.async_client import AsyncChatClient

async def main():
    async with AsyncChatClient(
        api_key="your-api-key",
        api_url="https://your-coze-agent-endpoint",
        project_id="your-project-id",
    ) as chat:
        async for event in chat.stream_message(query="Hello"):
            if event.is_answer:
                print(event.answer_text, end="", flush=True)
            elif event.is_message_end:
                break

asyncio.run(main())
```

## Client Configuration

Both `ChatClient` and `AsyncChatClient` accept the following parameters:

| Parameter        | Type    | Default | Description                                           |
|------------------|---------|---------|-------------------------------------------------------|
| `api_key`        | `str`   | —       | Bearer token for Coze API authentication              |
| `api_url`        | `str`   | —       | Agent/Workflow API endpoint URL                       |
| `project_id`     | `str`   | —       | Coze AI project ID                                    |
| `timeout`        | `float` | `600.0` | Request timeout in seconds                            |
| `max_retries`    | `int`   | `3`     | Maximum number of retry attempts on failure           |
| `retry_delay`    | `float` | `1.0`   | Initial delay between retries (exponential backoff)   |
| `enable_logging` | `bool`  | `False` | Enable detailed logging for debugging                 |

## Sending Messages

### `stream_message()`

| Parameter       | Type                          | Default     | Description                                   |
|-----------------|-------------------------------|-------------|-----------------------------------------------|
| `query`         | `str` or `List[TextPrompt]`   | —           | Query text or a list of prompt items          |
| `session_id`    | `str` or `None`               | `None`      | Session ID for multi-turn conversations       |
| `message_type`  | `str`                         | `"query"`   | Message type sent to the API                  |
| `extra_payload` | `Dict[str, Any]` or `None`    | `None`      | Additional fields merged into the request body|

### Using prompt lists

```python
from cozepy_ai_client import ChatClient, TextPrompt, build_prompt_list

prompts = build_prompt_list([
    TextPrompt(text="Summarize the following:"),
    TextPrompt(text="Python is a programming language..."),
])

with ChatClient(...) as chat:
    for event in chat.stream_message(query=prompts):
        ...
```

## SSE Events

Each iteration yields an `SSEEvent` object with the following helpers:

| Property / Method     | Description                                      |
|-----------------------|--------------------------------------------------|
| `event_type`          | `EventType` enum value                           |
| `is_answer`           | `True` if the event contains an answer chunk     |
| `answer_text`         | The text content of an answer event              |
| `is_message_start`    | `True` if this is the start-of-message event     |
| `is_message_end`      | `True` if this is the end-of-message event       |
| `content`             | Full `EventContent` with all possible payloads   |

### Event Types

| `EventType`        | Description                                  |
|--------------------|----------------------------------------------|
| `MESSAGE_START`    | Signals the start of a response stream       |
| `ANSWER`           | A chunk of the answer text                   |
| `TOOL_REQUEST`     | The agent is calling a tool                  |
| `TOOL_RESPONSE`    | Result returned from a tool call             |
| `MESSAGE_END`      | Signals the end of a response stream         |
| `ERROR`            | An error occurred during streaming           |

### Handling all event types

```python
from cozepy_ai_client import ChatClient, EventType

with ChatClient(...) as chat:
    for event in chat.stream_message(query="What tools do you have?"):
        match event.event_type:
            case EventType.ANSWER:
                print(event.answer_text, end="", flush=True)
            case EventType.TOOL_REQUEST:
                tc = event.content.tool_request
                print(f"\n[Tool call] {tc.tool_name}({tc.parameters})")
            case EventType.MESSAGE_END:
                me = event.content.message_end
                print(f"\n[Done] tokens used: {me.token_cost.total_tokens}")
                break
            case EventType.ERROR:
                print(f"\n[Error] {event.content.error.error_message}")
                break
```

## Error Handling

The library raises specific exceptions for different failure scenarios:

| Exception                  | Description                                     |
|----------------------------|-------------------------------------------------|
| `APIError`                 | Non-2xx HTTP response from the API              |
| `AuthenticationError`      | HTTP 401 — invalid or missing API key           |
| `RateLimitError`           | HTTP 429 — rate limit exceeded                  |
| `ValidationError`          | HTTP 422 — request validation failed            |
| `MaxRetriesExceededError`  | All retry attempts exhausted                    |
| `NetworkError`             | Network connectivity failure                    |
| `ClientTimeoutError`       | Request timed out                               |
| `StreamError`              | Failed to parse an SSE frame                    |

```python
from cozepy_ai_client import ChatClient
from cozepy_ai_client.exceptions import AuthenticationError, RateLimitError, APIError

try:
    with ChatClient(...) as chat:
        for event in chat.stream_message(query="Hello"):
            ...
except AuthenticationError:
    print("Invalid API key.")
except RateLimitError as e:
    print(f"Rate limited. Retry after {e.retry_after}s.")
except APIError as e:
    print(f"API error {e.status_code}: {e}")
```

## Development

```bash
git clone https://github.com/AyakuraYuki/cozepy-ai-client.git
cd cozepy-ai-client
uv sync
```

Run tests (requires environment variables `API_URL`, `TOKEN`, and `PROJECT_ID`):

```bash
uv run pytest tests/
```

## License

[MIT](./LICENSE) © 2026 Ayakura Yuki
