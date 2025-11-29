import requests
import time
from django.conf import settings
from google import genai
from google.genai import types
# --- KONFIGURASI FINAL ---

# --- KONFIGURASI GEMINI ---


# 2. EMBEDDING (GANTI KE MULTILINGUAL E5)
# Model ini support Bahasa Indonesia dan outputnya 768 dimensi (Aman untuk DB Anda)
HF_EMBED_URL = "https://router.huggingface.co/hf-inference/models/intfloat/multilingual-e5-large/pipeline/feature-extraction"

headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}

def get_embedding(text):
    """
    Mengubah teks Indo/Inggris menjadi vector 768 dimensi.
    """
    if not text: return None
    
    # PERBAIKAN PENTING UNTUK MODEL E5:
    # Model E5 bekerja paling baik jika kita kasih awalan "query:" atau "passage:"
    # Tapi untuk simplifikasi agar tidak error dimensi, kita kirim raw text dalam list.
    payload = {"inputs": [text]} 
    for attempt in range(3):
        try:
            response = requests.post(HF_EMBED_URL, headers=headers, json=payload, timeout=20)
            print(response.status_code)
            # SUKSES (200)
            if response.status_code == 200:
                data = response.json()
                
                # Normalisasi output (kadang list of list, kadang flat)
                if isinstance(data, list):
                    # Jika output [[0.1, 0.2...]] (Batch size 1)
                    if len(data) > 0 and isinstance(data[0], list):
                        return data[0]
                    # Jika output [0.1, 0.2...] (Flat)
                    return data
                
                print(f"⚠️ Format Vector Aneh: {str(data)[:50]}...")
                return None
            
            # MODEL LOADING (503)
            elif response.status_code == 503:
                wait = response.json().get('estimated_time', 5)
                print(f"🔄 Embedding API Loading... Tunggu {wait}s")
                time.sleep(wait)
                continue
            
            # ERROR LAIN
            else:
                print(f"❌ Embed API Error {response.status_code}: {response.text}")
                return None

        except Exception as e:
            print(f"⚠️ Embed Connection Error: {e}")
            return None
    return None

# --- FUNGSI CHAT BARU (GEMINI) ---
def generate_response_huggingface(prompt):
# Nama fungsinya biarkan 'generate_response_huggingface' 
    # supaya kita gak perlu ubah views.py, padahal isinya Gemini :D
    
    try:
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        client = genai.Client(api_key=api_key)
        respone = client.models.generate_content(
            model="gemini-2.5-pro",
            contents=prompt,
        )
        if respone.text:
            return respone.text.strip()
        else:
            return "Maaf, saya tidak dapat memberikan jawaban saat ini."
    except Exception as e:
        print(f"⚠️ Gemini API Error: {e,settings.GEMINI_API_KEY}")
        return "Maaf, terjadi kesalahan saat memproses permintaan Anda."