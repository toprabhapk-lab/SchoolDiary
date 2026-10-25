from email.policy import default

from django import forms
from django.forms import TimeInput

from .models import LibraryBook_model, SchoolCalender_model, Teacher_Model, Class_model, Student_Model, Parent_Model, \
    Subject_model, TimeTable_model, Notice_model, Exam_model


class LibraryBook_Form(forms.ModelForm):

    class Meta:
        model=LibraryBook_model
        fields=('BookName','Author','Publisher','Topic','Description',)


class DateInput(forms.DateInput):
    input_type='date'

class SchoolCalender_Form(forms.ModelForm):

    CalenderDate = forms.DateField(widget=DateInput)

    class Meta:
        model=SchoolCalender_model
        fields=('CalenderDate','Working_day','Description',)

class Teacher_Form(forms.ModelForm):

    class Meta:
        model = Teacher_Model
        fields = ('Code','Name', 'Designation', 'MobileNumber', 'Email',)


class Class_Form(forms.ModelForm):

    class Meta:
        model=Class_model
        fields=('Class_no','Section','Class_teacher',)



class Student_Form(forms.ModelForm):
    Adm_date = forms.DateField(widget=DateInput)
    DOB = forms.DateField(widget=DateInput)

    class Meta:
        model = Student_Model
        fields = ('Admission_no', 'Adm_date', 'Class', 'Roll_no', 'Name', 'Gender', 'DOB', 'Blood_group',
                  'MobileNumber', 'Address', 'Category', 'Caste', 'Religion', 'APL_BPL', 'Aadhar', 'Local_body',
                  'Bank_ac', 'Bank_name', 'IFSC',)



class Parent__Form(forms.ModelForm):

    class Meta:
        model=Parent_Model
        fields=('Student','Father_name','Mother_name','F_occupation','M_occupation','F_phone','M_phone',)

class Subject_Form(forms.ModelForm):

    class Meta:
        model=Subject_model
        fields=('Code','Name','Class','Subject_teacher',)

class TimeTable_Form(forms.ModelForm):

    class Meta:
        model=TimeTable_model
        fields=('Class','Day','Period','Lab_YN','Subject',)

class Notice_Form(forms.ModelForm):
    IssueDate = forms.DateField(widget=DateInput)

    class Meta:
        model=Notice_model
        fields=('IssueDate','Matter','Remark',)


class Exam_Form(forms.ModelForm):
    Date = forms.DateField(widget=DateInput)
    TimeFrom= forms.TimeField(widget=TimeInput)
    TimeTo= forms.TimeField(widget=TimeInput)

    class Meta:
        model=Exam_model
        fields=('Name','Subject','Date','TimeFrom','TimeTo','Max_mark',)