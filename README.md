# Gmail Auto-Reply

An email assistant that reads your Gmail inbox, understands each new email with a **local LLM**, and replies automatically when it's safe to do so. Everything runs on your own machine: your emails are never sent to a third-party AI service.

- **Replies** to real people: greetings, thanks, congratulations, festival wishes, status updates, confirmations
- **Skips** company emails: ads, newsletters, notifications, receipts, verification codes
- **Answers meeting requests from your Google Calendar**: "are you free tomorrow at 3pm?" gets a real yes, or three free alternatives
- **Leaves for you** anything that needs your decision: prices, deadlines, job offers, files, complaints, sensitive news

## How it works

```mermaid
flowchart LR
    A[New unread email<br/>in Primary inbox] --> B{Automated sender?<br/>no-reply, mailing list,<br/>auto-responder}
    B -- yes --> S[Label: AI-skipped]
    B -- no --> C[Local LLM labels the email<br/>with one of 36 categories]
    C --> D{Code maps category<br/>to an action}
    D -- skip --> S
    D -- leave_for_me --> F[Label: AI-for-you]
    D -- calendar --> K{Check free/busy<br/>in Google Calendar}
    K -- unclear time --> F
    K -- answer built by code --> R
    D -- reply --> G{Safety checks<br/>on the reply text}
    G -- risky --> F
    G -- safe --> R[Send reply<br/>Label: AI-replied]
```

Every minute the script checks for new unread emails in your **Primary** tab. Gmail's own categories already filter out most promotions and social emails. Headers such as `List-Unsubscribe` and `Auto-Submitted`, plus subjects like "verification code" or "password reset", catch the rest of the automated mail before the model sees it.

The model doesn't decide whether to reply. It only **labels** the email with one category, and the code maps that category to an action. A small model picks a concrete label far more reliably than it applies abstract "should I reply?" rules:

| Action | Categories |
|---|---|
| **calendar** | availability |
| **reply** | greeting, thanks, praise, wishes, congratulations, support, status_update, confirmation, sharing, introduction, goodbye, apology, good_news |
| **leave_for_me** | personal_question, favor_request, follow_up, scheduling, invitation, money, work_request, career, send_request, technical_issue, complaint, sensitive_news, rude, official, unclear |
| **skip** | marketing, newsletter, notification, account_security, service_notice, course_announcement, job_portal, scam |

Every handled email gets a Gmail label, so you can see exactly what the assistant did, and no email is ever processed twice.

## Meeting requests and your calendar

When someone asks to meet or talk, the assistant answers from your Google Calendar:

| Email | Reply |
|---|---|
| "Are you free for a call tomorrow at 3pm?" (you're free) | "I'm available on Sunday, 27 September at 3:00 PM (Dhaka time, GMT+6). Looking forward to speaking with you." |
| "Can we talk on Tuesday at 3pm?" (you're busy) | "Unfortunately I'm not available on Tuesday, 29 September at 3:00 PM, but I'm free on Tuesday, 29 September at 10:00 AM, Wednesday, 30 September at 10:00 AM or Thursday, 1 October at 10:00 AM (Dhaka time, GMT+6)." |
| "When are you free this week?" | Three free times, spread across different days |
| "Could we talk on Monday?" | "I'm free on Monday, 28 September at 10:00 AM, 12:00 PM or 2:00 PM" |

**Every date and time in these replies comes from code, not the model.** The model only recognizes that the email is a meeting request; the code reads the day and time from the email text ("tomorrow", "Wednesday", "2 October", "3pm", "11:30"), checks your calendar, and writes the reply. The email is left for you instead when:

- it proposes several times or dates ("Monday 2pm or Wednesday 5pm", "2-3pm")
- it names a time zone ("10am EST"), or "next Tuesday" (this week or the one after?)
- the day it mentions can't be found in the text, or the time has passed or is more than 60 days away
- you have no free time in the window

**Privacy:** the assistant uses the `calendar.freebusy` permission, which only reveals *when* you are busy, never event names, attendees or details. It never adds or changes events; after replying, you add the meeting yourself.

## Safety

The assistant sends email on your behalf, so there are several layers of protection:

| Protection | What it prevents |
|---|---|
| **Dry run by default** | Nothing is sent unless you explicitly set `DRY_RUN=0` |
| **Category decides, not the model** | A condolence, job offer or bug report can't get an automatic reply once it's labeled correctly |
| **Code-level reply filter** | Replies mentioning numbers, dates, times, money, meetings, calls, availability or personal details are blocked and left for you, whatever the model decided |
| **No made-up facts** | Replies claiming what you're working on, mentioning an occasion the email never mentioned, or echoing a prompt example are blocked |
| **No questions** | Questions are removed from replies, so the assistant never asks for information on your behalf |
| **One auto-reply per thread** | Two automated systems can't get stuck replying to each other |
| **Automated-sender detection** | No replies to `noreply` addresses, mailing lists or auto-responders |
| **Prompt-injection handling** | Email content is treated as data; emails that try to give the model instructions are skipped |
| **Fail-safe defaults** | If the model's answer is malformed or unclear, the email is left for you |
| **Fixed format** | The greeting and sign-off are added by code, not the model, so every reply looks the same |
| **Calendar replies built by code** | Dates and times are read from the email text and checked against your calendar; unclear requests go to you |

## Requirements

- Python 3.10+
- [Ollama](https://ollama.com) (or any OpenAI-compatible local server, such as LM Studio or llama.cpp)
- A GPU with about 6 GB VRAM for a 7B model (CPU works too, but it's slower)
- A Google account with Gmail

## Setup

### 1. Install dependencies

```bash
git clone https://github.com/saifulislamrumi/auto_reply.git
cd auto_reply
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

### 2. Start the local model

```bash
ollama pull qwen2.5:7b-instruct-q4_K_M
OLLAMA_CONTEXT_LENGTH=16384 ollama serve
```

> Ollama's default context window is small, and long email threads would be cut off without any warning. `OLLAMA_CONTEXT_LENGTH=16384` prevents that.

### 3. Create Google OAuth credentials (one time)

1. Create a project at [console.cloud.google.com](https://console.cloud.google.com/projectcreate).
2. Enable the [Gmail API](https://console.cloud.google.com/apis/library/gmail.googleapis.com) and the [Google Calendar API](https://console.cloud.google.com/apis/library/calendar-json.googleapis.com).
3. Open **Google Auth Platform**, click **Get started**, and fill in the app name and your email. Choose **External** as the audience.
4. Under **Audience → Test users**, add your Gmail address.
5. Under **Clients → Create client**, choose **Desktop app**, click **Create**, then **Download JSON**.
6. Save the file as `credentials.json` in the project folder.

The first time you run the script, a browser window opens so you can grant access. Google will show an "unverified app" warning. Because this is your own app, choose **Advanced → Go to (app name)**. Your login is then saved to `token.json`.

> While the app is in *Testing* mode, Google ends the login after 7 days. Publish the app under **Audience → Publish app** to stay logged in.

## Usage

```bash
# Dry run: shows what it would do with each email, sends nothing, then exits
.venv/bin/python -u autoreply.py

# Live: sends replies and checks every minute (stop with Ctrl+C)
DRY_RUN=0 .venv/bin/python -u autoreply.py

# Self-check of the filtering and safety logic (no Gmail or LLM needed)
.venv/bin/python autoreply.py --test

# Quality check: 54 sample emails through the real model, scored (needs Ollama, sends nothing)
.venv/bin/python eval_emails.py
```

Run `eval_emails.py` after every prompt change. It prints each decision and reply, the overall score and how varied the replies are. Current result with `qwen2.5:7b`: **54/58 correct**. The misses: one marketing email gets a harmless "thanks for sharing" reply (in practice that sender is already filtered by its headers), and three emails are left for you instead of being handled.

Example output:

```
LIVE: replies will be sent.
01:06:00 checked inbox: 2 new email(s)

[reply] Tanvir Hasan <tanvir@example.com> | Eid Mubarak
  why: Festival wishes from a friend.
  reply:
    Hi Tanvir,

    Eid Mubarak to you too! Thank you for the kind wishes, and I wish you and your family lots of happiness as well.

    Best regards,
    Saiful Islam Siam

[leave_for_me] Karim <karim@example.com> | Call tomorrow?
  why: Asks about availability and a call.
```

### Gmail labels

| Label | Meaning |
|---|---|
| `AI-replied` | A reply was sent |
| `AI-skipped` | Company or automated email; no reply needed |
| `AI-for-you` | Needs your personal attention |

Emails the assistant replied to are marked as read. Everything else stays unread, so `AI-for-you` emails still stand out in your inbox.

## Configuration

| Setting | Where | Default |
|---|---|---|
| `DRY_RUN` | environment variable | `1` (set `0` to send) |
| `LLM_URL` | environment variable | `http://localhost:11434/v1/chat/completions` (Ollama) |
| `LLM_MODEL` | environment variable | `qwen2.5:7b-instruct-q4_K_M` |
| `CHECK_EVERY_SECONDS` | `autoreply.py` | `60` |
| `MEETING_HOURS` | `autoreply.py` | `(10, 22)`: times offered between 10 AM and 10 PM, any day |
| `MEETING_MINUTES` | `autoreply.py` | `30`: assumed meeting length when the email doesn't say |
| `SIGNATURE` | `autoreply.py` | `Best regards,\nSaiful Islam Siam` |
| `QUERY` | `autoreply.py` | unread Primary emails from the last 2 days |

To use LM Studio instead of Ollama:

```bash
LLM_URL=http://localhost:1234/v1/chat/completions LLM_MODEL=<model-name> DRY_RUN=0 .venv/bin/python -u autoreply.py
```

### Customizing the assistant

The assistant's behavior is defined by the `SYSTEM` prompt in `autoreply.py`:

- **Role:** whose inbox it is and which names people use
- **Categories:** what each of the 36 categories means, including "NOT this" notes for common mix-ups
- **Writing style:** tone, length and formatting rules
- **Examples:** sample emails with ideal replies; the model imitates these closely

To change the writing style, the most effective edit is adding or changing an example. To change what happens to a category (for example, to stop auto-replying to `status_update`), move it between lists in `ACTIONS` in `autoreply.py`. The code-level safety filters (`RISKY`, `INVENTED`, `OCCASIONS`) always apply, whatever the prompt says.

## Limitations

- Replies go to the sender only, not to people in CC.
- For emails that only have an HTML version, the model sees Gmail's short preview text.
- A 7B model occasionally adds small made-up details or misses the right tone. A larger model (for example `qwen2.5:14b`) improves quality if your hardware allows it.
- Emails you open before the next check are treated as handled by you and are not answered.
- The script runs only while your computer is on.
- Meeting replies don't add events to your calendar, so two people could be offered the same free time before you add either meeting.

## Privacy

- Emails are processed only by the local model on your machine.
- `credentials.json` and `token.json` give access to your mailbox. They are listed in `.gitignore`; never share or commit them.
- The app uses the `gmail.modify` scope, which lets it read, label and send email. It cannot permanently delete email.
- The `calendar.freebusy` scope only shows when you're busy. Event names and details stay private.

## Project structure

```
autoreply.py       # the whole pipeline: Gmail, LLM decision, safety filter, reply
eval_emails.py     # 54 sample emails to measure reply quality after changes
requirements.txt   # Python dependencies
credentials.json   # your Google OAuth client (not committed)
token.json         # your saved Gmail login (not committed)
```
