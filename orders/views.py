from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import DepartmentRequest, QMNote, COFeedback, Department, CODecision, QMResponse
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import PermissionDenied
from django.contrib.auth import login as auth_login, logout, authenticate
from django.contrib import messages

# ========== templates links Views ==========
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
            else:
                return redirect_user_by_role(user)
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def redirect_user_by_role(user):
    if user.groups.filter(name='department').exists():
        return HttpResponseRedirect(reverse('department_dashboard'))
    elif user.groups.filter(name='qm').exists():
        return HttpResponseRedirect(reverse('qm_dashboard'))
    elif user.groups.filter(name='co').exists():
        return HttpResponseRedirect(reverse('co_dashboard'))
    else:
        return HttpResponseRedirect('/')
    
# Helper functions to check user groups
def is_department_user(user):
    return user.groups.filter(name='department').exists()

def is_qm_user(user):
    return user.groups.filter(name='qm').exists()

def is_co_user(user):
    return user.groups.filter(name='co').exists()

@login_required
@user_passes_test(is_department_user)
def department_dashboard(request):
    user_requests = DepartmentRequest.objects.filter(submitted_by=request.user)
    
    # Get QM responses for user's requests
    qm_responses = QMResponse.objects.filter(request__submitted_by=request.user).order_by('-response_date')
    
    context = {
        'my_requests': user_requests,
        'total_requests': user_requests.count(),
        'approved_requests': user_requests.filter(status='approved').count(),
        'rejected_requests': user_requests.filter(status='rejected').count(),
        'pending_requests': user_requests.filter(status='pending').count(),
        'qm_responses': qm_responses,
    }
    return render(request, 'department_dashboard.html', context)

@login_required
@user_passes_test(is_department_user)
def submit_request(request):
    if request.method == 'POST':
        department_id = request.POST.get('department')
        equipment = request.POST.get('equipment')
        quantity = request.POST.get('quantity')
        purpose = request.POST.get('purpose')

        try:
            department = Department.objects.get(id=department_id)
            
            DepartmentRequest.objects.create(
                department=department.name,
                equipment=equipment,
                quantity=quantity,
                purpose=purpose,
                submitted_by=request.user
            )
            
            messages.success(request, 'Your equipment request has been submitted successfully!')
            return redirect('department_dashboard')
            
        except Department.DoesNotExist:
            messages.error(request, 'Invalid department selected.')
        except Exception as e:
            messages.error(request, 'An error occurred while submitting your request.')
    
    departments = Department.objects.all()
    context = {'departments': departments}
    return render(request, 'submit_request.html', context)

@login_required
@user_passes_test(is_qm_user)
def qm_dashboard(request):
    all_requests = DepartmentRequest.objects.all()
    pending_requests = DepartmentRequest.objects.filter(status='pending')
    forwarded_requests = DepartmentRequest.objects.filter(status='forwarded')
    
    # Get requests that have been decided by CO (approved/rejected) but not yet responded to by QM
    co_decided_requests = DepartmentRequest.objects.filter(
        status__in=['approved', 'rejected']
    ).exclude(
        id__in=QMResponse.objects.values_list('request_id', flat=True)
    )
    
    co_feedbacks = COFeedback.objects.all().order_by('-date_sent')

    context = {
        'all_requests': all_requests,
        'incoming_requests': pending_requests,
        'pending_requests': pending_requests,
        'forwarded_requests': forwarded_requests.count(),
        'co_decided_requests': co_decided_requests,
        'total_requests': all_requests.count(),
        'pending_requests_count': pending_requests.count(),
        'co_feedbacks': co_feedbacks,
    }
    return render(request, 'qm_dashboard.html', context)

@login_required
@user_passes_test(is_qm_user)
def qm_forward(request):
    pending_requests = DepartmentRequest.objects.filter(status='pending').order_by('-date_submitted')
    context = {'pending_requests': pending_requests}
    return render(request, 'qm_forward.html', context)

@login_required
@user_passes_test(is_qm_user)
def forward_to_co(request):
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        note = request.POST.get('comment')
        
        try:
            request_obj = get_object_or_404(DepartmentRequest, pk=req_id)

            if request_obj.status == 'pending':
                request_obj.status = 'forwarded'
                request_obj.save()
                
                if note:
                    QMNote.objects.create(request=request_obj, note=note)
                
                messages.success(request, f'Request for {request_obj.equipment} has been forwarded to CO successfully!')
            else:
                messages.error(request, 'This request has already been processed.')
                
        except Exception as e:
            messages.error(request, 'An error occurred while forwarding the request.')

        return redirect('qm_dashboard')
    
    return redirect('qm_dashboard')

@login_required
@user_passes_test(is_qm_user)
def respond_to_department(request):
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        response_message = request.POST.get('response_message')
        
        try:
            request_obj = get_object_or_404(DepartmentRequest, pk=req_id)
            
            # Create QM response
            QMResponse.objects.create(
                request=request_obj,
                response_message=response_message,
                responded_by=request.user
            )
            
            # Mark request as completed
            request_obj.status = 'completed'
            request_obj.save()
            
            messages.success(request, f'Response sent to {request_obj.department} successfully!')
            
        except Exception as e:
            messages.error(request, 'An error occurred while sending the response.')
    
    return redirect('qm_dashboard')

@login_required
@user_passes_test(is_qm_user)
def view_feedbacks(request):
    feedbacks = COFeedback.objects.all()
    return render(request, 'qm_feedback.html', {'feedbacks': feedbacks})

@login_required
@user_passes_test(is_co_user)
def co_dashboard(request):
    pending_requests = DepartmentRequest.objects.filter(status='forwarded')
    approved_requests = DepartmentRequest.objects.filter(status='approved').count()
    rejected_requests = DepartmentRequest.objects.filter(status='rejected').count()
    total_pending = pending_requests.count()
    history_list = DepartmentRequest.objects.filter(status__in=['approved', 'rejected']).order_by('-date_submitted')

    context = {
        'review_list': pending_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
        'pending_requests': total_pending,
        'history_list': history_list,
    }
    return render(request, 'co_dashboard.html', context)

@login_required
@user_passes_test(is_co_user)
def co_action(request):
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        action = request.POST.get('action')
        reason = request.POST.get('reason', '')
        
        request_obj = get_object_or_404(DepartmentRequest, pk=req_id)

        if action == 'approve':
            request_obj.status = 'approved'
            decision = 'approved'
        elif action == 'reject':
            request_obj.status = 'rejected'
            decision = 'rejected'

        request_obj.save()
        
        # Create CO decision record
        CODecision.objects.create(
            request=request_obj,
            decision=decision,
            reason=reason,
            decided_by=request.user
        )
        
        messages.success(request, f'Request has been {decision} successfully!')
        return redirect('co_dashboard')

@login_required
@user_passes_test(is_co_user)
def send_feedback(request):
    if request.method == 'POST':
        message = request.POST.get('feedback')
        COFeedback.objects.create(message=message, sent_by=request.user)
        messages.success(request, 'Feedback sent to QM successfully!')
        return redirect('co_dashboard')
