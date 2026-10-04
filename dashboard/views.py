from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from course_material.models import Resource
from marketplace.models import MarketplaceListing
from housing.models import Job


@login_required
def home_dashboard_view(request):
    recent_resources = Resource.objects.select_related('uploaded_by').order_by('-created_at')[:4]
    recent_marketing = MarketplaceListing.objects.select_related('seller').order_by('-created_at')[:4]
    jobs = Job.objects.order_by('-created_at')[:4]

    context = {
        'recent_resources': recent_resources,
        'recent_marketing': recent_marketing,
        'jobs': jobs,
        'marketplace_count': MarketplaceListing.objects.count(),
        'resource_count': Resource.objects.count(),
        'job_count': Job.objects.count(),
    }
    return render(request, 'dashboard/dashboard.html', context)


@login_required
def profile_view(request):
    marketplace_listings = MarketplaceListing.objects.filter(
        seller=request.user,
    ).order_by('-created_at')
    jobs = Job.objects.filter(posted_by=request.user).order_by('-created_at')
    resources = Resource.objects.filter(
        uploaded_by=request.user,
    ).order_by('-created_at')

    context = {
        'marketplace_listings': marketplace_listings,
        'jobs': jobs,
        'resources': resources,
        'marketplace_count': marketplace_listings.count(),
        'job_count': jobs.count(),
        'resource_count': resources.count(),
    }
    return render(request, 'dashboard/profile.html', context)