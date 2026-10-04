from django import forms
from .models import Job

class JobForm(forms.ModelForm):
    class Meta:
        model = Job
        fields = ['title', 'organization', 'location', 'pay', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Weekend tutor'}),
            'organization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Company or employer (optional)'}),
            'location': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Braamfontein or Remote'}),
            'pay': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. R80/hour (optional)'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }