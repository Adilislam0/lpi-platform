import logging
import os
import smtplib
from collections import defaultdict
from email.message import EmailMessage

from dotenv import load_dotenv

from lpi.store import _get_client, get_user_email

load_dotenv()
logger = logging.getLogger(__name__)

_NOTIF_TEMPLATES = {
    "PushEvent": ("New GitHub Push 📤", "Activity detected in {repo}.\n\n💡 Insight: {explanation}"),
    "pr_merged":        ("PR Merged 🎉", "You merged PR #{pr_number}: '{title}' in {repo}.\n\n💡 Insight: {explanation}"),
    "commit_pushed":    ("New Commits 📦", "A new push was detected in {repo}.\n\n💡 Insight: {explanation}"),
    "phase_advanced":   ("SMILE Phase Advanced ✨", "Goal '{title}' moved to {phase}."),
    "inactivity_alert": ("Inactivity Detected ⚠️", "No activity detected in {repo} for {days} days."),
    "pr_opened": ("PR Opened 🚀", "{actor} opened PR #{pr_number}: '{title}' in {repo}.\n\n💡 Insight: {explanation}"),
    "goal_created":     ("New Goal Set 🎯", "You created the goal: '{title}'. Time to execute!\n\n💡 Insight: {explanation}"),
    "goal_completed":   ("Goal Completed 🏆", "Congratulations on crossing the finish line for '{title}'!\n\n💡 Insight: {explanation}")
}

def _dispatch_email(target_email: str, title: str, body: str) -> None:
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER")
    SMTP_PASS = os.getenv("SMTP_PASS")
    
    if not SMTP_USER or not SMTP_PASS:
        logger.warning("Email blocked: SMTP credentials missing.")
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg["Subject"] = title
    msg["From"] = SMTP_USER
    msg["To"] = target_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
        logger.info(f"📧 SUCCESS: Email sent to {target_email}")
    except Exception as e:
        logger.exception(f"SMTP ERROR for {target_email}: {e}")

def create_notification_if_new(user_id: str, signal_id: str, event_type: str, payload: dict) -> bool:
    template = _NOTIF_TEMPLATES.get(event_type)
    if not template: 
        return False

    title_tmpl, body_tmpl = template
    safe_payload = defaultdict(lambda: "[N/A]", payload)
    
    # Fallback explanation
    if "explanation" not in safe_payload:
        safe_payload["explanation"] = "Every contribution helps move your project forward."

    try:
        body = body_tmpl.format_map(safe_payload)
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
    except Exception as e:
        if "unique" in str(e).lower(): 
            return False
        logger.exception(f"Failed to record notification: {signal_id}")
        return False

    target_email = get_user_email(user_id)
    if target_email:
        _dispatch_email(target_email, title_tmpl, body)
    return True