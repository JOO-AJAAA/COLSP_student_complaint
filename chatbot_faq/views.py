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

    # C. Gabungkan Hasil
    context_text = ""
    is_santai_mode = False
    is_app_guide_mode = False 

    if final_chunks:
        for chunk in final_chunks:
            # Masukkan ke konteks
            context_text += f"- {chunk.answer} (Kategori: {chunk.category})\n"
            
            # Deteksi Persona
            if chunk.category == 'santai':
                is_santai_mode = True
            elif chunk.category == 'aplikasi':
                is_app_guide_mode = True
    else:
        context_text = "Tidak ditemukan data spesifik di database kampus."

    # ========================================================
    # 3. DYNAMIC PERSONA (Sama seperti sebelumnya)
    # ========================================================
    if is_app_guide_mode:
        system_persona = """
        Kamu adalah Pemandu Resmi aplikasi COLSP. 
        Jelaskan fitur website ini dengan langkah-langkah yang jelas.
        """
    elif is_santai_mode:
        system_persona = """
        Kamu adalah teman mahasiswa yang asik dan lucu. 
        Gunakan bahasa gaul (lo-gue) tapi tetap sopan.
        """
    else:
        system_persona = """
        Kamu adalah asisten akademik kampus yang profesional.
        Gunakan Bahasa Indonesia yang baku.
        """

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