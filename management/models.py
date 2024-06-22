from datetime import datetime

from django.db import models


# Create your models here.
class DormBuilding(models.Model):
    name = models.CharField(max_length=100)

class DormManager(models.Model):
    dormmanager_id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    building = models.ForeignKey(DormBuilding, on_delete=models.SET_NULL, null=True)


class Student(models.Model):
    student_id = models.CharField(max_length=100, primary_key=True)
    name = models.CharField(max_length=100)
    age = models.IntegerField()
    gender = models.CharField(max_length=10)
    phone = models.CharField(max_length=15)
    dorm = models.ForeignKey('Dorm', on_delete=models.SET_NULL, null=True)
    status = models.IntegerField(default=0)  # 0表示未入住，1表示申请入宿，2表示已入住，3表示申请退宿
    icon = models.ForeignKey('ImgUpload', on_delete=models.SET_NULL, null=True)

class ImgUpload(models.Model):
    image = models.ImageField(upload_to='img/')
    title = models.CharField(max_length=100,default=str(datetime.now))
    uploader = models.ForeignKey(Student, on_delete=models.CASCADE,null=True)

class Dorm(models.Model):
    Dorm_id = models.IntegerField(max_length=100, primary_key=True)
    building = models.ForeignKey(DormBuilding, on_delete=models.CASCADE)


class Visitor(models.Model):
    applicant = models.ForeignKey(Student, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15)
    visit_date = models.DateField()
    applicant_date = models.DateField(null=True)
    reason = models.CharField(max_length=200, null=True)
    state = models.IntegerField(default=0)


class Repair(models.Model):
    repair_date = models.DateField()
    building = models.ForeignKey(DormBuilding, on_delete=models.SET_NULL, null=True)
    description = models.TextField()
    reporter = models.ForeignKey(Student, on_delete=models.CASCADE)
    completed = models.BooleanField(default=False)


class DormApply(models.Model):
    applicant = models.ForeignKey(Student, on_delete=models.CASCADE)
    applicant_date = models.DateField(default=datetime.today().date())
    apply_type = models.IntegerField(default=0)  # 0为申请入住，1为申请退宿
    status = models.IntegerField(default=0)  # 0为未处理，1为允许，2为拒绝
