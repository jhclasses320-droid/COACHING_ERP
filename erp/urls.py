from django.urls import path, include
from django.shortcuts import redirect
from students.admin import admin_site

from django.conf import settings
from django.conf.urls.static import static


# Redirect homepage to student login
def home_redirect(request):
    return redirect("student_login")


urlpatterns = [

    path("", home_redirect, name="home"),

    # Custom Admin
    path("admin/", admin_site.urls),

    # Performance Module
    path("performance/", include("performance.urls")),

    # API
    path("api/", include("api.urls")),

    # Question Bank
    path("questionbank/", include("questionbank.urls")),

    # Students
    path("", include("students.urls")),

]




# ==========================================================
# DEVELOPMENT ONLY
# ==========================================================

if settings.DEBUG:

    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT,
    )

    urlpatterns += static(
        settings.STATIC_URL,
        document_root=settings.STATIC_ROOT,
    )

