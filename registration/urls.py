from django.urls import path
from django.contrib.auth.views import LogoutView
from . import views

urlpatterns = [
    path('', views.landing_auth_view, name='login'),
path(
    'logout/',
    LogoutView.as_view(next_page='logout'),
    name='logout',
    )
]
