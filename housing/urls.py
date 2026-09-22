from django.urls import path
from . import views

urlpatterns = [
    path('', views.accommodation_list_view, name='housing'),
    path('<int:pk>/', views.accommodation_detail_view, name='housing-detail'),
]