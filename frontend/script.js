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

  // Dev Mode Toggle Listener
  if (devModeBtn) {
    devModeBtn.addEventListener('click', toggleDevMode);
  }

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
}

// Toggle Developer Mode View
function toggleDevMode() {
  isDevModeActive = !isDevModeActive;

  if (isDevModeActive) {
    standardModeView.classList.add('hidden');
    devModeView.classList.remove('hidden');
    devModeText.textContent = 'Chat Mode';
    devModeBtn.classList.add('bg-zinc-900', 'text-white');
    devModeBtn.classList.remove('bg-white', 'text-zinc-700');
    
    if (viewTitle) viewTitle.textContent = 'Developer Ingestion & Pipeline';
    if (viewSubtitle) viewSubtitle.textContent = 'ChromaDB + Sparse BM25 ETL';
  } else {
    devModeView.classList.add('hidden');
    standardModeView.classList.remove('hidden');
    devModeText.textContent = 'Dev Mode';
    devModeBtn.classList.remove('bg-zinc-900', 'text-white');
    devModeBtn.classList.add('bg-white', 'text-zinc-700');

    if (viewTitle) viewTitle.textContent = 'KNOW-RAG Synthesis Engine';
    if (viewSubtitle) viewSubtitle.textContent = '2 sources active';
  }
}

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
