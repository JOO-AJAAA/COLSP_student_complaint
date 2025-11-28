from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
# Register your models here.
# 1. Definisi Action "Ban User"
@admin.action(description='🚫 Ban Selected Users (Matikan Akses)')
def ban_users(modeladmin, request, queryset):
    # Set is_active = False
    queryset.update(is_active=False)
    modeladmin.message_user(request, "User yang dipilih berhasil di-banned.")

# 2. Definisi Action "Unban User" (Siapa tau salah ban)
@admin.action(description='✅ Unban Selected Users (Pulihkan Akses)')
def unban_users(modeladmin, request, queryset):
    queryset.update(is_active=True)
    modeladmin.message_user(request, "Akses user berhasil dipulihkan.")

# 3. Extend UserAdmin Bawaan
class CustomUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'is_active', 'is_staff', 'last_login')
    list_filter = ('is_active', 'is_staff', 'date_joined')
    actions = [ban_users, unban_users] # Daftarkan action di sini

# 4. Re-Register
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)