import json
import os
from django.core.management.base import BaseCommand
from chatbot_faq.models import KnowledgeChunk
from django.conf import settings

class Command(BaseCommand):
    help = 'Import data dari file JSON ke Knowledge Base RAG'

    def add_arguments(self, parser):
        # Biar bisa ketik: python manage.py import_knowledge nama_file.json
        parser.add_argument('filename', type=str, help='Path ke file JSON hasil scraping')

    def handle(self, *args, **kwargs):
        filename = kwargs['filename']
        
        # Cek file ada atau nggak
        if not os.path.exists(filename):
            self.stdout.write(self.style.ERROR(f'File "{filename}" tidak ditemukan!'))
            return

        # Buka file JSON
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)

        total = len(data)
        self.stdout.write(self.style.SUCCESS(f'Mulai mengimpor {total} data... (Mohon tunggu, proses embedding butuh waktu)'))

        count = 0
        for item in data:
            count += 1
            # Ambil data dari JSON
            cat = item.get('category', 'umum')
            q = item.get('question') # Bisa null
            a = item.get('answer')

            if not a:
                self.stdout.write(self.style.WARNING(f'Skip data ke-{count}: Jawaban kosong.'))
                continue

            # Cek duplikat biar gak double (Optional)
            if KnowledgeChunk.objects.filter(answer=a).exists():
                self.stdout.write(f'Data ke-{count} sudah ada, skip.')
                continue

            # SIMPAN KE DB
            # Saat .create() dipanggil, method .save() di models.py akan jalan
            # Otomatis nembak ke Hugging Face -> dapet Vector -> Simpan.
            try:
                KnowledgeChunk.objects.create(
                    category=cat,
                    question=q,
                    answer=a
                )
                self.stdout.write(f'[{count}/{total}] Berhasil: {q if q else a[:30]}...')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Gagal import data ke-{count}: {e}'))

        self.stdout.write(self.style.SUCCESS(f'SELESAI! Berhasil mengimpor {count} data.'))