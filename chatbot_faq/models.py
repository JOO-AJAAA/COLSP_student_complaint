from django.db import models
from django.contrib.auth.models import User
from pgvector.django import VectorField
# Import fungsi dari utils di bawah
from .utils import get_embedding 

# 1. KNOWLEDGE BASE (Hybrid Structure)
class KnowledgeChunk(models.Model):
    # Kolom Pertanyaan (Opsional, diisi jika Q&A)
    question = models.CharField(max_length=500, blank=True, null=True, help_text="Isi pertanyaan jika ini Q&A. Kosongkan jika materi narasi.")
    
    # Kolom Jawaban/Materi (Wajib)
    answer = models.TextField(help_text="Jawaban atau Materi Lengkap.")
    
    # Kolom Vector (Disimpan otomatis)
    embedding = VectorField(dimensions=1024, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        # --- LOGIKA OTOMATIS (SISTEM CERDAS) ---
        # Gabungkan teks untuk di-embed
        if self.question:
            text_to_embed = f"Pertanyaan: {self.question}\nJawaban: {self.answer}"
        else:
            text_to_embed = self.answer
            
        # Panggil Utils untuk dapatkan angka vector
        # (Kita lakukan ini HANYA jika embedding belum ada atau teks berubah, 
        # tapi untuk simpelnya kita update terus tiap save)
        vector_result = get_embedding(text_to_embed)
        
        if vector_result:
            self.embedding = vector_result
            
        super().save(*args, **kwargs)

    def __str__(self):
        if self.question:
            return f"Q: {self.question}"
        return f"Materi: {self.answer[:50]}..."

# 2. CHAT HISTORY (Sudah Oke)
class ChatMessage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_history")
    user_message = models.TextField()
    ai_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['timestamp']