# 🎓 COLSP - Campus Online Student Complaint

![License](https://img.shields.io/badge/license-GPLv3-blue.svg)
![Django](https://img.shields.io/badge/django-4.2-green.svg)
![Python](https://img.shields.io/badge/python-3.9+-blue.svg)
![PostgreSQL](https://img.shields.io/badge/database-Neon%20PostgreSQL-336791.svg)

**COLSP (College Speech)** is a modern AI-based platform for student aspirations and complaints. This application is designed to bridge communication between students and the campus in a transparent, fast, and interactive manner.

More than just a digital suggestion box, COLSP is equipped with **Intelligent Chatbot (RAG)**, **Sentiment Analysis**, and system **Guest Mode** unique.

---

## 🚀 Fitur Unggulan

### 🤖 AI-Powered Features
* **Chatbot "YALQKA" (RAG):** A virtual assistant that can answer questions about academics, finances, and campus facilities. It uses the Hybrid (Vector + Keyword) Retrieval-Augmented Generation (RAG) method so that its answers are accurate based on campus guidelines, not AI hallucinations..
* **Auto-Summary & Sentiment:** Every report that comes in is automatically summarized and analyzed for sentiment (Positive/Negative/Neutral) by Google Gemini..
* **Smart Filtering:** The automated system rejects reports containing profanity (Toxic) or online gambling promotions using the Hugging Face model..

### 👤 User Experience (UX)
* **Guest Mode (Lazy Login):** Students can report without registering! Get a unique anonymous identity (such as *Panda_1293*) and a cute animal avatar..
* **Guest Trap & Verification:** Guests can browse, but if they want to interact (Like/Reaction), the system will request email OTP verification to convert the guest account to a permanent one..
* **Instagram-like UI:** Responsive display with *Bottom Navigation* on mobile and *Sidebar* on desktop. Supports **Dark Mode** & **Light Mode**.

### 🛠️ Technical Highlights
* **Hybrid Search:** Combining *Semantic Search* (pgvector) and *Keyword Search* for maximum chatbot accuracy.
* **Dynamic Persona:** Chatbots can change their speaking style (Formal/Casual/Guiding) depending on the context of the user's question..
* **Security:** Rate limiting, CSRF protection, and strict session management for guest accounts.

---

## 🛠️ Teknologi yang Digunakan

* **Backend:** Django (Python)
* **Database:** PostgreSQL (via Neon Tech) + `pgvector` extension.
* **AI & ML:**
    * *LLM:* Google Gemini 2.5 Flash.
    * *Embedding:* `intfloat/multilingual-e5-large`.
    * *Library:* Sentence-Transformers.
* **Frontend:** HTML5, CSS3 (Custom Variables), JavaScript (Vanilla), Bootstrap 5.
* **Storage:** Cloudinary (for file/image management).
* **Deployment:** Vercel.

---

## 💻 Cara Instalasi (Local Development)

Follow these steps to run the project on your computer:

1.  **Clone Repository**
    ```bash
    git clone [https://github.com/JOO-AJAAA/COLSP_student_complaint](https://github.com/JOO-AJAAA/COLSP_student_complaint)
    cd colsp
    ```

2.  **Make Virtual Environment**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Untuk Mac/Linux
    venv\Scripts\activate     # Untuk Windows
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Konfigurasi Environment (.env)**
    Duplikasi file `.env.example` menjadi `.env`, lalu isi dengan API Key Anda (Google, HuggingFace, Database URL, dll).

5.  **Migrasi Database**
    ```bash
    python manage.py makemigrations
    python manage.py migrate
    ```

6.  **Jalankan Server**
    ```bash
    python manage.py runserver
    ```
    Buka `http://127.0.0.1:8000` di browser.

7. **Use link(in github have link web)**
    ```
    [https://github.com/JOO-AJAAA/COLSP_student_complaint](https://github.com/JOO-AJAAA/COLSP_student_complaint)
    ```

---

## 📝 Cerita Pengembangan (Developer Notes)

Proyek ini adalah hasil dari perjalanan *trial and error* yang panjang untuk menciptakan sistem pengaduan yang tidak membosankan.

* **Evolusi Database:** Initially used MySQL, but migrated to **PostgreSQL (Neon)** in the middle of the road to support the *Vector Search* feature (`pgvector`) for Chatbot RAG.
* **Tantangan AI:** One of the biggest obstacles is dealing with the Hugging Face API, which is often down (Error 503/410). The solution is to build a system. **Hybrid Embedding** (Local during development, API during production) but when deploying, the code on GitHub now uses the API.
* **Transformasi UI:** The initial design was very rigid. We completely revamped it with inspiration from Instagram and ChatGPT, removing many rigid "cards" in favor of a clean, full-width look, and adding smooth interactive animations.

---

## 📄 Lisensi

This project is distributed under the license **GNU GPLv3**. See the file `LICENSE` for more details.

Copyright (c) 2025 Yohanes Gerardus Haga Zai.