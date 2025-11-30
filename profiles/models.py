from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
from django.db.models.signals import post_save
from django.dispatch import receiver

# Create your models here.
# 1. Profile untuk User (Menangani Guest & Avatar)
class Profile(models.Model): 
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    is_guest = models.BooleanField(default=False)
    avatar_animal = models.CharField(max_length=50, blank=True, null=True)
    avatar_image = models.ImageField(upload_to='profile_avatars/', blank=True, null=True)
    def __str__(self):
        return self.user.username

class OTPRequest(models.Model):
    # We save the destination email, not the User, because the User may not exist yet (or may be a Guest).
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # OTP valid for 5 minutes
    def is_valid(self):
        return self.created_at >= timezone.now() - datetime.timedelta(minutes=5)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)