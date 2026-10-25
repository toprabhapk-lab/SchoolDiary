from . import views
from django.urls import path

urlpatterns = [

    	path('',views.StudentHome,name='StudentHome'),
		path('Student_Notice/', views.Student_Notice, name='Student_Notice'),
		path('Student_TimeTable/', views.Student_TimeTable, name='Student_TimeTable'),
		path('Student_PersonalData/', views.Student_PersonalData, name='Student_PersonalData'),
		path('Student_Progress/', views.Student_Progress, name='Student_Progress'),
		path('student_academic_calendar/', views.student_academic_calendar, name='student_academic_calendar'),
		path('student_homework/', views.student_homework, name='student_homework'),
		path('student_attendance/', views.student_attendance, name='student_attendance'),
		path('student_acknowledgement/', views.student_acknowledgement, name='student_acknowledgement'),
		path('change-password/', views.change_password, name='change_password'),
]
