from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect, JsonResponse
from django.urls import reverse
from .models import DepartmentRequest, QMNote, COFeedback, Department, QMResponse, CODecision
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login as auth_login, logout, authenticate
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q, Count
from django.core.paginator import Paginator

# ========== Helper Functions ==========
def is_department_user(user):
    return user.groups.filter(name='department').exists()

def is_qm_user(user):
    return user.groups.filter(name='qm').exists()

def is_co_user(user):
    return user.groups.filter(name='co').exists()

def redirect_user_by_role(user):
    if user.groups.filter(name='department').exists():
        return HttpResponseRedirect(reverse('department_dashboard'))
    elif user.groups.filter(name='qm').exists():
        return HttpResponseRedirect(reverse('qm_dashboard'))
    elif user.groups.filter(name='co').exists():
        return HttpResponseRedirect(reverse('co_dashboard'))
    else:
        return HttpResponseRedirect('/')

# ========== Authentication Views ==========
def home(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')

def custom_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            if user.is_superuser or user.is_staff:
                return HttpResponseRedirect('/admin/')
            return redirect_user_by_role(user)
        return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

# ========== Department Views ==========
@login_required
@user_passes_test(is_department_user)
def department_dashboard(request):
    user = request.user
    user_requests = DepartmentRequest.objects.filter(submitted_by=user)
    
    stats = {
        'total_requests': user_requests.count(),
        'pending_requests': user_requests.filter(status='pending').count(),
        'approved_requests': user_requests.filter(status='approved').count(),
        'rejected_requests': user_requests.filter(status='rejected').count(),
        'completed_requests': user_requests.filter(status='completed').count(),
    }
    
    recent_requests = user_requests.order_by('-date_submitted')[:5]
    recent_responses = QMResponse.objects.filter(request__submitted_by=user).order_by('-response_date')[:3]
    unread_responses = QMResponse.objects.filter(request__submitted_by=user, is_read_by_department=False).count()

    context = {
        **stats,
        'recent_requests': recent_requests,
        'recent_responses': recent_responses,
        'unread_responses': unread_responses,
    }
    return render(request, 'department_dashboard.html', context)

@login_required
@user_passes_test(is_department_user)
def department_my_requests(request):
    requests = DepartmentRequest.objects.filter(submitted_by=request.user).order_by('-date_submitted')
    
    paginator = Paginator(requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'department_my_request.html', {'page_obj': page_obj})

@login_required
@user_passes_test(is_department_user)
def submit_request(request):
    if request.method == 'POST':
        try:
            department_id = request.POST.get('department')
            equipment = request.POST.get('equipment')
            quantity = request.POST.get('quantity')
            purpose = request.POST.get('purpose')
            specifications = request.POST.get('specifications', '')
            required_date = request.POST.get('required_date')
            additional_notes = request.POST.get('additional_notes', '')

            if not all([department_id, equipment, quantity, purpose]):
                messages.error(request, 'Please fill all required fields.')
                return redirect('submit_request')

            department = get_object_or_404(Department, id=department_id)
            
            today = timezone.now().date()
            daily_count = DepartmentRequest.objects.filter(date_submitted__date=today).count() + 1
            request_number = f"REQ-{today.strftime('%Y%m%d')}-{daily_count:03d}"

            request_obj = DepartmentRequest.objects.create(
                request_number=request_number,
                department=department,
                equipment=equipment,
                quantity=int(quantity),
                purpose=purpose,
                specifications=specifications,
                additional_notes=additional_notes,
                submitted_by=request.user,
                required_date=required_date if required_date else None
            )
            
            messages.success(request, f'Request {request_number} submitted successfully!')
            return redirect('department_dashboard')
            
        except Exception as e:
            messages.error(request, f'Error submitting request: {str(e)}')
    
    departments = Department.objects.all()
    return render(request, 'submit_request.html', {'departments': departments})

@login_required
@user_passes_test(is_department_user)
def department_notifications(request):
    responses = QMResponse.objects.filter(request__submitted_by=request.user).order_by('-response_date')
    unread_count = responses.filter(is_read_by_department=False).count()
    
    if 'mark_read' in request.GET:
        responses.update(is_read_by_department=True)
        return redirect('department_notifications')
    
    return render(request, 'department_notifications.html', {
        'responses': responses,
        'unread_count': unread_count
    })

@login_required
@user_passes_test(is_department_user)
def department_feedback(request):
    feedbacks = COFeedback.objects.filter(
        Q(sent_by__groups__name='co') | Q(sent_by__groups__name='qm')
    ).order_by('-date_sent')
    
    return render(request, 'department_feedback.html', {
        'feedbacks': feedbacks
    })

@login_required
@user_passes_test(is_department_user)
def mark_response_read(request, response_id):
    if request.method == 'POST':
        try:
            response = get_object_or_404(QMResponse, pk=response_id, request__submitted_by=request.user)
            response.is_read_by_department = True
            response.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})

# ========== QM Views ==========
@login_required
@user_passes_test(is_qm_user)
def qm_dashboard(request):
    stats = {
        'total_requests': DepartmentRequest.objects.count(),
        'pending_requests': DepartmentRequest.objects.filter(status='pending').count(),
        'forwarded_requests': DepartmentRequest.objects.filter(status='forwarded').count(),
        'approved_requests': DepartmentRequest.objects.filter(status='approved').count(),
        'rejected_requests': DepartmentRequest.objects.filter(status='rejected').count(),
        'unread_feedbacks': COFeedback.objects.filter(is_read_by_qm=False).count(),
    }
    
    recent_requests = DepartmentRequest.objects.filter(status='pending').order_by('-date_submitted')[:5]
    recent_feedbacks = COFeedback.objects.order_by('-date_sent')[:3]
    
    return render(request, 'qm_dashboard.html', {
        **stats,
        'recent_requests': recent_requests,
        'recent_feedbacks': recent_feedbacks
    })

@login_required
@user_passes_test(is_qm_user)
def qm_incoming_requests(request):
    requests = DepartmentRequest.objects.filter(status='pending').order_by('-date_submitted')
    paginator = Paginator(requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'qm_incoming_requests.html', {'page_obj': page_obj})

@login_required
@user_passes_test(is_qm_user)
def qm_forwarded_requests(request):
    requests = DepartmentRequest.objects.filter(status='forwarded').order_by('-date_submitted')
    paginator = Paginator(requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'qm_forwarded_requests.html', {'page_obj': page_obj})

@login_required
@user_passes_test(is_qm_user)
def qm_co_decisions(request):
    requests = DepartmentRequest.objects.filter(
        Q(status='approved') | Q(status='rejected'),
        qmresponse__isnull=True
    ).order_by('-date_submitted')
    paginator = Paginator(requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'qm_co_decisions.html', {'page_obj': page_obj})

@login_required
@user_passes_test(is_qm_user)
def qm_view_request(request, request_id):
    req = get_object_or_404(DepartmentRequest, id=request_id)
    context = {
        'request': req,
        'qm_note': getattr(req, 'qmnote', None),
        'co_decision': getattr(req, 'codecision', None),
        'qm_response': getattr(req, 'qmresponse', None),
    }
    return render(request, 'qm_view_request.html', context)

@login_required
@user_passes_test(is_qm_user)
def forward_to_co(request):
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        note = request.POST.get('comment', '')
        recommendation = request.POST.get('recommendation', 'review')
        
        try:
            req = get_object_or_404(DepartmentRequest, pk=req_id)
            if req.status == 'pending':
                req.status = 'forwarded'
                req.save()
                
                QMNote.objects.create(
                    request=req,
                    note=note,
                    recommendation=recommendation,
                    forwarded_by=request.user
                )
                messages.success(request, f'Request {req.request_number} forwarded to CO!')
            else:
                messages.error(request, 'Request already processed')
        except Exception as e:
            messages.error(request, f'Error forwarding request: {str(e)}')
    return redirect('qm_incoming_requests')

@login_required
@user_passes_test(is_qm_user)
def respond_to_department(request):
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        response_message = request.POST.get('response_message')
        pickup_instructions = request.POST.get('pickup_instructions', '')
        expected_delivery_date = request.POST.get('expected_delivery_date')
        
        try:
            req = get_object_or_404(DepartmentRequest, pk=req_id)
            QMResponse.objects.create(
                request=req,
                response_message=response_message,
                pickup_instructions=pickup_instructions,
                expected_delivery_date=expected_delivery_date,
                responded_by=request.user
            )
            
            if req.status == 'approved':
                req.status = 'completed'
                req.save()
                
            messages.success(request, 'Response sent successfully!')
        except Exception as e:
            messages.error(request, f'Error sending response: {str(e)}')
    return redirect('qm_co_decisions')

@login_required
@user_passes_test(is_qm_user)
def qm_feedbacks(request):
    feedbacks = COFeedback.objects.order_by('-date_sent')
    paginator = Paginator(feedbacks, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'qm_feedbacks.html', {'page_obj': page_obj})

@login_required
@user_passes_test(is_qm_user)
def mark_feedback_read(request, feedback_id):
    if request.method == 'POST':
        try:
            feedback = get_object_or_404(COFeedback, pk=feedback_id)
            feedback.is_read_by_qm = True
            feedback.save()
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False})

# ========== CO Views ==========
@login_required
@user_passes_test(is_co_user)
def co_dashboard(request):
    stats = {
        'total_requests': DepartmentRequest.objects.count(),
        'pending_requests': DepartmentRequest.objects.filter(status='forwarded').count(),
        'approved_requests': DepartmentRequest.objects.filter(status='approved').count(),
        'rejected_requests': DepartmentRequest.objects.filter(status='rejected').count(),
    }
    
    decided = stats['approved_requests'] + stats['rejected_requests']
    stats['approval_rate'] = round((stats['approved_requests'] / decided * 100) if decided > 0 else 0, 1)
    
    recent_decisions = CODecision.objects.order_by('-decision_date')[:5]
    return render(request, 'co_dashboard.html', {
        **stats,
        'recent_decisions': recent_decisions
    })

@login_required
@user_passes_test(is_co_user)
def co_review_requests(request):
    requests = DepartmentRequest.objects.filter(status='forwarded').order_by('-date_submitted')
    paginator = Paginator(requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'co_review_requests.html', {'page_obj': page_obj})

@login_required
@user_passes_test(is_co_user)
def co_decision_history(request):
    decisions = CODecision.objects.order_by('-decision_date')
    paginator = Paginator(decisions, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, 'co_decision_history.html', {'page_obj': page_obj})

@login_required
@user_passes_test(is_co_user)
def co_action(request):
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        action = request.POST.get('action')
        reason = request.POST.get('reason', '')
        
        try:
            req = get_object_or_404(DepartmentRequest, pk=req_id)
            if action in ['approve', 'reject']:
                req.status = 'approved' if action == 'approve' else 'rejected'
                req.save()
                
                CODecision.objects.create(
                    request=req,
                    decision=action,
                    reason=reason,
                    decided_by=request.user
                )
                messages.success(request, f'Request {req.request_number} {action}d!')
        except Exception as e:
            messages.error(request, f'Error processing request: {str(e)}')
    return redirect('co_review_requests')

@login_required
@user_passes_test(is_co_user)
def co_send_feedback(request):
    if request.method == 'POST':
        subject = request.POST.get('subject')
        message = request.POST.get('message')
        
        try:
            COFeedback.objects.create(
                subject=subject,
                message=message,
                sent_by=request.user
            )
            messages.success(request, 'Feedback sent successfully!')
            return redirect('co_dashboard')
        except Exception as e:
            messages.error(request, f'Error sending feedback: {str(e)}')
    return render(request, 'co_send_feedback.html')

# ========== AJAX Views ==========
@login_required
def get_request_status(request, request_id):
    try:
        req = get_object_or_404(DepartmentRequest, pk=request_id)
        data = {
            'request_number': req.request_number,
            'equipment': req.equipment,
            'quantity': req.quantity,
            'department': str(req.department),
            'status': req.get_status_display(),
            'purpose': req.purpose,
            'date_submitted': req.date_submitted.strftime('%b %d, %Y'),
        }
        
        if hasattr(req, 'qmnote'):
            data['qm_note'] = req.qmnote.note
            data['qm_recommendation'] = req.qmnote.get_recommendation_display()
            
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def dashboard_stats(request):
    try:
        if is_department_user(request.user):
            requests = DepartmentRequest.objects.filter(submitted_by=request.user)
            stats = {
                'total': requests.count(),
                'pending': requests.filter(status='pending').count(),
                'approved': requests.filter(status='approved').count(),
                'rejected': requests.filter(status='rejected').count(),
            }
        elif is_qm_user(request.user):
            stats = {
                'total': DepartmentRequest.objects.count(),
                'pending': DepartmentRequest.objects.filter(status='pending').count(),
                'forwarded': DepartmentRequest.objects.filter(status='forwarded').count(),
            }
        elif is_co_user(request.user):
            stats = {
                'total': DepartmentRequest.objects.count(),
                'pending': DepartmentRequest.objects.filter(status='forwarded').count(),
                'approved': DepartmentRequest.objects.filter(status='approved').count(),
                'rejected': DepartmentRequest.objects.filter(status='rejected').count(),
            }
        else:
            stats = {}
        return JsonResponse(stats)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
    
@login_required
@user_passes_test(is_department_user)
def get_request_details(request, request_id):
    """View to show details of a specific request"""
    req = get_object_or_404(
        DepartmentRequest, 
        id=request_id,
        submitted_by=request.user  # Ensure users can only see their own requests
    )
    
    context = {
        'request': req,
        'qm_response': getattr(req, 'qmresponse', None),
        'co_decision': getattr(req, 'codecision', None)
    }
    return render(request, 'department/request_details.html', context)