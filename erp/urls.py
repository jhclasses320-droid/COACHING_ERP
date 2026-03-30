
from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect


# Redirect homepage to student login
def home_redirect(request):
    return redirect('student_login')


urlpatterns = [
    path('', home_redirect, name='home'),

    path('admin/', admin.site.urls),

    # Students app URLs
    path('student/', include('students.urls')),
]

