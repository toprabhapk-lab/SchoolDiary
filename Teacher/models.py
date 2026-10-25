from django.db import models

from Admin_Principal.models import Student_Model, Teacher_Model, Exam_model, LibraryBook_model, Class_model, \
    Subject_model


class Attendance_model(models.Model):
    Student = models.ForeignKey(Student_Model, on_delete=models.CASCADE)
    AbsentDate = models.DateField()
    Parent_verification=models.BooleanField(default=False)

    class Meta:
        db_table = "Attendance"



class LateComing_model(models.Model):
    Student = models.ForeignKey(Student_Model, on_delete=models.CASCADE)
    Date = models.DateField()
    Time = models.TimeField()
    Parent_verification=models.BooleanField(default=False)
    class Meta:
        db_table = "LateComing"


class ParentTeacherCommunication_model(models.Model):
    Date = models.DateField()
    Student = models.ForeignKey(Student_Model, on_delete=models.CASCADE)
    Matter = models.TextField(max_length=100, null=True)
    ResponseTo = models.ForeignKey(

        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replies'
    )
    Communicator=models.TextField(max_length=100,null=True,choices=[('Teacher','Teacher'), ('Parent','Parent')])
    Remark = models.TextField(max_length=100, null=True)

    class Meta:
        db_table = "ParentTeacherCommunication"

class Marks_model(models.Model):
    Student = models.ForeignKey(Student_Model, on_delete=models.CASCADE)
    Exam= models.ForeignKey(Exam_model, on_delete=models.CASCADE)
    Score = models.IntegerField()
    Parent_verification_date = models.DateField(null=True)
    Principal_verification = models.BooleanField(default=False)

    class Meta:
        db_table = "Marks"


class Acknowledgement_model(models.Model):
    Date= models.DateField()
    Student = models.ForeignKey(Student_Model, on_delete=models.CASCADE)
    Mode = models.CharField(max_length=10, choices=[('Gain', 'Gain'), ('Lesson', 'Lesson')], default='Gain')
    Description = models.CharField(max_length=100, null=False)
    Parent_verification=models.BooleanField(default=False)
    Credit = models.IntegerField(null=True)
    Principal_verification = models.BooleanField(default=False)

    class Meta:
        db_table = "Acknowledgement"

class Library_issue_model(models.Model):
    Book= models.ForeignKey(LibraryBook_model, on_delete=models.CASCADE)
    Student = models.ForeignKey(Student_Model, on_delete=models.CASCADE)
    DateOfIssue = models.DateField()
    DateOfReturn = models.DateField(null=True)
    Teacher = models.ForeignKey(Teacher_Model, on_delete=models.SET_NULL, null=True)

    class Meta:
        db_table = "Library_issue"

class Homework_model(models.Model):
    Subject = models.ForeignKey(Subject_model, on_delete=models.CASCADE)
    DateOfIssue = models.DateField()
    Submission_date = models.DateField()
    Description = models.CharField(max_length=100, null=False)
 #   Attachment = models.CharField(max_length=100, null=True)


    class Meta:
        db_table = "Homework"

class HomeworkDone_model(models.Model):
    Student = models.ForeignKey(Student_Model, on_delete=models.CASCADE)
    Homework = models.ForeignKey(Homework_model, on_delete=models.CASCADE)
    Submitted_date = models.DateField()

    class Meta:
        db_table = "HomeworkDone"