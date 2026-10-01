"""
URL configuration for SSE_PROJECt project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.contrib.auth.decorators import user_passes_test
from django.urls import path, include


def superuser_required(view_func):
    return user_passes_test(lambda user: user.is_active and user.is_superuser)(view_func)


admin.site.login = superuser_required(admin.site.login)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('registration.urls')),
    path("dashboard/", include("dashboard.urls")),
    path('course_material/', include("course_material.urls")),
    path('housing/', include("housing.urls")),
    path('marketplace/', include("marketplace.urls")),
    path('messaging/', include("messaging.urls")),
]
