import re
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from course_material.models import Resource
from marketplace.models import MarketplaceListing
from housing.models import Job


@login_required
def home_dashboard_view(request):
    context = {
        'marketplace_count': MarketplaceListing.objects.count(),
        'resource_count': Resource.objects.count(),
        'job_count': Job.objects.count(),
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def profile_view(request):
    if request.method == 'POST' and 'change_username' in request.POST:
        new_username = request.POST.get('new_username', '').strip()
        if not new_username:
            messages.error(request, "Username cannot be empty.")
        elif new_username == request.user.username:
            messages.info(request, "New username is identical to your current username.")
        elif len(new_username) < 3 or len(new_username) > 30:
            messages.error(request, "Username must be between 3 and 30 characters.")
        elif not re.match(r'^[a-zA-Z0-9_.-]+$', new_username):
            messages.error(request, "Username can only contain letters, numbers, underscores, dashes, and periods.")
        elif User.objects.filter(username__iexact=new_username).exclude(pk=request.user.pk).exists():
            messages.error(request, f"The username '{new_username}' is already taken. Please choose another.")
        else:
            old_username = request.user.username
            request.user.username = new_username
            request.user.save()
            messages.success(request, f"Your username has been successfully updated from @{old_username} to @{new_username}!")
            return redirect('profile')

    context = {
        'marketplace_count': MarketplaceListing.objects.filter(
            seller=request.user,
        ).count(),
        'job_count': Job.objects.filter(posted_by=request.user).count(),
        'resource_count': Resource.objects.filter(
            uploaded_by=request.user,
        ).count(),
    }
    return render(request, 'dashboard/profile.html', context)