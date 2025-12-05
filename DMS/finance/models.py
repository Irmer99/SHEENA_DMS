from django.db import models
from django.conf import settings
from decimal import Decimal
from datetime import datetime, date


class FeeStructure(models.Model):
    """
    Defines fee types and amounts (tuition, registration, meals, etc.).
    Can be applied to invoices.
    """
    FREQUENCY_CHOICES = [
        ('one_time', 'One-Time Fee'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annual', 'Annual'),
    ]
    
    CATEGORY_CHOICES = [
        ('tuition', 'Tuition'),
        ('registration', 'Registration Fee'),
        ('meals', 'Meals'),
        ('activities', 'Activities/Field Trips'),
        ('supplies', 'Supplies'),
        ('late_pickup', 'Late Pickup Fee'),
        ('other', 'Other'),
    ]
    
    # name of the fee the parent is paying for
    name = models.CharField(
        max_length=100,
        help_text="e.g., 'Monthly Toddler Tuition', 'Registration Fee 2024'"
    )
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Fee amount in local currency"
    )
    frequency = models.CharField(max_length=15, choices=FREQUENCY_CHOICES)
    
    # Applicability
    applies_to_class = models.CharField(
        max_length=20,
        choices=[
            ('all', 'All Classes'),
            ('infants', 'Infants'),
            ('toddlers', 'Toddlers'),
            ('preschool', 'Preschool'),
            ('pre_k', 'Pre-K'),
        ],
        default='all'
    )
    
    description = models.TextField(
        blank=True,
        help_text="What this fee covers"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this fee structure is currently in use"
    )
    effective_date = models.DateField(
        help_text="Date this fee structure became/becomes effective"
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date this fee structure expires (leave blank if ongoing)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'fee_structures'
        ordering = ['-effective_date', 'name']
        verbose_name_plural = 'Fee Structures'
        
    def __str__(self):
        return f"{self.name} - {self.amount} ({self.get_frequency_display()})"
    
    @property
    def is_currently_effective(self):
        """Check if fee structure is currently valid"""
        today = date.today()
        if not self.is_active:
            return False
        if self.effective_date > today:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True


class Invoice(models.Model):
    """
    Invoice sent to parents for fees.
    Multiple invoices per child over time.
    """
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('sent', 'Sent'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('overdue', 'Overdue'),
        ('cancelled', 'Cancelled'),
    ]
    
    invoice_number = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        help_text="Auto-generated unique invoice number"
    )
    
    # Relationships
    parent = models.ForeignKey(
        'children.Parent',
        on_delete=models.PROTECT,
        related_name='invoices',
        help_text="Parent responsible for payment"
    )
    child = models.ForeignKey(
        'children.Child',
        on_delete=models.PROTECT,
        related_name='invoices',
        help_text="Child this invoice is for"
    )
    fee_structure = models.ForeignKey(
        FeeStructure,
        on_delete=models.PROTECT,
        related_name='invoices'
    )
    
    # Financial Details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Total invoice amount"
    )
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text="Total amount paid so far"
    )
    
    # Dates
    issue_date = models.DateField(
        auto_now_add=True,
        help_text="Date invoice was created"
    )
    due_date = models.DateField(help_text="Payment due date")
    paid_date = models.DateField(
        blank=True,
        null=True,
        help_text="Date invoice was fully paid"
    )
    
    # Status
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='draft'
    )
    
    # Additional Info
    description = models.TextField(
        blank=True,
        help_text="What this invoice covers (e.g., 'January 2024 Tuition')"
    )
    notes = models.TextField(
        blank=True,
        help_text="Internal notes or payment terms"
    )
    
    # Administrative
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_invoices'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'invoices'
        ordering = ['-issue_date', '-invoice_number']
        
    def save(self, *args, **kwargs):
        if not self.invoice_number:
            # Generate invoice number: INV-YYYYMMDD-XXXX
            today = datetime.now()
            prefix = f"INV-{today.strftime('%Y%m%d')}"
            last_invoice = Invoice.objects.filter(
                invoice_number__startswith=prefix
            ).order_by('-invoice_number').first()
            
            if last_invoice:
                last_num = int(last_invoice.invoice_number.split('-')[-1])
                new_num = last_num + 1
            else:
                new_num = 1
            
            self.invoice_number = f"{prefix}-{new_num:04d}"
        
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.invoice_number} - {self.parent.full_name} ({self.status})"
    
    @property
    def balance_due(self):
        """Calculate remaining balance"""
        return self.amount - self.amount_paid
    
    @property
    def is_overdue(self):
        """Check if invoice is past due date and unpaid"""
        if self.status in ['paid', 'cancelled']:
            return False
        return date.today() > self.due_date
    
    @property
    def days_overdue(self):
        """Calculate how many days past due"""
        if not self.is_overdue:
            return 0
        return (date.today() - self.due_date).days


class Payment(models.Model):
    """
    Records payments made against invoices.
    An invoice can have multiple payments (partial payments).
    """
    PAYMENT_METHOD_CHOICES = [
        ('cash', 'Cash'),
        ('mobile_money', 'Mobile Money'),
        ('bank_transfer', 'Bank Transfer'),
        ('debit_card', 'Debit Card'),
        ('credit_card', 'Credit Card'),
        ('cheque', 'Cheque'),
    ]
    
    invoice = models.ForeignKey(
        Invoice,
        on_delete=models.PROTECT,
        related_name='payments'
    )
    
    # Payment Details
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Amount paid in this transaction"
    )
    payment_date = models.DateField(
        default=date.today,
        help_text="Date payment was received"
    )
    payment_method = models.CharField(
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES
    )
    
    # Transaction Reference
    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
        help_text="Bank reference, mobile money code, cheque number, etc."
    )
    
    # Additional Info
    notes = models.TextField(
        blank=True,
        help_text="Additional payment notes"
    )
    receipt_number = models.CharField(
        max_length=50,
        blank=True,
        help_text="Receipt number issued to parent"
    )
    
    # Administrative
    processed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='processed_payments',
        help_text="Staff member who recorded this payment"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-payment_date', '-created_at']
        
    def __str__(self):
        return f"{self.amount} - {self.invoice.invoice_number} ({self.payment_date})"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        
        # Update invoice's amount_paid and status
        invoice = self.invoice
        total_paid = sum(
            payment.amount for payment in invoice.payments.all()
        )
        invoice.amount_paid = total_paid
        
        if total_paid >= invoice.amount:
            invoice.status = 'paid'
            invoice.paid_date = self.payment_date
        elif total_paid > 0:
            invoice.status = 'partial'
        
        invoice.save()


