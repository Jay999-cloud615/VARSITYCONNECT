from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import MarketplaceListing
from .forms import ListingStockForm, MarketplaceListingForm
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
		form = MarketplaceListingForm(request.POST, request.FILES)
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
@require_POST
def delete_listing(request, pk):
	listing = get_object_or_404(MarketplaceListing, pk=pk, seller=request.user)
	image = listing.image
	listing.delete()
	if image:
		image.delete(save=False)
	return redirect('marketplace')


@login_required
@require_POST
def update_listing_stock(request, pk):
	listing = get_object_or_404(MarketplaceListing, pk=pk, seller=request.user)
	form = ListingStockForm(request.POST, instance=listing)
	if form.is_valid():
		form.save()
		return redirect('listing_detail', pk=listing.pk)
	return render(request, 'marketplace/listing_detail.html', {
		'listing': listing,
		'stock_form': form,
	})


@login_required
def listing_detail(request, pk):
	listing = get_object_or_404(MarketplaceListing, pk=pk)
	context = {
	    'listing': listing,
	    'stock_form': ListingStockForm(instance=listing),
	}
	return render(request, 'marketplace/listing_detail.html', context)