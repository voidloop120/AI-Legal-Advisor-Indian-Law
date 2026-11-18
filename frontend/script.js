// ========================================================
// AI Legal Advisor - Frontend Client Logic
// Connects UI with FastAPI backend endpoints
// ========================================================

const API_BASE = ""; // Relative URL since backend serves frontend

// Track currently active case ID
let currentSelectedCaseId = null;

// ========================================================
// 1. Case Management (Load & Render Cases)
// ========================================================

/**
 * Fetches all cases from GET /api/cases and displays them in the 'My Cases' panel.
 */
async function loadCases() {
  const container = document.getElementById("casesListContainer");
  if (!container) return;

  try {
    const response = await fetch(`${API_BASE}/api/cases`);
    if (!response.ok) {
      throw new Error(`Failed to load cases: ${response.statusText}`);
    }

    const cases = await response.json();

    if (cases.length === 0) {
      container.innerHTML = `
        <div style="padding: 24px; text-align: center; color: var(--muted);">
          <p>No cases found.</p>
          <button id="emptyStartBtn" style="margin-top: 8px; color: var(--blue); background: none; border: none; cursor: pointer; font-weight: 600;">
            + Click here to start your first case
          </button>
        </div>
      `;
      document.getElementById("emptyStartBtn")?.addEventListener("click", openNewCaseModal);
      return;
    }

    // Render case cards
    container.innerHTML = cases.map(c => {
      // Determine CSS class for the status tag
      let statusClass = "active-status";
      let progressColorClass = "";
      if (c.status === "In Progress") {
        statusClass = "progress-status";
        progressColorClass = "green-progress";
      } else if (c.status === "Closed") {
        statusClass = "closed-status";
        progressColorClass = "purple-progress";
      }

      const isSelected = c.id === currentSelectedCaseId ? "selected" : "";

      return `
        <div class="case-card ${isSelected}" data-case-id="${c.id}">
          <div class="case-top">
            <span class="doc-icon">▤</span>
            <div>
              <h3>Case #${c.case_number}</h3>
              <p>${c.title} | ${c.police_station || c.case_type}</p>
              <small>Current Stage: <strong>${c.current_stage}</strong></small>
            </div>
            <span class="status ${statusClass}">${c.status}</span>
          </div>
          <div class="progress-row">
            <div class="progress">
              <span class="${progressColorClass}" style="width: ${c.progress_percent}%"></span>
            </div>
            <b>${c.progress_percent}%</b>
          </div>
        </div>
      `;
    }).join("");

    // Attach click events to each case card to load its Journey
    container.querySelectorAll(".case-card").forEach(card => {
      card.addEventListener("click", function () {
        const caseId = parseInt(this.getAttribute("data-case-id"), 10);
        selectCase(caseId);
      });
    });

    // If no case is selected yet, select the first one by default
    if (!currentSelectedCaseId && cases.length > 0) {
      selectCase(cases[0].id);
    }

  } catch (error) {
    console.error("Error loading cases:", error);
    container.innerHTML = `
      <p style="padding: 16px; color: #dc2626; text-align: center;">
        Could not connect to backend server. Make sure FastAPI is running.
      </p>
    `;
  }
}

/**
 * Highlights a selected case and loads its timeline stages into the Case Journey panel.
 */
async function selectCase(caseId) {
  currentSelectedCaseId = caseId;

  // Update UI selection outline
  document.querySelectorAll(".case-card").forEach(card => {
    const id = parseInt(card.getAttribute("data-case-id"), 10);
    if (id === caseId) {
      card.classList.add("selected");
    } else {
      card.classList.remove("selected");
    }
  });

  await loadCaseJourney(caseId);
}

/**
 * Fetches GET /api/cases/{caseId} and renders the timeline steps in the 'Case Journey' panel.
 */
async function loadCaseJourney(caseId) {
  const timelineEl = document.getElementById("journeyTimeline");
  const infoEl = document.getElementById("journeyInfo");
  const caseHeaderEl = document.getElementById("journeyCaseNumber");

  if (!timelineEl || !infoEl) return;

  try {
    const response = await fetch(`${API_BASE}/api/cases/${caseId}`);
    if (!response.ok) throw new Error("Failed to load case journey");

    const data = await response.json();

    if (caseHeaderEl) {
      caseHeaderEl.textContent = `Case #${data.case_number} (${data.case_type})`;
    }

    // Render timeline steps
    timelineEl.innerHTML = data.timeline.map(stage => {
      let itemClass = "";
      let dotContent = "";

      if (stage.status === "completed") {
        itemClass = "done";
        dotContent = "✓";
      } else if (stage.status === "current") {
        itemClass = "current";
        dotContent = "";
      }

      return `
        <div class="timeline-item ${itemClass}">
          <span class="dot">${dotContent}</span>
          <div>
            <strong>${stage.stage_name}</strong>
            ${stage.stage_date ? `<small>${stage.stage_date}</small>` : ""}
          </div>
        </div>
      `;
    }).join("");

    // Find current active stage description
    const currentStage = data.timeline.find(s => s.status === "current") || data.timeline[0];
    infoEl.innerHTML = `
      <strong>📍 You are here: ${data.current_stage}</strong>
      <p>${currentStage ? currentStage.description : "Case is under active legal processing."}</p>
      <button onclick="alert('Case Stage: ' + '${data.current_stage}' + '\\n' + '${(currentStage?.description || '').replace(/'/g, "\\'")}')">Know More →</button>
    `;

  } catch (error) {
    console.error("Error loading case journey:", error);
  }
}

// ========================================================
// 2. Start New Case Modal Handling
// ========================================================

const modal = document.getElementById("newCaseModal");
const closeModalBtn = document.getElementById("closeModalBtn");
const cancelModalBtn = document.getElementById("cancelModalBtn");
const newCaseForm = document.getElementById("newCaseForm");

function openNewCaseModal() {
  if (modal) modal.style.display = "flex";
}

function closeNewCaseModal() {
  if (modal) modal.style.display = "none";
  if (newCaseForm) newCaseForm.reset();
}

// Trigger modal from Feature Card or Sidebar Nav
document.getElementById("cardStartNewCase")?.addEventListener("click", function(e) {
  e.preventDefault();
  openNewCaseModal();
});

document.getElementById("navStartNewCase")?.addEventListener("click", function(e) {
  e.preventDefault();
  openNewCaseModal();
});

closeModalBtn?.addEventListener("click", closeNewCaseModal);
cancelModalBtn?.addEventListener("click", closeNewCaseModal);

// Close modal when clicking outside the card
window.addEventListener("click", function (event) {
  if (event.target === modal) {
    closeNewCaseModal();
  }
});

// Submit New Case Form -> POST /api/cases
newCaseForm?.addEventListener("submit", async function (e) {
  e.preventDefault();

  const title = document.getElementById("caseTitle").value.trim();
  const caseType = document.getElementById("caseType").value;
  const policeStation = document.getElementById("policeStation").value.trim();
  const description = document.getElementById("caseDesc").value.trim();

  if (!title) {
    alert("Please enter a case title or FIR number.");
    return;
  }

  const submitBtn = document.getElementById("saveCaseSubmitBtn");
  if (submitBtn) submitBtn.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/api/cases`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title,
        case_type: caseType,
        police_station: policeStation,
        description: description,
      }),
    });

    if (!response.ok) {
      throw new Error(`Failed to create case: ${response.statusText}`);
    }

    const createdCase = await response.json();
    closeNewCaseModal();

    // Select and load the newly created case
    currentSelectedCaseId = createdCase.id;
    await loadCases();
    await selectCase(createdCase.id);

    alert(`Case #${createdCase.case_number} created successfully!`);
  } catch (error) {
    console.error("Error creating case:", error);
    alert("Failed to create case. Please check that the server is running.");
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
});

// Refresh button for cases
document.getElementById("refreshCasesBtn")?.addEventListener("click", function () {
  loadCases();
});

// ========================================================
// 3. Search & Sidebar Navigation
// ========================================================

const searchInput = document.getElementById("searchInput");
searchInput?.addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    const query = searchInput.value.trim();
    if (!query) {
      alert("Please enter a legal search or question.");
      return;
    }
    alert(`Legal Search: "${query}"\n\nFull AI RAG search will be enabled in Phase 3 & 4!`);
  }
});

// Sidebar active toggle
document.querySelectorAll(".sidebar-nav .nav-item").forEach(item => {
  item.addEventListener("click", function () {
    document.querySelectorAll(".sidebar-nav .nav-item").forEach(nav => nav.classList.remove("active"));
    this.classList.add("active");
  });
});

// Fallback click handler for remaining placeholder cards
document.querySelectorAll(".feature-card, .tool-card").forEach(card => {
  if (card.id === "cardStartNewCase") return; // Handled separately

  card.addEventListener("click", function () {
    const title = this.querySelector("h3")?.textContent || "Feature";
    alert(`${title}\n\nThis feature will be connected in an upcoming phase.`);
  });
});

// Initial boot
document.addEventListener("DOMContentLoaded", () => {
  loadCases();
});
