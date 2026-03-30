
from django.urls import path, include
from django.shortcuts import redirect
from students.admin import admin_site   # ⭐ IMPORTANT


# Redirect homepage to student login
def home_redirect(request):
    return redirect('student_login')


urlpatterns = [
    path('', home_redirect, name='home'),

    # ⭐ USE CUSTOM ADMIN
    path('admin/', admin_site.urls),

    # Students app URLs
    path('student/', include('students.urls')),
]

