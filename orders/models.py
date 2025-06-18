from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import uuid
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    head_of_department = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ['name']


class DepartmentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('forwarded', 'Forwarded to CO'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    request_number = models.CharField(max_length=20, unique=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    equipment = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    purpose = models.TextField()
    specifications = models.TextField(blank=True)
    required_date = models.DateField(null=True, blank=True)
    additional_notes = models.TextField(blank=True)
    
    date_submitted = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='requests')
    
    def save(self, *args, **kwargs):
        if not self.request_number:
            # Generate unique request number
            today = timezone.now().date()
            date_str = today.strftime('%Y%m%d')
            
            # Get the count of requests created today
            daily_count = DepartmentRequest.objects.filter(
                date_submitted__date=today
            ).count() + 1
            
            # Generate request number with fallback to UUID if collision
            base_number = f"REQ-{date_str}-{daily_count:03d}"
            request_number = base_number
            
            # Ensure uniqueness
            counter = 1
            while DepartmentRequest.objects.filter(request_number=request_number).exists():
                request_number = f"{base_number}-{counter}"
                counter += 1
            
            self.request_number = request_number
            
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.request_number} - {self.equipment}"
    
    @property
    def days_pending(self):
        return (timezone.now().date() - self.date_submitted.date()).days
    
    class Meta:
        ordering = ['-date_submitted']

class QMNote(models.Model):
    RECOMMENDATION_CHOICES = [
        ('review', 'Needs Review'),
        ('approve', 'Recommend Approval'),
        ('reject', 'Recommend Rejection'),
    ]
    
    request = models.OneToOneField(DepartmentRequest, on_delete=models.CASCADE)
    note = models.TextField()
    recommendation = models.CharField(max_length=10, choices=RECOMMENDATION_CHOICES, default='review')
    forwarded_date = models.DateTimeField(auto_now_add=True)
    forwarded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"QM Note for {self.request.request_number}"

class CODecision(models.Model):
    DECISION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    request = models.OneToOneField(DepartmentRequest, on_delete=models.CASCADE)
    decision = models.CharField(max_length=10, choices=DECISION_CHOICES)
    reason = models.TextField()
    additional_notes = models.TextField(blank=True)
    budget_allocation = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    expected_procurement_date = models.DateField(null=True, blank=True)
    decision_date = models.DateTimeField(auto_now_add=True)
    decided_by = models.ForeignKey(User, on_delete=models.CASCADE)
    
    def __str__(self):
        return f"CO Decision for {self.request.request_number} - {self.decision}"
    
    class Meta:
        ordering = ['-decision_date']

class COFeedback(models.Model):
    FEEDBACK_TYPE_CHOICES = [
        ('general', 'General Feedback'),
        ('policy', 'Policy Clarification'),
        ('process', 'Process Improvement'),
        ('urgent', 'Urgent Matter'),
    ]
    
    subject = models.CharField(max_length=200, default='General Feedback')
    message = models.TextField()
    feedback_type = models.CharField(max_length=20, choices=FEEDBACK_TYPE_CHOICES, default='general')
    sent_by = models.ForeignKey(User, on_delete=models.CASCADE)
    date_sent = models.DateTimeField(auto_now_add=True)
    is_read_by_qm = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Feedback: {self.subject}"
    
    class Meta:
        ordering = ['-date_sent']

class QMResponse(models.Model):
    request = models.OneToOneField(DepartmentRequest, on_delete=models.CASCADE)
    response_message = models.TextField()
    pickup_instructions = models.TextField(blank=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    response_date = models.DateTimeField(auto_now_add=True)
    responded_by = models.ForeignKey(User, on_delete=models.CASCADE)
    is_read_by_department = models.BooleanField(default=False)
    
    def __str__(self):
        return f"QM Response for {self.request.request_number}"
    
    class Meta:
        ordering = ['-response_date']

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    employee_id = models.CharField(max_length=20, blank=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.department}"
