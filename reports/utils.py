import requests
import pypdf
from django.conf import settings
from .api_config_urls import HF_API_URL_NSFW,HF_API_URL_SPAM, HF_API_URL_TOXIC
from docx import Document
from deep_translator import GoogleTranslator
from django.conf import settings

headers = {"Authorization": f"Bearer {settings.HUGGINGFACE_API_KEY}"}
print(headers)

def translate_to_english(text):
    """
    Helper: Translate ID -> EN untuk kebutuhan model Gambling.
    Maksimal 500 char biar cepat.
    """
    if not text: return ""
    try:
        # Cut the text so it doesn't take too long to translate.
        text_sample = text[:500] 
        translated = GoogleTranslator(source='auto', target='en').translate(text_sample)
        return translated
    except:
        return text # Fallback: return the original text if it fails

def detect_gambling_probability(text):
    """
    Returns a float (0.0 to 1.0) representing the probability of the text being spam/gambling.
    """
    if not text: return 0.0
    english_text = translate_to_english(text)
    response = requests.post(HF_API_URL_SPAM, headers=headers, json={"inputs": english_text})
    data = response.json()
    scoreGambling = data[0][1]['score']
    print(f"Gambling score {scoreGambling}")
    return scoreGambling

def detect_toxicity_probability(text):
    """
    Returns a float (0.0 to 1.0) representing how toxic the text is.
    """
    if not text: return 0.0
    english_text = translate_to_english(text)
    respone = requests.post(HF_API_URL_TOXIC, headers=headers, json={"inputs": english_text})
    data = respone.json()
    scoreToxic = data[0][0]['score']
    print(f"toxicty probabilty score {scoreToxic}")
    return scoreToxic

def detect_image_vulgarity(image_file):
    """
    Returns a float (0.0 to 1.0) representing NSFW probability.
    """
    if not image_file: return 0.0

    # Accept either a Django UploadedFile (InMemoryUploadedFile / TemporaryUploadedFile)
    # or a file path string. For uploaded files, use the file-like object's read()
    # and then reset the pointer so callers can still save the file.
    try:
        if hasattr(image_file, 'read'):
            # Django InMemoryUploadedFile or similar
            image_data = image_file.read()
            # reset pointer for later use
            try:
                image_file.seek(0)
            except Exception:
                pass
        else:
            # Treat as file path
            with open(image_file, 'rb') as f:
                image_data = f.read()

        if not image_data:
            return 0.0

        resp = requests.post(HF_API_URL_NSFW, headers={'Content-Type': 'application/octet-stream', **headers}, data=image_data, timeout=30)
        if resp.status_code != 200:
            print(f"HF NSFW API returned status {resp.status_code}: {resp.text[:500]}")
            return 0.0

        try:
            result = resp.json()
        except ValueError as e:
            print(f"Error decoding HF NSFW JSON: {e}; raw: {resp.text[:500]}")
            return 0.0

        # Result format can vary; try to extract a reasonable NSFW score.
        # If it's a list of labels, search for common NSFW labels.
        nsfw_score = 0.0
        if isinstance(result, list):
            for item in result:
                label = (item.get('label') or '').lower() if isinstance(item, dict) else ''
                score = float(item.get('score', 0.0)) if isinstance(item, dict) else 0.0
                if any(k in label for k in ('nsfw', 'sexual', 'porn', 'explicit')):
                    nsfw_score = max(nsfw_score, score)
        elif isinstance(result, dict):
            # Sometimes result is a dict of scores
            for k, v in result.items():
                if isinstance(v, (int, float)) and 'nsfw' in k.lower():
                    nsfw_score = max(nsfw_score, float(v))

        print(f"nsfw score {nsfw_score}")
        return nsfw_score

    except Exception as e:
        print(f"Unexpected error checking image: {e}")
        try:
            if hasattr(image_file, 'seek'):
                image_file.seek(0)
        except Exception:
            pass
        return 0.0

def extract_text_from_document(uploaded_file):
    """
    Mengekstrak teks dari file PDF, DOCX, atau TXT.
    Mengembalikan string (maksimal 1000 karakter untuk efisiensi API).
    """
    text_content = ""
    filename = uploaded_file.name.lower()

    try:
        # 1. Handle PDF
        if filename.endswith('.pdf'):
            reader = pypdf.PdfReader(uploaded_file)
            # Ambil maksimal 2 halaman pertama saja (Sampling)
            max_pages = min(len(reader.pages), 2) 
            for i in range(max_pages):
                page_text = reader.pages[i].extract_text()
                if page_text:
                    text_content += page_text + "\n"

        # 2. Handle DOCX
        elif filename.endswith('.docx'):
            doc = Document(uploaded_file)
            # Gabungkan semua paragraf
            text_content = "\n".join([p.text for p in doc.paragraphs])

        # 3. Handle TXT
        elif filename.endswith('.txt'):
            text_content = uploaded_file.read().decode('utf-8', errors='ignore')

        # PENTING: Reset pointer file agar bisa disimpan ke DB/Storage nantinya
        uploaded_file.seek(0)
        
        # TRUNCATE: Potong teks agar tidak overload API Hugging Face
        # 1000 
        return text_content[:1000] 

    except Exception as e:
        print(f"Error parsing document: {e}")
        uploaded_file.seek(0) # Tetap reset pointer meski error
        return ""