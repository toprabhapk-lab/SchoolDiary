from . import views
from django.urls import path

urlpatterns = [
    path('', views.TeacherHome, name='TeacherHome'),
    path('students/', views.students_by_class, name='students_by_class'),
    path('attendance/', views.teacher_attendance, name='teacher_attendance'),
    path('Teacher_Communication/', views.Teacher_Communication, name='Teacher_Communication'),
    path('teacher_late_arrival/', views.teacher_late_arrival, name='teacher_late_arrival'),
    path('Teacher_Acknowledgement/', views.Teacher_Acknowledgement, name='Teacher_Acknowledgement'),
    path('Teacher_Homeworks/', views.Teacher_Homeworks, name='Teacher_Homeworks'),
    path('Teacher_Exam_Mark/', views.Teacher_Exam_Mark, name='Teacher_Exam_Mark'),
    path('Teacher_Library_Books/', views.Teacher_Library_Books, name='Teacher_Library_Books'),
    path('teacher_student_info/', views.teacher_student_info, name='teacher_student_info'),
    path('Teacher_TimeTables/', views.Teacher_TimeTables, name='Teacher_TimeTables'),
    path('teacher_academic_calendar/', views.teacher_academic_calendar, name='teacher_academic_calendar'),
    path('Teacher_Notice/', views.Teacher_Notice, name='Teacher_Notice'),
    path('Teacher_AttendanceReport/', views.Teacher_AttendanceReport, name='Teacher_AttendanceReport'),
    path('Teacher_MarkSheet/', views.Teacher_MarkSheet, name='Teacher_MarkSheet'),
    path('Teacher_ExamScheduleReport/', views.Teacher_ExamScheduleReport, name='Teacher_ExamScheduleReport'),
    path('Teacher_LeaveApplication/', views.Teacher_LeaveApplication, name='Teacher_LeaveApplication'),
    path('change_password/', views.change_password, name='T_change_password'),

]

