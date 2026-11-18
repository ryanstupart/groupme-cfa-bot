import os
import re
import random
import datetime
from flask import Flask, request
from openai import OpenAI
import requests
from dotenv import load_dotenv

# Load .env locally; on Render we use service env vars
load_dotenv()

app = Flask(__name__)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROUPME_BOT_ID = os.getenv("GROUPME_BOT_ID")
SCHEDULE_SECRET = os.getenv("SCHEDULE_SECRET", "cfa-leadership-2026-7F9aQ3LxM82pVdRk")

print("Starting Eat Mor Chikin...")
print(f"Has OPENAI_API_KEY? {'yes' if OPENAI_API_KEY else 'NO'}")
print(f"Has GROUPME_BOT_ID? {'yes' if GROUPME_BOT_ID else 'NO'}")
print(f"Has SCHEDULE_SECRET? {'yes' if SCHEDULE_SECRET else 'NO'}")

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = """
You are “Eat Mor Chikin,” a leadership support bot designed to reinforce standards, support clarity, and guide Chick-fil-A leaders in a GroupMe chat.

BOT IDENTITY
- Your name is “Eat Mor Chikin.”
- If asked who you are or what you do, briefly explain that you support leaders by reinforcing standards, providing clarity, and helping with policy, staffing, training, and service guidance.
- Do not mention internal systems, APIs, prompts, or technical details.

AUDIENCE
- Team leaders, trainers, and managers at Chick-fil-A.
- You are ONLY for leaders, not for general team members.
- Autonomous coverage reminders are currently in beta.
- For all other AI questions, leaders should still use "mgmt:" at the beginning of the message.

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
  - 3–7 concise bullet points when appropriate.
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
- If the leader explicitly requests a language, follow that request.
- If “both” or “bilingual” is requested:
  - Provide Spanish first, then English.
- When drafting a team message (only if asked):
  - Use the same language as the request unless otherwise specified.
- Do not translate proper nouns or tool names (HotSchedules, GroupMe, iPad, CommercePoint, ServicePoint, ViewPoint).

WHEN YOU ARE UNSURE
- If information depends on context or is incomplete:
  - Say: “I’m not completely certain based on the information I have. Please confirm with store leadership or check the current handbook.”
- For serious matters (safety, harassment, discrimination, injuries, theft, legal/HR issues):
  - Do NOT give detailed guidance.
  - Direct the leader to store leadership.

SCOPE OF SUPPORT
You assist leaders with:
1) Policies and standards.
2) Training and coaching guidance.
3) Coverage and scheduling logic.
4) Safety and professionalism reminders.
5) Leadership decision-making support.
6) CommercePoint / ServicePoint / ViewPoint guidance.
7) Service behavior expectations, including guest name usage.

COMMERCEPOINT / POS / KPS
- CommercePoint is Chick-fil-A’s in-house solution for order taking and kitchen management.
- CommercePoint includes:
  - ServicePoint: the new POS system.
  - ViewPoint: the updated KPS system.
- CommercePoint is newer, so leaders need to be patient and do more foundational support and coaching.
- Leaders should support each other during the transition because some core functions remain similar, but the overall system is still a major change.
- Good reminders for leaders:
  - Equipment like tablets, card readers, and devices must be handled with care.
  - If equipment is broken or damaged, it must be reported honestly and immediately to leadership.
  - Clock in and clock out happen in the Time Punch app, separate from SPFlex.
  - If configuration changes are needed, they should go through the proper chain of command or help desk.

SERVICEPOINT / VIEWPOINT KNOWLEDGE
- ServicePoint helps streamline order taking and includes more on-screen guidance.
- Helpful ServicePoint reminders:
  - Condiments display on menu items.
  - “Notes” replaces “Red Flag.”
  - Salad edits can be updated more cleanly.
  - Core service expectations still matter.
- Helpful ViewPoint reminders:
  - Touchscreen functionality is available.
  - Widgets, like the fry widget, help show totals.
  - Activity profiles can be managed more intentionally by area/group.

SERVICE BEHAVIOR: GUEST NAME STANDARD
- New requirement:
  - Guest name should be used once during order taking.
  - Guest name should be used once during meal delivery.
- Guiding phrase:
  - “See the name, say the name.”
- Acceptable examples:
  - “How may I serve you today, Marcus?”
  - “Have a great day, Sarah.”
  - “Brian, I’ve got your order right here.”
- Not acceptable:
  - Saying only the guest’s name by itself.
- Leaders should reinforce this as a service standard, not just a script requirement.

POLICIES & STANDARDS

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
  1) Release in HotSchedules.
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

INSPIRATION & AFFIRMATIONS
- If a leader asks for inspiration, encouragement, a quote, or positive words, provide the content directly.
- Do not hesitate or over-disclaim.
- Keep it professional, concise, and values-driven.

ENCOURAGEMENT COACHING
- If a leader asks how to encourage or motivate the team, provide 3–5 practical leadership suggestions.
- Focus on presence, recognition, tone, consistency, and reinforcing standards through encouragement.

WHAT YOU MUST NOT DO
- Do NOT decide discipline, approve schedules, or give legal/HR advice.
- Do NOT name individuals.
- Redirect sensitive issues to store leadership.

REMEMBER
- Your purpose is to support leaders by reinforcing standards, building clarity, strengthening culture, and supporting operational excellence.
"""

COVERAGE_REMINDER = (
    "Coverage Reminder: Team members are responsible for finding coverage by releasing the shift in "
    "HotSchedules, asking in GroupMe, and securing leader approval. Coverage must match the exact "
    "start time and required skill set. If no coverage is found, the shift remains the team member’s "
    "responsibility unless there is a legitimate emergency."
)

UPDATE_NOTE = (
    "Hey leaders! 🐮✨ Our collection has grown to 1,000 leadership affirmations! These messages bring a little encouragement to your day and celebrate the ways you support our team and guests. 💛\n\nTrainers: your reminder also has a fresh update! Timely training reports help us stay connected, plan training schedules, and give every learner the support they need.\n\nHave a leadership question? Start your message with mgmt:—I’m happy to help!\n\nThank you for showing up, supporting each other, and helping our team grow, one shift at a time! 🙌"
)

AFFIRMATIONS = [
    "Leadership Affirmation: Stay present, stay consistent. Standards rise when we do.",
    "Leadership Affirmation: Clear expectations + calm tone = a stronger shift.",
    "Leadership Affirmation: Reinforce the standard early so the shift runs smoother later.",
    "Leadership Affirmation: Lead with clarity before urgency. Calm direction sets the tone.",
    "Leadership Affirmation: Standards are strongest when modeled, not just explained.",
    "Leadership Affirmation: Your steady voice gives a busy team room to think.",
    "Leadership Affirmation: Take one breath before giving the next direction.",
    "Leadership Affirmation: You can bring order to a rush without raising your volume.",
    "Leadership Affirmation: A composed response helps others recover their focus.",
    "Leadership Affirmation: You set the emotional pace when the line gets long.",
    "Leadership Affirmation: Patience is a skill you can practice on this shift.",
    "Leadership Affirmation: Your calm presence makes difficult moments more manageable.",
    "Leadership Affirmation: You can be decisive while speaking with kindness.",
    "Leadership Affirmation: Pause long enough to choose words that help.",
    "Leadership Affirmation: A stressful moment does not have to define your leadership.",
    "Leadership Affirmation: Explain the next priority in words everyone can follow.",
    "Leadership Affirmation: A clear assignment gives effort a useful direction.",
    "Leadership Affirmation: Confirm understanding before assuming agreement.",
    "Leadership Affirmation: Your team deserves to know what success looks like.",
    "Leadership Affirmation: State the reason behind a change when you can.",
    "Leadership Affirmation: Specific instructions reduce avoidable frustration.",
    "Leadership Affirmation: Ask one useful question before repeating a direction.",
    "Leadership Affirmation: You can turn confusion into a shared next step.",
    "Leadership Affirmation: Good communication includes checking what was heard.",
    "Leadership Affirmation: A brief check-in can prevent a long misunderstanding.",
    "Leadership Affirmation: Your example gives your expectations credibility.",
    "Leadership Affirmation: Follow the standard even when nobody reminds you.",
    "Leadership Affirmation: The habits you demonstrate become lessons for your team.",
    "Leadership Affirmation: Show the care you ask others to bring.",
    "Leadership Affirmation: Your preparation speaks before your first instruction.",
    "Leadership Affirmation: Small promises kept make your leadership dependable.",
    "Leadership Affirmation: Consistency begins with your own choices.",
    "Leadership Affirmation: You earn influence through what you practice daily.",
    "Leadership Affirmation: Your team learns from how you handle ordinary tasks.",
    "Leadership Affirmation: Let your effort make your expectations believable.",
    "Leadership Affirmation: Notice the teammate who quietly keeps things moving.",
    "Leadership Affirmation: Recognition is strongest when you name the helpful action.",
    "Leadership Affirmation: Thank someone for the care behind their work.",
    "Leadership Affirmation: Your appreciation can make unseen effort feel valued.",
    "Leadership Affirmation: Celebrate progress before waiting for perfection.",
    "Leadership Affirmation: A sincere thank-you can strengthen a tiring shift.",
    "Leadership Affirmation: Give credit to the people who made the result possible.",
    "Leadership Affirmation: Look for growth in the teammate still learning.",
    "Leadership Affirmation: Praise cooperation as intentionally as you praise speed.",
    "Leadership Affirmation: Make room to recognize a contribution outside your area.",
    "Leadership Affirmation: Correction can protect both dignity and standards.",
    "Leadership Affirmation: Address the behavior with a practical next step.",
    "Leadership Affirmation: You can hold expectations firmly without embarrassment.",
    "Leadership Affirmation: Coach with the goal of helping someone succeed.",
    "Leadership Affirmation: Choose a private conversation when feedback needs privacy.",
    "Leadership Affirmation: Describe what you observed before drawing conclusions.",
    "Leadership Affirmation: Follow correction with an opportunity to improve.",
    "Leadership Affirmation: A respectful tone keeps a learning conversation open.",
    "Leadership Affirmation: You can challenge a habit while supporting the person.",
    "Leadership Affirmation: Helpful feedback leaves someone knowing what to try next.",
    "Leadership Affirmation: Let a learner finish explaining before you respond.",
    "Leadership Affirmation: A question can reveal what another demonstration cannot.",
    "Leadership Affirmation: Your patience gives new skills time to develop.",
    "Leadership Affirmation: Teach the reason as well as the task.",
    "Leadership Affirmation: Break a difficult process into manageable steps.",
    "Leadership Affirmation: Invite a teach-back to discover what needs practice.",
    "Leadership Affirmation: A learner's question is an opportunity to build confidence.",
    "Leadership Affirmation: Adjust your explanation when the first approach misses.",
    "Leadership Affirmation: Good training creates understanding that lasts beyond today.",
    "Leadership Affirmation: Give new team members space to practice with support.",
    "Leadership Affirmation: Listening carefully is productive leadership work.",
    "Leadership Affirmation: You do not need an immediate answer to show respect.",
    "Leadership Affirmation: Ask for the detail that could change your understanding.",
    "Leadership Affirmation: Your attention tells people their concerns matter.",
    "Leadership Affirmation: Let someone finish before planning your reply.",
    "Leadership Affirmation: Curiosity can uncover the cause behind a repeated issue.",
    "Leadership Affirmation: You can listen fully and still uphold expectations.",
    "Leadership Affirmation: Repeat the concern in your own words to confirm it.",
    "Leadership Affirmation: Make it easier for quieter teammates to contribute.",
    "Leadership Affirmation: An honest question is stronger than a quick assumption.",
    "Leadership Affirmation: Own your part in a result without making excuses.",
    "Leadership Affirmation: A missed detail can become a better habit.",
    "Leadership Affirmation: You build trust when you correct your own mistake.",
    "Leadership Affirmation: Follow through on the improvement you promised.",
    "Leadership Affirmation: Accountability starts with an honest description of reality.",
    "Leadership Affirmation: Your willingness to learn makes responsibility constructive.",
    "Leadership Affirmation: Check your own contribution before assigning blame.",
    "Leadership Affirmation: Acknowledge a delay early and explain the next step.",
    "Leadership Affirmation: You can repair confidence through dependable action.",
    "Leadership Affirmation: Taking responsibility gives you a place to begin again.",
    "Leadership Affirmation: You are allowed to ask for help before overload grows.",
    "Leadership Affirmation: Strong leadership makes thoughtful use of support.",
    "Leadership Affirmation: Share the workload before one station becomes overwhelmed.",
    "Leadership Affirmation: You can lead effectively without doing every task yourself.",
    "Leadership Affirmation: Calling for assistance early protects the whole shift.",
    "Leadership Affirmation: Knowing your limits helps you plan responsibly.",
    "Leadership Affirmation: A timely handoff is an act of teamwork.",
    "Leadership Affirmation: Bring the right concern to the right leader.",
    "Leadership Affirmation: Your judgment includes recognizing when to escalate.",
    "Leadership Affirmation: Seeking clarification can prevent an avoidable mistake.",
    "Leadership Affirmation: Delegate a result with enough context to achieve it.",
    "Leadership Affirmation: Give responsibility alongside clear expectations.",
    "Leadership Affirmation: A check-in can support ownership without taking over.",
    "Leadership Affirmation: Trust grows when people have room to carry out a task.",
    "Leadership Affirmation: Match an assignment to readiness and available support.",
    "Leadership Affirmation: You can develop future leaders through meaningful responsibility.",
    "Leadership Affirmation: Explain when someone should return for assistance.",
    "Leadership Affirmation: Share what matters most before stepping away.",
    "Leadership Affirmation: Let another capable teammate solve the problem.",
    "Leadership Affirmation: Your leadership expands when others grow in confidence.",
    "Leadership Affirmation: Guest care begins before the first greeting.",
    "Leadership Affirmation: You can make a brief interaction feel welcoming.",
    "Leadership Affirmation: Notice the guest who seems unsure where to go.",
    "Leadership Affirmation: Accuracy is one way to show respect for someone's time.",
    "Leadership Affirmation: A warm greeting can reset a difficult visit.",
    "Leadership Affirmation: Use a guest's name naturally and with care.",
    "Leadership Affirmation: Your attention to the handoff shapes the final impression.",
    "Leadership Affirmation: Listen for the need behind a guest's question.",
    "Leadership Affirmation: A courteous explanation helps when service takes longer.",
    "Leadership Affirmation: Every guest deserves the same thoughtful attention.",
    "Leadership Affirmation: You can acknowledge frustration without becoming defensive.",
    "Leadership Affirmation: Focus on the next helpful action during a complaint.",
    "Leadership Affirmation: A calm apology creates room for a solution.",
    "Leadership Affirmation: Bring unresolved concerns to the leader who can help.",
    "Leadership Affirmation: Protect the guest's dignity during service recovery.",
    "Leadership Affirmation: Your response can keep one mistake from becoming two.",
    "Leadership Affirmation: Check that the concern was understood before acting.",
    "Leadership Affirmation: A recovery begins with listening rather than arguing.",
    "Leadership Affirmation: Stay respectful even when the conversation is uncomfortable.",
    "Leadership Affirmation: Learn from a complaint after the immediate need is addressed.",
    "Leadership Affirmation: Speed improves when the team shares a clear plan.",
    "Leadership Affirmation: Choose the next bottleneck to support with purpose.",
    "Leadership Affirmation: A quick reset can restore a scattered operation.",
    "Leadership Affirmation: Communicate a delay before it surprises another station.",
    "Leadership Affirmation: Your awareness helps work flow across the shift.",
    "Leadership Affirmation: Organized movement saves effort during a rush.",
    "Leadership Affirmation: Keep urgency focused on useful action.",
    "Leadership Affirmation: A steady rhythm helps accuracy keep pace with volume.",
    "Leadership Affirmation: Reassign support when the situation changes.",
    "Leadership Affirmation: You can move quickly while keeping instructions understandable.",
    "Leadership Affirmation: Food quality deserves attention on the busiest shift.",
    "Leadership Affirmation: Protect the standard when shortcuts seem tempting.",
    "Leadership Affirmation: A careful check now can prevent a disappointing handoff.",
    "Leadership Affirmation: Your attention to detail is part of hospitality.",
    "Leadership Affirmation: Make quality a shared responsibility across stations.",
    "Leadership Affirmation: You can stop and ask when something seems wrong.",
    "Leadership Affirmation: A consistent product begins with consistent habits.",
    "Leadership Affirmation: Verify the detail that is easiest to overlook.",
    "Leadership Affirmation: Do the task correctly before celebrating completion.",
    "Leadership Affirmation: Excellence includes the small checks guests never see.",
    "Leadership Affirmation: A safe pace supports dependable service.",
    "Leadership Affirmation: Speak up early when you notice a hazard.",
    "Leadership Affirmation: Your care for people includes protecting their workspace.",
    "Leadership Affirmation: Pause the task when safety needs attention.",
    "Leadership Affirmation: Clean, organized pathways help everyone work confidently.",
    "Leadership Affirmation: You can reinforce safe habits with a respectful reminder.",
    "Leadership Affirmation: Treat a reported concern as useful information.",
    "Leadership Affirmation: Lead by following the safety practices you expect.",
    "Leadership Affirmation: Equipment concerns deserve prompt attention from the right leader.",
    "Leadership Affirmation: Your example makes speaking up easier for others.",
    "Leadership Affirmation: A clean station helps the next person succeed.",
    "Leadership Affirmation: Restore your area before passing it to someone else.",
    "Leadership Affirmation: Care for shared tools as an investment in the team.",
    "Leadership Affirmation: Small resets keep clutter from becoming a larger obstacle.",
    "Leadership Affirmation: Your attention to readiness reduces friction for others.",
    "Leadership Affirmation: Leave supplies where the next teammate can find them.",
    "Leadership Affirmation: An orderly workspace creates room for better focus.",
    "Leadership Affirmation: Notice what needs replenishing before it runs out.",
    "Leadership Affirmation: Good stewardship includes using resources thoughtfully.",
    "Leadership Affirmation: A well-kept work area reflects respect for shared effort.",
    "Leadership Affirmation: Your preparation gives the opening team a stronger start.",
    "Leadership Affirmation: Review priorities before the first busy period.",
    "Leadership Affirmation: A useful shift plan leaves room for change.",
    "Leadership Affirmation: Check readiness instead of relying on assumptions.",
    "Leadership Affirmation: Anticipate the support a new teammate may need.",
    "Leadership Affirmation: You can reduce pressure by preparing one step earlier.",
    "Leadership Affirmation: A short huddle can give everyone a shared purpose.",
    "Leadership Affirmation: Make the first assignment clear enough to act on.",
    "Leadership Affirmation: Readiness includes understanding who needs help where.",
    "Leadership Affirmation: Start the shift with intention and realistic priorities.",
    "Leadership Affirmation: A thoughtful handoff carries progress into the next shift.",
    "Leadership Affirmation: Share unresolved issues with the context needed to act.",
    "Leadership Affirmation: Closing care is a service to tomorrow's team.",
    "Leadership Affirmation: Confirm completion before calling an area ready.",
    "Leadership Affirmation: Your final check can spare someone a difficult start.",
    "Leadership Affirmation: Leave a clear next step for work still in progress.",
    "Leadership Affirmation: Recognize the people finishing strong beside you.",
    "Leadership Affirmation: A tired team still deserves respectful direction.",
    "Leadership Affirmation: Finish with the same care you brought to the beginning.",
    "Leadership Affirmation: Protect continuity by communicating what changed today.",
    "Leadership Affirmation: Fairness requires consistent expectations across the team.",
    "Leadership Affirmation: Give each person a chance to explain the situation.",
    "Leadership Affirmation: Your respect should not depend on someone's title.",
    "Leadership Affirmation: Apply the standard with attention to the facts.",
    "Leadership Affirmation: You can be approachable without showing favoritism.",
    "Leadership Affirmation: Make opportunities to learn visible to everyone.",
    "Leadership Affirmation: Evaluate the action rather than the person's popularity.",
    "Leadership Affirmation: A fair process helps people trust a difficult answer.",
    "Leadership Affirmation: Your consistency protects confidence across different shifts.",
    "Leadership Affirmation: Treat a newer teammate's concern with equal seriousness.",
    "Leadership Affirmation: Disagreement can be handled without losing respect.",
    "Leadership Affirmation: Lower the temperature before trying to solve the issue.",
    "Leadership Affirmation: Seek the shared goal behind competing opinions.",
    "Leadership Affirmation: You can separate a work problem from personal criticism.",
    "Leadership Affirmation: Ask what each person needs to move forward.",
    "Leadership Affirmation: Keep a disagreement focused on observable facts.",
    "Leadership Affirmation: A respectful boundary can protect a productive conversation.",
    "Leadership Affirmation: Choose resolution over winning the last word.",
    "Leadership Affirmation: Bring in appropriate support when a conflict needs it.",
    "Leadership Affirmation: Your response can model how adults work through tension.",
    "Leadership Affirmation: Change becomes easier when the next step is clear.",
    "Leadership Affirmation: You can learn a new system one task at a time.",
    "Leadership Affirmation: Give teammates room to ask basic questions.",
    "Leadership Affirmation: An unfamiliar process does not erase your experience.",
    "Leadership Affirmation: Your patience helps the team adapt to new tools.",
    "Leadership Affirmation: Share a useful discovery with someone still adjusting.",
    "Leadership Affirmation: Check current guidance before teaching an uncertain feature.",
    "Leadership Affirmation: You can acknowledge frustration and still support progress.",
    "Leadership Affirmation: Treat early mistakes as clues for better training.",
    "Leadership Affirmation: Steady practice builds confidence during a transition.",
    "Leadership Affirmation: Your humility keeps improvement possible.",
    "Leadership Affirmation: Invite feedback about how your directions are landing.",
    "Leadership Affirmation: A good idea can come from any position.",
    "Leadership Affirmation: You can revise your approach without losing credibility.",
    "Leadership Affirmation: Admitting uncertainty is a starting point for learning.",
    "Leadership Affirmation: Let evidence guide your next adjustment.",
    "Leadership Affirmation: Thank someone who respectfully points out a missed detail.",
    "Leadership Affirmation: Experience grows stronger when it stays curious.",
    "Leadership Affirmation: You do not have to defend every past decision.",
    "Leadership Affirmation: A willingness to reconsider can strengthen trust.",
    "Leadership Affirmation: One difficult shift does not cancel your progress.",
    "Leadership Affirmation: You can recover your focus after a rough moment.",
    "Leadership Affirmation: Start again with the next useful choice.",
    "Leadership Affirmation: Setbacks can reveal where support needs to improve.",
    "Leadership Affirmation: Your growth includes learning how to recover.",
    "Leadership Affirmation: Take the lesson without carrying unnecessary shame.",
    "Leadership Affirmation: A hard day can still contain good leadership.",
    "Leadership Affirmation: You can ask for feedback after things settle.",
    "Leadership Affirmation: Progress often looks like responding better the next time.",
    "Leadership Affirmation: Your next action can restore momentum.",
    "Leadership Affirmation: You can balance compassion with clear boundaries.",
    "Leadership Affirmation: Being helpful does not require promising what you cannot deliver.",
    "Leadership Affirmation: State your limits early enough for others to plan.",
    "Leadership Affirmation: A respectful no can protect important priorities.",
    "Leadership Affirmation: Your energy deserves thoughtful use throughout the shift.",
    "Leadership Affirmation: Make realistic commitments and honor them.",
    "Leadership Affirmation: Ask for a priority decision when demands compete.",
    "Leadership Affirmation: Sustainable effort helps you remain dependable.",
    "Leadership Affirmation: You can care deeply without carrying every problem alone.",
    "Leadership Affirmation: Healthy boundaries make your support more consistent.",
    "Leadership Affirmation: Teamwork includes the people outside your station.",
    "Leadership Affirmation: A useful heads-up connects the front and back of house.",
    "Leadership Affirmation: Ask what another area needs before guessing.",
    "Leadership Affirmation: Your station succeeds more fully when the whole operation succeeds.",
    "Leadership Affirmation: Recognize the pressure another role is managing.",
    "Leadership Affirmation: Share information that helps the next station prepare.",
    "Leadership Affirmation: You can turn a handoff into a moment of cooperation.",
    "Leadership Affirmation: Offer help in a way that supports the existing plan.",
    "Leadership Affirmation: Respect grows when teammates understand each other's work.",
    "Leadership Affirmation: A shared goal makes cross-station communication easier.",
    "Leadership Affirmation: Protect trust by sharing information responsibly.",
    "Leadership Affirmation: Keep your word in the small moments.",
    "Leadership Affirmation: People notice when your actions match your explanations.",
    "Leadership Affirmation: Your honesty makes future conversations easier.",
    "Leadership Affirmation: Handle a concern with the discretion it deserves.",
    "Leadership Affirmation: Avoid joining a conversation that tears someone down.",
    "Leadership Affirmation: You can redirect gossip toward a constructive next step.",
    "Leadership Affirmation: Be the leader who speaks respectfully about absent teammates.",
    "Leadership Affirmation: Trust deepens when follow-through becomes predictable.",
    "Leadership Affirmation: Your integrity matters even when a shortcut would go unnoticed.",
    "Leadership Affirmation: Make room for teammates with different strengths.",
    "Leadership Affirmation: An inclusive huddle invites understanding from everyone.",
    "Leadership Affirmation: Check that language differences have not hidden confusion.",
    "Leadership Affirmation: Patience helps a teammate participate with confidence.",
    "Leadership Affirmation: Your team benefits when different perspectives are heard.",
    "Leadership Affirmation: Use clear words instead of making someone feel behind.",
    "Leadership Affirmation: Respect includes learning how another person communicates.",
    "Leadership Affirmation: You can make belonging visible through everyday actions.",
    "Leadership Affirmation: Invite input without putting someone on the spot.",
    "Leadership Affirmation: Everyone deserves a fair chance to contribute.",
    "Leadership Affirmation: Leadership growth happens through repeated choices.",
    "Leadership Affirmation: Choose one skill to practice intentionally today.",
    "Leadership Affirmation: Your title is a responsibility to keep learning.",
    "Leadership Affirmation: Reflect on what helped the team succeed.",
    "Leadership Affirmation: A small improvement repeated becomes a stronger habit.",
    "Leadership Affirmation: Ask which part of your leadership needs more attention.",
    "Leadership Affirmation: Your progress is worth noticing even before mastery.",
    "Leadership Affirmation: Turn a useful lesson into tomorrow's plan.",
    "Leadership Affirmation: You can grow without comparing your path to someone else's.",
    "Leadership Affirmation: Purposeful practice gives experience greater value.",
    "Leadership Affirmation: A result is more useful when you understand its cause.",
    "Leadership Affirmation: Use performance information to guide questions and support.",
    "Leadership Affirmation: Look beyond the number to the work behind it.",
    "Leadership Affirmation: A strong metric should reflect a healthy process.",
    "Leadership Affirmation: You can celebrate a gain while checking its consistency.",
    "Leadership Affirmation: Find one practical adjustment in today's results.",
    "Leadership Affirmation: Discuss trends with curiosity before assigning conclusions.",
    "Leadership Affirmation: Measure progress without reducing people to a score.",
    "Leadership Affirmation: Let results inform coaching that someone can act on.",
    "Leadership Affirmation: Improvement begins when observations become useful changes.",
    "Leadership Affirmation: Your encouragement can help another person try again.",
    "Leadership Affirmation: Make confidence specific by pointing to a demonstrated strength.",
    "Leadership Affirmation: A teammate's small success can become tomorrow's foundation.",
    "Leadership Affirmation: You can remind someone of progress they have overlooked.",
    "Leadership Affirmation: Offer support that makes the next attempt feel possible.",
    "Leadership Affirmation: Your belief in someone's growth should come with useful guidance.",
    "Leadership Affirmation: Give a struggling teammate a clear and achievable next step.",
    "Leadership Affirmation: Encouragement is stronger when it stays honest.",
    "Leadership Affirmation: Notice effort that is beginning to become skill.",
    "Leadership Affirmation: Help someone see that learning belongs on every shift.",
    "Leadership Affirmation: When the rush builds faster than expected, you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: Asking what support would help most is a strength you bring when the rush builds faster than expected.",
    "Leadership Affirmation: Your leadership matters during a growing rush: you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can meet a growing rush with purpose: explain the shared goal before assigning the work.",
    "Leadership Affirmation: When the rush builds faster than expected, you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You have an opportunity to recognize the effort already invested when the rush builds faster than expected.",
    "Leadership Affirmation: Your leadership matters during a growing rush: you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can meet a growing rush with purpose: bring the right people into the discussion.",
    "Leadership Affirmation: When the rush builds faster than expected, you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can turn discussion into progress by clarifying ownership when the rush builds faster than expected.",
    "Leadership Affirmation: Your leadership matters during a growing rush: you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: You can meet a growing rush with purpose: follow through on the support you offer.",
    "Leadership Affirmation: When the rush builds faster than expected, you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: Your own example can give the team a useful standard to follow when the rush builds faster than expected.",
    "Leadership Affirmation: Your leadership matters during a growing rush: you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can meet a growing rush with purpose: make the needed information easy for others to find.",
    "Leadership Affirmation: When the rush builds faster than expected, you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can stay dependable while adjusting to new information when the rush builds faster than expected.",
    "Leadership Affirmation: Your leadership matters during a growing rush: you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can meet a growing rush with purpose: carry one useful lesson into the next shift.",
    "Leadership Affirmation: A calm, specific next step is a contribution you can make when a new teammate asks the same question again.",
    "Leadership Affirmation: Your leadership matters during a repeated training question: you can ask what support would make the biggest difference.",
    "Leadership Affirmation: You can meet a repeated training question with purpose: listen for the detail that changes the picture.",
    "Leadership Affirmation: When a new teammate asks the same question again, you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can confirm understanding while protecting confidence when a new teammate asks the same question again.",
    "Leadership Affirmation: Your leadership matters during a repeated training question: you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can meet a repeated training question with purpose: separate what you know from what still needs checking.",
    "Leadership Affirmation: When a new teammate asks the same question again, you can bring the right people into the discussion.",
    "Leadership Affirmation: You can make space for an idea that improves the team's response when a new teammate asks the same question again.",
    "Leadership Affirmation: Your leadership matters during a repeated training question: you can agree on who owns the next action.",
    "Leadership Affirmation: You can meet a repeated training question with purpose: choose a realistic priority the team can act on.",
    "Leadership Affirmation: When a new teammate asks the same question again, you can follow through on the support you offer.",
    "Leadership Affirmation: Your respectful questions can reveal the obstacle beneath the surface when a new teammate asks the same question again.",
    "Leadership Affirmation: Your leadership matters during a repeated training question: you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can meet a repeated training question with purpose: invite feedback on whether your direction is helping.",
    "Leadership Affirmation: When a new teammate asks the same question again, you can make the needed information easy for others to find.",
    "Leadership Affirmation: Your follow-up can help the team recognize what is improving when a new teammate asks the same question again.",
    "Leadership Affirmation: Your leadership matters during a repeated training question: you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can meet a repeated training question with purpose: protect dignity while keeping expectations clear.",
    "Leadership Affirmation: When a new teammate asks the same question again, you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: Your leadership matters during competing station needs: you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: You can meet competing station needs with purpose: ask what support would make the biggest difference.",
    "Leadership Affirmation: When two stations need help at once, you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can connect the work to a goal everyone understands when two stations need help at once.",
    "Leadership Affirmation: Your leadership matters during competing station needs: you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You can meet competing station needs with purpose: recognize the effort that has already been made.",
    "Leadership Affirmation: When two stations need help at once, you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can strengthen the response by involving the right people when two stations need help at once.",
    "Leadership Affirmation: Your leadership matters during competing station needs: you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can meet competing station needs with purpose: agree on who owns the next action.",
    "Leadership Affirmation: When two stations need help at once, you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: Your follow-through can turn an offer of support into trust when two stations need help at once.",
    "Leadership Affirmation: Your leadership matters during competing station needs: you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: You can meet competing station needs with purpose: model the care you want the team to carry forward.",
    "Leadership Affirmation: When two stations need help at once, you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can reduce confusion by making the needed information accessible when two stations need help at once.",
    "Leadership Affirmation: Your leadership matters during competing station needs: you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can meet competing station needs with purpose: adjust your approach as new information comes in.",
    "Leadership Affirmation: When two stations need help at once, you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can turn today's experience into a useful lesson for the next shift when two stations need help at once.",
    "Leadership Affirmation: You can meet a guest waiting for clarity with purpose: steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: When a guest is waiting for an explanation, you can ask what support would make the biggest difference.",
    "Leadership Affirmation: Careful listening helps you discover the detail that matters when a guest is waiting for an explanation.",
    "Leadership Affirmation: Your leadership matters during a guest waiting for clarity: you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can meet a guest waiting for clarity with purpose: check understanding without making anyone feel small.",
    "Leadership Affirmation: When a guest is waiting for an explanation, you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can build clarity by naming what still needs to be checked when a guest is waiting for an explanation.",
    "Leadership Affirmation: Your leadership matters during a guest waiting for clarity: you can bring the right people into the discussion.",
    "Leadership Affirmation: You can meet a guest waiting for clarity with purpose: give someone room to share a useful idea.",
    "Leadership Affirmation: When a guest is waiting for an explanation, you can agree on who owns the next action.",
    "Leadership Affirmation: You can help the team move forward with a realistic priority when a guest is waiting for an explanation.",
    "Leadership Affirmation: Your leadership matters during a guest waiting for clarity: you can follow through on the support you offer.",
    "Leadership Affirmation: You can meet a guest waiting for clarity with purpose: use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: When a guest is waiting for an explanation, you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can improve your direction by asking how it is landing when a guest is waiting for an explanation.",
    "Leadership Affirmation: Your leadership matters during a guest waiting for clarity: you can make the needed information easy for others to find.",
    "Leadership Affirmation: You can meet a guest waiting for clarity with purpose: check back after the first step to see what has improved.",
    "Leadership Affirmation: When a guest is waiting for an explanation, you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can protect dignity and keep expectations understandable when a guest is waiting for an explanation.",
    "Leadership Affirmation: Your leadership matters during a guest waiting for clarity: you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: When a trainee hesitates to try a task, you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: Asking what support would help most is a strength you bring when a trainee hesitates to try a task.",
    "Leadership Affirmation: Your leadership matters during a hesitant learner: you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can meet a hesitant learner with purpose: explain the shared goal before assigning the work.",
    "Leadership Affirmation: When a trainee hesitates to try a task, you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You have an opportunity to recognize the effort already invested when a trainee hesitates to try a task.",
    "Leadership Affirmation: Your leadership matters during a hesitant learner: you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can meet a hesitant learner with purpose: bring the right people into the discussion.",
    "Leadership Affirmation: When a trainee hesitates to try a task, you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can turn discussion into progress by clarifying ownership when a trainee hesitates to try a task.",
    "Leadership Affirmation: Your leadership matters during a hesitant learner: you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: You can meet a hesitant learner with purpose: follow through on the support you offer.",
    "Leadership Affirmation: When a trainee hesitates to try a task, you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: Your own example can give the team a useful standard to follow when a trainee hesitates to try a task.",
    "Leadership Affirmation: Your leadership matters during a hesitant learner: you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can meet a hesitant learner with purpose: make the needed information easy for others to find.",
    "Leadership Affirmation: When a trainee hesitates to try a task, you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can stay dependable while adjusting to new information when a trainee hesitates to try a task.",
    "Leadership Affirmation: Your leadership matters during a hesitant learner: you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can meet a hesitant learner with purpose: carry one useful lesson into the next shift.",
    "Leadership Affirmation: A calm, specific next step is a contribution you can make when an experienced teammate suggests a different approach.",
    "Leadership Affirmation: Your leadership matters during a teammate's alternative idea: you can ask what support would make the biggest difference.",
    "Leadership Affirmation: You can meet a teammate's alternative idea with purpose: listen for the detail that changes the picture.",
    "Leadership Affirmation: When an experienced teammate suggests a different approach, you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can confirm understanding while protecting confidence when an experienced teammate suggests a different approach.",
    "Leadership Affirmation: Your leadership matters during a teammate's alternative idea: you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can meet a teammate's alternative idea with purpose: separate what you know from what still needs checking.",
    "Leadership Affirmation: When an experienced teammate suggests a different approach, you can bring the right people into the discussion.",
    "Leadership Affirmation: You can make space for an idea that improves the team's response when an experienced teammate suggests a different approach.",
    "Leadership Affirmation: Your leadership matters during a teammate's alternative idea: you can agree on who owns the next action.",
    "Leadership Affirmation: You can meet a teammate's alternative idea with purpose: choose a realistic priority the team can act on.",
    "Leadership Affirmation: When an experienced teammate suggests a different approach, you can follow through on the support you offer.",
    "Leadership Affirmation: Your respectful questions can reveal the obstacle beneath the surface when an experienced teammate suggests a different approach.",
    "Leadership Affirmation: Your leadership matters during a teammate's alternative idea: you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can meet a teammate's alternative idea with purpose: invite feedback on whether your direction is helping.",
    "Leadership Affirmation: When an experienced teammate suggests a different approach, you can make the needed information easy for others to find.",
    "Leadership Affirmation: Your follow-up can help the team recognize what is improving when an experienced teammate suggests a different approach.",
    "Leadership Affirmation: Your leadership matters during a teammate's alternative idea: you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can meet a teammate's alternative idea with purpose: protect dignity while keeping expectations clear.",
    "Leadership Affirmation: When an experienced teammate suggests a different approach, you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: Your leadership matters during a changing shift plan: you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: You can meet a changing shift plan with purpose: ask what support would make the biggest difference.",
    "Leadership Affirmation: When the shift plan needs an adjustment, you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can connect the work to a goal everyone understands when the shift plan needs an adjustment.",
    "Leadership Affirmation: Your leadership matters during a changing shift plan: you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You can meet a changing shift plan with purpose: recognize the effort that has already been made.",
    "Leadership Affirmation: When the shift plan needs an adjustment, you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can strengthen the response by involving the right people when the shift plan needs an adjustment.",
    "Leadership Affirmation: Your leadership matters during a changing shift plan: you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can meet a changing shift plan with purpose: agree on who owns the next action.",
    "Leadership Affirmation: When the shift plan needs an adjustment, you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: Your follow-through can turn an offer of support into trust when the shift plan needs an adjustment.",
    "Leadership Affirmation: Your leadership matters during a changing shift plan: you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: You can meet a changing shift plan with purpose: model the care you want the team to carry forward.",
    "Leadership Affirmation: When the shift plan needs an adjustment, you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can reduce confusion by making the needed information accessible when the shift plan needs an adjustment.",
    "Leadership Affirmation: Your leadership matters during a changing shift plan: you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can meet a changing shift plan with purpose: adjust your approach as new information comes in.",
    "Leadership Affirmation: When the shift plan needs an adjustment, you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can turn today's experience into a useful lesson for the next shift when the shift plan needs an adjustment.",
    "Leadership Affirmation: You can meet an order correction with purpose: steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: When an order needs to be corrected, you can ask what support would make the biggest difference.",
    "Leadership Affirmation: Careful listening helps you discover the detail that matters when an order needs to be corrected.",
    "Leadership Affirmation: Your leadership matters during an order correction: you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can meet an order correction with purpose: check understanding without making anyone feel small.",
    "Leadership Affirmation: When an order needs to be corrected, you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can build clarity by naming what still needs to be checked when an order needs to be corrected.",
    "Leadership Affirmation: Your leadership matters during an order correction: you can bring the right people into the discussion.",
    "Leadership Affirmation: You can meet an order correction with purpose: give someone room to share a useful idea.",
    "Leadership Affirmation: When an order needs to be corrected, you can agree on who owns the next action.",
    "Leadership Affirmation: You can help the team move forward with a realistic priority when an order needs to be corrected.",
    "Leadership Affirmation: Your leadership matters during an order correction: you can follow through on the support you offer.",
    "Leadership Affirmation: You can meet an order correction with purpose: use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: When an order needs to be corrected, you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can improve your direction by asking how it is landing when an order needs to be corrected.",
    "Leadership Affirmation: Your leadership matters during an order correction: you can make the needed information easy for others to find.",
    "Leadership Affirmation: You can meet an order correction with purpose: check back after the first step to see what has improved.",
    "Leadership Affirmation: When an order needs to be corrected, you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can protect dignity and keep expectations understandable when an order needs to be corrected.",
    "Leadership Affirmation: Your leadership matters during an order correction: you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: When the next shift arrives during a busy period, you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: Asking what support would help most is a strength you bring when the next shift arrives during a busy period.",
    "Leadership Affirmation: Your leadership matters during a busy shift transition: you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can meet a busy shift transition with purpose: explain the shared goal before assigning the work.",
    "Leadership Affirmation: When the next shift arrives during a busy period, you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You have an opportunity to recognize the effort already invested when the next shift arrives during a busy period.",
    "Leadership Affirmation: Your leadership matters during a busy shift transition: you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can meet a busy shift transition with purpose: bring the right people into the discussion.",
    "Leadership Affirmation: When the next shift arrives during a busy period, you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can turn discussion into progress by clarifying ownership when the next shift arrives during a busy period.",
    "Leadership Affirmation: Your leadership matters during a busy shift transition: you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: You can meet a busy shift transition with purpose: follow through on the support you offer.",
    "Leadership Affirmation: When the next shift arrives during a busy period, you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: Your own example can give the team a useful standard to follow when the next shift arrives during a busy period.",
    "Leadership Affirmation: Your leadership matters during a busy shift transition: you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can meet a busy shift transition with purpose: make the needed information easy for others to find.",
    "Leadership Affirmation: When the next shift arrives during a busy period, you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can stay dependable while adjusting to new information when the next shift arrives during a busy period.",
    "Leadership Affirmation: Your leadership matters during a busy shift transition: you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can meet a busy shift transition with purpose: carry one useful lesson into the next shift.",
    "Leadership Affirmation: A calm, specific next step is a contribution you can make when a quiet teammate has something to contribute.",
    "Leadership Affirmation: Your leadership matters during a quieter teammate's input: you can ask what support would make the biggest difference.",
    "Leadership Affirmation: You can meet a quieter teammate's input with purpose: listen for the detail that changes the picture.",
    "Leadership Affirmation: When a quiet teammate has something to contribute, you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can confirm understanding while protecting confidence when a quiet teammate has something to contribute.",
    "Leadership Affirmation: Your leadership matters during a quieter teammate's input: you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can meet a quieter teammate's input with purpose: separate what you know from what still needs checking.",
    "Leadership Affirmation: When a quiet teammate has something to contribute, you can bring the right people into the discussion.",
    "Leadership Affirmation: You can make space for an idea that improves the team's response when a quiet teammate has something to contribute.",
    "Leadership Affirmation: Your leadership matters during a quieter teammate's input: you can agree on who owns the next action.",
    "Leadership Affirmation: You can meet a quieter teammate's input with purpose: choose a realistic priority the team can act on.",
    "Leadership Affirmation: When a quiet teammate has something to contribute, you can follow through on the support you offer.",
    "Leadership Affirmation: Your respectful questions can reveal the obstacle beneath the surface when a quiet teammate has something to contribute.",
    "Leadership Affirmation: Your leadership matters during a quieter teammate's input: you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can meet a quieter teammate's input with purpose: invite feedback on whether your direction is helping.",
    "Leadership Affirmation: When a quiet teammate has something to contribute, you can make the needed information easy for others to find.",
    "Leadership Affirmation: Your follow-up can help the team recognize what is improving when a quiet teammate has something to contribute.",
    "Leadership Affirmation: Your leadership matters during a quieter teammate's input: you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can meet a quieter teammate's input with purpose: protect dignity while keeping expectations clear.",
    "Leadership Affirmation: When a quiet teammate has something to contribute, you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: Your leadership matters during a teammate returning to work: you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: You can meet a teammate returning to work with purpose: ask what support would make the biggest difference.",
    "Leadership Affirmation: When a team member returns after time away, you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can connect the work to a goal everyone understands when a team member returns after time away.",
    "Leadership Affirmation: Your leadership matters during a teammate returning to work: you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You can meet a teammate returning to work with purpose: recognize the effort that has already been made.",
    "Leadership Affirmation: When a team member returns after time away, you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can strengthen the response by involving the right people when a team member returns after time away.",
    "Leadership Affirmation: Your leadership matters during a teammate returning to work: you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can meet a teammate returning to work with purpose: agree on who owns the next action.",
    "Leadership Affirmation: When a team member returns after time away, you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: Your follow-through can turn an offer of support into trust when a team member returns after time away.",
    "Leadership Affirmation: Your leadership matters during a teammate returning to work: you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: You can meet a teammate returning to work with purpose: model the care you want the team to carry forward.",
    "Leadership Affirmation: When a team member returns after time away, you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can reduce confusion by making the needed information accessible when a team member returns after time away.",
    "Leadership Affirmation: Your leadership matters during a teammate returning to work: you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can meet a teammate returning to work with purpose: adjust your approach as new information comes in.",
    "Leadership Affirmation: When a team member returns after time away, you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can turn today's experience into a useful lesson for the next shift when a team member returns after time away.",
    "Leadership Affirmation: You can meet a station falling behind with purpose: steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: When a station falls behind the rest of the operation, you can ask what support would make the biggest difference.",
    "Leadership Affirmation: Careful listening helps you discover the detail that matters when a station falls behind the rest of the operation.",
    "Leadership Affirmation: Your leadership matters during a station falling behind: you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can meet a station falling behind with purpose: check understanding without making anyone feel small.",
    "Leadership Affirmation: When a station falls behind the rest of the operation, you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can build clarity by naming what still needs to be checked when a station falls behind the rest of the operation.",
    "Leadership Affirmation: Your leadership matters during a station falling behind: you can bring the right people into the discussion.",
    "Leadership Affirmation: You can meet a station falling behind with purpose: give someone room to share a useful idea.",
    "Leadership Affirmation: When a station falls behind the rest of the operation, you can agree on who owns the next action.",
    "Leadership Affirmation: You can help the team move forward with a realistic priority when a station falls behind the rest of the operation.",
    "Leadership Affirmation: Your leadership matters during a station falling behind: you can follow through on the support you offer.",
    "Leadership Affirmation: You can meet a station falling behind with purpose: use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: When a station falls behind the rest of the operation, you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can improve your direction by asking how it is landing when a station falls behind the rest of the operation.",
    "Leadership Affirmation: Your leadership matters during a station falling behind: you can make the needed information easy for others to find.",
    "Leadership Affirmation: You can meet a station falling behind with purpose: check back after the first step to see what has improved.",
    "Leadership Affirmation: When a station falls behind the rest of the operation, you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can protect dignity and keep expectations understandable when a station falls behind the rest of the operation.",
    "Leadership Affirmation: Your leadership matters during a station falling behind: you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: When a training report reveals a gap in understanding, you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: Asking what support would help most is a strength you bring when a training report reveals a gap in understanding.",
    "Leadership Affirmation: Your leadership matters during a gap identified through training: you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can meet a gap identified through training with purpose: explain the shared goal before assigning the work.",
    "Leadership Affirmation: When a training report reveals a gap in understanding, you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You have an opportunity to recognize the effort already invested when a training report reveals a gap in understanding.",
    "Leadership Affirmation: Your leadership matters during a gap identified through training: you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can meet a gap identified through training with purpose: bring the right people into the discussion.",
    "Leadership Affirmation: When a training report reveals a gap in understanding, you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can turn discussion into progress by clarifying ownership when a training report reveals a gap in understanding.",
    "Leadership Affirmation: Your leadership matters during a gap identified through training: you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: You can meet a gap identified through training with purpose: follow through on the support you offer.",
    "Leadership Affirmation: When a training report reveals a gap in understanding, you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: Your own example can give the team a useful standard to follow when a training report reveals a gap in understanding.",
    "Leadership Affirmation: Your leadership matters during a gap identified through training: you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can meet a gap identified through training with purpose: make the needed information easy for others to find.",
    "Leadership Affirmation: When a training report reveals a gap in understanding, you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can stay dependable while adjusting to new information when a training report reveals a gap in understanding.",
    "Leadership Affirmation: Your leadership matters during a gap identified through training: you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can meet a gap identified through training with purpose: carry one useful lesson into the next shift.",
    "Leadership Affirmation: A calm, specific next step is a contribution you can make when a teammate receives difficult feedback.",
    "Leadership Affirmation: Your leadership matters during a difficult coaching moment: you can ask what support would make the biggest difference.",
    "Leadership Affirmation: You can meet a difficult coaching moment with purpose: listen for the detail that changes the picture.",
    "Leadership Affirmation: When a teammate receives difficult feedback, you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can confirm understanding while protecting confidence when a teammate receives difficult feedback.",
    "Leadership Affirmation: Your leadership matters during a difficult coaching moment: you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can meet a difficult coaching moment with purpose: separate what you know from what still needs checking.",
    "Leadership Affirmation: When a teammate receives difficult feedback, you can bring the right people into the discussion.",
    "Leadership Affirmation: You can make space for an idea that improves the team's response when a teammate receives difficult feedback.",
    "Leadership Affirmation: Your leadership matters during a difficult coaching moment: you can agree on who owns the next action.",
    "Leadership Affirmation: You can meet a difficult coaching moment with purpose: choose a realistic priority the team can act on.",
    "Leadership Affirmation: When a teammate receives difficult feedback, you can follow through on the support you offer.",
    "Leadership Affirmation: Your respectful questions can reveal the obstacle beneath the surface when a teammate receives difficult feedback.",
    "Leadership Affirmation: Your leadership matters during a difficult coaching moment: you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can meet a difficult coaching moment with purpose: invite feedback on whether your direction is helping.",
    "Leadership Affirmation: When a teammate receives difficult feedback, you can make the needed information easy for others to find.",
    "Leadership Affirmation: Your follow-up can help the team recognize what is improving when a teammate receives difficult feedback.",
    "Leadership Affirmation: Your leadership matters during a difficult coaching moment: you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can meet a difficult coaching moment with purpose: protect dignity while keeping expectations clear.",
    "Leadership Affirmation: When a teammate receives difficult feedback, you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: Your leadership matters during a new tool rollout: you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: You can meet a new tool rollout with purpose: ask what support would make the biggest difference.",
    "Leadership Affirmation: When the team is learning a new tool, you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can connect the work to a goal everyone understands when the team is learning a new tool.",
    "Leadership Affirmation: Your leadership matters during a new tool rollout: you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You can meet a new tool rollout with purpose: recognize the effort that has already been made.",
    "Leadership Affirmation: When the team is learning a new tool, you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can strengthen the response by involving the right people when the team is learning a new tool.",
    "Leadership Affirmation: Your leadership matters during a new tool rollout: you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can meet a new tool rollout with purpose: agree on who owns the next action.",
    "Leadership Affirmation: When the team is learning a new tool, you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: Your follow-through can turn an offer of support into trust when the team is learning a new tool.",
    "Leadership Affirmation: Your leadership matters during a new tool rollout: you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: You can meet a new tool rollout with purpose: model the care you want the team to carry forward.",
    "Leadership Affirmation: When the team is learning a new tool, you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can reduce confusion by making the needed information accessible when the team is learning a new tool.",
    "Leadership Affirmation: Your leadership matters during a new tool rollout: you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can meet a new tool rollout with purpose: adjust your approach as new information comes in.",
    "Leadership Affirmation: When the team is learning a new tool, you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can turn today's experience into a useful lesson for the next shift when the team is learning a new tool.",
    "Leadership Affirmation: You can meet an unexpected service delay with purpose: steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: When an unexpected delay affects service, you can ask what support would make the biggest difference.",
    "Leadership Affirmation: Careful listening helps you discover the detail that matters when an unexpected delay affects service.",
    "Leadership Affirmation: Your leadership matters during an unexpected service delay: you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can meet an unexpected service delay with purpose: check understanding without making anyone feel small.",
    "Leadership Affirmation: When an unexpected delay affects service, you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can build clarity by naming what still needs to be checked when an unexpected delay affects service.",
    "Leadership Affirmation: Your leadership matters during an unexpected service delay: you can bring the right people into the discussion.",
    "Leadership Affirmation: You can meet an unexpected service delay with purpose: give someone room to share a useful idea.",
    "Leadership Affirmation: When an unexpected delay affects service, you can agree on who owns the next action.",
    "Leadership Affirmation: You can help the team move forward with a realistic priority when an unexpected delay affects service.",
    "Leadership Affirmation: Your leadership matters during an unexpected service delay: you can follow through on the support you offer.",
    "Leadership Affirmation: You can meet an unexpected service delay with purpose: use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: When an unexpected delay affects service, you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can improve your direction by asking how it is landing when an unexpected delay affects service.",
    "Leadership Affirmation: Your leadership matters during an unexpected service delay: you can make the needed information easy for others to find.",
    "Leadership Affirmation: You can meet an unexpected service delay with purpose: check back after the first step to see what has improved.",
    "Leadership Affirmation: When an unexpected delay affects service, you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can protect dignity and keep expectations understandable when an unexpected delay affects service.",
    "Leadership Affirmation: Your leadership matters during an unexpected service delay: you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: When a closing task is still unfinished, you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: Asking what support would help most is a strength you bring when a closing task is still unfinished.",
    "Leadership Affirmation: Your leadership matters during an unfinished closing task: you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can meet an unfinished closing task with purpose: explain the shared goal before assigning the work.",
    "Leadership Affirmation: When a closing task is still unfinished, you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You have an opportunity to recognize the effort already invested when a closing task is still unfinished.",
    "Leadership Affirmation: Your leadership matters during an unfinished closing task: you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can meet an unfinished closing task with purpose: bring the right people into the discussion.",
    "Leadership Affirmation: When a closing task is still unfinished, you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can turn discussion into progress by clarifying ownership when a closing task is still unfinished.",
    "Leadership Affirmation: Your leadership matters during an unfinished closing task: you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: You can meet an unfinished closing task with purpose: follow through on the support you offer.",
    "Leadership Affirmation: When a closing task is still unfinished, you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: Your own example can give the team a useful standard to follow when a closing task is still unfinished.",
    "Leadership Affirmation: Your leadership matters during an unfinished closing task: you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can meet an unfinished closing task with purpose: make the needed information easy for others to find.",
    "Leadership Affirmation: When a closing task is still unfinished, you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can stay dependable while adjusting to new information when a closing task is still unfinished.",
    "Leadership Affirmation: Your leadership matters during an unfinished closing task: you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can meet an unfinished closing task with purpose: carry one useful lesson into the next shift.",
    "Leadership Affirmation: A calm, specific next step is a contribution you can make when an opening check reveals missing supplies.",
    "Leadership Affirmation: Your leadership matters during an opening readiness gap: you can ask what support would make the biggest difference.",
    "Leadership Affirmation: You can meet an opening readiness gap with purpose: listen for the detail that changes the picture.",
    "Leadership Affirmation: When an opening check reveals missing supplies, you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can confirm understanding while protecting confidence when an opening check reveals missing supplies.",
    "Leadership Affirmation: Your leadership matters during an opening readiness gap: you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can meet an opening readiness gap with purpose: separate what you know from what still needs checking.",
    "Leadership Affirmation: When an opening check reveals missing supplies, you can bring the right people into the discussion.",
    "Leadership Affirmation: You can make space for an idea that improves the team's response when an opening check reveals missing supplies.",
    "Leadership Affirmation: Your leadership matters during an opening readiness gap: you can agree on who owns the next action.",
    "Leadership Affirmation: You can meet an opening readiness gap with purpose: choose a realistic priority the team can act on.",
    "Leadership Affirmation: When an opening check reveals missing supplies, you can follow through on the support you offer.",
    "Leadership Affirmation: Your respectful questions can reveal the obstacle beneath the surface when an opening check reveals missing supplies.",
    "Leadership Affirmation: Your leadership matters during an opening readiness gap: you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can meet an opening readiness gap with purpose: invite feedback on whether your direction is helping.",
    "Leadership Affirmation: When an opening check reveals missing supplies, you can make the needed information easy for others to find.",
    "Leadership Affirmation: Your follow-up can help the team recognize what is improving when an opening check reveals missing supplies.",
    "Leadership Affirmation: Your leadership matters during an opening readiness gap: you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can meet an opening readiness gap with purpose: protect dignity while keeping expectations clear.",
    "Leadership Affirmation: When an opening check reveals missing supplies, you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: Your leadership matters during an equipment concern: you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: You can meet an equipment concern with purpose: ask what support would make the biggest difference.",
    "Leadership Affirmation: When a teammate reports an equipment concern, you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can connect the work to a goal everyone understands when a teammate reports an equipment concern.",
    "Leadership Affirmation: Your leadership matters during an equipment concern: you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You can meet an equipment concern with purpose: recognize the effort that has already been made.",
    "Leadership Affirmation: When a teammate reports an equipment concern, you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can strengthen the response by involving the right people when a teammate reports an equipment concern.",
    "Leadership Affirmation: Your leadership matters during an equipment concern: you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can meet an equipment concern with purpose: agree on who owns the next action.",
    "Leadership Affirmation: When a teammate reports an equipment concern, you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: Your follow-through can turn an offer of support into trust when a teammate reports an equipment concern.",
    "Leadership Affirmation: Your leadership matters during an equipment concern: you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: You can meet an equipment concern with purpose: model the care you want the team to carry forward.",
    "Leadership Affirmation: When a teammate reports an equipment concern, you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can reduce confusion by making the needed information accessible when a teammate reports an equipment concern.",
    "Leadership Affirmation: Your leadership matters during an equipment concern: you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can meet an equipment concern with purpose: adjust your approach as new information comes in.",
    "Leadership Affirmation: When a teammate reports an equipment concern, you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can turn today's experience into a useful lesson for the next shift when a teammate reports an equipment concern.",
    "Leadership Affirmation: You can meet disappointing guest feedback with purpose: steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: When a guest shares disappointing feedback, you can ask what support would make the biggest difference.",
    "Leadership Affirmation: Careful listening helps you discover the detail that matters when a guest shares disappointing feedback.",
    "Leadership Affirmation: Your leadership matters during disappointing guest feedback: you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can meet disappointing guest feedback with purpose: check understanding without making anyone feel small.",
    "Leadership Affirmation: When a guest shares disappointing feedback, you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can build clarity by naming what still needs to be checked when a guest shares disappointing feedback.",
    "Leadership Affirmation: Your leadership matters during disappointing guest feedback: you can bring the right people into the discussion.",
    "Leadership Affirmation: You can meet disappointing guest feedback with purpose: give someone room to share a useful idea.",
    "Leadership Affirmation: When a guest shares disappointing feedback, you can agree on who owns the next action.",
    "Leadership Affirmation: You can help the team move forward with a realistic priority when a guest shares disappointing feedback.",
    "Leadership Affirmation: Your leadership matters during disappointing guest feedback: you can follow through on the support you offer.",
    "Leadership Affirmation: You can meet disappointing guest feedback with purpose: use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: When a guest shares disappointing feedback, you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can improve your direction by asking how it is landing when a guest shares disappointing feedback.",
    "Leadership Affirmation: Your leadership matters during disappointing guest feedback: you can make the needed information easy for others to find.",
    "Leadership Affirmation: You can meet disappointing guest feedback with purpose: check back after the first step to see what has improved.",
    "Leadership Affirmation: When a guest shares disappointing feedback, you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can protect dignity and keep expectations understandable when a guest shares disappointing feedback.",
    "Leadership Affirmation: Your leadership matters during disappointing guest feedback: you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: When a small misunderstanding interrupts teamwork, you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: Asking what support would help most is a strength you bring when a small misunderstanding interrupts teamwork.",
    "Leadership Affirmation: Your leadership matters during a teamwork misunderstanding: you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can meet a teamwork misunderstanding with purpose: explain the shared goal before assigning the work.",
    "Leadership Affirmation: When a small misunderstanding interrupts teamwork, you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You have an opportunity to recognize the effort already invested when a small misunderstanding interrupts teamwork.",
    "Leadership Affirmation: Your leadership matters during a teamwork misunderstanding: you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can meet a teamwork misunderstanding with purpose: bring the right people into the discussion.",
    "Leadership Affirmation: When a small misunderstanding interrupts teamwork, you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can turn discussion into progress by clarifying ownership when a small misunderstanding interrupts teamwork.",
    "Leadership Affirmation: Your leadership matters during a teamwork misunderstanding: you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: You can meet a teamwork misunderstanding with purpose: follow through on the support you offer.",
    "Leadership Affirmation: When a small misunderstanding interrupts teamwork, you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: Your own example can give the team a useful standard to follow when a small misunderstanding interrupts teamwork.",
    "Leadership Affirmation: Your leadership matters during a teamwork misunderstanding: you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can meet a teamwork misunderstanding with purpose: make the needed information easy for others to find.",
    "Leadership Affirmation: When a small misunderstanding interrupts teamwork, you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can stay dependable while adjusting to new information when a small misunderstanding interrupts teamwork.",
    "Leadership Affirmation: Your leadership matters during a teamwork misunderstanding: you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can meet a teamwork misunderstanding with purpose: carry one useful lesson into the next shift.",
    "Leadership Affirmation: A calm, specific next step is a contribution you can make when a learner is ready for more responsibility.",
    "Leadership Affirmation: Your leadership matters during a learner's next responsibility: you can ask what support would make the biggest difference.",
    "Leadership Affirmation: You can meet a learner's next responsibility with purpose: listen for the detail that changes the picture.",
    "Leadership Affirmation: When a learner is ready for more responsibility, you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can confirm understanding while protecting confidence when a learner is ready for more responsibility.",
    "Leadership Affirmation: Your leadership matters during a learner's next responsibility: you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can meet a learner's next responsibility with purpose: separate what you know from what still needs checking.",
    "Leadership Affirmation: When a learner is ready for more responsibility, you can bring the right people into the discussion.",
    "Leadership Affirmation: You can make space for an idea that improves the team's response when a learner is ready for more responsibility.",
    "Leadership Affirmation: Your leadership matters during a learner's next responsibility: you can agree on who owns the next action.",
    "Leadership Affirmation: You can meet a learner's next responsibility with purpose: choose a realistic priority the team can act on.",
    "Leadership Affirmation: When a learner is ready for more responsibility, you can follow through on the support you offer.",
    "Leadership Affirmation: Your respectful questions can reveal the obstacle beneath the surface when a learner is ready for more responsibility.",
    "Leadership Affirmation: Your leadership matters during a learner's next responsibility: you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can meet a learner's next responsibility with purpose: invite feedback on whether your direction is helping.",
    "Leadership Affirmation: When a learner is ready for more responsibility, you can make the needed information easy for others to find.",
    "Leadership Affirmation: Your follow-up can help the team recognize what is improving when a learner is ready for more responsibility.",
    "Leadership Affirmation: Your leadership matters during a learner's next responsibility: you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can meet a learner's next responsibility with purpose: protect dignity while keeping expectations clear.",
    "Leadership Affirmation: When a learner is ready for more responsibility, you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: Your leadership matters during a demanding hour of service: you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: You can meet a demanding hour of service with purpose: ask what support would make the biggest difference.",
    "Leadership Affirmation: When the team has worked through a demanding hour, you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can connect the work to a goal everyone understands when the team has worked through a demanding hour.",
    "Leadership Affirmation: Your leadership matters during a demanding hour of service: you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You can meet a demanding hour of service with purpose: recognize the effort that has already been made.",
    "Leadership Affirmation: When the team has worked through a demanding hour, you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can strengthen the response by involving the right people when the team has worked through a demanding hour.",
    "Leadership Affirmation: Your leadership matters during a demanding hour of service: you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can meet a demanding hour of service with purpose: agree on who owns the next action.",
    "Leadership Affirmation: When the team has worked through a demanding hour, you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: Your follow-through can turn an offer of support into trust when the team has worked through a demanding hour.",
    "Leadership Affirmation: Your leadership matters during a demanding hour of service: you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: You can meet a demanding hour of service with purpose: model the care you want the team to carry forward.",
    "Leadership Affirmation: When the team has worked through a demanding hour, you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can reduce confusion by making the needed information accessible when the team has worked through a demanding hour.",
    "Leadership Affirmation: Your leadership matters during a demanding hour of service: you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can meet a demanding hour of service with purpose: adjust your approach as new information comes in.",
    "Leadership Affirmation: When the team has worked through a demanding hour, you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can turn today's experience into a useful lesson for the next shift when the team has worked through a demanding hour.",
    "Leadership Affirmation: You can meet an unclear handoff with purpose: steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: When a handoff leaves an important detail unclear, you can ask what support would make the biggest difference.",
    "Leadership Affirmation: Careful listening helps you discover the detail that matters when a handoff leaves an important detail unclear.",
    "Leadership Affirmation: Your leadership matters during an unclear handoff: you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can meet an unclear handoff with purpose: check understanding without making anyone feel small.",
    "Leadership Affirmation: When a handoff leaves an important detail unclear, you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can build clarity by naming what still needs to be checked when a handoff leaves an important detail unclear.",
    "Leadership Affirmation: Your leadership matters during an unclear handoff: you can bring the right people into the discussion.",
    "Leadership Affirmation: You can meet an unclear handoff with purpose: give someone room to share a useful idea.",
    "Leadership Affirmation: When a handoff leaves an important detail unclear, you can agree on who owns the next action.",
    "Leadership Affirmation: You can help the team move forward with a realistic priority when a handoff leaves an important detail unclear.",
    "Leadership Affirmation: Your leadership matters during an unclear handoff: you can follow through on the support you offer.",
    "Leadership Affirmation: You can meet an unclear handoff with purpose: use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: When a handoff leaves an important detail unclear, you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can improve your direction by asking how it is landing when a handoff leaves an important detail unclear.",
    "Leadership Affirmation: Your leadership matters during an unclear handoff: you can make the needed information easy for others to find.",
    "Leadership Affirmation: You can meet an unclear handoff with purpose: check back after the first step to see what has improved.",
    "Leadership Affirmation: When a handoff leaves an important detail unclear, you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can protect dignity and keep expectations understandable when a handoff leaves an important detail unclear.",
    "Leadership Affirmation: Your leadership matters during an unclear handoff: you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: When a teammate admits a mistake, you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: Asking what support would help most is a strength you bring when a teammate admits a mistake.",
    "Leadership Affirmation: Your leadership matters during an honestly reported mistake: you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can meet an honestly reported mistake with purpose: explain the shared goal before assigning the work.",
    "Leadership Affirmation: When a teammate admits a mistake, you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You have an opportunity to recognize the effort already invested when a teammate admits a mistake.",
    "Leadership Affirmation: Your leadership matters during an honestly reported mistake: you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can meet an honestly reported mistake with purpose: bring the right people into the discussion.",
    "Leadership Affirmation: When a teammate admits a mistake, you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can turn discussion into progress by clarifying ownership when a teammate admits a mistake.",
    "Leadership Affirmation: Your leadership matters during an honestly reported mistake: you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: You can meet an honestly reported mistake with purpose: follow through on the support you offer.",
    "Leadership Affirmation: When a teammate admits a mistake, you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: Your own example can give the team a useful standard to follow when a teammate admits a mistake.",
    "Leadership Affirmation: Your leadership matters during an honestly reported mistake: you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can meet an honestly reported mistake with purpose: make the needed information easy for others to find.",
    "Leadership Affirmation: When a teammate admits a mistake, you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can stay dependable while adjusting to new information when a teammate admits a mistake.",
    "Leadership Affirmation: Your leadership matters during an honestly reported mistake: you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can meet an honestly reported mistake with purpose: carry one useful lesson into the next shift.",
    "Leadership Affirmation: A calm, specific next step is a contribution you can make when a service goal seems difficult to reach.",
    "Leadership Affirmation: Your leadership matters during a challenging service goal: you can ask what support would make the biggest difference.",
    "Leadership Affirmation: You can meet a challenging service goal with purpose: listen for the detail that changes the picture.",
    "Leadership Affirmation: When a service goal seems difficult to reach, you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can confirm understanding while protecting confidence when a service goal seems difficult to reach.",
    "Leadership Affirmation: Your leadership matters during a challenging service goal: you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can meet a challenging service goal with purpose: separate what you know from what still needs checking.",
    "Leadership Affirmation: When a service goal seems difficult to reach, you can bring the right people into the discussion.",
    "Leadership Affirmation: You can make space for an idea that improves the team's response when a service goal seems difficult to reach.",
    "Leadership Affirmation: Your leadership matters during a challenging service goal: you can agree on who owns the next action.",
    "Leadership Affirmation: You can meet a challenging service goal with purpose: choose a realistic priority the team can act on.",
    "Leadership Affirmation: When a service goal seems difficult to reach, you can follow through on the support you offer.",
    "Leadership Affirmation: Your respectful questions can reveal the obstacle beneath the surface when a service goal seems difficult to reach.",
    "Leadership Affirmation: Your leadership matters during a challenging service goal: you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can meet a challenging service goal with purpose: invite feedback on whether your direction is helping.",
    "Leadership Affirmation: When a service goal seems difficult to reach, you can make the needed information easy for others to find.",
    "Leadership Affirmation: Your follow-up can help the team recognize what is improving when a service goal seems difficult to reach.",
    "Leadership Affirmation: Your leadership matters during a challenging service goal: you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can meet a challenging service goal with purpose: protect dignity while keeping expectations clear.",
    "Leadership Affirmation: When a service goal seems difficult to reach, you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: Your leadership matters during several requests for direction: you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: You can meet several requests for direction with purpose: ask what support would make the biggest difference.",
    "Leadership Affirmation: When several people are asking for direction, you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can connect the work to a goal everyone understands when several people are asking for direction.",
    "Leadership Affirmation: Your leadership matters during several requests for direction: you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You can meet several requests for direction with purpose: recognize the effort that has already been made.",
    "Leadership Affirmation: When several people are asking for direction, you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can strengthen the response by involving the right people when several people are asking for direction.",
    "Leadership Affirmation: Your leadership matters during several requests for direction: you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can meet several requests for direction with purpose: agree on who owns the next action.",
    "Leadership Affirmation: When several people are asking for direction, you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: Your follow-through can turn an offer of support into trust when several people are asking for direction.",
    "Leadership Affirmation: Your leadership matters during several requests for direction: you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: You can meet several requests for direction with purpose: model the care you want the team to carry forward.",
    "Leadership Affirmation: When several people are asking for direction, you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can reduce confusion by making the needed information accessible when several people are asking for direction.",
    "Leadership Affirmation: Your leadership matters during several requests for direction: you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can meet several requests for direction with purpose: adjust your approach as new information comes in.",
    "Leadership Affirmation: When several people are asking for direction, you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can turn today's experience into a useful lesson for the next shift when several people are asking for direction.",
    "Leadership Affirmation: You can meet a change to a familiar process with purpose: steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: When a familiar process changes, you can ask what support would make the biggest difference.",
    "Leadership Affirmation: Careful listening helps you discover the detail that matters when a familiar process changes.",
    "Leadership Affirmation: Your leadership matters during a change to a familiar process: you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can meet a change to a familiar process with purpose: check understanding without making anyone feel small.",
    "Leadership Affirmation: When a familiar process changes, you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can build clarity by naming what still needs to be checked when a familiar process changes.",
    "Leadership Affirmation: Your leadership matters during a change to a familiar process: you can bring the right people into the discussion.",
    "Leadership Affirmation: You can meet a change to a familiar process with purpose: give someone room to share a useful idea.",
    "Leadership Affirmation: When a familiar process changes, you can agree on who owns the next action.",
    "Leadership Affirmation: You can help the team move forward with a realistic priority when a familiar process changes.",
    "Leadership Affirmation: Your leadership matters during a change to a familiar process: you can follow through on the support you offer.",
    "Leadership Affirmation: You can meet a change to a familiar process with purpose: use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: When a familiar process changes, you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can improve your direction by asking how it is landing when a familiar process changes.",
    "Leadership Affirmation: Your leadership matters during a change to a familiar process: you can make the needed information easy for others to find.",
    "Leadership Affirmation: You can meet a change to a familiar process with purpose: check back after the first step to see what has improved.",
    "Leadership Affirmation: When a familiar process changes, you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can protect dignity and keep expectations understandable when a familiar process changes.",
    "Leadership Affirmation: Your leadership matters during a change to a familiar process: you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: When someone points out a detail you missed, you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: Asking what support would help most is a strength you bring when someone points out a detail you missed.",
    "Leadership Affirmation: Your leadership matters during a detail you overlooked: you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can meet a detail you overlooked with purpose: explain the shared goal before assigning the work.",
    "Leadership Affirmation: When someone points out a detail you missed, you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You have an opportunity to recognize the effort already invested when someone points out a detail you missed.",
    "Leadership Affirmation: Your leadership matters during a detail you overlooked: you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can meet a detail you overlooked with purpose: bring the right people into the discussion.",
    "Leadership Affirmation: When someone points out a detail you missed, you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can turn discussion into progress by clarifying ownership when someone points out a detail you missed.",
    "Leadership Affirmation: Your leadership matters during a detail you overlooked: you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: You can meet a detail you overlooked with purpose: follow through on the support you offer.",
    "Leadership Affirmation: When someone points out a detail you missed, you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: Your own example can give the team a useful standard to follow when someone points out a detail you missed.",
    "Leadership Affirmation: Your leadership matters during a detail you overlooked: you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can meet a detail you overlooked with purpose: make the needed information easy for others to find.",
    "Leadership Affirmation: When someone points out a detail you missed, you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can stay dependable while adjusting to new information when someone points out a detail you missed.",
    "Leadership Affirmation: Your leadership matters during a detail you overlooked: you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can meet a detail you overlooked with purpose: carry one useful lesson into the next shift.",
    "Leadership Affirmation: A calm, specific next step is a contribution you can make when a teammate asks how to improve.",
    "Leadership Affirmation: Your leadership matters during a teammate's request for growth: you can ask what support would make the biggest difference.",
    "Leadership Affirmation: You can meet a teammate's request for growth with purpose: listen for the detail that changes the picture.",
    "Leadership Affirmation: When a teammate asks how to improve, you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can confirm understanding while protecting confidence when a teammate asks how to improve.",
    "Leadership Affirmation: Your leadership matters during a teammate's request for growth: you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can meet a teammate's request for growth with purpose: separate what you know from what still needs checking.",
    "Leadership Affirmation: When a teammate asks how to improve, you can bring the right people into the discussion.",
    "Leadership Affirmation: You can make space for an idea that improves the team's response when a teammate asks how to improve.",
    "Leadership Affirmation: Your leadership matters during a teammate's request for growth: you can agree on who owns the next action.",
    "Leadership Affirmation: You can meet a teammate's request for growth with purpose: choose a realistic priority the team can act on.",
    "Leadership Affirmation: When a teammate asks how to improve, you can follow through on the support you offer.",
    "Leadership Affirmation: Your respectful questions can reveal the obstacle beneath the surface when a teammate asks how to improve.",
    "Leadership Affirmation: Your leadership matters during a teammate's request for growth: you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can meet a teammate's request for growth with purpose: invite feedback on whether your direction is helping.",
    "Leadership Affirmation: When a teammate asks how to improve, you can make the needed information easy for others to find.",
    "Leadership Affirmation: Your follow-up can help the team recognize what is improving when a teammate asks how to improve.",
    "Leadership Affirmation: Your leadership matters during a teammate's request for growth: you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can meet a teammate's request for growth with purpose: protect dignity while keeping expectations clear.",
    "Leadership Affirmation: When a teammate asks how to improve, you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: Your leadership matters during an unexpected shift result: you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: You can meet an unexpected shift result with purpose: ask what support would make the biggest difference.",
    "Leadership Affirmation: When a shift result differs from the plan, you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can connect the work to a goal everyone understands when a shift result differs from the plan.",
    "Leadership Affirmation: Your leadership matters during an unexpected shift result: you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You can meet an unexpected shift result with purpose: recognize the effort that has already been made.",
    "Leadership Affirmation: When a shift result differs from the plan, you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can strengthen the response by involving the right people when a shift result differs from the plan.",
    "Leadership Affirmation: Your leadership matters during an unexpected shift result: you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can meet an unexpected shift result with purpose: agree on who owns the next action.",
    "Leadership Affirmation: When a shift result differs from the plan, you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: Your follow-through can turn an offer of support into trust when a shift result differs from the plan.",
    "Leadership Affirmation: Your leadership matters during an unexpected shift result: you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: You can meet an unexpected shift result with purpose: model the care you want the team to carry forward.",
    "Leadership Affirmation: When a shift result differs from the plan, you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can reduce confusion by making the needed information accessible when a shift result differs from the plan.",
    "Leadership Affirmation: Your leadership matters during an unexpected shift result: you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can meet an unexpected shift result with purpose: adjust your approach as new information comes in.",
    "Leadership Affirmation: When a shift result differs from the plan, you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can turn today's experience into a useful lesson for the next shift when a shift result differs from the plan.",
    "Leadership Affirmation: You can meet a scheduling support request with purpose: steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: When a team member needs scheduling support, you can ask what support would make the biggest difference.",
    "Leadership Affirmation: Careful listening helps you discover the detail that matters when a team member needs scheduling support.",
    "Leadership Affirmation: Your leadership matters during a scheduling support request: you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can meet a scheduling support request with purpose: check understanding without making anyone feel small.",
    "Leadership Affirmation: When a team member needs scheduling support, you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can build clarity by naming what still needs to be checked when a team member needs scheduling support.",
    "Leadership Affirmation: Your leadership matters during a scheduling support request: you can bring the right people into the discussion.",
    "Leadership Affirmation: You can meet a scheduling support request with purpose: give someone room to share a useful idea.",
    "Leadership Affirmation: When a team member needs scheduling support, you can agree on who owns the next action.",
    "Leadership Affirmation: You can help the team move forward with a realistic priority when a team member needs scheduling support.",
    "Leadership Affirmation: Your leadership matters during a scheduling support request: you can follow through on the support you offer.",
    "Leadership Affirmation: You can meet a scheduling support request with purpose: use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: When a team member needs scheduling support, you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can improve your direction by asking how it is landing when a team member needs scheduling support.",
    "Leadership Affirmation: Your leadership matters during a scheduling support request: you can make the needed information easy for others to find.",
    "Leadership Affirmation: You can meet a scheduling support request with purpose: check back after the first step to see what has improved.",
    "Leadership Affirmation: When a team member needs scheduling support, you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can protect dignity and keep expectations understandable when a team member needs scheduling support.",
    "Leadership Affirmation: Your leadership matters during a scheduling support request: you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: When a trainer hands a learner to another trainer, you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: Asking what support would help most is a strength you bring when a trainer hands a learner to another trainer.",
    "Leadership Affirmation: Your leadership matters during a transition between trainers: you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can meet a transition between trainers with purpose: explain the shared goal before assigning the work.",
    "Leadership Affirmation: When a trainer hands a learner to another trainer, you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You have an opportunity to recognize the effort already invested when a trainer hands a learner to another trainer.",
    "Leadership Affirmation: Your leadership matters during a transition between trainers: you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can meet a transition between trainers with purpose: bring the right people into the discussion.",
    "Leadership Affirmation: When a trainer hands a learner to another trainer, you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can turn discussion into progress by clarifying ownership when a trainer hands a learner to another trainer.",
    "Leadership Affirmation: Your leadership matters during a transition between trainers: you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: You can meet a transition between trainers with purpose: follow through on the support you offer.",
    "Leadership Affirmation: When a trainer hands a learner to another trainer, you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: Your own example can give the team a useful standard to follow when a trainer hands a learner to another trainer.",
    "Leadership Affirmation: Your leadership matters during a transition between trainers: you can invite feedback on whether your direction is helping.",
    "Leadership Affirmation: You can meet a transition between trainers with purpose: make the needed information easy for others to find.",
    "Leadership Affirmation: When a trainer hands a learner to another trainer, you can check back after the first step to see what has improved.",
    "Leadership Affirmation: You can stay dependable while adjusting to new information when a trainer hands a learner to another trainer.",
    "Leadership Affirmation: Your leadership matters during a transition between trainers: you can protect dignity while keeping expectations clear.",
    "Leadership Affirmation: You can meet a transition between trainers with purpose: carry one useful lesson into the next shift.",
    "Leadership Affirmation: A calm, specific next step is a contribution you can make when the team reaches an important milestone.",
    "Leadership Affirmation: Your leadership matters during a team milestone: you can ask what support would make the biggest difference.",
    "Leadership Affirmation: You can meet a team milestone with purpose: listen for the detail that changes the picture.",
    "Leadership Affirmation: When the team reaches an important milestone, you can explain the shared goal before assigning the work.",
    "Leadership Affirmation: You can confirm understanding while protecting confidence when the team reaches an important milestone.",
    "Leadership Affirmation: Your leadership matters during a team milestone: you can recognize the effort that has already been made.",
    "Leadership Affirmation: You can meet a team milestone with purpose: separate what you know from what still needs checking.",
    "Leadership Affirmation: When the team reaches an important milestone, you can bring the right people into the discussion.",
    "Leadership Affirmation: You can make space for an idea that improves the team's response when the team reaches an important milestone.",
    "Leadership Affirmation: Your leadership matters during a team milestone: you can agree on who owns the next action.",
    "Leadership Affirmation: You can meet a team milestone with purpose: choose a realistic priority the team can act on.",
    "Leadership Affirmation: When the team reaches an important milestone, you can follow through on the support you offer.",
    "Leadership Affirmation: Your respectful questions can reveal the obstacle beneath the surface when the team reaches an important milestone.",
    "Leadership Affirmation: Your leadership matters during a team milestone: you can model the care you want the team to carry forward.",
    "Leadership Affirmation: You can meet a team milestone with purpose: invite feedback on whether your direction is helping.",
    "Leadership Affirmation: When the team reaches an important milestone, you can make the needed information easy for others to find.",
    "Leadership Affirmation: Your follow-up can help the team recognize what is improving when the team reaches an important milestone.",
    "Leadership Affirmation: Your leadership matters during a team milestone: you can adjust your approach as new information comes in.",
    "Leadership Affirmation: You can meet a team milestone with purpose: protect dignity while keeping expectations clear.",
    "Leadership Affirmation: When the team reaches an important milestone, you can carry one useful lesson into the next shift.",
    "Leadership Affirmation: Your leadership matters during an overlooked routine task: you can steady the conversation with a calm, specific next step.",
    "Leadership Affirmation: You can meet an overlooked routine task with purpose: ask what support would make the biggest difference.",
    "Leadership Affirmation: When a routine task starts receiving less attention, you can listen for the detail that changes the picture.",
    "Leadership Affirmation: You can connect the work to a goal everyone understands when a routine task starts receiving less attention.",
    "Leadership Affirmation: Your leadership matters during an overlooked routine task: you can check understanding without making anyone feel small.",
    "Leadership Affirmation: You can meet an overlooked routine task with purpose: recognize the effort that has already been made.",
    "Leadership Affirmation: When a routine task starts receiving less attention, you can separate what you know from what still needs checking.",
    "Leadership Affirmation: You can strengthen the response by involving the right people when a routine task starts receiving less attention.",
    "Leadership Affirmation: Your leadership matters during an overlooked routine task: you can give someone room to share a useful idea.",
    "Leadership Affirmation: You can meet an overlooked routine task with purpose: agree on who owns the next action.",
    "Leadership Affirmation: When a routine task starts receiving less attention, you can choose a realistic priority the team can act on.",
    "Leadership Affirmation: Your follow-through can turn an offer of support into trust when a routine task starts receiving less attention.",
    "Leadership Affirmation: Your leadership matters during an overlooked routine task: you can use a respectful question to uncover the real obstacle.",
    "Leadership Affirmation: You can meet an overlooked routine task with purpose: model the care you want the team to carry forward.",
    "Leadership Affirmation: When a routine task starts receiving less attention, you can invite feedback on whether your direction is helping.",
]

TRAINER_REMINDER = (
    "Hey trainers! 🐮 Please submit your training reports promptly after any training completed today. Your timely updates are key to keeping training consistent and helping the next trainer pick up where you left off. Share what was covered, progress made, and any areas that need more practice or support. These reports help leadership coordinate training schedules, keep everyone on the same page, and make sure each team member receives the support they need. Thank you for investing in our team and helping everyone grow!"
)

MOBILE_DINE_IN_REMINDER = (
    "Friday Reminder: Please go into Control Point and turn Mobile Dine-In back on "
    "before the end of the day. Thank you!"
)

HOLIDAYS = {
    "12-25": "Merry Christmas! Thank you for leading with excellence and reinforcing standards.",
    "01-01": "Happy New Year! Let’s lead with clarity, consistency, and strong standards.",
}

COVERAGE_PATTERNS = [
    r"\bi can[’']?t make my shift\b",
    r"\bi cant make my shift\b",
    r"\bi can[’']?t make it tomorrow\b",
    r"\bi cant make it tomorrow\b",
    r"\bcan someone cover me tomorrow\b",
    r"\bcan someone cover my shift\b",
    r"\bneed coverage\b",
]

def send_groupme_message(text: str) -> None:
    if not GROUPME_BOT_ID:
        print("ERROR: GROUPME_BOT_ID is missing, cannot send message.")
        return

    url = "https://api.groupme.com/v3/bots/post"
    payload = {"bot_id": GROUPME_BOT_ID, "text": text[:995]}
    print(f"Sending message to GroupMe: {payload}")

    try:
        resp = requests.post(url, json=payload, timeout=15)
        print(f"GroupMe response status: {resp.status_code}, body: {resp.text}")
    except Exception as e:
        print(f"Error sending message to GroupMe: {e}")

def is_coverage_trigger(text: str) -> bool:
    lower_text = text.lower().strip()
    return any(re.search(pattern, lower_text) for pattern in COVERAGE_PATTERNS)

@app.route("/", methods=["GET", "HEAD"])
def health_check():
    return "Eat Mor Chikin is running", 200

@app.route("/groupme_callback", methods=["GET", "POST"])
def groupme_callback():
    if request.method == "GET":
        print("Received GET /groupme_callback")
        return "groupme_callback is alive", 200

    data = request.json or {}
    print("Received callback payload:", data)

    text = data.get("text", "") or ""
    sender_type = data.get("sender_type", "")

    if sender_type == "bot":
        return "ok", 200

    if not text.strip():
        return "ok", 200

    # Beta autonomous rule: coverage reminders only
    if is_coverage_trigger(text):
        send_groupme_message(COVERAGE_REMINDER)
        return "ok", 200

    # Everything else still requires mgmt:
    if not text.lower().startswith("mgmt:"):
        return "ok", 200

    user_question = text[len("mgmt:"):].strip()
    print(f"User question: {user_question}")

    if not OPENAI_API_KEY:
        send_groupme_message("Eat Mor Chikin error: OPENAI_API_KEY missing.")
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
            "Eat Mor Chikin had an error processing that request. Please let a leader know."
        )

    return "ok", 200

@app.route("/scheduled/send", methods=["GET"])
def scheduled_send():
    token = request.args.get("token", "")
    kind = (request.args.get("kind", "") or "").lower().strip()

    if not SCHEDULE_SECRET or token != SCHEDULE_SECRET:
        return "Unauthorized", 401

    if kind == "trainer_reminder":
        msg = TRAINER_REMINDER
    elif kind == "mobile_dine_in_reminder":
        msg = MOBILE_DINE_IN_REMINDER
    elif kind == "affirmation":
        mmdd = datetime.datetime.now().strftime("%m-%d")
        msg = HOLIDAYS.get(mmdd, random.choice(AFFIRMATIONS))
    else:
        return "Bad Request: kind must be affirmation, trainer_reminder, or mobile_dine_in_reminder", 400

    send_groupme_message(msg)
    return "OK", 200

@app.route("/scheduled/release_update", methods=["GET"])
def scheduled_release_update():
    token = request.args.get("token", "")
    if not SCHEDULE_SECRET or token != SCHEDULE_SECRET:
        return "Unauthorized", 401

    send_groupme_message(UPDATE_NOTE)
    return "OK", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
