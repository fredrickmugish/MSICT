from django.contrib import admin
from .models import DepartmentRequest, QMNote, COFeedback, Department, CODecision, QMResponse

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')

@admin.register(DepartmentRequest)
class DepartmentRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'department', 'equipment', 'quantity', 'status', 'date_submitted', 'submitted_by')
    list_filter = ('status', 'department', 'date_submitted')
    search_fields = ('equipment', 'department', 'submitted_by__username')
    ordering = ('-date_submitted',)

@admin.register(QMNote)
class QMNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'note', 'forwarded_date')
    search_fields = ('note', 'request__equipment')

@admin.register(CODecision)
class CODecisionAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'decision', 'decided_by', 'decision_date')
    list_filter = ('decision', 'decision_date')
    search_fields = ('request__equipment', 'decided_by__username')

@admin.register(QMResponse)
class QMResponseAdmin(admin.ModelAdmin):
    list_display = ('id', 'request', 'responded_by', 'response_date')
    search_fields = ('response_message', 'request__equipment')

@admin.register(COFeedback)
class COFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'sent_by', 'message', 'date_sent')
    search_fields = ('message', 'sent_by__username')
    ordering = ('-date_sent',)
