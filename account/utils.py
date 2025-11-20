import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from .models import Profile, OTPRequest

# Pastikan list ini sesuai dengan nama file di static/account/img/
ANIMALS = ['kucing', 'panda', 'rubah', 'koala', 'bebek']

def create_guest_account():
    """Membuat user guest unik: rubah_839120"""
    while True:
        animal = random.choice(ANIMALS)
        # Generate 6 digit angka
        number = ''.join(random.choices(string.digits, k=6))
        username = f"{animal}_{number}"
        
        if not User.objects.filter(username=username).exists():
            break
            
    # Buat User Guest
    user = User.objects.create_user(username=username)
    user.set_unusable_password() # Tidak butuh password
    
    # Buat Profile
    Profile.objects.create(user=user, is_guest=True, avatar_animal=animal)
    
    return user

def send_otp_email(email):
    """Generate OTP, simpan di DB, dan kirim email"""
    # Generate 6 digit angka
    otp = ''.join(random.choices(string.digits, k=6))
    
    # Hapus OTP lama untuk email ini (biar gak numpuk)
    OTPRequest.objects.filter(email=email).delete()
    
    # Simpan baru
    OTPRequest.objects.create(email=email, otp_code=otp)
    
    # Kirim Email (Pastikan setting EMAIL_HOST di settings.py sudah benar)
    send_mail(
        'Kode Verifikasi COLSP',
        f'Kode OTP Anda adalah: {otp}. Berlaku 5 menit.',
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )
    return True