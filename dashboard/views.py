from django.contrib.auth.decorators import login_required
from django.shortcuts import render
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