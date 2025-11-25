from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from .models import Report
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
    # List recent reports for index view
    qs = Report.objects.select_related('author').all()
    return render(request, 'reports/indexForReports.html', {'reports_list': qs})

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


@require_POST
def toggle_reaction(request):
    """API endpoint to toggle/create reactions for a report.

    Expects JSON body: {"report_id": "<uuid>", "type": "agree"}
    Behavior:
    - If the user is not authenticated or is a guest account (profile.is_guest),
      return 403 with code 'guest_restriction' so frontend can open OTP modal.
    - Otherwise toggle or create the Reaction and return updated counts per type.
    """
    import json
    from django.shortcuts import get_object_or_404
    from django.http import HttpResponseBadRequest
    from .models import Reaction

    try:
        data = json.loads(request.body.decode('utf-8'))
    except Exception:
        return HttpResponseBadRequest('Invalid payload')

    report_id = data.get('report_id')
    rtype = data.get('type')
    if not report_id or not rtype:
        return HttpResponseBadRequest('Missing report_id or type')

    # Gatekeeper: deny guests
    user = request.user
    if not user.is_authenticated:
        return JsonResponse({'code': 'guest_restriction', 'message': 'Please verify to interact'}, status=403)

    # If profile exists and is_guest True -> treat as guest
    profile = getattr(user, 'profile', None)
    if profile and getattr(profile, 'is_guest', False):
        return JsonResponse({'code': 'guest_restriction', 'message': 'Please verify to interact'}, status=403)

    report = get_object_or_404(Report, pk=report_id)

    try:
        existing = Reaction.objects.filter(user=user, report=report).first()
        if existing:
            if existing.type == rtype:
                # Toggle off
                existing.delete()
            else:
                existing.type = rtype
                existing.save()
        else:
            Reaction.objects.create(user=user, report=report, type=rtype)

        # Return updated counts
        counts = {
            'agree': report.agree_count,
            'support': report.support_count,
            'sad': report.sad_count,
            'shock': report.shock_count,
            'confused': report.confused_count,
        }

        return JsonResponse({'status': 'success', 'counts': counts})

    except Exception as e:
        print('Reaction error:', e)
        return JsonResponse({'status': 'error', 'message': 'Unable to process reaction'}, status=500)