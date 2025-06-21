from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
import uuid

class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    head_of_department = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='headed_departments'
    )
    created_date = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name
    
    def get_absolute_url(self):
        return reverse('department_dashboard')
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Department'
        verbose_name_plural = 'Departments'


class DepartmentRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('forwarded', 'Forwarded to CO'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('completed', 'Completed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    request_number = models.CharField(max_length=20, unique=True, blank=True)
    department = models.ForeignKey(
        Department, 
        on_delete=models.CASCADE,
        related_name='requests'
    )
    equipment = models.CharField(max_length=200)
    quantity = models.PositiveIntegerField()
    purpose = models.TextField()
    specifications = models.TextField(blank=True)
    required_date = models.DateField(null=True, blank=True)
    additional_notes = models.TextField(blank=True)
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='medium'
    )
    
    date_submitted = models.DateTimeField(auto_now_add=True)
    date_updated = models.DateTimeField(auto_now=True)
    
    status = models.CharField(
        max_length=20, 
        choices=STATUS_CHOICES, 
        default='pending'
    )
    submitted_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='submitted_requests'
    )
    
    def save(self, *args, **kwargs):
        if not self.request_number:
            self.generate_request_number()
        super().save(*args, **kwargs)
    
    def generate_request_number(self):
        today = timezone.now().date()
        date_str = today.strftime('%Y%m%d')
        daily_count = DepartmentRequest.objects.filter(
            date_submitted__date=today
        ).count() + 1
        base_number = f"REQ-{date_str}-{daily_count:03d}"
        request_number = base_number
        
        counter = 1
        while DepartmentRequest.objects.filter(request_number=request_number).exists():
            request_number = f"{base_number}-{counter}"
            counter += 1
        
        self.request_number = request_number
    
    @property
    def days_pending(self):
        """Calculate days since submission"""
        return (timezone.now().date() - self.date_submitted.date()).days
    
    def get_absolute_url(self):
        return reverse('department_dashboard')
    
    def get_status_class(self):
        """Return CSS class based on status"""
        return {
            'pending': 'warning',
            'forwarded': 'info',
            'approved': 'success',
            'rejected': 'danger',
            'completed': 'dark',
        }.get(self.status, 'secondary')
    
    def get_priority_class(self):
        """Return CSS class based on priority"""
        return {
            'low': 'success',
            'medium': 'warning',
            'high': 'danger',
            'urgent': 'danger pulse',
        }.get(self.priority, 'secondary')
    
    def __str__(self):
        return f"{self.request_number} - {self.equipment}"
    
    class Meta:
        ordering = ['-date_submitted']
        verbose_name = 'Department Request'
        verbose_name_plural = 'Department Requests'


class QMNote(models.Model):
    RECOMMENDATION_CHOICES = [
        ('review', 'Needs Review'),
        ('approve', 'Recommend Approval'),
        ('reject', 'Recommend Rejection'),
    ]
    
    request = models.OneToOneField(
        DepartmentRequest, 
        on_delete=models.CASCADE,
        related_name='qmnote'
    )
    note = models.TextField()
    recommendation = models.CharField(
        max_length=10, 
        choices=RECOMMENDATION_CHOICES, 
        default='review'
    )
    forwarded_date = models.DateTimeField(auto_now_add=True)
    forwarded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='forwarded_notes'
    )
    
    def get_recommendation_class(self):
        """Return CSS class based on recommendation"""
        return {
            'approve': 'success',
            'reject': 'danger',
            'review': 'warning',
        }.get(self.recommendation, 'secondary')
    
    def __str__(self):
        return f"QM Note for {self.request.request_number}"
    
    class Meta:
        ordering = ['-forwarded_date']
        verbose_name = 'QM Note'
        verbose_name_plural = 'QM Notes'


class CODecision(models.Model):
    DECISION_CHOICES = [
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]
    
    request = models.OneToOneField(
        DepartmentRequest, 
        on_delete=models.CASCADE,
        related_name='codecision'
    )
    decision = models.CharField(
        max_length=10, 
        choices=DECISION_CHOICES
    )
    reason = models.TextField()
    additional_notes = models.TextField(blank=True)
    budget_allocation = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True
    )
    expected_procurement_date = models.DateField(null=True, blank=True)
    decision_date = models.DateTimeField(auto_now_add=True)
    decided_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='decisions'
    )
    
    def get_decision_class(self):
        """Return CSS class based on decision"""
        return {
            'approved': 'success',
            'rejected': 'danger',
        }.get(self.decision, 'secondary')
    
    def __str__(self):
        return f"CO Decision for {self.request.request_number} - {self.get_decision_display()}"
    
    class Meta:
        ordering = ['-decision_date']
        verbose_name = 'CO Decision'
        verbose_name_plural = 'CO Decisions'


class COFeedback(models.Model):
    FEEDBACK_TYPE_CHOICES = [
        ('general', 'General Feedback'),
        ('policy', 'Policy Clarification'),
        ('process', 'Process Improvement'),
        ('urgent', 'Urgent Matter'),
    ]
    
    subject = models.CharField(max_length=200, default='General Feedback')
    message = models.TextField()
    feedback_type = models.CharField(
        max_length=20, 
        choices=FEEDBACK_TYPE_CHOICES, 
        default='general'
    )
    sent_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='sent_feedbacks'
    )
    date_sent = models.DateTimeField(auto_now_add=True)
    is_read_by_qm = models.BooleanField(default=False)
    
    def get_feedback_class(self):
        """Return CSS class based on feedback type"""
        return {
            'urgent': 'danger',
            'policy': 'warning',
            'process': 'info',
            'general': 'primary',
        }.get(self.feedback_type, 'secondary')
    
    def __str__(self):
        return f"Feedback: {self.subject}"
    
    class Meta:
        ordering = ['-date_sent']
        verbose_name = 'CO Feedback'
        verbose_name_plural = 'CO Feedbacks'


class QMResponse(models.Model):
    request = models.OneToOneField(
        DepartmentRequest, 
        on_delete=models.CASCADE,
        related_name='qmresponse'
    )
    response_message = models.TextField()
    pickup_instructions = models.TextField(blank=True)
    expected_delivery_date = models.DateField(null=True, blank=True)
    response_date = models.DateTimeField(auto_now_add=True)
    responded_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='responses'
    )
    is_read_by_department = models.BooleanField(default=False)
    
    def __str__(self):
        return f"QM Response for {self.request.request_number}"
    
    class Meta:
        ordering = ['-response_date']
        verbose_name = 'QM Response'
        verbose_name_plural = 'QM Responses'


class UserProfile(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE,
        related_name='profile'
    )
    department = models.ForeignKey(
        Department, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='members'
    )
    phone_number = models.CharField(max_length=15, blank=True)
    employee_id = models.CharField(max_length=20, blank=True)
    
    def get_user_role(self):
        """Determine the user's role based on groups"""
        if self.user.groups.filter(name='department').exists():
            return 'Department'
        elif self.user.groups.filter(name='qm').exists():
            return 'QM'
        elif self.user.groups.filter(name='co').exists():
            return 'CO'
        return 'Unknown'
    
    def __str__(self):
        return f"{self.user.username} - {self.department or 'No Department'}"
    
    class Meta:
        verbose_name = 'User Profile'
        verbose_name_plural = 'User Profiles'