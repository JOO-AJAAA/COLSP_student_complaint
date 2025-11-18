const themeToggle = document.getElementById("themeToggle");
const themeIcon = document.getElementById("themeIcon");
const body = document.body;

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

  const formData = {
    reportType: document.querySelector('input[name="reportType"]:checked')
      .value,
    category: document.getElementById("category").value,
    title: document.getElementById("title").value,
    description: document.getElementById("description").value,
    attachments: fileInput.files,
  };

  console.log("Form submitted:", formData);
  alert(
    "Report submitted successfully! (This is a demo - backend integration pending)"
  );
});

// Sidebar navigation: active state + quick click animation
(function () {
  const navItems = document.querySelectorAll(".right-nav .nav-item");
  if (!navItems || !navItems.length) return;

  // Set active based on current path (simple match)
  const path = window.location.pathname;
  navItems.forEach((a) => {
    try {
      const href = a.getAttribute("href");
      if (href && (href === path || (href !== "/" && path.startsWith(href)))) {
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
