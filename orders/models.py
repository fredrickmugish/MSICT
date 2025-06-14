# Create your models here.
# models.py (in your Django app)
from django.db import models
from django.contrib.auth.models import User

class DepartmentRequest(models.Model):
    department = models.CharField(max_length=100)
    equipment = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    purpose = models.TextField()
    date_submitted = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('forwarded', 'Forwarded'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], default='pending')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')

class QMNote(models.Model):
    request = models.OneToOneField(DepartmentRequest, on_delete=models.CASCADE)
    note = models.TextField()
    forwarded_date = models.DateTimeField(auto_now_add=True)

class COFeedback(models.Model):
    message = models.TextField()
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_sent = models.DateTimeField(auto_now_add=True)





