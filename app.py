import os
from flask import Flask, request
from openai import OpenAI
import requests
from dotenv import load_dotenv

load_dotenv()  # loads .env file locally; on Render we use env vars

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROUPME_BOT_ID = os.getenv("GROUPME_BOT_ID")

print("Starting Manager.API bot...")
print(f"Has OPENAI_API_KEY? {'yes' if OPENAI_API_KEY else 'NO'}")
print(f"Has GROUPME_BOT_ID? {'yes' if GROUPME_BOT_ID else 'NO'}")

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are “Manager.API”, an AI assistant that supports Chick-fil-A leaders in a GroupMe chat.

Audience:
- Shift leaders and managers at Chick-fil-A.
- They need quick clarifications on policy, training, and communication.

Goals:
1. Answer questions about store policies, time off, availability, scheduling, minors, safety, and training.
2. Help leaders write clear, short messages leaders can paste into the chat.

Tone:
Professional, friendly, direct, and solution-focused.

If unsure about a policy, say:
"I'm not 100% sure based on the info I have. Please confirm with Ryan or check the official handbook."
"""

def send_groupme_message(text: str):
    """Send a message back into the GroupMe group using the bot."""
    if not GROUPME_BOT_ID:
        print("ERROR: GROUPME_BOT_ID is missing, cannot send message.")
        return

    url = "https://api.groupme.com/v3/bots/post"
    payload = {
        "bot_id": GROUPME_BOT_ID,
        "text": text[:995],  # GroupMe limit ~1000 chars
    }
    print(f"Sending message to GroupMe: {payload}")
    try:
        resp = requests.post(url, json=payload)
        print(f"GroupMe response status: {resp.status_code}, body: {resp.text}")
    except Exception as e:
        print(f"Error sending message to GroupMe: {e}")


@app.route("/", methods=["GET", "HEAD"])
def health_check():
    """Simple health check so / doesn't 404."""
    return "Manager.API is running", 200


@app.route("/groupme_callback", methods=["POST"])
def groupme_callback():
    data = request.json or {}
    print("Received callback payload:", data)

    text = data.get("text", "")
    sender_type = data.get("sender_type", "")

    # Ignore messages sent by the bot itself
    if sender_type == "bot":
        print("Ignoring bot message")
        return "ok", 200

    if not text:
        print("No text in message, ignoring")
        return "ok", 200

    # Only respond when leaders type mgmt:
    if not text.lower().startswith("mgmt:"):
        print("Message does not start with mgmt:, ignoring")
        return "ok", 200

    user_question = text[len("mgmt:"):].strip()
    print(f"User question: {user_question}")

    if not OPENAI_API_KEY:
        print("ERROR: OPENAI_API_KEY is missing")
        send_groupme_message("Manager.API error: OPENAI_API_KEY is not configured.")
        return "ok", 200

    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_question},
            ],
            temperature=0.2,
        )

        ai_response = completion.choices[0].message.content
        print("AI response:", ai_response)
        send_groupme_message(ai_response)

    except Exception as e:
        print("Error while calling OpenAI or sending response:", repr(e))
        send_groupme_message(
            "Manager.API had an error processing that request. "
            "Please let Ryan know and try again later."
        )

    return "ok", 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
