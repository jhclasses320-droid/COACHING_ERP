
from django.urls import path, include
from django.shortcuts import redirect
from students.admin import admin_site


# Redirect homepage to student login
def home_redirect(request):
    return redirect('student_login')


urlpatterns = [
    path('', home_redirect, name='home'),

    # custom admin
    path('admin/', admin_site.urls),

    # include app urls
    path('', include('students.urls')),
]

