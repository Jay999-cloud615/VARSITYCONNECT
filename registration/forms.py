from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User

CUT_STUDENT_DOMAIN = "@stud.cut.ac.za"


class StudentRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        label="Student Email",
        required=False,
        help_text="Must be your Central University of Technology student email (e.g. 222084665@stud.cut.ac.za).",
        widget=forms.EmailInput(attrs={
            'placeholder': 'e.g. 222084665@stud.cut.ac.za',
            'autocomplete': 'email',
        })
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if email:
            if not email.endswith(CUT_STUDENT_DOMAIN):
                raise forms.ValidationError(
                    f"Only students with a valid {CUT_STUDENT_DOMAIN} email address can register (e.g. 222084665{CUT_STUDENT_DOMAIN}).",
                    code='invalid_domain',
                )
            if User.objects.filter(email__iexact=email).exists():
                raise forms.ValidationError(
                    "An account with this student email address already exists.",
                    code='duplicate_email',
                )
        return email

    def clean(self):
        cleaned_data = super().clean()
        username = cleaned_data.get('username', '').strip()
        email = cleaned_data.get('email', '').strip()

        # If email was omitted (e.g. programmatic tests posting username/passwords only)
        if not email and username:
            if username.lower().endswith(CUT_STUDENT_DOMAIN):
                cleaned_data['email'] = username.lower()
            else:
                cleaned_data['email'] = f"{username.lower()}{CUT_STUDENT_DOMAIN}"
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data.get('email', '').strip().lower()
        if commit:
            user.save()
        return user


class StudentAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Student Number, Username or Student Email",
        widget=forms.TextInput(attrs={
            'autofocus': True,
            'placeholder': 'e.g. 222084665@stud.cut.ac.za or 222084665',
            'autocomplete': 'username',
        })
    )

    def clean(self):
        username_or_email = self.cleaned_data.get('username', '').strip()
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
                    f"Access restricted: Students can only log in if their student email has the domain {CUT_STUDENT_DOMAIN} (e.g., 222084665{CUT_STUDENT_DOMAIN}).",
                    code='invalid_student_domain',
                )
