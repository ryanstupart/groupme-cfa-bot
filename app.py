import os
from flask import Flask, request
from openai import OpenAI
import requests
from dotenv import load_dotenv

# Load .env locally; on Render we use service env vars
load_dotenv()

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROUPME_BOT_ID = os.getenv("GROUPME_BOT_ID")

print("Starting Manager.API bot...")
print(f"Has OPENAI_API_KEY? {'yes' if OPENAI_API_KEY else 'NO'}")
print(f"Has GROUPME_BOT_ID? {'yes' if GROUPME_BOT_ID else 'NO'}")

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are “Manager.API”, an AI assistant that supports Chick-fil-A leaders in a GroupMe chat.

AUDIENCE
- Team leaders, trainers, and managers at Chick-fil-A.
- You are ONLY for leaders, not for general team members.
- Assume messages starting with "mgmt:" are from leaders asking for help.

IDENTITY & PHILOSOPHY
- You operate with a LEADERSHIP mindset, not a “just manage the policy” mindset.
- A manager protects the business and enforces rules.
- A leader:
  - Leads by example.
  - Inspires growth and positive culture.
  - Reinforces the STANDARD so policies are naturally followed.
- Emphasize reinforcing standards over quoting policy.
- Maintain clarity, consistency, professionalism, and leadership presence.
- Never name specific individuals.
- You provide guidance and coaching, not decisions or approvals.

TONE & RESPONSE STYLE
- Professional, calm, clear, and confident.
- Speak like an experienced shift leader or director.
- Avoid slang, sarcasm, or emotional language.
- Preferred format:
  - 1–2 sentence leadership-focused summary.
  - 3–7 concise bullet points.
- Do NOT proactively offer to write messages.
- ONLY draft a message for the team if explicitly requested.

MESSAGE LENGTH & LIMITATIONS
- GroupMe has a practical limit of ~1,000 characters.
- Keep responses concise and structured.
- Avoid long paragraphs.
- If content would be too long, summarize.
- Never exceed 950 characters.

BILINGUAL (ENGLISH / SPANISH)
- You must understand both English and Spanish.
- Default behavior:
  - If the inquiry is primarily in Spanish, respond in Spanish.
  - If the inquiry is primarily in English, respond in English.
- If the leader explicitly requests a language (e.g., “en español”, “in English”), follow that request.
- If “both” or “bilingual” is requested:
  - Provide Spanish first, then English.
- When drafting a team message (only if asked):
  - Use the same language as the request unless otherwise specified.
- Do not translate proper nouns or tool names (HotSchedules, GroupMe, iPad).
- The activation keyword remains “mgmt:”.

WHEN YOU ARE UNSURE
- If information depends on context or is incomplete:
  - Say: “I’m not completely certain based on the information I have. Please confirm with store leadership or check the current handbook.”
- For serious matters (safety, harassment, discrimination, injuries, theft, legal/HR issues):
  - Do NOT give detailed guidance.
  - Direct the leader to store leadership.

SCOPE OF SUPPORT
You assist leaders with:
1) Policies and standards (as defined below).
2) Training and coaching guidance.
3) Coverage and scheduling logic (high-level).
4) Safety and professionalism reminders.
5) Leadership decision-making support (not approvals).

POLICIES & STANDARDS
Use the following as your source of truth. Do not invent rules. If something is not defined, stay general and advise checking with leadership.

1) RESPECT & CONDUCT
- “Guest first, always” applies to guests and team members.
- Treat everyone with honor, dignity, and respect.
- No bullying, harassment, intimidation, teasing, or throwing items.
- No hostile work environment.
- Profanity is prohibited in all languages.
- Concerns should be escalated to leadership.

2) CLOCKING IN & READINESS
- Clock in only when fully ready:
  - Uniform complete, shirt tucked, belt on, name tag attached.
  - Personal items stored in a locker.
- Clock in at FRONT COUNTER registers only.
- Do not clock in and then finish getting ready.

3) UNIFORM & NAME TAGS
- Required: Chick-fil-A polo, Oobe pants, belt, name tag, approved non-slip shoes.
- Missing name tag must be reported before clock-in.
- Replacement name tags cost $5.

4) PERSONAL DEVICES
- Phones are not allowed while working.
- Enforcement:
  - 1st offense: warning.
  - 2nd offense: confiscation.
  - Refusal: write-up and sent home.
- Expo exception: phone may be taken on first offense due to trust level.

5) DRINK POLICY
- One medium tea or fountain drink per shift.
- Premium drinks must be purchased.

6) BREAKS
- 5+ hours: one 30-minute break.
- Under 5 hours: 15-minute break if business allows.

7) BREAK FOOD & DISCOUNTS
- One entrée and one medium or small side per shift.
- Excludes 30-count nuggets and 10-count strips.
- Off-the-clock: 50% off one entrée and one side per day.
- Desserts and seasonal items are full price.

8) FOOD POLICY & WASTE
- Food is never free.
- Extra food must be purchased, logged as waste, or disposed of.
- Taking food without paying:
  - 1st offense: must pay.
  - 2nd offense: meeting with leadership.

9) SHIFT CHECK-IN
- Team members must check in with a leader at the start and end of each shift.

10) ATTENDANCE & CALLOUTS
- Team members are responsible for finding coverage.
- Leaders are not required to find coverage.
- Sick callouts require a doctor’s note.
- No-call/no-show results in a write-up.

11) SHIFT SWAPS (TEAM MEMBERS)
- The scheduled employee owns the shift.
- Coverage must match:
  - Exact start time.
  - Required skill set.
- Process:
  1) Release shift in HotSchedules.
  2) Ask in GroupMe.
  3) Optional direct outreach.
  4) Coverage is valid only after leader approval.
- If no coverage is found, the shift remains the employee’s responsibility unless a legitimate emergency exists.

12) MINORS & COVERAGE (GEORGIA — 15-YEAR-OLDS)
When school is in session:
- Max 3 hours per school day.
- Max 18 hours per school week.
- Work window: 7 AM–7 PM.
- Cannot work or cover shifts past 7 PM.
- Work permit required.

When school is not in session:
- Up to 8 hours/day, 40 hours/week.
- Cannot work before 7 AM.
- Federal rules may allow up to 9 PM in summer.

Leaders must ensure all coverage complies with minor labor laws.

13) LEADERSHIP COVERAGE
- Leaders must be covered by another leader-level team member.
- Trainers and team leaders cannot be covered by regular employees.
- Acceptable coverage:
  - Trainer → trainer, team leader, or higher.
  - Team leader → team leader or manager.
- Exceptions require store leadership approval.

14) TRAINEES
- Trainees are on restricted schedules.
- Cannot pick up regular shifts or cover leadership roles.
- Training schedules align with trainer availability.
- If a trainee calls out, leaders decide next steps.

15) LANGUAGE & PROFESSIONALISM
- Profanity is prohibited.
- Leaders must model professional language and behavior.

16) STAFFING MODEL: FOH (8 PM–9 PM STANDARD)
- With 10 FOH team members:
  - 2 iPad order takers (two active lanes).
  - 1 drinks.
  - 1 desserts.
  - 2 baggers.
  - 1 register.
  - 1 window.
  - 1 stuffer.
  - 1 floating support.

Drive-Thru Flow:
- Two lanes for order taking.
- Lanes merge into ONE at meal delivery.
- Window and stuffer alternate ownership of each order.

9–10 PM staffing remains in beta; leaders use discretion.

LEADERSHIP EXPECTATIONS
- Lead by example.
- Reinforce standards consistently.
- Communicate clearly and proactively.
- Consider guest impact, team morale, safety, and compliance.
- Provide guidance, not commands.

WHAT YOU MUST NOT DO
- Do NOT decide discipline, approve schedules, or give legal/HR advice.
- Do NOT name individuals.
- Redirect sensitive issues to store leadership.

REMEMBER
- Your purpose is to support leaders by reinforcing standards, building clarity, and strengthening culture.
"""


def send_groupme_message(text: str) -> None:
    if not GROUPME_BOT_ID:
        print("ERROR: GROUPME_BOT_ID is missing, cannot send message.")
        return

    url = "https://api.groupme.com/v3/bots/post"
    payload = {"bot_id": GROUPME_BOT_ID, "text": text[:995]}
    print(f"Sending message to GroupMe: {payload}")

    try:
        resp = requests.post(url, json=payload)
        print(f"GroupMe response status: {resp.status_code}, body: {resp.text}")
    except Exception as e:
        print(f"Error sending message to GroupMe: {e}")

@app.route("/", methods=["GET", "HEAD"])
def health_check():
    return "Manager.API is running", 200

@app.route("/groupme_callback", methods=["GET", "POST"])
def groupme_callback():
    if request.method == "GET":
        print("Received GET /groupme_callback")
        return "groupme_callback is alive", 200

    data = request.json or {}
    print("Received callback payload:", data)

    text = data.get("text", "")
    sender_type = data.get("sender_type", "")

    if sender_type == "bot":
        return "ok", 200

    if not text:
        return "ok", 200

    if not text.lower().startswith("mgmt:"):
        return "ok", 200

    user_question = text[len("mgmt:"):].strip()
    print(f"User question: {user_question}")

    if not OPENAI_API_KEY:
        send_groupme_message("Manager.API error: OPENAI_API_KEY missing.")
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
        print("Error calling OpenAI:", repr(e))
        send_groupme_message(
            "Manager.API had an error processing that request. Please let a leader know."
        )

    return "ok", 200
    
import datetime
import random

SCHEDULE_SECRET = os.getenv("SCHEDULE_SECRET", "")

AFFIRMATIONS = [
    "Leadership Affirmation: Stay present, stay consistent. Standards rise when we do.",
    "Leadership Affirmation: Clear expectations + calm tone = a stronger shift.",
    "Leadership Affirmation: Reinforce the standard early so the shift runs smoother later.",
    "Leadership Affirmation: Lead with clarity before urgency. Calm direction sets the tone.",
    "Leadership Affirmation: Standards are strongest when modeled, not just explained.",
    "Leadership Affirmation: Consistency today prevents correction tomorrow.",
    "Leadership Affirmation: Your presence sets the ceiling for the shift.",
    "Leadership Affirmation: Strong leaders simplify the moment without lowering the standard.",
    "Leadership Affirmation: Clear expectations create confident teams.",
    "Leadership Affirmation: When leaders stay steady, the team follows.",
    "Leadership Affirmation: Reinforce the standard early to avoid friction later.",
    "Leadership Affirmation: Leadership is shown most in routine moments.",
    "Leadership Affirmation: Calm leadership keeps the shift moving forward.",
    "Leadership Affirmation: Standards rise when leaders are visible and engaged.",
    "Leadership Affirmation: Lead with purpose, not pressure.",
    "Leadership Affirmation: A composed leader creates a composed team.",
    "Leadership Affirmation: Consistency builds trust faster than intensity.",
    "Leadership Affirmation: Your example teaches more than your words.",
    "Leadership Affirmation: Strong leadership removes confusion, not accountability.",
    "Leadership Affirmation: Set the tone early and maintain it with presence.",
    "Leadership Affirmation: Leadership is choosing clarity over reaction.",
    "Leadership Affirmation: Standards are reinforced through repetition and example.",
    "Leadership Affirmation: When leaders stay aligned, the shift stays controlled.",
    "Leadership Affirmation: Calm direction creates momentum.",
    "Leadership Affirmation: Reinforcing standards protects both people and process.",
    "Leadership Affirmation: Strong leaders guide before they correct.",
    "Leadership Affirmation: The team mirrors what leadership tolerates.",
    "Leadership Affirmation: Lead intentionally, even in small decisions.",
    "Leadership Affirmation: Consistent leadership builds predictable excellence.",
    "Leadership Affirmation: Standards feel natural when leadership is steady.",
    "Leadership Affirmation: Presence is a leadership tool—use it often.",
    "Leadership Affirmation: Clear communication prevents repeated correction.",
    "Leadership Affirmation: Leadership is clarity under pressure.",
    "Leadership Affirmation: Reinforcing standards builds confidence across the shift.",
    "Leadership Affirmation: Strong leaders coach in the moment, not after the fact.",
    "Leadership Affirmation: Calm leadership keeps systems working.",
    "Leadership Affirmation: Standards are upheld through daily habits.",
    "Leadership Affirmation: A leader’s tone sets the emotional pace of the shift.",
    "Leadership Affirmation: Consistency builds credibility.",
    "Leadership Affirmation: Lead with patience and purpose.",
    "Leadership Affirmation: Reinforcing the standard creates stability.",
    "Leadership Affirmation: Leadership is being dependable in every moment.",
    "Leadership Affirmation: Clear direction keeps the team focused.",
    "Leadership Affirmation: Presence matters more than volume.",
    "Leadership Affirmation: Strong leaders stay composed when the pace increases.",
    "Leadership Affirmation: Standards are sustained through steady leadership.",
    "Leadership Affirmation: Lead in a way others can follow confidently.",
    "Leadership Affirmation: Consistency is the foundation of trust.",
    "Leadership Affirmation: Reinforcing expectations early sets the shift up for success.",
    "Leadership Affirmation: Leadership is guiding, not rushing.",
    "Leadership Affirmation: Calm leadership keeps decisions clean.",
    "Leadership Affirmation: Standards feel achievable when leaders model them.",
    "Leadership Affirmation: Strong leaders reduce uncertainty.",
    "Leadership Affirmation: Presence and clarity keep the team aligned.",
    "Leadership Affirmation: Leadership is steady even when the environment is not.",
    "Leadership Affirmation: Reinforcing standards creates long-term success.",
    "Leadership Affirmation: Clear leadership prevents reactive leadership.",
    "Leadership Affirmation: Lead with intention, not urgency.",
    "Leadership Affirmation: Standards are protected through consistency.",
    "Leadership Affirmation: Strong leaders stay visible and engaged.",
    "Leadership Affirmation: Calm direction supports strong execution.",
    "Leadership Affirmation: Leadership is consistency in action.",
    "Leadership Affirmation: Reinforce expectations with clarity and respect.",
    "Leadership Affirmation: Presence builds confidence across the team.",
    "Leadership Affirmation: Strong leadership creates predictable results.",
    "Leadership Affirmation: Standards rise when leaders remain steady.",
    "Leadership Affirmation: Leadership is calm guidance in busy moments.",
    "Leadership Affirmation: Clear expectations create smooth operations.",
    "Leadership Affirmation: Reinforcing the standard builds momentum.",
    "Leadership Affirmation: Strong leaders correct early and coach calmly.",
    "Leadership Affirmation: Leadership is clarity without compromise.",
    "Leadership Affirmation: Presence reinforces accountability.",
    "Leadership Affirmation: Standards thrive under consistent leadership.",
    "Leadership Affirmation: Calm leadership keeps the shift controlled.",
    "Leadership Affirmation: Lead with patience and precision.",
    "Leadership Affirmation: Strong leaders maintain clarity under pressure.",
    "Leadership Affirmation: Reinforcing standards strengthens the team.",
    "Leadership Affirmation: Leadership is steady influence, not force.",
    "Leadership Affirmation: Presence keeps systems aligned.",
    "Leadership Affirmation: Clear leadership supports confident execution.",
    "Leadership Affirmation: Standards are reinforced through daily leadership.",
    "Leadership Affirmation: Strong leaders guide the shift, not chase it.",
    "Leadership Affirmation: Calm presence steadies the team.",
    "Leadership Affirmation: Leadership is consistency in every interaction.",
    "Leadership Affirmation: Reinforcing expectations builds operational trust.",
    "Leadership Affirmation: Strong leadership creates smooth transitions.",
    "Leadership Affirmation: Lead with clarity, consistency, and purpose.",
    "Leadership Affirmation: Standards are strongest when leadership is visible.",
    "Leadership Affirmation: Calm leadership creates lasting results.",
    "Leadership Affirmation: Leadership is reinforcing the standard every day.",
    "Leadership Affirmation: Strong leaders set direction and maintain it."

]

TRAINER_REMINDER = "Trainers: Please remember to submit training reports for any training completed today. Thank you!"

HOLIDAYS = {
    "12-25": "Merry Christmas! Thank you for leading with excellence and reinforcing standards.",
    "01-01": "Happy New Year! Let’s lead with clarity, consistency, and strong standards.",
}

@app.route("/scheduled/send", methods=["GET"])
def scheduled_send():
    token = request.args.get("token", "")
    kind = (request.args.get("kind", "") or "").lower().strip()

    if not SCHEDULE_SECRET or token != SCHEDULE_SECRET:
        return "Unauthorized", 401

    # Choose message based on kind
    if kind == "trainer_reminder":
        msg = TRAINER_REMINDER

    elif kind == "affirmation":
        mmdd = datetime.datetime.now().strftime("%m-%d")
        msg = HOLIDAYS.get(mmdd, random.choice(AFFIRMATIONS))

    else:
        return "Bad Request: kind must be affirmation or trainer_reminder", 400

    send_groupme_message(msg)
    return "OK", 200




if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
