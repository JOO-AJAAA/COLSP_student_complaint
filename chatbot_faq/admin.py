from django.contrib import admin
from .models import KnowledgeChunk, ChatMessage
# Register your models here.

@admin.register(KnowledgeChunk)
class KnowledgeChunkAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'created_at')
    search_fields = ('question', 'answer')
    # Sembunyikan kolom embedding karena itu urusan mesin
    exclude = ('embedding',) 

admin.site.register(ChatMessage) # Opsional, buat pantau chat
