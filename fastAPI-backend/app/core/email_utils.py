import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.config import settings


def _build_otp_email(otp: str, purpose: str, new_value: str) -> tuple[str, str]:
    if purpose == "change_email":
        subject = "Verify your new email address"
        action_label = "confirm your new email address"
        detail_line = f"<p>Your new email: <strong>{new_value}</strong></p>"
    else:
        subject = "Verify your phone number change"
        action_label = "confirm your phone number change"
        detail_line = f"<p>New phone number: <strong>{new_value}</strong></p>"

    html_body = f"""
    <html>
      <body style="font-family: Arial, sans-serif; color: #333; max-width: 480px; margin: auto;">
        <h2>Verification Code</h2>
        <p>Use the OTP below to {action_label}:</p>
        {detail_line}
        <div style="
          background: #f0f4ff;
          border: 1px solid #c0caff;
          border-radius: 8px;
          padding: 16px 32px;
          font-size: 32px;
          font-weight: bold;
          letter-spacing: 8px;
          display: inline-block;
          margin: 16px 0;
        ">{otp}</div>
        <p style="color: #888; font-size: 13px;">
          This code expires in <strong>10 minutes</strong>.<br>
          If you did not request this, please ignore this email.
        </p>
      </body>
    </html>
    """
    return subject, html_body


def _send_sync(msg: MIMEMultipart, to_email: str):
    with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
        server.ehlo()
        if settings.SMTP_USE_TLS:
            server.starttls()
        server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
        server.sendmail(settings.SMTP_FROM_EMAIL, to_email, msg.as_string())


async def send_otp_email(to_email: str, otp: str, purpose: str, new_value: str):
    subject, html_body = _build_otp_email(otp, purpose, new_value)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = settings.SMTP_FROM_EMAIL
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html"))

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, _send_sync, msg, to_email)