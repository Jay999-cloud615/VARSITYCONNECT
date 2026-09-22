from django.urls import path
from . import views

urlpatterns = [
    path('', views.course_material_view, name='course_material'),
    path('download/<int:pk>/', views.download_resource_view, name='resource-download'),
]