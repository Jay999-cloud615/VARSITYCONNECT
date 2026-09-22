from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import MarketplaceListing
from .forms import MarketplaceListingForm
from django.shortcuts import get_object_or_404
# Create your views here.

@login_required
def marketplace_home(request):
	# Fetch all listings from the database, newest first
	listings = MarketplaceListing.objects.all().order_by('-created_at')

	context = {
		'listings': listings,
	}
	return render(request, 'marketplace/market_place_home.html', context)


@login_required
def create_listing(request):
	if request.method == 'POST':
		form = MarketplaceListingForm(request.POST)
		if form.is_valid():
			listing = form.save(commit=False)
			listing.seller = request.user  # Assign the currently logged-in user as the seller
			listing.save()
			return redirect('marketplace')
	else:
		form = MarketplaceListingForm()

	context = {
		'form': form,
	}
	return render(request, 'marketplace/create_listing.html', context)

@login_required
def listing_detail(request, pk):
	listing = get_object_or_404(MarketplaceListing, pk=pk)
	context = {
	    'listing': listing,
	}
	return render(request, 'marketplace/listing_detail.html', context)