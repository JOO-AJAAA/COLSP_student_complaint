from django.contrib import admin
from .models import Report
# Register your models here.
@admin.action(description='✅ Set Status to Verified (Tampilkan di Web)')
def make_verified(modeladmin, request, queryset):
    queryset.update(status='verified')

@admin.action(description='❌ Set Status to Rejected (Tolak Laporan)')
def make_rejected(modeladmin, request, queryset):
    queryset.update(status='rejected')

class ReportAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'category', 'status', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('title', 'description', 'author__username')
    
    # Tombol Action Massal
    actions = [make_verified, make_rejected]
    
    # Biar admin bisa lihat foto attachment langsung (Opsional, butuh library tambahan biasanya)
    # Tapi defaultnya akan muncul link file.

admin.site.register(Report, ReportAdmin)