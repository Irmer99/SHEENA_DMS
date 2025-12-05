from django.urls import path

from . import views

app_name = 'accounts'
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    # path('redirect-dashboard/', views.redirect_dashboard, name='redirect-dashboard'),
    path('admin/dashboard/', views.admin_dashboard, name='admin-dashboard'),
    path('staff/dashboard/', views.staff_dashboard, name='staff-dashboard'),
    path('parent/dashboard/', views.parent_dashboard, name='parent-dashboard'),
    # path('', views.accounts_views, name='accounts_home'),
]