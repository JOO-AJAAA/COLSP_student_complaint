if (window.__colsp_base_js_loaded) {
  console.warn("base.js already loaded — skipping duplicate execution");
} else {
  window.__colsp_base_js_loaded = true;
  (function () {
    "use strict";

    const themeToggle = document.getElementById("themeToggle");
    const themeIcon = document.getElementById("themeIcon");
    const body = document.body;

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
        submitBtn.disabled = true;
        const origHtml = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Analyzing...';

        openReportModal();
        setReportModalStage("loading");

        // Use the correct API Endpoint for submission
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

            // Handle Rejected (400)
            if (res.status === 400) {
              const message = data && data.message ? data.message : "Submission rejected.";
              setReportModalStage("error", { message, details: data });
              submitBtn.disabled = false;
              submitBtn.innerHTML = origHtml;
              return;
            }

            // Handle Server Error (500)
            if (res.status === 500) {
              const message = data && data.message ? data.message : "Server error.";
              setReportModalStage("error", { message, details: data });
              submitBtn.disabled = false;
              submitBtn.innerHTML = origHtml;
              return;
            }

            // Handle Success
            if (res.ok) {
              const successMsg = data && data.message ? data.message : "Report sent!";
              setReportModalStage("success", {
                message: successMsg,
                redirect: data && data.redirect_url,
              });

              setTimeout(() => {
                window.location.href = data.redirect_url || "/reports/";
              }, 1400);
              return;
            }

            // Fallback
            setReportModalStage("error", { message: "Unexpected response." });
            submitBtn.disabled = false;
            submitBtn.innerHTML = origHtml;
          })
          .catch((err) => {
            console.error("submit error", err);
            setReportModalStage("error", { message: "Network error." });
            submitBtn.disabled = false;
            submitBtn.innerHTML = origHtml;
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
    // Expose needed helpers
    window.openReportModal = openReportModal;
    window.closeReportModal = closeReportModal;
    window.setReportModalStage = setReportModalStage;


    /* =========================================
       6. REACTION LOGIC (PERBAIKAN UTAMA DISINI)
       ========================================= */
    window.submitReaction = function (reportId, emojiType, btnElement) {
      const btn = typeof btnElement === "string" ? document.querySelector(btnElement) : btnElement;
      
      // FIX 1: URL Dynamic yang Benar sesuai backend
      const url = `/reports/api/reaction/${reportId}/`;

      fetch(url, {
        method: "POST",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded", // FIX 2: Pakai Form Encoded
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrftoken,
        },
        // FIX 3: Kirim data dengan URLSearchParams agar terbaca request.POST di Django
        body: new URLSearchParams({
            'reaction_type': emojiType
        })
      })
        .then(async (res) => {
          const data = await res.json().catch(() => ({}));
          
          // FIX 4: Tangkap status 403 Forbidden -> Trigger Modal
          if (res.status === 403 && data.code === "guest_restriction") {
            openOtpModal();
            return;
          }
          
          if (!res.ok) {
            console.error("Reaction failed", data);
            return;
          }

          // Update counts in DOM
          if (data && data.counts) {
            Object.keys(data.counts).forEach((k) => {
              const el = document.getElementById(`count-${k}-${reportId}`);
              if (el) el.textContent = data.counts[k];
            });
             // Update Total if exists
            const totalEl = document.getElementById(`count-total-${reportId}`);
            if (totalEl && data.total_reactions !== undefined) {
                totalEl.textContent = data.total_reactions;
            }
          }
          // Toggle active style
          if (btn) btn.classList.toggle("active");
        })
        .catch((err) => console.error("Reaction network error", err));
    };

    /* =========================================
       7. OTP MODAL LOGIC (Sesuai Path '/api/kontol/')
       ========================================= */
    window.openOtpModal = function() {
      if (document.getElementById("otp-modal")) return; 
      
      const modalHtml = `
      <div class="modal fade show" id="otp-modal" style="display:block; background: rgba(0,0,0,0.8); z-index: 9999;">
        <div class="modal-dialog modal-dialog-centered modal-sm">
          <div class="modal-content bg-dark text-white border-secondary">
            <div class="modal-header border-secondary">
              <h5 class="modal-title">Guest Verification</h5>
              <button type="button" class="btn-close btn-close-white" id="otp-close"></button>
            </div>
            <div class="modal-body" id="otp-body">
              <div id="otp-stage-1">
                <p class="small text-muted mb-3">Enter email to verify action.</p>
                <input id="otp-email" class="form-control bg-secondary text-white border-0 mb-3" type="email" placeholder="you@example.com" />
                <button id="otp-send" class="btn btn-success w-100">Send Code</button>
              </div>
              <div id="otp-stage-2" style="display:none;">
                <p class="small text-success mb-3">Code sent to email.</p>
                <input id="otp-code" class="form-control bg-secondary text-white border-0 mb-3" type="text" placeholder="6-digit code" style="text-align:center; letter-spacing: 3px;" />
                <button id="otp-verify" class="btn btn-primary w-100">Verify</button>
              </div>
            </div>
          </div>
        </div>
      </div>`;
      
      const wrapper = document.createElement("div");
      wrapper.innerHTML = modalHtml;
      document.body.appendChild(wrapper);

      document.getElementById("otp-close").addEventListener("click", closeOtpModal);
      document.getElementById("otp-send").addEventListener("click", sendOtpCode);
      document.getElementById("otp-verify").addEventListener("click", verifyOtpCode);
    }

    window.closeOtpModal = function() {
      const m = document.getElementById("otp-modal");
      if (m) m.parentElement.remove();
    }

    window.sendOtpCode = function() {
      const email = document.getElementById("otp-email").value;
      if (!email) return alert("Please enter your email");
      const btn = document.getElementById("otp-send");
      btn.disabled = true;
      btn.textContent = "Sending...";
      
      // URL KHUSUS YANG ANDA MINTA
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
            document.getElementById("otp-stage-1").style.display = "none";
            document.getElementById("otp-stage-2").style.display = "block";
          } else {
            alert(data.message || "Failed to send OTP");
            btn.disabled = false;
            btn.textContent = "Send Code";
          }
        })
        .catch((err) => {
          console.error(err);
          alert("Network error");
          btn.disabled = false;
          btn.textContent = "Send Code";
        });
    }

    window.verifyOtpCode = function() {
      const email = document.getElementById("otp-email").value;
      const code = document.getElementById("otp-code").value;
      if (!code) return alert("Please enter the code");
      const btn = document.getElementById("otp-verify");
      btn.disabled = true;
      btn.textContent = "Verifying...";
      
      // URL KHUSUS YANG ANDA MINTA
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
            alert(data.message || "Invalid code");
            btn.disabled = false;
            btn.textContent = "Verify";
          }
        })
        .catch((err) => {
          console.error(err);
          alert("Network error");
          btn.disabled = false;
          btn.textContent = "Verify";
        });
    }

    // --- 8. Sidebar Nav Animation ---
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
            // Cek apakah ini tombol dropdown profile (jangan animasi navigasi)
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