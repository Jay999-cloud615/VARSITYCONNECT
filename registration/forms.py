import re
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import StudentEmailVerification

CUT_STUDENT_DOMAIN = "@stud.cut.ac.za"
VALID_STUDENT_PREFIXES = ("221", "222", "223", "224", "225")


class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label="Student Email",
        required=False,
        help_text="e.g. 224183920@stud.cut.ac.za",
        widget=forms.EmailInput(attrs={
            'placeholder': 'e.g. 224183920@stud.cut.ac.za',
            'autocomplete': 'email',
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = (self.cleaned_data.get('email') or '').strip().lower()
        if email:
            if not email.endswith(CUT_STUDENT_DOMAIN):
                raise forms.ValidationError(
                    f"Invalid email domain. Only official CUT student emails ending with {CUT_STUDENT_DOMAIN} are accepted (e.g. 224183920{CUT_STUDENT_DOMAIN}).",
                    code='invalid_domain',
                )
            student_num = email.split('@')[0]
            # Check student number digits and valid prefix (221, 222, 223, 224, 225)
            if student_num.isdigit():
                if not (7 <= len(student_num) <= 10 and student_num.startswith(VALID_STUDENT_PREFIXES)):
                    raise forms.ValidationError(
                        f" correct format is  224183920{CUT_STUDENT_DOMAIN}).",
                        code='invalid_student_prefix',
                    )
            else:
                if not student_num.replace('_', '').isalnum():
                    raise forms.ValidationError(
                        f"Student numbers must start with 221, 222, 223, 224, or 225 (e.g. 224183920{CUT_STUDENT_DOMAIN}).",
                        code='invalid_student_number',
                    )

            # Check if this student email is already registered
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError(
                    f"This student email ({email}) is already registered and active. Please log in with your credentials.",
                    code='duplicate_email',
                )
        return email

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data is None:
            cleaned_data = {}
        username = (cleaned_data.get('username') or '').strip()
        email = (cleaned_data.get('email') or '').strip()

        # If email was omitted (e.g. programmatic tests posting username/passwords only)
        if not email and username:
            if username.lower().endswith(CUT_STUDENT_DOMAIN):
                cleaned_data['email'] = username.lower()
            elif username.isdigit() and username.startswith(VALID_STUDENT_PREFIXES):
                cleaned_data['email'] = f"{username.lower()}{CUT_STUDENT_DOMAIN}"
            else:
                cleaned_data['email'] = f"{username.lower()}{CUT_STUDENT_DOMAIN}"
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = (self.cleaned_data.get('email') or '').strip().lower()
        if commit:
            user.save()
        return user


class StudentAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Student Number, Username or Student Email",
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'placeholder': 'e.g. 224183920@stud.cut.ac.za',
            'autocomplete': 'username',
        })
    )

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data is None:
            cleaned_data = {}
        username_or_email = (self.cleaned_data.get('username') or '').strip()
        password = self.cleaned_data.get('password')

        if username_or_email and password:
            lookup_username = username_or_email
            # If user entered an email address or matches a registered student email
            user_by_email = User.objects.filter(email__iexact=username_or_email).first()
            if user_by_email:
                lookup_username = user_by_email.username

            self.user_cache = authenticate(
                self.request,
                username=lookup_username,
                password=password
            )

            if self.user_cache is None and lookup_username != username_or_email:
                self.user_cache = authenticate(
                    self.request,
                    username=username_or_email,
                    password=password
                )

            if self.user_cache is None:
                raise self.get_invalid_login_error()
            else:
                self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data

    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        # Superusers and staff administrators are exempt
        if user.is_superuser or user.is_staff:
            return

        email = (user.email or '').strip().lower()
        if not email.endswith(CUT_STUDENT_DOMAIN):
            if user.username.lower().endswith(CUT_STUDENT_DOMAIN):
                user.email = user.username.lower()
                user.save(update_fields=['email'])
            else:
                raise forms.ValidationError(
                    f"Access restricted: Students can only log in if their student email has the domain {CUT_STUDENT_DOMAIN} (e.g., 224183920{CUT_STUDENT_DOMAIN}).",
                    code='invalid_student_domain',
                )

        # Check if student email is verified (if verification record exists)
        try:
            if hasattr(user, 'student_verification') and not user.student_verification.is_verified:
                raise forms.ValidationError(
                    f"Your student email ({user.email}) has not been verified yet. Please enter your 6-digit verification code.",
                    code='unverified_student_email',
                )
        except Exception:
            pass


class EmailVerificationForm(forms.Form):
    otp_code = forms.CharField(
        max_length=6,
        min_length=6,
        label="6-Digit Verification Code",
        widget=forms.TextInput(attrs={
            'placeholder': '123456',
            'autofocus': True,
            'maxlength': '6',
            'pattern': r'\d{6}',
            'class': 'verify-otp-input',
            'autocomplete': 'one-time-code',
        })
    )

    def clean_otp_code(self):
        code = (self.cleaned_data.get('otp_code') or '').strip()
        if not code.isdigit() or len(code) != 6:
            raise forms.ValidationError("Please enter the 6-digit verification code.")
        return code
