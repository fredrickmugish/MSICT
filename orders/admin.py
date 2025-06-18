from django.contrib import admin
from .models import DepartmentRequest, QMNote, COFeedback, Department, QMResponse, CODecision, UserProfile

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'head_of_department', 'is_active', 'created_date')
    list_filter = ('is_active', 'created_date')
    search_fields = ('name',)  # Note: this should be a tuple, so we need the comma
    list_editable = ('is_active',)
    ordering = ('name',)

@admin.register(DepartmentRequest)
class DepartmentRequestAdmin(admin.ModelAdmin):
    list_display = ('request_number', 'equipment', 'department', 'quantity', 'status', 'date_submitted', 'submitted_by')
    list_filter = ('status',  'department', 'date_submitted')
    search_fields = ('request_number', 'equipment', 'department__name', 'submitted_by__username')
    ordering = ('-date_submitted',)
    readonly_fields = ('request_number', 'date_submitted', 'date_updated', 'days_pending')
    
    fieldsets = (
        ('Request Information', {
            'fields': ('request_number', 'department', 'submitted_by', 'date_submitted', 'date_updated')
        }),
        ('Equipment Details', {
            'fields': ('equipment', 'quantity', 'specifications',)
        }),
        ('Request Details', {
            'fields': ('purpose',  'required_date', 'additional_notes')
        }),
        ('Status', {
            'fields': ('status',)
        }),
    )

@admin.register(QMNote)
class QMNoteAdmin(admin.ModelAdmin):
    list_display = ('request', 'recommendation', 'forwarded_by', 'forwarded_date')
    list_filter = ('recommendation', 'forwarded_date')
    search_fields = ('request__request_number', 'request__equipment', 'note')
    ordering = ('-forwarded_date',)

@admin.register(CODecision)
class CODecisionAdmin(admin.ModelAdmin):
    list_display = ('request', 'decision', 'budget_allocation', 'decided_by', 'decision_date')
    list_filter = ('decision', 'decision_date')
    search_fields = ('request__request_number', 'request__equipment', 'reason')
    ordering = ('-decision_date',)

@admin.register(COFeedback)
class COFeedbackAdmin(admin.ModelAdmin):
    list_display = ('subject', 'feedback_type', 'sent_by', 'date_sent', 'is_read_by_qm')
    list_filter = ('feedback_type', 'is_read_by_qm', 'date_sent')
    search_fields = ('subject', 'message', 'sent_by__username')
    ordering = ('-date_sent',)

@admin.register(QMResponse)
class QMResponseAdmin(admin.ModelAdmin):
    list_display = ('request', 'responded_by', 'response_date', 'expected_delivery_date', 'is_read_by_department')
    list_filter = ('response_date', 'is_read_by_department')
    search_fields = ('request__request_number', 'request__equipment', 'response_message')
    ordering = ('-response_date',)

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'employee_id', 'phone_number')
    list_filter = ('department',)
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'employee_id')
