from django import forms
from .models import Resource

class ResourceUploadForm(forms.ModelForm):
    class Meta:
        model = Resource
        fields = ['title', 'category', 'pdf_file', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'pdf_file': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }