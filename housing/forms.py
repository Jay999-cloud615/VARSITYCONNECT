from django import forms
from .models import Accommodation

class AccommodationForm(forms.ModelForm):
    class Meta:
        model = Accommodation
        fields = ['title', 'location', 'price_per_month', 'amenities', 'description', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'price_per_month': forms.NumberInput(attrs={'class': 'form-control'}),
            'amenities': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }