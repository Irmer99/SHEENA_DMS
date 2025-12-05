from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q

from .models import Child, Parent, Enrollment


# ============================================
# ADMIN/STAFF VIEWS
# ============================================

@login_required
def child_list_view(request):
    """
    List all children - Only Admin and Staff can access
    Shows search functionality
    """
    # Check if user is admin or staff
    if request.user.role not in ['admin', 'staff']:
        messages.error(request, 'Access denied')
        return redirect('accounts:redirect-dashboard')
    
    # Get all active children
    children = Child.objects.filter(is_active=True).order_by('last_name', 'first_name')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        children = children.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(registration_number__icontains=search_query)
        )
    
    context = {
        'children': children,
        'search_query': search_query,
    }
    
    return render(request, 'children/child_list.html', context)


@login_required
def child_detail_view(request, pk):
    """
    View detailed information about a specific child
    Admin/Staff see everything, Parents only see their children
    """
    child = get_object_or_404(Child, pk=pk)
    
    # Check permissions
    if request.user.role == 'parent':
        # Parent can only view their own children
        try:
            parent_profile = request.user.parent_profile
            if child not in parent_profile.children.all():
                messages.error(request, 'Access denied - This is not your child')
                return redirect('accounts:parent-dashboard')
        except:
            messages.error(request, 'Parent profile not found')
            return redirect('accounts:parent-dashboard')
    elif request.user.role not in ['admin', 'staff']:
        messages.error(request, 'Access denied')
        return redirect('accounts:redirect-dashboard')
    
    # Get related data
    enrollments = child.enrollments.all()
    parents = child.parents.all()
    
    context = {
        'child': child,
        'enrollments': enrollments,
        'parents': parents,
    }
    
    return render(request, 'children/child_detail.html', context)


# ============================================
# PARENT VIEWS
# ============================================

@login_required
def my_children_view(request):
    """
    Parent view - shows only their children
    """
    if request.user.role != 'parent':
        messages.error(request, 'Access denied')
        return redirect('accounts:redirect-dashboard')
    
    try:
        parent_profile = request.user.parent_profile
        children = parent_profile.children.all()
        
        context = {
            'children': children,
        }
        
        return render(request, 'children/my_children.html', context)
    
    except Exception as e:
        messages.error(request, 'Error loading your children')
        return redirect('accounts:parent-dashboard')