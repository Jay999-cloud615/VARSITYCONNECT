from django.urls import path
from . import views

urlpatterns = [
    path("marketplace/", views.marketplace_home, name="marketplace"),
    path("create/", views.create_listing, name="create_listing"),
    path("listing/<int:pk>/", views.listing_detail, name="listing_detail"),
]