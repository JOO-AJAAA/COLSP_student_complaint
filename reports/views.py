from django.shortcuts import render,get_object_or_404
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.http import HttpResponse, Http404
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from .models import Report,Reaction
from .utils import (
    detect_gambling_probability, 
    detect_toxicity_probability, 
    detect_image_vulgarity, 
    extract_text_from_document
)
from profiles.utils import get_avatar_url
# Import Utility Baru
from .gemini_utils import generate_report_metadata
# Create your views here.
import os
import mimetypes

def reports(request):
    # 1. Query Dasar (Belum dieksekusi/Lazy)
    qs = Report.objects.select_related('author').prefetch_related('reactions').order_by('-created_at')

    # 2. SETUP PAGINATOR (6 Postingan per halaman)
    paginator = Paginator(qs, 6) 
    page_number = request.GET.get('page', 1) # Ambil nomor halaman dari URL (default 1)
    page_obj = paginator.get_page(page_number)

    # 3. IMPORT SOCIAL ACCOUNT (Sama seperti sebelumnya)
    try:
        from allauth.socialaccount.models import SocialAccount
    except ImportError:
        SocialAccount = None

    # 4. PROCESS HANYA 6 ITEM (Optimasi Kinerja)
    final_reports_list = []
    
    for r in page_obj: # Loop hanya berjalan 6 kali
        # --- A. Logic Avatar ---
        author_name = r.author.get_full_name() or r.author.username
        avatar_url = get_avatar_url(r.author)

        setattr(r, 'author_display_name', author_name)
        setattr(r, 'author_avatar_url', avatar_url)

        # --- B. Logic Reaction ---
        all_reactions = r.reactions.all()
        r.agree_count = sum(1 for x in all_reactions if x.type == 'agree')
        r.support_count = sum(1 for x in all_reactions if x.type == 'support')
        r.sad_count = sum(1 for x in all_reactions if x.type == 'sad')
        r.shock_count = sum(1 for x in all_reactions if x.type == 'shock')
        r.confused_count = sum(1 for x in all_reactions if x.type == 'confused')
        r.total_reactions_count = len(all_reactions)

        final_reports_list.append(r)

    # 5. CEK: APAKAH INI REQUEST SCROLLING (AJAX)?
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Render potongan HTML kartu saja (bukan seluruh halaman)
        html = render_to_string('reports/includes/report_list_chunk.html', {'reports_list': final_reports_list}, request=request)
        
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next() # Beritahu JS apakah masih ada halaman berikutnya
        })

    # 6. JIKA BUKAN AJAX (Halaman Pertama dibuka biasa)
    return render(request, 'reports/indexForReports.html', {
        'reports_list': final_reports_list,
        'has_next': page_obj.has_next() # Untuk inisialisasi JS
    })

def preview_file(request, report_id):
    report = get_object_or_404(Report, pk=report_id)
    
    if not report.attachment:
        raise Http404("No attachment found")

    file_path = report.attachment.path
    
    # Pastikan file ada di disk
    if not os.path.exists(file_path):
        raise Http404("File not found on server")

    # Deteksi Mime Type (PDF, Image, dll)
    content_type, encoding = mimetypes.guess_type(file_path)
    content_type = content_type or 'application/octet-stream'

    # Buka file
    with open(file_path, 'rb') as f:
        response = HttpResponse(f.read(), content_type=content_type)
    
    # KUNCI UTAMA: 'inline' berarti buka di browser, 'attachment' berarti download
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
    
    return response

@require_POST
def submit_report_api(request):
    """
    Handles report submission with a 3-layer filtering system.
    """

    # =========================================================
    # RATE LIMIT 3x / 5 MENIT (BERDASARKAN USER LOGIN)
    # =========================================================
    user_id = request.user.id if request.user.is_authenticated else request.META.get('REMOTE_ADDR')
    cache_key = f"submit_report_{user_id}"

    submit_count = cache.get(cache_key, 0)

    if submit_count >= 1:
        return JsonResponse({
            'status': 'rejected',
            'reason': 'rate_limit',
            'message': 'Sistem spam lagi tahap pengembangan. Untuk saat ini, mohon batasi pengiriman laporan menjadi 1 kali setiap 5 menit.'
        }, status=429)

    # -------------------------------
    # LANJUT KE LOGIKA KAMU ASLI
    # -------------------------------

    # 1. Extract Data
    title = request.POST.get('title', '')
    description = request.POST.get('description', '')
    attachment = request.FILES.get('attachment')
    report_type = request.POST.get('type', '').strip()
    category = request.POST.get('category', '').strip()

    # Validasi Dasar
    if not description:
        return JsonResponse({'status': 'error', 'message': 'Deskripsi laporan wajib diisi.'}, status=400)

    # =========================================================
    # PHASE 1: FAIL-FAST (GAMBLING DETECTION)
    # =========================================================

    gambling_score_title = detect_gambling_probability(title)
    gambling_score_desc = detect_gambling_probability(description)

    if gambling_score_title + gambling_score_desc > 0.25:
        return JsonResponse({
            'status': 'rejected',
            'reason': 'gambling',
            'message': 'System detected gambling or spam content. Submission rejected.'
        }, status=400)

    # =========================================================
    # PHASE 2: WEIGHTED PENALTY SYSTEM
    # =========================================================

    toxic_score_title = detect_toxicity_probability(title)
    toxic_score_desc = detect_toxicity_probability(description)

    attachment_penalty_score = 0.0

    if attachment:
        content_type = attachment.content_type
        filename = attachment.name.lower()

        if content_type.startswith('image/'):
            attachment_penalty_score = detect_image_vulgarity(attachment)

        elif filename.endswith(('.pdf', '.docx', '.txt')):
            extracted_text = extract_text_from_document(attachment)

            if extracted_text:
                attachment_penalty_score = detect_toxicity_probability(extracted_text)

    weighted_score = (toxic_score_title * 0.2) + \
                     (toxic_score_desc * 0.4) + \
                     (attachment_penalty_score * 0.4)

    if weighted_score > 0.42:
        return JsonResponse({
            'status': 'rejected',
            'reason': 'violation',
            'message': 'Laporan mengandung konten yang melanggar aturan.'
        }, status=400)

    # =========================================================
    # PHASE 3: AI PROCESSING
    # =========================================================

    try:
        ai_data = generate_report_metadata(description, title)

        final_title = ai_data.get('final_title', title)
        final_summary = ai_data.get('summary', '')
        final_sentiment = ai_data.get('sentiment', 'Netral')

        # =========================================================
        # PHASE 4: SAVE TO DATABASE
        # =========================================================

        new_report = Report.objects.create(
            author=request.user,
            title=final_title,
            description=description,
            type=report_type,
            category=category,
            attachment=attachment,
            ai_summary=final_summary,
            sentiment_score=final_sentiment,
            status='pending'
        )

        # =========================================================
        # UPDATE RATE LIMIT COUNTER (SETELAH BERHASIL SAVE)
        # =========================================================

        if submit_count == 0:
            cache.set(cache_key, 1, timeout=300)  # 5 menit
        else:
            cache.incr(cache_key)

        return JsonResponse({
            'status': 'success',
            'message': 'Laporan berhasil dikirim!',
            'redirect_url': '/reports/'
        })

    except Exception as e:
        print(f"Error Saving Report: {e}")
        return JsonResponse({
            'status': 'error',
            'message': 'Terjadi kesalahan sistem saat menyimpan laporan.'
        }, status=500)

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
                action = 'removed'
            else:
                # Jika tipe beda -> Ganti
                existing.type = rtype
                existing.save()
                action = 'updated'
        else:
            # Belum ada -> Buat baru
            Reaction.objects.create(user=request.user, report=report, type=rtype)
            action = 'created'

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
            'action': action,
            'counts': counts,
            'total_reactions': total_reactions
        })

    except Exception as e:
        print(f"Reaction Error: {e}")
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)