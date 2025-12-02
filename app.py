import os
from flask import Flask, request
from openai import OpenAI
import requests
from dotenv import load_dotenv

load_dotenv()  # loads .env file

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROUPME_BOT_ID = os.getenv("GROUPME_BOT_ID")

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

def send_groupme_message(text):
    url = "https://api.groupme.com/v3/bots/post"
    payload = {
        "bot_id": GROUPME_BOT_ID,
        "text": text[:995]
    }
    requests.post(url, json=payload)


@app.route("/groupme_callback", methods=["POST"])
def groupme_callback():
    data = request.json or {}
    text = data.get("text", "")
    sender_type = data.get("sender_type", "")

    # Ignore bot itself
    if sender_type == "bot":
        return "ok", 200

    # Only respond when leaders type mgmt:
    if not text.lower().startswith("mgmt:"):
        return "ok", 200

    user_question = text[5:].strip()

    # Call OpenAI
    completion = client.chat.completions.create(
        model="gpt-5.1-mini",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_question}
        ],
        temperature=0.2,
    )

    ai_response = completion.choices[0].message.content
    send_groupme_message(ai_response)

    return "ok", 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

