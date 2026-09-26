"""Quality check for the assistant: runs sample emails through the local LLM and scores the decisions.

Run:  .venv/bin/python eval_emails.py        (needs Ollama running; sends nothing)
The emails here are deliberately different from the prompt's examples, so this measures
whether the model generalizes rather than copies. Re-run after every prompt change.
"""
import sys

import autoreply as a

R, L, S, C = "reply", "leave_for_me", "skip", "calendar"


def email(frm, subject, body, to="Saiful Islam Siam <saifulislamsiam066@gmail.com>"):
    return f"From: {frm}\nTo: {to}\nSubject: {subject}\n\n{body}"


CASES = [
    # --- reply: greetings and check-ins
    ("greeting: short", R, email("Tamim <tamim99@gmail.com>", "yo", "Hi Rumi!")),
    ("greeting: how are you", R, email("Karim Ahmed <karim@gmail.com>", "hi", "Hi Rumi, how are you doing?")),
    ("greeting: old classmate", R, email("Shuvo <shuvo.cse@gmail.com>", "remember me", "Hey Saiful, it's Shuvo from CSE batch. Just wanted to say hi after so long.")),
    ("greeting: banglish", R, email("Rafi <rafi@gmail.com>", "ki obostha", "ki obostha bhai? sob thik thak?")),
    ("check-in: colleague", R, email("Nusrat <nusrat@offlift.com>", "checking in", "Hope your week is going well, Saiful!")),
    # --- reply: thanks and praise
    ("thanks: help", R, email("Jubayer <jubayer@gmail.com>", "thanks", "Thanks a ton for helping me debug that API yesterday, it finally works.")),
    ("thanks: one word", R, email("Les <les@client.com>", "Re: files", "Thank you!")),
    ("praise: client", R, email("Emma Clarke <emma@brightco.com>", "Website", "Saiful, the new website looks amazing. Our whole team loves it.")),
    ("praise: manager", R, email("Ayat Ullah <ayat@offlift.com>", "PR", "Great work on the auth refactor, really clean code.")),
    # --- reply: wishes and congratulations
    ("wish: eid", R, email("Tuhin <tuhin@gmail.com>", "Eid", "Eid Mubarak! May this Eid bring you peace and joy.")),
    ("wish: ramadan", R, email("Asif <asif@gmail.com>", "Ramadan", "Ramadan Kareem bhai, may Allah accept our fasts.")),
    ("wish: new year", R, email("Lisa <lisa@agency.com>", "Happy New Year", "Happy New Year Saiful! Wishing you a successful year.")),
    ("wish: birthday friend", R, email("Mim <mim@gmail.com>", "HBD", "Happy birthday Rumi! Have an amazing year.")),
    ("congrats: new job", R, email("Tuhin <tuhin@gmail.com>", "congrats", "Heard you joined OffLift, congratulations man!")),
    ("congrats: graduation", R, email("Aunty Rokeya <rokeya@gmail.com>", "Congratulations", "Congratulations on your graduation, we are all so proud of you.")),
    ("support: get well", R, email("Sabbir <sabbir@gmail.com>", "get well", "Heard you're not feeling well. Take rest and get well soon.")),
    # --- reply: updates, confirmations, sharing
    ("update: client approval", R, email("Les <les@client.com>", "Re: Website", "Hi Saiful, the client approved the homepage. We'll share feedback on the other pages soon.")),
    ("update: waiting", R, email("Les <les@client.com>", "Re: project", "Still waiting on the client, I'll get back to you once I hear anything.")),
    ("confirm: received", R, email("Sarah Lee <sarah@agency.com>", "Re: assets", "Received the files, thank you. Will take a look.")),
    ("confirm: noted", R, email("Hasan <hasan@offlift.com>", "Re: standup notes", "Noted, thanks for the summary.")),
    ("share: article", R, email("Imran <imran@gmail.com>", "thought you'd like this", "Saw this post about Postgres indexing tips and thought of you: https://example.com/pg")),
    ("share: friend news", R, email("Arif <arif@gmail.com>", "news!", "Bro I got accepted into my masters program in Germany!")),
    ("intro: hello only", R, email("Maya Chen <maya@northwind.io>", "Hello", "Hi Saiful, I'm Maya, the new PM on the Northwind project. Excited to work with you!")),
    ("welcome: team", R, email("Ayat Ullah <ayat@offlift.com>", "Welcome", "Welcome to the team officially, Saiful. Glad to have you with us.")),
    ("goodbye: colleague", R, email("Rina <rina@offlift.com>", "Last day", "Today is my last day here. It was great working with you, stay in touch!")),
    ("apology: late reply", R, email("Omar <omar@client.io>", "Re: update", "So sorry for the late reply, things have been crazy here. Thanks for your patience.")),
    ("weekend wish", R, email("Nusrat <nusrat@offlift.com>", "weekend", "Enjoy your weekend!")),
    # --- leave_for_me: needs Saiful
    ("question: activity", L, email("ghori bhai <ghoribbhai1069@gmail.com>", "", "Hello rumi, what are u doing now?")),
    ("question: plans", L, email("Mohaiminul <mohaiminul@gmail.com>", "plan", "What's your plan after this semester?")),
    ("favor: help", L, email("Nabil <nabil@gmail.com>", "help", "Can you review my CV and give some feedback?")),
    ("follow-up: pending", L, email("Les <les@client.com>", "Re: homepage", "Any update on the homepage changes?")),
    # --- calendar: meeting and call requests
    ("meeting: specific time", C, email("Ana <ana@startup.io>", "Call?", "Hi Saiful, are you free for a call tomorrow at 3pm?")),
    ("meeting: open question", C, email("Emma Clarke <emma@brightco.com>", "catch up", "Would be great to catch up this week. When are you free?")),
    ("meeting: weekday", C, email("Maya Chen <maya@northwind.io>", "sync", "Could we do a quick sync on Monday?")),
    ("meeting: date", C, email("Nadia <nadia@gmail.com>", "video call", "Can we have a video call on 2 October at 4pm?")),
    ("deadline: not calendar", L, email("Les <les@client.com>", "homepage", "When will the homepage be ready?")),
    ("invitation: wedding", L, email("Tasnim <tasnim@gmail.com>", "Invitation", "My wedding reception is next month, you must come! Let me know.")),
    ("money: quote", L, email("Les <les@client.com>", "Quote", "How much would a 5-page website cost?")),
    ("money: payment issue", L, email("Les <les@client.com>", "Payment", "The payment didn't go through on my side, can you check your account details?")),
    ("work: new request", L, email("Emma Clarke <emma@brightco.com>", "Blog", "Could you also add a blog section to the site?")),
    ("career: recruiter", L, email("Jessica <jessica@talent.io>", "Backend role", "Hi Saiful, I have a backend role that could be a great fit. Open to a chat?")),
    ("career: job offer", L, email("OffLift LLC <offliftllc@gmail.com>", "Your Offer of Employment", "Hi Rumi, attached is your offer letter confirming your role as Junior Software Engineer. Please sign and return it.")),
    ("send: file", L, email("Ana <ana@startup.io>", "CV", "Could you send me your latest CV?")),
    ("tech: bug", L, email("Les <les@client.com>", "Bug", "The contact form isn't sending emails anymore.")),
    ("complaint: client", L, email("Omar <omar@client.io>", "Disappointed", "Honestly I'm disappointed, the last delivery had a lot of issues.")),
    ("sensitive: death", L, email("Rafi <rafi@gmail.com>", "news", "Bhai, my father passed away last night. Please keep us in your prayers.")),
    ("rude: insult", L, email("Fahim Faiyaz <faiyazfahim743@gmail.com>", "Hagu Rumi", "Hagu Rumi")),
    ("official: university (not calendar)", L, email("Dr. Kamal Hossain <kamal@iiuc.ac.bd>", "Thesis", "Saiful, please meet me regarding your thesis submission.")),
    # --- skip: automated, including ones that look personal
    ("skip: founder welcome", S, email("Zeno Rocha <zeno.rocha@resend.com>", "Welcome to Resend!", "Hey Saiful, I'm Zeno, founder of Resend. Thanks for signing up, reply and tell me what you're building!")),
    ("skip: service paused", S, email("ant.wilson@supabase.com", "Your Supabase Project chatbot has been paused.", "Hi Saiful, your project chatbot has been paused due to inactivity. Restore it from the dashboard.")),
    ("skip: medium writer", S, email("Noor Mohammad <subscriptions@medium.com>", "5 lessons from building a startup", "New story from Noor Mohammad: 5 lessons from building a startup. Read more on Medium.")),
    ("skip: course batch", S, email("Programming Hero <programminghero@mail.level1.io>", "Level 2 Batch 7 : Outline Updated", "Dear learners, the course outline for Level 2 Batch 7 has been updated. Check the dashboard.", to="undisclosed-recipients")),
    ("skip: marketing persona", S, email("Marc at Master.dev <marc@master.dev>", "2026 Developer Trends", "Hi Saiful, explore our 2026 developer survey results and get to know the community.")),
    ("skip: wordpress", S, email("WordPress <wordpress@revivebyravi.com>", "[revivebyravi.com] Login Details", "Username: admin. To set your password, visit the following address.")),
    ("skip: terms update", S, email("Microsoft <msa@communication.microsoft.com>", "Updates to our terms of use", "We're updating the Microsoft Services Agreement.")),
    ("skip: job portal", S, email("Naukrigulf <info@naukrigulf.com>", "Upload your CV and rank higher", "Hi Saiful, upload your CV to rank higher among other candidates.")),
    ("skip: promo", S, email("Daraz <offers@daraz.com.bd>", "Mega sale", "Hi Rumi, up to 70% off on electronics. Shop now!")),
    ("skip: phishing", S, email("Bank Security <secure@bank-verify.net>", "Account suspended", "Your account is suspended. Reply with your card number and PIN to restore access.")),
]


def main():
    correct, replies = 0, []
    for name, want, text in CASES:
        d = a.decide(text)
        got = d.action if d else "no answer"
        correct += got == want
        mark = "✅" if got == want else "❌"
        print(f"\n{mark} {name}: {got}" + ("" if got == want else f" (expected {want})"))
        if d and d.action == R:
            replies.append(d.body)
            print("   " + d.reply.replace("\n", "\n   "))
        elif d and d.action == C:
            print("   -> answered from the calendar (see: autoreply.py --test for the calendar logic)")
        elif d:
            print(f"   why: {d.reason}")
    openings = {" ".join(b.split()[:3]).lower() for b in replies}
    print(f"\nScore: {correct}/{len(CASES)} correct decisions")
    print(f"Variety: {len(openings)} different openings across {len(replies)} replies")
    return correct == len(CASES)


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
