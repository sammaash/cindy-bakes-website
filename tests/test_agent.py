"""Regression tests for CindyBakesAgent conversation-history replay."""

import os
import unittest
from unittest.mock import MagicMock

os.environ.setdefault("OPENAI_API_KEY", "test-key-not-a-real-secret")

from agent import CindyBakesAgent, _strip_output_only_fields


class FakeOutputItem:
    """Stand-in for an SDK response.output item (has model_dump, like the real ones)."""

    def __init__(self, data):
        self._data = data
        self.type = data.get("type")

    def model_dump(self, mode="json"):
        return dict(self._data)


class StripOutputOnlyFieldsTests(unittest.TestCase):
    def test_strips_status_and_id_from_sdk_object(self):
        item = FakeOutputItem({
            "id": "msg_123", "type": "message", "role": "assistant",
            "status": "completed", "content": [{"type": "output_text", "text": "hi"}],
        })
        result = _strip_output_only_fields(item)

        self.assertNotIn("status", result)
        self.assertNotIn("id", result)
        self.assertEqual(result["role"], "assistant")

    def test_strips_status_and_id_from_plain_dict(self):
        item = {"id": "msg_456", "type": "message", "role": "assistant", "status": "completed"}
        result = _strip_output_only_fields(item)

        self.assertNotIn("status", result)
        self.assertNotIn("id", result)


class RestoreStateSanitizesHistoryTests(unittest.TestCase):
    def test_restore_state_strips_status_from_saved_history(self):
        agent = CindyBakesAgent()
        saved_input_items = [
            {"role": "user", "content": "Hi"},
            {
                "id": "msg_789", "type": "message", "role": "assistant", "status": "completed",
                "content": [{"type": "output_text", "text": "Welcome!"}],
            },
        ]

        agent.restore_state(draft=None, input_items=saved_input_items)

        for item in agent.input_items:
            self.assertNotIn("status", item)
            self.assertNotIn("id", item)


def _fake_message_response(text, message_id):
    """Build a fake responses.create() return value with no tool calls."""
    output_item = FakeOutputItem({
        "id": message_id, "type": "message", "role": "assistant", "status": "completed",
        "content": [{"type": "output_text", "text": text, "annotations": []}],
    })
    response = MagicMock()
    response.output = [output_item]
    response.output_text = text
    return response


class TwoTurnConversationReplayTests(unittest.TestCase):
    """Simulates the reported production bug end-to-end without calling OpenAI."""

    def test_second_turn_never_replays_status_or_id(self):
        agent = CindyBakesAgent()
        agent.client.responses.create = MagicMock(
            return_value=_fake_message_response(
                "Hi! Welcome to Cindy Bakes. What cake would you like to order?", "msg_turn1"
            )
        )
        reply1 = agent.respond("Hi")
        self.assertIn("Welcome", reply1)

        draft, input_items = agent.export_state()

        # Simulate WhatsAppAgentService reloading the saved conversation for the next webhook call.
        agent2 = CindyBakesAgent()
        agent2.restore_state(draft, input_items)

        captured_calls = []

        def fake_create(**kwargs):
            captured_calls.append(kwargs["input"])
            return _fake_message_response("Great, what weight would you like?", "msg_turn2")

        agent2.client.responses.create = MagicMock(side_effect=fake_create)

        reply2 = agent2.respond("Vanilla 2kg")

        self.assertEqual(reply2, "Great, what weight would you like?")
        sent_input = captured_calls[0]
        for item in sent_input:
            if isinstance(item, dict):
                self.assertNotIn("status", item)
                self.assertNotIn("id", item)


if __name__ == "__main__":
    unittest.main()
