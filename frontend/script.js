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
// 4. AI Legal Assistant (Chat & Grounded RAG Q&A)
// ========================================================

const aiAssistantModal = document.getElementById("aiAssistantModal");
const navAiAssistant = document.getElementById("navAiAssistant");
const cardAiAssistant = document.getElementById("cardAiAssistant");
const closeAssistantModalBtn = document.getElementById("closeAssistantModalBtn");
const closeAssistantFooterBtn = document.getElementById("closeAssistantFooterBtn");
const assistantForm = document.getElementById("assistantForm");
const assistantQuestionInput = document.getElementById("assistantQuestionInput");
const assistantActFilter = document.getElementById("assistantActFilter");
const chatMessagesContainer = document.getElementById("chatMessagesContainer");
const sendAssistantBtn = document.getElementById("sendAssistantBtn");

function openAssistantModal(initialQuestion = "") {
  if (!aiAssistantModal) return;
  aiAssistantModal.style.display = "flex";
  if (initialQuestion && assistantQuestionInput) {
    assistantQuestionInput.value = initialQuestion;
    handleAssistantSubmit();
  } else if (assistantQuestionInput) {
    setTimeout(() => assistantQuestionInput.focus(), 100);
  }
}

function closeAssistantModal() {
  if (!aiAssistantModal) return;
  aiAssistantModal.style.display = "none";
}

// Open modal triggers
navAiAssistant?.addEventListener("click", (e) => {
  e.preventDefault();
  openAssistantModal();
});

cardAiAssistant?.addEventListener("click", () => {
  openAssistantModal();
});

closeAssistantModalBtn?.addEventListener("click", closeAssistantModal);
closeAssistantFooterBtn?.addEventListener("click", closeAssistantModal);

// Close on backdrop click
aiAssistantModal?.addEventListener("click", (e) => {
  if (e.target === aiAssistantModal) closeAssistantModal();
});

// Quick prompt chip click handlers
document.querySelectorAll(".quick-prompt-chip").forEach(chip => {
  chip.addEventListener("click", function () {
    const promptText = this.getAttribute("data-prompt") || this.textContent;
    if (assistantQuestionInput) {
      assistantQuestionInput.value = promptText;
      handleAssistantSubmit();
    }
  });
});

/**
 * Converts simple markdown formatting (headings, bold, bullets) into clean HTML.
 */
function formatLegalTextToHtml(text) {
  if (!text) return "";
  let html = text
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^- (.*$)/gim, '<li>$1</li>');

  // Convert double newlines to paragraphs
  html = html.split('\n\n').map(p => {
    p = p.trim();
    if (!p) return '';
    if (p.startsWith('<h3>') || p.startsWith('<li>')) return p;
    return `<p>${p.replace(/\n/g, '<br>')}</p>`;
  }).join('');

  return html;
}

/**
 * Handles question submission, calls /api/assistant/ask, and displays response.
 */
async function handleAssistantSubmit(e) {
  if (e) e.preventDefault();
  if (!assistantQuestionInput || !chatMessagesContainer) return;

  const question = assistantQuestionInput.value.trim();
  if (!question) return;

  const actFilter = assistantActFilter ? assistantActFilter.value : null;

  // 1. Render User Message
  const userMsgEl = document.createElement("div");
  userMsgEl.className = "chat-msg user-msg";
  userMsgEl.innerHTML = `
    <div class="msg-avatar">👤</div>
    <div class="msg-body">
      <div class="msg-header">You</div>
      <div class="msg-content">
        <p>${question}</p>
      </div>
    </div>
  `;
  chatMessagesContainer.appendChild(userMsgEl);
  assistantQuestionInput.value = "";

  // 2. Render Loading Indicator
  const loadingId = "loadingMsg_" + Date.now();
  const loadingMsgEl = document.createElement("div");
  loadingMsgEl.className = "chat-msg assistant-msg";
  loadingMsgEl.id = loadingId;
  loadingMsgEl.innerHTML = `
    <div class="msg-avatar">🤖</div>
    <div class="msg-body">
      <div class="msg-header">AI Legal Advisor <span class="badge-neutral">Searching Statutes...</span></div>
      <div class="msg-content">
        <p><em>Reviewing statutory provisions (BNS, BNSS, BSA, CPA) and generating grounded legal information...</em></p>
      </div>
    </div>
  `;
  chatMessagesContainer.appendChild(loadingMsgEl);
  chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;

  // Disable button while processing
  if (sendAssistantBtn) sendAssistantBtn.disabled = true;

  try {
    const response = await fetch(`${API_BASE}/api/assistant/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        question: question,
        act_filter: actFilter || null,
        n_provisions: 3
      })
    });

    if (!response.ok) {
      throw new Error(`Server responded with status ${response.status}`);
    }

    const data = await response.json();

    // 3. Render Citations pills
    let citationsHtml = "";
    if (data.citations && data.citations.length > 0) {
      citationsHtml = `
        <div style="margin-top: 10px; margin-bottom: 6px;">
          <small style="font-weight: 700; color: #475569; display: block; margin-bottom: 4px;">Cited Statutes & Sections:</small>
          ${data.citations.map(c => `
            <span class="citation-pill" title="${c.title || ''}">${c.tag}</span>
          `).join("")}
        </div>
      `;
    }

    // Replace loading placeholder with actual response
    const answerFormatted = formatLegalTextToHtml(data.answer);
    loadingMsgEl.innerHTML = `
      <div class="msg-avatar">⚖️</div>
      <div class="msg-body">
        <div class="msg-header">
          AI Legal Advisor
          <span class="badge-bailable">${data.llm_used || "Knowledge Engine"}</span>
          ${data.provisions_count > 0 ? `<span class="badge-neutral">${data.provisions_count} Section(s) Grounded</span>` : ''}
        </div>
        <div class="msg-content">
          ${answerFormatted}
          ${citationsHtml}
          <p class="disclaimer-note"><em>${data.disclaimer}</em></p>
        </div>
      </div>
    `;

  } catch (err) {
    console.error("Assistant API Error:", err);
    loadingMsgEl.innerHTML = `
      <div class="msg-avatar">⚠️</div>
      <div class="msg-body" style="border-color: #fecaca; background: #fff5f5;">
        <div class="msg-header" style="color: #991b1b;">Connection Error</div>
        <div class="msg-content" style="color: #991b1b;">
          <p>Unable to connect to the legal assistant service: ${err.message}. Please check if the FastAPI backend is running.</p>
        </div>
      </div>
    `;
  } finally {
    if (sendAssistantBtn) sendAssistantBtn.disabled = false;
    chatMessagesContainer.scrollTop = chatMessagesContainer.scrollHeight;
  }
}

assistantForm?.addEventListener("submit", handleAssistantSubmit);

// ========================================================
// 5. FIR Analyzer & Offense Classifier (Phase 5)
// ========================================================

const firAnalyzerModal = document.getElementById("firAnalyzerModal");
const navFirAnalyzer = document.getElementById("navFirAnalyzer");
const cardFirAnalyzer = document.getElementById("cardFirAnalyzer");
const closeFirModalBtn = document.getElementById("closeFirModalBtn");
const closeFirFooterBtn = document.getElementById("closeFirFooterBtn");
const firTextInput = document.getElementById("firTextInput");
const firFileInput = document.getElementById("firFileInput");
const firFileStatus = document.getElementById("firFileStatus");
const analyzeFirSubmitBtn = document.getElementById("analyzeFirSubmitBtn");
const firReportPlaceholder = document.getElementById("firReportPlaceholder");
const firReportContent = document.getElementById("firReportContent");

// Sample FIR Scenarios embedded for instant 1-click testing
const CLIENT_SAMPLE_FIRS = {
  cyber_fraud: "To the Station House Officer, Cyber Crime PS. I, Rahul Sharma, state that on 14 Jan 2026, I received a call from an unknown person posing as a bank executive from SBI. The caller deceived me into believing that my debit card was blocked and fraudulently induced me to share my OTP. Immediately thereafter, an unauthorized transaction of Rs 45,000 was debited from my account. When I asked for a refund, the accused dishonestly misappropriated the amount and switched off their phone. I request registration of an FIR for cheating, online fraud, and dishonest inducement.",
  theft: "To the Inspector of Police. I, Priya Verma, parked my Honda Activa (Registration KA-03-HF-9821) at the Metro Station parking lot on 17 Jan 2026 at 9:00 AM. When I returned in the evening at 6:30 PM, the vehicle was missing. I checked with the security guard and confirmed that an unidentified person moved and took away my two-wheeler dishonestly without my consent. I request you to register an FIR for vehicle theft and recover my stolen property.",
  assault: "To the Station House Officer. On 19 Jan 2026 around 8:00 PM, while returning from the market, my neighbor Mr. Rakesh Verma stopped me over a parking dispute. He made threatening gestures, used abusive language, and used criminal force to push me against a wall. He intentionally caused bodily pain and hurt to my right arm and threatened to harm me further if I complained. Kindly register an FIR for assault, voluntarily causing hurt, and criminal intimidation."
};

function openFirModal() {
  if (!firAnalyzerModal) return;
  firAnalyzerModal.style.display = "flex";
  if (firTextInput) setTimeout(() => firTextInput.focus(), 100);
}

function closeFirModal() {
  if (!firAnalyzerModal) return;
  firAnalyzerModal.style.display = "none";
}

navFirAnalyzer?.addEventListener("click", (e) => {
  e.preventDefault();
  openFirModal();
});

cardFirAnalyzer?.addEventListener("click", () => {
  openFirModal();
});

closeFirModalBtn?.addEventListener("click", closeFirModal);
closeFirFooterBtn?.addEventListener("click", closeFirModal);

firAnalyzerModal?.addEventListener("click", (e) => {
  if (e.target === firAnalyzerModal) closeFirModal();
});

// Sample FIR button handlers
document.getElementById("loadSampleCyberBtn")?.addEventListener("click", () => {
  if (firTextInput) {
    firTextInput.value = CLIENT_SAMPLE_FIRS.cyber_fraud;
    runFirAnalysis(CLIENT_SAMPLE_FIRS.cyber_fraud, "Sample_Cyber_Fraud.txt");
  }
});

document.getElementById("loadSampleTheftBtn")?.addEventListener("click", () => {
  if (firTextInput) {
    firTextInput.value = CLIENT_SAMPLE_FIRS.theft;
    runFirAnalysis(CLIENT_SAMPLE_FIRS.theft, "Sample_Theft.txt");
  }
});

document.getElementById("loadSampleAssaultBtn")?.addEventListener("click", () => {
  if (firTextInput) {
    firTextInput.value = CLIENT_SAMPLE_FIRS.assault;
    runFirAnalysis(CLIENT_SAMPLE_FIRS.assault, "Sample_Assault.txt");
  }
});

// File upload handler (reads .txt file in browser using FileReader)
firFileInput?.addEventListener("change", function () {
  const file = this.files[0];
  if (!file) return;

  if (!file.name.toLowerCase().endsWith(".txt")) {
    alert("Please select a plain text (.txt) file.");
    this.value = "";
    return;
  }

  const reader = new FileReader();
  reader.onload = function (e) {
    const text = e.target.result;
    if (firTextInput) firTextInput.value = text;
    if (firFileStatus) firFileStatus.textContent = `✓ Loaded: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`;
    runFirAnalysis(text, file.name);
  };
  reader.readAsText(file);
});

// Manual analyze submit
analyzeFirSubmitBtn?.addEventListener("click", () => {
  const text = firTextInput ? firTextInput.value.trim() : "";
  if (!text) {
    alert("Please enter or paste FIR complaint text to analyze.");
    return;
  }
  runFirAnalysis(text);
});

/**
 * Sends FIR text to /api/fir/analyze and renders the statutory report.
 */
async function runFirAnalysis(text, fileName = "") {
  if (!text || text.length < 10) {
    alert("FIR text must be at least 10 characters long.");
    return;
  }

  if (analyzeFirSubmitBtn) {
    analyzeFirSubmitBtn.disabled = true;
    analyzeFirSubmitBtn.innerHTML = `<span>Analyzing Statutes...</span> ⏳`;
  }

  if (firReportPlaceholder) firReportPlaceholder.style.display = "none";
  if (firReportContent) {
    firReportContent.style.display = "block";
    firReportContent.innerHTML = `
      <div style="text-align: center; padding: 40px 16px; color: #475569;">
        <span style="font-size: 28px; display: block; margin-bottom: 8px;">⏳</span>
        <p><strong>Mapping allegations to BNS and BNSS statutes...</strong></p>
        <small>Checking cognizable classification, arrest thresholds, and bail rights.</small>
      </div>
    `;
  }

  try {
    const response = await fetch(`${API_BASE}/api/fir/analyze`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: text,
        file_name: fileName || null
      })
    });

    if (!response.ok) {
      throw new Error(`Server returned status ${response.status}`);
    }

    const data = await response.json();
    renderFirReport(data, fileName);

  } catch (err) {
    console.error("FIR Analysis Error:", err);
    if (firReportContent) {
      firReportContent.innerHTML = `
        <div style="background: #fff5f5; border: 1px solid #fecaca; padding: 14px; border-radius: 6px; color: #991b1b;">
          <strong>Error analyzing FIR:</strong> ${err.message}
        </div>
      `;
    }
  } finally {
    if (analyzeFirSubmitBtn) {
      analyzeFirSubmitBtn.disabled = false;
      analyzeFirSubmitBtn.innerHTML = `<span>Analyze FIR & Classify Charges</span> ➔`;
    }
  }
}

/**
 * Renders the structured findings report.
 */
function renderFirReport(data, fileName) {
  if (!firReportContent) return;

  const classification = data.overall_classification || {};
  const isBailable = !classification.is_non_bailable;
  const isCognizable = classification.is_cognizable;

  // Extracted entities row
  let entitiesHtml = "";
  const entities = data.entities_detected || {};
  if (Object.keys(entities).length > 0) {
    entitiesHtml = `
      <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px; padding: 10px 12px; margin-bottom: 12px; font-size: 12px;">
        <strong style="color: #475569; display: block; margin-bottom: 4px;">Detected Case Entities:</strong>
        <div style="display: flex; gap: 8px; flex-wrap: wrap;">
          ${entities.financial_loss ? `<span class="keyword-tag">💰 Financial Loss: <strong>${entities.financial_loss}</strong></span>` : ''}
          ${entities.vehicle_number ? `<span class="keyword-tag">🚗 Vehicle: <strong>${entities.vehicle_number}</strong></span>` : ''}
          ${entities.incident_date ? `<span class="keyword-tag">📅 Incident Date: <strong>${entities.incident_date}</strong></span>` : ''}
          ${fileName ? `<span class="keyword-tag">📄 Source: <strong>${fileName}</strong></span>` : ''}
        </div>
      </div>
    `;
  }

  // Matched BNS sections list
  const sectionsHtml = (data.matched_sections || []).map(s => `
    <div class="fir-section-card">
      <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 4px;">
        <h4 style="margin: 0; color: #0f172a;">${s.act} ${s.section}: ${s.title}</h4>
        <span class="badge ${s.bailable === 'Non-Bailable' ? 'badge-non-bailable' : 'badge-bailable'}">${s.bailable}</span>
      </div>
      <p style="margin: 0 0 6px 0; font-size: 12px; color: #334155;">${s.description || ''}</p>
      <div style="font-size: 11px; color: #475569; background: #ffffff; padding: 6px 8px; border-radius: 4px; border: 1px solid #e2e8f0;">
        ⚖️ <strong>Statutory Penalty:</strong> ${s.punishment || 'As prescribed by law'}
      </div>
    </div>
  `).join("");

  // Citizen Rights list
  const rightsHtml = (data.citizen_rights_and_steps || []).map(r => `
    <li>${r}</li>
  `).join("");

  firReportContent.innerHTML = `
    <!-- Classification Badges -->
    <div class="fir-badge-row">
      <span class="fir-badge ${isCognizable ? 'cognizable' : 'non-cognizable'}">
        ${isCognizable ? '🚨 Cognizable Offense' : 'ℹ️ Non-Cognizable Offense'}
      </span>
      <span class="fir-badge ${isBailable ? 'bailable' : 'non-bailable'}">
        ${isBailable ? '🟢 Bailable (Station/Court)' : '🔴 Non-Bailable (Magistrate Hearing Required)'}
      </span>
    </div>

    ${entitiesHtml}

    <!-- Matched Statutory Offenses -->
    <h4 style="font-size: 13px; color: #0f172a; margin: 12px 0 8px 0;">Applicable Sections under Bharatiya Nyaya Sanhita (BNS):</h4>
    ${sectionsHtml}

    <!-- Police Arrest Power Guidance under BNSS -->
    <div class="fir-guidance-box" style="margin-top: 14px;">
      <strong>👮 Police Arrest Powers (BNSS § 35):</strong>
      ${data.arrest_power_guidance || ''}
    </div>

    <!-- Bail Guidance under BNSS -->
    <div class="fir-guidance-box" style="background: #fefce8; border-color: #fef08a; color: #854d0e;">
      <strong style="color: #713f12;">🏛️ Bail Legal Guidance (BNSS § 479 & § 482):</strong>
      ${data.bail_guidance || ''}
    </div>

    <!-- Citizen Action Checklist -->
    <div style="margin-top: 14px;">
      <h4 style="font-size: 12px; color: #0f172a; margin-bottom: 6px;">Citizen Rights & Procedural Safeguards:</h4>
      <ul class="fir-checklist">
        ${rightsHtml}
      </ul>
    </div>
  `;
}

// ========================================================
// 6. User Authentication & Session Management (Phase 6)
// ========================================================

const AUTH_USER_KEY = "ai_legal_user";
const AUTH_TOKEN_KEY = "ai_legal_token";

const profileAreaBtn = document.getElementById("profileAreaBtn");
const userAvatar = document.getElementById("userAvatar");
const userDisplayName = document.getElementById("userDisplayName");
const authActionLabel = document.getElementById("authActionLabel");
const loginModal = document.getElementById("loginModal");
const closeLoginModalBtn = document.getElementById("closeLoginModalBtn");
const closeLoginModalFooterBtn = document.getElementById("closeLoginModalFooterBtn");
const tabSignInBtn = document.getElementById("tabSignInBtn");
const tabRegisterBtn = document.getElementById("tabRegisterBtn");
const signInForm = document.getElementById("signInForm");
const registerForm = document.getElementById("registerForm");
const loggedInView = document.getElementById("loggedInView");
const fillDemoLoginBtn = document.getElementById("fillDemoLoginBtn");
const logoutBtn = document.getElementById("logoutBtn");
const loginErrorMsg = document.getElementById("loginErrorMsg");
const regErrorMsg = document.getElementById("regErrorMsg");
const demoLoginPrompt = document.getElementById("demoLoginPrompt");

/**
 * Returns current logged-in user from localStorage,
 * or defaults to demo user Ankit Sharma for seamless viva experience.
 */
function getCurrentUser() {
  const stored = localStorage.getItem(AUTH_USER_KEY);
  if (stored) {
    try { return JSON.parse(stored); } catch (e) { return null; }
  }
  // Default demo user profile if nothing stored
  return {
    id: 1,
    username: "ankit",
    full_name: "Ankit Sharma",
    email: "ankit@example.com"
  };
}

/**
 * Updates top-bar header with user avatar, name, and status.
 */
function updateAuthUI() {
  const user = getCurrentUser();
  if (user && userDisplayName && userAvatar) {
    const firstName = user.full_name ? user.full_name.split(" ")[0] : user.username;
    userDisplayName.textContent = `Hello, ${firstName}`;
    userAvatar.textContent = (user.full_name || user.username || "A").charAt(0).toUpperCase();
    if (authActionLabel) authActionLabel.textContent = "Switch / Out";

    // Update modal account view
    const modalAvatar = document.getElementById("modalUserAvatar");
    const modalName = document.getElementById("modalUserName");
    const modalEmail = document.getElementById("modalUserEmail");
    if (modalAvatar) modalAvatar.textContent = (user.full_name || "A").charAt(0).toUpperCase();
    if (modalName) modalName.textContent = user.full_name;
    if (modalEmail) modalEmail.textContent = user.email;
  } else if (userDisplayName && userAvatar) {
    userDisplayName.textContent = "Guest Citizen";
    userAvatar.textContent = "?";
    if (authActionLabel) authActionLabel.textContent = "Sign In";
  }
}

function openLoginModal() {
  if (!loginModal) return;
  loginModal.style.display = "flex";

  const user = getCurrentUser();
  const isExplicitGuest = localStorage.getItem("ai_legal_guest") === "true";

  if (user && !isExplicitGuest) {
    // Show logged-in view
    if (loggedInView) loggedInView.style.display = "block";
    if (signInForm) signInForm.style.display = "none";
    if (registerForm) registerForm.style.display = "none";
    if (demoLoginPrompt) demoLoginPrompt.style.display = "none";
  } else {
    // Show sign-in form
    switchAuthTab("signin");
  }
}

function closeLoginModal() {
  if (!loginModal) return;
  loginModal.style.display = "none";
  if (loginErrorMsg) loginErrorMsg.style.display = "none";
  if (regErrorMsg) regErrorMsg.style.display = "none";
}

function switchAuthTab(tab) {
  if (tab === "signin") {
    tabSignInBtn?.classList.add("active");
    tabRegisterBtn?.classList.remove("active");
    if (signInForm) signInForm.style.display = "block";
    if (registerForm) registerForm.style.display = "none";
    if (loggedInView) loggedInView.style.display = "none";
    if (demoLoginPrompt) demoLoginPrompt.style.display = "flex";
  } else {
    tabSignInBtn?.classList.remove("active");
    tabRegisterBtn?.classList.add("active");
    if (signInForm) signInForm.style.display = "none";
    if (registerForm) registerForm.style.display = "block";
    if (loggedInView) loggedInView.style.display = "none";
    if (demoLoginPrompt) demoLoginPrompt.style.display = "none";
  }
}

// Event Listeners
profileAreaBtn?.addEventListener("click", openLoginModal);
closeLoginModalBtn?.addEventListener("click", closeLoginModal);
closeLoginModalFooterBtn?.addEventListener("click", closeLoginModal);

loginModal?.addEventListener("click", (e) => {
  if (e.target === loginModal) closeLoginModal();
});

tabSignInBtn?.addEventListener("click", () => switchAuthTab("signin"));
tabRegisterBtn?.addEventListener("click", () => switchAuthTab("register"));

// Auto-fill demo credentials
fillDemoLoginBtn?.addEventListener("click", () => {
  const usernameInput = document.getElementById("loginUsername");
  const passwordInput = document.getElementById("loginPassword");
  if (usernameInput) usernameInput.value = "ankit";
  if (passwordInput) passwordInput.value = "legal123";
});

// Handle Sign In Submit
signInForm?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const usernameInput = document.getElementById("loginUsername");
  const passwordInput = document.getElementById("loginPassword");
  const submitBtn = document.getElementById("loginSubmitBtn");

  const username = usernameInput ? usernameInput.value.trim() : "";
  const password = passwordInput ? passwordInput.value : "";
  if (!username || !password) return;

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = "Verifying...";
  }
  if (loginErrorMsg) loginErrorMsg.style.display = "none";

  try {
    const response = await fetch(`${API_BASE}/api/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Authentication failed.");
    }

    // Save user & token in localStorage
    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(data.user));
    localStorage.setItem(AUTH_TOKEN_KEY, data.token);
    localStorage.removeItem("ai_legal_guest");

    updateAuthUI();
    closeLoginModal();
    alert(`Welcome back, ${data.user.full_name}!`);
  } catch (err) {
    if (loginErrorMsg) {
      loginErrorMsg.textContent = err.message;
      loginErrorMsg.style.display = "block";
    }
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Sign In";
    }
  }
});

// Handle Register Submit
registerForm?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const regFullName = document.getElementById("regFullName")?.value.trim();
  const regUsername = document.getElementById("regUsername")?.value.trim();
  const regEmail = document.getElementById("regEmail")?.value.trim();
  const regPassword = document.getElementById("regPassword")?.value;
  const submitBtn = document.getElementById("registerSubmitBtn");

  if (!regFullName || !regUsername || !regEmail || !regPassword) return;

  if (submitBtn) {
    submitBtn.disabled = true;
    submitBtn.textContent = "Creating Account...";
  }
  if (regErrorMsg) regErrorMsg.style.display = "none";

  try {
    const response = await fetch(`${API_BASE}/api/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        full_name: regFullName,
        username: regUsername,
        email: regEmail,
        password: regPassword
      })
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || "Registration failed.");
    }

    localStorage.setItem(AUTH_USER_KEY, JSON.stringify(data.user));
    localStorage.setItem(AUTH_TOKEN_KEY, data.token);
    localStorage.removeItem("ai_legal_guest");

    updateAuthUI();
    closeLoginModal();
    alert(`Account created successfully for ${data.user.full_name}!`);
  } catch (err) {
    if (regErrorMsg) {
      regErrorMsg.textContent = err.message;
      regErrorMsg.style.display = "block";
    }
  } finally {
    if (submitBtn) {
      submitBtn.disabled = false;
      submitBtn.textContent = "Create Account";
    }
  }
});

// Logout Handler
logoutBtn?.addEventListener("click", () => {
  localStorage.removeItem(AUTH_USER_KEY);
  localStorage.removeItem(AUTH_TOKEN_KEY);
  localStorage.setItem("ai_legal_guest", "true");
  updateAuthUI();
  closeLoginModal();
  alert("You have been signed out. You are now browsing as a Guest Citizen.");
});

// ========================================================
// 7. Global Search & Sidebar Navigation
// ========================================================

const searchInput = document.getElementById("searchInput");
searchInput?.addEventListener("keydown", function (event) {
  if (event.key === "Enter") {
    const query = searchInput.value.trim();
    if (!query) {
      alert("Please enter a legal search or question.");
      return;
    }
    // If query looks like an FIR or police matter, open FIR Analyzer!
    if (query.toLowerCase().includes("fir") || query.toLowerCase().includes("stolen") || query.toLowerCase().includes("police report")) {
      openFirModal();
      if (firTextInput) firTextInput.value = query;
      runFirAnalysis(query);
    } else if (query.includes("?") || query.toLowerCase().startsWith("what") || query.toLowerCase().startsWith("how") || query.toLowerCase().startsWith("can")) {
      openAssistantModal(query);
    } else {
      openLawExplorer(query);
    }
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
  if (card.id === "cardStartNewCase" || card.id === "cardLawExplorer" || card.id === "cardAiAssistant" || card.id === "cardFirAnalyzer") return; // Handled

  card.addEventListener("click", function () {
    const title = this.querySelector("h3")?.textContent || "Feature";
    alert(`${title}\n\nThis feature will be connected in an upcoming phase.`);
  });
});

// Initial boot
document.addEventListener("DOMContentLoaded", () => {
  updateAuthUI();
  loadCases();
});



