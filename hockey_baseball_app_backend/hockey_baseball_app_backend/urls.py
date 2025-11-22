"""
URL configuration for hockey_baseball_app_backend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.middleware.csrf import get_token
from .api import api

def health_check(request):
    """Health check endpoint for AWS App Runner"""
    return JsonResponse({"status": "healthy", "service": "hockey-app-backend"})

@csrf_exempt
@ensure_csrf_cookie
def get_csrf_token(request):
    """CSRF token endpoint - returns token in JSON and sets cookie"""
    csrf_token = get_token(request)
    response = JsonResponse({"csrf_token": csrf_token})
    return response

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/users/csrf", get_csrf_token, name="csrf_token"),  # CSRF endpoint before API router
    path("api/", api.urls),
    path("health/", health_check, name="health_check"),
]

if settings.USE_LOCAL_STORAGE:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
