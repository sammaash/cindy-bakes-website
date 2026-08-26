"""Command-line conversational sales agent for Cindy Bakes."""

import re

from agent import CindyBakesAgent


def safe_error_message(error):
    """Return an error message with common secrets redacted."""
    message = str(error)
    message = re.sub(r"sk-[A-Za-z0-9_-]+", "[REDACTED API KEY]", message)
    message = re.sub(r"(?i)bearer\s+[^\s,]+", "Bearer [REDACTED]", message)
    message = re.sub(r"(?i)(api[_ -]?key\s*[=:]\s*)[^\s,]+", r"\1[REDACTED]", message)
    return message or "No error message was provided."


def show_api_error(error):
    """Show useful diagnostic details without exposing credentials."""
    status_code = getattr(error, "status_code", None)
    print(f"Cindy Bakes: I couldn't complete that request. ({type(error).__name__})")
    print(f"Status code: {status_code if status_code is not None else 'Not available'}")
    print(f"Safe error message: {safe_error_message(error)}")


def run_bot():
    """Run one natural customer conversation until the user exits."""
    try:
        agent = CindyBakesAgent()
    except RuntimeError as error:
        print(f"Setup error: {error}")
        return

    print("Cindy Bakes: Hello! How can I help you today?")
    while True:
        customer_message = input("You: ").strip()
        if customer_message.lower() in {"exit", "quit", "goodbye"}:
            print("Cindy Bakes: Thank you for chatting with Cindy Bakes. Goodbye!")
            break
        if not customer_message:
            continue
        try:
            print(f"Cindy Bakes: {agent.respond(customer_message)}")
        except Exception as error:
            show_api_error(error)
            print("Cindy Bakes: I’m having trouble responding right now. Please try again or talk to a human.")


if __name__ == "__main__":
    run_bot()
