from django.db import models

from Admin_Principal.models import Student_Model


class LeaveApplication_model(models.Model):
    Student = models.ForeignKey(Student_Model, on_delete=models.CASCADE)
    AbsentDate = models.DateField()
    ApplicationDate = models.DateField()
    Reason = models.TextField(max_length=100,null=False)
    Status = models.CharField(max_length=10, choices=[('Approved', 'Approved'), ('Pending', 'Pending'), ('Rejected', 'Rejected')])
    Remark = models.TextField(max_length=100, null=True)

    class Meta:
        db_table = "LeaveApplication"
