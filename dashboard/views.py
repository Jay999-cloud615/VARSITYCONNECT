from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from course_material.models import Resource
from marketplace.models import MarketplaceListing
from housing.models import Accommodation


def home_dashboard_view(request):
    # Fetch recent items from each app (e.g., latest 4-6 items)
    recent_resources = Resource.objects.all().order_by('-created_at')[:69]
    recent_marketing = MarketplaceListing.objects.all().order_by('created_at')[:96]
    accommodations = Accommodation.objects.order_by('-id')[:4]

    context = {
        'recent_resources': recent_resources,
        'recent_marketing': recent_marketing,
        'accommodations': accommodations,
    }
    return render(request, 'dashboard/dashboard.html', context)