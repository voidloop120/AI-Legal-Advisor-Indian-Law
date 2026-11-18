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
// 3. Law & Section Explorer (Phase 3)
// ========================================================

const lawModal = document.getElementById("lawExplorerModal");
const closeLawModalBtn = document.getElementById("closeLawModalBtn");
const closeLawModalFooterBtn = document.getElementById("closeLawModalFooterBtn");
const lawSearchInput = document.getElementById("lawSearchInput");
const actTabsContainer = document.getElementById("actTabsContainer");
const lawListContainer = document.getElementById("lawListContainer");
const lawResultsCount = document.getElementById("lawResultsCount");

let selectedActFilter = ""; // Empty string means "All Acts"

/**
 * Opens the Law Explorer modal with an optional search term.
 */
function openLawExplorer(initialSearch = "") {
  if (!lawModal) return;
  lawModal.style.display = "flex";

  if (lawSearchInput) {
    lawSearchInput.value = initialSearch;
    lawSearchInput.focus();
  }

  loadLaws(selectedActFilter, initialSearch);
}

/**
 * Closes the Law Explorer modal.
 */
function closeLawExplorer() {
  if (lawModal) lawModal.style.display = "none";
}

/**
 * Fetches laws from GET /api/laws with optional act filter and search query.
 */
async function loadLaws(act = "", search = "") {
  if (!lawListContainer) return;

  lawListContainer.innerHTML = `
    <div style="padding: 24px; text-align: center; color: var(--muted);">
      <p>Searching Indian legal provisions...</p>
    </div>
  `;

  try {
    const params = new URLSearchParams();
    if (act) params.append("act", act);
    if (search) params.append("search", search);

    const url = `${API_BASE}/api/laws?${params.toString()}`;
    const response = await fetch(url);

    if (!response.ok) {
      throw new Error(`Failed to load laws: ${response.statusText}`);
    }

    const data = await response.json();
    const laws = data.laws || [];

    if (lawResultsCount) {
      const actLabel = act ? ` under ${act}` : "";
      const searchLabel = search ? ` matching "${search}"` : "";
      lawResultsCount.textContent = `Found ${laws.length} legal provision${laws.length === 1 ? "" : "s"}${actLabel}${searchLabel}`;
    }

    if (laws.length === 0) {
      lawListContainer.innerHTML = `
        <div style="padding: 32px; text-align: center; color: var(--muted); background: #f8fafc; border-radius: 8px;">
          <p style="font-weight: 600; color: var(--text);">No matching legal provisions found.</p>
          <p style="font-size: 13px; margin-top: 6px;">Try searching for broad terms like "theft", "bail", "cheating", "electronic evidence", or "refund".</p>
          <p style="font-size: 11px; margin-top: 12px; color: #92400e;">⚠️ The system only returns verified statutory law and does not invent ungrounded sections.</p>
        </div>
      `;
      return;
    }

    // Render law cards
    lawListContainer.innerHTML = laws.map(item => {
      const actClass = `act-${(item.act_short || "").toLowerCase()}`;

      // Badge classes
      let cognizableBadge = "";
      if (item.cognizable.toLowerCase().includes("cognizable") && !item.cognizable.toLowerCase().includes("non")) {
        cognizableBadge = `<span class="badge badge-cognizable">${item.cognizable}</span>`;
      } else if (item.cognizable.toLowerCase().includes("non-cognizable")) {
        cognizableBadge = `<span class="badge badge-non-cognizable">${item.cognizable}</span>`;
      } else {
        cognizableBadge = `<span class="badge badge-neutral">${item.cognizable}</span>`;
      }

      let bailableBadge = "";
      if (item.bailable.toLowerCase().includes("non-bailable")) {
        bailableBadge = `<span class="badge badge-non-bailable">${item.bailable}</span>`;
      } else if (item.bailable.toLowerCase().includes("bailable")) {
        bailableBadge = `<span class="badge badge-bailable">${item.bailable}</span>`;
      } else {
        bailableBadge = `<span class="badge badge-neutral">${item.bailable}</span>`;
      }

      const keywordsHtml = (item.keywords || [])
        .map(kw => `<span class="keyword-tag">#${kw}</span>`)
        .join(" ");

      return `
        <article class="law-card ${actClass}">
          <div class="law-card-header">
            <div class="law-card-title-group">
              <span class="law-card-act">${item.act_short} • ${item.act}</span>
              <h4>${item.section}: ${item.title}</h4>
            </div>
            <div class="law-badges">
              ${cognizableBadge}
              ${bailableBadge}
            </div>
          </div>
          <p class="law-card-desc">${item.description}</p>
          <div class="law-card-punishment">
            <strong>⏳ Legal Consequence / Punishment:</strong> ${item.punishment}
          </div>
          <div class="law-keywords">
            ${keywordsHtml}
          </div>
        </article>
      `;
    }).join("");

  } catch (error) {
    console.error("Error loading laws:", error);
    lawListContainer.innerHTML = `
      <p style="padding: 16px; color: #dc2626; text-align: center;">
        Failed to load legal provisions from server. Make sure FastAPI backend is active.
      </p>
    `;
  }
}

// Attach event handlers for Law Explorer
document.getElementById("cardLawExplorer")?.addEventListener("click", function (e) {
  e.preventDefault();
  openLawExplorer();
});

document.getElementById("navLawExplorer")?.addEventListener("click", function (e) {
  e.preventDefault();
  openLawExplorer();
});

closeLawModalBtn?.addEventListener("click", closeLawExplorer);
closeLawModalFooterBtn?.addEventListener("click", closeLawExplorer);

// Close on outside backdrop click
window.addEventListener("click", function (event) {
  if (event.target === lawModal) {
    closeLawExplorer();
  }
});

// Live search input with debouncing
let lawSearchDebounceTimer = null;
lawSearchInput?.addEventListener("input", function () {
  clearTimeout(lawSearchDebounceTimer);
  lawSearchDebounceTimer = setTimeout(() => {
    loadLaws(selectedActFilter, lawSearchInput.value.trim());
  }, 300);
});

// Act filter tabs handling
actTabsContainer?.querySelectorAll(".act-tab").forEach(tab => {
  tab.addEventListener("click", function () {
    actTabsContainer.querySelectorAll(".act-tab").forEach(t => t.classList.remove("active"));
    this.classList.add("active");
    selectedActFilter = this.getAttribute("data-act") || "";
    loadLaws(selectedActFilter, lawSearchInput ? lawSearchInput.value.trim() : "");
  });
});

// ========================================================
// 4. Global Search & Sidebar Navigation
// ========================================================

const searchInput = document.getElementById("searchInput");
searchInput?.addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    const query = searchInput.value.trim();
    if (!query) {
      alert("Please enter a legal search or question.");
      return;
    }
    // Seamlessly open the Law & Section Explorer with the searched query!
    openLawExplorer(query);
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
  if (card.id === "cardStartNewCase" || card.id === "cardLawExplorer") return; // Handled

  card.addEventListener("click", function () {
    const title = this.querySelector("h3")?.textContent || "Feature";
    alert(`${title}\n\nThis feature will be connected in an upcoming phase.`);
  });
});

// Initial boot
document.addEventListener("DOMContentLoaded", () => {
  loadCases();
});
