from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from pgvector.django import L2Distance
from django.contrib.postgres.search import SearchVector 
from django.db.models import Q
from django.shortcuts import render
from .models import ChatMessage, KnowledgeChunk
from .utils import get_embedding, generate_response_huggingface

@login_required
@require_POST
def chat_api(request):
    user_query = request.POST.get('message')
    
    if not user_query:
        return JsonResponse({'error': 'Pesan kosong'}, status=400)

    # 1. HISTORY (Sama seperti sebelumnya)
    last_chats = ChatMessage.objects.filter(user=request.user).order_by('-timestamp')[:5]
    chat_history_text = ""
    if last_chats:
        for chat in reversed(last_chats):
            chat_history_text += f"User: {chat.user_message}\nAI: {chat.ai_response}\n"
    else:
        chat_history_text = "Belum ada riwayat percakapan."

    # ========================================================
    # 2. HYBRID RETRIEVAL (VECTOR + KEYWORD) 🚀
    # ========================================================
    
    final_chunks = []
    seen_ids = set() # Untuk mencegah data duplikat
    detected_categories = []

    # A. VECTOR SEARCH (Pencarian Makna)
    query_vector = get_embedding(user_query)
    if query_vector:
        vector_results = KnowledgeChunk.objects.order_by(
            L2Distance('embedding', query_vector)
        )[:3] # Ambil Top 3 dari makna
        
        for chunk in vector_results:
            if chunk.id not in seen_ids:
                final_chunks.append(chunk)
                seen_ids.add(chunk.id)
                detected_categories.append(chunk.category)

    # B. KEYWORD SEARCH (Pencarian Kata Kunci Persis)
    # Ini berguna kalau user nanya nama gedung spesifik atau kode unik
    keyword_results = KnowledgeChunk.objects.annotate(
        search=SearchVector('question', 'answer'),
    ).filter(
        Q(question__icontains=user_query) | Q(answer__icontains=user_query)
    )[:2] # Ambil Top 2 dari keyword

    for chunk in keyword_results:
        if chunk.id not in seen_ids:
            final_chunks.append(chunk)
            seen_ids.add(chunk.id)
            detected_categories.append(chunk.category)

    # C. Gabungkan Hasil
    context_text = ""

    if final_chunks:
        for chunk in final_chunks:
            context_text += f"- {chunk.answer} (Kategori: {chunk.category})\n"
    else:
        context_text = "Tidak ditemukan data spesifik di database kampus."

    # ========================================================
    # 3. DYNAMIC PERSONA (Sama seperti sebelumnya)
    # ========================================================
    if detected_categories:
        # Cari kategori terbanyak (modus)
        primary_category = max(set(detected_categories), key=detected_categories.count)
    else:
        primary_category = 'umum'
    # DEFINISI PERSONA (Dictionary)
    persona_map = {
        'santai': """
            PERAN: Kamu adalah teman mahasiswa yang asik, lucu, dan 'relate' banget sama kehidupan kampus.
            GAYA BICARA: Gunakan bahasa gaul (lo-gue), santai, boleh pakai emoji, dan sedikit bercanda.
            """,
            
        'aplikasi': """
            PERAN: Kamu adalah Pemandu Teknis / CS Resmi aplikasi COLSP.
            GAYA BICARA: Instruksional, jelas, to-the-point, dan sangat membantu.
            FOKUS: Arahkan user langkah demi langkah (Step-by-step).
            """,
            
        'keuangan': """
            PERAN: Kamu adalah Staf Bagian Keuangan yang teliti dan profesional.
            GAYA BICARA: Formal, sopan, tapi tegas mengenai angka, tanggal tenggat, dan denda.
            FOKUS: Pastikan informasi nominal uang dan tanggal akurat.
            """,
            
        'beasiswa': """
            PERAN: Kamu adalah Mentor Beasiswa yang suportif dan menyemangati.
            GAYA BICARA: Ramah, memotivasi, dan penuh harapan. Gunakan sapaan 'Sobat Mahasiswa'.
            FOKUS: Dorong mahasiswa untuk mendaftar dan tidak menyerah.
            """,
            
        'fasilitas': """
            PERAN: Kamu adalah Guide Kampus / Bagian Sarana Prasarana.
            GAYA BICARA: Informatif dan deskriptif.
            FOKUS: Jelaskan lokasi gedung atau fungsi fasilitas dengan detail agar user tidak tersesat.
            """,
            
        'kemahasiswaan': """
            PERAN: Kamu adalah Kakak Tingkat / Anggota BEM yang aktif.
            GAYA BICARA: Energik, seru, dan mengajak berpartisipasi.
            FOKUS: Kegiatan organisasi, lomba, dan pengembangan diri.
            """,
            
        'kebijakan': """
            PERAN: Kamu adalah Birokrat Kampus / Bagian Hukum.
            GAYA BICARA: Sangat formal, kaku, dan mengacu pada aturan tertulis.
            FOKUS: Kutip peraturan jika perlu. Jangan memberikan celah pelanggaran.
            """,
            
        'akademik': """
            PERAN: Kamu adalah Staf Akademik (Baak).
            GAYA BICARA: Administratif, rapi, dan prosedural.
            FOKUS: KRS, Nilai, Cuti, dan Jadwal Kuliah.
            """,
    }

    system_persona = persona_map.get(primary_category, """
        PERAN: Kamu adalah asisten kampus serba bisa yang profesional dan ramah.
        GAYA BICARA: Bahasa Indonesia baku yang sopan dan jelas.
    """)

    # 4. RAKIT PROMPT (Sama)
    final_prompt = f"""
    <|system|>
    {system_persona}
    
    INSTRUKSI: Jawab pertanyaan user berdasarkan KONTEKS DATA berikut. Jika tidak ada info yang relevan,
    katakan "Maaf, saya tidak memiliki informasi tersebut.". Tapi tetap berikan jawaban yang membantu dan ramah.
    Kalau memang tidak tahu, jangan jawab saja menggunakan apa yang kamu ingat dari luar konteks. tapi jangan jadikan
    itu sebagai sumber utama jawabanmu. Kasihan usernya nanti kalau kamu jawab tidak tahu, tapi jawab seenaknya dari ingatanmu sendiri. dan
    beri informasi yang relevan juga dari konteks pertanyaan dia. Jangan buat-buat informasi yang tidak ada di konteks. Gunakan bahasa yang sesuai dengan persona di atas.
    
    KONTEKS DATA KAMPUS:
    {context_text}
    
    RIWAYAT CHAT:
    {chat_history_text}
    <|end|>
    <|user|>
    {user_query}
    <|assistant|>
    """

    # 5. GENERATE (Sama)
    ai_answer = generate_response_huggingface(final_prompt)

    ChatMessage.objects.create(
        user=request.user,
        user_message=user_query,
        ai_response=ai_answer
    )

    return JsonResponse({'response': ai_answer})

@login_required
def chat_page(request):
    """
    Merender halaman antarmuka Chatbot YALQKA.
    """
    # Kita bisa kirim konteks tambahan jika perlu (misal nama user)
    context = {
        'bot_name': 'YALQKA',
        'welcome_message': f"Halo {request.user.first_name or request.user.username}! Saya YALQKA, asisten cerdas kampus. Ada yang bisa saya bantu?"
    }
    return render(request, 'chatbot_faq/chat_interface.html', context)