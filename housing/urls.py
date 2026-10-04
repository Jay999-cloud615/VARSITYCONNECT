from django.urls import path
from . import views

urlpatterns = [
    path('', views.job_list_view, name='jobs'),
    path('<int:pk>/', views.job_detail_view, name='job-detail'),
    path('<int:pk>/delete/', views.delete_job_view, name='job-delete'),
]