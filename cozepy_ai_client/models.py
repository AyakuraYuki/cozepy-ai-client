# -*- coding: utf-8 -*-

from enum import Enum
from typing import Dict, Any, List, Union

from pydantic import BaseModel, Field


# ===========================================================================
# Request helpers
# ===========================================================================

class TextPrompt(BaseModel):
    """
    A single text prompt item.

    Serializes to::

        {"type": "text", "content": {"text": "..."}}
    """

    text: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": "text",
            "content": {"text": self.text}
        }


PromptItem = Union[TextPrompt]


def build_prompt_list(prompts: str | List[PromptItem]) -> List[Dict[str, Any]]:
    """
    Normalize a user-friendly prompt value into the API list format.

    Accepts either a plain string which converted to a single
    :class:`TextPrompt` or a list of :class:`PromptItem` instances.
    """
    if isinstance(prompts, str):
        prompts = [TextPrompt(text=prompts)]
    return [p.to_dict() for p in prompts]


# ===========================================================================
# SSE response models
# ===========================================================================

class EventType(str, Enum):
    """Known values of the top-level ``type`` field."""

    MESSAGE_START = "message_start"
    MESSAGE_END = "message_end"
    ANSWER = "answer"
    ERROR = "error"
    TOOL_REQUEST = "tool_request"
    TOOL_RESPONSE = "tool_response"


class MessageStartContent(BaseModel):
    """Payload of ``content.message_start``."""

    local_msg_id: str = ""
    msg_id: str = ""
    execute_id: str = ""


class TokenCost(BaseModel):
    """Token usage statistics returned in ``message_end``."""

    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0


class MessageEndContent(BaseModel):
    """Payload of ``content.message_end``."""

    code: str = "0"
    message: str = ""
    token_cost: TokenCost = Field(default_factory=TokenCost)
    time_cost_ms: int = 0


class ErrorContent(BaseModel):
    """Payload of ``content.error``."""

    local_msg_id: str = ""
    code: int = 0
    error_msg: str = ""


class ToolRequestContent(BaseModel):
    """Payload of ``content.tool_request``."""

    tool_call_id: str = ""
    tool_name: str = ""
    parameters: Dict[str, Any] = Field(default_factory=dict)
    is_parallel: bool | None = None
    index: int | None = None
    stream_parameters: str | None = None


class ToolResponseContent(BaseModel):
    """Payload of ``content.tool_response``."""

    tool_call_id: str = ""
    code: str = ""
    message: str = ""
    result: str = ""
    time_cost_ms: int | None = None
    tool_name: str | None = None


class EventContent(BaseModel):
    """
    The ``content`` object present in every SSE frame.

    Depending on the event ``type`` only a subset of fields is populated;
    the rest stay ``None``.
    """

    answer: str | None = None
    thinking: Dict[str, Any] | None = None
    tool_request: ToolRequestContent | None = None
    tool_response: ToolResponseContent | None = None
    error: ErrorContent | None = None
    message_start: MessageStartContent | None = None
    message_end: MessageEndContent | None = None


class SSEEvent(BaseModel):
    """
    A single parsed SSE ``data:`` frame.

    This is the primary model that callers iterate over when consuming
    a stream. Every ``data:`` line emitted by the Coze API is
    deserialized into one ``SSEEvent`` object.

    Example::

        for event in chat.stream("Hi"):
            if event.is_answer and event.answer_text:
                print(event.answer_text, end="")
    """

    type: str  # Event type - typically one of :class:`EventType` values.

    session_id: str = ""
    query_msg_id: str = ""
    reply_id: str = ""
    msg_id: str = ""
    sequence_id: int = 0
    finish: bool = False
    content: EventContent = Field(default_factory=EventContent)
    log_id: str = ""

    @property
    def is_answer(self) -> bool:
        """``True`` when this frame carries an answer text chunk."""
        return self.type == EventType.ANSWER

    @property
    def answer_text(self) -> str:
        """Shortcut for getting the answer chunk, or empty string."""
        return self.content.answer or ""

    @property
    def is_message_start(self) -> bool:
        return self.type == EventType.MESSAGE_START

    @property
    def is_message_end(self) -> bool:
        return self.type == EventType.MESSAGE_END

    @classmethod
    def from_json(cls, raw_json: str) -> "SSEEvent":
        """Deserialize a raw JSON string from frames into an :class:`SSEEvent`."""
        return cls.model_validate_json(raw_json)
