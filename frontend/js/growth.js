// ── GROWTH MODULE JS ─────────────────────────────────────────
// WHO Z-score analysis + Chart.js visualization

const API = 'http://localhost:8001';

// Active tab switcher
function switchTab(tab) {
  document.querySelectorAll('.submodule-panel').forEach(p => p.classList.remove('active'));
  document.querySelectorAll('.stab').forEach(t => t.classList.remove('active'));
  document.getElementById('panel_' + tab).classList.add('active');
  event.target.classList.add('active');
}

// ── ANALYZE GROWTH ────────────────────────────────────────────
async function analyzeGrowth(type) {
  const age    = parseFloat(document.getElementById('g_age').value);
  const sex    = document.getElementById('g_sex').value;
  const resultDiv = document.getElementById('result_' + type);

  if (!age || isNaN(age)) {
    showError(resultDiv, 'Please enter the child\'s age in months before analyzing.'); return;
  }

  let payload = { age_months: age, sex };

  if (type === 'weight') {
    const w = parseFloat(document.getElementById('g_weight').value);
    if (!w) { showError(resultDiv, 'Please enter the child\'s weight.'); return; }
    payload.weight_kg = w;
  } else if (type === 'length') {
    const l = parseFloat(document.getElementById('g_length').value);
    if (!l) { showError(resultDiv, 'Please enter the child\'s length/height.'); return; }
    payload.length_cm = l;
  } else if (type === 'hc') {
    const h = parseFloat(document.getElementById('g_hc').value);
    if (!h) { showError(resultDiv, 'Please enter the head circumference.'); return; }
    payload.hc_cm = h;
  }

  resultDiv.innerHTML = loadingHTML();

  try {
    const res  = await fetch(`${API}/api/growth/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    const data = await res.json();

    if (!data.success) throw new Error('Analysis failed');

    if (type === 'weight' && data.results.weight_for_age)
      renderWeightResult(data.results.weight_for_age, age, sex, payload.weight_kg, resultDiv);
    else if (type === 'length' && data.results.length_for_age)
      renderLengthResult(data.results.length_for_age, age, sex, payload.length_cm, resultDiv);
    else if (type === 'hc' && data.results.head_circumference)
      renderHCResult(data.results.head_circumference, age, sex, payload.hc_cm, resultDiv);

  } catch (e) {
    showError(resultDiv, 'Could not reach the backend. Make sure the server is running on port 8000.');
  }
}

// ── WEIGHT RESULT ─────────────────────────────────────────────
function renderWeightResult(r, age, sex, weight, div) {
  const { statusClass, statusLabel } = getStatusInfo(r.z_score, 'weight');

  div.innerHTML = `
    <div class="card anim-fadeup">
      <div class="card-header">
        <div class="card-icon icon-clay">⚖️</div>
        <div><div class="card-title">Weight-for-Age Result</div><div class="card-subtitle">${sex === 'boys' ? 'Boy' : 'Girl'}, ${age} months · ${weight} kg</div></div>
      </div>

      <div class="result-summary">
        <div class="zscore-big">
          <div class="zscore-big-num">${r.z_score}</div>
          <div class="zscore-big-label">Z-Score</div>
        </div>
        <div class="result-detail">
          <div class="pill ${statusClass}" style="margin-bottom: 8px">${statusLabel}</div>
          <h3 style="font-family: 'Lora', serif">${r.status}</h3>
          <p style="font-size: 0.85rem; color: var(--text-mid); margin-top: 4px">${getStatusDesc(r.z_score, 'weight')}</p>
        </div>
      </div>

      ${r.ftt_risk ? `<div class="ftt-banner">⚠️ Possible Failure to Thrive (FTT) detected — weight below 3rd percentile. Monitor closely and consult a pediatrician.</div>` : ''}

      <div class="result-block ${getBlockClass(r.z_score, 'weight')}" style="margin-top: 1rem">
        <strong>What to do next</strong>
        <p>${r.guidance}</p>
      </div>

      ${renderZScoreBar(r.z_score)}
      ${renderWeightChart(age, sex, weight)}
    </div>`;
}

// ── LENGTH RESULT ─────────────────────────────────────────────
function renderLengthResult(r, age, sex, length, div) {
  const { statusClass } = getStatusInfo(r.z_score, 'length');

  div.innerHTML = `
    <div class="card anim-fadeup">
      <div class="card-header">
        <div class="card-icon icon-moss">📐</div>
        <div><div class="card-title">Length-for-Age Result</div><div class="card-subtitle">${sex === 'boys' ? 'Boy' : 'Girl'}, ${age} months · ${length} cm</div></div>
      </div>

      <div class="result-summary">
        <div class="zscore-big">
          <div class="zscore-big-num">${r.z_score}</div>
          <div class="zscore-big-label">Z-Score</div>
        </div>
        <div class="result-detail">
          <div class="pill ${statusClass}" style="margin-bottom: 8px">${r.status}</div>
          <p style="font-size: 0.85rem; color: var(--text-mid)">${getStatusDesc(r.z_score, 'length')}</p>
        </div>
      </div>

      <div class="result-block ${getBlockClass(r.z_score, 'length')}" style="margin-top: 1rem">
        <strong>What to do next</strong>
        <p>${r.guidance}</p>
      </div>

      ${renderZScoreBar(r.z_score)}
      ${renderLengthChart(age, sex, length)}
    </div>`;
}

// ── HC RESULT ─────────────────────────────────────────────────
function renderHCResult(r, age, sex, hc, div) {
  const isAlert = r.z_score < -2 || r.z_score > 2;

  div.innerHTML = `
    <div class="card anim-fadeup">
      <div class="card-header">
        <div class="card-icon icon-sand">🔵</div>
        <div><div class="card-title">Head Circumference Result</div><div class="card-subtitle">${sex === 'boys' ? 'Boy' : 'Girl'}, ${age} months · ${hc} cm</div></div>
      </div>

      <div class="result-summary">
        <div class="zscore-big">
          <div class="zscore-big-num">${r.z_score}</div>
          <div class="zscore-big-label">Z-Score</div>
        </div>
        <div class="result-detail">
          <div class="pill ${isAlert ? 'pill-alert' : 'pill-ok'}" style="margin-bottom: 8px">${r.status}</div>
          <p style="font-size: 0.85rem; color: var(--text-mid)">${r.status === 'Normal Head Growth' ? 'Head circumference is within the expected range for age.' : 'Head circumference is outside the normal range for age.'}</p>
        </div>
      </div>

      ${isAlert ? `<div class="alert-box alert-alert"><span class="alert-icon">🏥</span><div>Head circumference abnormalities <strong>cannot be corrected through diet or exercise</strong>. Please consult a pediatrician or neurologist for evaluation.</div></div>` : ''}

      <div class="result-block ${isAlert ? 'result-alert' : 'result-ok'}" style="margin-top: 0.5rem">
        <strong>What to do next</strong>
        <p>${r.guidance}</p>
      </div>

      ${renderZScoreBar(r.z_score)}
      ${renderHCChart(age, sex, hc)}
    </div>`;
}

// ── Z-SCORE BAR ───────────────────────────────────────────────
function renderZScoreBar(z) {
  const pct = Math.min(Math.max(((z + 4) / 8) * 100, 2), 98);
  const markerColor = z < -2 ? 'var(--alert)' : z > 2 ? 'var(--warn)' : 'var(--moss)';
  return `
    <div class="zscore-meter-wrap">
      <div class="zscore-label-row">
        <span>−3 SD (Severe)</span>
        <span>−2 SD</span>
        <span>Median</span>
        <span>+2 SD</span>
        <span>+3 SD</span>
      </div>
      <div class="zscore-track">
        <div class="zscore-marker" style="left: ${pct}%; border-color: ${markerColor}"></div>
      </div>
    </div>`;
}

// ── CHART: WEIGHT FOR AGE ─────────────────────────────────────
function renderWeightChart(age, sex, weight) {
  const canvasId = 'chart_weight_' + Date.now();

  // Approximate WHO reference centiles (boys, simplified)
  const refData = {
    boys: {
      ages:  [0,  1,  2,  3,  4,  5,  6,  9,  12, 18, 24, 36, 48, 60],
      p3:    [2.5,3.4,4.4,5.1,5.6,6.1,6.4,7.1,7.8,9.2,10.2,12.1,13.9,15.5],
      p15:   [2.9,3.9,4.9,5.6,6.2,6.7,7.1,7.8,8.6,10.1,11.3,13.4,15.3,17.2],
      p50:   [3.3,4.5,5.6,6.4,7.0,7.5,7.9,8.9,9.6,11.0,12.1,14.3,16.3,18.3],
      p85:   [3.9,5.1,6.3,7.1,7.9,8.5,8.9,10.1,11.0,12.6,13.9,16.4,18.7,21.0],
      p97:   [4.3,5.7,7.1,8.0,8.9,9.5,10.0,11.4,12.4,14.2,15.7,18.5,21.1,23.9],
    },
    girls: {
      ages:  [0,  1,  2,  3,  4,  5,  6,  9,  12, 18, 24, 36, 48, 60],
      p3:    [2.4,3.2,4.0,4.6,5.1,5.5,5.8,6.6,7.1,8.2,9.1,10.9,12.4,14.0],
      p15:   [2.8,3.6,4.5,5.2,5.8,6.2,6.6,7.5,8.1,9.5,10.6,12.7,14.5,16.3],
      p50:   [3.2,4.2,5.1,5.8,6.4,6.9,7.3,8.2,8.9,10.2,11.5,13.9,15.9,17.9],
      p85:   [3.7,4.8,5.9,6.7,7.4,8.0,8.4,9.6,10.5,12.1,13.6,16.4,18.8,21.2],
      p97:   [4.2,5.5,6.7,7.6,8.4,9.0,9.5,10.9,11.8,13.8,15.5,18.7,21.5,24.3],
    }
  };

  const d = refData[sex] || refData.boys;

  setTimeout(() => {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: d.ages,
        datasets: [
          { label: '3rd', data: d.p3,  borderColor: '#e17055', borderWidth: 1.5, fill: false, pointRadius: 0, borderDash: [4,4] },
          { label: '15th', data: d.p15, borderColor: '#fdcb6e', borderWidth: 1.5, fill: false, pointRadius: 0, borderDash: [4,4] },
          { label: '50th (Median)', data: d.p50, borderColor: '#7a9e6e', borderWidth: 2.5, fill: false, pointRadius: 0 },
          { label: '85th', data: d.p85, borderColor: '#fdcb6e', borderWidth: 1.5, fill: false, pointRadius: 0, borderDash: [4,4] },
          { label: '97th', data: d.p97, borderColor: '#e17055', borderWidth: 1.5, fill: false, pointRadius: 0, borderDash: [4,4] },
          { label: 'Your Child', data: [{ x: age, y: weight }], borderColor: '#c97b5a', backgroundColor: '#c97b5a',
            pointRadius: 9, pointHoverRadius: 11, showLine: false, type: 'scatter' }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: {
          legend: { position: 'top', labels: { font: { family: 'Nunito', size: 11 }, boxWidth: 20, padding: 12 } },
          tooltip: { callbacks: {
            label: ctx => ctx.dataset.label === 'Your Child'
              ? `Your child: ${weight} kg at ${age} months`
              : `${ctx.dataset.label}: ${ctx.parsed.y} kg`
          }}
        },
        scales: {
          x: { title: { display: true, text: 'Age (months)', font: { family: 'Nunito', size: 11 } },
               grid: { color: 'rgba(0,0,0,0.04)' } },
          y: { title: { display: true, text: 'Weight (kg)', font: { family: 'Nunito', size: 11 } },
               grid: { color: 'rgba(0,0,0,0.04)' } }
        }
      }
    });
  }, 100);

  return `
    <div class="chart-box">
      <div class="chart-title">WHO Weight-for-Age Chart — ${sex === 'boys' ? 'Boys' : 'Girls'} 0–60 months</div>
      <div class="chart-wrap"><canvas id="${canvasId}"></canvas></div>
    </div>`;
}

// ── CHART: LENGTH FOR AGE ─────────────────────────────────────
function renderLengthChart(age, sex, length) {
  const canvasId = 'chart_len_' + Date.now();

  const refData = {
    boys: {
      ages: [0, 3, 6, 9, 12, 18, 24, 36, 48, 60],
      p3:   [46.1, 57.6, 63.3, 67.7, 71.0, 76.0, 80.0, 87.2, 93.7, 99.9],
      p50:  [49.9, 61.4, 67.6, 72.0, 75.7, 82.3, 87.8, 96.1, 103.3, 110.0],
      p97:  [53.4, 65.5, 72.3, 77.0, 81.2, 88.4, 95.3, 104.5, 112.7, 120.0],
    },
    girls: {
      ages: [0, 3, 6, 9, 12, 18, 24, 36, 48, 60],
      p3:   [45.4, 55.8, 61.2, 65.3, 68.9, 74.0, 78.0, 85.8, 92.2, 98.4],
      p50:  [49.1, 59.8, 65.7, 70.1, 74.0, 80.7, 86.4, 95.1, 102.7, 109.4],
      p97:  [52.9, 64.0, 70.4, 75.5, 79.7, 87.6, 94.7, 103.1, 111.4, 119.0],
    }
  };

  const d = refData[sex] || refData.boys;

  setTimeout(() => {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: d.ages,
        datasets: [
          { label: '3rd (Stunting)', data: d.p3, borderColor: '#e17055', borderWidth: 1.5, fill: false, pointRadius: 0, borderDash: [4,4] },
          { label: '50th (Median)',  data: d.p50, borderColor: '#7a9e6e', borderWidth: 2.5, fill: false, pointRadius: 0 },
          { label: '97th',          data: d.p97, borderColor: '#e17055', borderWidth: 1.5, fill: false, pointRadius: 0, borderDash: [4,4] },
          { label: 'Your Child', data: [{ x: age, y: length }], borderColor: '#c97b5a', backgroundColor: '#c97b5a',
            pointRadius: 9, pointHoverRadius: 11, showLine: false, type: 'scatter' }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'top', labels: { font: { family: 'Nunito', size: 11 }, boxWidth: 20 } } },
        scales: {
          x: { title: { display: true, text: 'Age (months)', font: { family: 'Nunito', size: 11 } }, grid: { color: 'rgba(0,0,0,0.04)' } },
          y: { title: { display: true, text: 'Length/Height (cm)', font: { family: 'Nunito', size: 11 } }, grid: { color: 'rgba(0,0,0,0.04)' } }
        }
      }
    });
  }, 100);

  return `
    <div class="chart-box">
      <div class="chart-title">WHO Length/Height-for-Age Chart — ${sex === 'boys' ? 'Boys' : 'Girls'}</div>
      <div class="chart-wrap"><canvas id="${canvasId}"></canvas></div>
    </div>`;
}

// ── CHART: HEAD CIRCUMFERENCE ─────────────────────────────────
function renderHCChart(age, sex, hc) {
  const canvasId = 'chart_hc_' + Date.now();

  const refData = {
    boys: {
      ages: [0, 3, 6, 9, 12, 18, 24, 36, 48, 60],
      p3:   [31.9, 37.9, 41.0, 43.0, 44.5, 46.2, 47.2, 48.5, 49.2, 49.8],
      p50:  [34.5, 40.5, 43.3, 45.3, 46.6, 48.0, 49.0, 50.3, 51.0, 51.7],
      p97:  [37.1, 43.3, 45.9, 47.9, 49.3, 50.8, 51.7, 53.0, 53.7, 54.4],
    },
    girls: {
      ages: [0, 3, 6, 9, 12, 18, 24, 36, 48, 60],
      p3:   [31.5, 37.1, 40.0, 41.8, 43.2, 44.8, 45.9, 47.2, 47.9, 48.6],
      p50:  [33.9, 39.5, 42.2, 44.2, 45.4, 46.9, 47.8, 49.1, 49.8, 50.5],
      p97:  [36.2, 42.0, 44.9, 46.9, 48.2, 49.7, 50.6, 52.0, 52.7, 53.4],
    }
  };

  const d = refData[sex] || refData.boys;

  setTimeout(() => {
    const ctx = document.getElementById(canvasId)?.getContext('2d');
    if (!ctx) return;
    new Chart(ctx, {
      type: 'line',
      data: {
        labels: d.ages,
        datasets: [
          { label: '3rd (Microcephaly risk)', data: d.p3, borderColor: '#e17055', borderWidth: 1.5, fill: false, pointRadius: 0, borderDash: [4,4] },
          { label: '50th (Median)',           data: d.p50, borderColor: '#7a9e6e', borderWidth: 2.5, fill: false, pointRadius: 0 },
          { label: '97th (Macrocephaly risk)',data: d.p97, borderColor: '#e17055', borderWidth: 1.5, fill: false, pointRadius: 0, borderDash: [4,4] },
          { label: 'Your Child', data: [{ x: age, y: hc }], borderColor: '#c97b5a', backgroundColor: '#c97b5a',
            pointRadius: 9, pointHoverRadius: 11, showLine: false, type: 'scatter' }
        ]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { position: 'top', labels: { font: { family: 'Nunito', size: 11 }, boxWidth: 20 } } },
        scales: {
          x: { title: { display: true, text: 'Age (months)', font: { family: 'Nunito', size: 11 } }, grid: { color: 'rgba(0,0,0,0.04)' } },
          y: { title: { display: true, text: 'Head Circumference (cm)', font: { family: 'Nunito', size: 11 } }, grid: { color: 'rgba(0,0,0,0.04)' } }
        }
      }
    });
  }, 100);

  return `
    <div class="chart-box">
      <div class="chart-title">WHO Head Circumference-for-Age Chart — ${sex === 'boys' ? 'Boys' : 'Girls'}</div>
      <div class="chart-wrap"><canvas id="${canvasId}"></canvas></div>
    </div>`;
}

// ── HELPERS ───────────────────────────────────────────────────
function getStatusInfo(z, type) {
  if (type === 'hc') {
    if (z < -2 || z > 2) return { statusClass: 'pill-alert', statusLabel: '🔴 Abnormal' };
    return { statusClass: 'pill-ok', statusLabel: '🟢 Normal' };
  }
  if (z < -3) return { statusClass: 'pill-alert', statusLabel: '🔴 Severe' };
  if (z < -2) return { statusClass: 'pill-warn',  statusLabel: '🟡 Monitor' };
  if (z > 2)  return { statusClass: 'pill-warn',  statusLabel: '🟡 Overweight' };
  return { statusClass: 'pill-ok', statusLabel: '🟢 Normal' };
}

function getStatusDesc(z, type) {
  if (type === 'weight') {
    if (z < -3) return 'Severe underweight — significantly below the 3rd percentile.';
    if (z < -2) return 'Underweight — below the expected range for this age.';
    if (z > 2)  return 'Above expected weight range — monitor dietary habits.';
    return 'Weight is within the healthy range for this age.';
  }
  if (type === 'length') {
    if (z < -3) return 'Severe stunting — significant chronic growth deficit.';
    if (z < -2) return 'Stunting detected — height is below expected for age.';
    return 'Height is within the normal range for this age.';
  }
  return '';
}

function getBlockClass(z, type) {
  if (type === 'hc') return (z < -2 || z > 2) ? 'result-alert' : 'result-ok';
  if (z < -2) return 'result-alert';
  if (z > 2)  return 'result-warn';
  return 'result-ok';
}

function loadingHTML() {
  return `<div class="card"><div class="loading-dots"><div class="dot"></div><div class="dot"></div><div class="dot"></div> Analyzing...</div></div>`;
}

function showError(div, msg) {
  div.innerHTML = `<div class="card"><div class="alert-box alert-alert"><span class="alert-icon">❌</span><div>${msg}</div></div></div>`;
}