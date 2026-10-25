"""
URL configuration for SchoolDiary project.


"""
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('Admin_Principal/',include('Admin_Principal.urls')),
    path('',include('Login.urls')),
    path('Teacher/', include('Teacher.urls')),
    path('Student/', include('Student.urls')),
    path('Parent/', include('Parent.urls')),
]
