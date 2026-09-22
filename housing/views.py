from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import Accommodation
from .forms import AccommodationForm

@login_required
def accommodation_list_view(request):
    if request.method == 'POST':
        form = AccommodationForm(request.POST, request.FILES)
        if form.is_valid():
            property_item = form.save(commit=False)
            property_item.landlord = request.user
            property_item.save()
            return redirect('housing')
    else:
        form = AccommodationForm()

    accommodations = Accommodation.objects.all().order_by('-created_at')

    context = {
        'form': form,
        'accommodations': accommodations,
    }
    return render(request, 'housing/accommodation_list.html', context)

@login_required
def accommodation_detail_view(request, pk):
    accommodation = get_object_or_404(Accommodation, pk=pk)
    context = {
        'accommodation': accommodation,
    }
    return render(request, 'housing/accommodation_detail.html', context)