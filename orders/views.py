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
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q, Count
from django.core.paginator import Paginator

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
            # Check if user is superuser or staff member
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

# ========== Department Views ==========
@login_required
@user_passes_test(is_department_user)
def department_dashboard(request):
    user_requests = DepartmentRequest.objects.filter(submitted_by=request.user).order_by('-date_submitted')
    
    # Get statistics
    total_requests = user_requests.count()
    pending_count = user_requests.filter(status='pending').count()
    forwarded_count = user_requests.filter(status='forwarded').count()
    approved_count = user_requests.filter(status='approved').count()
    rejected_count = user_requests.filter(status='rejected').count()
    completed_count = user_requests.filter(status='completed').count()
    
    # Get recent responses from QM
    recent_responses = QMResponse.objects.filter(request__submitted_by=request.user).order_by('-response_date')[:5]
    
    # Get unread responses count
    unread_responses = QMResponse.objects.filter(
        request__submitted_by=request.user,
        is_read_by_department=False
    ).count()

    context = {
        'user_requests': user_requests[:10],  # Show latest 10 requests
        'my_requests': user_requests,
        'total_requests': total_requests,
        'pending_requests': pending_count,
        'forwarded_requests': forwarded_count,
        'approved_requests': approved_count,
        'rejected_requests': rejected_count,
        'completed_requests': completed_count,
        'recent_responses': recent_responses,
        'unread_responses': unread_responses,
        'feedbacks': [],
    }
    return render(request, 'department_dashboard.html', context)
@login_required
@user_passes_test(is_department_user)
def submit_request(request):
    if request.method == 'POST':
        try:
            # Debug: Print all POST data
            print("=== DEBUG: POST DATA ===")
            for key, value in request.POST.items():
                print(f"{key}: {value}")
            print("========================")
            
            # Get form data
            department_id = request.POST.get('department')
            equipment = request.POST.get('equipment')
            quantity = request.POST.get('quantity')
            purpose = request.POST.get('purpose')
            specifications = request.POST.get('specifications', '')
            required_date = request.POST.get('required_date')
            additional_notes = request.POST.get('additional_notes', '')

            # Validate required fields
            if not department_id:
                messages.error(request, 'Please select a department.')
                raise ValueError("Department not selected")
            
            if not equipment:
                messages.error(request, 'Please enter equipment name.')
                raise ValueError("Equipment name not provided")
                
            if not quantity:
                messages.error(request, 'Please enter quantity.')
                raise ValueError("Quantity not provided")
                
            if not purpose:
                messages.error(request, 'Please enter purpose.')
                raise ValueError("Purpose not provided")

            print(f"Department ID: {department_id}")
            print(f"Equipment: {equipment}")
            print(f"Quantity: {quantity}")

            # Get department object
            try:
                department = Department.objects.get(id=department_id)
                print(f"Department found: {department.name}")
            except Department.DoesNotExist:
                print("Department does not exist")
                messages.error(request, 'Invalid department selected.')
                raise
            
            # Generate request number
            today = timezone.now().date()
            daily_count = DepartmentRequest.objects.filter(date_submitted__date=today).count() + 1
            request_number = f"REQ-{today.strftime('%Y%m%d')}-{daily_count:03d}"

            print(f"Generated request number: {request_number}")

            # Prepare data for creation
            request_data = {
                'request_number': request_number,
                'department': department,
                'equipment': equipment,
                'quantity': int(quantity),
                'purpose': purpose,
                'specifications': specifications,
                'additional_notes': additional_notes,
                'submitted_by': request.user
            }
            
            # Handle optional date field
            if required_date:
                try:
                    from datetime import datetime
                    parsed_date = datetime.strptime(required_date, '%Y-%m-%d').date()
                    request_data['required_date'] = parsed_date
                    print(f"Required date: {parsed_date}")
                except ValueError as e:
                    print(f"Date parsing error: {e}")
                    # Don't fail the request for date parsing issues
                    pass

            print("Creating request with data:")
            for key, value in request_data.items():
                print(f"  {key}: {value}")

            # Create the request
            request_obj = DepartmentRequest.objects.create(**request_data)
            
            print(f"Request created successfully with ID: {request_obj.id}")
            messages.success(request, f'Your equipment request ({request_number}) has been submitted successfully!')
            return redirect('department_dashboard')
            
        except Exception as e:
            print(f"=== ERROR DETAILS ===")
            print(f"Error type: {type(e).__name__}")
            print(f"Error message: {str(e)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            print("====================")
            
            # Show specific error message if we haven't already set one
            if not messages.get_messages(request):
                messages.error(request, f'An error occurred while submitting your request: {str(e)}')
    
    # For GET requests, show the form
    try:
        departments = Department.objects.all()
        recent_requests = DepartmentRequest.objects.filter(submitted_by=request.user).order_by('-date_submitted')[:5]
        
        print(f"Available departments: {[dept.name for dept in departments]}")
        print(f"Recent requests count: {recent_requests.count()}")
        
        context = {
            'departments': departments,
            'recent_requests': recent_requests
        }
        return render(request, 'submit_request.html', context)
        
    except Exception as e:
        print(f"Error loading form data: {e}")
        messages.error(request, 'Error loading form data.')
        return render(request, 'submit_request.html', {'departments': [], 'recent_requests': []})

# ========== QM Views ==========
@login_required
@user_passes_test(is_qm_user)
def qm_dashboard(request):
    # Get all requests for statistics
    all_requests = DepartmentRequest.objects.all()
    
    # Get requests by status
    pending_requests = DepartmentRequest.objects.filter(status='pending').order_by('-date_submitted')
    forwarded_requests_list = DepartmentRequest.objects.filter(status='forwarded').order_by('-date_submitted')
    
    # Get CO decided requests awaiting QM response
    co_decided_requests = DepartmentRequest.objects.filter(
        status__in=['approved', 'rejected']
    ).exclude(
        id__in=QMResponse.objects.values_list('request_id', flat=True)
    ).order_by('-date_submitted')
    
    # Get counts
    total_requests = all_requests.count()
    pending_count = pending_requests.count()
    forwarded_count = forwarded_requests_list.count()
    approved_count = all_requests.filter(status='approved').count()
    rejected_count = all_requests.filter(status='rejected').count()
    completed_count = all_requests.filter(status='completed').count()
    
    # Get CO feedbacks
    co_feedbacks = COFeedback.objects.all().order_by('-date_sent')
    unread_feedbacks = co_feedbacks.filter(is_read_by_qm=False).count()

    context = {
        'all_requests': all_requests,
        'incoming_requests': pending_requests,
        'forwarded_requests_list': forwarded_requests_list,
        'co_decided_requests': co_decided_requests,
        'total_requests': total_requests,
        'pending_requests_count': pending_count,
        'forwarded_count': forwarded_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'completed_count': completed_count,
        'co_feedbacks': co_feedbacks,
        'unread_feedbacks': unread_feedbacks,
    }
    return render(request, 'qm_dashboard.html', context)

@login_required
@user_passes_test(is_qm_user)
def qm_forward(request):
    # Get pending requests for the form
    pending_requests = DepartmentRequest.objects.filter(status='pending').order_by('-date_submitted')
    
    context = {
        'pending_requests': pending_requests,
    }
    return render(request, 'qm_forward.html', context)

@login_required
@user_passes_test(is_qm_user)
def forward_to_co(request):
    if request.method == 'POST':
        req_id = request.POST.get('request_id')
        note = request.POST.get('comment', '')
        recommendation = request.POST.get('recommendation', 'review')
        
        try:
            request_obj = get_object_or_404(DepartmentRequest, pk=req_id)

            if request_obj.status == 'pending':
                request_obj.status = 'forwarded'
                request_obj.save()
                
                # Create QM note
                QMNote.objects.create(
                    request=request_obj,
                    note=note,
                    recommendation=recommendation,
                    forwarded_by=request.user
                )
                
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
        pickup_instructions = request.POST.get('pickup_instructions', '')
        expected_delivery_date = request.POST.get('expected_delivery_date')
        
        try:
            request_obj = get_object_or_404(DepartmentRequest, pk=req_id)
            
            # Create QM response
            QMResponse.objects.create(
                request=request_obj,
                response_message=response_message,
                pickup_instructions=pickup_instructions,
                expected_delivery_date=expected_delivery_date if expected_delivery_date else None,
                responded_by=request.user
            )
            
            # Update request status to completed if approved
            if request_obj.status == 'approved':
                request_obj.status = 'completed'
                request_obj.save()
            
            messages.success(request, f'Response sent to {request_obj.department} for {request_obj.equipment}!')
            
        except Exception as e:
            messages.error(request, 'An error occurred while sending the response.')
            
        return redirect('qm_dashboard')

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

@login_required
@user_passes_test(is_qm_user)
def view_feedbacks(request):
    feedbacks = COFeedback.objects.all().order_by('-date_sent')
    return render(request, 'qm_feedback.html', {'feedbacks': feedbacks})

# ========== CO Views ==========
@login_required
@user_passes_test(is_co_user)
def co_dashboard(request):
    # Get requests awaiting review
    pending_requests = DepartmentRequest.objects.filter(status='forwarded').order_by('-date_submitted')
    
    # Add calculated fields - FIXED: Don't assign to property, just access it
    for req in pending_requests:
        # Access the property (don't assign to it)
        calculated_days = req.days_pending  # This reads the property
        
        # Add QM note information
        try:
            req.qm_note = req.qmnote
        except:
            req.qm_note = None
    
    # Get statistics
    all_requests = DepartmentRequest.objects.all()
    total_requests = all_requests.count()
    approved_count = all_requests.filter(status='approved').count()
    rejected_count = all_requests.filter(status='rejected').count()
    completed_count = all_requests.filter(status='completed').count()
    pending_count = pending_requests.count()
    
    # Calculate approval rate
    decided_requests = approved_count + rejected_count
    approval_rate = (approved_count / decided_requests * 100) if decided_requests > 0 else 0
    
    # Get recent decisions
    recent_decisions = CODecision.objects.select_related('request').order_by('-decision_date')[:10]
    
    # Get history list (excluding pending)
    history_list = DepartmentRequest.objects.exclude(status='pending').order_by('-date_submitted')[:20]

    context = {
        'review_list': pending_requests,
        'total_requests': total_requests,
        'approved_requests': approved_count,
        'rejected_requests': rejected_count,
        'completed_requests': completed_count,
        'pending_requests': pending_count,
        'approval_rate': round(approval_rate, 1),
        'recent_decisions': recent_decisions,
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
        additional_notes = request.POST.get('additional_notes', '')
        budget_allocation = request.POST.get('budget_allocation')
        expected_procurement_date = request.POST.get('expected_procurement_date')
        
        try:
            request_obj = get_object_or_404(DepartmentRequest, pk=req_id)

            if action in ['approve', 'reject']:
                request_obj.status = 'approved' if action == 'approve' else 'rejected'
                request_obj.save()
                
                # Create CO decision record
                CODecision.objects.create(
                    request=request_obj,
                    decision=action,
                    reason=reason,
                    additional_notes=additional_notes,
                    budget_allocation=budget_allocation if budget_allocation else None,
                    expected_procurement_date=expected_procurement_date if expected_procurement_date else None,
                    decided_by=request.user
                )
                
                action_text = 'approved' if action == 'approve' else 'rejected'
                messages.success(request, f'Request for {request_obj.equipment} has been {action_text}!')
                
        except Exception as e:
            messages.error(request, 'An error occurred while processing the request.')
            
        return redirect('co_dashboard')
    
    return redirect('co_dashboard')

@login_required
@user_passes_test(is_co_user)
def send_feedback(request):
    if request.method == 'POST':
        subject = request.POST.get('subject', 'General Feedback')
        message = request.POST.get('message')
        feedback_type = request.POST.get('feedback_type', 'general')
        
        try:
            COFeedback.objects.create(
                subject=subject,
                message=message,
                feedback_type=feedback_type,
                sent_by=request.user
            )
            messages.success(request, 'Feedback sent to QM successfully!')
        except Exception as e:
            messages.error(request, 'An error occurred while sending feedback.')
            
        return redirect('co_dashboard')
    
    return redirect('co_dashboard')

# ========== AJAX/API Views ==========
@login_required
def get_request_status(request, request_id):
    try:
        req = get_object_or_404(DepartmentRequest, pk=request_id)
        
        # Calculate days pending using the property (read-only)
        days_pending = req.days_pending
        
        # Get QM note if exists
        qm_note = None
        qm_recommendation = None
        qm_forwarded_date = None
        try:
            qm_note_obj = req.qmnote
            qm_note = qm_note_obj.note
            qm_recommendation = qm_note_obj.get_recommendation_display()
            qm_forwarded_date = qm_note_obj.forwarded_date.strftime('%b %d, %Y %H:%M')
        except:
            pass

        data = {
            'request_number': req.request_number,
            'equipment': req.equipment,
            'quantity': req.quantity,
            'department': str(req.department),
            'priority_display': req.get_priority_display(),
            'status_display': req.get_status_display(),
            'purpose': req.purpose,
            'date_submitted': req.date_submitted.strftime('%b %d, %Y'),
            'last_updated': req.date_submitted.strftime('%b %d, %Y %H:%M'),
            'days_pending': days_pending,
            'qm_note': qm_note,
            'qm_recommendation': qm_recommendation,
            'qm_forwarded_date': qm_forwarded_date,
        }
        return JsonResponse(data)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def dashboard_stats(request):
    """Return dashboard statistics as JSON"""
    try:
        if is_department_user(request.user):
            user_requests = DepartmentRequest.objects.filter(submitted_by=request.user)
            stats = {
                'total_requests': user_requests.count(),
                'pending_requests': user_requests.filter(status='pending').count(),
                'approved_requests': user_requests.filter(status='approved').count(),
                'rejected_requests': user_requests.filter(status='rejected').count(),
            }
        elif is_qm_user(request.user):
            all_requests = DepartmentRequest.objects.all()
            stats = {
                'total_requests': all_requests.count(),
                'pending_requests': all_requests.filter(status='pending').count(),
                'forwarded_requests': all_requests.filter(status='forwarded').count(),
                'completed_requests': all_requests.filter(status='completed').count(),
            }
        elif is_co_user(request.user):
            all_requests = DepartmentRequest.objects.all()
            stats = {
                'total_requests': all_requests.count(),
                'pending_requests': all_requests.filter(status='forwarded').count(),
                'approved_requests': all_requests.filter(status='approved').count(),
                'rejected_requests': all_requests.filter(status='rejected').count(),
            }
        else:
            stats = {}
            
        return JsonResponse(stats)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

# Add this function to your existing views.py file
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
