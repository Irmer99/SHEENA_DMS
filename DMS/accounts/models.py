from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator

class User(AbstractUser):
    """
    Extended User model for authentication across all roles.
    Replaces Django's default User model.
    """
    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('parent', 'Parent'),
    ]
    
    role = models.CharField(
        max_length=10,
        choices=ROLE_CHOICES,
        help_text="User's role in the system"
    )
    phone = models.CharField(
        max_length=15,
        validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number')],
        help_text="Contact phone number"
    )
    email = models.EmailField(
        unique=True,
        help_text="Email address for login and notifications"
    )
    profile_picture = models.ImageField(
        upload_to='profiles/',
        blank=True,
        null=True
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Designates whether this user should be treated as active"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        
    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username



