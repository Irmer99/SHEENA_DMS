from django.urls import path
from . import views

app_name = 'finance'

urlpatterns = [
    # Parent Views
    path('invoices/', views.parent_invoices_list, name='parent_invoices_list'),
    path('invoices/<int:invoice_id>/', views.parent_invoice_detail, name='parent_invoice_detail'),
    path('invoices/<int:invoice_id>/pay/', views.parent_make_payment, name='parent_make_payment'),
    path('payments/<int:payment_id>/confirmation/', views.parent_payment_confirmation, name='parent_payment_confirmation'),
    
    # Admin/Finance Views
    path('admin/dashboard/', views.finance_dashboard, name='finance_dashboard'),
    path('admin/payments/', views.payment_history, name='payment_history'),
    path('admin/outstanding/', views.outstanding_invoices, name='outstanding_invoices'),
    path('admin/parent/<int:parent_id>/account/', views.parent_account_summary, name='parent_account_summary'),
]