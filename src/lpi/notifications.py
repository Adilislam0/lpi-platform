import logging
import os
import smtplib
from email.message import EmailMessage

from lpi.store import _get_client

logger = logging.getLogger(__name__)

# Define what your email subjects and bodies should look like
_NOTIF_TEMPLATES = {
    "pr_merged":        ("PR Merged 🎉", "You merged a PR in {repo}."),
    "commit_pushed":    ("New Commits 📦", "{commit_count} commits pushed to {branch}."),
    "phase_advanced":   ("SMILE Phase Advanced ✨", "Goal '{title}' moved to {phase}."),
    "inactivity_alert": ("Inactivity Detected ⚠️", "No activity detected for {days} days."),
    "PullRequestEvent": ("New GitHub PR 🚀", "A PR was created/updated in {repo}."),
    "PushEvent":        ("New GitHub Push 📤", "New commits pushed to {repo}."),
}

def _dispatch_email(user_id: str, title: str, body: str) -> None:
    """
    Fetches the user's email from Supabase and sends a real email via SMTP.
    """
    client = _get_client()
    
    # 1. Fetch the user's email from the Supabase 'users' table
    # (If your database uses a 'profiles' table instead, update the table name below)
    try:
        user_data = client.table("users").select("email").eq("id", user_id).execute()
        if not user_data.data:
            logger.error(f"Email dispatch failed: No email found for user {user_id}")
            return
            
        target_email = user_data.data[0]["email"]
    except Exception as e:
        logger.error(f"Failed to fetch user email from Supabase: {e}")
        return

    # 2. Configure SMTP Credentials
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER") 
    SMTP_PASS = os.getenv("SMTP_PASS") 
    
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
            server.starttls() # Secure the connection
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
            
        logger.info(f"📧 SUCCESS: Email sent to {target_email} for user {user_id}")
        
    except Exception as e:
        logger.exception(f"Failed to send email to {target_email}: {e}")


def create_notification_if_new(
    user_id: str,
    signal_id: str,
    event_type: str,
    payload: dict,
) -> bool:
    """
    Attempts to log a notification. Returns True if successful (new), 
    or False if it was a duplicate.
    """
    template = _NOTIF_TEMPLATES.get(event_type)
    if not template:
        return False

    title_tmpl, body_tmpl = template
    
    # Safely format the body string with data from the payload
    try:
        body = body_tmpl.format(**{
            k: payload.get(k, k)
            for k in ["repo", "commit_count", "branch", "title", "phase", "days"]
        })
    except Exception:
        body = body_tmpl

    try:
        # Use the existing Supabase client setup
        client = _get_client()
        client.table("notifications").insert({
            "user_id":  user_id,
            "signal_id": signal_id,
            "type":     event_type,
            "title":    title_tmpl,
            "body":     body,
        }).execute()
        
        # --- TRIGGER EMAIL HERE ---
        # Because we got past the DB insert, we know definitively that this is NOT a duplicate.
        _dispatch_email(user_id=user_id, title=title_tmpl, body=body)
        
        return True

    except Exception as e:
        error_str = str(e).lower()
        
        # If Postgres blocks it due to the UNIQUE constraint, catch it quietly
        if "duplicate" in error_str or "unique" in error_str or "23505" in error_str:
            logger.debug(f"Duplicate signal {signal_id} detected. Email blocked.")
            return False 
            
        logger.exception(f"Failed to create notification for signal {signal_id}")
        return False