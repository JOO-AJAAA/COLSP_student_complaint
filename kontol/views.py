from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from .utils import create_guest_account, send_otp_email
from .models import OTPRequest
from django.views.decorators.csrf import csrf_exempt

# Create your views here.
def guest_login_view(request):
    user = create_guest_account()
    # Login backend force (bypass password check)
    login(request, user, backend='django.contrib.auth.backends.ModelBackend')
    return redirect('home') # Ganti dengan nama url home Anda


@csrf_exempt
@require_POST
def guest_login_api(request):
    """API endpoint for JS to create a guest account and login.

    Returns JSON: {status:'success', username: 'panda_123', avatar: 'panda'}
    """
    try:
        user = create_guest_account()
        login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        avatar = getattr(user.profile, 'avatar_animal', '')
        return JsonResponse({'status': 'success', 'username': user.username, 'avatar': avatar})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# === 2. REQUEST OTP (AJAX) ===
@require_POST
def request_otp_view(request):
    email = request.POST.get('email')
    if not email:
        return JsonResponse({'status': 'error', 'message': 'Email wajib diisi'})
    
    try:
        send_otp_email(email)
        return JsonResponse({'status': 'success', 'message': 'OTP terkirim ke email Anda'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'Gagal mengirim email'})

# === 3. VERIFY OTP & SWITCH/PROMOTE ACCOUNT (AJAX) ===
# Logika Inti yang Anda Request ada di sini
@require_POST
def verify_otp_view(request):
    email = request.POST.get('email')
    otp_input = request.POST.get('otp')
    current_user = request.user # Ini User Guest (misal: panda_123)

    # A. Validasi OTP
    otp_obj = OTPRequest.objects.filter(email=email, otp_code=otp_input).first()
    
    if not otp_obj or not otp_obj.is_valid():
        return JsonResponse({'status': 'error', 'message': 'OTP Salah atau Kadaluarsa'})
    
    # Hapus OTP setelah dipakai
    otp_obj.delete()

    # B. Cek Apakah Email Sudah Terdaftar (Existing User)
    existing_user = User.objects.filter(email=email).first()

    if existing_user:
        # ==================================================
        # SKENARIO 1: EMAIL LAMA (SWITCH SESSION & DELETE GUEST)
        # ==================================================
        
        # PENTING: Jika Guest sudah buat laporan, kita harus memindahkan laporan itu 
        # ke existing_user SEBELUM menghapus guest, kalau tidak laporannya ikut terhapus.
        # Contoh:
        # Report.objects.filter(author=current_user).update(author=existing_user)
        
        # 1. Logout Guest
        logout(request)
        
        # 2. Hapus Akun Guest (Cleanup)
        if current_user.is_authenticated and current_user.profile.is_guest:
             current_user.delete() 

        # 3. Login Existing User
        login(request, existing_user, backend='django.contrib.auth.backends.ModelBackend')
        
        return JsonResponse({
            'status': 'success', 
            'action': 'switched', 
            'message': 'Berhasil masuk ke akun lama Anda!'
        })

    else:
        # ==================================================
        # SKENARIO 2: EMAIL BARU (PROMOTE GUEST)
        # ==================================================
        
        current_user.email = email
        current_user.profile.is_guest = False # Hapus status tamu
        current_user.profile.save()
        current_user.save()
        
        return JsonResponse({
            'status': 'success', 
            'action': 'promoted', 
            'message': 'Akun berhasil diverifikasi dan disimpan!'
        })