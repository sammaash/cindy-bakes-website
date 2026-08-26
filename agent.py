"""LLM orchestration for one Cindy Bakes customer conversation."""

import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from business_rules import BUSINESS_RULES, DELIVERY_ORIGIN
from catalog import CAKE_PRICES
from database import create_pending_order, get_payment_status
from delivery import calculate_delivery_cost
from order import OrderDraft
from pricing import calculate_quote

SYSTEM_PROMPT = """You are Cindy Bakes' friendly sales assistant in a command-line chat.
Have a natural, concise conversation. Never show a numbered menu unless the customer asks.
Never invent, estimate, or alter prices, deposits, delivery costs, business rules,
availability, or order status. Use tools for every Cindy Bakes price or policy answer.
Use update_order_draft whenever a customer supplies order details, and get_order_draft
to see what remains. Use calculate_current_quote for every monetary amount; never do
money arithmetic yourself. Custom flavours and custom cakes require human pricing.
Do not quote them. For delivery orders, do not estimate the delivery distance or delivery cost.
Just collect a specific delivery location and store it in the order. The delivery fee is KSh 32 per km,
but the exact travel cost is confirmed later by staff. Do not mention a calculated distance or price.

For a standard cake order collect the fields in this order: name, flavour, weight (1, 2, or 3 kg),
quantity, date needed in a clear day/month format or YYYY-MM-DD, personalisation type,
fulfilment (delivery or pickup), delivery location when applicable, and phone number.
Do not summarize, quote, or confirm an order while any required field is still missing. In particular,
never summarize or confirm an order before the personalisation type is known. Always ask for
personalisation type before you summarize or confirm an order. If the customer asks for a topper,
store non_edible_topper. If they ask for an edible print, store edible_print. If they say no
personalisation, store none. If they only say they want personalisation, ask whether they want a
non-edible topper or an edible print before updating the draft. If fulfilment is delivery, ask for a
specific location such as an estate, street, or landmark. Ask only the next required question, not a list
of questions. When complete, calculate the quote and clearly give the subtotal, required 70% deposit,
and the remaining balance after the deposit. Explain that the exact delivery charge will be confirmed
later by staff, and that the deposit must be paid at least 3 days before the delivery or pickup date.
Only call confirm_order after the customer explicitly confirms a complete order and quote. It creates
an order awaiting human payment verification; explain that the order is pending until staff verify
the 70% deposit. Never say a payment has been received or verified unless get_payment_status returns
payment_verified as true. You cannot verify payments yourself.
"""

EMPTY_PARAMETERS = {"type": "object", "properties": {}, "additionalProperties": False}
ORDER_ID_PARAMETERS = {
    "type": "object",
    "properties": {"order_id": {"type": "integer"}},
    "required": ["order_id"],
    "additionalProperties": False,
}
UPDATE_PROPERTIES = {
    "customer_name": {"type": "string"}, "flavour": {"type": "string"},
    "weight_kg": {"type": "integer"}, "quantity": {"type": "integer"},
    "date_needed": {"type": "string"},
    "personalisation_type": {
        "type": "string", "enum": ["none", "non_edible_topper", "edible_print"]
    },
    "fulfilment": {"type": "string"},
    "delivery_location": {"type": "string"}, "phone_number": {"type": "string"},
}
TOOLS = [
    {"type": "function", "name": "get_catalogue", "description": "Get approved standard flavours, weights, and prices.", "parameters": EMPTY_PARAMETERS},
    {"type": "function", "name": "get_business_rules", "description": "Get approved Cindy Bakes business rules.", "parameters": EMPTY_PARAMETERS},
    {"type": "function", "name": "update_order_draft", "description": "Store only order details explicitly supplied by the customer. Omit unknown fields.", "parameters": {"type": "object", "properties": UPDATE_PROPERTIES, "additionalProperties": False}},
    {"type": "function", "name": "get_order_draft", "description": "Get current order details and exact missing fields.", "parameters": EMPTY_PARAMETERS},
    {"type": "function", "name": "calculate_delivery_cost", "description": "Get the actual road-driving distance and delivery cost from the fixed origin to the customer's delivery location.", "parameters": {"type": "object", "properties": {"delivery_location": {"type": "string"}}, "required": ["delivery_location"], "additionalProperties": False}},
    {"type": "function", "name": "calculate_current_quote", "description": "Calculate the approved cake, personalisation, and delivery total from the current draft using the real route distance when delivery is required.", "parameters": EMPTY_PARAMETERS},
    {"type": "function", "name": "confirm_order", "description": "Persist the complete, customer-confirmed order as pending human payment verification.", "parameters": EMPTY_PARAMETERS},
    {"type": "function", "name": "get_payment_status", "description": "Get the database-confirmed payment status for an order. Use before making any payment-verification claim.", "parameters": ORDER_ID_PARAMETERS},
]


class CindyBakesAgent:
    """Keeps LLM message history and order state for one CLI session."""

    def __init__(self, whatsapp_wa_id: str | None = None):
        load_dotenv()
        if not os.getenv("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is missing. Add it to .env before starting the bot.")
        self.client = OpenAI()
        self.model = os.getenv("OPENAI_MODEL", "gpt-5.6")
        self.draft = OrderDraft()
        self.input_items = []
        self.whatsapp_wa_id = whatsapp_wa_id

    def restore_state(self, draft: dict | None, input_items: list | None) -> None:
        """Restore a WhatsApp conversation without changing terminal behavior."""
        if draft:
            self.draft.update(**{key: value for key, value in draft.items() if hasattr(self.draft, key)})
        self.input_items = input_items or []

    def export_state(self) -> tuple[dict, list]:
        """Return serializable draft and response input state."""
        serialized_items = [
            item.model_dump(mode="json") if hasattr(item, "model_dump") else item
            for item in self.input_items
        ]
        return self.draft.as_dict(), serialized_items

    def _run_tool(self, name: str, arguments: dict) -> dict:
        if name == "get_catalogue":
            return {"catalogue": CAKE_PRICES, "currency": "KSh"}
        if name == "get_business_rules":
            return BUSINESS_RULES
        if name == "update_order_draft":
            return self.draft.update(**arguments)
        if name == "get_order_draft":
            return self.draft.as_dict()
        if name == "calculate_delivery_cost":
            try:
                return calculate_delivery_cost(arguments["delivery_location"], DELIVERY_ORIGIN)
            except (ValueError, RuntimeError) as error:
                return {"error": str(error)}
        if name == "calculate_current_quote":
            missing = self.draft.missing_fields()
            if missing:
                return {"error": "Order details are incomplete.", "missing_fields": missing}
            try:
                delivery_cost = None
                delivery_distance_km = None
                delivery_rate_per_km = 32
                if self.draft.fulfilment == "delivery":
                    if not self.draft.delivery_location:
                        return {"error": "Please provide a more specific delivery location before quoting."}
                    delivery_cost = None
                    delivery_distance_km = None
                    delivery_rate_per_km = 32
                return calculate_quote(
                    self.draft.flavour,
                    self.draft.weight_kg,
                    self.draft.quantity,
                    self.draft.personalisation_type,
                    delivery_cost=delivery_cost,
                    delivery_distance_km=delivery_distance_km,
                    delivery_rate_per_km=delivery_rate_per_km,
                )
            except (ValueError, RuntimeError) as error:
                return {"error": str(error)}
        if name == "confirm_order":
            missing = self.draft.missing_fields()
            if missing:
                return {"error": "Order details are incomplete.", "missing_fields": missing}
            try:
                delivery_cost = None
                delivery_distance_km = None
                delivery_rate_per_km = 32
                if self.draft.fulfilment == "delivery":
                    if not self.draft.delivery_location:
                        return {"error": "Please provide a more specific delivery location before confirming the order."}
                    delivery_cost = None
                    delivery_distance_km = None
                    delivery_rate_per_km = 32
                quote = calculate_quote(
                    self.draft.flavour,
                    self.draft.weight_kg,
                    self.draft.quantity,
                    self.draft.personalisation_type,
                    delivery_cost=delivery_cost,
                    delivery_distance_km=delivery_distance_km,
                    delivery_rate_per_km=delivery_rate_per_km,
                )
                quote["delivery_status"] = "manual_confirmation_required"
                draft = self.draft.as_dict()
                draft["whatsapp_wa_id"] = self.whatsapp_wa_id
                return create_pending_order(draft, quote)
            except (ValueError, RuntimeError) as error:
                return {"error": str(error)}
        if name == "get_payment_status":
            status = get_payment_status(arguments["order_id"])
            return status or {"error": "Order not found."}
        return {"error": "Unknown tool."}

    def respond(self, customer_message: str) -> str:
        """Process one customer message and return the natural-language reply."""
        self.input_items.append({"role": "user", "content": customer_message})
        for _ in range(6):
            response = self.client.responses.create(
                model=self.model,
                instructions=SYSTEM_PROMPT,
                input=self.input_items,
                tools=TOOLS,
            )
            self.input_items.extend(response.output)
            tool_calls = [item for item in response.output if item.type == "function_call"]
            if not tool_calls:
                return response.output_text or "I’m sorry, I couldn’t prepare a response. Please try again."
            for tool_call in tool_calls:
                result = self._run_tool(tool_call.name, json.loads(tool_call.arguments))
                self.input_items.append({
                    "type": "function_call_output",
                    "call_id": tool_call.call_id,
                    "output": json.dumps(result),
                })
        return "I’m sorry, I couldn’t complete that request. Please try again or talk to a human."
