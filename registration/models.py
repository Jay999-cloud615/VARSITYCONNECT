import random
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


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

    def is_valid_code(self, candidate_code):
        if not candidate_code:
            return False
        return str(self.otp_code).strip() == str(candidate_code).strip()

    def __str__(self):
        status = "Verified" if self.is_verified else "Pending"
        return f"{self.user.username} ({self.email}) - {status}"
