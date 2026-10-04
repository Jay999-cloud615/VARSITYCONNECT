from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_dashboard_view, name='dashboard'),
    path('profile/', views.profile_view, name='profile'),
]