"""Bridge persistent WhatsApp conversations to CindyBakesAgent."""

from __future__ import annotations

from pathlib import Path

from agent import CindyBakesAgent
from database import DEFAULT_DATABASE_PATH
from notifications import WhatsAppCloudNotifier, _whatsapp_number
from whatsapp_database import (
    complete_event, latest_order_id, load_conversation, save_conversation,
)


class WhatsAppAgentService:
    def __init__(self, sender: WhatsAppCloudNotifier, database_path: str | Path = DEFAULT_DATABASE_PATH,
                 agent_factory=CindyBakesAgent):
        self.sender = sender
        self.database_path = database_path
        self.agent_factory = agent_factory

    def process_text(self, message_id: str, wa_id: str, phone_number: str, text: str) -> None:
        conversation = load_conversation(wa_id, self.database_path)
        agent = self.agent_factory(whatsapp_wa_id=wa_id)
        if conversation:
            agent.restore_state(conversation["draft"], conversation["input_items"])
        try:
            reply = agent.respond(text)
            draft, input_items = agent.export_state()
            save_conversation(
                wa_id, phone_number, draft, input_items,
                latest_order_id(wa_id, self.database_path), self.database_path,
            )
            self.sender.send_text(_whatsapp_number(phone_number), reply)
            complete_event(message_id, database_path=self.database_path)
        except Exception as error:
            complete_event(message_id, "FAILED", str(error)[:500], self.database_path)
            raise
