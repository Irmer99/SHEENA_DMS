from django import forms
from django.core.exceptions import ValidationError
from decimal import Decimal
from .models import Payment


class PaymentForm(forms.Form):
    """
    Form for parents to submit a payment against an invoice
    """
    amount = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        min_value=Decimal('0.01'),
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter amount to pay',
            'step': '0.01',
        }),
        label='Amount'
    )
    
    payment_method = forms.ChoiceField(
        choices=Payment.PAYMENT_METHOD_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Payment Method'
    )
    
    transaction_reference = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Cheque #, Mobile Money Code, Bank Reference',
        }),
        label='Transaction Reference (optional)'
    )
    
    notes = forms.CharField(
        max_length=500,
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Add any additional notes (optional)',
        }),
        label='Notes (optional)'
    )
    
    def clean_amount(self):
        """Validate that amount is positive"""
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise ValidationError("Amount must be greater than 0.")
        return amount
