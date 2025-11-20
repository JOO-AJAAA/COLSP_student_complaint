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

    def __str__(self):
        return self.user.username

# 2. Model untuk menyimpan Kode OTP Sementara
class OTPRequest(models.Model):
    # Kita simpan email tujuan, bukan User, karena User-nya mungkin belum ada (atau Guest)
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    
    # OTP valid selama 5 menit
    def is_valid(self):
        return self.created_at >= timezone.now() - datetime.timedelta(minutes=5)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)