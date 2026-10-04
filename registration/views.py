from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.contrib.auth import login, logout
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST


@require_POST
def logout_thank_you_view(request):
	logout(request)
	return render(request, "registration/logout_thanks.html")


def landing_auth_view(request):
	create_form = UserCreationForm()
	login_form = AuthenticationForm()

	if request.method == "POST":
		if "save" in request.POST:
			create_form = UserCreationForm(request.POST)
			if create_form.is_valid():
				user = create_form.save()
				login(request, user)
				messages.success(
					request, "Registration Successful! You Are Now Logged In."
				)
				return redirect("dashboard")
			else:
				messages.error(request, "Registration Failed. Check errors below.")

		elif "login_submit" in request.POST:
			login_form = AuthenticationForm(request, data=request.POST)
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
				messages.error(request, "Invalid username or password.")

	context = {
		"register_form": create_form,
		"login_form": login_form,
		"next": request.POST.get("next") or request.GET.get("next", ""),
	}
	return render(request, "registration/login.html", context)