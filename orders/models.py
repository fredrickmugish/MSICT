# models.py (in your Django app)
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)  # Use default instead of auto_now_add

    def __str__(self):
        return self.name

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
        ('rejected', 'Rejected'),
        ('completed', 'Completed')
    ], default='pending')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')

    def __str__(self):
        return f"{self.equipment} - {self.department}"

class QMNote(models.Model):
    request = models.OneToOneField(DepartmentRequest, on_delete=models.CASCADE)
    note = models.TextField()
    forwarded_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Note for {self.request.equipment}"

class CODecision(models.Model):
    request = models.OneToOneField(DepartmentRequest, on_delete=models.CASCADE)
    decision = models.CharField(max_length=20, choices=[
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ])
    reason = models.TextField(blank=True)
    decided_by = models.ForeignKey(User, on_delete=models.CASCADE)
    decision_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.decision} - {self.request.equipment}"

class QMResponse(models.Model):
    request = models.OneToOneField(DepartmentRequest, on_delete=models.CASCADE)
    response_message = models.TextField()
    responded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    response_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Response to {self.request.equipment}"

class COFeedback(models.Model):
    message = models.TextField()
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_sent = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback from {self.sent_by.username}"
