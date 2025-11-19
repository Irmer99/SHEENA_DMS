# from django.shortcuts import render
# from django.http import HttpResponse
# from django.template import loader
# Create your views here.
# def accounts_views(request):
#     template = loader.get_template('home.html')
#     return HttpResponse(template.render())

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required


def login_view(request):
    # If already logged in, redirect to dashboard
    if request.user.is_authenticated:
        return redirect('accounts:redirect-dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.get_full_name() or user.username}!')
            return redirect('accounts:redirect-dashboard')
        else:
            messages.error(request, 'Invalid username or password')
    
    return render(request, 'accounts/login.html')

# logout view can be added similarly
@login_required
def logout_view(request):
    from django.contrib.auth import logout
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:login')