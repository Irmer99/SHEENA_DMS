from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages


def login_view(request):
    """Login view - handles user authentication"""
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            
            # Check if user has a valid role
            if not hasattr(user, 'role') or not user.role:
                messages.error(request, 'Your account does not have a role assigned. Please contact admin.')
                logout(request)
                return render(request, 'accounts/login.html')
            
            # Redirect based on role - DIRECTLY, no intermediate redirect
            if user.role == 'admin':
                return redirect('accounts:admin-dashboard')
            elif user.role == 'staff':
                return redirect('accounts:staff-dashboard')
            elif user.role == 'parent':
                return redirect('accounts:parent-dashboard')
            else:
                messages.error(request, f'Invalid role: {user.role}')
                logout(request)
                return render(request, 'accounts/login.html')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    """Logout view - logs out the user"""
    logout(request)
    messages.info(request, 'You have been logged out successfully')
    return redirect('accounts:login')


@login_required
def admin_dashboard(request):
    """Admin dashboard - only accessible by admins"""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied - Admin only')
        logout(request)
        return redirect('accounts:login')
    
    context = {
        'user': request.user,
    }
    
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
def staff_dashboard(request):
    """Staff dashboard - only accessible by staff"""
    if request.user.role != 'staff':
        messages.error(request, 'Access denied - Staff only')
        logout(request)
        return redirect('accounts:login')
    
    context = {
        'user': request.user,
    }
    
    return render(request, 'accounts/staff_dashboard.html', context)


@login_required
def parent_dashboard(request):
    """Parent dashboard - only accessible by parents"""
    if request.user.role != 'parent':
        messages.error(request, 'Access denied - Parent only')
        logout(request)
        return redirect('accounts:login')
    
    context = {
        'user': request.user,
    }
    
    return render(request, 'accounts/parent_dashboard.html', context)