import logging
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


def send_student_otp_email(user, email, otp_code):
    """
    Dispatches a branded, polished OTP verification email to the student's email address.
    Sends both HTML and plain-text versions.
    Returns (success: bool, error_message: str or None).
    """
    subject = f"Your VarsityConnect Verification Code: {otp_code}"
    sender = getattr(settings, 'DEFAULT_FROM_EMAIL', 'VarsityConnect <no-reply@stud.cut.ac.za>')

    plain_message = (
        f"Hello {user.username},\n\n"
        f"Your 6-digit CUT student email verification code is:\n\n"
        f"    {otp_code}\n\n"
        f"This code will expire in 10 minutes.\n\n"
        f"Please enter this code on the verification screen to activate your VarsityConnect account.\n\n"
        f"If you did not create an account on VarsityConnect, please ignore this email.\n\n"
        f"— VarsityConnect Team\n"
        f"Central University of Technology, Free State\n"
    )

    html_message = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Verify your VarsityConnect Student Email</title>
      <style>
        body {{
          margin: 0;
          padding: 0;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
          background-color: #f4f6f9;
          color: #24272b;
        }}
        .email-container {{
          max-width: 560px;
          margin: 32px auto;
          background: #ffffff;
          border-radius: 12px;
          overflow: hidden;
          box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
          border: 1px solid #e2e8f0;
        }}
        .email-header {{
          background: linear-gradient(135deg, #004ba8 0%, #3e78b2 100%);
          padding: 32px 24px;
          text-align: center;
          color: #ffffff;
        }}
        .brand-badge {{
          display: inline-block;
          width: 44px;
          height: 44px;
          line-height: 44px;
          background: rgba(255, 255, 255, 0.2);
          border-radius: 10px;
          font-size: 22px;
          font-weight: 800;
          margin-bottom: 12px;
        }}
        .brand-title {{
          margin: 0;
          font-size: 22px;
          font-weight: 800;
          letter-spacing: -0.3px;
        }}
        .brand-subtitle {{
          margin: 4px 0 0;
          font-size: 13px;
          opacity: 0.9;
        }}
        .email-body {{
          padding: 36px 32px;
          text-align: center;
        }}
        .greeting {{
          font-size: 18px;
          font-weight: 700;
          color: #07070a;
          margin-top: 0;
          margin-bottom: 12px;
        }}
        .intro-text {{
          font-size: 14.5px;
          line-height: 1.6;
          color: #4a525a;
          margin: 0 0 28px;
        }}
        .otp-box {{
          background: #f0f5fc;
          border: 2px dashed #3e78b2;
          border-radius: 12px;
          padding: 20px 24px;
          margin: 0 auto 28px;
          display: inline-block;
        }}
        .otp-label {{
          font-size: 11px;
          font-weight: 700;
          text-transform: uppercase;
          letter-spacing: 1.5px;
          color: #3e78b2;
          margin-bottom: 8px;
        }}
        .otp-digits {{
          font-size: 34px;
          font-weight: 800;
          letter-spacing: 10px;
          color: #004ba8;
          font-family: 'Courier New', Courier, monospace;
        }}
        .timer-notice {{
          font-size: 13px;
          color: #718096;
          margin-bottom: 24px;
        }}
        .security-note {{
          font-size: 12.5px;
          line-height: 1.5;
          color: #a0aec0;
          border-top: 1px solid #edf2f7;
          padding-top: 20px;
          margin-top: 20px;
        }}
        .email-footer {{
          background: #f8fafc;
          padding: 20px 24px;
          text-align: center;
          font-size: 12px;
          color: #718096;
          border-top: 1px solid #e2e8f0;
        }}
      </style>
    </head>
    <body>
      <div class="email-container">
        <div class="email-header">
          <div class="brand-badge">V</div>
          <h1 class="brand-title">VarsityConnect</h1>
          <p class="brand-subtitle">Central University of Technology &bull; Student Hub</p>
        </div>
        <div class="email-body">
          <h2 class="greeting">Hello {user.username}!</h2>
          <p class="intro-text">
            Thank you for registering on <strong>VarsityConnect</strong>. To verify your student email address (<code>{email}</code>) and activate your account, please enter the following 6-digit verification code:
          </p>
          <div class="otp-box">
            <div class="otp-label">Verification Code</div>
            <div class="otp-digits">{otp_code}</div>
          </div>
          <p class="timer-notice">⏱ <strong>This code will expire in 10 minutes.</strong></p>
          <p class="security-note">
            If you did not request this verification code, someone may have entered your student email address by mistake. You can safely ignore this email. Never share this code with anyone.
          </p>
        </div>
        <div class="email-footer">
          &copy; 2026 VarsityConnect &bull; Central University of Technology, Free State.<br>
          This is an automated system notification.
        </div>
      </div>
    </body>
    </html>
    """

    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=sender,
            recipient_list=[email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"[VarsityConnect OTP Email] Successfully sent verification code to {email}")
        return True, None
    except Exception as e:
        error_msg = str(e)
        logger.warning(
            f"[VarsityConnect OTP Email] Failed to send email to {email}: {error_msg}. "
            f"Code generated: {otp_code}"
        )
        # Always output to console for server logs / terminal inspection
        print(f"\n==========================================")
        print(f"[VARSITYCONNECT OTP] Student: {user.username} ({email})")
        print(f"[VARSITYCONNECT OTP] 6-Digit Code: {otp_code}")
        print(f"==========================================\n")
        return False, error_msg
