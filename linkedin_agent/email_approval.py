import os
import time
import smtplib
import imaplib
import email
from email.message import EmailMessage
from email.header import decode_header, make_header
from dotenv import load_dotenv

load_dotenv(override=True)
EMAIL = os.getenv("EMAIL_ADDRESS")
PASSWORD = os.getenv("EMAIL_APP_PASSWORD")


def send_email(subject, body):
    """Send an email to yourself through Gmail."""
    message = EmailMessage()
    message["From"] = EMAIL
    message["To"] = EMAIL
    message["Subject"] = subject
    message.set_content(body)
    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(EMAIL, PASSWORD)
        server.send_message(message)


def get_text(message):
    """Get the plain text of an email."""
    if message.is_multipart():
        for part in message.walk():
            if part.get_content_type() == "text/plain" and not part.get_filename():
                charset = part.get_content_charset() or "utf-8"
                return part.get_payload(decode=True).decode(charset, errors="ignore")
        return ""
    charset = message.get_content_charset() or "utf-8"
    return message.get_payload(decode=True).decode(charset, errors="ignore")


def check_reply(code):
    """Look for your reply. Returns 'YES', 'NO', or None."""
    mail = imaplib.IMAP4_SSL("imap.gmail.com")
    mail.login(EMAIL, PASSWORD)
    try:
        mail.select("INBOX")
        status, data = mail.search(None, f'(SUBJECT "{code}")')
        for number in data[0].split():
            status, message_data = mail.fetch(number, "(BODY.PEEK[])")
            message = email.message_from_bytes(message_data[0][1])
            subject = str(make_header(decode_header(message["Subject"] or "")))
            if not subject.lower().startswith("re"):
                continue  # this is the agent's own email, not your reply

            lines = [line.strip() for line in get_text(message).splitlines() if line.strip()]
            first_line = lines[0].upper() if lines else ""
            if first_line.startswith("NO"):
                return "NO"
            if first_line.startswith("YES"):
                return "YES"
    finally:
        mail.logout()
    return None


def wait_for_reply(code, minutes=120, check_every=60):
    """Check the inbox every minute until you reply or time runs out."""
    print(f"📬 Waiting up to {minutes} minutes for your reply...")
    end_time = time.time() + minutes * 60
    while time.time() < end_time:
        try:
            decision = check_reply(code)
            if decision:
                print(f"   📩 You replied: {decision}")
                return decision
        except Exception as error:
            print(f"   (inbox check failed: {str(error)[:60]})")
        time.sleep(check_every)
    print("   ⏰ No reply. Time is up.")
    return "TIMEOUT"


if __name__ == "__main__":
    send_email("[LinkedIn Agent TEST1] Test email",
               "This is a test from your agent.\n\nReply YES or NO to this email.")
    print("✅ Test email sent! Reply YES or NO from your phone.")
    print("Result:", wait_for_reply("TEST1", minutes=5, check_every=20))