// ---------------------------------------------------------
// KNOW-RAG ENTERPRISE FRONTEND SCRIPT (HTML/CSS/JS)
// ---------------------------------------------------------

const API_BASE_URL = "http://127.0.0.1:8000";

// Session State
let sessionId = crypto.randomUUID ? crypto.randomUUID() : 'sess_' + Date.now();
let chatMessages = [];
let lastRetrievedSources = [];
let isDevModeActive = false;

// DOM Elements
const sidebar = document.getElementById('sidebar');
const closeSidebarBtn = document.getElementById('close-sidebar-btn');
const openSidebarBtn = document.getElementById('open-sidebar-btn');

const citationDrawer = document.getElementById('citation-drawer');
const toggleSourcesBtn = document.getElementById('toggle-sources-btn');
const closeDrawerBtn = document.getElementById('close-drawer-btn');

const newChatBtn = document.getElementById('new-chat-btn');
const refreshIndexBtn = document.getElementById('refresh-index-btn');
const streamingToggle = document.getElementById('streaming-toggle');
const sessionIdDisplay = document.getElementById('session-id-display');

const viewTitle = document.getElementById('view-title');
const viewSubtitle = document.getElementById('view-subtitle');

const standardModeView = document.getElementById('standard-mode-view');
const devModeView = document.getElementById('dev-mode-view');

const devModeBtn = document.getElementById('dev-mode-btn');
const devModeText = document.getElementById('dev-mode-text');

const starterQuestions = document.getElementById('starter-questions');
const messagesContainer = document.getElementById('messages-container');
const drawerChunksContainer = document.getElementById('drawer-chunks-container');

const chatForm = document.getElementById('chat-form');
const userInput = document.getElementById('user-input');

// Initialize App
function initApp() {
  if (sessionIdDisplay) {
    sessionIdDisplay.textContent = sessionId.substring(0, 8) + '...';
  }

  // Dev Mode Toggle managed via onclick attribute in index.html

  // Refresh Index Listener
  if (refreshIndexBtn) {
    refreshIndexBtn.addEventListener('click', handleRefreshIndex);
  }

  // Sidebar Controls
  if (closeSidebarBtn) {
    closeSidebarBtn.addEventListener('click', () => {
      sidebar.classList.add('-ml-72');
      openSidebarBtn.classList.remove('hidden');
    });
  }

  if (openSidebarBtn) {
    openSidebarBtn.addEventListener('click', () => {
      sidebar.classList.remove('-ml-72');
      openSidebarBtn.classList.add('hidden');
    });
  }

  // Citation Drawer Controls
  if (toggleSourcesBtn) {
    toggleSourcesBtn.addEventListener('click', () => {
      citationDrawer.classList.toggle('hidden');
    });
  }

  if (closeDrawerBtn) {
    closeDrawerBtn.addEventListener('click', () => {
      citationDrawer.classList.add('hidden');
    });
  }

  // New Chat Button
  if (newChatBtn) {
    newChatBtn.addEventListener('click', () => {
      sessionId = crypto.randomUUID ? crypto.randomUUID() : 'sess_' + Date.now();
      if (sessionIdDisplay) sessionIdDisplay.textContent = sessionId.substring(0, 8) + '...';
      chatMessages = [];
      messagesContainer.innerHTML = '';
      starterQuestions.classList.remove('hidden');
      drawerChunksContainer.innerHTML = `
        <div class="text-xs text-zinc-400 text-center py-8">
          No active retrieved chunks. Ask a question to view citations.
        </div>
      `;
    });
  }

  // Starter Cards Click Listeners
  document.querySelectorAll('.starter-card').forEach(card => {
    card.addEventListener('click', () => {
      const prompt = card.getAttribute('data-prompt');
      if (prompt) {
        userInput.value = prompt;
        handleFormSubmit();
      }
    });
  });

  // Chat Form Listeners
  if (chatForm) {
    chatForm.addEventListener('submit', (e) => {
      e.preventDefault();
      handleFormSubmit();
    });
  }

  if (userInput) {
    userInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleFormSubmit();
      }
    });
  }

  // Setup Dev Mode Ingestion
  setupIngestion();
  loadSources();
}

function setupIngestion() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const scrapeUrlBtn = document.getElementById('scrape-url-btn');
  const webUrlInput = document.getElementById('web-url-input');

  if (dropZone && fileInput) {
    // Prevent default drag events to allow drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
      dropZone.addEventListener(eventName, (e) => e.preventDefault(), false);
    });

    // Drag-over styling
    dropZone.addEventListener('dragover', () => {
      dropZone.classList.add('border-zinc-500', 'bg-zinc-100');
    });

    dropZone.addEventListener('dragleave', () => {
      dropZone.classList.remove('border-zinc-500', 'bg-zinc-100');
    });

    // Drop handler
    dropZone.addEventListener('drop', (e) => {
      dropZone.classList.remove('border-zinc-500', 'bg-zinc-100');
      const files = e.dataTransfer.files;
      if (files.length > 0) {
        uploadFile(files[0]);
      }
    });

    // File input change handler
    fileInput.addEventListener('change', () => {
      if (fileInput.files.length > 0) {
        uploadFile(fileInput.files[0]);
      }
    });
  }

  if (scrapeUrlBtn && webUrlInput) {
    scrapeUrlBtn.addEventListener('click', async (e) => {
      e.preventDefault();
      const url = webUrlInput.value.trim();
      if (!url) {
        alert("Please enter a valid documentation URL.");
        return;
      }

      scrapeUrlBtn.disabled = true;
      const originalText = scrapeUrlBtn.textContent;
      scrapeUrlBtn.textContent = 'Scraping...';

      try {
        const res = await fetch(`${API_BASE_URL}/ingest-web`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ url: url })
        });
        const data = await res.json();
        if (res.ok) {
          alert(`Success: ${data.message}`);
          webUrlInput.value = '';
          loadSources();
        } else {
          alert(`Error: ${data.detail || 'Failed to scrape website'}`);
        }
      } catch (err) {
        alert(`Request failed: ${err.message}`);
      } finally {
        scrapeUrlBtn.disabled = false;
        scrapeUrlBtn.textContent = originalText;
      }
    });
  }
}

async function uploadFile(file) {
  const dropZone = document.getElementById('drop-zone');
  const originalHtml = dropZone.innerHTML;
  
  dropZone.innerHTML = `
    <div class="flex flex-col items-center justify-center space-y-3">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-zinc-800"></div>
      <p class="text-sm font-medium text-zinc-900">Uploading and chunking ${escapeHtml(file.name)}...</p>
    </div>
  `;

  const formData = new FormData();
  formData.append('file', file);

  try {
    const res = await fetch(`${API_BASE_URL}/ingest-file`, {
      method: 'POST',
      body: formData
    });
    const data = await res.json();
    if (res.ok) {
      alert(`Success: ${data.message}`);
      loadSources();
    } else {
      alert(`Error: ${data.detail || 'Failed to ingest file'}`);
    }
  } catch (err) {
    alert(`Upload failed: ${err.message}`);
  } finally {
    dropZone.innerHTML = originalHtml;
    // Rebind change event after innerHTML restoration
    const fileInput = document.getElementById('file-input');
    if (fileInput) {
      fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
          uploadFile(fileInput.files[0]);
        }
      });
    }
  }
}

async function loadSources() {
  try {
    const res = await fetch(`${API_BASE_URL}/list-sources`);
    if (!res.ok) return;
    const data = await res.json();
    const sources = data.sources || [];
    
    // Update active source counts in header and Dev Mode UI
    const headerSub = document.getElementById('view-subtitle');
    if (headerSub) {
      headerSub.textContent = `${sources.length} sources active`;
    }
    const devCount = document.getElementById('dev-sources-count');
    if (devCount) {
      devCount.textContent = `${sources.length} files active in ChromaDB`;
    }
    
    // 1. Update Sidebar Connected Sources List
    const sidebarList = document.getElementById('sidebar-sources-list');
    if (sidebarList) {
      if (sources.length === 0) {
        sidebarList.innerHTML = `<div class="text-[11px] text-zinc-400 px-2.5 py-2">No active sources</div>`;
      } else {
        sidebarList.innerHTML = sources.map(s => {
          const isWeb = s.type === 'website';
          const icon = isWeb 
            ? `<svg class="w-4 h-4 text-zinc-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"/></svg>`
            : `<svg class="w-4 h-4 text-zinc-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>`;
          const badge = isWeb
            ? `<span class="text-[10px] text-zinc-400 font-mono">Web Docs</span>`
            : `<span class="w-1.5 h-1.5 rounded-full bg-emerald-500 flex-shrink-0"></span>`;
            
          return `
            <div class="group flex items-center justify-between px-2.5 py-2 rounded-lg text-xs text-zinc-700 hover:bg-zinc-100 hover:text-zinc-900 transition-colors">
              <div class="flex items-center space-x-2.5 truncate">
                ${icon}
                <span class="truncate" title="${escapeHtml(s.source)}">${escapeHtml(s.source)}</span>
              </div>
              ${badge}
            </div>
          `;
        }).join('');
      }
    }
    
    // 2. Update Dev Mode Sources Table
    const devTable = document.getElementById('dev-sources-table');
    if (devTable) {
      if (sources.length === 0) {
        devTable.innerHTML = `
          <tr>
            <td colspan="5" class="py-6 text-center text-xs text-zinc-400">No documents ingested in vector database yet.</td>
          </tr>
        `;
      } else {
        devTable.innerHTML = sources.map(s => {
          const isWeb = s.type === 'website';
          const icon = isWeb 
            ? `<svg class="w-4 h-4 text-zinc-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9"/></svg>`
            : `<svg class="w-4 h-4 text-zinc-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"/></svg>`;
            
          return `
            <tr class="hover:bg-zinc-50/50 transition-colors">
              <td class="py-3 px-4 font-medium text-zinc-900 flex items-center space-x-2 truncate max-w-xs">
                ${icon}
                <span class="truncate" title="${escapeHtml(s.source)}">${escapeHtml(s.source)}</span>
              </td>
              <td class="py-3 px-4 font-mono text-zinc-500 uppercase">${escapeHtml(s.type)}</td>
              <td class="py-3 px-4 font-mono text-zinc-700">${s.chunks} chunks</td>
              <td class="py-3 px-4">
                <span class="inline-flex items-center space-x-1.5 px-2 py-0.5 rounded-full text-[10px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <span class="w-1.5 h-1.5 rounded-full bg-emerald-500"></span>
                  <span>Indexed</span>
                </span>
              </td>
              <td class="py-3 px-4 text-right space-x-2">
                <button class="text-zinc-500 hover:text-zinc-900 font-mono text-[11px] hover:underline" onclick="handleRefreshIndex()">Re-index</button>
              </td>
            </tr>
          `;
        }).join('');
      }
    }
  } catch (err) {
    console.error("Error loading sources list:", err);
  }
}


// Toggle Developer Mode View
function toggleDevMode(e) {
  if (e && e.preventDefault) e.preventDefault();
  isDevModeActive = !isDevModeActive;
  console.log("Dev Mode Toggled! Active:", isDevModeActive);

  const stdView = document.getElementById('standard-mode-view');
  const dView = document.getElementById('dev-mode-view');
  const btnText = document.getElementById('dev-mode-text');
  const btn = document.getElementById('dev-mode-btn');
  const vTitle = document.getElementById('view-title');
  const vSub = document.getElementById('view-subtitle');
  const sideSrc = document.getElementById('sidebar-sources-container');

  if (isDevModeActive) {
    if (stdView) {
      stdView.classList.add('hidden');
      stdView.style.display = 'none';
    }
    if (dView) {
      dView.classList.remove('hidden');
      dView.style.display = 'block';
    }
    if (btnText) btnText.textContent = 'Chat Mode';
    if (btn) {
      btn.classList.add('bg-zinc-900', 'text-white');
      btn.classList.remove('bg-white', 'text-zinc-700');
    }
    if (vTitle) vTitle.textContent = 'Developer Ingestion & Pipeline';
    if (vSub) vSub.textContent = 'ChromaDB + Sparse BM25 ETL';
    if (sideSrc) {
      sideSrc.style.display = 'block';
    }
  } else {
    if (dView) {
      dView.classList.add('hidden');
      dView.style.display = 'none';
    }
    if (stdView) {
      stdView.classList.remove('hidden');
      stdView.style.display = 'flex';
    }
    if (btnText) btnText.textContent = 'Dev Mode';
    if (btn) {
      btn.classList.remove('bg-zinc-900', 'text-white');
      btn.classList.add('bg-white', 'text-zinc-700');
    }
    if (vTitle) vTitle.textContent = 'KNOW-RAG Synthesis Engine';
    if (vSub) vSub.textContent = '2 sources active';
    if (sideSrc) {
      sideSrc.style.display = 'none';
    }
  }
}

window.toggleDevMode = toggleDevMode;

// Handle Refresh Index POST Call
async function handleRefreshIndex() {
  const originalText = refreshIndexBtn.innerHTML;
  refreshIndexBtn.innerHTML = `<span>Re-indexing...</span>`;
  try {
    const res = await fetch(`${API_BASE_URL}/refresh`, { method: 'POST' });
    const data = await res.json();
    alert(`Index Refreshed Successfully!\nTotal Chunks Indexed: ${data.total_documents}`);
  } catch (err) {
    alert(`Error refreshing index: ${err.message}`);
  } finally {
    refreshIndexBtn.innerHTML = originalText;
  }
}

// Handle Form Submission
async function handleFormSubmit() {
  const questionText = userInput.value.trim();
  if (!questionText) return;

  userInput.value = '';
  starterQuestions.classList.add('hidden');

  appendUserMessage(questionText);
  const indicatorId = showProcessingIndicator();
  const { messageCard, contentEl, metaEl } = createAIMessageContainer();

  const isStreaming = streamingToggle ? streamingToggle.checked : true;

  if (isStreaming) {
    await handleStreamingResponse(questionText, contentEl, metaEl, indicatorId);
  } else {
    await handleNonStreamingResponse(questionText, contentEl, metaEl, indicatorId);
  }
}

// Render User Message
function appendUserMessage(text) {
  const userEl = document.createElement('div');
  userEl.className = 'flex justify-end fade-in';
  userEl.innerHTML = `
    <div class="max-w-2xl bg-zinc-900 text-white rounded-2xl px-5 py-3.5 text-sm leading-relaxed shadow-sm">
      ${escapeHtml(text)}
    </div>
  `;
  messagesContainer.appendChild(userEl);
  scrollToBottom();
}

// Processing Indicator
function showProcessingIndicator() {
  const id = 'indicator-' + Date.now();
  const indEl = document.createElement('div');
  indEl.id = id;
  indEl.className = 'flex items-center space-x-3 px-4 py-2.5 bg-zinc-50 border border-zinc-200 rounded-xl text-xs text-zinc-600 max-w-xl fade-in';
  indEl.innerHTML = `
    <div class="relative flex h-2 w-2">
      <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-zinc-400 opacity-75"></span>
      <span class="relative inline-flex rounded-full h-2 w-2 bg-zinc-800"></span>
    </div>
    <div class="flex-1 flex items-center justify-between">
      <span>Retrieving hybrid context & reranking...</span>
      <span class="text-[10px] font-mono text-zinc-400">Dense + BM25</span>
    </div>
  `;
  messagesContainer.appendChild(indEl);
  scrollToBottom();
  return id;
}

function removeProcessingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// Create AI Message Container
function createAIMessageContainer() {
  const wrapper = document.createElement('div');
  wrapper.className = 'flex space-x-4 fade-in';
  
  wrapper.innerHTML = `
    <div class="w-7 h-7 rounded-lg bg-zinc-100 border border-zinc-250 flex items-center justify-center text-xs font-bold text-zinc-800 flex-shrink-0 mt-0.5 shadow-sm">
      AI
    </div>
    <div class="flex-1 space-y-3 max-w-2xl text-sm leading-relaxed text-zinc-800">
      <div class="ai-content leading-relaxed space-y-2 text-zinc-800"></div>
      <div class="ai-meta"></div>
    </div>
  `;

  messagesContainer.appendChild(wrapper);
  scrollToBottom();

  return {
    messageCard: wrapper,
    contentEl: wrapper.querySelector('.ai-content'),
    metaEl: wrapper.querySelector('.ai-meta')
  };
}

// Stream Response Handler
async function handleStreamingResponse(questionText, contentEl, metaEl, indicatorId) {
  contentEl.classList.add('streaming-cursor');
  let fullText = '';
  let metadataStr = '';
  let isMetadata = false;

  try {
    const res = await fetch(`${API_BASE_URL}/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: questionText, session_id: sessionId })
    });

    removeProcessingIndicator(indicatorId);

    if (!res.ok) {
      contentEl.classList.remove('streaming-cursor');
      contentEl.innerHTML = `<span class="text-red-600">Error ${res.status}: ${res.statusText}</span>`;
      return;
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      
      const chunk = decoder.decode(value, { stream: true });
      if (!chunk) continue;

      if (isMetadata) {
        metadataStr += chunk;
      } else {
        buffer += chunk;
        if (buffer.includes('<END_OF_ANSWER>')) {
          const parts = buffer.split('<END_OF_ANSWER>');
          fullText += parts[0];
          contentEl.innerHTML = formatMarkdown(fullText);
          isMetadata = true;
          metadataStr += parts[1] || '';
          buffer = '';
        } else {
          if (buffer.includes('<')) {
            const idx = buffer.indexOf('<');
            fullText += buffer.substring(0, idx);
            buffer = buffer.substring(idx);
          } else {
            fullText += buffer;
            buffer = '';
          }
          contentEl.innerHTML = formatMarkdown(fullText);
        }
      }
      scrollToBottom();
    }

    if (buffer && !isMetadata) {
      fullText += buffer;
    }

    contentEl.classList.remove('streaming-cursor');
    contentEl.innerHTML = formatMarkdown(fullText);

    let sources = [];
    let latencies = null;

    if (metadataStr.trim()) {
      try {
        const meta = JSON.parse(metadataStr.trim());
        sources = meta.sources || [];
        latencies = meta.latencies || null;
      } catch (err) {
        console.error('Error parsing metadata JSON trailer:', err);
      }
    }

    renderMetadata(metaEl, sources, latencies);

  } catch (err) {
    removeProcessingIndicator(indicatorId);
    contentEl.classList.remove('streaming-cursor');
    contentEl.innerHTML = `<span class="text-red-600">Connection error: ${err.message}</span>`;
  }
}

// Non-Streaming Response Handler
async function handleNonStreamingResponse(questionText, contentEl, metaEl, indicatorId) {
  try {
    const res = await fetch(`${API_BASE_URL}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: questionText, session_id: sessionId })
    });

    removeProcessingIndicator(indicatorId);

    if (!res.ok) {
      contentEl.innerHTML = `<span class="text-red-600">Error ${res.status}: ${res.statusText}</span>`;
      return;
    }

    const data = await res.json();
    contentEl.innerHTML = formatMarkdown(data.answer || '');
    renderMetadata(metaEl, data.sources || [], data.latencies || null);

  } catch (err) {
    removeProcessingIndicator(indicatorId);
    contentEl.innerHTML = `<span class="text-red-600">Connection error: ${err.message}</span>`;
  }
}

// Render Latencies & Sources Metadata
function renderMetadata(metaEl, sources, latencies) {
  let html = '';

  if (latencies) {
    html += `
      <div class="flex items-center space-x-1.5 flex-wrap pt-2 text-[11px] font-mono">
        <span class="bg-zinc-100 border border-zinc-200 px-2 py-0.5 rounded text-zinc-700">🔍 Hybrid: ${latencies.retriever || 0} ms</span>
        <span class="bg-zinc-100 border border-zinc-200 px-2 py-0.5 rounded text-zinc-700">🎯 Rerank: ${latencies.reranker || 0} ms</span>
        <span class="bg-zinc-100 border border-zinc-200 px-2 py-0.5 rounded text-zinc-700">⚡ Gemini: ${latencies.llm || 0} ms</span>
        <span class="bg-zinc-900 text-white px-2 py-0.5 rounded">⏱️ Total: ${latencies.total || 0} ms</span>
      </div>
    `;
  }

  if (sources && sources.length > 0) {
    html += `
      <div class="pt-3 border-t border-zinc-150 flex items-center justify-between text-xs mt-3">
        <div class="flex items-center space-x-2 text-zinc-500">
          <svg class="w-3.5 h-3.5 text-zinc-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/></svg>
          <span>Grounded in ${sources.length} retrieved chunks</span>
        </div>
        <button class="open-sources-drawer-btn text-xs text-zinc-700 font-medium hover:underline">
          View Citations →
        </button>
      </div>
    `;

    updateDrawerChunks(sources);
  }

  metaEl.innerHTML = html;

  const openDrawerBtn = metaEl.querySelector('.open-sources-drawer-btn');
  if (openDrawerBtn) {
    openDrawerBtn.addEventListener('click', () => {
      citationDrawer.classList.remove('hidden');
    });
  }

  scrollToBottom();
}

// Update Citation Drawer Chunks
function updateDrawerChunks(sources) {
  if (!sources || sources.length === 0) return;
  lastRetrievedSources = sources;

  let html = '';
  sources.forEach((s) => {
    if (typeof s === 'object') {
      const docType = (s.type || 'unknown').toUpperCase();
      const sourceName = s.source || 'Unknown Source';
      const pageStr = s.page ? `, p.${s.page}` : '';
      const scoreStr = s.score ? `Score: ${s.score}` : '';
      const previewStr = s.preview || '';
      const url = s.url;

      const titleHtml = url 
        ? `<a href="${url}" target="_blank" class="hover:underline text-zinc-900 font-semibold">${escapeHtml(sourceName)}</a>`
        : `<span class="text-zinc-900 font-semibold">${escapeHtml(sourceName)}</span>`;

      html += `
        <div class="bg-zinc-50 border border-zinc-200 rounded-xl p-3 space-y-2 text-xs fade-in">
          <div class="flex items-center justify-between text-[11px]">
            <span class="font-mono text-zinc-800 font-semibold">[${docType}${pageStr}]</span>
            <span class="bg-emerald-50 text-emerald-700 border border-emerald-200/80 px-1.5 py-0.5 rounded font-mono text-[10px]">${scoreStr}</span>
          </div>
          <div class="text-zinc-900 font-medium">${titleHtml}</div>
          ${previewStr ? `<p class="text-zinc-600 leading-relaxed font-sans italic bg-white p-2.5 rounded-lg border border-zinc-150 text-[11px]">"${escapeHtml(previewStr)}"</p>` : ''}
        </div>
      `;
    } else {
      html += `<div class="p-2 bg-zinc-50 border border-zinc-200 rounded-lg text-xs text-zinc-700">${escapeHtml(String(s))}</div>`;
    }
  });

  drawerChunksContainer.innerHTML = html;
}

// Utilities
function scrollToBottom() {
  const chatStream = document.getElementById('chat-stream');
  if (chatStream) {
    chatStream.scrollTop = chatStream.scrollHeight;
  }
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function formatMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/`([^`]+)`/g, '<code class="font-mono bg-zinc-100 px-1 py-0.5 rounded text-[12px] text-zinc-800 border border-zinc-200">$1</code>')
    .replace(/\n\n/g, '<br/><br/>')
    .replace(/\n/g, '<br/>');
}

// Run Initialization
document.addEventListener('DOMContentLoaded', initApp);
