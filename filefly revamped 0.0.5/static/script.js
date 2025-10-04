// === ELEMENTS ===
const uploadForm = document.getElementById("uploadForm");
const senderName = document.getElementById("senderName");
const fileInput = document.getElementById("fileInput");
const uploadBtn = document.getElementById("uploadBtn");
const fileList = document.getElementById("fileList");
const progressBar = document.getElementById("progressBar");
const popup = document.getElementById("popup");
const popupMessage = document.getElementById("popupMessage");
const closePopup = document.getElementById("closePopup");

// === EVENT LISTENERS ===

// Show chosen files instantly
fileInput.addEventListener("change", () => {
  fileList.innerHTML = "";
  for (const file of fileInput.files) {
    const li = document.createElement("li");
    li.textContent = file.name;
    fileList.appendChild(li);
  }
});

// Handle upload
uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();

  const sender = senderName.value.trim() || "noname";
  const files = fileInput.files;

  if (!files.length) {
    showPopup("Please select a file to upload!");
    return;
  }

  // Upload files one by one (clean and compatible with Flask)
  for (const file of files) {
    await uploadFile(file, sender);
  }

  // Reset form after upload
  uploadForm.reset();
  progressBar.style.width = "0%";
  showPopup("✅ All files uploaded successfully!");
});

// === CORE FUNCTION ===
async function uploadFile(file, sender) {
  const formData = new FormData();
  formData.append("file", file);
  formData.append("sender", sender);

  try {
    const response = await fetch("/upload", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) throw new Error("Upload failed");

    const result = await response.json();

    if (result.success) {
      updateProgress(100);
    } else {
      showPopup("⚠️ Error: " + (result.error || "Unknown error"));
    }
  } catch (err) {
    console.error(err);
    showPopup("❌ Upload failed: " + err.message);
  }
}

// === UI HELPERS ===

// Simulate progress bar
function updateProgress(percent) {
  progressBar.style.width = percent + "%";
  progressBar.textContent = percent + "%";
}

// Show popup
function showPopup(message) {
  popupMessage.textContent = message;
  popup.classList.add("show");
}

// Close popup
closePopup.addEventListener("click", () => {
  popup.classList.remove("show");
});
