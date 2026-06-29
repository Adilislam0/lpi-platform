import logging
import os
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from lpi.store import _get_client

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

# Define notification templates
_NOTIF_TEMPLATES = {
    "pr_merged":        ("PR Merged 🎉", "You merged a PR in {repo}."),
    "commit_pushed":    ("New Commits 📦", "{commit_count} commits pushed to {branch}."),
    "phase_advanced":   ("SMILE Phase Advanced ✨", "Goal '{title}' moved to {phase}."),
    "inactivity_alert": ("Inactivity Detected ⚠️", "No activity detected for {days} days."),
    "PullRequestEvent": ("New GitHub PR 🚀", "A PR was created/updated in {repo}."),
    "PushEvent":        ("New GitHub Push 📤", "New commits pushed to {repo}."),
}

def _dispatch_email(user_id: str, title: str, body: str) -> None:
    print(f"DEBUG: Starting _dispatch_email for {user_id}")
    
    # --- HARDCODE THE EMAIL FOR TESTING ---
    target_email = "your-actual-email@gmail.com"  # REPLACE THIS
    print(f"DEBUG: Using hardcoded email: {target_email}")
    
    # 2. Configure SMTP Credentials
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    
    print(f"DEBUG: SMTP_USER is {SMTP_USER}")
    print(f"DEBUG: SMTP_PASS is {bool(SMTP_PASS)} (True if loaded)")

    if not SMTP_USER or not SMTP_PASS:
        logger.warning("Email blocked: SMTP credentials are not set in the environment variables.")
        return

    # 3. Build the Email
    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = title
    msg["From"] = SMTP_USER
    msg["To"] = target_email

    # 4. Send the Email
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.set_debuglevel(1) # Prints SMTP conversation to terminal
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        logger.info(f"📧 SUCCESS: Email sent to {target_email}")
    except Exception as e:
        print(f"DEBUG: CRITICAL SMTP ERROR: {e}")
        logger.exception(f"Failed to send email to {target_email}: {e}")

def create_notification_if_new(user_id: str, signal_id: str, event_type: str, payload: dict) -> bool:
    template = _NOTIF_TEMPLATES.get(event_type)
    if not template:
        return False

    title_tmpl, body_tmpl = template
    
    try:
        body = body_tmpl.format(**{
            k: payload.get(k, k)
            for k in ["repo", "commit_count", "branch", "title", "phase", "days"]
        })
    except Exception:
        body = body_tmpl

    try:
        client = _get_client()
        client.table("notifications").insert({
            "user_id":  user_id,
            "signal_id": signal_id,
            "type":     event_type,
            "title":    title_tmpl,
            "body":     body,
        }).execute()
        
        _dispatch_email(user_id=user_id, title=title_tmpl, body=body)
        return True
    except Exception as e:
        logger.exception(f"Failed to create notification for signal {signal_id}")
        return False

if __name__ == "__main__":
    _dispatch_email("a6cabc79-6ef8-46eb-9092-ed104f9fd349", "Test Subject", "Test Body")