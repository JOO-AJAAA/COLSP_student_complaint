import requests
import time
from django.conf import settings

# --- KONFIGURASI FINAL ---

# 1. LLM: Qwen 2.5 (Sangat Pintar & Logis)
HF_CHAT_URL = "https://router.huggingface.co/v1/chat/completions"
# Kita pakai model 72B (paling pintar) atau 7B (lebih cepat)
HF_MODEL_ID = "Qwen/Qwen2.5-72B-Instruct"

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
                wait = response.json().get('estimated_time', 10)
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

# --- FUNGSI CHAT BARU (QWEN) ---
def generate_response_huggingface(prompt):
    """
    Menggunakan Endpoint Chat Completions (OpenAI Style).
    Lebih stabil dan pintar.
    """
    
    # Payload standar OpenAI/Qwen
    payload = {
        "model": HF_MODEL_ID,
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "max_tokens": 512,
        "temperature": 0.7,
        "stream": False # Matikan stream biar bisa disimpan ke DB
    }

    for attempt in range(3):
        try:
            response = requests.post(HF_CHAT_URL, headers=headers, json=payload, timeout=60)
            
            if response.status_code == 200:
                result = response.json()
                # Ambil text dari struktur JSON OpenAI
                return result['choices'][0]['message']['content'].strip()
            
            elif response.status_code == 503: # Loading
                continue
            
            else:
                print(f"❌ Qwen Error {response.status_code}: {response.text}")
                return f"Maaf, server AI sedang sibuk ({response.status_code})."

        except Exception as e:
            print(f"⚠️ Qwen Connection Error: {e}")
            
    return "Maaf, Qwen sedang tidak bisa dihubungi."