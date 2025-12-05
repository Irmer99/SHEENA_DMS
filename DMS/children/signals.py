from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.models import User
from .models import Parent

@receiver(post_save, sender=User)
def create_parent_profile(sender, instance, created, **kwargs):
    # Check if this is a NEW user (created=True)
    
    if created:
        # OPTIONAL: Check if their role is actually 'Parent' 
        # (Assuming you have a 'role' field on your User model)
        if getattr(instance, 'role', '') == 'Parent': 
            Parent.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_parent_profile(sender, instance, **kwargs):
    # Whenever the User is saved, save the Parent profile too
    # to ensure they stay in sync if data changes.
    try:
        instance.parent.save()
    except Parent.DoesNotExist:
        pass