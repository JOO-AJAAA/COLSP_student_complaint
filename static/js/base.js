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
      
      // URL: /api/kontol/request-otp/
      fetch("/api/kontol/request-otp/", {
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
      
      // URL: /api/kontol/verify-otp/
      fetch("/api/kontol/verify-otp/", {
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

          // Update UI
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
          if (btn) btn.classList.toggle("active");
      })
      .catch((err) => console.error("Reaction error", err));
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
      const navItems = document.querySelectorAll(".right-nav .nav-item");
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

  })();
}