from django.contrib import messages
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from .forms import StudentAuthenticationForm, StudentRegistrationForm


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
				# Check if the rejection was specifically due to non-student domain
				domain_error = False
				for error_list in login_form.errors.as_data().values():
					for err in error_list:
						if getattr(err, 'code', None) == 'invalid_student_domain':
							domain_error = True
							break
				if domain_error:
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
			login(request, user)
			messages.success(
				request, "Registration Successful! You Are Now Logged In."
			)
			return redirect("dashboard")

	context = {
		"register_form": create_form,
	}
	return render(request, "registration/register.html", context)