if (window.__colsp_base_js_loaded) {
  console.warn("base.js already loaded — skipping duplicate execution");
} else {
  window.__colsp_base_js_loaded = true;
  (function () {
    "use strict";

    const themeToggle = document.getElementById("themeToggle");
    const themeIcon = document.getElementById("themeIcon");
    const body = document.body;

    // CSRF helper: read csrftoken from cookies
    function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== "") {
        const cookies = document.cookie.split(";");
        for (let i = 0; i < cookies.length; i++) {
          const cookie = cookies[i].trim();
          // Does this cookie string begin with the name we want?
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

    themeToggle.addEventListener("click", () => {
      const currentTheme = body.getAttribute("data-theme");
      const newTheme = currentTheme === "dark" ? "light" : "dark";

      body.setAttribute("data-theme", newTheme);
      themeIcon.className = newTheme === "dark" ? "fas fa-moon" : "fas fa-sun";

      localStorage.setItem("theme", newTheme);
    });

    const savedTheme = localStorage.getItem("theme") || "dark";
    body.setAttribute("data-theme", savedTheme);
    themeIcon.className = savedTheme === "dark" ? "fas fa-moon" : "fas fa-sun";

    const fileInput = document.getElementById("attachment");
    const fileLabel = document.querySelector(".file-upload-label span");

    fileInput.addEventListener("change", (e) => {
      const files = e.target.files;
      if (files.length > 0) {
        fileLabel.textContent =
          files.length === 1 ? files[0].name : `${files.length} files selected`;
      } else {
        fileLabel.textContent = "Click to upload files or drag and drop";
      }
    });

    document.getElementById("reportForm").addEventListener("submit", (e) => {
      e.preventDefault();
      const submitBtn = e.target.querySelector(".btn-submit");

      // Prepare FormData
      const fd = new FormData();
      const reportTypeInput = document.querySelector(
        'input[name="reportType"]:checked'
      );
      if (reportTypeInput) fd.append("type", reportTypeInput.value);
      fd.append("category", document.getElementById("category").value);
      fd.append("title", document.getElementById("title").value);
      fd.append("description", document.getElementById("description").value);
      // Attach first file if present (server expects 'attachment')
      if (fileInput.files && fileInput.files.length > 0) {
        fd.append("attachment", fileInput.files[0]);
      }

      // UI: loading state
      submitBtn.disabled = true;
      const origHtml = submitBtn.innerHTML;
      submitBtn.innerHTML =
        '<i class="fas fa-spinner fa-spin"></i> Analyzing...';

      // Open modal and show loading stage
      openReportModal();
      setReportModalStage("loading");

      // Clear any existing alert (kept for legacy locations)
      const existingAlert = document.querySelector("#report-alert");
      if (existingAlert) existingAlert.remove();

      fetch("/reports/submit/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "X-CSRFToken": csrftoken,
          "X-Requested-With": "XMLHttpRequest",
        },
        body: fd,
      })
        .then(async (res) => {
          const data = await res.json().catch(() => ({}));

          if (res.status === 400) {
            // Rejected content (gambling/toxic etc.) -> show in modal
            const message =
              data && data.message ? data.message : "Submission rejected.";
            setReportModalStage("error", { message, details: data });
            submitBtn.disabled = false;
            submitBtn.innerHTML = origHtml;
            return;
          }

          if (res.status === 500) {
            const message =
              data && data.message
                ? data.message
                : "Server error. Please try again later.";
            setReportModalStage("error", { message, details: data });
            submitBtn.disabled = false;
            submitBtn.innerHTML = origHtml;
            return;
          }

          // Success
          if (res.ok) {
            const successMsg =
              data && data.message ? data.message : "Report successfully sent!";
            setReportModalStage("success", {
              message: successMsg,
              redirect: data && data.redirect_url,
            });

            // If redirect_url provided, respect it after brief delay
            if (data && data.redirect_url) {
              setTimeout(() => {
                window.location.href = data.redirect_url;
              }, 1400);
            } else {
              setTimeout(() => {
                window.location.href = "/reports/";
              }, 1400);
            }
            return;
          }

          // Fallback: show a generic error
          setReportModalStage("error", {
            message: "Unexpected response from server.",
          });
          submitBtn.disabled = false;
          submitBtn.innerHTML = origHtml;
        })
        .catch((err) => {
          console.error("submit error", err);
          setReportModalStage("error", {
            message: "Network error. Please try again.",
          });
          submitBtn.disabled = false;
          submitBtn.innerHTML = origHtml;
        });
    });

    /* Report modal helpers */
    function openReportModal() {
      const modal = document.getElementById("report-result-modal");
      if (!modal) return;
      modal.style.display = "block";
      document.body.classList.add("modal-open");
      // attach close handlers
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
      // reset to loading state
      setReportModalStage("loading");
    }

    function setReportModalStage(stage, opts) {
      const loading = document.getElementById("report-modal-stage-loading");
      const result = document.getElementById("report-modal-stage-result");
      const title = document.getElementById("report-modal-title");
      const resultContent = document.getElementById(
        "report-modal-result-content"
      );
      const footer = document.getElementById("report-modal-footer");
      const actionBtn = document.getElementById("report-modal-action");

      if (!loading || !result || !title || !resultContent) return;

      if (stage === "loading") {
        title.textContent = "Analyzing report";
        loading.style.display = "block";
        result.style.display = "none";
        footer.style.display = "none";
        actionBtn.style.display = "none";
      } else if (stage === "success") {
        title.textContent = "Analysis complete";
        loading.style.display = "none";
        result.style.display = "block";
        footer.style.display = "block";
        actionBtn.style.display = "none";
        resultContent.innerHTML = `<div class="alert alert-success">${
          opts && opts.message ? opts.message : "Success"
        }</div>`;
      } else if (stage === "error") {
        title.textContent = "Analysis result";
        loading.style.display = "none";
        result.style.display = "block";
        footer.style.display = "block";
        actionBtn.style.display = "none";
        const msg =
          opts && opts.message ? opts.message : "Failed to analyze the report";
        resultContent.innerHTML = `<div class="alert alert-danger">${msg}</div>`;
      }
    }

    /* Reaction & OTP flow */
    window.submitReaction = function (reportId, emojiType, btnElement) {
      // btnElement may be the DOM element or an id selector
      const btn =
        typeof btnElement === "string"
          ? document.querySelector(btnElement)
          : btnElement;
      fetch("/reports/toggle-reaction/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/json",
          "X-Requested-With": "XMLHttpRequest",
          "X-CSRFToken": csrftoken,
        },
        body: JSON.stringify({ report_id: reportId, type: emojiType }),
      })
        .then(async (res) => {
          const data = await res.json().catch(() => ({}));
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
          }
          // Toggle active style
          if (btn) btn.classList.toggle("active");
        })
        .catch((err) => console.error("Reaction network error", err));
    };

    /* OTP modal helpers */
    function openOtpModal() {
      if (document.getElementById("otp-modal")) return; // already open
      const modalHtml = `
  <div class="modal fade show" id="otp-modal" style="display:block; background: rgba(0,0,0,0.5);">
    <div class="modal-dialog modal-sm">
      <div class="modal-content bg-dark text-white">
        <div class="modal-header">
          <h5 class="modal-title">Verify to interact</h5>
          <button type="button" class="btn-close btn-close-white" id="otp-close"></button>
        </div>
        <div class="modal-body" id="otp-body">
          <div id="otp-stage-1">
            <label class="form-label">Enter your email</label>
            <input id="otp-email" class="form-control" type="email" placeholder="you@example.com" />
            <button id="otp-send" class="btn btn-signup mt-3">Send Code</button>
          </div>
          <div id="otp-stage-2" style="display:none;">
            <p class="small">Code sent. Check your email.</p>
            <input id="otp-code" class="form-control" type="text" placeholder="6-digit code" />
            <button id="otp-verify" class="btn btn-signup mt-3">Verify</button>
          </div>
        </div>
      </div>
    </div>
  </div>`;
      const wrapper = document.createElement("div");
      wrapper.innerHTML = modalHtml;
      document.body.appendChild(wrapper);

      document
        .getElementById("otp-close")
        .addEventListener("click", closeOtpModal);
      document
        .getElementById("otp-send")
        .addEventListener("click", sendOtpCode);
      document
        .getElementById("otp-verify")
        .addEventListener("click", verifyOtpCode);
    }

    function closeOtpModal() {
      const m = document.getElementById("otp-modal");
      if (m) m.parentElement.remove();
    }

    function sendOtpCode() {
      const email = document.getElementById("otp-email").value;
      if (!email) return alert("Please enter your email");
      const btn = document.getElementById("otp-send");
      btn.disabled = true;
      btn.textContent = "Sending...";
      fetch("/api/kontol/request-otp/", {
        method: "POST",
        credentials: "same-origin",
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
            alert(data && data.message ? data.message : "Failed to send OTP");
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

    function verifyOtpCode() {
      const email = document.getElementById("otp-email").value;
      const code = document.getElementById("otp-code").value;
      if (!code) return alert("Please enter the code");
      const btn = document.getElementById("otp-verify");
      btn.disabled = true;
      btn.textContent = "Verifying...";
      fetch("/api/kontol/verify-otp/", {
        method: "POST",
        credentials: "same-origin",
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
          "X-CSRFToken": csrftoken,
        },
        body: `email=${encodeURIComponent(email)}&otp=${encodeURIComponent(
          code
        )}`,
      })
        .then(async (res) => {
          const data = await res.json().catch(() => ({}));
          if (res.ok && data.status === "success") {
            // close and reload to reflect authenticated user
            closeOtpModal();
            window.location.reload();
          } else {
            alert(data && data.message ? data.message : "Invalid code");
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

    // Sidebar navigation: active state + quick click animation
    (function () {
      const navItems = document.querySelectorAll(".right-nav .nav-item");
      if (!navItems || !navItems.length) return;

      // Set active based on current path (simple match)
      const path = window.location.pathname;
      navItems.forEach((a) => {
        try {
          const href = a.getAttribute("href");
          if (
            href &&
            (href === path || (href !== "/" && path.startsWith(href)))
          ) {
            a.classList.add("active");
          }
        } catch (e) {
          /* ignore */
        }
      });

      navItems.forEach((a) => {
        a.addEventListener("click", (ev) => {
          // quick visual feedback before navigation
          ev.preventDefault();
          navItems.forEach((n) => n.classList.remove("active"));
          a.classList.add("active");
          a.classList.add("nav-click");
          setTimeout(() => a.classList.remove("nav-click"), 160);

          const target = a.getAttribute("href");
          // short delay so animation is perceptible but fast
          setTimeout(() => {
            if (target) window.location.href = target;
          }, 140);
        });
      });
    })();
    // Expose selected helpers to global scope for other inline handlers
    try {
      window.openOtpModal = openOtpModal;
      window.closeOtpModal = closeOtpModal;
      window.sendOtpCode = sendOtpCode;
      window.verifyOtpCode = verifyOtpCode;
      window.openReportModal = openReportModal;
      window.closeReportModal = closeReportModal;
      window.setReportModalStage = setReportModalStage;
    } catch (e) {
      console.warn("Failed to attach helpers to window", e);
    }
  })();
}
