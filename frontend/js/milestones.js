// ── MILESTONES MODULE JS ─────────────────────────────────────
// TDSC-based evaluation with Chart.js timeline visualization

const API = 'http://localhost:8001';
const answers = {};
let loadedMilestones = [];

// ── PROFILE HELPERS ───────────────────────────────────────────
function toggleGestational() {
  const show = document.getElementById('m_premature').value === 'yes';
  document.getElementById('gestGroup').style.display = show ? 'flex' : 'none';
}

// ── LOAD CHECKLIST ────────────────────────────────────────────
async function loadChecklist() {
  const age = parseFloat(document.getElementById('m_age').value);
  if (!age || isNaN(age) || age < 0 || age > 36) {
    alert('Please enter a valid age between 0 and 36 months.'); return;
  }

  try {
    const res = await fetch(`${API}/api/milestones/checklist?age_months=${age}`);
    const data = await res.json();
    loadedMilestones = data.milestones;

    const subtitle = document.getElementById('checklistSubtitle');
    subtitle.textContent = `Showing milestones relevant for ${age} months — grouped by domain`;

    renderChecklist(loadedMilestones);
    document.getElementById('checklistSection').style.display = 'block';
    document.getElementById('resultsSection').style.display = 'none';
    document.getElementById('checklistSection').scrollIntoView({ behavior: 'smooth', block: 'start' });

  } catch (e) {
    alert('Could not load milestones. Make sure the backend is running on port 8000.');
  }
}

// ── RENDER CHECKLIST ──────────────────────────────────────────
function renderChecklist(milestones) {
  const container = document.getElementById('milestoneItems');
  container.innerHTML = '';

  // Group by domain
  const domains = ['Gross Motor', 'Fine Motor', 'Language', 'Social'];
  const grouped = {};
  domains.forEach(d => grouped[d] = []);
  milestones.forEach(m => { if (grouped[m.domain]) grouped[m.domain].push(m); });

  const domainIcons = { 'Gross Motor': '🏃', 'Fine Motor': '✋', 'Language': '🗣️', 'Social': '👥' };
  const chipClass = { 'Gross Motor': 'chip-gross', 'Fine Motor': 'chip-fine', 'Language': 'chip-language', 'Social': 'chip-social' };

  domains.forEach(domain => {
    if (!grouped[domain].length) return;

    // Domain heading
    const heading = document.createElement('div');
    heading.className = 'domain-heading';
    heading.textContent = `${domainIcons[domain]} ${domain}`;
    container.appendChild(heading);

    grouped[domain].forEach(m => {
      const div = document.createElement('div');
      div.className = 'milestone-item';
      div.innerHTML = `
        <div class="milestone-toggles">
          <button class="toggle-btn t-yes" id="yes_${m.id}" onclick="setAnswer(${m.id}, true)">✓ Yes</button>
          <button class="toggle-btn t-no"  id="no_${m.id}"  onclick="setAnswer(${m.id}, false)">✗ No</button>
        </div>
        <div class="milestone-label">${m.label}</div>
        <div class="domain-chip ${chipClass[domain]}">${domain}</div>
      `;
      container.appendChild(div);
    });
  });
}

function setAnswer(id, value) {
  answers[String(id)] = value;
  document.getElementById('yes_' + id).classList.toggle('sel', value === true);
  document.getElementById('no_' + id).classList.toggle('sel', value === false);
}

// ── EVALUATE ──────────────────────────────────────────────────
async function evaluate() {
  const age         = parseFloat(document.getElementById('m_age').value);
  const sex         = document.getElementById('m_sex').value;
  const isPremature = document.getElementById('m_premature').value === 'yes';
  const gestational = parseInt(document.getElementById('m_gestational')?.value) || null;
  const regression  = document.getElementById('m_regression').checked;

  if (Object.keys(answers).length === 0) {
    alert('Please answer at least a few milestone questions before evaluating.'); return;
  }

  try {
    const res = await fetch(`${API}/api/milestones/evaluate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        age_months: age, sex,
        premature: isPremature,
        gestational_age_weeks: gestational,
        answers, regression
      })
    });
    const data = await res.json();
    renderResults(data, age);

  } catch (e) {
    alert('Could not reach the backend. Make sure the server is running on port 8000.');
  }
}

// ── RENDER RESULTS ────────────────────────────────────────────
function renderResults(data, inputAge) {
  const resultsDiv = document.getElementById('resultsSection');
  resultsDiv.style.display = 'block';

  const domainIcons  = { 'Gross Motor': '🏃', 'Fine Motor': '✋', 'Language': '🗣️', 'Social': '👥' };
  const statusConfig = {
    normal:       { cls: 'dr-normal',  icon: '🟢', label: 'Normal',        labelColor: '#2e7d32' },
    monitor:      { cls: 'dr-monitor', icon: '🟡', label: 'Monitor',       labelColor: '#7a4a10' },
    flag:         { cls: 'dr-flag',    icon: '🔴', label: 'Needs Eval.',   labelColor: '#7a1f18' },
    not_assessed: { cls: 'dr-na',      icon: '⚪', label: 'Not Assessed',  labelColor: '#9e9e9e' }
  };

  let html = '';

  // Corrected age notice
  if (data.corrected_age !== inputAge) {
    html += `<div class="alert-box alert-info"><span class="alert-icon">ℹ️</span>
      <div>Using <strong>corrected age: ${data.corrected_age} months</strong> (adjusted for prematurity) to prevent false delay alarms.</div>
    </div>`;
  }

  // Regression
  if (data.regression_alert) {
    html += `<div class="alert-box alert-alert"><span class="alert-icon">🚨</span>
      <div><strong>Regression Detected!</strong> Loss of previously acquired skills requires immediate pediatric evaluation. Please see a doctor as soon as possible.</div>
    </div>`;
  }

  // Domain status grid
  html += `<div class="card anim-fadeup"><div class="card-header"><div class="card-icon icon-clay">📊</div>
    <div><div class="card-title">Domain Assessment</div><div class="card-subtitle">Results across all 4 developmental domains</div></div></div>
    <div class="domain-result-grid">`;

  for (const [domain, status] of Object.entries(data.domain_status)) {
    const cfg = statusConfig[status] || statusConfig.not_assessed;
    html += `<div class="domain-result-card ${cfg.cls}">
      <span class="dr-icon">${domainIcons[domain] || '📌'}</span>
      <div class="dr-name">${domain}</div>
      <div class="dr-label" style="color: ${cfg.labelColor}">${cfg.icon} ${cfg.label}</div>
    </div>`;
  }
  html += '</div>';

  // Red flags
  if (data.red_flags.length > 0) {
    html += `<div class="result-block result-alert" style="margin-top: 0.5rem">
      <strong>🔴 Milestones Needing Attention (${data.red_flags.length})</strong>
      <ul style="margin-left: 1.2rem; margin-top: 0.5rem; line-height: 2; font-size: 0.875rem">
        ${data.red_flags.map(f => `<li><strong>${f.domain}:</strong> ${f.milestone} — ${f.message}</li>`).join('')}
      </ul>
    </div>`;
  }

  // Special notes
  if (data.special_notes.length > 0) {
    data.special_notes.forEach(n => {
      html += `<div class="alert-box alert-warn" style="margin-top: 0.8rem"><span class="alert-icon">💡</span><div>${n}</div></div>`;
    });
  }

  // Disclaimer
  html += `<div style="font-size: 0.78rem; color: var(--text-soft); margin-top: 1rem; line-height: 1.6; padding: 0.8rem; background: rgba(0,0,0,0.025); border-radius: var(--radius-sm)">
    ⚠️ <strong>Screening only, not diagnosis.</strong> This tool is for informational purposes. A trained professional should evaluate any concerns.
  </div></div>`;

  // Timeline chart
  html += renderTimelineChart(data, inputAge);

  // Stimulation tips
  html += `<div class="card anim-fadeup"><div class="card-header"><div class="card-icon icon-moss">🌱</div>
    <div><div class="card-title">Early Stimulation Tips</div><div class="card-subtitle">What you can do at home every day</div></div></div>
    <div class="tips-grid">`;

  const tipIcons = { 'Gross Motor': '🏃', 'Fine Motor': '✋', 'Language': '🗣️', 'Social': '👥' };
  for (const [domain, tips] of Object.entries(data.stimulation_tips)) {
    html += `<div class="tip-card">
      <div class="tip-card-header">${tipIcons[domain] || '💡'} ${domain}</div>
      <ul>${tips.map(t => `<li>${t}</li>`).join('')}</ul>
    </div>`;
  }
  html += '</div></div>';

  resultsDiv.innerHTML = html;
  resultsDiv.scrollIntoView({ behavior: 'smooth' });

  // Trigger chart render after DOM update
  setTimeout(() => renderTimelineChartCanvas(data, inputAge), 150);
}

// ── TIMELINE CHART ────────────────────────────────────────────
function renderTimelineChart(data, age) {
  return `
    <div class="card anim-fadeup">
      <div class="card-header">
        <div class="card-icon icon-sand">📈</div>
        <div><div class="card-title">Milestone Timeline View</div>
        <div class="card-subtitle">TDSC attainment windows vs. child's current age</div></div>
      </div>
      <div class="timeline-box">
        <div class="timeline-title">Each bar = normal attainment window · Orange line = your child's age</div>
        <div class="timeline-wrap"><canvas id="timelineChart"></canvas></div>
      </div>
    </div>`;
}

function renderTimelineChartCanvas(data, childAge) {
  const ctx = document.getElementById('timelineChart');
  if (!ctx) return;

  // Build datasets from answered milestones
  const labels = [];
  const starts = [];
  const durations = [];
  const colors = [];

  const statusMap = {};
  (data.red_flags || []).forEach(f => { statusMap[f.milestone] = 'flag'; });

  loadedMilestones.forEach(m => {
    const answeredKey = String(m.id);
    if (!(answeredKey in answers)) return;

    labels.push(m.label.length > 32 ? m.label.substring(0, 30) + '…' : m.label);
    starts.push(m.start);
    durations.push(m.end - m.start);

    const answered = answers[answeredKey];
    const isFlag = !answered && childAge > m.end;
    const isMonitor = !answered && childAge >= m.start && childAge <= m.end;

    colors.push(isFlag ? 'rgba(192,72,58,0.7)' : isMonitor ? 'rgba(196,123,42,0.6)' : 'rgba(90,143,90,0.65)');
  });

  new Chart(ctx, {
    type: 'bar',
    data: {
      labels,
      datasets: [
        {
          label: 'Attainment Window (months)',
          data: durations,
          backgroundColor: colors,
          borderColor: colors.map(c => c.replace('0.7', '1').replace('0.6', '1').replace('0.65', '1')),
          borderWidth: 1,
          borderRadius: 4,
          base: starts
        }
      ]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: ctx => {
              const i = ctx.dataIndex;
              return ` Normal window: ${starts[i]}–${starts[i] + durations[i]} months`;
            }
          }
        },
        annotation: {
          // We'll draw the child age line manually
        }
      },
      scales: {
        x: {
          min: 0, max: 36,
          title: { display: true, text: 'Age (months)', font: { family: 'Nunito', size: 11 } },
          grid: { color: 'rgba(0,0,0,0.05)' },
          ticks: { font: { family: 'Nunito', size: 10 } }
        },
        y: {
          ticks: { font: { family: 'Nunito', size: 10 }, color: '#7a6355' },
          grid: { display: false }
        }
      }
    },
    plugins: [{
      id: 'childAgeLine',
      afterDraw(chart) {
        const { ctx: c, chartArea, scales } = chart;
        const xPos = scales.x.getPixelForValue(childAge);
        if (xPos < chartArea.left || xPos > chartArea.right) return;

        c.save();
        c.beginPath();
        c.moveTo(xPos, chartArea.top);
        c.lineTo(xPos, chartArea.bottom);
        c.strokeStyle = '#c97b5a';
        c.lineWidth = 2.5;
        c.setLineDash([6, 4]);
        c.stroke();

        c.fillStyle = '#c97b5a';
        c.font = '700 11px Nunito';
        c.textAlign = 'center';
        c.fillText(`${childAge}m`, xPos, chartArea.top - 6);
        c.restore();
      }
    }]
  });
}