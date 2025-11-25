import random
import string
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from .models import Profile, OTPRequest
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.core.mail import EmailMultiAlternatives

# Make sure this list matches the file names in static/account/img/
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
    user.save()
    # A Profile may be created by a post_save signal. Use get_or_create to
    # avoid IntegrityError from duplicate creation.
    try:
        profile, created = Profile.objects.get_or_create(user=user)
        profile.is_guest = True
        profile.avatar_animal = animal
        profile.save()
    except Exception:
        # fallback: try to update if profile exists
        try:
            p = user.profile
            p.is_guest = True
            p.avatar_animal = animal
            p.save()
        except Exception:
            pass

    return user

def send_otp_email(email_tujuan):
    """
    Generate OTP, Simpan ke DB, dan Kirim Email HTML Cantik.
    """
    # 1. Generate Kode 6 Digit
    otp_code = ''.join(random.choices(string.digits, k=6))
    
    # 2. Simpan ke Database
    # Hapus OTP lama milik email ini (Cleanup) agar tidak numpuk
    OTPRequest.objects.filter(email=email_tujuan).delete()
    
    # Buat OTP baru (created_at otomatis terisi oleh Django)
    OTPRequest.objects.create(email=email_tujuan, otp_code=otp_code)
    
    # 3. Siapkan Email
    subject = '🔐 Kode OTP Verifikasi COLSP'
    from_email = settings.DEFAULT_FROM_EMAIL
    to = [email_tujuan]
    
    # Context data untuk dikirim ke template HTML
    context = {
        'otp_code': otp_code
    }
    
    # 4. Render Template
    # Pastikan file 'templates/account/email/otp_email.html' sudah dibuat
    html_content = render_to_string('account/email/otp_email.html', context)
    
    # Buat versi Text Only (untuk fallback)
    text_content = strip_tags(html_content) 
    
    # 5. Buat Objek Email dan Kirim
    msg = EmailMultiAlternatives(subject, text_content, from_email, to)
    msg.attach_alternative(html_content, "text/html") # Tempelkan versi HTML
    
    try:
        msg.send()
        return True
    except Exception as e:
        print(f"🔥 Gagal mengirim OTP: {e}")
        return False