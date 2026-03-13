/**
 * NeoCare — Module 3: Postpartum Care
 * File: frontend/js/postpartum.js
 *
 * Talks ONLY to FastAPI on port 8000.
 * Groq API key never appears here — it lives in backend/modules/postpartum.py
 */

const NeoCarePostpartum = (() => {

  // ════════════════════════════════════════
  //  CONFIG
  // ════════════════════════════════════════
  const API = (window.location.hostname === '127.0.0.1' || window.location.hostname === 'localhost' || window.location.protocol === 'file:') ? 'http://127.0.0.1:8000/api' : window.location.origin + '/api';

  // Stable session ID per browser
  const SESSION = (() => {
    let id = localStorage.getItem('nc_sid');
    if (!id) {
      id = 'sess_' + Math.random().toString(36).slice(2, 10);
      localStorage.setItem('nc_sid', id);
    }
    return id;
  })();

  let epdsAnswers = {};

  // ════════════════════════════════════════
  //  INIT
  // ════════════════════════════════════════
  function init() {
    restoreProfile();
    loadEPDS();
  }

  // ════════════════════════════════════════
  //  PROFILE
  // ════════════════════════════════════════
  function getProfile() {
    return {
      mother_name:    document.getElementById('motherName').value.trim()   || null,
      baby_age_weeks: parseInt(document.getElementById('babyAge').value)   || null,
      delivery_type:  document.getElementById('deliveryType').value,
      bf_status:      document.getElementById('bfStatus').value,
    };
  }

  function saveProfile() {
    const profile = getProfile();
    const partner = {
      name:    document.getElementById('guardianName').value.trim()  || null,
      email:   document.getElementById('guardianEmail').value.trim() || null,
      phone:   document.getElementById('guardianPhone').value.trim() || null,
      consent: document.getElementById('alertConsent').checked,
    };
    localStorage.setItem('nc_profile', JSON.stringify({ ...profile, partner }));

    // Persist partner info to backend
    fetch(`${API}/partner-setup`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ session: SESSION, partner }),
    }).catch(() => {});

    const el = document.getElementById('profileSaved');
    el.style.display = 'inline';
    setTimeout(() => (el.style.display = 'none'), 2500);
  }

  function restoreProfile() {
    try {
      const raw = localStorage.getItem('nc_profile');
      if (!raw) return;
      const p = JSON.parse(raw);
      if (p.mother_name)    _val('motherName',    p.mother_name);
      if (p.baby_age_weeks) _val('babyAge',       p.baby_age_weeks);
      if (p.delivery_type)  _val('deliveryType',  p.delivery_type);
      if (p.bf_status)      _val('bfStatus',      p.bf_status);
      if (p.partner) {
        if (p.partner.name)  _val('guardianName',  p.partner.name);
        if (p.partner.email) _val('guardianEmail', p.partner.email);
        if (p.partner.phone) _val('guardianPhone', p.partner.phone);
        document.getElementById('alertConsent').checked = p.partner.consent !== false;
      }
    } catch (e) { /* ignore parse errors */ }
  }

  function _val(id, value) {
    const el = document.getElementById(id);
    if (el) el.value = value;
  }

  // ════════════════════════════════════════
  //  TABS
  // ════════════════════════════════════════
  function switchTab(tab, btn) {
    document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    document.getElementById('panel_' + tab).classList.add('active');
    btn.classList.add('active');
    if (tab === 'dash') renderDashboard();
  }

  // ════════════════════════════════════════
  //  CHAT  →  POST /api/chat
  // ════════════════════════════════════════
  async function sendMessage() {
    const input = document.getElementById('chatInput');
    const text  = input.value.trim();
    if (!text) return;

    appendBubble('user', text);
    input.value = '';
    input.style.height = 'auto';
    document.getElementById('sendBtn').disabled = true;

    const typingEl = showTyping();

    try {
      const res = await fetch(`${API}/chat`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          session: SESSION,
          message: text,
          profile: getProfile(),
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({}));
        throw new Error(err.detail || `Server error ${res.status}`);
      }

      const data = await res.json();
      typingEl.remove();
      appendBubble('bot', data.reply, data.is_emergency);

      if (data.wellness)        updateMeter(data.wellness);
      if (data.is_emergency)    showEmergencyBanner();
      if (data.alert_triggered) showToast('📊 Wellness alert logged for guardian.', 'warn');

    } catch (e) {
      typingEl.remove();
      appendBubble('bot',
        `**Connection issue**\n\nCould not reach the NeoCare server.\n\n` +
        `• Make sure FastAPI is running: \`uvicorn main:app --reload --port 8000\`\n\n` +
        `_Error: ${e.message}_`
      );
    }

    document.getElementById('sendBtn').disabled = false;
  }

  function quickSend(text) {
    document.getElementById('chatInput').value = text;
    sendMessage();
  }

  function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  }

  function autoResize(el) {
    el.style.height = 'auto';
    el.style.height = Math.min(el.scrollHeight, 110) + 'px';
  }

  // ════════════════════════════════════════
  //  WELLNESS METER
  // ════════════════════════════════════════
  function updateMeter(w) {
    const bar  = document.getElementById('riskBar');
    const lbl  = document.getElementById('riskLabel');
    const note = document.getElementById('riskNote');
    bar.style.width = Math.max(4, w.score) + '%';
    if (w.level === 'high') {
      bar.style.background = 'var(--danger)';
      lbl.style.color      = 'var(--danger)';
      lbl.textContent      = 'High Concern 🔴';
      note.textContent     = 'Persistent distress detected';
    } else if (w.level === 'medium') {
      bar.style.background = 'var(--warn)';
      lbl.style.color      = 'var(--warn)';
      lbl.textContent      = 'Monitor 🟡';
      note.textContent     = 'Some distress signals noticed';
    } else {
      bar.style.background = 'var(--ok)';
      lbl.style.color      = 'var(--ok)';
      lbl.textContent      = 'All Good 🟢';
      note.textContent     = 'Keep checking in 💛';
    }
  }

  function showEmergencyBanner() {
    const b = document.getElementById('emergencyBanner');
    b.style.display = 'flex';
    setTimeout(() => (b.style.display = 'none'), 30000);
  }

  // ════════════════════════════════════════
  //  BUBBLE HELPERS
  // ════════════════════════════════════════
  function appendBubble(role, text, emergency = false) {
    const wrap = document.createElement('div');
    wrap.className = `msg ${role}`;

    const av = document.createElement('div');
    av.className  = 'msg-avatar';
    av.textContent = role === 'bot' ? '🌿' : '👩';

    const bub = document.createElement('div');
    bub.className = 'msg-bubble';
    bub.innerHTML = renderMarkdown(text);

    if (emergency && role === 'bot') {
      const e = document.createElement('div');
      e.className = 'emergency-block';
      e.innerHTML =
        '🚨 <strong>Emergency signs detected.</strong><br/>' +
        'Call <strong>108</strong> now or go to the nearest hospital.<br/>' +
        'Mental health crisis: iCall <strong>9152987821</strong>';
      bub.appendChild(e);
    }

    wrap.appendChild(av);
    wrap.appendChild(bub);

    const msgs = document.getElementById('chatMessages');
    msgs.appendChild(wrap);
    msgs.scrollTop = msgs.scrollHeight;
    return wrap;
  }

  function showTyping() {
    const msgs = document.getElementById('chatMessages');
    const w    = document.createElement('div');
    w.className = 'msg bot';
    w.innerHTML =
      `<div class="msg-avatar">🌿</div>` +
      `<div class="typing">` +
        `<div class="typing-dot"></div>` +
        `<div class="typing-dot"></div>` +
        `<div class="typing-dot"></div>` +
      `</div>`;
    msgs.appendChild(w);
    msgs.scrollTop = msgs.scrollHeight;
    return w;
  }

  // Simple Markdown → HTML
  function renderMarkdown(text) {
    return text
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g,     '<em>$1</em>')
      .replace(/^#{1,3} (.+)$/gm, '<strong>$1</strong>')
      .replace(/^[•\-]\s(.+)$/gm, '<li>$1</li>')
      .replace(/(<li>[\s\S]*?<\/li>\n?)+/g, m => `<ul>${m}</ul>`)
      .replace(
        /🏥 \*\*Seek help if:\*\*(.*?)(?=\n\n|\n[A-Z*🎯💚]|$)/gs,
        '<div class="seek-help">🏥 <strong>Seek help if:</strong>$1</div>'
      )
      .replace(/\n\n/g, '<br/><br/>')
      .replace(/\n/g,   '<br/>');
  }

  // Toast notification
  function showToast(msg, type = 'warn') {
    const n = document.createElement('div');
    n.className = `alert alert-${type} toast`;
    n.innerHTML = `<span>📊</span><div>${msg}</div>`;
    document.body.appendChild(n);
    setTimeout(() => n.remove(), 6000);
  }

  // ════════════════════════════════════════
  //  EPDS  →  GET  /api/ppd-screening/questions
  //           POST /api/ppd-screening
  // ════════════════════════════════════════
  async function loadEPDS() {
    try {
      const res  = await fetch(`${API}/ppd-screening/questions`);
      const data = await res.json();
      renderEPDSForm(data.questions);
    } catch (e) {
      document.getElementById('epdsForm').innerHTML =
        '<div class="alert alert-warn"><span>⚠️</span>' +
        '<div>Could not load questions — is the FastAPI server running?</div></div>';
    }
  }

  function renderEPDSForm(questions) {
    const form = document.getElementById('epdsForm');
    form.innerHTML = '';
    questions.forEach((item, qi) => {
      const div = document.createElement('div');
      div.className = 'epds-q';
      div.innerHTML =
        `<div class="epds-qtext">${qi + 1}. ${item.q}` +
        (item.critical
          ? ' <span class="epds-critical">(Crisis check question)</span>'
          : '') +
        `</div>` +
        `<div class="epds-opts">` +
        item.opts.map((o, oi) =>
          `<label class="epds-opt" id="eopt_${qi}_${oi}">` +
          `<input type="radio" name="eq${qi}" value="${oi}" ` +
          `onchange="NeoCarePostpartum.selectEPDS(${qi},${oi})"/>` +
          `${o}</label>`
        ).join('') +
        `</div>`;
      form.appendChild(div);
    });
  }

  function selectEPDS(qi, oi) {
    epdsAnswers[qi] = oi;
    for (let i = 0; i < 4; i++) {
      const el = document.getElementById(`eopt_${qi}_${i}`);
      if (el) el.classList.toggle('sel', i === oi);
    }
  }

  async function submitEPDS() {
    if (Object.keys(epdsAnswers).length < 10) {
      alert('Please answer all 10 questions.');
      return;
    }
    document.getElementById('epdsSpinner').style.display = 'inline';

    try {
      const res = await fetch(`${API}/ppd-screening`, {
        method:  'POST',
        headers: { 'Content-Type': 'application/json' },
        body:    JSON.stringify({
          session: SESSION,
          answers: Object.fromEntries(
            Object.entries(epdsAnswers).map(([k, v]) => [String(k), v])
          ),
        }),
      });
      if (!res.ok) throw new Error(`Server error ${res.status}`);
      const data = await res.json();
      renderEPDSResult(data);
      if (data.wellness) updateMeter(data.wellness);
    } catch (e) {
      alert('Could not submit — make sure the FastAPI server is running on port 8000.');
    }

    document.getElementById('epdsSpinner').style.display = 'none';
  }

  function renderEPDSResult(d) {
    const C = {
      low:    { border: 'var(--ok)',     bg: 'var(--ok-bg)',     text: '#2d5a2d' },
      medium: { border: 'var(--warn)',   bg: 'var(--warn-bg)',   text: '#7a4a10' },
      high:   { border: 'var(--danger)', bg: 'var(--danger-bg)', text: '#6a1a18' },
    };
    const c    = C[d.level];
    const emoji = d.level === 'low' ? '🟢' : d.level === 'medium' ? '🟡' : '🔴';
    const label = d.level === 'low'
      ? 'Low Concern'
      : d.level === 'medium'
      ? 'Moderate — Monitor'
      : 'High — Please Seek Support';

    document.getElementById('epdsResult').innerHTML = `
      <div class="card epds-result-card">
        <div class="epds-score-row">
          <div class="score-circle" style="border-color:${c.border};color:${c.text}">
            <span class="score-num">${d.score}</span>
            <span class="score-sub">/ 30</span>
          </div>
          <div>
            <div class="score-label">${emoji} ${label}</div>
            <div class="score-meta">Edinburgh Postnatal Depression Scale · Score ${d.score}/30</div>
            ${d.crisis
              ? `<div class="score-crisis">⚠️ Question 10 response requires immediate attention</div>`
              : ''}
            ${d.alert_triggered
              ? `<div class="score-alert-note">📊 Wellness alert sent to guardian dashboard</div>`
              : ''}
          </div>
        </div>

        <div class="epds-guidance" style="border-left-color:${c.border};background:${c.bg};color:${c.text}">
          ${d.guidance}
        </div>

        ${d.resources && d.resources.length ? `
        <div class="alert alert-danger">
          <span>🚨</span>
          <div>
            <strong>Please reach out for support right now:</strong><br/>
            ${d.resources.map(r =>
              `📞 ${r.name}: <strong>${r.number}</strong> (${r.hours})`
            ).join('<br/>')}
          </div>
        </div>` : ''}

        <div style="display:flex;gap:8px;flex-wrap:wrap;margin-top:.6rem">
          <button class="btn btn-rose btn-sm" onclick="NeoCarePostpartum.chatAboutEPDS(${d.score})">
            💬 Talk to NeoCare about this
          </button>
        </div>

        <div class="epds-disclaimer">
          ⚠️ EPDS is a screening tool — not a clinical diagnosis. Please speak with your healthcare provider for a full assessment.
        </div>
      </div>`;
  }

  function chatAboutEPDS(score) {
    // Switch to chat tab
    const chatTab = document.querySelectorAll('.tab')[0];
    switchTab('chat', chatTab);
    document.getElementById('chatInput').value =
      `I just completed the EPDS self-test and got a score of ${score}/30. ` +
      `Can you help me understand what this means and what I should do next?`;
    sendMessage();
  }

  // ════════════════════════════════════════
  //  DASHBOARD  →  GET /api/alerts
  //               GET /api/chat-state
  // ════════════════════════════════════════
  async function renderDashboard() {
    const el = document.getElementById('dashboardContent');
    el.innerHTML = '<div style="color:var(--soft);font-size:.87rem">Loading…</div>';

    try {
      const [stateRes, alertsRes] = await Promise.all([
        fetch(`${API}/chat-state?session=${SESSION}`),
        fetch(`${API}/alerts?session=${SESSION}`),
      ]);
      const state  = await stateRes.json();
      const alerts = (await alertsRes.json()).alerts || [];

      const gName   = document.getElementById('guardianName').value  || 'Not set';
      const gEmail  = document.getElementById('guardianEmail').value || 'Not set';
      const gPhone  = document.getElementById('guardianPhone').value || 'Not set';
      const consent = document.getElementById('alertConsent').checked;
      const w       = state.wellness || { label: '🟢 All Good', score: 0 };

      const alertsHtml = alerts.length === 0
        ? `<div class="dash-empty">No alerts yet. The system monitors patterns across multiple messages before generating one.</div>`
        : alerts.map(a => `
          <div class="alert-item ${a.severity === 'high' ? 'a-high' : 'a-med'}">
            <span class="alert-icon">${a.severity === 'high' ? '🔴' : '🟡'}</span>
            <div class="alert-body">
              <div class="alert-title">
                ${a.severity === 'high' ? 'High Concern' : 'Moderate Concern'} Alert
                <span class="alert-reason">${a.reason}</span>
              </div>
              <div class="alert-details">${a.details || ''}</div>
              <div class="alert-meta">
                ${new Date(a.created_at * 1000).toLocaleString()} ·
                To: ${gName} (${gEmail}) ·
                Status: <strong>${a.sent_status}</strong> ·
                ${consent ? '✅ Consent given' : '⚠️ Consent off'}
              </div>
            </div>
          </div>`
        ).join('');

      el.innerHTML = `
        <div class="summary-grid">
          <div class="summary-tile" style="background:var(--rose-pale)">
            <div class="tile-label">Guardian</div>
            <div class="tile-value">${gName}</div>
            <div class="tile-sub">${gEmail}</div>
            <div class="tile-sub">${gPhone}</div>
          </div>
          <div class="summary-tile" style="background:var(--sage-pale)">
            <div class="tile-label">Current Wellness</div>
            <div class="tile-value">${w.label}</div>
            <div class="tile-sub">Score: ${w.score}/100</div>
          </div>
          <div class="summary-tile" style="background:${consent ? 'var(--ok-bg)' : 'var(--danger-bg)'}">
            <div class="tile-label">Alert Status</div>
            <div class="tile-value" style="color:${consent ? 'var(--ok)' : 'var(--danger)'}">
              ${consent ? '✅ Enabled' : '❌ Disabled'}
            </div>
            <div class="tile-sub">${alerts.length} alert${alerts.length !== 1 ? 's' : ''} generated</div>
          </div>
        </div>

        <div class="dash-section-title">📋 Alert Log</div>
        ${alertsHtml}

        <div class="dash-privacy">
          🔒 <strong>Privacy:</strong> NeoCare never shares chat messages.
          Only a brief wellness summary is included in alerts.
          The mother fully controls alert consent.
        </div>`;

    } catch (e) {
      el.innerHTML =
        `<div class="alert alert-warn"><span>⚠️</span>` +
        `<div>Could not load dashboard — is the FastAPI server running on port 8000?</div></div>`;
    }
  }

  // ════════════════════════════════════════
  //  PUBLIC API
  // ════════════════════════════════════════
  return {
    init,
    saveProfile,
    switchTab,
    sendMessage,
    quickSend,
    handleKey,
    autoResize,
    selectEPDS,
    submitEPDS,
    chatAboutEPDS,
  };

})();

// Boot on DOM ready
document.addEventListener('DOMContentLoaded', () => NeoCarePostpartum.init());