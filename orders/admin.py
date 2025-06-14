# Register your models here.
from django.contrib import admin
from .models import DepartmentRequest, QMNote, COFeedback

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

@admin.register(COFeedback)
class COFeedbackAdmin(admin.ModelAdmin):
    list_display = ('id', 'sent_by', 'message', 'date_sent')
    search_fields = ('message', 'sent_by__username')
    ordering = ('-date_sent',)
