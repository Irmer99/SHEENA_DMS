from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Sum, F, DecimalField
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import HttpResponseForbidden
from functools import wraps
from decimal import Decimal
from datetime import date, timedelta

from .models import Invoice, Payment, FeeStructure
from children.models import Parent, Child


# ============================================================================
# DECORATORS & PERMISSIONS
# ============================================================================

def parent_required(view_func):
    """Decorator to restrict view to users with role='parent'"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if getattr(request.user, 'role', None) != 'parent':
            messages.error(request, "You do not have permission to access this page.")
            return HttpResponseForbidden("Access Denied")
        return view_func(request, *args, **kwargs)
    return wrapper


def admin_finance_required(view_func):
    """Decorator to restrict view to admin/finance staff"""
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if getattr(request.user, 'role', None) not in ['admin', 'staff']:
            messages.error(request, "You do not have permission to access this page.")
            return HttpResponseForbidden("Access Denied")
        return view_func(request, *args, **kwargs)
    return wrapper


def get_parent_invoices(parent):
    """Helper: Get all invoices for a parent's children"""
    return Invoice.objects.filter(
        parent=parent
    ).select_related('child', 'fee_structure', 'created_by').prefetch_related('payments').order_by('-due_date')


def can_parent_access_invoice(request, invoice):
    """Helper: Check if logged-in parent can access invoice"""
    if not hasattr(request.user, 'parent_profile'):
        return False
    return invoice.parent == request.user.parent_profile


def can_parent_access_payment(request, payment):
    """Helper: Check if logged-in parent can access payment"""
    return can_parent_access_invoice(request, payment.invoice)


# ============================================================================
# PARENT VIEWS
# ============================================================================

@login_required
@parent_required
def parent_invoices_list(request):
    """
    Parent view: List all invoices for their children
    Shows unpaid, partial, and paid invoices
    """
    parent = request.user.parent_profile
    invoices = get_parent_invoices(parent)
    
    # Optional filtering by status
    status_filter = request.GET.get('status', '')
    if status_filter and status_filter in ['draft', 'sent', 'paid', 'partial', 'overdue']:
        invoices = invoices.filter(status=status_filter)
    
    # Calculate totals for parent's view
    total_due = invoices.aggregate(
        total=Coalesce(Sum('balance_due'), Decimal('0.00'), output_field=DecimalField())
    )['total']
    
    total_paid = invoices.aggregate(
        total=Coalesce(Sum('amount_paid'), Decimal('0.00'), output_field=DecimalField())
    )['total']
    
    context = {
        'invoices': invoices,
        'total_due': total_due,
        'total_paid': total_paid,
        'status_filter': status_filter,
    }
    return render(request, 'finance/parent_invoices_list.html', context)


@login_required
@parent_required
def parent_invoice_detail(request, invoice_id):
    """
    Parent view: Show detailed invoice with payment history
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if not can_parent_access_invoice(request, invoice):
        messages.error(request, "You cannot access this invoice.")
        return HttpResponseForbidden("Access Denied")
    
    payments = invoice.payments.all().order_by('-payment_date')
    
    context = {
        'invoice': invoice,
        'payments': payments,
        'balance_due': invoice.balance_due,
        'is_overdue': invoice.is_overdue,
        'days_overdue': invoice.days_overdue,
    }
    return render(request, 'finance/parent_invoice_detail.html', context)


@login_required
@parent_required
def parent_make_payment(request, invoice_id):
    """
    Parent view: Submit a payment for an invoice
    Accepts GET (show form) and POST (process payment)
    """
    invoice = get_object_or_404(Invoice, id=invoice_id)
    
    if not can_parent_access_invoice(request, invoice):
        messages.error(request, "You cannot pay this invoice.")
        return HttpResponseForbidden("Access Denied")
    
    if invoice.status == 'paid':
        messages.warning(request, "This invoice is already fully paid.")
        return redirect('parent_invoice_detail', invoice_id=invoice.id)
    
    if request.method == 'POST':
        # Get form data
        amount = request.POST.get('amount', '').strip()
        payment_method = request.POST.get('payment_method', '').strip()
        transaction_reference = request.POST.get('transaction_reference', '').strip()
        notes = request.POST.get('notes', '').strip()
        
        # Validation
        try:
            amount = Decimal(amount)
            if amount <= 0:
                raise ValueError("Amount must be greater than 0")
            if amount > invoice.balance_due:
                raise ValueError(f"Amount cannot exceed balance due (${invoice.balance_due})")
        except (ValueError, TypeError) as e:
            messages.error(request, f"Invalid amount: {str(e)}")
            return redirect('parent_make_payment', invoice_id=invoice.id)
        
        if not payment_method:
            messages.error(request, "Please select a payment method.")
            return redirect('parent_make_payment', invoice_id=invoice.id)
        
        # Create payment record
        payment = Payment.objects.create(
            invoice=invoice,
            amount=amount,
            payment_method=payment_method,
            transaction_reference=transaction_reference,
            notes=notes,
            payment_date=date.today(),
            # processed_by could be left null for parent-submitted payments, or set to a system user
        )
        
        messages.success(request, f"Payment of ${amount} recorded successfully!")
        return redirect('parent_payment_confirmation', payment_id=payment.id)
    
    context = {
        'invoice': invoice,
        'balance_due': invoice.balance_due,
        'payment_methods': Payment.PAYMENT_METHOD_CHOICES,
    }
    return render(request, 'finance/parent_make_payment.html', context)


@login_required
@parent_required
def parent_payment_confirmation(request, payment_id):
    """
    Parent view: Show payment confirmation and receipt preview
    """
    payment = get_object_or_404(Payment, id=payment_id)
    
    if not can_parent_access_payment(request, payment):
        messages.error(request, "You cannot access this payment.")
        return HttpResponseForbidden("Access Denied")
    
    context = {
        'payment': payment,
        'invoice': payment.invoice,
    }
    return render(request, 'finance/parent_payment_confirmation.html', context)


# ============================================================================
# ADMIN/FINANCE VIEWS
# ============================================================================

@login_required
@admin_finance_required
def finance_dashboard(request):
    """
    Admin/Finance view: Dashboard with summary and recent activity
    """
    # Summary statistics
    all_invoices = Invoice.objects.all()
    
    total_due = all_invoices.aggregate(
        total=Coalesce(Sum('balance_due'), Decimal('0.00'), output_field=DecimalField())
    )['total']
    
    total_paid = all_invoices.aggregate(
        total=Coalesce(Sum('amount_paid'), Decimal('0.00'), output_field=DecimalField())
    )['total']
    
    total_invoices = all_invoices.count()
    
    unpaid_count = all_invoices.filter(status__in=['draft', 'sent', 'partial']).count()
    overdue_count = all_invoices.filter(status='overdue').count()
    
    # Recent payments (last 10)
    recent_payments = Payment.objects.select_related(
        'invoice', 'invoice__parent', 'invoice__child'
    ).order_by('-payment_date')[:10]
    
    # Overdue invoices (top 5)
    overdue_invoices = all_invoices.filter(
        status__in=['sent', 'partial', 'overdue']
    ).order_by('due_date')[:5]
    
    context = {
        'total_due': total_due,
        'total_paid': total_paid,
        'total_invoices': total_invoices,
        'unpaid_count': unpaid_count,
        'overdue_count': overdue_count,
        'recent_payments': recent_payments,
        'overdue_invoices': overdue_invoices,
    }
    return render(request, 'finance/admin_dashboard.html', context)


@login_required
@admin_finance_required
def payment_history(request):
    """
    Admin/Finance view: Full payment history with filters and pagination
    """
    payments = Payment.objects.select_related(
        'invoice', 'invoice__parent', 'invoice__child', 'processed_by'
    ).order_by('-payment_date')
    
    # Filters
    parent_filter = request.GET.get('parent', '').strip()
    child_filter = request.GET.get('child', '').strip()
    date_from = request.GET.get('date_from', '').strip()
    date_to = request.GET.get('date_to', '').strip()
    
    if parent_filter:
        payments = payments.filter(
            Q(invoice__parent__first_name__icontains=parent_filter) |
            Q(invoice__parent__last_name__icontains=parent_filter)
        )
    
    if child_filter:
        payments = payments.filter(
            Q(invoice__child__first_name__icontains=child_filter) |
            Q(invoice__child__last_name__icontains=child_filter)
        )
    
    if date_from:
        try:
            date_from_obj = timezone.datetime.strptime(date_from, '%Y-%m-%d').date()
            payments = payments.filter(payment_date__gte=date_from_obj)
        except ValueError:
            messages.warning(request, "Invalid 'from' date format.")
    
    if date_to:
        try:
            date_to_obj = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
            payments = payments.filter(payment_date__lte=date_to_obj)
        except ValueError:
            messages.warning(request, "Invalid 'to' date format.")
    
    # Pagination
    paginator = Paginator(payments, 20)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Summary for filtered results
    filtered_total = payments.aggregate(
        total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField())
    )['total']
    
    context = {
        'page_obj': page_obj,
        'filtered_total': filtered_total,
        'parent_filter': parent_filter,
        'child_filter': child_filter,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'finance/admin_payment_history.html', context)


@login_required
@admin_finance_required
def outstanding_invoices(request):
    """
    Admin/Finance view: All unpaid/partial invoices sorted by urgency
    """
    invoices = Invoice.objects.filter(
        status__in=['sent', 'partial', 'overdue']
    ).select_related(
        'parent', 'child', 'fee_structure'
    ).order_by('due_date', '-created_at')
    
    # Optional filter by parent or child
    parent_filter = request.GET.get('parent', '').strip()
    child_filter = request.GET.get('child', '').strip()
    
    if parent_filter:
        invoices = invoices.filter(
            Q(parent__first_name__icontains=parent_filter) |
            Q(parent__last_name__icontains=parent_filter)
        )
    
    if child_filter:
        invoices = invoices.filter(
            Q(child__first_name__icontains=child_filter) |
            Q(child__last_name__icontains=child_filter)
        )
    
    # Pagination
    paginator = Paginator(invoices, 25)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    # Summary
    total_outstanding = invoices.aggregate(
        total=Coalesce(Sum('balance_due'), Decimal('0.00'), output_field=DecimalField())
    )['total']
    
    context = {
        'page_obj': page_obj,
        'total_outstanding': total_outstanding,
        'parent_filter': parent_filter,
        'child_filter': child_filter,
    }
    return render(request, 'finance/admin_outstanding_invoices.html', context)


@login_required
@admin_finance_required
def parent_account_summary(request, parent_id):
    """
    Admin/Finance view: View a specific parent's account with all invoices and payment history
    """
    parent = get_object_or_404(Parent, id=parent_id)
    
    invoices = Invoice.objects.filter(parent=parent).select_related(
        'child', 'fee_structure'
    ).prefetch_related('payments').order_by('-due_date')
    
    payments = Payment.objects.filter(
        invoice__parent=parent
    ).select_related('invoice', 'invoice__child').order_by('-payment_date')
    
    # Summary
    total_billed = invoices.aggregate(
        total=Coalesce(Sum('amount'), Decimal('0.00'), output_field=DecimalField())
    )['total']
    
    total_paid = invoices.aggregate(
        total=Coalesce(Sum('amount_paid'), Decimal('0.00'), output_field=DecimalField())
    )['total']
    
    total_balance_due = invoices.aggregate(
        total=Coalesce(Sum('balance_due'), Decimal('0.00'), output_field=DecimalField())
    )['total']
    
    # Pagination for payments
    paginator = Paginator(payments, 15)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    context = {
        'parent': parent,
        'invoices': invoices,
        'page_obj': page_obj,
        'total_billed': total_billed,
        'total_paid': total_paid,
        'total_balance_due': total_balance_due,
    }
    return render(request, 'finance/admin_parent_account_summary.html', context)
