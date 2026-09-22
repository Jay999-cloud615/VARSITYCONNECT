from django import forms
from .models import MarketplaceListing

class MarketplaceListingForm(forms.ModelForm):
    class Meta:
        model = MarketplaceListing
        fields = ['title', 'price', 'price_suffix', 'category', 'condition', 'description', 'location']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Casio fx-991 Calculator'}),
            'price': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '280'}),
            'price_suffix': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. /hr (optional)'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'condition': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Like new'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Describe your item...'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Wits campus / 0.4 km'}),
        }

