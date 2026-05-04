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
}

function updateNavigation() {
  const btnNext = document.getElementById("btn-next");
  const btnBack = document.getElementById("btn-back");
  btnBack.disabled = state.currentStep === 1;
  if (state.currentStep === 1) btnNext.disabled = !state.examType;
  else if (state.currentStep === 2) btnNext.disabled = state.files.length === 0;
  else btnNext.disabled = false;
}

// Step 1
async function selectExam(type) {
  if (state.examType && state.examType !== type && state.files.length > 0) {
    if (
      !confirm(
        "Switching exam types will clear your current batch and delete processed images from server. Continue?",
      )
    )
      return;
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
    if (c.innerText.includes(type)) c.classList.add("selected");
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
async function handleFiles(e) {
  const files = e.target.files;
  if (files.length === 0) return;

  const formData = new FormData();
  formData.append("exam_type", state.examType);
  for (let file of files) formData.append("files", file);

  setStatus("Uploading and processing batch...");
  document.getElementById("loader").classList.remove("hidden");

  try {
    const response = await fetch("http://localhost:8000/upload", {
      method: "POST",
      body: formData,
    });
    const data = await response.json();

    if (data.status === "success") {
      const newFiles = data.results.map((res) => ({
        name: res.filename,
        displayName: res.filename.replace(/\.[^/.]+$/, ""), // Strip extension
        image: res.image,
        data: res.data,
        x: 0,
        y: 0,
        processed: true,
      }));
      state.files = [...state.files, ...newFiles];
      renderFileList();
      updateNavigation();
      if (state.files.length > 0)
        selectFile(state.files.length - newFiles.length);
      setStatus(`Processed ${newFiles.length} files successfully.`);
    }
  } catch (err) {
    setStatus("Error: " + err.message);
  } finally {
    document.getElementById("loader").classList.add("hidden");
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

  document.getElementById("omr-preview").src = file.image;
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
  const numericQs =
    state.examType === "JEE"
      ? [21, 22, 23, 24, 25, 46, 47, 48, 49, 50, 71, 72, 73, 74, 75]
      : [];

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
        let pills = options
          .map((opt) => {
            const selected = answer === opt ? "selected" : "";
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

  // Update visual state
  const row = el.closest(".q-row");
  row.querySelectorAll(".pill").forEach((p) => p.classList.remove("selected"));
  el.classList.add("selected");

  // Remove status badge if it exists
  const badge = row.querySelector(".q-status");
  if (badge) badge.remove();

  // Update data in state
  if (state.currentFileIndex !== -1) {
    state.files[state.currentFileIndex].data[subject][qNum] = opt;
  }
}

function updateNumAnswer(el) {
  const subject = el.dataset.subject;
  const qNum = el.dataset.q;
  const val = el.value.trim() || "SKIPPED";
  if (state.currentFileIndex !== -1) {
    state.files[state.currentFileIndex].data[subject][qNum] = val;
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
      html += `<div class="key-cell">
                <span class="key-cell-q">Q${qNum}</span>
                <span class="key-cell-a">${answer}</span>
            </div>`;
    }
    html += `</div></div>`;
  }
  container.innerHTML = html;
  lucide.createIcons();
}

function clearAnswerKey() {
  state.answerKey = {};
  document.getElementById("key-upload-zone").classList.remove("hidden");
  document.getElementById("key-preview").classList.add("hidden");
  document.getElementById("key-file-input").value = "";
  setStatus("Answer key removed");
}

// Step 4: Calculate on frontend + generate from templates
async function calculateFinal() {
  const examName = document.getElementById("exam-name").value;
  if (!examName) {
    setStatus("Please enter an exam name");
    return;
  }
  if (Object.keys(state.answerKey).length === 0) {
    setStatus("Upload an answer key first (Step 3)");
    return;
  }
  if (state.files.length === 0) {
    setStatus("No processed files available");
    return;
  }

  const btn = document.querySelector("#step-4 .btn-primary");
  btn.innerHTML = '<div class="spinner small"></div> Calculating...';
  btn.disabled = true;
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
        if (answer === "SKIPPED" || answer === "" || answer === "INVALID") {
          skipped++;
        } else {
          const studentAnsStr = String(answer).trim().toUpperCase();
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

          if (
            validAnswers.includes("*") ||
            validAnswers.includes(studentAnsStr)
          ) {
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
    html = html.replace(
      /{{EXAM_TYPE}}/g,
      state.examType === "JEE" ? "JEE MAINS" : "NEET AITS",
    );
    html = html.replace(/{{DATE}}/g, today);

    let subj1 = "Physics",
      subj2 = "Chemistry",
      subj3 = state.examType === "JEE" ? "Maths" : "Biology";
    html = html.replace(/{{SUBJ1}}/g, subj1);
    html = html.replace(/{{SUBJ2}}/g, subj2);
    html = html.replace(/{{SUBJ3}}/g, subj3);

    let rowsHtml = "";
    state.leaderboard.forEach((student, i) => {
      const score1 =
        student.subjects[
          Object.keys(student.subjects).find((k) =>
            k.toLowerCase().includes("physics"),
          )
        ]?.score ?? "--";
      const score2 =
        student.subjects[
          Object.keys(student.subjects).find((k) =>
            k.toLowerCase().includes("chemistry"),
          )
        ]?.score ?? "--";

      let score3 = "--";
      if (state.examType === "JEE") {
        score3 =
          student.subjects[
            Object.keys(student.subjects).find((k) =>
              k.toLowerCase().includes("math"),
            )
          ]?.score ?? "--";
      } else {
        const bio1 =
          student.subjects[
            Object.keys(student.subjects).find((k) =>
              k.toLowerCase().includes("biology i"),
            )
          ]?.score ?? 0;
        const bio2 =
          student.subjects[
            Object.keys(student.subjects).find((k) =>
              k.toLowerCase().includes("biology ii"),
            )
          ]?.score ?? 0;
        const bioOnly =
          student.subjects[
            Object.keys(student.subjects).find(
              (k) => k.toLowerCase() === "biology",
            )
          ]?.score;
        score3 = bioOnly !== undefined ? bioOnly : bio1 + bio2;
      }

      const maxScore = state.examType === "JEE" ? 300 : 720;
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
  setStatus("Fetching report template...");

  try {
    const res = await fetch(`/template/${state.examType}`);
    const { template } = await res.json();
    const today = new Date().toLocaleDateString("en-IN");

    // Extract style from template
    const styleMatch = template.match(/<style>([\s\S]*?)<\/style>/i);
    let styles = styleMatch ? styleMatch[1] : "";

    // CRITICAL FIX: The template uses "body { display: flex; justify-content: center; }"
    // which makes all reports go side-by-side in a combined document.
    // Force body to block and remove centering flex for the combined document
    styles += `
            body { display: block !important; background: #f1f5f9 !important; margin: 0 !important; padding: 0 !important; }
            .pdf-page-wrapper { 
                display: flex; 
                justify-content: center; 
                width: 100%; 
                page-break-after: always; 
            }
            .pdf-page-wrapper:last-child {
                page-break-after: avoid !important;
            }
            .report-paper {
                margin: 0 !important;
                box-shadow: none !important;
            }
            td {
                padding: 4px 2px !important;
            }
            .q-num {
                width: 35px !important;
                padding-left: 5px !important;
            }
            .ans-cell {
                width: 50px !important;
                text-align: center !important;
            }
            th:nth-child(1) { text-align: left !important; padding-left: 5px !important; }
            th:nth-child(2), th:nth-child(3) {
                text-align: center !important;
            }
            table {
                table-layout: fixed;
                width: 100% !important;
            }
        `;

    let allPagesContent = "";

    for (const student of state.leaderboard) {
      let html = template;

      // Fill basic info
      html = html.replace(/\{\{STUDENT_NAME\}\}/g, student.name);
      html = html.replace(/\{\{DATE\}\}/g, today);
      html = html.replace(/\{\{TOTAL_SCORE\}\}/g, student.totalScore);
      html = html.replace(/\{\{ATTEMPTED\}\}/g, student.attempted);
      html = html.replace(/\{\{RIGHT\}\}/g, student.totalCorrect);
      html = html.replace(/\{\{WRONG\}\}/g, student.totalWrong);
      html = html.replace(/\{\{UNATTEMPTED\}\}/g, student.totalSkipped);

      // Fill subjects
      for (const [subject, stats] of Object.entries(student.subjects)) {
        const key = subject.toUpperCase().replace(/ /g, "_");
        const keySection = state.answerKey[subject] || {};
        const questions = student.data[subject] || {};

        let rowsHtml = "";
        const sortedNums = Object.keys(questions).sort(
          (a, b) => parseInt(a) - parseInt(b),
        );

        for (const qNum of sortedNums) {
          const answer = questions[qNum];
          const correctAns = keySection[qNum] || "";
          let statusClass = "skipped";

          if (answer === "SKIPPED" || answer === "") {
            statusClass = "skipped";
          } else if (answer === "INVALID") {
            statusClass = "invalid";
          } else {
            const studentAnsStr = String(answer).trim().toUpperCase();
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

            if (
              validAnswers.includes("*") ||
              validAnswers.includes(studentAnsStr)
            ) {
              statusClass = "correct";
            } else {
              statusClass = "wrong";
            }
          }

          rowsHtml += `<tr>
                        <td class="q-num">${qNum}</td>
                        <td class="ans-cell">
                            <span class="status-dot ${statusClass}">${answer === "SKIPPED" || answer === "" ? "—" : answer === "INVALID" ? "INV" : answer}</span>
                        </td>
                        <td class="ans-cell" style="font-weight: 600; color: #64748b;">${correctAns || "—"}</td>
                    </tr>`;
        }

        html = html.replace(
          new RegExp(`\\{\\{${key}_ROWS\\}\\}`, "g"),
          rowsHtml,
        );
        html = html.replace(
          new RegExp(`\\{\\{${key}_RIGHT\\}\\}`, "g"),
          stats.correct,
        );
        html = html.replace(
          new RegExp(`\\{\\{${key}_WRONG\\}\\}`, "g"),
          stats.wrong,
        );
        html = html.replace(
          new RegExp(`\\{\\{${key}_SCORE\\}\\}`, "g"),
          stats.score,
        );
      }

      // Embed logo
      html = html.replace(/{{LOGO_B64}}/g, state.logoB64);

      // Get body content
      const bodyMatch = html.match(/<body[^>]*>([\s\S]*)<\/body>/i);
      if (bodyMatch) {
        allPagesContent += `<div class="pdf-page-wrapper">${bodyMatch[1]}</div>`;
      }
    }

    const finalHtml = `<!DOCTYPE html><html><head><meta charset="UTF-8">
            <title>${state.examName} - Scorecards</title>
            <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
            <style>${styles}</style>
        </head><body>${allPagesContent}</body></html>`;

    setStatus("Generating PDF on server...");
    const pdfRes = await fetch("http://localhost:8000/generate-pdf", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ html: finalHtml, exam_name: state.examName }),
    });

    if (!pdfRes.ok) throw new Error("PDF conversion failed");

    const blob = await pdfRes.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `${state.examName}_Scorecards.pdf`;
    a.click();
    setStatus("Final PDF Scorecards downloaded successfully");
  } catch (err) {
    console.error(err);
    setStatus("Failed to generate scorecards: " + err.message);
  }
}

function setStatus(text) {
  document.getElementById("status-text").innerText = text;
}
