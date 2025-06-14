# views.py

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import Group
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import DepartmentRequest, QMNote, COFeedback




# ========== templates links Views ==========
def home(request):
    return render(request, 'index.html')

def about(request):
    return render(request, 'about.html')

def contact(request):
    return render(request, 'contact.html')


# ========== Department (HZO) Dashboard Views ==========

@login_required
def department_dashboard(request):
    user_requests = DepartmentRequest.objects.filter(submitted_by=request.user)
    submitted_count = user_requests.count()
    approved_count = user_requests.filter(status='approved').count()
    rejected_count = user_requests.filter(status='rejected').count()

    context = {
        'user_requests': user_requests,
        'submitted_count': submitted_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
    }
    return render(request, 'department_dashboard.html', context)

@login_required
def submit_request(request):
    if request.method == 'POST':
        equipment = request.POST.get('equipment')
        quantity = request.POST.get('quantity')
        purpose = request.POST.get('purpose')

        DepartmentRequest.objects.create(
            department=request.user.profile.department_name,  # assuming Profile model
            equipment=equipment,
            quantity=quantity,
            purpose=purpose,
            submitted_by=request.user
        )
        return redirect('department_dashboard')


# ========== QM (Store Keeper) Dashboard Views ==========

@login_required
def qm_dashboard(request):
    all_requests = DepartmentRequest.objects.all()
    forwarded_count = DepartmentRequest.objects.filter(status='forwarded').count()
    pending_count = DepartmentRequest.objects.filter(status='pending').count()

    context = {
        'all_requests': all_requests,
        'forwarded_count': forwarded_count,
        'pending_count': pending_count,
    }
    return render(request, 'qm_dashboard.html', context)

@login_required
def forward_to_co(request):
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        note = request.POST.get('note')
        request_obj = get_object_or_404(DepartmentRequest, pk=req_id)

        if request_obj.status == 'pending':
            request_obj.status = 'forwarded'
            request_obj.save()
            QMNote.objects.create(request=request_obj, note=note)

        return redirect('qm_dashboard')

@login_required
def view_feedbacks(request):
    feedbacks = COFeedback.objects.all()
    return render(request, 'qm_feedback.html', {'feedbacks': feedbacks})


# ========== CO (Commanding Officer) Dashboard Views ==========

@login_required
def co_dashboard(request):
    pending_requests = DepartmentRequest.objects.filter(status='forwarded')
    approved_requests = DepartmentRequest.objects.filter(status='approved').count()
    rejected_requests = DepartmentRequest.objects.filter(status='rejected').count()
    total_pending = pending_requests.count()
    history_list = DepartmentRequest.objects.exclude(status='pending')

    context = {
        'review_list': pending_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
        'pending_requests': total_pending,
        'history_list': history_list,
    }
    return render(request, 'co_dashboard.html', context)

@login_required
def co_action(request):
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        action = request.POST.get('action')
        request_obj = get_object_or_404(DepartmentRequest, pk=req_id)

        if action == 'approve':
            request_obj.status = 'approved'
        elif action == 'reject':
            request_obj.status = 'rejected'

        request_obj.save()
        return redirect('co_dashboard')

@login_required
def send_feedback(request):
    if request.method == 'POST':
        message = request.POST.get('feedback')
        COFeedback.objects.create(message=message, sent_by=request.user)
        return redirect('co_dashboard')


# ========== Custom Login and Role-Based Redirection ==========

def custom_login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect_user_by_role(user)
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})

    return render(request, 'login.html')

def redirect_user_by_role(user):
    if user.groups.filter(name='department').exists():
        return HttpResponseRedirect(reverse('department_dashboard'))
    elif user.groups.filter(name='qm').exists():
        return HttpResponseRedirect(reverse('qm_dashboard'))
    elif user.groups.filter(name='co').exists():
        return HttpResponseRedirect(reverse('co_dashboard'))
    else:
        return HttpResponseRedirect('/')
