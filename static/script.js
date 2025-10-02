const dropArea = document.getElementById("drop-area");
const fileElem = document.getElementById("fileElem");
const overlay = document.getElementById("overlay");
const preview = document.getElementById("preview");
const uploadBtn = document.getElementById("uploadBtn");
const senderInput = document.getElementById("sender");
const filenameBase = document.getElementById("filename-base");
const filenameExt = document.getElementById("filename-ext");
const progressContainer = document.getElementById("progress-container");
const progressBar = document.getElementById("progress-bar");

let selectedFile = null;

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

// Handle file
function handleFile(file) {
  if (!file) return;
  selectedFile = file;

  // Preview
  preview.innerHTML = "";
  if (file.type.startsWith("image/")) {
    const img = document.createElement("img");
    img.src = URL.createObjectURL(file);
    preview.appendChild(img);
  } else if (file.type.startsWith("video/")) {
    const video = document.createElement("video");
    video.src = URL.createObjectURL(file);
    video.controls = true;
    preview.appendChild(video);
  } else {
    alert("Only images and videos can be previewed.");
    return;
  }

  // Filename editing
  const parts = file.name.split(".");
  const ext = parts.pop();
  const base = parts.join(".");
  filenameBase.value = base;
  filenameExt.textContent = "." + ext;

  // Enable popup + upload button
  overlay.classList.remove("hidden");
  uploadBtn.classList.add("enabled");
  uploadBtn.disabled = false;
}

// Upload
uploadBtn.addEventListener("click", () => {
  if (!selectedFile) return;

  const sender = senderInput.value.trim() || "noname";
  const finalName = filenameBase.value + filenameExt.textContent;

  const formData = new FormData();
  formData.append("file", selectedFile, finalName);
  formData.append("sender", sender);

  // Button state
  uploadBtn.classList.remove("enabled");
  uploadBtn.classList.add("sending");
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
      uploadBtn.classList.remove("sending");
      uploadBtn.classList.add("sent");
      uploadBtn.textContent = "Sent!";
      uploadBtn.disabled = true;
      selectedFile = null;
      setTimeout(() => {
        overlay.classList.add("hidden");
        preview.innerHTML = "";
        progressBar.style.width = "0";
        uploadBtn.textContent = "Upload";
        uploadBtn.className = "";
        uploadBtn.disabled = true;
      }, 1500);
    } else {
      alert("Upload failed.");
    }
  };

  xhr.send(formData);
});
