"""
Transactional email service.

Provider is swappable via the EMAIL_PROVIDER env var:
  - "resend" (default): uses https://resend.com HTTP API
  - "ses": uses AWS SES in AWS_REGION (requires domain/sender verification + production access)

Handles: password reset, signup welcome, form submission notifications,
account approval notifications, and admin alerts.

Usage:
    from app.utils.email import send_password_reset, send_welcome, send_form_notification
"""

import asyncio
import logging
import os
from concurrent.futures import ThreadPoolExecutor

import httpx

logger = logging.getLogger(__name__)

SENDER = os.getenv("EMAIL_SENDER", os.getenv("RESEND_SENDER_EMAIL", "noreply@meydanfzai.com"))
RESEND_API_KEY = os.getenv("RESEND_API_KEY", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://meydanfzai.com")
EMAIL_PROVIDER = os.getenv("EMAIL_PROVIDER", "resend").lower()

_executor = ThreadPoolExecutor(max_workers=2)


def _send_via_resend(to: str, subject: str, html_body: str, text_body: str = ""):
    """Send via Resend HTTP API."""
    if not RESEND_API_KEY:
        logger.warning("[EMAIL] RESEND_API_KEY not set — skipping email to %s", to)
        return

    try:
        resp = httpx.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            json={
                "from": f"Meydan Free Zone <{SENDER}>",
                "to": [to],
                "subject": subject,
                "html": html_body,
            },
            timeout=10,
        )
        if resp.status_code >= 400:
            logger.error(f"[EMAIL] Resend API error {resp.status_code}: {resp.text} (to={to})")
        else:
            logger.info(f"[EMAIL] Sent '{subject}' to {to} via resend")
    except Exception as e:
        logger.error(f"[EMAIL] Failed to send '{subject}' to {to} via resend: {e}")


def _send_via_ses(to: str, subject: str, html_body: str, text_body: str = ""):
    """Send via AWS SES in the current AWS_REGION."""
    try:
        import boto3

        ses = boto3.client("ses", region_name=os.getenv("AWS_REGION", "ap-southeast-1"))
        body = {"Html": {"Data": html_body, "Charset": "UTF-8"}}
        if text_body:
            body["Text"] = {"Data": text_body, "Charset": "UTF-8"}

        ses.send_email(
            Source=f"Meydan Free Zone <{SENDER}>",
            Destination={"ToAddresses": [to]},
            Message={
                "Subject": {"Data": subject, "Charset": "UTF-8"},
                "Body": body,
            },
        )
        logger.info(f"[EMAIL] Sent '{subject}' to {to} via ses")
    except Exception as e:
        logger.error(f"[EMAIL] Failed to send '{subject}' to {to} via ses: {e}")


def _send_raw(to: str, subject: str, html_body: str, text_body: str = ""):
    """Dispatch to the configured email provider."""
    if EMAIL_PROVIDER == "ses":
        _send_via_ses(to, subject, html_body, text_body)
    else:
        _send_via_resend(to, subject, html_body, text_body)


def send_email_bg(to: str, subject: str, html_body: str, text_body: str = ""):
    """Fire-and-forget email send (non-blocking)."""
    try:
        loop = asyncio.get_running_loop()
        loop.run_in_executor(_executor, _send_raw, to, subject, html_body, text_body)
    except RuntimeError:
        # No event loop — run directly (e.g. in tests)
        _send_raw(to, subject, html_body, text_body)


# ── Email wrapper ─────────────────────────────────────────────────

def _base_template(content: str) -> str:
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
body {{ margin:0; padding:0; background:#f4f5f7; font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif; }}
.wrap {{ max-width:560px; margin:40px auto; background:#fff; border-radius:12px; overflow:hidden; box-shadow:0 2px 12px rgba(0,0,0,0.08); }}
.header {{ background:linear-gradient(135deg,#1a1a2e,#16213e); padding:28px 32px; text-align:center; }}
.header img {{ height:32px; }}
.header h2 {{ color:#fff; margin:12px 0 0; font-size:18px; font-weight:600; }}
.body {{ padding:32px; color:#333; line-height:1.7; font-size:15px; }}
.body h3 {{ color:#1a1a2e; margin:0 0 12px; }}
.btn {{ display:inline-block; background:linear-gradient(135deg,#4f46e5,#7c3aed); color:#fff !important; padding:12px 28px; border-radius:8px; text-decoration:none; font-weight:600; font-size:15px; margin:20px 0; }}
.footer {{ padding:20px 32px; background:#f9fafb; text-align:center; font-size:12px; color:#9ca3af; border-top:1px solid #e5e7eb; }}
.field {{ background:#f4f5f7; padding:10px 14px; border-radius:6px; margin:6px 0; font-size:14px; }}
.field strong {{ color:#1a1a2e; }}
</style></head>
<body><div class="wrap">
<div class="header"><h2>Meydan Free Zone</h2></div>
<div class="body">{content}</div>
<div class="footer">Meydan Free Zone AI Website Generator<br>&copy; 2026 Meydan Free Zone. All rights reserved.</div>
</div></body></html>"""


# ── Specific email types ──────────────────────────────────────────

def send_password_reset(to: str, reset_token: str):
    """Send password reset link."""
    reset_url = f"{FRONTEND_URL}/reset-password?token={reset_token}"
    html = _base_template(f"""
<h3>Password Reset</h3>
<p>We received a request to reset your password. Click the button below to set a new password:</p>
<p style="text-align:center"><a href="{reset_url}" class="btn">Reset Password</a></p>
<p style="font-size:13px;color:#6b7280;">This link expires in 1 hour. If you didn't request this, you can safely ignore this email.</p>
""")
    send_email_bg(to, "Reset Your Password — Meydan Free Zone", html)


def send_welcome(to: str, full_name: str = ""):
    """Send welcome email after signup."""
    name = full_name or "there"
    html = _base_template(f"""
<h3>Welcome to Meydan Free Zone!</h3>
<p>Hi {name},</p>
<p>Thank you for signing up for the Meydan Free Zone AI Website Generator. Your account has been created successfully.</p>
<p>Your account is pending admin approval. Once approved, you can start building your website right away.</p>
<p style="text-align:center"><a href="{FRONTEND_URL}/login" class="btn">Sign In</a></p>
<p style="font-size:13px;color:#6b7280;">We'll notify you by email once your account is approved.</p>
""")
    send_email_bg(to, "Welcome to Meydan Free Zone!", html)


def send_email_verification(to: str, verification_token: str, full_name: str = ""):
    """Send email verification link after signup. User must click before admin can approve."""
    name = full_name or "there"
    verify_url = f"{FRONTEND_URL}/verify-email?token={verification_token}"
    html = _base_template(f"""
<h3>Confirm Your Email</h3>
<p>Hi {name},</p>
<p>Thanks for signing up for the Meydan Free Zone AI Website Generator. Please confirm your email address by clicking the button below — this is required before your account can be reviewed for approval.</p>
<p style="text-align:center"><a href="{verify_url}" class="btn">Confirm Email</a></p>
<p style="font-size:13px;color:#6b7280;">After confirming, an admin will review your account and notify you once it's approved.</p>
<p style="font-size:13px;color:#6b7280;">If you didn't sign up, you can safely ignore this email.</p>
""")
    send_email_bg(to, "Confirm your email — Meydan Free Zone", html)


def send_approval_notification(to: str, full_name: str = ""):
    """Notify user that their account has been approved."""
    name = full_name or "there"
    html = _base_template(f"""
<h3>Account Approved!</h3>
<p>Hi {name},</p>
<p>Great news — your Meydan Free Zone account has been approved! You can now start building your website.</p>
<p style="text-align:center"><a href="{FRONTEND_URL}/login" class="btn">Start Building</a></p>
<p style="font-size:13px;color:#6b7280;">Log in to your dashboard and use the AI website generator to create your business website in minutes.</p>
""")
    send_email_bg(to, "Your Account is Approved — Meydan Free Zone", html)


def send_form_notification(to: str, site_name: str, fields: dict, source_page: str = ""):
    """Notify site owner about a new contact form submission."""
    # Build fields HTML
    fields_html = ""
    for key, value in fields.items():
        if key.startswith("_"):
            continue
        label = key.replace("_", " ").title()
        fields_html += f'<div class="field"><strong>{label}:</strong> {value}</div>\n'

    page_info = f" (from {source_page})" if source_page else ""
    html = _base_template(f"""
<h3>New Form Submission</h3>
<p>You received a new contact form submission on <strong>{site_name}</strong>{page_info}:</p>
{fields_html}
<p style="text-align:center"><a href="{FRONTEND_URL}/dashboard#inbox" class="btn">View in Inbox</a></p>
<p style="font-size:13px;color:#6b7280;">You can view and manage all submissions in your dashboard inbox.</p>
""")
    send_email_bg(to, f"New message on {site_name} — Meydan Free Zone", html)


def send_admin_new_signup(admin_email: str, user_email: str, full_name: str = "", company_name: str = ""):
    """Notify admin about a new user signup."""
    html = _base_template(f"""
<h3>New User Signup</h3>
<p>A new user has signed up and is awaiting approval:</p>
<div class="field"><strong>Email:</strong> {user_email}</div>
<div class="field"><strong>Name:</strong> {full_name or 'Not provided'}</div>
<div class="field"><strong>Company:</strong> {company_name or 'Not provided'}</div>
<p style="text-align:center"><a href="{FRONTEND_URL}/admin" class="btn">Review in Admin Panel</a></p>
""")
    send_email_bg(admin_email, f"New Signup: {user_email} — Meydan Free Zone", html)
