// ============================================================
// ResMgmt AI Chatbot Widget
// Include this script at the bottom of every page.
// ============================================================

(function () {
  // Inject styles
  const style = document.createElement('style');
  style.textContent = `
    #chat-fab {
      position: fixed;
      bottom: 28px;
      right: 28px;
      width: 56px;
      height: 56px;
      border-radius: 50%;
      background: #2563eb;
      color: #fff;
      border: none;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 22px;
      box-shadow: 0 4px 16px rgba(37,99,235,0.4);
      z-index: 9999;
      transition: transform 0.2s, background 0.2s;
    }
    #chat-fab:hover { background: #1d4ed8; transform: scale(1.08); }

    #chat-panel {
      position: fixed;
      bottom: 96px;
      right: 28px;
      width: 380px;
      max-height: 540px;
      background: #fff;
      border-radius: 16px;
      box-shadow: 0 8px 40px rgba(0,0,0,0.18);
      display: flex;
      flex-direction: column;
      z-index: 9998;
      overflow: hidden;
      transform: scale(0.92) translateY(20px);
      opacity: 0;
      pointer-events: none;
      transition: opacity 0.2s, transform 0.2s;
    }
    #chat-panel.open {
      opacity: 1;
      pointer-events: all;
      transform: scale(1) translateY(0);
    }

    #chat-header {
      background: #2563eb;
      color: #fff;
      padding: 14px 18px;
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 600;
      font-size: 15px;
    }
    #chat-header i { font-size: 18px; }
    #chat-header span { flex: 1; }
    #chat-close {
      background: none;
      border: none;
      color: #fff;
      font-size: 20px;
      cursor: pointer;
      line-height: 1;
      opacity: 0.8;
    }
    #chat-close:hover { opacity: 1; }

    #chat-messages {
      flex: 1;
      overflow-y: auto;
      padding: 16px;
      display: flex;
      flex-direction: column;
      gap: 12px;
      background: #f8fafc;
    }

    .chat-bubble {
      max-width: 85%;
      padding: 10px 14px;
      border-radius: 12px;
      font-size: 13.5px;
      line-height: 1.55;
      word-break: break-word;
      white-space: pre-wrap;
    }
    .chat-bubble.bot {
      background: #fff;
      border: 1px solid #e2e8f0;
      align-self: flex-start;
      border-bottom-left-radius: 4px;
      color: #1e293b;
    }
    .chat-bubble.user {
      background: #2563eb;
      color: #fff;
      align-self: flex-end;
      border-bottom-right-radius: 4px;
    }
    .chat-bubble.typing {
      background: #fff;
      border: 1px solid #e2e8f0;
      align-self: flex-start;
      color: #94a3b8;
      font-style: italic;
    }

    #chat-input-row {
      display: flex;
      gap: 8px;
      padding: 12px 14px;
      border-top: 1px solid #e2e8f0;
      background: #fff;
    }
    #chat-input {
      flex: 1;
      border: 1px solid #cbd5e1;
      border-radius: 8px;
      padding: 8px 12px;
      font-size: 13.5px;
      outline: none;
      font-family: inherit;
      resize: none;
      line-height: 1.4;
    }
    #chat-input:focus { border-color: #2563eb; }
    #chat-send {
      background: #2563eb;
      color: #fff;
      border: none;
      border-radius: 8px;
      padding: 8px 14px;
      cursor: pointer;
      font-size: 15px;
      transition: background 0.2s;
      display: flex;
      align-items: center;
      justify-content: center;
    }
    #chat-send:hover { background: #1d4ed8; }
    #chat-send:disabled { background: #93c5fd; cursor: not-allowed; }

    #chat-hint {
      font-size: 11px;
      color: #94a3b8;
      text-align: center;
      padding: 0 14px 10px;
      background: #fff;
    }
  `;
  document.head.appendChild(style);

  // Inject HTML
  const fab = document.createElement('button');
  fab.id = 'chat-fab';
  fab.title = 'Ask AI Assistant';
  fab.innerHTML = '<i class="fas fa-robot"></i>';

  const panel = document.createElement('div');
  panel.id = 'chat-panel';
  panel.innerHTML = `
    <div id="chat-header">
      <i class="fas fa-robot"></i>
      <span>ResMgmt AI Assistant</span>
      <button id="chat-close" title="Close">×</button>
    </div>
    <div id="chat-messages">
      <div class="chat-bubble bot">👋 Hi! I'm your AI assistant. Ask me anything about your <strong>Employees, SOWs, Invoices,</strong> or <strong>Payments</strong>.</div>
    </div>
    <div id="chat-input-row">
      <textarea id="chat-input" rows="1" placeholder="Ask a question..."></textarea>
      <button id="chat-send" title="Send"><i class="fas fa-paper-plane"></i></button>
    </div>
    <div id="chat-hint">Powered by Gemini AI · Reads live database</div>
  `;

  document.body.appendChild(fab);
  document.body.appendChild(panel);

  // Toggle panel
  fab.addEventListener('click', () => {
    panel.classList.toggle('open');
    if (panel.classList.contains('open')) {
      document.getElementById('chat-input').focus();
    }
  });
  document.getElementById('chat-close').addEventListener('click', () => {
    panel.classList.remove('open');
  });

  // Send message
  async function sendMessage() {
    const input = document.getElementById('chat-input');
    const question = input.value.trim();
    if (!question) return;

    const messages = document.getElementById('chat-messages');
    const sendBtn = document.getElementById('chat-send');

    // Add user bubble
    const userBubble = document.createElement('div');
    userBubble.className = 'chat-bubble user';
    userBubble.textContent = question;
    messages.appendChild(userBubble);

    // Clear input
    input.value = '';
    sendBtn.disabled = true;

    // Add typing indicator
    const typing = document.createElement('div');
    typing.className = 'chat-bubble typing';
    typing.textContent = 'Thinking...';
    messages.appendChild(typing);
    messages.scrollTop = messages.scrollHeight;

    try {
      const res = await fetch('/api/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question })
      });
      const data = await res.json();

      typing.className = 'chat-bubble bot';
      typing.textContent = data.answer || 'Sorry, I could not get an answer.';
    } catch (err) {
      typing.className = 'chat-bubble bot';
      typing.textContent = '❌ Error connecting to AI. Please make sure the server is running.';
    }

    sendBtn.disabled = false;
    messages.scrollTop = messages.scrollHeight;
  }

  document.getElementById('chat-send').addEventListener('click', sendMessage);
  document.getElementById('chat-input').addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
})();
