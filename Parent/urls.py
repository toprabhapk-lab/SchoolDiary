from . import views
from django.urls import path

urlpatterns = [
    path('',views.ParentHome,name='ParentHome'),
	path('Parent_TimeTable/',views.Parent_TimeTable,name='Parent_TimeTable'),
	path('Parent_Notice/',views.Parent_Notice,name='Parent_Notice'),
	path('Parent_TimeTable/', views.Parent_TimeTable, name='Parent_TimeTable'),
	path('Parent_PersonalData/', views.Parent_PersonalData, name='Parent_PersonalData'),
	path('Parent_Progress/', views.Parent_Progress, name='Parent_Progress'),
	path('verify_mark/', views.verify_mark, name='verify_mark'),
	path('Parent_AcademicCalendar/', views.Parent_AcademicCalendar, name='Parent_AcademicCalendar'),
	path('Parent_Homework/', views.Parent_Homework, name='Parent_Homework'),
	path('parent_attendance/', views.parent_attendance, name='Parent_Attendance'),
	path('verify_attendance/<str:record_type>/<int:record_id>/', views.verify_attendance, name='verify_attendance'),
	path('parent_acknowledgement/', views.parent_acknowledgement, name='parent_acknowledgement'),
	path('verify_acknowledgement/<int:ack_id>/', views.verify_acknowledgement, name='verify_acknowledgement'),
	path('Parent_LeaveApplication/', views.Parent_LeaveApplication, name='Parent_LeaveApplication'),
	path('Parent_Communication/', views.Parent_Communication, name='Parent_Communication'),
	path('change_password/', views.change_password, name='change_password'),
]
