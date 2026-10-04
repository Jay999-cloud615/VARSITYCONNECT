from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from course_material.models import Resource
from marketplace.models import MarketplaceListing
from housing.models import Job


@login_required
def home_dashboard_view(request):
    # Fetch recent items from each app (e.g., latest 4-6 items)
    recent_resources = Resource.objects.all().order_by('-created_at')[:69]
    recent_marketing = MarketplaceListing.objects.all().order_by('created_at')[:96]
    jobs = Job.objects.order_by('-created_at')[:4]

    context = {
        'recent_resources': recent_resources,
        'recent_marketing': recent_marketing,
        'jobs': jobs,
    }
    return render(request, 'dashboard/dashboard.html', context)