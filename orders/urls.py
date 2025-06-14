from django.urls import path
from . import views

urlpatterns = [
    # Home page
    path('', views.home, name='home'),

    # Login page
    path('login/', views.custom_login_view, name='login'),

     # New pages
    path('about/', views.about, name='about'),
    path('contact/', views.contact, name='contact'),

    # Department (HZO)
    path('department/dashboard/', views.department_dashboard, name='department_dashboard'),
    path('department/submit/', views.submit_request, name='submit_request'),

    # QM (Store Keeper)
    path('qm/dashboard/', views.qm_dashboard, name='qm_dashboard'),
    path('qm/forward/', views.forward_to_co, name='forward_to_co'),
    path('qm/feedbacks/', views.view_feedbacks, name='qm_feedbacks'),

    # CO (Commanding Officer)
    path('co/dashboard/', views.co_dashboard, name='co_dashboard'),
    path('co/action/', views.co_action, name='co_action'),
    path('co/send-feedback/', views.send_feedback, name='send_feedback'),
]
