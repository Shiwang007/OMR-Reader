// App State
const state = {
  currentStep: 1,
  examType: "",
  files: [],
  currentFileIndex: -1,
  answerKey: {},
  zoom: {
    scale: 0.25,
    panX: 0,
    panY: 0,
    dragging: false,
    startX: 0,
    startY: 0,
  },
  logoB64: "",
};

// Initialize
document.addEventListener("DOMContentLoaded", async () => {
  lucide.createIcons();
  setupEventListeners();
  state.logoB64 = await loadLogo();
});

async function loadLogo() {
  try {
    const res = await fetch("/assets/Medjeex_Logo.png");
    const blob = await res.blob();
    return new Promise((resolve) => {
      const reader = new FileReader();
      reader.onloadend = () => resolve(reader.result);
      reader.readAsDataURL(blob);
    });
  } catch (e) {
    console.error("Failed to load logo:", e);
    return "";
  }
}

function setupEventListeners() {
  document.getElementById("file-input").addEventListener("change", handleFiles);

  // Pan: drag
  const viewport = document.getElementById("preview-viewport");
  if (viewport) {
    viewport.addEventListener("mousedown", (e) => {
      state.zoom.dragging = true;
      state.zoom.startX = e.clientX - state.zoom.panX;
      state.zoom.startY = e.clientY - state.zoom.panY;
    });
    window.addEventListener("mousemove", (e) => {
      if (!state.zoom.dragging) return;
      state.zoom.panX = e.clientX - state.zoom.startX;
      state.zoom.panY = e.clientY - state.zoom.startY;
      applyZoom();
    });
    window.addEventListener("mouseup", () => {
      state.zoom.dragging = false;
    });
  }

  // Keyboard Navigation for Files (Arrow Up/Down)
  window.addEventListener("keydown", (e) => {
    if (state.currentStep !== 2) return;

    // Don't trigger if user is typing in an input
    if (e.target.tagName === "INPUT" || e.target.tagName === "TEXTAREA") return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      if (state.currentFileIndex < state.files.length - 1) {
        selectFile(state.currentFileIndex + 1);
      }
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      if (state.currentFileIndex > 0) {
        selectFile(state.currentFileIndex - 1);
      }
    }
  });
}

// Zoom functions
function applyZoom() {
  const container = document.getElementById("zoom-container");
  if (!container) return;
  container.style.transform = `translate(${state.zoom.panX}px, ${state.zoom.panY}px) scale(${state.zoom.scale})`;
  document.getElementById("zoom-level").innerText =
    Math.round(state.zoom.scale * 100) + "%";
}

function zoomIn() {
  state.zoom.scale = Math.min(5, state.zoom.scale + 0.25);
  applyZoom();
}
function zoomOut() {
  state.zoom.scale = Math.max(0.2, state.zoom.scale - 0.25);
  applyZoom();
}
function zoomReset() {
  state.zoom = {
    scale: 0.25,
    panX: 0,
    panY: 0,
    dragging: false,
    startX: 0,
    startY: 0,
  };
  applyZoom();
}

// Step Navigation
function nextStep() {
  if (state.currentStep < 4) goToStep(state.currentStep + 1);
}
function prevStep() {
  if (state.currentStep > 1) goToStep(state.currentStep - 1);
}
function goToStep(step) {
  document
    .querySelectorAll(".step-section")
    .forEach((s) => s.classList.remove("active"));
  document
    .querySelectorAll(".step")
    .forEach((s) => s.classList.remove("active"));
  state.currentStep = step;
  document.getElementById(`step-${step}`).classList.add("active");
  document.querySelector(`.step[data-step="${step}"]`).classList.add("active");
  updateNavigation();
  if (step === 3) renderAnswerGrid();
  
  // Hide export buttons and leaderboard container if moving away from step 4
  if (step < 4) {
    document.getElementById("export-buttons").classList.add("hidden");
    const leaderboardDetails = document.getElementById("leaderboard-details-container");
    if (leaderboardDetails) leaderboardDetails.classList.add("hidden");
    const calcBtn = document.querySelector("#step-4 .btn-primary.large");
    if (calcBtn) calcBtn.innerHTML = '<i data-lucide="zap"></i> Calculate & Generate Reports';
  }
}

function updateNavigation() {
  const btnNext = document.getElementById("btn-next");
  const btnBack = document.getElementById("btn-back");
  btnBack.disabled = state.currentStep === 1;
  if (state.currentStep === 1) btnNext.disabled = !state.examType;
  else if (state.currentStep === 2) btnNext.disabled = state.files.length === 0;
  else if (state.currentStep === 3) btnNext.disabled = Object.keys(state.answerKey).length === 0;
  else btnNext.disabled = false;
}

// Step 1
async function selectExam(type) {
  if (state.examType === type) {
    nextStep();
    return;
  }

  if (state.examType && state.files.length > 0) {
    if (!confirm("Switching exam types will clear your current batch and delete processed images from server. Continue?")) return;
  }

  // Call server to physically delete files
  try {
    await fetch("http://localhost:8000/clear-session", { method: "POST" });
  } catch (err) {
    console.error("Failed to clear server session:", err);
  }

  state.examType = type;

  // Full Reset
  state.files = [];
  state.currentFileIndex = -1;
  state.answerKey = {};
  state.leaderboard = [];
  state.zoom = {
    scale: 0.25,
    panX: 0,
    panY: 0,
    dragging: false,
    startX: 0,
    startY: 0,
  };

  // UI Reset
  document.querySelectorAll(".exam-card").forEach((c) => {
    c.classList.remove("selected");
    if (c.getAttribute("onclick") === `selectExam('${type}')`) c.classList.add("selected");
  });

  // Clear UI containers
  const fileList = document.getElementById("file-list");
  if (fileList) fileList.innerHTML = "";

  const ansPanel = document.getElementById("answer-panel");
  if (ansPanel)
    ansPanel.innerHTML =
      '<div class="answer-empty"><i data-lucide="scan"></i><p>Upload and process an OMR sheet to see detected answers here.</p></div>';

  const keyPreview = document.getElementById("key-preview");
  if (keyPreview) keyPreview.classList.add("hidden");

  const keyUpload = document.getElementById("key-upload-zone");
  if (keyUpload) keyUpload.classList.remove("hidden");

  const exportBtns = document.getElementById("export-buttons");
  if (exportBtns) exportBtns.classList.add("hidden");

  const leaderboardDetails = document.getElementById("leaderboard-details-container");
  if (leaderboardDetails) leaderboardDetails.classList.add("hidden");

  // Reset stats
  ["stat-total", "stat-avg", "stat-top"].forEach((id) => {
    const el = document.getElementById(id);
    if (el) el.innerText = id === "stat-total" ? "0" : "--";
  });

  const nameInput = document.getElementById("student-name-input");
  if (nameInput) nameInput.value = "";

  const preview = document.getElementById("omr-preview");
  if (preview) preview.src = "";

  const examInput = document.getElementById("exam-name");
  if (examInput) examInput.value = "";

  updateNavigation();
  lucide.createIcons();
  setStatus(`Selected ${type} - Session reset`);
}

// Step 2: Upload & Process
function readJsonFile(file) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const parsed = JSON.parse(event.target.result);
        resolve({ file, parsed });
      } catch (err) {
        reject(new Error(`Failed to parse ${file.name}: ${err.message}`));
      }
    };
    reader.onerror = () => reject(new Error(`Failed to read ${file.name}`));
    reader.readAsText(file);
  });
}

async function handleFiles(e) {
  const files = Array.from(e.target.files);
  if (files.length === 0) return;

  const jsonFiles = files.filter(f => f.name.endsWith(".json"));
  const imageFiles = files.filter(f => !f.name.endsWith(".json"));

  const jsonResults = [];
  if (jsonFiles.length > 0) {
    try {
      const readPromises = jsonFiles.map(readJsonFile);
      const results = await Promise.all(readPromises);
      results.forEach(({ file, parsed }) => {
        let displayName = file.name.replace(/\.[^/.]+$/, "");
        let answersData = {};
        let x = 0, y = 0;
        
        if (parsed && parsed.answers) {
          answersData = parsed.answers;
          if (parsed.student_name) displayName = parsed.student_name;
          if (parsed.calibration) {
            x = parsed.calibration.x_shift || 0;
            y = parsed.calibration.y_shift || 0;
          }
        } else {
          answersData = parsed;
        }

        jsonResults.push({
          name: file.name,
          displayName: displayName,
          image: "",
          data: answersData,
          x: x,
          y: y,
          processed: true,
          isJsonUpload: true
        });
      });
    } catch (err) {
      alert(err.message);
      return;
    }
  }

  let imageResults = [];
  if (imageFiles.length > 0) {
    const formData = new FormData();
    formData.append("exam_type", state.examType);
    for (let file of imageFiles) formData.append("files", file);

    setStatus("Uploading and processing batch...");
    document.getElementById("loader").classList.remove("hidden");

    try {
      const response = await fetch("http://localhost:8000/upload", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();

      if (data.status === "success") {
        imageResults = data.results.map((res) => ({
          name: res.filename,
          displayName: res.filename.replace(/\.[^/.]+$/, ""), // Strip extension
          image: res.image,
          data: res.data,
          x: 0,
          y: 0,
          processed: true,
          isJsonUpload: false
        }));
      }
    } catch (err) {
      setStatus("Error: " + err.message);
    } finally {
      document.getElementById("loader").classList.add("hidden");
    }
  }

  const allNewFiles = [...imageResults, ...jsonResults];
  if (allNewFiles.length > 0) {
    state.files = [...state.files, ...allNewFiles];
    renderFileList();
    updateNavigation();
    selectFile(state.files.length - allNewFiles.length);
    setStatus(`Processed ${allNewFiles.length} files successfully.`);
  }
}

function renderFileList() {
  const list = document.getElementById("file-list");
  list.innerHTML = "";
  state.files.forEach((file, idx) => {
    const item = document.createElement("div");
    item.className = `file-item ${idx === state.currentFileIndex ? "active" : ""}`;
    item.onclick = () => selectFile(idx);
    item.innerHTML = `<div class="file-info">
            <i data-lucide="${file.processed ? "check-circle-2" : "file-image"}" class="${file.processed ? "text-success" : ""}"></i>
            <span>${file.displayName || file.name}</span>
        </div>`;
    list.appendChild(item);
  });
  document.getElementById("file-count").innerText = state.files.length;
  lucide.createIcons();
}

function selectFile(idx) {
  state.currentFileIndex = idx;
  const file = state.files[idx];

  const nameInput = document.getElementById("student-name-input");
  if (nameInput) nameInput.value = file.displayName || file.name;

  const omrPreview = document.getElementById("omr-preview");
  let jsonPlaceholder = document.getElementById("json-placeholder");

  if (file.isJsonUpload) {
    if (omrPreview) omrPreview.style.display = "none";
    if (!jsonPlaceholder) {
      const viewport = document.getElementById("preview-viewport");
      jsonPlaceholder = document.createElement("div");
      jsonPlaceholder.id = "json-placeholder";
      jsonPlaceholder.className = "json-placeholder-overlay";
      jsonPlaceholder.innerHTML = `
        <i data-lucide="file-json" class="json-placeholder-icon"></i>
        <h3>OMR JSON Data Loaded</h3>
        <p id="json-placeholder-filename"></p>
        <div class="json-placeholder-badge">Calibration: X: <span id="json-x-val">0</span>, Y: <span id="json-y-val">0</span></div>
      `;
      viewport.appendChild(jsonPlaceholder);
    }
    jsonPlaceholder.style.display = "flex";
    document.getElementById("json-placeholder-filename").innerText = file.name;
    document.getElementById("json-x-val").innerText = file.x;
    document.getElementById("json-y-val").innerText = file.y;
    
    // Disable calibration controls since they don't apply to JSON
    document.querySelectorAll(".calibration-bar input, .calibration-bar button").forEach(el => el.disabled = true);
  } else {
    if (omrPreview) {
      omrPreview.style.display = "block";
      omrPreview.src = file.image;
    }
    if (jsonPlaceholder) {
      jsonPlaceholder.style.display = "none";
    }
    // Enable calibration controls
    document.querySelectorAll(".calibration-bar input, .calibration-bar button").forEach(el => el.disabled = false);
  }

  document.getElementById("shift-x").value = file.x;
  document.getElementById("shift-y").value = file.y;

  zoomReset();
  renderAnswerPanel(file.data);
  renderFileList();
}

function handleNameChange(newName) {
  const file = state.files[state.currentFileIndex];
  if (file) {
    file.displayName = newName;
    renderFileList(); // Update the sidebar list immediately
  }
}

// Render Answer Panel (visual cards)
function renderAnswerPanel(data) {
  const panel = document.getElementById("answer-panel");
  if (!data || Object.keys(data).length === 0) {
    panel.innerHTML = `<div class="answer-empty"><i data-lucide="scan"></i><p>No detection data available.</p></div>`;
    lucide.createIcons();
    return;
  }

  let html = "";
  let numericQs = [];
  if (state.examType === "JEE") {
    numericQs = [21, 22, 23, 24, 25, 46, 47, 48, 49, 50, 71, 72, 73, 74, 75];
  } else if (state.examType === "JEE_ADV_1") {
    numericQs = [9, 10, 11, 12, 25, 26, 27, 28, 41, 42, 43, 44];
  } else if (state.examType === "JEE_ADV_2") {
    numericQs = [10, 11, 12, 13, 14, 15, 16, 17, 18, 28, 29, 30, 31, 32, 33, 34, 35, 36, 46, 47, 48, 49, 50, 51, 52, 53, 54];
  }

  for (const [subject, questions] of Object.entries(data)) {
    const qEntries = Object.entries(questions);
    const answered = qEntries.filter(
      ([, v]) => v !== "SKIPPED" && v !== "INVALID",
    ).length;

    html += `<div class="subject-section">`;
    html += `<div class="subject-header"><span>${subject}</span><span class="subject-count">${answered}/${qEntries.length} answered</span></div>`;

    for (const [qNum, answer] of qEntries) {
      const qNumInt = parseInt(qNum);
      const isNumeric = numericQs.includes(qNumInt);

      if (isNumeric) {
        // Numerical question — show text input
        const val = answer === "SKIPPED" ? "" : answer;
        html += `<div class="q-row">
                    <span class="q-label">${qNum}</span>
                    <input type="text" class="num-input" value="${val}" placeholder="Enter answer"
                        data-subject="${subject}" data-q="${qNum}"
                        onchange="updateNumAnswer(this)">
                    <span class="q-type-badge">NUM</span>
                </div>`;
      } else {
        // MCQ question — show pills
        const options = ["A", "B", "C", "D"];
        const selectedOpts = answer ? answer.split(",") : [];
        let pills = options
          .map((opt) => {
            const selected = selectedOpts.includes(opt) ? "selected" : "";
            return `<div class="pill ${selected}" data-subject="${subject}" data-q="${qNum}" data-opt="${opt}" onclick="selectOption(this)">${opt}</div>`;
          })
          .join("");

        let statusBadge = "";
        if (answer === "SKIPPED")
          statusBadge = '<span class="q-status skipped">Skip</span>';
        else if (answer === "INVALID")
          statusBadge = '<span class="q-status invalid">Invalid</span>';

        html += `<div class="q-row">
                    <span class="q-label">${qNum}</span>
                    <div class="option-pills">${pills}</div>
                    ${statusBadge}
                </div>`;
      }
    }
    html += `</div>`;
  }
  panel.innerHTML = html;
  lucide.createIcons();
}

function selectOption(el) {
  const subject = el.dataset.subject;
  const qNum = el.dataset.q;
  const opt = el.dataset.opt;

  const row = el.closest(".q-row");
  const wasSelected = el.classList.contains("selected");

  // Remove existing status badge if any (like Skip/Invalid)
  const oldBadge = row.querySelector(".q-status");
  if (oldBadge) oldBadge.remove();

  if (wasSelected) {
    el.classList.remove("selected");
  } else {
    el.classList.add("selected");
  }

  // Get all currently selected pills in this row
  const selectedPills = Array.from(row.querySelectorAll(".pill.selected"))
    .map(p => p.dataset.opt)
    .sort();

  if (state.currentFileIndex !== -1) {
    if (selectedPills.length === 0) {
      state.files[state.currentFileIndex].data[subject][qNum] = "SKIPPED";
      // Append Skip badge
      const badge = document.createElement("span");
      badge.className = "q-status skipped";
      badge.innerText = "Skip";
      row.appendChild(badge);
    } else {
      state.files[state.currentFileIndex].data[subject][qNum] = selectedPills.join(",");
    }
  }

  // Update subject answered count dynamically
  updateSubjectCount(row);
}

function updateNumAnswer(el) {
  const subject = el.dataset.subject;
  const qNum = el.dataset.q;
  const val = el.value.trim() || "SKIPPED";
  if (state.currentFileIndex !== -1) {
    state.files[state.currentFileIndex].data[subject][qNum] = val;
  }
  const row = el.closest(".q-row");
  updateSubjectCount(row);
}

function updateSubjectCount(row) {
  const subjectSection = row.closest(".subject-section");
  if (!subjectSection) return;
  const countSpan = subjectSection.querySelector(".subject-count");
  if (countSpan) {
    const rows = subjectSection.querySelectorAll(".q-row");
    let answeredCount = 0;
    rows.forEach(r => {
      const selectedPill = r.querySelector(".pill.selected");
      const numInput = r.querySelector(".num-input");
      if (selectedPill) {
        answeredCount++;
      } else if (numInput && numInput.value.trim() !== "" && numInput.value.trim() !== "SKIPPED" && numInput.value.trim() !== "INVALID") {
        answeredCount++;
      }
    });
    countSpan.innerText = `${answeredCount}/${rows.length} answered`;
  }
}

function saveAnswerEdits() {
  if (state.currentFileIndex === -1) return;
  setStatus("Answer edits saved to record");
}

async function reprocessImage() {
  if (state.currentFileIndex === -1) return;
  const file = state.files[state.currentFileIndex];
  file.x = parseInt(document.getElementById("shift-x").value);
  file.y = parseInt(document.getElementById("shift-y").value);

  document.getElementById("loader").classList.remove("hidden");
  setStatus("Reprocessing with new calibration...");

  const formData = new FormData();
  formData.append("filename", file.name);
  formData.append("exam_type", state.examType);
  formData.append("x_shift", file.x);
  formData.append("y_shift", file.y);

  try {
    const response = await fetch("http://localhost:8000/process", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();
    if (data.status === "success") {
      file.image = data.processed_image;
      file.data = data.results;
      document.getElementById("omr-preview").src = file.image;
      renderAnswerPanel(file.data);
      setStatus("Calibration updated successfully");
    } else {
      setStatus("Processing error: " + data.message);
    }
  } catch (err) {
    setStatus("Calibration failed: " + err.message);
  } finally {
    document.getElementById("loader").classList.add("hidden");
  }
}

function applyToAll() {
  const x = parseInt(document.getElementById("shift-x").value);
  const y = parseInt(document.getElementById("shift-y").value);
  state.files.forEach((f) => {
    f.x = x;
    f.y = y;
  });
  setStatus(`Applied X:${x} Y:${y} to all ${state.files.length} files`);
}

// Step 3: Answer Key Upload
function renderAnswerGrid() {
  // Setup file input listener if not already done
  const keyInput = document.getElementById("key-file-input");
  if (!keyInput._bound) {
    keyInput.addEventListener("change", handleAnswerKeyUpload);
    keyInput._bound = true;
  }
}

function handleAnswerKeyUpload(e) {
  const file = e.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function (ev) {
    try {
      const keyData = JSON.parse(ev.target.result);
      state.answerKey = keyData;

      // Show preview, hide upload zone
      document.getElementById("key-upload-zone").classList.add("hidden");
      document.getElementById("key-preview").classList.remove("hidden");
      document.getElementById("key-filename").innerText = file.name;

      renderKeyPreview(keyData);
      setStatus("Answer key loaded: " + file.name);
      updateNavigation();
    } catch (err) {
      setStatus("Invalid JSON file: " + err.message);
    }
  };
  reader.readAsText(file);
}

function renderKeyPreview(data) {
  const container = document.getElementById("key-content");
  let html = "";

  for (const [subject, questions] of Object.entries(data)) {
    html += `<div class="key-subject-section">`;
    html += `<div class="key-subject-header">${subject}</div>`;
    html += `<div class="key-grid">`;

    const entries =
      typeof questions === "object" ? Object.entries(questions) : [];
    for (const [qNum, answer] of entries) {
      const displayAns = answer || "—";
      const isUnmarked = !answer || answer === "SKIPPED";
      const colorStyle = isUnmarked ? "color: var(--text-muted);" : "";
      const escapedSubj = subject.replace(/'/g, "\\'");
      
      html += `<div class="key-cell" onclick="editKeyCell(this, '${escapedSubj}', '${qNum}')" title="Click to edit / unmark">
                <span class="key-cell-q">Q${qNum}</span>
                <span class="key-cell-a" style="${colorStyle}">${displayAns}</span>
            </div>`;
    }
    html += `</div></div>`;
  }
  container.innerHTML = html;
  lucide.createIcons();
}

function editKeyCell(el, subject, qNum) {
  const currentVal = state.answerKey[subject][qNum] || "";
  const newVal = prompt(
    `Edit Answer Key for ${subject} Q${qNum}:\n` +
    `Enter correct answer (e.g. A, B, C, D, or multiple like A,B, or * for bonus, number for numericals).\n` +
    `Leave blank to UNMARK:`,
    currentVal
  );
  
  if (newVal === null) return; // Cancelled
  
  const trimmed = newVal.trim().toUpperCase();
  if (trimmed === "") {
    // Unmark
    delete state.answerKey[subject][qNum];
    el.querySelector(".key-cell-a").innerText = "—";
    el.querySelector(".key-cell-a").style.color = "var(--text-muted)";
    setStatus(`Unmarked ${subject} Q${qNum} in Answer Key`);
  } else {
    state.answerKey[subject][qNum] = trimmed;
    el.querySelector(".key-cell-a").innerText = trimmed;
    el.querySelector(".key-cell-a").style.color = "var(--primary)";
    setStatus(`Updated ${subject} Q${qNum} to ${trimmed} in Answer Key`);
  }
}

function clearAnswerKey() {
  state.answerKey = {};
  document.getElementById("key-upload-zone").classList.remove("hidden");
  document.getElementById("key-preview").classList.add("hidden");
  document.getElementById("key-file-input").value = "";
  setStatus("Answer key removed");
  updateNavigation();
}

// Step 4: Calculate on frontend + generate from templates
async function calculateFinal() {
  const examName = document.getElementById("exam-name").value;
  if (!examName) {
    alert("Please enter an exam name at the top of the page.");
    return;
  }
  if (Object.keys(state.answerKey).length === 0) {
    alert("No Answer Key found. Please go back to Step 3 and upload the master key.");
    return;
  }
  if (state.files.length === 0) {
    alert("No processed files found. Please go back to Step 2 and upload OMR sheets.");
    return;
  }

  const btn = document.querySelector("#step-4 .btn-primary");
  if (btn) {
    btn.innerHTML = '<div class="spinner small"></div> Calculating...';
    btn.disabled = true;
  }
  setStatus("Calculating scores...");

  // Score every student on the frontend
  const leaderboard = [];
  for (const file of state.files) {
    let totalCorrect = 0,
      totalWrong = 0,
      totalSkipped = 0,
      totalScore = 0;
    const subjectStats = {};

    for (const [subject, questions] of Object.entries(file.data)) {
      let correct = 0,
        wrong = 0,
        skipped = 0;
      // Case-insensitive subject matching
      const keySection =
        state.answerKey[subject] ||
        state.answerKey[
          Object.keys(state.answerKey).find(
            (k) => k.toLowerCase() === subject.toLowerCase(),
          )
        ] ||
        {};

      for (const [qNum, answer] of Object.entries(questions)) {
        const correctAns = keySection[qNum] || "";
        
        let validAnswers = [];
        if (Array.isArray(correctAns)) {
          correctAns.forEach((item) => {
            const parts = String(item)
              .split(",")
              .map((s) => s.trim().toUpperCase());
            validAnswers = validAnswers.concat(parts);
          });
        } else {
          validAnswers = String(correctAns)
            .split(",")
            .map((s) => s.trim().toUpperCase());
        }

        const isGraceQuestion = validAnswers.includes("*");

        if (isGraceQuestion) {
          correct++;
        } else if (answer === "SKIPPED" || answer === "" || answer === "INVALID") {
          skipped++;
        } else {
          const studentAnsStr = String(answer).trim().toUpperCase();
          if (validAnswers.includes(studentAnsStr)) {
            correct++;
          } else {
            wrong++;
          }
        }
      }
      const score = correct * 4 - wrong * 1;
      subjectStats[subject] = { correct, wrong, skipped, score };
      totalCorrect += correct;
      totalWrong += wrong;
      totalSkipped += skipped;
      totalScore += score;
    }

    leaderboard.push({
      name: file.displayName || file.name.replace(/\.[^/.]+$/, ""),
      data: file.data,
      totalScore,
      totalCorrect,
      totalWrong,
      totalSkipped,
      attempted: totalCorrect + totalWrong,
      subjects: subjectStats,
    });
  }

  leaderboard.sort((a, b) => b.totalScore - a.totalScore);
  state.leaderboard = leaderboard;
  state.examName = examName;

  const scores = leaderboard.map((s) => s.totalScore);
  document.getElementById("stat-total").innerText = leaderboard.length;
  document.getElementById("stat-avg").innerText = scores.length
    ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length)
    : "--";
  document.getElementById("stat-top").innerText = scores.length
    ? Math.max(...scores)
    : "--";
  document.getElementById("export-buttons").classList.remove("hidden");
  btn.innerHTML = '<i data-lucide="check-circle-2"></i> Done';
  setStatus(`Scored ${leaderboard.length} students`);
  renderLeaderboard();
  lucide.createIcons();
}

function downloadLeaderboard() {
  if (!state.leaderboard || state.leaderboard.length === 0) {
    setStatus("Calculate first");
    return;
  }
  const subjects = Object.keys(state.leaderboard[0].subjects || {});
  let csv = "Rank,Name,Total Score,Attempted,Correct,Wrong,Skipped";
  subjects.forEach((s) => (csv += `,${s}`));
  csv += "\n";

  state.leaderboard.forEach((s, i) => {
    csv += `${i + 1},"${s.name}",${s.totalScore},${s.attempted},${s.totalCorrect},${s.totalWrong},${s.totalSkipped}`;
    subjects.forEach(
      (sub) => (csv += `,${(s.subjects[sub] || {}).score || 0}`),
    );
    csv += "\n";
  });

  const blob = new Blob([csv], { type: "text/csv" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${state.examName}_Leaderboard.csv`;
  a.click();
  setStatus("Leaderboard CSV downloaded");
}

async function downloadLeaderboardPDF() {
  if (!state.leaderboard || state.leaderboard.length === 0) {
    setStatus("Calculate first");
    return;
  }

  try {
    setStatus("Preparing leaderboard...");
    const res = await fetch(`/template/leaderboard`);
    const { template } = await res.json();

    const today = new Date().toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "short",
      year: "numeric",
    });

    let html = template;
    html = html.replace(/{{EXAM_NAME}}/g, state.examName.toUpperCase());
    html = html.replace(/{{LOGO_B64}}/g, state.logoB64);
    let examTypeStr = "NEET AITS";
    if (state.examType === "JEE") examTypeStr = "JEE MAINS";
    else if (state.examType.startsWith("JEE_ADV")) examTypeStr = "JEE ADVANCED";

    html = html.replace(/{{EXAM_TYPE}}/g, examTypeStr);
    html = html.replace(/{{DATE}}/g, today);

    let subj1 = "Physics",
      subj2 = "Chemistry",
      subj3 = "Biology";
    
    if (state.examType === "JEE") {
      subj3 = "Maths";
    } else if (state.examType.startsWith("JEE_ADV")) {
      subj1 = "Maths";
      subj2 = "Physics";
      subj3 = "Chemistry";
    }

    html = html.replace(/{{SUBJ1}}/g, subj1);
    html = html.replace(/{{SUBJ2}}/g, subj2);
    html = html.replace(/{{SUBJ3}}/g, subj3);

    let rowsHtml = "";
    state.leaderboard.forEach((student, i) => {
      let score1, score2, score3;
      
      const getScore = (subStr) => student.subjects[Object.keys(student.subjects).find((k) => k.toLowerCase().includes(subStr))]?.score ?? "--";

      if (state.examType.startsWith("JEE_ADV")) {
        score1 = getScore("math");
        score2 = getScore("physics");
        score3 = getScore("chemistry");
      } else {
        score1 = getScore("physics");
        score2 = getScore("chemistry");
        
        if (state.examType === "JEE") {
          score3 = getScore("math");
        } else {
          const bio1 = getScore("biology i");
          const bio2 = getScore("biology ii");
          const bioOnly = getScore("biology");
          score3 = bioOnly !== "--" ? bioOnly : (bio1 !== "--" ? bio1 : 0) + (bio2 !== "--" ? bio2 : 0);
        }
      }

      let maxScore = 720;
      if (state.examType === "JEE") maxScore = 300;
      else if (state.examType.startsWith("JEE_ADV")) maxScore = 216; // 54 questions * 4

      const pct = ((student.totalScore / maxScore) * 100).toFixed(1) + "%";

      rowsHtml += `<tr>
                <td class="rank-col">${i + 1}</td>
                <td class="name-col">${student.name}</td>
                <td class="score-col">${student.totalScore}</td>
                <td class="pct-col">${pct}</td>
                <td class="subj-col">${score1}</td>
                <td class="subj-col">${score2}</td>
                <td class="subj-col">${score3}</td>
                <td class="stat-col">${student.attempted}</td>
                <td class="stat-col">${student.totalCorrect}</td>
                <td class="stat-col">${student.totalWrong}</td>
            </tr>`;
    });

    html = html.replace("{{ROWS}}", rowsHtml);

    setStatus("Generating PDF on server...");
    const pdfRes = await fetch("http://localhost:8000/generate-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        html: html,
        exam_name: state.examName + "_Leaderboard",
      }),
    });

    if (!pdfRes.ok) throw new Error("PDF conversion failed");

    const blob = await pdfRes.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${state.examName}_Leaderboard.pdf`;
    a.click();
    setStatus("Leaderboard PDF downloaded successfully");
  } catch (err) {
    console.error(err);
    setStatus("Failed to generate leaderboard PDF: " + err.message);
  }
}

async function downloadScoreCards() {
  if (!state.leaderboard || state.leaderboard.length === 0) {
    setStatus("Calculate first");
    return;
  }
  setStatus("Fetching scorecard template...");

  try {
    const res = await fetch(`/template/${state.examType}`);
    const { template } = await res.json();
    const today = new Date().toLocaleDateString("en-IN");

    const styleMatch = template.match(/<style>([\s\S]*?)<\/style>/i);
    let styles = styleMatch ? styleMatch[1] : "";
    
    // Minimal styles for multi-page export
    styles += `
        body { display: block !important; margin: 0 !important; padding: 0 !important; background: #fff !important; }
        .pdf-page-wrapper { width: 100%; page-break-after: always; }
        .pdf-page-wrapper:last-child { page-break-after: avoid !important; }
    `;

    let allPagesContent = "";
    for (const student of state.leaderboard) {
      allPagesContent += `<div class="pdf-page-wrapper">${generateScorecardPage(student, template, today)}</div>`;
    }

    await generateAndDownloadPDF(allPagesContent, styles, state.examName + "_Scorecards");
    setStatus("Scorecards downloaded successfully");
    downloadCheckedOMRsJSONZIP();
  } catch (err) {
    console.error(err);
    setStatus("Failed: " + err.message);
  }
}

async function downloadComparisonPDF() {
  if (!state.leaderboard || state.leaderboard.length === 0) {
    setStatus("Calculate first");
    return;
  }
  setStatus("Fetching analysis templates...");

  try {
    const compRes = await fetch(`/template/comparison`);
    const topperRes = await fetch(`/template/topper`);
    const { template: compTemplate } = await compRes.json();
    const { template: topperTemplate } = await topperRes.json();
    const today = new Date().toLocaleDateString("en-IN");
    const classStats = getClassStats();
    const topper = state.leaderboard[0];

    const styleMatch = compTemplate.match(/<style>([\s\S]*?)<\/style>/i);
    let styles = styleMatch ? styleMatch[1] : "";
    styles += `
        body { display: block !important; margin: 0 !important; padding: 0 !important; background: #fff !important; }
        .pdf-page-wrapper { width: 100%; page-break-after: always; }
        .pdf-page-wrapper:last-child { page-break-after: avoid !important; }
    `;

    let allPagesContent = "";
    state.leaderboard.forEach((student, i) => {
      allPagesContent += `<div class="pdf-page-wrapper">${generateAnalysisPage(student, i + 1, topper, classStats, compTemplate, topperTemplate, today)}</div>`;
    });

    await generateAndDownloadPDF(allPagesContent, styles, state.examName + "_Analysis");
    setStatus("Analysis reports downloaded successfully");
  } catch (err) {
    console.error(err);
    setStatus("Failed: " + err.message);
  }
}

async function downloadFullReports() {
  if (!state.leaderboard || state.leaderboard.length === 0) {
    setStatus("Calculate first");
    return;
  }
  setStatus("Fetching all templates...");

  try {
    const [scoreRes, compRes, topperRes] = await Promise.all([
      fetch(`/template/${state.examType}`),
      fetch(`/template/comparison`),
      fetch(`/template/topper`)
    ]);
    
    const { template: scoreTemplate } = await scoreRes.json();
    const { template: compTemplate } = await compRes.json();
    const { template: topperTemplate } = await topperRes.json();
    
    const today = new Date().toLocaleDateString("en-IN");
    const classStats = getClassStats();
    const topper = state.leaderboard[0];

    // Combine styles but keep them isolated
    const scoreStyleMatch = scoreTemplate.match(/<style>([\s\S]*?)<\/style>/i);
    const compStyleMatch = compTemplate.match(/<style>([\s\S]*?)<\/style>/i);
    let styles = (scoreStyleMatch ? scoreStyleMatch[1] : "") + (compStyleMatch ? compStyleMatch[1] : "");
    styles += `
        body { display: block !important; margin: 0 !important; padding: 0 !important; background: #fff !important; }
        .pdf-page-wrapper { 
            width: 100%; 
            page-break-after: always; 
            overflow: visible;
        }
        .pdf-page-wrapper:last-child { page-break-after: avoid !important; }
    `;

    let allPagesContent = "";
    for (let i = 0; i < state.leaderboard.length; i++) {
      const student = state.leaderboard[i];
      // Page 1: Scorecard
      allPagesContent += `<div class="pdf-page-wrapper">${generateScorecardPage(student, scoreTemplate, today)}</div>`;
      // Page 2: Analysis
      allPagesContent += `<div class="pdf-page-wrapper">${generateAnalysisPage(student, i + 1, topper, classStats, compTemplate, topperTemplate, today)}</div>`;
    }

    await generateAndDownloadPDF(allPagesContent, styles, state.examName + "_Full_Reports");
    setStatus("Full combined reports downloaded successfully");
  } catch (err) {
    console.error(err);
    setStatus("Failed: " + err.message);
  }
}

function getClassStats() {
  const stats = {};
  if (!state.leaderboard || state.leaderboard.length === 0) return stats;

  const firstStudent = state.leaderboard[0];
  for (const subject of Object.keys(firstStudent.subjects)) {
    const scores = state.leaderboard.map(s => s.subjects[subject]?.score || 0);
    const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
    stats[subject] = { avg: Math.round(avg * 10) / 10 };
  }
  return stats;
}

function generateScorecardPage(student, template, today) {
  let html = template;
  html = html.replace(/\{\{STUDENT_NAME\}\}/g, student.name);
  html = html.replace(/\{\{DATE\}\}/g, today);
  html = html.replace(/\{\{TOTAL_SCORE\}\}/g, student.totalScore);
  html = html.replace(/\{\{ATTEMPTED\}\}/g, student.attempted);
  html = html.replace(/\{\{RIGHT\}\}/g, student.totalCorrect);
  html = html.replace(/\{\{WRONG\}\}/g, student.totalWrong);
  html = html.replace(/\{\{UNATTEMPTED\}\}/g, student.totalSkipped);

  for (const [subject, stats] of Object.entries(student.subjects)) {
    const key = subject.toUpperCase().replace(/ /g, "_");
    const keySection = state.answerKey[subject] || {};
    const questions = student.data[subject] || {};

    let rowsHtml = "";
    const sortedNums = Object.keys(questions).sort((a, b) => parseInt(a) - parseInt(b));

    for (const qNum of sortedNums) {
      const answer = questions[qNum];
      const correctAns = keySection[qNum] || "";
      let statusClass = "skipped";

      let validAnswers = [];
      if (Array.isArray(correctAns)) {
        correctAns.forEach(item => {
          const parts = String(item).split(",").map(s => s.trim().toUpperCase());
          validAnswers = validAnswers.concat(parts);
        });
      } else {
        validAnswers = String(correctAns).split(",").map(s => s.trim().toUpperCase());
      }
      const isGraceQuestion = validAnswers.includes("*");

      if (isGraceQuestion) {
        statusClass = "correct";
      } else if (answer === "SKIPPED" || answer === "") {
        statusClass = "skipped";
      } else if (answer === "INVALID") {
        statusClass = "invalid";
      } else {
        const studentAnsStr = String(answer).trim().toUpperCase();
        if (validAnswers.includes(studentAnsStr)) statusClass = "correct";
        else statusClass = "wrong";
      }

      rowsHtml += `<tr>
                    <td class="q-num">${qNum}</td>
                    <td class="ans-cell">
                        <span class="status-dot ${statusClass}">${answer === "SKIPPED" || answer === "" ? "—" : answer === "INVALID" ? "INV" : answer}</span>
                    </td>
                    <td class="ans-cell" style="font-weight: 600; color: #64748b;">${correctAns || "—"}</td>
                </tr>`;
    }

    html = html.replace(new RegExp(`\\{\\{${key}_ROWS\\}\\}`, "g"), rowsHtml);
    html = html.replace(new RegExp(`\\{\\{${key}_RIGHT\\}\\}`, "g"), stats.correct);
    html = html.replace(new RegExp(`\\{\\{${key}_WRONG\\}\\}`, "g"), stats.wrong);
    html = html.replace(new RegExp(`\\{\\{${key}_SCORE\\}\\}`, "g"), stats.score);
  }

  html = html.replace(/{{LOGO_B64}}/g, state.logoB64);
  html = html.replace(/\{\{EXAM_NAME\}\}/g, state.examName.toUpperCase());
  const bodyMatch = html.match(/<body[^>]*>([\s\S]*)<\/body>/i);
  const content = bodyMatch ? bodyMatch[1] : "";
  return `<div class="theme-scorecard">${content}</div>`;
}

function generateAnalysisPage(student, rank, topper, classStats, compTemplate, topperTemplate, today) {
  const isTopper = rank === 1;
  let html = isTopper ? topperTemplate : compTemplate;

  const maxScore = state.examType === "JEE" ? 300 : 720;
  const maxSubjScore = state.examType === "JEE" ? 100 : 180;

  html = html.replace(/{{STUDENT_NAME}}/g, student.name);
  html = html.replace(/{{DATE}}/g, today);
  html = html.replace(/{{EXAM_NAME}}/g, state.examName.toUpperCase());
  html = html.replace(/{{EXAM_TYPE}}/g, state.examName.toUpperCase());
  html = html.replace(/{{LOGO_B64}}/g, state.logoB64);
  html = html.replace(/{{TOTAL_SCORE}}/g, student.totalScore + "/" + maxScore);

  const totalQuestions = Object.values(state.answerKey).reduce((acc, subj) => acc + Object.keys(subj).length, 0);
  const totalAccuracy = student.attempted > 0 ? Math.round((student.totalCorrect / student.attempted) * 100) : 0;
  const totalAttemptRate = Math.round((student.attempted / totalQuestions) * 100);

  let weakestSubj = "N/A";
  let minAcc = 101;
  let marksLostWeakest = 0;

  for (const [subj, stats] of Object.entries(student.subjects)) {
    const attempted = stats.correct + stats.wrong;
    const acc = attempted > 0 ? (stats.correct / attempted) * 100 : 0;
    if (acc < minAcc && attempted > 0) {
      minAcc = acc;
      weakestSubj = subj;
      marksLostWeakest = stats.wrong;
    }
  }

  if (isTopper) {
    html = html.replace(/{{ACCURACY}}/g, totalAccuracy);
    html = html.replace(/{{MARKS_LOST}}/g, student.totalWrong);
    html = html.replace(/{{POTENTIAL_SCORE}}/g, student.totalScore + student.totalWrong);
    html = html.replace(/{{MARKS_EARNED}}/g, student.totalCorrect * 4);
    html = html.replace(/{{UNATTEMPTED_POTENTIAL}}/g, student.totalSkipped * 4);
    html = html.split('{{WEAKEST_SUBJECT}}').join(weakestSubj);
    html = html.split('{{WEAKEST_ACCURACY}}').join(Math.round(minAcc));

    let rowsHtml = "";
    for (const [subj, stats] of Object.entries(student.subjects)) {
      const attempted = stats.correct + stats.wrong;
      const acc = attempted > 0 ? Math.round((stats.correct / attempted) * 100) : 0;
      const qInSubj = Object.keys(state.answerKey[subj] || {}).length;
      const attRate = qInSubj > 0 ? Math.round((attempted / qInSubj) * 100) : 0;
      
      rowsHtml += `<tr>
                <td>${subj}</td>
                <td><b>${stats.score}/${maxSubjScore}</b></td>
                <td>${acc}%</td>
                <td>${attRate}%</td>
                <td style="color: var(--danger)">${stats.wrong}</td>
                <td style="color: var(--warning)">${stats.skipped}</td>
            </tr>`;
    }
    html = html.replace(/{{ROWS}}/g, rowsHtml);
  } else {
    html = html.replace(/{{RANK}}/g, rank);
    html = html.replace(/{{CLASS_AVG}}/g, Math.round(state.leaderboard.reduce((a, b) => a + b.totalScore, 0) / state.leaderboard.length));
    html = html.replace(/{{TOPPER_SCORE}}/g, topper.totalScore);
    html = html.replace(/{{SCORE_GAP}}/g, topper.totalScore - student.totalScore);
    html = html.replace(/{{ACCURACY}}/g, totalAccuracy);
    html = html.replace(/{{ATTEMPT_RATE}}/g, totalAttemptRate);
    html = html.replace(/{{POTENTIAL_SCORE}}/g, student.totalScore + student.totalWrong);
    html = html.replace(/{{MARKS_EARNED}}/g, student.totalCorrect * 4);
    html = html.replace(/{{MARKS_LOST}}/g, student.totalWrong);
    html = html.split('{{WEAKEST_SUBJECT}}').join(weakestSubj);
    html = html.split('{{WEAKEST_SCORE}}').join(student.subjects[weakestSubj]?.score || 0);
    html = html.split('{{TOPPER_WEAKEST_SCORE}}').join(topper.subjects[weakestSubj]?.score || 0);
    html = html.split('{{MARKS_LOST_WEAKEST}}').join(marksLostWeakest);

    let rowsHtml = "";
    for (const [subj, stats] of Object.entries(student.subjects)) {
      const topStats = topper.subjects[subj] || { score: 0 };
      const avg = classStats[subj]?.avg || 0;
      const attempted = stats.correct + stats.wrong;
      const acc = attempted > 0 ? Math.round((stats.correct / attempted) * 100) : 0;
      const qInSubj = Object.keys(state.answerKey[subj] || {}).length;
      const attRate = qInSubj > 0 ? Math.round((attempted / qInSubj) * 100) : 0;
      
      let statusTag = '<span class="tag tag-avg">Average</span>';
      if (stats.score > avg + 10) statusTag = '<span class="tag tag-strong">Strong</span>';
      else if (stats.score < avg - 10) statusTag = '<span class="tag tag-weak">Weak</span>';

      rowsHtml += `<tr>
                <td>${subj}</td>
                <td><b>${stats.score}/${maxSubjScore}</b></td>
                <td style="color: var(--success)">${topStats.score}/${maxSubjScore}</td>
                <td>${avg}/${maxSubjScore}</td>
                <td>${acc}%</td>
                <td>${attRate}%</td>
                <td>${statusTag}</td>
            </tr>`;
    }
    html = html.replace(/{{ROWS}}/g, rowsHtml);
  }

  const bodyMatch = html.match(/<body[^>]*>([\s\S]*)<\/body>/i);
  const content = bodyMatch ? bodyMatch[1] : "";
  return `<div class="theme-analysis">${content}</div>`;
}

async function generatePDFBlob(htmlContent, styles, filename) {
  const finalHtml = `<!DOCTYPE html><html><head><meta charset="UTF-8">
            <title>${filename}</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
            <style>
                @page { size: A4; margin: 0; }
                ${styles}
            </style>
        </head><body>${htmlContent}</body></html>`;

  const pdfRes = await fetch("http://localhost:8000/generate-pdf", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ html: finalHtml, exam_name: filename }),
  });

  if (!pdfRes.ok) throw new Error("PDF conversion failed");
  return await pdfRes.blob();
}

async function generateAndDownloadPDF(htmlContent, styles, filename) {
  const blob = await generatePDFBlob(htmlContent, styles, filename);
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${filename}.pdf`;
  a.click();
}

function setStatus(text) {
  document.getElementById("status-text").innerText = text;
}

/* ===== NEW: INDIVIDUAL REPORTS & LEADERBOARD ACTIONS ===== */

function renderLeaderboard() {
  const container = document.getElementById("leaderboard-details-container");
  const tbody = document.getElementById("leaderboard-rows");
  
  if (!state.leaderboard || state.leaderboard.length === 0) {
    container.classList.add("hidden");
    return;
  }
  
  container.classList.remove("hidden");
  tbody.innerHTML = "";
  
  state.leaderboard.forEach((student, index) => {
    const rank = index + 1;
    const attempted = student.attempted;
    const accuracy = attempted > 0 ? Math.round((student.totalCorrect / attempted) * 100) : 0;
    
    let rankBadgeClass = "rank-other";
    if (rank === 1) rankBadgeClass = "rank-badge rank-1";
    else if (rank === 2) rankBadgeClass = "rank-badge rank-2";
    else if (rank === 3) rankBadgeClass = "rank-badge rank-3";
    
    const tr = document.createElement("tr");
    tr.dataset.name = student.name.toLowerCase();
    tr.innerHTML = `
      <td><span class="${rankBadgeClass}">${rank}</span></td>
      <td style="font-weight: 600;">${student.name}</td>
      <td style="font-weight: 700; color: var(--primary);">${student.totalScore}</td>
      <td>${accuracy}%</td>
      <td style="color: var(--success); font-weight: 600;">${student.totalCorrect}</td>
      <td style="color: var(--danger); font-weight: 600;">${student.totalWrong}</td>
      <td style="color: var(--text-muted);">${student.totalSkipped}</td>
      <td style="text-align: right; display: flex; gap: 0.5rem; justify-content: flex-end;">
        <button class="btn-action" onclick="downloadIndividualReport(${index})">
          <i data-lucide="download"></i> Report
        </button>
        <button class="btn-action" onclick="downloadIndividualJSON(${index})">
          <i data-lucide="file-json"></i> JSON
        </button>
      </td>
    `;
    tbody.appendChild(tr);
  });
  
  // Clear search input on render
  const searchInput = document.getElementById("student-search");
  if (searchInput) searchInput.value = "";
  
  lucide.createIcons();
}

function filterLeaderboard(query) {
  const lowerQuery = query.toLowerCase().trim();
  const rows = document.querySelectorAll("#leaderboard-rows tr");
  
  rows.forEach(row => {
    const name = row.dataset.name || "";
    if (name.includes(lowerQuery)) {
      row.classList.remove("hidden");
    } else {
      row.classList.add("hidden");
    }
  });
}

async function downloadIndividualReport(index) {
  const student = state.leaderboard[index];
  if (!student) return;
  
  setStatus(`Generating report for ${student.name}...`);
  try {
    const [scoreRes, compRes, topperRes] = await Promise.all([
      fetch(`/template/${state.examType}`),
      fetch(`/template/comparison`),
      fetch(`/template/topper`)
    ]);
    
    const { template: scoreTemplate } = await scoreRes.json();
    const { template: compTemplate } = await compRes.json();
    const { template: topperTemplate } = await topperRes.json();
    
    const today = new Date().toLocaleDateString("en-IN");
    const classStats = getClassStats();
    const topper = state.leaderboard[0];

    const scoreStyleMatch = scoreTemplate.match(/<style>([\s\S]*?)<\/style>/i);
    const compStyleMatch = compTemplate.match(/<style>([\s\S]*?)<\/style>/i);
    let styles = (scoreStyleMatch ? scoreStyleMatch[1] : "") + (compStyleMatch ? compStyleMatch[1] : "");
    styles += `
        body { display: block !important; margin: 0 !important; padding: 0 !important; background: #fff !important; }
        .pdf-page-wrapper { 
            width: 100%; 
            page-break-after: always; 
            overflow: visible;
        }
        .pdf-page-wrapper:last-child { page-break-after: avoid !important; }
    `;

    let allPagesContent = "";
    // Page 1: Scorecard
    allPagesContent += `<div class="pdf-page-wrapper">${generateScorecardPage(student, scoreTemplate, today)}</div>`;
    // Page 2: Analysis (Topper if rank is 1, comparison for others)
    allPagesContent += `<div class="pdf-page-wrapper">${generateAnalysisPage(student, index + 1, topper, classStats, compTemplate, topperTemplate, today)}</div>`;

    await generateAndDownloadPDF(allPagesContent, styles, `${student.name}_Report`);
    setStatus(`Report for ${student.name} downloaded successfully`);
  } catch (err) {
    console.error(err);
    alert("Report generation failed: " + err.message);
    setStatus("Failed: " + err.message);
  }
}

async function downloadAllIndividualZIP() {
  if (!state.leaderboard || state.leaderboard.length === 0) {
    setStatus("Calculate first");
    return;
  }
  
  const loader = document.getElementById("global-loader");
  const loaderTitle = document.getElementById("global-loader-title");
  const loaderMsg = document.getElementById("global-loader-msg");
  const loaderProgress = document.getElementById("global-loader-progress");
  
  loader.classList.remove("hidden");
  loaderTitle.innerText = "Generating ZIP Archive";
  loaderMsg.innerText = `Starting report generation for ${state.leaderboard.length} students...`;
  loaderProgress.style.width = "0%";
  
  try {
    const [scoreRes, compRes, topperRes] = await Promise.all([
      fetch(`/template/${state.examType}`),
      fetch(`/template/comparison`),
      fetch(`/template/topper`)
    ]);
    
    const { template: scoreTemplate } = await scoreRes.json();
    const { template: compTemplate } = await compRes.json();
    const { template: topperTemplate } = await topperRes.json();
    
    const today = new Date().toLocaleDateString("en-IN");
    const classStats = getClassStats();
    const topper = state.leaderboard[0];

    const scoreStyleMatch = scoreTemplate.match(/<style>([\s\S]*?)<\/style>/i);
    const compStyleMatch = compTemplate.match(/<style>([\s\S]*?)<\/style>/i);
    let styles = (scoreStyleMatch ? scoreStyleMatch[1] : "") + (compStyleMatch ? compStyleMatch[1] : "");
    styles += `
        body { display: block !important; margin: 0 !important; padding: 0 !important; background: #fff !important; }
        .pdf-page-wrapper { 
            width: 100%; 
            page-break-after: always; 
            overflow: visible;
        }
        .pdf-page-wrapper:last-child { page-break-after: avoid !important; }
    `;

    const zip = new JSZip();
    const total = state.leaderboard.length;

    for (let i = 0; i < total; i++) {
      const student = state.leaderboard[i];
      loaderMsg.innerText = `Generating PDF for ${student.name} (${i + 1}/${total})...`;
      loaderProgress.style.width = `${Math.round((i / total) * 100)}%`;

      let allPagesContent = "";
      // Page 1: Scorecard
      allPagesContent += `<div class="pdf-page-wrapper">${generateScorecardPage(student, scoreTemplate, today)}</div>`;
      // Page 2: Analysis (Topper if rank is 1, comparison for others)
      allPagesContent += `<div class="pdf-page-wrapper">${generateAnalysisPage(student, i + 1, topper, classStats, compTemplate, topperTemplate, today)}</div>`;

      const pdfBlob = await generatePDFBlob(allPagesContent, styles, `${student.name}_Report`);
      zip.file(`${i + 1}_${student.name}_Report.pdf`, pdfBlob);
    }

    loaderMsg.innerText = "Compressing files into ZIP archive...";
    loaderProgress.style.width = "95%";

    const content = await zip.generateAsync({ type: "blob" });
    saveAs(content, `${state.examName}_Student_Reports.zip`);

    loaderProgress.style.width = "100%";
    setStatus("ZIP download started successfully!");
    setTimeout(() => {
      loader.classList.add("hidden");
    }, 1000);
  } catch (err) {
    console.error(err);
    alert("ZIP Generation failed: " + err.message);
    loader.classList.add("hidden");
    setStatus("Failed to generate ZIP: " + err.message);
  }
}

/* ===== NEW DOWNLOAD JSON FUNCTIONS ===== */

function downloadActiveOMRJSON() {
  if (state.currentFileIndex === -1) {
    alert("No OMR sheet selected.");
    return;
  }
  const file = state.files[state.currentFileIndex];
  const name = file.displayName || file.name.replace(/\.[^/.]+$/, "");
  
  const jsonData = {
    student_name: name,
    exam_type: state.examType,
    calibration: {
      x_shift: file.x,
      y_shift: file.y
    },
    answers: file.data
  };
  
  const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${name}_OMR_Data.json`;
  a.click();
  setStatus(`JSON for ${name} downloaded`);
}

function downloadCheckedOMRsJSONZIP() {
  if (!state.files || state.files.length === 0) {
    alert("No OMR files processed.");
    return;
  }
  
  try {
    setStatus("Generating OMR JSON ZIP...");
    const zip = new JSZip();
    
    state.files.forEach((file, idx) => {
      const name = file.displayName || file.name.replace(/\.[^/.]+$/, "");
      const jsonData = {
        student_name: name,
        exam_type: state.examType,
        calibration: {
          x_shift: file.x,
          y_shift: file.y
        },
        answers: file.data
      };
      
      if (state.leaderboard && state.leaderboard.length > 0) {
        const scoreInfo = state.leaderboard.find(l => l.name === name);
        if (scoreInfo) {
          jsonData.score_summary = {
            total_score: scoreInfo.totalScore,
            total_correct: scoreInfo.totalCorrect,
            total_wrong: scoreInfo.totalWrong,
            total_skipped: scoreInfo.totalSkipped,
            attempted: scoreInfo.attempted,
            subjects: scoreInfo.subjects
          };
        }
      }
      zip.file(`${idx + 1}_${name}_OMR_Data.json`, JSON.stringify(jsonData, null, 2));
    });
    
    zip.generateAsync({ type: "blob" }).then((content) => {
      saveAs(content, `${state.examName || "Checked"}_OMR_JSON_Data.zip`);
      setStatus("OMR JSON ZIP downloaded successfully!");
    });
  } catch (err) {
    console.error(err);
    alert("JSON ZIP generation failed: " + err.message);
    setStatus("Failed to generate JSON ZIP");
  }
}

function downloadIndividualJSON(index) {
  const student = state.leaderboard[index];
  if (!student) return;
  
  const file = state.files.find(f => (f.displayName || f.name.replace(/\.[^/.]+$/, "")) === student.name);
  const x_shift = file ? file.x : 0;
  const y_shift = file ? file.y : 0;
  
  const jsonData = {
    student_name: student.name,
    exam_type: state.examType,
    calibration: {
      x_shift: x_shift,
      y_shift: y_shift
    },
    answers: student.data,
    score_summary: {
      total_score: student.totalScore,
      total_correct: student.totalCorrect,
      total_wrong: student.totalWrong,
      total_skipped: student.totalSkipped,
      attempted: student.attempted,
      subjects: student.subjects
    }
  };
  
  const blob = new Blob([JSON.stringify(jsonData, null, 2)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `${student.name}_OMR_Data.json`;
  a.click();
  setStatus(`JSON for ${student.name} downloaded`);
}

