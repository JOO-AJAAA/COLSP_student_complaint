if (window.__colsp_base_js_loaded) {
  console.warn("base.js already loaded — skipping duplicate execution");
} else {
  window.__colsp_base_js_loaded = true;

  (function () {
    "use strict";

    // --- 1. CSRF Helper ---
    function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          if (cookie.substring(0, name.length + 1) === name + "=") {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }
    let csrftoken = getCookie("csrftoken");
    if (!csrftoken) {
      const meta = document.querySelector('meta[name="csrf-token"]');
      if (meta) csrftoken = meta.getAttribute("content");
    }

    // --- 2. Theme Logic ---
    const themeToggle = document.getElementById("themeToggle");
    const themeIcon = document.getElementById("themeIcon");
    const body = document.body;

    if (themeToggle) {
      themeToggle.addEventListener("click", () => {
        const currentTheme = body.getAttribute("data-theme");
        const newTheme = currentTheme === "dark" ? "light" : "dark";
        body.setAttribute("data-theme", newTheme);
        if (themeIcon) themeIcon.className = newTheme === "dark" ? "fas fa-moon" : "fas fa-sun";
        localStorage.setItem("theme", newTheme);
      });
    }

    const savedTheme = localStorage.getItem("theme") || "dark";
    body.setAttribute("data-theme", savedTheme);
    if (themeIcon) themeIcon.className = savedTheme === "dark" ? "fas fa-moon" : "fas fa-sun";

    // --- 3. File Input Logic ---
    const fileInput = document.getElementById("attachment");
    const fileLabel = document.querySelector(".file-upload-label span");

    if (fileInput && fileLabel) {
      fileInput.addEventListener("change", (e) => {
        const files = e.target.files;
        if (files.length > 0) {
          fileLabel.textContent =
            files.length === 1 ? files[0].name : `${files.length} files selected`;
        } else {
          fileLabel.textContent = "Click to upload files or drag and drop";
        }
      });
    }

    // --- 4. Report Submission Logic ---
    const reportForm = document.getElementById("reportForm");
    if (reportForm) {
      reportForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const submitBtn = e.target.querySelector(".btn-submit");

        // Prepare FormData
        const fd = new FormData();
        const reportTypeInput = document.querySelector('input[name="reportType"]:checked');
        if (reportTypeInput) fd.append("type", reportTypeInput.value);
        
        const cat = document.getElementById("category");
        if(cat) fd.append("category", cat.value);
        
        const tit = document.getElementById("title");
        if(tit) fd.append("title", tit.value);

        const desc = document.getElementById("description");
        if(desc) fd.append("description", desc.value);

        if (fileInput && fileInput.files && fileInput.files.length > 0) {
          fd.append("attachment", fileInput.files[0]);
        }

        // UI: loading state
        if(submitBtn) {
            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';
        }

        openReportModal();
        setReportModalStage("loading");

        fetch("/reports/api/submit/", {
          method: "POST",
          headers: {
            "X-CSRFToken": csrftoken,
            "X-Requested-With": "XMLHttpRequest",
          },
          body: fd,
        })
          .then(async (res) => {
            const data = await res.json().catch(() => ({}));
            
            // Restore button
            if(submitBtn) {
                 submitBtn.disabled = false;
                 submitBtn.innerHTML = "Submit Report";
            }

            if (res.status === 400) {
              setReportModalStage("error", { message: data.message || "Submission rejected." });
              return;
            }
            if (res.status === 429) {
              setReportModalStage("error", { message: data.message || "Too many requests. Please try again later." });
              return;
            }
            if (res.status === 500) {
              setReportModalStage("error", { message: data.message || "Server error." });
              return;
            }
            if (res.ok) {
              setReportModalStage("success", {
                message: data.message || "Report sent!",
                redirect: data.redirect_url,
              });
              setTimeout(() => {
                window.location.href = data.redirect_url || "/reports/";
              }, 1400);
              return;
            }
            setReportModalStage("error", { message: "Unexpected response." });
          })
          .catch((err) => {
            console.error("submit error", err);
            setReportModalStage("error", { message: "Network error." });
            if(submitBtn) {
                submitBtn.disabled = false;
                submitBtn.innerHTML = "Submit Report";
            }
          });
      });
    }

    // --- 5. Report Modal Helpers ---
    function openReportModal() {
      const modal = document.getElementById("report-result-modal");
      if (!modal) return;
      modal.style.display = "block";
      document.body.classList.add("modal-open");
      
      const closeBtn = document.getElementById("report-modal-close");
      const closeBtn2 = document.getElementById("report-modal-close-2");
      if (closeBtn) closeBtn.addEventListener("click", closeReportModal);
      if (closeBtn2) closeBtn2.addEventListener("click", closeReportModal);
    }

    function closeReportModal() {
      const modal = document.getElementById("report-result-modal");
      if (!modal) return;
      modal.style.display = "none";
      document.body.classList.remove("modal-open");
      setReportModalStage("loading");
    }

    function setReportModalStage(stage, opts) {
      const loading = document.getElementById("report-modal-stage-loading");
      const result = document.getElementById("report-modal-stage-result");
      const title = document.getElementById("report-modal-title");
      const resultContent = document.getElementById("report-modal-result-content");
      const footer = document.getElementById("report-modal-footer");
      const actionBtn = document.getElementById("report-modal-action");

      if (!loading || !result || !title || !resultContent) return;

      if (stage === "loading") {
        title.textContent = "Analyzing report";
        loading.style.display = "block";
        result.style.display = "none";
        if(footer) footer.style.display = "none";
        if(actionBtn) actionBtn.style.display = "none";
      } else if (stage === "success") {
        title.textContent = "Analysis complete";
        loading.style.display = "none";
        result.style.display = "block";
        if(footer) footer.style.display = "block";
        resultContent.innerHTML = `<div class="alert alert-success">${opts?.message || "Success"}</div>`;
      } else if (stage === "error") {
        title.textContent = "Analysis result";
        loading.style.display = "none";
        result.style.display = "block";
        if(footer) footer.style.display = "block";
        const msg = opts?.message || "Failed";
        resultContent.innerHTML = `<div class="alert alert-danger">${msg}</div>`;
      }
    }

    // --- 6. OTP LOGIC FUNCTIONS (Didefinisikan dulu biar tidak ReferenceError) ---
    
    function closeOtpModal() {
      const m = document.getElementById("otp-modal");
      if (m) m.parentElement.remove();
    }

    function sendOtpCode() {
      const emailEl = document.getElementById("otp-email");
      if (!emailEl) return; // Safety check
      
      const email = emailEl.value;
      if (!email) return alert("Email wajib diisi");
      
      const btn = document.getElementById("otp-send");
      if(btn) {
          btn.disabled = true;
          btn.textContent = "Mengirim...";
      }
      
      fetch("/api/profiles/request-otp/", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": csrftoken,
        },
        body: `email=${encodeURIComponent(email)}`,
      })
      .then(async (res) => {
          const data = await res.json().catch(() => ({}));
          if (res.ok && data.status === "success") {
            const s1 = document.getElementById("otp-stage-1");
            const s2 = document.getElementById("otp-stage-2");
            if(s1) s1.style.display = "none";
            if(s2) s2.style.display = "block";
          } else {
            alert(data.message || "Gagal mengirim OTP");
            if(btn) { btn.disabled = false; btn.textContent = "Kirim Kode"; }
          }
      })
      .catch((err) => {
          console.error(err);
          alert("Network Error");
          if(btn) { btn.disabled = false; btn.textContent = "Kirim Kode"; }
      });
    }

    function verifyOtpCode() {
      const emailEl = document.getElementById("otp-email");
      const codeEl = document.getElementById("otp-code");
      
      if (!emailEl || !codeEl) return;

      const email = emailEl.value;
      const code = codeEl.value;
      
      if (!code) return alert("Kode wajib diisi");
      
      const btn = document.getElementById("otp-verify");
      if(btn) {
          btn.disabled = true;
          btn.textContent = "Memverifikasi...";
      }
      
      fetch("/api/profiles/verify-otp/", {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": csrftoken,
        },
        body: `email=${encodeURIComponent(email)}&otp=${encodeURIComponent(code)}`,
      })
      .then(async (res) => {
          const data = await res.json().catch(() => ({}));
          if (res.ok && data.status === "success") {
            closeOtpModal();
            window.location.reload();
          } else {
            alert(data.message || "Kode Salah");
            if(btn) { btn.disabled = false; btn.textContent = "Verifikasi"; }
          }
      })
      .catch((err) => {
          alert("Network Error");
          if(btn) { btn.disabled = false; btn.textContent = "Verifikasi"; }
      });
    }

    function openOtpModal() {
      if (document.getElementById("otp-modal")) return; 
      
      const modalHtml = `
      <div class="modal fade show" id="otp-modal" style="display:block; background: rgba(0,0,0,0.8); z-index: 9999;">
        <div class="modal-dialog modal-dialog-centered modal-sm">
          <div class="modal-content bg-dark text-white border-secondary">
            <div class="modal-header border-secondary">
              <h5 class="modal-title">Verifikasi Akun</h5>
              <button type="button" class="btn-close btn-close-white" id="otp-close"></button>
            </div>
            <div class="modal-body">
              <div id="otp-stage-1">
                <p class="small text-muted">Masukkan email untuk verifikasi.</p>
                <input id="otp-email" class="form-control bg-secondary text-white border-0 mb-3" type="email" placeholder="Email Anda" />
                <button id="otp-send" class="btn btn-success w-100">Kirim Kode</button>
              </div>
              <div id="otp-stage-2" style="display:none;">
                <p class="small text-success">Kode terkirim ke email!</p>
                <input id="otp-code" class="form-control bg-secondary text-white border-0 mb-3" type="text" placeholder="6 Digit Kode" style="text-align:center; letter-spacing:3px;"/>
                <button id="otp-verify" class="btn btn-primary w-100">Verifikasi</button>
              </div>
            </div>
          </div>
        </div>
      </div>`;
      
      const wrapper = document.createElement("div");
      wrapper.innerHTML = modalHtml;
      document.body.appendChild(wrapper);

      // PASANG EVENT LISTENER (Sekarang aman karena fungsi sudah didefinisikan di atas)
      document.getElementById("otp-close").addEventListener("click", closeOtpModal);
      document.getElementById("otp-send").addEventListener("click", sendOtpCode);
      document.getElementById("otp-verify").addEventListener("click", verifyOtpCode);
    }

    // --- 7. REACTION LOGIC ---
    function submitReaction(reportId, emojiType, btnElement) {
      const btn = typeof btnElement === "string" ? document.querySelector(btnElement) : btnElement;
      const actualBtn = btn.closest('button');
      if (btn.disabled) return;
      actualBtn.style.opacity = "0.7";
      btn.disabled = true;
      btn.style.opacity = "0.5";
      btn.style.cursor = "wait"; // Ubah kursor jadi jam pasir
      // URL Report Reaction
      const url = `/reports/api/reaction/${reportId}/`;

      fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrftoken,
        },
        body: new URLSearchParams({ 'reaction_type': emojiType })
      })
      .then(async (res) => {
          const data = await res.json().catch(() => ({}));
          
          // HANDLE GUEST (403)
          if (res.status === 403 && data.code === "guest_restriction") {
            openOtpModal(); // Panggil fungsi lokal
            return;
          }
          
          if (!res.ok) {
            console.error("Reaction failed", data);
            return;
          }
          const parentDiv = actualBtn.parentElement;
          const siblings = parentDiv.querySelectorAll('.btn-reaction');

          siblings.forEach(b => {
              b.classList.remove('active');
              // Opsional: Hapus style inline jika ada sisa
              b.style.opacity = "1";
          });

          // 4. SET ACTIVE BARU (Hanya jika action bukan 'removed')
          if (data.action === 'created' || data.action === 'updated') {
              actualBtn.classList.add('active');
          }
          // === UPDATE ANGKA ===
          if (data && data.counts) {
            Object.keys(data.counts).forEach((k) => {
              const el = document.getElementById(`count-${k}-${reportId}`);
              if (el) el.textContent = data.counts[k];
            });
            const totalEl = document.getElementById(`count-total-${reportId}`);
            if (totalEl && data.total_reactions !== undefined) {
                totalEl.textContent = data.total_reactions;
            }
          }
      })
      .catch((err) => console.error("Network error", err))
      .finally(() => {
          // Buka kunci visual
          if(actualBtn) actualBtn.style.opacity = "1";
      });
    }


    // --- 8. EXPOSE TO GLOBAL WINDOW (Agar bisa dipanggil onclick HTML) ---
    window.openReportModal = openReportModal;
    window.closeReportModal = closeReportModal;
    window.setReportModalStage = setReportModalStage;
    
    window.openOtpModal = openOtpModal;
    window.closeOtpModal = closeOtpModal;
    window.sendOtpCode = sendOtpCode;
    window.verifyOtpCode = verifyOtpCode;
    
    window.submitReaction = submitReaction;


    // --- 9. Sidebar Nav Animation ---
    (function () {
      const navItems = document.querySelectorAll(".right-nav .nav-item, .bottom-nav .nav-item");
      if (!navItems || !navItems.length) return;
      const path = window.location.pathname;
      navItems.forEach((a) => {
        try {
          const href = a.getAttribute("href");
          if (href && (href === path || (href !== "/" && path.startsWith(href)))) {
            a.classList.add("active");
          }
        } catch (e) {}
      });
      navItems.forEach((a) => {
        a.addEventListener("click", (ev) => {
            if(a.hasAttribute('data-bs-toggle')) return; 
            ev.preventDefault();
            navItems.forEach((n) => n.classList.remove("active"));
            a.classList.add("active");
            a.classList.add("nav-click");
            setTimeout(() => a.classList.remove("nav-click"), 160);
            const target = a.getAttribute("href");
            setTimeout(() => {
                if (target) window.location.href = target;
            }, 140);
        });
      });
    })();
    // --- 10. Guest Account Logout Restriction ---
(function() {
        const STORAGE_KEY = 'colsp_guest_login_time';
        
        // 1. Cek Status Guest dari Body
        const isGuest = document.body.getAttribute('data-is-guest') === 'true';

        // === LOGIKA PEMBERSIHAN (PENTING) ===
        // Jika user yang buka halaman ini BUKAN Guest (misal sudah logout, atau user biasa),
        // Hapus timer lama dari memori browser.
        // Jadi pas login guest lagi nanti, timer mulai dari nol.
        if (!isGuest) {
            localStorage.removeItem(STORAGE_KEY);
            return; // Stop, tidak perlu kunci tombol logout
        }

        // 2. Cari tombol logout
        const logoutBtns = document.querySelectorAll("form[action*='logout'] button");
        if (logoutBtns.length === 0) return;

        // 3. Logika Waktu
        const LOCK_DURATION = 120; // 120 Detik (2 Menit)

        // Cek kapan guest ini mulai login
        let startTime = localStorage.getItem(STORAGE_KEY);
        
        // Jika belum ada data (Guest baru masuk), set waktu sekarang
        if (!startTime) {
            startTime = Math.floor(Date.now() / 1000); 
            localStorage.setItem(STORAGE_KEY, startTime);
        }

        // Fungsi Update UI
        function updateButtons(timeLeft) {
            logoutBtns.forEach(btn => {
                // Simpan state asli sekali saja
                if (!btn.dataset.originalText) {
                    btn.dataset.originalText = btn.innerHTML;
                    btn.dataset.originalClasses = btn.className;
                }

                if (timeLeft > 0) {
                    // TERKUNCI
                    btn.disabled = true;
                    btn.style.opacity = "0.6";
                    btn.style.cursor = "not-allowed";
                    btn.className = "btn btn-secondary w-100"; // Paksa jadi abu-abu
                    btn.innerHTML = `<i class="fas fa-lock"></i> Wait (${timeLeft}s)`;
                } else {
                    // TERBUKA
                    btn.disabled = false;
                    btn.style.opacity = "1";
                    btn.style.cursor = "pointer";
                    btn.className = btn.dataset.originalClasses; // Balikin warna asli
                    btn.innerHTML = btn.dataset.originalText;    // Balikin teks asli
                }
            });
        }

        // 4. Loop Timer
        const timer = setInterval(() => {
            const now = Math.floor(Date.now() / 1000);
            const elapsed = now - parseInt(startTime);
            const remaining = LOCK_DURATION - elapsed;

            if (remaining <= 0) {
                clearInterval(timer);
                updateButtons(0); // Buka kunci
            } else {
                updateButtons(remaining);
            }
        }, 1000);

        // Jalankan sekali di awal biar instan
        const initialNow = Math.floor(Date.now() / 1000);
        const initialRem = LOCK_DURATION - (initialNow - parseInt(startTime));
        if (initialRem > 0) updateButtons(initialRem);

    })();

// --- WELCOME BUBBLE LOGIC (TYPING + AUTO DISMISS) ---
    (function() {
        const bubble = document.getElementById('chat-welcome-bubble');
        const textElement = document.getElementById('typewriter-text');
        const message = "Bingung soal UKT atau Fasilitas atau lainya? Tanya aku di sini!";
        
        if (!bubble || !textElement) return;

        // Cek localStorage
        const hasSeen = localStorage.getItem('colsp_chat_welcome_seen');
        if (hasSeen) return; 

        // 1. Munculkan Bubble (Delay dikit pas load biar smooth)
        setTimeout(() => {
            bubble.style.display = 'block';
            startTyping();
        }, 1000);

        function startTyping() {
            let i = 0;
            const speed = 50; // Kecepatan ketik (ms per huruf)

            function type() {
                if (i < message.length) {
                    textElement.innerHTML += message.charAt(i);
                    i++;
                    setTimeout(type, speed);
                } else {
                    // 2. Selesai Ngetik -> Hapus Kursor kedip
                    const style = document.createElement('style');
                    style.innerHTML = "#typewriter-text::after { content: ''; }"; 
                    document.head.appendChild(style);

                    // 3. Mulai Hitung Mundur 5 Detik
                    setTimeout(autoDismiss, 5000);
                }
            }
            type();
        }

        function autoDismiss() {
            // Tambahkan class CSS fade-out
            bubble.classList.add('fade-out');
            
            // Tunggu animasi CSS selesai (1 detik), baru display none
            setTimeout(() => {
                bubble.style.display = 'none';
                // Jangan simpan localStorage jika hilang otomatis (biar muncul lagi next session)
                // Atau simpan jika mau permanen hilang:
                // localStorage.setItem('colsp_chat_welcome_seen', 'true'); 
            }, 1000);
        }

        // Fungsi tutup manual (Klik X)
        window.dismissBubble = function() {
            bubble.style.display = 'none';
            localStorage.setItem('colsp_chat_welcome_seen', 'true'); // Permanen hilang
        };
    })();

    /* =========================================
  GEMINI-STYLE CHAT LOGIC
   ========================================= */
(function() {
    const chatForm = document.getElementById('chat-form');
    const chatInput = document.getElementById('chat-input');
    const welcomeScreen = document.getElementById('welcome-screen');
    const chatBox = document.getElementById('chat-box');
    const loadingIndicator = document.getElementById('loading-animation');

    if (!chatForm) return; // Stop jika bukan di halaman chat

    // Fungsi Render Pesan User
    function appendUserMessage(message) {
        // 1. Sembunyikan Welcome Screen, Munculkan Chat Box
        if (welcomeScreen && !welcomeScreen.classList.contains('d-none')) {
            welcomeScreen.classList.add('d-none');
            chatBox.classList.remove('d-none');
        }

        const msgDiv = document.createElement('div');
        msgDiv.className = 'message user-message d-flex mb-4 justify-content-end';
        msgDiv.innerHTML = `
            <div class="message-content">
                ${escapeHtml(message)}
            </div>
        `;
        // Insert sebelum loading indicator
        chatBox.insertBefore(msgDiv, loadingIndicator);
        scrollToBottom();
    }

    // Fungsi Render Pesan Bot
    function appendBotMessage(messageHTML) {
        const msgDiv = document.createElement('div');
        msgDiv.className = 'message bot-message d-flex mb-4';
        msgDiv.innerHTML = `
            <div class="flex-shrink-0 me-3">
                <div class="avatar-robot-small rounded-circle d-flex align-items-center justify-content-center">
                    <i class="fas fa-robot text-white small"></i>
                </div>
            </div>
            <div class="message-content">
                ${messageHTML}
            </div>
        `;
        chatBox.insertBefore(msgDiv, loadingIndicator);
        scrollToBottom();
    }

    // Fungsi Submit
function handleChatSubmit(e) {
        if (e) e.preventDefault(); 

        const message = chatInput.value.trim();
        if (!message) return;

        // 1. Tampilkan Pesan User
        appendUserMessage(message);
        chatInput.value = '';
        
        // 2. TAMPILKAN EFEK BERPIKIR
        showLoading(); 

        const csrftoken = getCookie('csrftoken');
        
        fetch("/chatbot-faq/api/chat/", {
            method: "POST",
            headers: { 
                "Content-Type": "application/x-www-form-urlencoded", 
                "X-CSRFToken": csrftoken 
            },
            body: `message=${encodeURIComponent(message)}`
        })
        .then(res => res.json())
        .then(data => {
            // 3. SEMBUNYIKAN EFEK BERPIKIR (WAJIB DULUAN)
            hideLoading();

            // 4. Baru Tampilkan Jawaban Bot
            if (data.response) {
                // Ganti newline dengan <br> dan bold markdown (**) dengan <b> (simple formatting)
                let formatted = data.response
                    .replace(/\n/g, '<br>')
                    .replace(/\*\*(.*?)\*\*/g, '<b>$1</b>'); 
                appendBotMessage(formatted);
            } else {
                appendBotMessage("Maaf, saya tidak mengerti.");
            }
        })
        .catch(err => {
            hideLoading(); // Tetap sembunyikan kalau error
            console.error(err);
            appendBotMessage("⚠️ Maaf, terjadi kesalahan koneksi.");
        });
    }

function showLoading() {
        if (!loadingIndicator) return;
        // Pindahkan elemen loading ke urutan paling bawah DOM chatbox
        // Agar dia selalu muncul SETELAH pesan terakhir user
        chatBox.appendChild(loadingIndicator);
        
        // Munculkan
        loadingIndicator.classList.remove('d-none');
        scrollToBottom();
    }

    function hideLoading() {
        if (!loadingIndicator) return;
        // Sembunyikan
        loadingIndicator.classList.add('d-none');
    }
    chatForm.addEventListener('submit', handleChatSubmit);
    // 2. Saat tekan Enter (Optional, tapi bagus buat UX)
    chatInput.addEventListener('keydown', function(e) {
        // Jika tekan Enter TANPA Shift
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // Cegah enter bikin baris baru
            // Buat event dummy untuk dikirim ke handleChatSubmit
            handleChatSubmit(e); 
        }
    });
    // --- HELPER SCROLL ---
    function scrollToBottom() {
        chatBox.scrollTop = chatBox.scrollHeight;
    }

    // Helper: Escape HTML (Security)
    function escapeHtml(text) {
        return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
    }

    // Helper: Send Quick Message (Chips)
    window.sendQuickMessage = function(msg) {
        chatInput.value = msg;
        // Trigger submit event manually
        chatForm.dispatchEvent(new Event('submit'));
    };

})();

  })();
}
document.addEventListener('click', function(e) {
    // 1. Cek apakah yang diklik adalah tombol dengan class 'preview-trigger'
    // Kita pakai .closest() agar kalau user klik ikon <i> di dalam tombol, tetap terdeteksi
    const trigger = e.target.closest('.preview-trigger');
    
    // Jika bukan tombol preview, abaikan
    if (!trigger) return;

    // 2. Hentikan perilaku default (jangan langsung buka link)
    e.preventDefault();
    const url = trigger.href;

    // 3. Deteksi apakah User menggunakan Mobile (HP/Tablet)
    // Regex sederhana untuk mendeteksi iPhone, iPad, Android
    const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);

    if (isMobile) {
        // PERILAKU MOBILE:
        // Buka di tab yang SAMA (window.location).
        // Ini membiarkan browser HP (Chrome/Safari Mobile) menangani file secara native.
        // Biasanya HP akan otomatis membuka PDF Viewer atau Gallery tanpa membuka tab baru yang menumpuk.
        window.location.href = url; 
    } else {
        // PERILAKU DESKTOP:
        // Buka di TAB BARU (_blank).
        // Agar user tidak kehilangan halaman saat ini dan bisa multitasking.
        window.open(url, '_blank');
    }
});