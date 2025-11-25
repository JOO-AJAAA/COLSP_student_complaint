from google import genai
import json
from django.conf import settings
import os


# Konfigurasi API Key (Pastikan ada di .env Anda)
client = genai.Client(api_key=settings.GEMINI_API_KEY)
def generate_report_metadata(description, user_title=None):
    """
    Mengirim deskripsi laporan ke Gemini untuk dianalisis.
    Output: Dictionary {'summary': '...', 'sentiment': '...', 'suggested_title': '...'}
    """
    try:
        model = 'gemini-2.5-flash'
        
        # Prompt Engineering: Kita suruh Gemini jadi admin yang pintar
        prompt = f"""
        Anda adalah asisten admin kampus. Analisis laporan mahasiswa berikut:
        
        Laporan: "{description}"
        Judul User: "{user_title if user_title else 'KOSONG'}"

        Tugas Anda:
        1. Tentukan Sentimen (Positif/Negatif/Netral).
        2. Buat Ringkasan padat (maksimal 2 kalimat).
        3. Jika 'Judul User' adalah KOSONG atau sangat tidak jelas (kurang dari 3 kata), buatkan Judul yang profesional dan deskriptif. Jika Judul User sudah bagus, gunakan judul user tersebut.

        Keluarkan HANYA dalam format JSON:
        {{
            "sentiment": "Positif/Negatif/Netral",
            "summary": "Ringkasan anda...",
            "final_title": "Judul final..."
        }}
        """

        response = client.models.generate_content(
            model=model,
            contents=prompt,
        )
        
        # Bersihkan response (kadang Gemini kasih markdown ```json ... ```)
        clean_text = response.text.replace('```json', '').replace('```', '').strip()
        
        return json.loads(clean_text)

    except Exception as e:
        print(f"Gemini Error: {e}")
        # Fallback (Plan B jika AI Error/Kuota Habis)
        return {
            "sentiment": "Netral",
            "summary": description[:100] + "...", # Potong manual
            "final_title": user_title if user_title else "Laporan Tanpa Judul"
        }