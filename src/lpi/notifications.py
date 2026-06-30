import logging
import os
import smtplib
from collections import defaultdict
from email.message import EmailMessage
from dotenv import load_dotenv

from lpi.store import _get_client, get_user_email

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

# Updated templates to include rich data (commit messages, titles)
_NOTIF_TEMPLATES = {
    "pr_merged":        ("PR Merged 🎉", "You merged PR #{pr_number}: '{title}' in {repo}."),
    "commit_pushed":    ("New Commits 📦", "{commit_count} commit(s) pushed to {branch} in {repo}.\nLatest: {last_commit_message}"),
    "phase_advanced":   ("SMILE Phase Advanced ✨", "Goal '{title}' moved to {phase}."),
    "inactivity_alert": ("Inactivity Detected ⚠️", "No activity detected for {days} days."),
    "PullRequestEvent": ("New GitHub PR 🚀", "A PR was created/updated in {repo}."),
    "PushEvent":        ("New GitHub Push 📤", "New commits pushed to {repo}."),
}

def _dispatch_email(target_email: str, title: str, body: str) -> None:
    """Sends the actual email via SMTP."""
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    
    if not SMTP_USER or not SMTP_PASS:
        logger.warning("Email blocked: SMTP credentials are not set in the environment variables.")
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = title
    msg["From"] = SMTP_USER
    msg["To"] = target_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            # server.set_debuglevel(1) # Uncomment to debug SMTP connection
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        logger.info(f"📧 SUCCESS: Email sent to {target_email}")
    except Exception as e:
        logger.exception(f"CRITICAL SMTP ERROR for {target_email}: {e}")

def create_notification_if_new(user_id: str, signal_id: str, event_type: str, payload: dict) -> bool:
    """Records the notification in Supabase and fires off an email."""
    template = _NOTIF_TEMPLATES.get(event_type)
    if not template:
        return False

    title_tmpl, body_tmpl = template
    
    # 1. Safely format the body. 
    # Using defaultdict ensures missing keys in the payload just render as empty strings or defaults, preventing crashes.
    safe_payload = defaultdict(lambda: "[N/A]", payload)
    try:
        body = body_tmpl.format_map(safe_payload)
    except Exception as e:
        logger.warning(f"Error formatting payload: {e}")
        body = body_tmpl # Fallback to raw template if formatting totally fails

    # 2. Insert into Database (Dedup logic)
    try:
        client = _get_client()
        client.table("notifications").insert({
            "user_id":  user_id,
            "signal_id": signal_id,
            "type":     event_type,
            "title":    title_tmpl,
            "body":     body,
        }).execute()
    except Exception as e:
        if "duplicate" in str(e).lower() or "unique" in str(e).lower():
            # DB constraint caught it - exactly what we want for dedup
            return False   
        logger.exception(f"Failed to create notification for signal {signal_id}")
        return False

    # 3. Fetch User Email and Dispatch
    target_email = get_user_email(user_id)
    
    if target_email:
        _dispatch_email(target_email=target_email, title=title_tmpl, body=body)
    else:
        logger.warning(f"No email found in 'users' table for user_id: {user_id}. DB log created, but email skipped.")
        
    return True

if __name__ == "__main__":
    # Test block
    _dispatch_email("test@example.com", "System Test", "Checking SMTP configuration.")