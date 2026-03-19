# -*- coding: utf-8 -*-

from cozepy_ai_client import TextPrompt, build_prompt_list


class TestPromptModels:
    def test_text_prompt_to_dict(self):
        p = TextPrompt(text="hi")
        assert p.to_dict() == {"type": "text", "content": {"text": "hi"}}

    def test_build_prompt_list_from_string(self):
        p = build_prompt_list("hi")
        assert p == [{"type": "text", "content": {"text": "hi"}}]

    def test_build_prompt_list_from_items(self):
        items = [TextPrompt(text="hi"), TextPrompt(text="bye")]
        p = build_prompt_list(items)
        assert len(p) == 2
        assert p[0]["type"] == "text"
        assert p[1]["type"] == "text"

    def test_build_prompt_list_from_empty_string(self):
        p = build_prompt_list("")
        assert p == [{"type": "text", "content": {"text": ""}}]
