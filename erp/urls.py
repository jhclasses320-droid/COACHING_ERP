
from django.urls import path, include
from students.admin import admin_site

urlpatterns = [
    # ✅ ALL APP URLS
    path('', include('students.urls')),

    # ✅ CUSTOM ADMIN PANEL
    path('admin/', admin_site.urls),
]





