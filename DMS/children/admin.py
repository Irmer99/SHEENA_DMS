from django.contrib import admin
from .models import Parent, Child, Enrollment


# Register Parent model
@admin.register(Parent)
class ParentAdmin(admin.ModelAdmin):
    """
    Admin interface for Parent model
    """
    list_display = ['full_name', 'user', 'phone', 'created_at']
    search_fields = ['first_name', 'last_name', 'phone', 'user__email']
    list_filter = ['created_at']
    
    fieldsets = (
        ('User Account', {
            'fields': ('user',)
        }),
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'phone', 'address')
        }),
        ('Emergency Contact', {
            'fields': ('emergency_contact_name', 'emergency_contact_phone')
        }),
    )


# Register Child model
@admin.register(Child)
class ChildAdmin(admin.ModelAdmin):
    """
    Admin interface for Child model
    """
    list_display = ['full_name', 'registration_number', 'date_of_birth', 'age', 'gender', 'is_active']
    search_fields = ['first_name', 'last_name', 'registration_number']
    list_filter = ['gender', 'is_active', 'created_at']
    readonly_fields = ['registration_number', 'created_at', 'updated_at']  # Don't let admin edit these
    filter_horizontal = ['parents']  # Better UI for selecting multiple parents
    
    fieldsets = (
        ('Registration', {
            'fields': ('registration_number',)  # Read-only, auto-generated
        }),
        ('Basic Information', {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'photo')
        }),
        ('Parents/Guardians', {
            'fields': ('parents',)
        }),
        ('Medical Information', {
            'fields': ('medical_info',),
            'description': 'Only editable by staff and admin'
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)  # Hidden by default
        }),
    )


# Register Enrollment model
@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    """
    Admin interface for Enrollment model
    """
    list_display = ['child', 'class_room', 'enrollment_date', 'status', 'created_at']
    search_fields = ['child__first_name', 'child__last_name', 'child__registration_number']
    list_filter = ['class_room', 'status', 'enrollment_date']
    
    fieldsets = (
        ('Child', {
            'fields': ('child',)
        }),
        ('Enrollment Details', {
            'fields': ('enrollment_date', 'class_room', 'status')
        }),
    )