from django.shortcuts import render,redirect
from django.http import JsonResponse
from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from .utils import create_guest_account, send_otp_email
from .models import OTPRequest
from reports.models import Report
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt

@login_required
def profile_view(request):
    user = request.user
    user_reports = Report.objects.filter(author=user).order_by('-created_at')
    total_reports = user_reports.count()
    total_impact = sum(r.total_upvotes for r in user_reports)
    context = {
        'user': user,
        'reports': user_reports,
        'stats': {
            'total_reports': total_reports,
            'total_impact': total_impact,
        }
    }
    return render(request, 'account/profile.html', context)



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
        # Ensure session is saved so the session cookie is set in response
        try:
            request.session.save()
        except Exception:
            pass
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
        ok = send_otp_email(email)
        if ok:
            return JsonResponse({'status': 'success', 'message': 'OTP terkirim ke email Anda'})
        else:
            return JsonResponse({'status': 'error', 'message': 'Gagal mengirim email. Periksa konfigurasi email server.'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': 'Gagal mengirim email'})

# === 3. VERIFY OTP & SWITCH/PROMOTE ACCOUNT (AJAX) ===
# Logika Inti yang Anda Request ada di sini
@require_POST
def verify_otp_view(request):
    # Debug: Print data yang masuk ke Terminal
    print("--- DEBUG VERIFY OTP ---")
    
    email = request.POST.get('email')
    otp_input = request.POST.get('otp')
    
    print(f"Email: {email}")
    print(f"OTP Input: {otp_input}")

    if not email or not otp_input:
        return JsonResponse({'status': 'error', 'message': 'Email dan OTP wajib diisi'}, status=400)

    # 1. Cek OTP di Database
    # Cari OTP yang cocok email & kodenya
    otp_obj = OTPRequest.objects.filter(email=email, otp_code=otp_input).first()
    
    if not otp_obj:
        print("GAGAL: OTP Salah atau Tidak Ditemukan di DB")
        return JsonResponse({'status': 'error', 'message': 'Kode OTP Salah!'}, status=400)
    
    # Cek expired (memanggil method model is_valid)
    if not otp_obj.is_valid():
        print("GAGAL: OTP Kadaluarsa")
        return JsonResponse({'status': 'error', 'message': 'Kode OTP Kadaluarsa'}, status=400)

    # Hapus OTP karena sudah dipakai
    otp_obj.delete()
    print("SUKSES: OTP Valid. Memproses User...")

    # 2. Proses User (Switching atau Promoting)
    try:
        current_user = request.user
        existing_user = User.objects.filter(email=email).first()

        if existing_user:
            # SKENARIO A: Email Lama (Switch Account)
            print(f"Switching ke user lama: {existing_user.username}")
            
            logout(request)
            # PENTING: Hapus guest user biar gak nyampah (Opsional)
            if current_user.is_authenticated and hasattr(current_user, 'profile') and current_user.profile.is_guest:
                 current_user.delete()
            
            login(request, existing_user, backend='django.contrib.auth.backends.ModelBackend')
            
        else:
            # SKENARIO B: Email Baru (Promote Guest)
            print(f"Promote guest: {current_user.username} ke email {email}")
            
            current_user.email = email
            # Pastikan profile ada sebelum akses
            if hasattr(current_user, 'profile'):
                current_user.profile.is_guest = False
                current_user.profile.save()
            current_user.save()

        return JsonResponse({'status': 'success', 'message': 'Verifikasi Berhasil!'})

    except Exception as e:
        print(f"ERROR SYSTEM: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)