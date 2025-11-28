import os
import re
import pypdf
from docx import Document
from django.core.management.base import BaseCommand
from chatbot_faq.models import KnowledgeChunk
from django.conf import settings

class Command(BaseCommand):
    help = 'Pipeline: Baca PDF/DOCX -> Bersihkan -> Chunk -> Embed -> Simpan'

    def add_arguments(self, parser):
        # Opsi kategori (default: umum)
        parser.add_argument('--category', type=str, default='umum', help='Kategori materi')

    def clean_text(self, text):
        """
        Fungsi 'Laundry' untuk membersihkan teks kotor dari PDF.
        """
        # 1. Hapus Nomor Halaman (Contoh: "Halaman 12", "Page 1 of 10", atau angka sendirian di baris)
        # Regex ini mencari angka di awal/akhir baris yang sendirian
        text = re.sub(r'^\d+\s*$', '', text, flags=re.MULTILINE) 
        text = re.sub(r'^\s*Page\s+\d+.*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        # 2. Hapus Header/Footer berulang (Biasanya pendek dan di awal/akhir)
        # Hapus baris yang kurang dari 5 huruf (biasanya sampah scan)
        lines = []
        for line in text.split('\n'):
            if len(line.strip()) > 5: 
                lines.append(line.strip())
        
        # 3. Gabungkan kembali
        clean_text = '\n'.join(lines)
        
        # 4. Hapus spasi berlebih (Multiple spaces -> single space)
        clean_text = re.sub(r'\s+', ' ', clean_text)
        
        return clean_text

    def extract_from_pdf(self, filepath):
        text_content = ""
        try:
            reader = pypdf.PdfReader(filepath)
            for page in reader.pages:
                text_content += page.extract_text() + "\n\n" # Tambah jarak antar halaman
        except Exception as e:
            print(f"❌ Error PDF {filepath}: {e}")
        return text_content

    def extract_from_docx(self, filepath):
        text_content = ""
        try:
            doc = Document(filepath)
            for para in doc.paragraphs:
                text_content += para.text + "\n\n"
        except Exception as e:
            print(f"❌ Error DOCX {filepath}: {e}")
        return text_content

    def handle(self, *args, **kwargs):
        category = kwargs['category']
        
        # 1. SCAN FOLDER INPUT
        input_dir = os.path.join(settings.BASE_DIR, '_PIPELINE_INPUT')
        
        if not os.path.exists(input_dir):
            os.makedirs(input_dir)
            self.stdout.write(self.style.WARNING(f"Folder '{input_dir}' baru dibuat. Silakan masukkan file ke sana."))
            return

        files = [f for f in os.listdir(input_dir) if f.endswith(('.pdf', '.docx', '.txt'))]
        
        if not files:
            self.stdout.write(self.style.WARNING("Folder kosong. Masukkan file .pdf / .docx dulu."))
            return

        self.stdout.write(self.style.SUCCESS(f"Mulai memproses {len(files)} file..."))

        # 2. LOOP SETIAP FILE
        for filename in files:
            filepath = os.path.join(input_dir, filename)
            self.stdout.write(f"\n📄 Processing: {filename}...")
            
            # A. Ekstraksi Teks Mentah
            raw_text = ""
            if filename.endswith('.pdf'):
                raw_text = self.extract_from_pdf(filepath)
            elif filename.endswith('.docx'):
                raw_text = self.extract_from_docx(filepath)
            elif filename.endswith('.txt'):
                with open(filepath, 'r', encoding='utf-8') as f:
                    raw_text = f.read()

            # B. Pembersihan (Laundry)
            cleaned_text = self.clean_text(raw_text)

            # C. Chunking (Potong Kue)
            # Kita potong per 500 karakter atau per kalimat jika ada titik.
            # Strategi simpel: Split by ". " (Titik Spasi) lalu gabung sampai panjang cukup.
            
            # Cara simpel & efektif: Split per 2-3 kalimat (approx 300-500 chars)
            sentences = cleaned_text.split('. ')
            current_chunk = ""
            chunks_to_save = []
            
            for sentence in sentences:
                current_chunk += sentence + ". "
                if len(current_chunk) > 400: # Jika sudah cukup panjang
                    chunks_to_save.append(current_chunk)
                    current_chunk = ""
            
            if current_chunk: # Sisa potongan terakhir
                chunks_to_save.append(current_chunk)

            # D. Simpan ke DB (Otomatis Embed di models.py)
            saved_count = 0
            for chunk_text in chunks_to_save:
                if len(chunk_text) < 20: continue # Skip sampah pendek
                
                # Cek duplikat
                if not KnowledgeChunk.objects.filter(answer=chunk_text).exists():
                    KnowledgeChunk.objects.create(
                        category=category,
                        question=None, # Biarkan kosong (Materi Narasi)
                        answer=chunk_text
                    )
                    saved_count += 1
            
            self.stdout.write(self.style.SUCCESS(f"   ✅ Tersimpan {saved_count} chunks dari {filename}"))

        self.stdout.write(self.style.SUCCESS("\n🎉 SEMUA FILE SELESAI DIPROSES!"))