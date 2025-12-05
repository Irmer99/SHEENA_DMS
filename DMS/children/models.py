from django.db import models
from django.conf import settings
from datetime import date, datetime


class Parent(models.Model):
    """
    Parent/Guardian model - linked to a User account
    One parent can have multiple children (ManyToMany in Child model)
    """
    # Link to Django User account (one-to-one relationship)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='parent_profile',
        help_text="Linked user account for login"
    )
    
    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15, help_text="Primary contact number")
    address = models.TextField(help_text="Full residential address")
    
    # Emergency Contact (different from parent)
    emergency_contact_name = models.CharField(
        max_length=100,
        help_text="Emergency contact person name"
    )
    emergency_contact_phone = models.CharField(
        max_length=15,
        help_text="Emergency contact phone number"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'parents'
        ordering = ['last_name', 'first_name']
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def full_name(self):
        """Returns full name of parent"""
        return f"{self.first_name} {self.last_name}"


class Child(models.Model):
    """
    Child model - represents a child enrolled in the daycare
    Can have multiple parents (mother, father, guardians)
    """
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    # Registration number - auto-generated on save (e.g., REG-2024-001)
    registration_number = models.CharField(
        max_length=50,
        unique=True,
        blank=True,  # Allow blank so we can auto-generate
        help_text="Auto-generated registration number"
    )
    
    # Basic Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField(help_text="Child's date of birth")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    
    # Relationships - One child can have multiple parents
    parents = models.ManyToManyField(
        Parent,
        related_name='children',
        help_text="Select all parents/guardians for this child"
    )
    
    # Medical Information (editable only by staff/admin)
    medical_info = models.TextField(
        blank=True,
        help_text="Allergies, medical conditions, medications, etc."
    )
    
    # Photo
    photo = models.ImageField(
        upload_to='children/photos/',
        blank=True,
        null=True,
        help_text="Child's photo"
    )
    
    # Status
    is_active = models.BooleanField(
        default=True,
        help_text="Is the child currently enrolled?"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'children'
        ordering = ['last_name', 'first_name']
        verbose_name_plural = 'children'  # Correct plural form
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.registration_number})"
    
    @property
    def full_name(self):
        """Returns full name of child"""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def age(self):
        """Calculate current age in years"""
        today = date.today()
        age = today.year - self.date_of_birth.year
        # Adjust if birthday hasn't occurred yet this year
        if (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day):
            age -= 1
        return age
    
    def save(self, *args, **kwargs):
        """
        Override save method to auto-generate registration number
        Format: REG-YYYY-XXX (e.g., REG-2024-001, REG-2024-002)
        """
        if not self.registration_number:
            # Get current year
            year = datetime.now().year
            
            # Find last registration number for this year
            last_child = Child.objects.filter(
                registration_number__startswith=f'REG-{year}'
            ).order_by('-registration_number').first()
            
            if last_child:
                # Extract number from last registration (e.g., 001 from REG-2024-001)
                last_num = int(last_child.registration_number.split('-')[-1])
                new_num = last_num + 1
            else:
                # First child of the year
                new_num = 1
            
            # Generate new registration number with zero-padding (001, 002, etc.)
            self.registration_number = f'REG-{year}-{new_num:03d}'
        
        # Call parent save method
        super().save(*args, **kwargs)


class Enrollment(models.Model):
    """
    Enrollment model - tracks when a child enrolls and their classroom
    A child can have multiple enrollments over time (if they leave and return)
    """
    CLASS_CHOICES = [
        ('toddlers', 'Toddlers (1-2 years)'),
        ('preschool', 'Preschool (3-4 years)'),
        ('pre_k', 'Pre-K (4-5 years)'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('completed', 'Completed'),
    ]
    
    # Which child is being enrolled
    child = models.ForeignKey(
        Child,
        on_delete=models.CASCADE,
        related_name='enrollments',
        help_text="Child being enrolled"
    )
    
    # Enrollment details
    enrollment_date = models.DateField(
        help_text="Date child started/will start"
    )
    
    class_room = models.CharField(
        max_length=20,
        choices=CLASS_CHOICES,
        help_text="Age-appropriate classroom"
    )
    
    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='active',
        help_text="Current enrollment status"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'enrollments'
        ordering = ['-enrollment_date']  # Most recent first
    
    def __str__(self):
        return f"{self.child.full_name} - {self.get_class_room_display()} ({self.status})"