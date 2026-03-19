# -*- coding: utf-8 -*-

import os
import unittest

from cozepy_ai_client import ChatClient

API_URL = os.environ.get("API_URL")
TOKEN = os.environ.get("TOKEN")
PROJECT_ID = os.environ.get("PROJECT_ID")


class TestClient(unittest.TestCase):
    def setUp(self):
        self.client = ChatClient(
            api_key=TOKEN,
            api_url=API_URL,
            project_id=PROJECT_ID,
            enable_logging=True,
        )

    def test_stream_message(self):
        for event in self.client.stream_message(
                query="Hello",
                session_id="abc-123"
        ):
            if event.is_answer:
                print(event.answer_text, end="")
            elif event.is_message_end:
                break
        print()
        print("finished")
