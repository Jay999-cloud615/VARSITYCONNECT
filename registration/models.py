import random
from datetime import timedelta
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

OTP_EXPIRY_MINUTES = 10
RESEND_COOLDOWN_SECONDS = 60


class StudentEmailVerification(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_verification')
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_new_code(self):
        self.otp_code = f"{random.randint(100000, 999999)}"
        self.updated_at = timezone.now()
        self.save()
        return self.otp_code

    def is_expired(self):
        """Returns True if the verification code has exceeded the 10-minute validity window."""
        if not self.updated_at:
            return False
        return timezone.now() > (self.updated_at + timedelta(minutes=OTP_EXPIRY_MINUTES))

    def seconds_until_can_resend(self):
        """Returns remaining seconds before another verification email can be requested."""
        if not self.updated_at:
            return 0
        elapsed = (timezone.now() - self.updated_at).total_seconds()
        remaining = RESEND_COOLDOWN_SECONDS - int(elapsed)
        return max(0, remaining)

    def can_resend(self):
        return self.seconds_until_can_resend() == 0

    def verify_code(self, candidate_code):
        """
        Validates the candidate OTP code.
        Returns a tuple: (is_valid: bool, error_message: str or None).
        """
        if not candidate_code:
            return False, "Please enter the 6-digit verification code."
        candidate = str(candidate_code).strip()
        if len(candidate) != 6 or not candidate.isdigit():
            return False, "The verification code must be exactly 6 digits."
        if self.is_expired():
            return False, "This verification code has expired (codes expire after 10 minutes). Please request a new code below."
        if str(self.otp_code).strip() != candidate:
            return False, "Incorrect verification code. Please check your student inbox and try again."
        return True, None

    def is_valid_code(self, candidate_code):
        valid, _ = self.verify_code(candidate_code)
        return valid

    def __str__(self):
        status = "Verified" if self.is_verified else "Pending"
        return f"{self.user.username} ({self.email}) - {status}"
