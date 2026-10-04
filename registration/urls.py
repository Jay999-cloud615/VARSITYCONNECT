from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_auth_view, name='login'),
    path('register/', views.registration_view, name='register'),
    path('logout/', views.logout_thank_you_view, name='logout'),
]
