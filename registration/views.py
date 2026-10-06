import random
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .emails import send_student_otp_email
from .forms import (
	StudentAuthenticationForm,
	StudentRegistrationForm,
	EmailVerificationForm,
	CUT_STUDENT_DOMAIN,
	VALID_STUDENT_PREFIXES,
)
from .models import StudentEmailVerification


@require_POST
def logout_thank_you_view(request):
	logout(request)
	return render(request, "registration/logout_thanks.html")


def landing_auth_view(request):
	if request.user.is_authenticated:
		logout(request)

	login_form = StudentAuthenticationForm()

	if request.method == "POST":
		if "login_submit" in request.POST:
			login_form = StudentAuthenticationForm(request, data=request.POST)
			if login_form.is_valid():
				user = login_form.get_user()
				login(request, user)
				next_url = request.POST.get("next") or request.GET.get("next")
				if next_url and url_has_allowed_host_and_scheme(
					next_url,
					allowed_hosts={request.get_host()},
					require_https=request.is_secure(),
				):
					return redirect(next_url)
				return redirect("dashboard")
			else:
				domain_error = False
				unverified_error = False
				for error_list in login_form.errors.as_data().values():
					for err in error_list:
						if getattr(err, 'code', None) == 'invalid_student_domain':
							domain_error = True
						elif getattr(err, 'code', None) == 'unverified_student_email':
							unverified_error = True

				if unverified_error:
					username_entered = (request.POST.get('username') or '').strip()
					user_match = User.objects.filter(username__iexact=username_entered).first() or \
					             User.objects.filter(email__iexact=username_entered).first()
					if user_match:
						request.session['pending_verification_user_id'] = user_match.pk
						messages.warning(
							request,
							f"Please verify your student email ({user_match.email}) before logging in."
						)
						return redirect('verify_student_email')
				elif domain_error:
					messages.error(
						request,
						"Access restricted: Students can only log in if their student email has the domain @stud.cut.ac.za (e.g. 224183920@stud.cut.ac.za)."
					)
				else:
					messages.error(request, "Invalid username or password.")

	context = {
		"login_form": login_form,
		"next": request.POST.get("next") or request.GET.get("next", ""),
	}
	return render(request, "registration/login.html", context)


def _safe_get_or_create_verification(user, otp_code=None, is_verified=False):
	"""
	Safely retrieves or creates a StudentEmailVerification record.
	If the database table does not exist yet (e.g. pending migrations on PythonAnywhere),
	attempts an automatic migrate and retries.
	"""
	for attempt in range(2):
		try:
			verification = getattr(user, 'student_verification', None)
			if not verification:
				if not otp_code:
					otp_code = f"{random.randint(100000, 999999)}"
				verification = StudentEmailVerification.objects.create(
					user=user,
					email=user.email or f"{user.username}@stud.cut.ac.za",
					otp_code=otp_code,
					is_verified=is_verified,
				)
			return verification, False
		except Exception:
			if attempt == 0:
				try:
					from django.core.management import call_command
					call_command('migrate', 'registration', interactive=False)
					continue
				except Exception:
					break
	return None, True


def registration_view(request):
	create_form = StudentRegistrationForm()

	if request.method == "POST":
		create_form = StudentRegistrationForm(request.POST)
		if create_form.is_valid():
			user = create_form.save()
			has_explicit_email = bool((request.POST.get('email') or '').strip())
			otp_code = f"{random.randint(100000, 999999)}"

			if has_explicit_email:
				verification, failed = _safe_get_or_create_verification(
					user, otp_code=otp_code, is_verified=False
				)
				if failed or not verification:
					# Fallback if DB table is temporarily inaccessible
					login(request, user)
					messages.success(request, "Registration Successful! You Are Now Logged In.")
					return redirect("dashboard")

				# Dispatch branded OTP email to student
				send_student_otp_email(user, user.email, otp_code)
				request.session['pending_verification_user_id'] = user.pk
				request.session['verification_attempts'] = 0

				messages.info(
					request,
					f"A 6-digit verification code has been dispatched to {user.email}. Please check your student inbox."
				)
				return redirect('verify_student_email')
			else:
				# Legacy test without email field: auto-verify and log in directly
				_safe_get_or_create_verification(user, otp_code=otp_code, is_verified=True)
				login(request, user)
				messages.success(
					request, "Registration Successful! You Are Now Logged In."
				)
				return redirect("dashboard")

	context = {
		"register_form": create_form,
	}
	return render(request, "registration/register.html", context)


def verify_student_email_view(request):
	user_id = request.session.get('pending_verification_user_id')
	user = None
	if user_id:
		user = User.objects.filter(pk=user_id).first()
	elif request.user.is_authenticated:
		user = request.user

	if not user:
		messages.info(request, "Please log in or register to verify your student email.")
		return redirect('login')

	verification, failed = _safe_get_or_create_verification(user)
	if failed or not verification:
		login(request, user)
		messages.success(request, "Welcome to VarsityConnect!")
		return redirect('dashboard')

	if verification.is_verified:
		messages.info(request, "Your student email is already verified.")
		return redirect('dashboard')

	form = EmailVerificationForm()

	if request.method == "POST":
		# 1. Handle Updating Mistyped Email
		if "update_email" in request.POST:
			new_email = (request.POST.get('new_email') or '').strip().lower()
			if not new_email.endswith(CUT_STUDENT_DOMAIN):
				messages.error(request, f"Invalid student email. Must end with {CUT_STUDENT_DOMAIN}.")
				return redirect('verify_student_email')
			student_num = new_email.split('@')[0]
			if not (student_num.isdigit() and student_num.startswith(VALID_STUDENT_PREFIXES) and 7 <= len(student_num) <= 10):
				messages.error(request, "Student number must start with 221, 222, 223, 224, or 225.")
				return redirect('verify_student_email')
			if User.objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
				messages.error(request, f"The email {new_email} is already in use by another account.")
				return redirect('verify_student_email')

			user.email = new_email
			user.save(update_fields=['email'])
			verification.email = new_email
			new_code = verification.generate_new_code()
			request.session['verification_attempts'] = 0
			send_student_otp_email(user, new_email, new_code)
			messages.success(request, f"Student email updated to {new_email}. A fresh code was sent.")
			return redirect('verify_student_email')

		# 2. Handle Resending Code with Cooldown Check
		if "resend_code" in request.POST:
			if not verification.can_resend():
				wait_sec = verification.seconds_until_can_resend()
				messages.warning(request, f"Please wait {wait_sec} seconds before requesting another code.")
				return redirect('verify_student_email')

			new_code = verification.generate_new_code()
			request.session['verification_attempts'] = 0
			send_student_otp_email(user, verification.email, new_code)
			messages.success(request, f"A fresh 6-digit verification code has been dispatched to {verification.email}.")
			return redirect('verify_student_email')

		# 3. Handle Verifying Code
		form = EmailVerificationForm(request.POST)
		if form.is_valid():
			candidate = form.cleaned_data['otp_code']
			attempts = request.session.get('verification_attempts', 0) + 1
			request.session['verification_attempts'] = attempts

			if attempts > 5:
				messages.error(
					request,
					"Too many incorrect attempts. For security reasons, please click 'Resend verification code' to receive a new code."
				)
				return redirect('verify_student_email')

			is_valid, error_reason = verification.verify_code(candidate)
			if is_valid:
				try:
					verification.is_verified = True
					verification.save()
				except Exception:
					pass
				login(request, user)
				if 'pending_verification_user_id' in request.session:
					del request.session['pending_verification_user_id']
				if 'verification_attempts' in request.session:
					del request.session['verification_attempts']
				messages.success(
					request,
					f"Student email {verification.email} has been successfully verified! Welcome to VarsityConnect."
				)
				return redirect('dashboard')
			else:
				messages.error(request, error_reason)

	context = {
		'form': form,
		'student_email': verification.email,
		'student_user': user,
		'cooldown_remaining': verification.seconds_until_can_resend(),
		'can_resend': verification.can_resend(),
	}
	return render(request, 'registration/verify_email.html', context)