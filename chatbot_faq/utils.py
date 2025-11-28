import requests
import time
from django.conf import settings

# --- KONFIGURASI FINAL ---

# 1. LLM (Tetap Zephyr) - Otak Chatbot
HF_LLM_URL = "https://router.huggingface.co/hf-inference/models/HuggingFaceH4/zephyr-7b-beta"

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
    print(headers)
    payload = {"inputs": [text]} 
    print(payload)
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

def generate_response_huggingface(prompt):
    """
    Generate response chat
    """
    # Prompt Template Zephyr
    formatted_prompt = f"<|system|>\nKamu adalah asisten kampus yang membantu menjawab pertanyaan mahasiswa dalam Bahasa Indonesia.<|end|>\n<|user|>\n{prompt}<|end|>\n<|assistant|>"

    payload = {
        "inputs": formatted_prompt,
        "parameters": {
            "max_new_tokens": 512, 
            "temperature": 0.7,
            "return_full_text": False
        }
    }

    for attempt in range(3):
        try:
            response = requests.post(HF_LLM_URL, headers=headers, json=payload, timeout=40)
            
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0 and 'generated_text' in result[0]:
                    return result[0]['generated_text'].strip()
                return str(result)
            
            elif response.status_code == 503:
                print(f"🔄 Chat API Loading...")
                time.sleep(5)
                continue
            
            else:
                print(f"❌ Chat API Error {response.status_code}: {response.text}")
                return f"Maaf, server AI sedang sibuk ({response.status_code})."

        except Exception as e:
            print(f"⚠️ Chat Connection Error: {e}")
            
    return "Maaf, tidak dapat terhubung ke otak AI."