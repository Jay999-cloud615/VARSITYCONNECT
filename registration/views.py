from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User
from django.shortcuts import redirect, render
from django.contrib.auth import login


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
				identifier = getattr(user, "username", getattr(user, "email", "User"))
				messages.success(request, f"Welcome back, {identifier}!")
				return redirect("dashboard")
			else:
				messages.error(request, "Invalid username or password.")

	context = {
		"register_form": create_form,
		"login_form": login_form,
	}
	return render(request, "registration/login.html", context)