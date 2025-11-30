import requests
import time
from django.conf import settings
from google import genai
from google.genai import types
from sentence_transformers import SentenceTransformer

# --- KONFIGURASI FINAL ---

# --- KONFIGURASI GEMINI ---
# Configure Google Search tool correctly
# 2. EMBEDDING (GANTI KE MULTILINGUAL E5)
# Model ini support Bahasa Indonesia dan outputnya 768 dimensi (Aman untuk DB Anda)
MODEL_NAME = "intfloat/multilingual-e5-large"
HF_EMBED_URL = f"https://router.huggingface.co/hf-inference/models/{MODEL_NAME}/"

local_embedder = None
if getattr(settings, 'USE_LOCAL_EMBEDDING', False):
    # print(f"🖥️  Mode Development: Loading Model '{MODEL_NAME}' ke RAM Laptop...")
    # try:
    #     
        # Download otomatis saat pertama kali jalan (~2GB)
    local_embedder = SentenceTransformer(MODEL_NAME)
    #     print("✅ Model Lokal Siap!")
    # except ImportError:
    #     print("❌ Library 'sentence-transformers' belum diinstall! Fallback ke API.")
    #     local_embedder = None

headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}

def get_embedding(text):
    """
    Mengubah teks Indo/Inggris menjadi vector 768 dimensi.
    """
    if not text: return None
    
    # PERBAIKAN PENTING UNTUK MODEL E5:
    if local_embedder:
        try:
            # Perbaikan format E5: Tambahkan 'query: ' atau 'passage: '
            # Tapi untuk simpel, raw text dulu gpp.
            vector = local_embedder.encode(text, normalize_embeddings=True)
            return vector.tolist() # Ubah numpy array ke list biasa
        except Exception as e:
            print(f"❌ Local Embed Error: {e}")
            return None

    # JALUR 2: API (Production)
    else:
        payload = {"inputs": [text]} 
        for attempt in range(3):
            try:
                response = requests.post(HF_EMBED_URL, headers=headers, json=payload, timeout=20)
                
                if response.status_code == 200:
                    data = response.json()
                    if isinstance(data, list):
                        if len(data) > 0 and isinstance(data[0], list): return data[0]
                    return data
                elif response.status_code == 503:
                    time.sleep(5)
                    continue
                else:
                    print(f"API Error {response.status_code}: {response.text}")
                    return None
            except Exception as e:
                print(f"Connection Error: {e}")
                
        return None

# --- FUNGSI CHAT BARU (GEMINI) ---
def generate_response_huggingface(prompt):
    # Nama fungsinya biarkan 'generate_response_huggingface' 
    # supaya kita gak perlu ubah views.py, padahal isinya Gemini :D
    
    try:
        api_key = getattr(settings, 'GEMINI_API_KEY', None)
        if not api_key:
            print("⚠️ GEMINI_API_KEY tidak ditemukan di settings!")
            return "Maaf, konfigurasi API tidak lengkap."
            
        client = genai.Client(api_key=api_key)
        
        # Generate content with Google Search tool enabled
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.7,
                top_p=0.95,
            )
        )
        
        # Access the response correctly
        if response and hasattr(response, 'text') and response.text:
            return response.text.strip()
        elif response and hasattr(response, 'candidates') and response.candidates:
            # Try to extract text from candidates
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                parts = candidate.content.parts
                if parts and hasattr(parts[0], 'text'):
                    return parts[0].text.strip()
        
        return "Maaf, saya tidak dapat memberikan jawaban saat ini."
        
    except Exception as e:
        print(f"⚠️ Gemini API Error: {e}")
        import traceback
        traceback.print_exc()
        return "Maaf, terjadi kesalahan saat memproses permintaan Anda."