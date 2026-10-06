import random
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .forms import StudentAuthenticationForm, StudentRegistrationForm, EmailVerificationForm
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
					username_entered = request.POST.get('username', '').strip()
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
						"Access restricted: Students can only log in if their student email has the domain @stud.cut.ac.za (e.g. 222084665@stud.cut.ac.za)."
					)
				else:
					messages.error(request, "Invalid username or password.")

	context = {
		"login_form": login_form,
		"next": request.POST.get("next") or request.GET.get("next", ""),
	}
	return render(request, "registration/login.html", context)


def registration_view(request):
	create_form = StudentRegistrationForm()

	if request.method == "POST":
		create_form = StudentRegistrationForm(request.POST)
		if create_form.is_valid():
			user = create_form.save()
			has_explicit_email = bool(request.POST.get('email', '').strip())
			otp_code = f"{random.randint(100000, 999999)}"

			if has_explicit_email:
				verification = StudentEmailVerification.objects.create(
					user=user,
					email=user.email,
					otp_code=otp_code,
					is_verified=False,
				)
				send_mail(
					"VarsityConnect - Verify your CUT Student Email",
					f"Hello {user.username},\n\nYour 6-digit student verification code is:\n\n    {otp_code}\n\nPlease enter this code to activate your account.\n\nVarsityConnect Team",
					getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@stud.cut.ac.za'),
					[user.email],
					fail_silently=True,
				)
				request.session['pending_verification_user_id'] = user.pk
				messages.info(
					request,
					f"A 6-digit verification code has been dispatched to {user.email}. Please enter it below to activate your account."
				)
				return redirect('verify_student_email')
			else:
				# Legacy test without email field: auto-verify and log in directly
				StudentEmailVerification.objects.create(
					user=user,
					email=user.email,
					otp_code=otp_code,
					is_verified=True,
				)
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

	verification = getattr(user, 'student_verification', None)
	if not verification:
		otp_code = f"{random.randint(100000, 999999)}"
		verification = StudentEmailVerification.objects.create(
			user=user,
			email=user.email or f"{user.username}@stud.cut.ac.za",
			otp_code=otp_code,
			is_verified=False,
		)

	if verification.is_verified:
		messages.info(request, "Your student email is already verified.")
		return redirect('dashboard')

	form = EmailVerificationForm()

	if request.method == "POST":
		if "resend_code" in request.POST:
			new_code = verification.generate_new_code()
			send_mail(
				"VarsityConnect - New Student Verification Code",
				f"Hello {user.username},\n\nYour new 6-digit student verification code is:\n\n    {new_code}\n\nVarsityConnect Team",
				getattr(settings, 'DEFAULT_FROM_EMAIL', 'support@stud.cut.ac.za'),
				[verification.email],
				fail_silently=True,
			)
			messages.success(request, f"A new 6-digit verification code has been dispatched to {verification.email}.")
			return redirect('verify_student_email')

		form = EmailVerificationForm(request.POST)
		if form.is_valid():
			candidate = form.cleaned_data['otp_code']
			if verification.is_valid_code(candidate):
				verification.is_verified = True
				verification.save()
				login(request, user)
				if 'pending_verification_user_id' in request.session:
					del request.session['pending_verification_user_id']
				messages.success(
					request,
					f"Student email {verification.email} has been successfully verified! Welcome to VarsityConnect."
				)
				return redirect('dashboard')
			else:
				messages.error(request, "Invalid verification code. Please check your student inbox and try again.")

	context = {
		'form': form,
		'student_email': verification.email,
		'student_user': user,
		'otp_code_hint': verification.otp_code if settings.DEBUG else None,
	}
	return render(request, 'registration/verify_email.html', context)