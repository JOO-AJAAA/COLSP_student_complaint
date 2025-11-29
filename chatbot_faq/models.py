from django.db import models
from django.contrib.auth.models import User
from pgvector.django import VectorField,HnswIndex
# Import fungsi dari utils di bawah
from .utils import get_embedding 

# 1. KNOWLEDGE BASE (Hybrid Structure)
class KnowledgeChunk(models.Model):
    # 1. DEFINISI PILIHAN KATEGORI
    CATEGORY_CHOICES = [
        ('akademik', 'Akademik'),
        ('keuangan', 'Keuangan / UKT'),
        ('fasilitas', 'Fasilitas'),
        ('kemahasiswaan', 'Kemahasiswaan'),
        ('umum', 'Umum/Lainnya'),
        ('santai', 'Santai / Lelucon'),
        ('aplikasi', 'Seputar Aplikasi COLSP / Cara Pakai'),
        ('beasiswa', 'Beasiswa dan Bantuan Dana'),
        ('kebijakan', 'Kebijakan Kampus dan Peraturan'),
    ]
    
    # 2. FIELD KATEGORI (DROPDOWN ADA DI SINI)
    category = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES,  # <--- CHOICES PINDAH KESINI
        default='umum'
    )

    # 3. FIELD PERTANYAAN (TEKS BIASA)
    # Hapus parameter 'choices' dari sini!
    question = models.CharField(
        max_length=500, 
        blank=True, 
        null=True, 
        help_text="Isi pertanyaan jika ini Q&A. Kosongkan jika materi narasi."
    )
    
    # 4. FIELD JAWABAN/MATERI
    answer = models.TextField(help_text="Jawaban atau Materi Lengkap.")
    
    # 5. VECTOR FIELD
    embedding = VectorField(dimensions=1024, null=True, blank=True)

    class Meta:
        indexes = [
            # Tambahkan Index HNSW untuk kolom embedding
            HnswIndex(
                name='knowledge_chunk_vec_index',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops'] # Optimasi untuk Cosine Similarity
            )
        ]
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # Logika Embed (Tetap Sama)
        if self.question:
            text_to_embed = f"Pertanyaan: {self.question}\nJawaban: {self.answer}"
        else:
            text_to_embed = self.answer
            
        vector_result = get_embedding(text_to_embed)
        if vector_result:
            self.embedding = vector_result
            
        super().save(*args, **kwargs)

    def __str__(self):
        # Biar di list admin kelihatan kategorinya
        label = self.get_category_display()
        if self.question:
            return f"[{label}] Q: {self.question}"
        return f"[{label}] Materi: {self.answer[:50]}..."

# 2. CHAT HISTORY (Sudah Oke)
class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_history")
    user_message = models.TextField()
    ai_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']