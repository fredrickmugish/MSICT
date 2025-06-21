from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView
from .views import get_request_details  # Add this import

urlpatterns = [
    # ========== Public URLs ==========
    path('', views.home, name='home'),
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),
    path('login/', views.custom_login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    # ========== Department URLs ==========
    path('department/dashboard/', views.department_dashboard, name='department_dashboard'),
    path('department/my-requests/', views.department_my_requests, name='department_my_requests'),
    path('department/submit-request/', views.submit_request, name='submit_request'),
    path('department/feedback/', views.department_feedback, name='department_feedback'),
    path('department/notifications/', views.department_notifications, name='department_notifications'),
    path('department/mark-read/<int:response_id>/', views.mark_response_read, name='mark_response_read'),
    path('request/<int:request_id>/details/', get_request_details, name='get_request_details'),



    # ========== QM URLs ==========
    path('qm/', views.qm_dashboard, name='qm_dashboard'),
    path('qm/incoming-requests/', views.qm_incoming_requests, name='qm_incoming_requests'),
    path('qm/forwarded-requests/', views.qm_forwarded_requests, name='qm_forwarded_requests'),#need modification(fredy template)
    path('qm/co-decisions/', views.qm_co_decisions, name='qm_co_decisions'),
    path('qm/feedbacks/', views.qm_feedbacks, name='qm_feedbacks'),
    path('qm/view-request/<int:request_id>/', views.qm_view_request, name='qm_view_request'),
    path('qm/forward-to-co/', views.forward_to_co, name='forward_to_co'),
    path('qm/respond-to-dept/', views.respond_to_department, name='respond_to_department'),
    path('qm/mark-feedback-read/<int:feedback_id>/', views.mark_feedback_read, name='mark_feedback_read'),
    
    # ========== CO URLs ==========
    path('co/', views.co_dashboard, name='co_dashboard'),
    path('co/review-requests/', views.co_review_requests, name='co_review_requests'),
    path('co/decision-history/', views.co_decision_history, name='co_decision_history'),
    path('co/take-action/', views.co_action, name='co_action'),
    path('co/send-feedback/', views.co_send_feedback, name='co_send_feedback'),
    # path('co/feedback/', views.co_feedback, name='co_feedback'),
    
    # ========== AJAX URLs ==========
    path('ajax/request-status/<int:request_id>/', views.get_request_status, name='get_request_status'),
    path('ajax/dashboard-stats/', views.dashboard_stats, name='dashboard_stats'),
]