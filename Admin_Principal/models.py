from enum import unique

from django.contrib.auth.models import User
from django.db import models

# Create your models here.
class LibraryBook_model(models.Model):
    BookNo = models.CharField(max_length=10,unique=True)
    BookName = models.CharField(max_length=100)
    Language = models.CharField(max_length=25,choices=[('English','English'),('Hindi','Hindi'),('Malayalam','Malayalam'),('Tamil','Tamil'),('Telugu','Telugu'),('Kannada','Kannada'),('Other Indian Language','Other_Indian_Language'),('Foreign_Language','Foreign_Language')],default='English')
    Author= models.CharField(max_length=40)
    Publisher = models.CharField(max_length=40)
    Topic =models.CharField(max_length=30)
    Description = models.TextField(max_length=100)

    class Meta:
        db_table = "LibraryBook"

    def __str__(self):
        return f"({self.BookNo}) {self.BookName}"

class SchoolCalender_model(models.Model):
    CalenderDate = models.DateField()
    Working_day =models.BooleanField(default=True)
    Description = models.TextField(max_length=100,null=True)


    class Meta:
        db_table = "SchoolCalender"


class Role_Model(models.Model):
    user_type=models.CharField(max_length=20)
    Login=models.OneToOneField(User,on_delete=models.CASCADE)

class Teacher_Model(models.Model):
    Code = models.CharField(max_length=10,unique=True,null=False)
    Name = models.CharField(max_length=60,null=True)
    Designation= models.CharField(max_length=80,null=True)
    MobileNumber = models.BigIntegerField(null=True)
    Email = models.EmailField(null=True)
    Login=models.OneToOneField(User,on_delete=models.CASCADE,null=True)

    class Meta:
        db_table = "Teacher"

    def __str__(self):
        return self.Name+self.Designation

class Class_model(models.Model):
    Class_no = models.IntegerField(null=False)
    Section = models.CharField(max_length=50,null=False,choices=[('LKG','LKG'),('UKG','UKG'),('LP','LP'),('UP','UP'),('HS','HS'),('HSS','HSS')])
    Division = models.CharField(max_length=2,choices=[('A','A'),('B','B'),('C','C'),('D','D'),('E','E'),('F','F'),('G','G'),('H','H'),('I','I'),('J','J'),('K','K'),('L','L'),('M','M'),('N','N'),('O','O'),('P','P'),('Q','Q'),('R','R'),('S','S'),('T','T'),('U','U'),('V','V'),('W','W'),('X','X'),('Y','Y'),('Z','Z')],null=True)
    Class_teacher = models.OneToOneField(Teacher_Model,on_delete=models.PROTECT)

    class Meta:
        db_table = "Class"

    def __str__(self):
        return f"{self.Class_no} {self.Section} {self.Class_teacher.Name}"

class Student_Model(models.Model):
    Admission_no =  models.CharField(max_length=10,unique=True,null=False)
    Adm_date = models.DateField()
    Class = models.ForeignKey(Class_model, on_delete=models.CASCADE)
    Roll_no = models.IntegerField()
    Name = models.CharField(max_length=60)
    Gender = models.CharField(max_length=10,choices=[('Male', 'Male'),('Female', 'Female'),('Other', 'Other')])
    DOB = models.DateField()
    Blood_group = models.CharField(max_length=10, choices=[('A+VE', 'A+VE'), ('A-VE', 'A-VE'), ('B+VE', 'B+VE'), ('B-VE', 'B-VE'),('AB+VE', 'AB+VE'), ('AB-VE', 'AB-VE'),('O+VE', 'O+VE'), ('O-VE', 'O-VE')])
    MobileNumber = models.BigIntegerField(null=True)
    Address = models.TextField(max_length=100)
    Category = models.CharField(max_length=30)
    Caste = models.CharField(max_length=30)
    Religion = models.CharField(max_length=30)
    APL_BPL = models.CharField(max_length=3, choices=[('APL', 'APL'), ('BPL', 'BPL')])
    Aadhar = models.CharField(max_length=12)
    Local_body = models.CharField(max_length=30)
    Bank_ac = models.CharField(max_length=30)
    Bank_name = models.CharField(max_length=30)
    IFSC = models.CharField(max_length=30)
    Login=models.OneToOneField(User,on_delete=models.CASCADE,null=True)

    class Meta:
        db_table = "Student"

    def __str__(self):
            return f"{self.Admission_no} {self.Name}"

class Parent_Model(models.Model):
    Student = models.ForeignKey(Student_Model, on_delete=models.CASCADE)
    Father_name = models.CharField(max_length=60,null=False)
    Mother_name = models.CharField(max_length=60,null=False)
    F_occupation = models.CharField(max_length=30,null=True)
    M_occupation = models.CharField(max_length=30,null=True)
    F_phone = models.BigIntegerField(null=False)
    M_phone = models.BigIntegerField(null=False)
    Login = models.OneToOneField(User, on_delete=models.CASCADE, null=True)

    class Meta:
        db_table = "Parent"

class Sibling_model(models.Model):
    Student = models.ForeignKey(Student_Model, on_delete=models.CASCADE,related_name='siblings')
    Sibling_student = models.ForeignKey(Student_Model, on_delete=models.CASCADE,
        related_name='related_to')

    class Meta:
        db_table = "Sibling"

class Subject_model(models.Model):
    Code = models.CharField(max_length=10,null=False,unique=True)
    Name = models.CharField(max_length=60,null=False)
    Class = models.ForeignKey(Class_model, on_delete=models.CASCADE)
    Subject_teacher = models.ForeignKey(Teacher_Model,on_delete=models.SET_NULL,null=True,blank=True)

    class Meta:
        db_table = "Subject"

    def __str__(self):
            return f"{self.Code} {self.Name} {self.Subject_teacher} {self.Subject_teacher.Name} {self.Class} {self.Class.Class_no} {self.Class.Section} "


class TimeTable_model(models.Model):
    Class = models.ForeignKey(Class_model, on_delete=models.CASCADE)
    Day= models.CharField(max_length=10,choices=[('Monday','MON'),('Tuesday','TUE'),('Wednesday','WED'),('Thursday','THUR'),('Friday','FRI'),('Saturday','SAT')])
    Period =models.IntegerField()
    Lab_YN=models.BooleanField(default=False)
    Subject = models.ForeignKey(Subject_model, on_delete=models.PROTECT)

    class Meta:
        db_table = "TimeTable"

class Notice_model(models.Model):
    IssueDate = models.DateField()
    Matter = models.TextField(max_length=200, blank=True, null=True)
    Title = models.CharField(max_length=100, blank=True, null=True)
    Remark = models.CharField(max_length=60, blank=True, null=True)

    class Meta:
        db_table = "Notice"

class Exam_model(models.Model):
    Name = models.CharField(max_length=60, null=False)
    Subject = models.ForeignKey(Subject_model, on_delete=models.CASCADE)
    Date = models.DateField()
    TimeFrom = models.TimeField()
    TimeTo = models.TimeField()
    Max_mark = models.IntegerField()

    class Meta:
        db_table = "Exam"


