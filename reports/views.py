from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Report,Reaction
from .utils import (
    detect_gambling_probability, 
    detect_toxicity_probability, 
    detect_image_vulgarity, 
    extract_text_from_document
)
# Import Utility Baru
from .gemini_utils import generate_report_metadata
# Create your views here.

def reports(request):
    # 1. OPTIMASI DATABASE
    # Tambahkan 'prefetch_related' untuk 'reactions'. 
    # Ini mengambil semua reaksi sekaligus, jadi jauh lebih cepat.
    qs = Report.objects.select_related('author').prefetch_related('reactions').all()

    # Import SocialAccount dengan aman
    try:
        from allauth.socialaccount.models import SocialAccount
    except ImportError:
        SocialAccount = None

    reports_list = []
    
    for r in qs:
        # --- LOGIKA AVATAR (Kode Anda Sebelumnya) ---
        author_name = r.author.get_full_name() or r.author.username
        avatar_url = ''
        
        # Cek Profile (Guest)
        try:
            prof = getattr(r.author, 'profile', None)
            if prof and getattr(prof, 'avatar_animal', None):
                avatar_url = f"/static/account/img/{prof.avatar_animal}.svg"
        except Exception:
            pass

        # Cek Social Account (Google)
        if not avatar_url and SocialAccount:
            sa = SocialAccount.objects.filter(user=r.author).first()
            if sa:
                extra = getattr(sa, 'extra_data', {}) or {}
                avatar_url = extra.get('picture') or extra.get('avatar_url') or ''

        # Pasang atribut Avatar & Nama
        setattr(r, 'author_display_name', author_name)
        setattr(r, 'author_avatar_url', avatar_url)

        # --- LOGIKA MENGHITUNG REACTION (INI YANG KURANG) ---
        # Kita hitung manual menggunakan Python list comprehension
        # karena datanya sudah di-prefetch (ada di memori), ini sangat cepat.
        
        all_reactions = r.reactions.all() # Mengambil dari cache prefetch
        
        # Hitung jumlah per tipe
        agree_c = sum(1 for x in all_reactions if x.type == 'agree')
        support_c = sum(1 for x in all_reactions if x.type == 'support')
        sad_c = sum(1 for x in all_reactions if x.type == 'sad')
        shock_c = sum(1 for x in all_reactions if x.type == 'shock')
        confused_c = sum(1 for x in all_reactions if x.type == 'confused')

        # Tempelkan hasil hitungan ke objek report agar bisa dibaca template
        setattr(r, 'custom_agree_count', agree_c)
        setattr(r, 'custom_support_count', support_c)
        setattr(r, 'custom_sad_count', sad_c)
        setattr(r, 'custom_shock_count', shock_c)
        setattr(r, 'custom_confused_count', confused_c)
        # Masukkan ke list final
        reports_list.append(r)

    return render(request, 'reports/indexForReports.html', {'reports_list': reports_list})
# Import your Gemini wrapper here
# from .gemini_utils import generate_ai_summary 

@require_POST
def submit_report_api(request):
    """
    Handles report submission with a 3-layer filtering system.
    """
    # 1. Extract Data
    title = request.POST.get('title', '')
    description = request.POST.get('description', '')
    attachment = request.FILES.get('attachment') # This is the file object
    report_type = request.POST.get('type', '').strip()
    category = request.POST.get('category', '').strip()
    
    # Validasi Dasar
    if not description:
        return JsonResponse({'status': 'error', 'message': 'Deskripsi laporan wajib diisi.'}, status=400)

    # --- PHASE 1: FAIL-FAST (GAMBLING DETECTION) ---
    # Threshold: 30% (0.3). If detected, block immediately.
    
    gambling_score_title = detect_gambling_probability(title)
    gambling_score_desc = detect_gambling_probability(description)

    if gambling_score_title + gambling_score_desc > 0.25:
        return JsonResponse({
            'status': 'rejected',
            'reason': 'gambling',
            'message': 'System detected gambling or spam content. Submission rejected.'
        }, status=400)


    # --- PHASE 2: WEIGHTED PENALTY SYSTEM (TOXICITY & NSFW) ---
    # Weights: Title (20%), Description (40%), Attachment (40%)
    # Threshold: 44% (0.44)
    
    toxic_score_title = detect_toxicity_probability(title)
    toxic_score_desc = detect_toxicity_probability(description)
    
    # B. Hitung Skor Attachment (Dinamis)
    attachment_penalty_score = 0.0
    
    if attachment:
        content_type = attachment.content_type
        filename = attachment.name.lower()

        # KASUS 1: GAMBAR (Cek NSFW)
        if content_type.startswith('image/'):
            attachment_penalty_score = detect_image_vulgarity(attachment)
            
        # KASUS 2: DOKUMEN (Cek Toxic Text)
        elif filename.endswith(('.pdf', '.docx', '.txt')):
            # 1. Parsing isinya
            extracted_text = extract_text_from_document(attachment)
            
            # 2. Jika berhasil dapet teks, kirim ke HF Toxic Model
            if extracted_text:
                # Kita pakai model yg sama dengan title/desc
                attachment_penalty_score = detect_toxicity_probability(extracted_text)

    # C. Kalkulasi Rumus (Sesuai Request Anda)
    # Title (20%) + Desc (40%) + Attachment (40%)
    
    weighted_score = (toxic_score_title * 0.2) + \
                     (toxic_score_desc * 0.4) + \
                     (attachment_penalty_score * 0.4)

    # D. Final Decision (Ambang Batas 44%)
    if weighted_score > 0.44:
        return JsonResponse({
            'status': 'rejected',
            'reason': 'violation',
            'message': 'Laporan mengandung konten yang melanggar aturan (Teks kasar atau lampiran tidak pantas).'
        }, status=400)

# =========================================================
    # PHASE 3: AI PROCESSING (GEMINI)
    # =========================================================
    
    try:
        # Panggil Gemini Utility
        ai_data = generate_report_metadata(description, title)
        
        # Ambil hasil olahan AI
        final_title = ai_data.get('final_title', title)
        final_summary = ai_data.get('summary', '')
        final_sentiment = ai_data.get('sentiment', 'Netral')
        
        # =========================================================
        # PHASE 4: SAVE TO DATABASE
        # =========================================================
        
        new_report = Report.objects.create(
            author=request.user,  # User yang sedang login (Guest/Member)
            title=final_title,    # Judul (bisa dari User atau AI)
            description=description,
            type=report_type,
            category=category,
            attachment=attachment,
            
            # Field AI
            ai_summary=final_summary,
            sentiment_score=final_sentiment,
            
            status='pending' # Default status
        )
        
        return JsonResponse({
            'status': 'success', 
            'message': 'Laporan berhasil dikirim!',
            'redirect_url': '/reports/' # Opsional: jika mau redirect via JS
        })

    except Exception as e:
        print(f"Error Saving Report: {e}")
        return JsonResponse({'status': 'error', 'message': 'Terjadi kesalahan sistem saat menyimpan laporan.'}, status=500)


from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import Report, Reaction

# PERBAIKAN: Tambahkan parameter 'report_id' di sini agar cocok dengan URL
@login_required
@require_POST
def toggle_reaction_api(request, report_id): 
    
    # 1. GATEKEEPER: Cek Guest Account
    # Kita cek apakah user punya profile guest
    if hasattr(request.user, 'profile') and request.user.profile.is_guest:
        return JsonResponse({
            'code': 'guest_restriction', 
            'message': 'Please verify to interact'
        }, status=403)

    # 2. Ambil Data dari URL dan POST
    # report_id sudah didapat dari parameter fungsi (dari URL)
    
    # Karena JS pakai URLSearchParams, data ada di request.POST, BUKAN json body
    rtype = request.POST.get('reaction_type') 
    
    if not rtype:
        return JsonResponse({'status': 'error', 'message': 'Missing reaction type'}, status=400)

    # 3. Ambil Report dari Database
    report = get_object_or_404(Report, pk=report_id)

    # 4. Logika Toggle (Simpan/Hapus/Update)
    try:
        existing = Reaction.objects.filter(user=request.user, report=report).first()
        
        if existing:
            if existing.type == rtype:
                # Jika tipe sama -> Hapus (Unlike)
                existing.delete()
            else:
                # Jika tipe beda -> Ganti
                existing.type = rtype
                existing.save()
        else:
            # Belum ada -> Buat baru
            Reaction.objects.create(user=request.user, report=report, type=rtype)

        # 5. Hitung Ulang Jumlah (Agar UI Update Realtime)
        # Kita hitung manual dari DB agar akurat
        # (Alternatif: Gunakan related_name jika sudah diset di models)
        
        # Ambil semua reaksi laporan ini
        reactions = report.reactions.all()
        
        counts = {
            'agree': reactions.filter(type='agree').count(),
            'support': reactions.filter(type='support').count(),
            'sad': reactions.filter(type='sad').count(),
            'shock': reactions.filter(type='shock').count(),
            'confused': reactions.filter(type='confused').count(),
        }
        
        # Hitung total
        total_reactions = reactions.count()

        return JsonResponse({
            'status': 'success', 
            'counts': counts,
            'total_reactions': total_reactions
        })

    except Exception as e:
        print(f"Reaction Error: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)