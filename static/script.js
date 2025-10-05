const dropArea = document.getElementById("drop-area");
const fileElem = document.getElementById("fileElem");
const overlay = document.getElementById("overlay");
const preview = document.getElementById("preview");
const pairBtn = document.getElementById("pairBtn");
const uploadBtn = document.getElementById("uploadBtn");
const senderInput = document.getElementById("sender");
const filenameBase = document.getElementById("filename-base");
const filenameExt = document.getElementById("filename-ext");
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");

let selectedFile = null;
let paired = false;
let statusPoller = null;

// Drag and drop
dropArea.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropArea.style.background = "rgba(74,144,226,0.2)";
});
dropArea.addEventListener("dragleave", () => {
  dropArea.style.background = "transparent";
});
dropArea.addEventListener("drop", (e) => {
  e.preventDefault();
  dropArea.style.background = "transparent";
  handleFile(e.dataTransfer.files[0]);
});

// Click on drop area = open file picker
dropArea.addEventListener("click", () => {
  fileElem.click();
});

// When file chosen via picker
fileElem.addEventListener("change", (e) => {
  handleFile(e.target.files[0]);
});

// Handle file selection
function handleFile(file) {
  if (!file) return;
  selectedFile = file;

  // Reset preview
  preview.innerHTML = "";

  if (file.type.startsWith("image/")) {
    const img = document.createElement("img");
    img.src = URL.createObjectURL(file);
    img.style.maxWidth = "100%";
    img.style.maxHeight = "100%";
    preview.appendChild(img);
  } else if (file.type.startsWith("video/")) {
    const video = document.createElement("video");
    video.src = URL.createObjectURL(file);
    video.controls = true;
    video.style.maxWidth = "100%";
    video.style.maxHeight = "100%";
    preview.appendChild(video);
  } else {
    const info = document.createElement("p");
    info.textContent = "File selected: " + file.name;
    preview.appendChild(info);
  }

  // Filename editing
  const parts = file.name.split(".");
  const ext = parts.pop();
  const base = parts.join(".");
  filenameBase.value = base;
  filenameExt.textContent = "." + ext;

  // Enable popup + upload button
  overlay.classList.remove("hidden");
  uploadBtn.className = "enabled"; // only use class
  uploadBtn.textContent = "Upload";
}

// ========== pairing ==========

// Check pair status on page load
function checkStatusOnce() {
  fetch("/status")
    .then(res => res.json())
    .then(data => {
      if (data.paired && data.status === "approved") {
        paired = true;
        pairBtn.style.display = "none";
        uploadBtn.style.display = "inline-block";
        uploadBtn.disabled = false;
      } else {
        paired = false;
        pairBtn.style.display = "inline-block";
        uploadBtn.style.display = "none";
      }
    })
    .catch(err => {
      console.error("Status check failed:", err);
      pairBtn.style.display = "inline-block";
      uploadBtn.style.display = "none";
    });
}

window.addEventListener("load", () => {
  checkStatusOnce();
});

// Poll status (used after sending a pair request)
function startStatusPoll(interval = 2000) {
  if (statusPoller) return;
  statusPoller = setInterval(() => {
    fetch("/status")
      .then(r => r.json())
      .then(data => {
        if (data.paired && data.status === "approved") {
          // approved -> stop polling, enable upload
          clearInterval(statusPoller);
          statusPoller = null;
          paired = true;
          pairBtn.style.display = "none";
          uploadBtn.style.display = "inline-block";
          uploadBtn.disabled = false;
          alert("✅ Pairing approved. You can now upload files.");
        } else if (data.status === "denied") {
          clearInterval(statusPoller);
          statusPoller = null;
          alert("❌ Pairing denied by admin.");
        } // if pending, keep polling
      })
      .catch(err => {
        console.error("status poll error", err);
      });
  }, interval);
}

// Pair request
pairBtn.addEventListener("click", () => {
  const sender = senderInput.value.trim() || "noname";

  fetch("/pair", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sender })
  })
    .then(res => res.json())
    .then(data => {
      if (data.success) {
        // server says already paired
        paired = true;
        pairBtn.style.display = "none";
        uploadBtn.style.display = "inline-block";
        uploadBtn.disabled = false;
        alert("Already paired. You can upload now.");
      } else if (data.pending) {
        // pending created: start polling status
        alert("Pair request sent. Waiting for admin approval...");
        startStatusPoll(2000);
      } else {
        // if server returns denied or error
        alert("Pairing failed: " + (data.message || "unknown"));
      }
    })
    .catch(err => {
      console.error("Pair error:", err);
      alert("Error contacting server for pairing.");
    });
});

// Ensure Upload button is hidden until paired
uploadBtn.style.display = "none";

// ========== upload ==========
// Upload
uploadBtn.addEventListener("click", () => {
  if (!selectedFile) return;

  const sender = senderInput.value.trim() || "noname";
  const finalName = filenameBase.value + filenameExt.textContent;

  const formData = new FormData();
  formData.append("file", selectedFile, finalName);
  formData.append("sender", sender);

  // Button state
  uploadBtn.className = "sending";
  uploadBtn.textContent = "Sending...";

  progressContainer.classList.remove("hidden");
  progressBar.style.width = "0";

  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/upload", true);

  xhr.upload.onprogress = (e) => {
    if (e.lengthComputable) {
      const percent = (e.loaded / e.total) * 100;
      progressBar.style.width = percent + "%";
    }
  };

  xhr.onload = () => {
    if (xhr.status === 200) {
      uploadBtn.className = "sent";
      uploadBtn.textContent = "Sent!";
      selectedFile = null;

      setTimeout(() => {
        overlay.classList.add("hidden");
        preview.innerHTML = "";
        progressBar.style.width = "0";
        uploadBtn.textContent = "Upload";
        uploadBtn.className = ""; // reset to neutral
      }, 1500);
    } else {
      alert("Upload failed.");
      uploadBtn.className = "enabled";
      uploadBtn.textContent = "Upload";
    }
  };

  xhr.onerror = () => {
    alert("Upload failed (network error).");
    uploadBtn.className = "enabled";
    uploadBtn.textContent = "Upload";
  };

  xhr.send(formData);
});
