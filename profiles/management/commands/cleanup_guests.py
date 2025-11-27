from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta

class Command(BaseCommand):
    help = 'Menghapus akun Guest yang tidak aktif lebih dari 15 hari'

    def handle(self, *args, **kwargs):
        # Hitung tanggal batas (Hari ini - 15 hari)
        expiration_date = timezone.now() - timedelta(days=15)
        
        # Cari User yang:
        # 1. Punya profile Guest (is_guest=True)
        # 2. Login terakhir (last_login) lebih lama dari 15 hari lalu
        # 3. Atau akun dibuat (date_joined) lebih lama dari 15 hari (jika gapernah login ulang)
        
        guests_to_delete = User.objects.filter(
            profile__is_guest=True,
            date_joined__lt=expiration_date
        )
        
        count = guests_to_delete.count()
        
        if count > 0:
            # Hapus massal
            guests_to_delete.delete()
            self.stdout.write(self.style.SUCCESS(f'✅ Berhasil menghapus {count} akun guest kadaluarsa.'))
        else:
            self.stdout.write(self.style.WARNING('🧹 Tidak ada akun guest yang perlu dihapus hari ini.'))