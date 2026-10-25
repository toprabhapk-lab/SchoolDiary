from  .import views
from django.urls import path

urlpatterns = [
       path('',views.SchoolDiaryHeaderView,name='SchoolDiaryHeaderView'),
       path('SchoolDiaryReadmoreView', views.SchoolDiaryReadmoreView, name='SchoolDiaryReadmoreView'),
       path('login',views.login,name='login'),
]