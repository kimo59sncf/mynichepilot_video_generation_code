/* ============================================================================
   MyNichePilot — Studio VIP · Logique applicative
   ========================================================================== */
'use strict';

const state = {
  config: null,
  health: null,
  videos: [],
  status: null,
  selectedSeq: null,       // null = pipeline complet, sinon 1..5
  running: false,
  currentStage: null,
  renderedCount: 0,
  totalToRender: 5,
  es: null,
  timer: null,
  startedAt: null,
};

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));

function apiFetch(path, opts) {
  return fetch(path, opts).then((r) => {
    const ctype = r.headers.get('content-type') || '';
    if (ctype.includes('application/json')) return r.json();
    return r.text();
  });
}

function fmtTime(sec) {
  if (sec == null || isNaN(sec)) return '—';
  sec = Math.floor(sec);
  const m = Math.floor(sec / 60);
  const s = sec % 60;
  return m > 0 ? `${m}m ${s.toString().padStart(2, '0')}s` : `${s}s`;
}

function fmtSize(b) {
  if (b == null || isNaN(b)) return '—';
  const units = ['o', 'Ko', 'Mo', 'Go'];
  let i = 0;
  while (b >= 1024 && i < units.length - 1) { b /= 1024; i++; }
  return (i === 0 ? Math.round(b) : b.toFixed(1)) + ' ' + units[i];
}

function escapeHtml(s) {
  return String(s ?? '').replace(/[&<>"']/g, (c) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
  }[c]));
}

let toastTimer = null;
function toast(msg, type = 'info') {
  const el = $('#toast');
  el.textContent = msg;
  el.className = 'toast show ' + type;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.remove('show'), 3400);
}

/* ------- légende sociale & copie ------- */
function socialText(v) {
  return ((v && v.caption) || '') + '\n\n' + ((v && v.hashtags_str) || '').trim();
}

async function copyVideoCaption(name) {
  const v = (state.videos || []).find((x) => x.name === name);
  if (!v) return;
  const text = socialText(v);
  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
    } else {
      const ta = document.createElement('textarea');
      ta.value = text;
      ta.style.position = 'fixed';
      ta.style.opacity = '0';
      document.body.appendChild(ta);
      ta.select();
      document.execCommand('copy');
      ta.remove();
    }
    toast('Légende + hashtags copiés 📋', 'success');
  } catch (e) {
    toast('Impossible de copier automatiquement.', 'error');
  }
}
window.copyVideoCaption = copyVideoCaption;

/* ------- fond étoilé ------- */
function buildStars() {
  const wrap = $('#stars');
  const count = 90;
  for (let i = 0; i < count; i++) {
    const s = document.createElement('span');
    s.className = 'star';
    const size = Math.random() * 2.4 + 0.6;
    s.style.width = size + 'px';
    s.style.height = size + 'px';
    s.style.left = Math.random() * 100 + '%';
    s.style.top = Math.random() * 100 + '%';
    s.style.setProperty('--dur', (Math.random() * 6 + 3) + 's');
    s.style.animationDelay = Math.random() * 5 + 's';
    wrap.appendChild(s);
  }
}

/* ------- navigation ------- */
const SECTIONS = ['dashboard', 'studio', 'sequences', 'outputs', 'system'];
const SECTION_TITLES = {
  dashboard: 'Tableau de bord',
  studio: 'Studio de production',
  sequences: 'Séquences',
  outputs: 'Sorties vidéo',
  system: 'État du système',
};

function switchSection(name) {
  $$('.nav-item').forEach((b) => b.classList.toggle('active', b.dataset.section === name));
  $$('.section').forEach((s) => s.classList.toggle('is-active', s.id === 'section-' + name));
  $('#pageTitle').textContent = SECTION_TITLES[name] || name;
  $('#pageSubtitle').textContent = name === 'studio'
    ? 'Lance et supervise la génération en direct'
    : 'Production vidéo publicitaire 9:16';
}

function bindNav() {
  $$('.nav-item').forEach((b) => b.addEventListener('click', () => switchSection(b.dataset.section)));
  $$('[data-goto]').forEach((b) => b.addEventListener('click', () => switchSection(b.dataset.goto)));
  $('#heroLaunch').addEventListener('click', () => { switchSection('studio'); launch(true); });
}

/* ------- rendu : dashboard ------- */
const PIPELINE = [
  { key: 'assets', title: 'Initialisation & assets', desc: 'Polices, boussole, fond cosmique' },
  { key: 'voice', title: 'Voix off neuronale', desc: 'Edge-TTS fr-FR-HenriNeural' },
  { key: 'music', title: 'Musique & SFX', desc: 'Electro 120 BPM + 4 bruitages' },
  { key: 'mix', title: 'Mixage & ducking', desc: 'Sidechain -8 dB sous la voix' },
  { key: 'render', title: 'Rendu & encodage', desc: 'Pillow + FFmpeg H.264 1080×1920' },
  { key: 'master', title: 'Master final', desc: 'Concaténation des 5 séquences' },
];

function renderPipeline(activeKey) {
  const list = $('#pipelineList');
  if (!list) return;
  const activeIdx = Math.max(0, PIPELINE.findIndex((p) => p.key === activeKey));
  list.innerHTML = PIPELINE.map((p, i) => {
    let cls = '';
    if (state.status && (state.status.status === 'finished' || state.status.status === 'stopped') && i < activeIdx) cls = 'done';
    if (i < activeIdx && state.running) cls = 'done';
    if (i === activeIdx && (state.running || (state.status && state.status.status !== 'idle'))) cls = 'active';
    return `<li class="${cls}">
      <span class="step-num">${i + 1}</span>
      <span class="step-body">
        <span class="step-title">${p.title}</span>
        <span class="step-desc">${p.desc}</span>
      </span>
      <span class="step-dot"></span>
    </li>`;
  }).join('');
}

function renderStats() {
  const c = state.config;
  const totalFrames = c ? Math.round(c.total_duration * c.fps) : 0;
  const produced = state.videos.length;
  const master = state.videos.find((v) => v.is_master);
  const stats = [
    { label: 'Séquences', value: c ? c.sequences.length : '—', unit: 'clips', trend: '5 narrations continues' },
    { label: 'Durée totale', value: c ? c.total_duration.toFixed(1) : '—', unit: 'sec', trend: '9:16 vertical' },
    { label: 'Images générées', value: totalFrames.toLocaleString('fr-FR') || '—', unit: 'frames', trend: `${c ? c.fps : 30} FPS` },
    { label: 'Vidéos produites', value: produced, unit: master ? 'master ✓' : 'fichiers', trend: master ? 'Master disponible' : 'Aucun master pour l’instant' },
  ];
  $('#statsGrid').innerHTML = stats.map((s) => `
    <div class="stat">
      <div class="stat-label">${s.label}</div>
      <div class="stat-value">${s.value} <span class="unit">${s.unit}</span></div>
      <div class="stat-trend">${s.trend}</div>
    </div>`).join('');
}

const PALETTE_KEYS = [
  ['fond_nuit', 'Fond nuit', '#000b15'],
  ['fond_mid', 'Bleu nuit', '#091039'],
  ['gold', 'Or chaud', '#fcd34d'],
  ['amber', 'Ambre', '#eca760'],
  ['orange', 'Orange', '#f59e0b'],
  ['emerald', 'Émeraude', '#34d399'],
  ['cyan', 'Cyan data', '#60a5fa'],
  ['red', 'Alerte', '#ef4444'],
];

function renderPalette() {
  $('#palette').innerHTML = PALETTE_KEYS.map(([key, name, hex]) => `
    <div class="swatch">
      <span class="chip" style="background:${hex}"></span>
      <span class="sw-name">${name}</span>
      <span class="sw-hex">${hex}</span>
    </div>`).join('');
}

/* ------- rendu : séquences ------- */
const SEQ_ICONS = ['⚡', '🎯', '📊', '🚀', '🏆'];
const SEQ_COLORS = [['#ef4444', '#38,16,26'], ['#f59e0b', '#55,38,15'], ['#60a5fa', '#16,26,64'], ['#34d399', '#18,55,70'], ['#fcd34d', '#55,38,15']];

function renderSequences() {
  const c = state.config;
  if (!c) return;
  $('#seqGrid').innerHTML = c.sequences.map((s) => {
    const [icon, rgb] = [SEQ_ICONS[s.id - 1], SEQ_COLORS[s.id - 1][1]];
    const [fg] = SEQ_COLORS[s.id - 1][0];
    return `
      <article class="seq-card">
        <div class="seq-post" style="background:linear-gradient(135deg, rgba(${rgb},.85), rgba(9,16,57,.92));">
          <span class="seq-num-big">${String(s.id).padStart(2, '0')}</span>
          <span class="seq-icon" style="background:rgba(0,0,0,.25);border:1px solid ${fg}">${icon}</span>
        </div>
        <div class="seq-body">
          <h4 class="seq-title">${escapeHtml(s.title)}</h4>
          <span class="seq-dur">${s.duration.toFixed(2)} s · ${Math.round(s.duration * c.fps)} frames</span>
          <p class="seq-voice">${escapeHtml(s.voice_text)}</p>
          <div class="seq-sfx">${(s.sfx || []).map((x) => `<span class="sfx-tag">${escapeHtml(x)}</span>`).join('')}</div>
        </div>
      </article>`;
  }).join('');
}

function renderChips() {
  const c = state.config;
  if (!c) return;
  const all = '<button class="chip active" data-seq="">Tout le pipeline</button>';
  const rest = c.sequences.map((s) => `<button class="chip" data-seq="${s.id}">Seq ${s.id}</button>`).join('');
  $('#seqChips').innerHTML = all + rest;
  $$('#seqChips .chip').forEach((chip) => chip.addEventListener('click', () => {
    $$('#seqChips .chip').forEach((x) => x.classList.remove('active'));
    chip.classList.add('active');
    state.selectedSeq = chip.dataset.seq === '' ? null : parseInt(chip.dataset.seq, 10);
    state.totalToRender = state.selectedSeq ? 1 : c.sequences.length;
  }));
}

/* ------- rendu : sorties vidéo ------- */
function renderVideos() {
  const grid = $('#videosGrid');
  if (!grid) return;
  if (!state.videos.length) {
    grid.innerHTML = `<div class="empty-state"><div class="big">🎬</div><p>Aucune vidéo générée pour le moment.<br/>Lance la production depuis le Studio.</p></div>`;
    return;
  }
  grid.innerHTML = state.videos.map((v) => {
    const url = '/api/video/' + encodeURIComponent(v.name);
    const masterBadge = v.is_master ? '🏆 Master officiel' : (v.sequence_id ? 'Séquence ' + v.sequence_id : 'Clip');
    return `
      <article class="video-card">
        <div class="v-head">
          <span class="v-thumb">${v.is_master ? '🏆' : '🎞️'}</span>
          <div class="v-info">
            <div class="v-name" title="${escapeHtml(v.name)}">${escapeHtml(v.name)}</div>
            <div class="v-meta">${fmtSize(v.size)} · ${new Date(v.mtime * 1000).toLocaleString('fr-FR')} · ${masterBadge}</div>
          </div>
        </div>
        <video controls preload="metadata" src="${url}"></video>
        ${v.caption ? `
        <div class="v-caption">
          <div class="v-caption-head">
            <span class="v-caption-label">📝 Légende sociale</span>
            <button class="btn btn-mini" onclick="copyVideoCaption('${escapeHtml(v.name)}')">Copier</button>
          </div>
          <p class="v-caption-text">${escapeHtml(v.caption)}</p>
          ${(v.hashtags || []).length ? `<div class="v-hashtags">${v.hashtags.map((h) => `<span class="sfx-tag">${escapeHtml(h)}</span>`).join('')}</div>` : ''}
        </div>` : ''}
        <div class="v-actions">
          <a class="btn btn-outline" href="${url}" download="${escapeHtml(v.name)}">Télécharger</a>
          <a class="btn btn-outline" href="${url}" target="_blank" rel="noopener">Ouvrir</a>
        </div>
      </article>`;
  }).join('');
}

/* ------- rendu : système ------- */
function renderSystem() {
  const grid = $('#systemGrid');
  if (!grid || !state.health) return;
  const h = state.health;
  const cards = [];
  cards.push(sysCard('🐍', 'Python', h.python, (h.python ? 'ok' : 'ko'), h.python_executable || ''));
  cards.push(sysCard('🎞️', 'FFmpeg', (h.ffmpeg && h.ffmpeg.ok) ? (h.ffmpeg.version || 'détecté') : 'Non détecté', (h.ffmpeg && h.ffmpeg.ok) ? 'ok' : 'ko', h.ffmpeg && h.ffmpeg.path ? h.ffmpeg.path : 'Requis pour l’encodage vidéo'));
  cards.push(sysCard('🧩', 'Générateur vidéo', h.generator_importable ? 'Importable' : 'Erreur import', h.generator_importable ? 'ok' : 'ko', h.generator_error || 'generate_video_mynichepilot.py'));
  const deps = Object.entries(h.deps || {});
  ['pillow', 'numpy', 'scipy', 'edge_tts'].forEach((name) => {
    const d = (h.deps || {})[name];
    if (!d) return;
    cards.push(sysCard('📦', name, d.ok ? ('v' + d.version) : d.error || 'manquant', d.ok ? 'ok' : 'ko', ''));
  });
  cards.push(sysCard('📂', 'Dossier de sortie', 'output/', 'ok', h.output_dir || ''));
  grid.innerHTML = cards.join('');
}

function sysCard(icon, name, detail, status, sub) {
  return `
    <div class="sys-card">
      <span class="sys-icon" style="background:rgba(96,165,250,.1)">${icon}</span>
      <div>
        <div class="sys-name">${escapeHtml(name)}</div>
        <div class="sys-detail">${escapeHtml(detail)}${sub ? '<br/>' + escapeHtml(sub) : ''}</div>
        <span class="sys-status ${status}">${status === 'ok' ? '✓ Opérationnel' : '✗ Manquant'}</span>
      </div>
    </div>`;
}

/* ------- console & logs ------- */
const MAX_LOG_LINES = 400;
let logLineCount = 0;

function classifyLine(line) {
  const t = line.trim();
  if (/^[$].*/.test(t) || /python.*generate_video|generate_video.*\.py/.test(t)) return 'cmd';
  if (/^(✔|✓|✅|🎉)/.test(t) || /succès|TERMINÉ|prêt|Prêt|finalisée|mixé|générée|prête/i.test(t)) return 'green';
  if (/^(✖|❌|⚠)/.test(t) || /erreur|échec|Erreur|introuvable|crash/i.test(t)) return 'red';
  if (/^(ℹ|⚙)/.test(t) || /détecté/.test(t)) return 'amber';
  if (/^(>>>|---|===)/.test(t) || /Étape|Concaténation|MASTER|production/i.test(t)) return 'gold';
  if (/^(>>> Rendu)/.test(t) || /Synthèse|Mixage/i.test(t)) return 'cyan';
  return 'dim';
}

function appendLog(raw, color) {
  const consoleEl = $('#console');
  if (!consoleEl) return;
  const line = document.createElement('div');
  line.className = 'console-line ' + (color || classifyLine(raw || ''));
  line.textContent = raw || ' ';
  consoleEl.appendChild(line);
  logLineCount++;
  if (logLineCount > MAX_LOG_LINES) {
    while (consoleEl.children.length > MAX_LOG_LINES) consoleEl.removeChild(consoleEl.firstChild);
  }
  const counter = $('#logCount');
  if (counter) counter.textContent = logLineCount + ' ligne' + (logLineCount > 1 ? 's' : '');
  consoleEl.scrollTop = consoleEl.scrollHeight;
}

function clearConsole() {
  const consoleEl = $('#console');
  if (consoleEl) consoleEl.innerHTML = '';
  logLineCount = 0;
  const counter = $('#logCount');
  if (counter) counter.textContent = '0 ligne';
}

/* ------- progression & stages ------- */
const STAGE_MAP = [
  { key: 'assets', re: /Étape 1|Initialisation des assets/i, pct: 5, label: 'Initialisation des assets' },
  { key: 'voice', re: /Étape 2\.1|Synthèse vocale|Edge-TTS/i, pct: 12, label: 'Voix off neuronale' },
  { key: 'music', re: /Étape 2\.2|musique électro/i, pct: 28, label: 'Musique & SFX procéduraux' },
  { key: 'mix', re: /Étape 2\.3|Mixage/i, pct: 40, label: 'Mixage & ducking' },
  { key: 'render', re: /Rendu vidéo : sequence_/i, pct: 45, label: 'Rendu & encodage FFmpeg' },
  { key: 'master', re: /Concaténation/i, pct: 96, label: 'Assemblage du master' },
];

function setProgress(pct, indeterminate) {
  const fill = $('#progressFill');
  if (!fill) return;
  if (indeterminate) {
    fill.className = 'progress-fill indeterminate';
    return;
  }
  fill.className = 'progress-fill';
  fill.style.width = Math.min(100, Math.max(0, pct)) + '%';
}

function setStage(key, label) {
  state.currentStage = key;
  const tag = $('#stageTag');
  if (tag && label) tag.textContent = label;
  renderPipeline(key);
}

function detectStage(raw) {
  for (const st of STAGE_MAP) {
    if (st.re.test(raw)) {
      setStage(st.key, st.label);
      setProgress(st.pct);
      if (st.key === 'render') {
        const m = raw.match(/sequence_(\d)/);
        if (m) {
          const meta = $('#metaSeq');
          if (meta) meta.textContent = 'Séquence ' + m[1];
        }
      }
      return;
    }
  }
  // fin de rendu d'une séquence
  if (/Séquence finalisée/i.test(raw)) {
    state.renderedCount++;
    const pct = 45 + (state.renderedCount / Math.max(1, state.totalToRender)) * 50;
    setProgress(pct);
  }
}

function handleState(payload) {
  const status = payload.s;
  const wasRunning = state.running;
  state.running = status === 'running';
  if (state.status) state.status.status = status;
  if (payload.exit_code != null && state.status) state.status.exit_code = payload.exit_code;

  if (state.running && !wasRunning) startTimer();
  if (!state.running && wasRunning) stopTimer();

  if (status === 'running') {
    state.renderedCount = 0;
    setStage('assets', 'Initialisation…');
    setProgress(2, true);
    appendLog('', 'dim');
  } else if (status === 'finished') {
    if (payload.exit_code === 0) {
      setStage('master', 'Terminé ✓');
      setProgress(100);
      setLiveBadge('done', '✓ Terminé');
      toast('Production terminée avec succès 🎉', 'success');
    } else {
      setLiveBadge('idle', '● Terminé (erreur)');
      toast('Le pipeline s’est terminé avec une erreur.', 'error');
    }
    loadVideos();
  } else if (status === 'stopped') {
    setLiveBadge('idle', '● Interrompu');
    toast('Production interrompue.', 'info');
    loadVideos();
  }
  updateControls();
  refreshMeta();
}

function startTimer() {
  state.startedAt = Date.now();
  stopTimer();
  state.timer = setInterval(refreshMeta, 500);
}

function stopTimer() {
  if (state.timer) { clearInterval(state.timer); state.timer = null; }
}

function refreshMeta() {
  const el = $('#metaElapsed');
  if (!el || !state.running) return;
  if (state.startedAt) el.textContent = fmtTime((Date.now() - state.startedAt) / 1000);
}

function setLiveBadge(cls, label) {
  const badge = $('#liveBadge');
  if (!badge) return;
  badge.className = 'badge badge-live ' + cls;
  badge.textContent = label;
}

function updateControls() {
  const runBtn = $('#runBtn');
  const stopBtn = $('#stopBtn');
  if (runBtn) { runBtn.disabled = state.running; runBtn.textContent = state.running ? 'Production en cours…' : 'Lancer la production'; }
  if (stopBtn) stopBtn.disabled = !state.running;
  if (!state.running) {
    const el = $('#metaState');
    if (el && state.status) el.textContent = state.status.status === 'finished' ? 'Terminé' : (state.status.status === 'stopped' ? 'Interrompu' : 'En attente');
  } else {
    const el = $('#metaState');
    if (el) el.textContent = 'En cours';
  }
}

/* ------- SSE : flux temps réel ------- */
function connectEvents() {
  if (state.es) state.es.close();
  state.es = new EventSource('/api/events');

  state.es.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data);
      if (data.e === 'log') {
        appendLog(data.m);
        detectStage(data.m || '');
      } else if (data.e === 'state') {
        handleState(data);
      }
    } catch (e) { /* ignore */ }
  };

  state.es.onerror = () => {
    // reconnexion automatique gérée par le navigateur
  };
}

/* ------- actions ------- */
async function launch(auto = false) {
  if (state.running) return;
  const skip = $('#skipAudio') ? $('#skipAudio').checked : false;
  const outDir = $('#outputDir') ? $('#outputDir').value.trim() : '';
  const body = {
    sequence: state.selectedSeq,
    skip_audio: skip,
    output_dir: outDir,
  };
  try {
    const res = await fetch('/api/run', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    if (data.ok) {
      setLiveBadge('started', '● Lancement…');
      toast(auto ? 'Production lancée depuis le tableau de bord.' : 'Production lancée.', 'success');
    } else {
      toast(data.error || 'Impossible de lancer la production.', 'error');
    }
  } catch (e) {
    toast('Erreur réseau lors du lancement.', 'error');
  }
}

async function stopPipeline() {
  try {
    await fetch('/api/stop', { method: 'POST' });
  } catch (e) {
    toast('Erreur réseau lors de l’arrêt.', 'error');
  }
}

/* ------- chargement des données ------- */
async function loadConfig() {
  try { state.config = await apiFetch('/api/config'); } catch (e) { state.config = null; }
  if (state.config) {
    $('#formatBadge').textContent = `9:16 · ${state.config.width}×${state.config.height}`;
    $('#fpsBadge').textContent = `${state.config.fps} FPS`;
    state.totalToRender = state.config.sequences.length;
  }
}

async function loadHealth() {
  try { state.health = await apiFetch('/api/health'); } catch (e) { state.health = null; }
  renderSystem();
  const dot = $('#serverDot');
  const label = $('#serverLabel');
  if (dot && label) {
    dot.className = 'server-dot on';
    label.textContent = 'Serveur connecté';
  }
}

async function loadVideos() {
  try {
    const d = await apiFetch('/api/videos');
    state.videos = d.videos || [];
  } catch (e) { state.videos = []; }
  renderVideos();
  renderStats();
}

async function loadStatus() {
  try {
    const st = await apiFetch('/api/status');
    state.status = st;
    state.running = !!(st.running || st.status === 'running');
    if (state.running) startTimer();
    updateControls();
    refreshMeta();
    if (st.status === 'running') setLiveBadge('running', '● En cours');
    else if (st.status === 'finished') setLiveBadge('done', '✓ Terminé');
    else setLiveBadge('idle', '● En attente');
  } catch (e) { /* ignore */ }
}

/* ------- liaison des événements ------- */
function bindActions() {
  $('#runBtn')?.addEventListener('click', () => launch(false));
  $('#stopBtn')?.addEventListener('click', stopPipeline);
  $('#clearLogBtn')?.addEventListener('click', clearConsole);
  $('#skipAudio')?.addEventListener('change', (e) => {
    const txt = $('#skipAudioText');
    if (txt) txt.textContent = e.target.checked ? 'Oui — réutiliser l’audio existant' : 'Non — régénérer la voix off';
  });
}

/* ------- démarrage ------- */
async function boot() {
  buildStars();
  bindNav();
  bindActions();
  renderPipeline(null);
  renderPalette();

  await Promise.all([loadConfig(), loadHealth(), loadVideos(), loadStatus()]);

  renderSequences();
  renderChips();
  renderStats();
  renderPipeline(state.currentStage);

  connectEvents();
}

document.addEventListener('DOMContentLoaded', boot);