/* ═══════════════════════════════════════════════════════════
   Résumé+ — Dashboard statistiques administrateur
   Consomme les endpoints /api/admin/statistics/* (agrégés, anonymisés).
   Aucune donnée hardcodée : tout provient de l'API.
   ═══════════════════════════════════════════════════════════ */
'use strict';

const API_BASE = '/api';

/* ── État ─────────────────────────────────────────────────── */
let accessToken = localStorage.getItem('stats_access');
let refreshToken = localStorage.getItem('stats_refresh');
let currentSection = 'overview';
let currentPeriod = 'last_30_days';
let customStart = '';
let customEnd = '';
let servicesCache = null;

const charts = {};
const chartsBySection = {};

/* ── Petits helpers ───────────────────────────────────────── */
function fmt(n) {
  if (n === null || n === undefined) return '—';
  return Number(n).toLocaleString('fr-FR');
}
function money(n) {
  if (n === null || n === undefined) return '—';
  return `${Number(n).toLocaleString('fr-FR', { maximumFractionDigits: 2 })} FC`;
}
function qs(params) {
  const p = new URLSearchParams({ period: currentPeriod });
  if (currentPeriod === 'custom') {
    if (customStart) p.set('start_date', customStart);
    if (customEnd) p.set('end_date', customEnd);
  }
  if (params) for (const [k, v] of Object.entries(params)) if (v) p.set(k, v);
  return p.toString();
}
const $ = (id) => document.getElementById(id);

/* ── Appel API avec refresh automatique ───────────────────── */
async function api(path, params, retried = false) {
  const url = `${API_BASE}${path}?${qs(params)}`;
  const res = await fetch(url, {
    headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
  });
  if (res.status === 401 && !retried) {
    const refreshed = await tryRefresh();
    if (refreshed) return api(path, params, true);
    logout();
    throw new Error('Session expirée. Veuillez vous reconnecter.');
  }
  if (!res.ok) {
    let detail = `Erreur ${res.status}`;
    try {
      const body = await res.json();
      if (body && body.error) detail = body.error;
    } catch (_) { /* réponse non JSON */ }
    throw new Error(detail);
  }
  return res.json();
}

async function tryRefresh() {
  if (!refreshToken) return false;
  try {
    const res = await fetch(`${API_BASE}/auth/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh: refreshToken }),
    });
    if (!res.ok) return false;
    const body = await res.json();
    accessToken = body.access;
    localStorage.setItem('stats_access', accessToken);
    return true;
  } catch (_) {
    return false;
  }
}

/* ── Connexion / déconnexion ──────────────────────────────── */
async function login(username, password) {
  const res = await fetch(`${API_BASE}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    const msg = body.detail || body.non_field_errors || body.error
      || 'Identifiants invalides.';
    throw new Error(Array.isArray(msg) ? msg.join(' ') : msg);
  }
  const data = await res.json();
  accessToken = data.access;
  refreshToken = data.refresh;
  localStorage.setItem('stats_access', accessToken);
  localStorage.setItem('stats_refresh', refreshToken);
}

function logout() {
  accessToken = null;
  refreshToken = null;
  localStorage.removeItem('stats_access');
  localStorage.removeItem('stats_refresh');
  $('dashboard').hidden = true;
  $('login-screen').style.display = 'flex';
  $('login-username').value = '';
  $('login-password').value = '';
}

/* ── Cartes statistiques ──────────────────────────────────── */
function statCard(label, value, sub, colorClass = '') {
  return `<div class="stat-card ${colorClass}">
    <div class="label">${label}</div>
    <div class="value">${value}</div>
    ${sub ? `<div class="sub">${sub}</div>` : ''}
  </div>`;
}

function renderCards(containerId, cards) {
  $(containerId).innerHTML = cards.map((c) => statCard(c.label, c.value, c.sub, c.cls)).join('');
}

/* ── Graphiques Chart.js ──────────────────────────────────── */
function lineChart(canvasId, points, valueKey, label, color = '#a9dfd8') {
  if (charts[canvasId]) charts[canvasId].destroy();
  const canvas = $(canvasId);
  if (!canvas) return;
  const values = points.map((p) => (p[valueKey] ?? 0));
  const isEmpty = values.every((v) => !v);
  const ctx = canvas.getContext('2d');

  if (isEmpty) {
    // Empty state : message centré sur le canvas.
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = '14px Segoe UI, sans-serif';
    ctx.fillStyle = '#8f8f9c';
    ctx.textAlign = 'center';
    ctx.fillText('Aucune donnée sur cette période', canvas.width / 2, canvas.height / 2);
    return;
  }

  charts[canvasId] = new Chart(ctx, {
    type: 'line',
    data: {
      labels: points.map((p) => p.date),
      datasets: [{
        label,
        data: values,
        borderColor: color,
        backgroundColor: color + '22',
        fill: true,
        tension: 0.3,
        pointRadius: 2,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { maxTicksLimit: 10, font: { size: 10 } } },
        y: { beginAtZero: true },
      },
    },
  });
}

function barChart(canvasId, labels, datasets, stacked = false) {
  if (charts[canvasId]) charts[canvasId].destroy();
  const canvas = $(canvasId);
  if (!canvas) return;
  const isEmpty = datasets.every((d) => d.data.every((v) => !v));
  const ctx = canvas.getContext('2d');
  if (isEmpty) {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.font = '14px Segoe UI, sans-serif';
    ctx.fillStyle = '#8f8f9c';
    ctx.textAlign = 'center';
    ctx.fillText('Aucune donnée sur cette période', canvas.width / 2, canvas.height / 2);
    return;
  }
  charts[canvasId] = new Chart(ctx, {
    type: 'bar',
    data: { labels, datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: datasets.length > 1 } },
      scales: { x: { stacked, ticks: { maxTicksLimit: 10, font: { size: 10 } } }, y: { stacked, beginAtZero: true } },
    },
  });
}

/* ── Bandeau de statut (loading / erreur) ─────────────────── */
function setStatus(kind, message) {
  const banner = $('status-banner');
  if (!message) { banner.hidden = true; return; }
  banner.hidden = false;
  banner.className = `status-banner ${kind}`;
  banner.textContent = message;
}

/* ── Chargement des sections ──────────────────────────────── */
const LOADERS = {
  overview: loadOverview,
  users: loadUsers,
  summaries: loadSummaries,
  qcm: loadQcm,
  transactions: loadTransactions,
  purchases: loadPurchases,
  subscriptions: loadSubscriptions,
  revenue: loadRevenue,
};

async function showSection(name) {
  currentSection = name;
  document.querySelectorAll('.nav-item').forEach((b) =>
    b.classList.toggle('active', b.dataset.section === name));
  document.querySelectorAll('.tab-section').forEach((s) =>
    s.classList.toggle('active', s.id === `section-${name}`));
  renderSectionFilters(name);
  await loadSection(name);
}

async function loadSection(name) {
  setStatus('loading', `Chargement des statistiques… (période : ${$('period-select').selectedOptions[0].text})`);
  try {
    await LOADERS[name]();
    setStatus(null);
  } catch (err) {
    setStatus('error', `Impossible de charger les statistiques : ${err.message}`);
  }
}

/* ── Vue générale ─────────────────────────────────────────── */
async function loadOverview() {
  const { data } = await api('/admin/statistics/overview/');
  const tr = data.transactions;
  renderCards('overview-cards', [
    { label: 'Total utilisateurs', value: fmt(data.users.total), sub: `+${fmt(data.users.new_in_period)} nouveaux`, cls: 'accent' },
    { label: 'Nouveaux utilisateurs', value: fmt(data.users.new_in_period), cls: 'accent' },
    { label: 'Total résumés générés', value: fmt(data.summaries.total), sub: `+${fmt(data.summaries.in_period)} sur la période`, cls: 'green' },
    { label: 'Total QCM générés', value: fmt(data.qcm.total), sub: `+${fmt(data.qcm.in_period)} sur la période`, cls: 'green' },
    { label: 'Total transactions', value: fmt(tr.total), cls: 'orange' },
    { label: 'Transactions réussies', value: fmt(tr.succeeded), sub: `${tr.launched} lancées · ${tr.failed} échouées · ${tr.cancelled} annulées`, cls: 'orange' },
    { label: 'Résumés achetés', value: fmt(data.purchases.total), sub: `+${fmt(data.purchases.in_period)} sur la période`, cls: 'red' },
    { label: 'Abonnements actifs', value: fmt(data.subscriptions.active), sub: `+${fmt(data.subscriptions.new_in_period)} nouveaux`, cls: 'red' },
    { label: 'Revenu total', value: money(data.revenue.total), sub: `${money(data.revenue.in_period)} sur la période`, cls: 'red' },
  ]);
  const rev = await api('/admin/statistics/revenue/');
  const daily = (rev.data.total.daily || []).map((d) => ({ date: d.date, total: d.total }));
  lineChart('chart-overview-revenue', daily, 'total', 'Revenu quotidien', '#a9dfd8');
}

/* ── Utilisateurs ─────────────────────────────────────────── */
async function loadUsers() {
  const { data } = await api('/admin/statistics/users/');
  renderCards('users-cards', [
    { label: 'Total utilisateurs', value: fmt(data.total), cls: 'accent' },
    { label: 'Nouveaux utilisateurs', value: fmt(data.new_in_period), sub: 'sur la période', cls: 'accent' },
  ]);
  lineChart('chart-users-daily', data.daily, 'count', 'Inscriptions', '#a9dfd8');
  lineChart('chart-users-weekly', data.weekly, 'count', 'Inscriptions', '#dcc789');
  lineChart('chart-users-monthly', data.monthly, 'count', 'Inscriptions', '#56849c');
}

/* ── Résumés ──────────────────────────────────────────────── */
async function loadSummaries() {
  const { data } = await api('/admin/statistics/summaries/');
  renderCards('summaries-cards', [
    { label: 'Total résumés générés', value: fmt(data.total), cls: 'green' },
    { label: "Générés aujourd'hui", value: fmt(data.today), cls: 'green' },
    { label: 'Cette semaine', value: fmt(data.this_week), cls: 'green' },
    { label: 'Ce mois', value: fmt(data.this_month), cls: 'green' },
  ]);
  lineChart('chart-summaries-daily', data.daily, 'count', 'Résumés', '#a9dfd8');
  lineChart('chart-summaries-weekly', data.weekly, 'count', 'Résumés', '#dcc789');
  lineChart('chart-summaries-monthly', data.monthly, 'count', 'Résumés', '#56849c');
}

/* ── QCM ──────────────────────────────────────────────────── */
async function loadQcm() {
  const { data } = await api('/admin/statistics/qcm/');
  renderCards('qcm-cards', [
    { label: 'Total QCM générés', value: fmt(data.total), sub: `${fmt(data.classic_total)} classiques · ${fmt(data.personalized_total)} personnalisés`, cls: 'green' },
    { label: "Générés aujourd'hui", value: fmt(data.today), cls: 'green' },
    { label: 'Cette semaine', value: fmt(data.this_week), cls: 'green' },
    { label: 'Ce mois', value: fmt(data.this_month), cls: 'green' },
  ]);
  lineChart('chart-qcm-daily', data.daily, 'count', 'QCM', '#a9dfd8');
  lineChart('chart-qcm-weekly', data.weekly, 'count', 'QCM', '#dcc789');
  lineChart('chart-qcm-monthly', data.monthly, 'count', 'QCM', '#56849c');
}

/* ── Transactions ─────────────────────────────────────────── */
async function loadTransactions() {
  const status = $('filter-transaction-status')?.value;
  const type = $('filter-transaction-type')?.value;
  const params = {};
  if (status) params.status = status;
  if (type) params.type = type;

  const { data } = await api('/admin/statistics/transactions/', params);
  const bs = data.by_status;
  renderCards('transactions-cards', [
    { label: 'Transactions (période)', value: fmt(data.total), cls: 'orange' },
    { label: 'Lancées', value: fmt(bs.pending), cls: 'orange' },
    { label: 'Réussies', value: fmt(bs.completed), cls: 'green' },
    { label: 'Échouées', value: fmt(bs.failed), cls: 'red' },
    { label: 'Annulées', value: fmt(bs.refunded), cls: 'red' },
    { label: 'Taux de réussite', value: `${data.success_rate} %`, cls: 'accent' },
  ]);
  lineChart('chart-transactions-daily', data.daily, 'count', 'Transactions', '#dcc789');
  lineChart('chart-transactions-weekly', data.weekly, 'count', 'Transactions', '#dcc789');
  lineChart('chart-transactions-monthly', data.monthly, 'count', 'Transactions', '#dcc789');
}

/* ── Achats ───────────────────────────────────────────────── */
async function loadPurchases() {
  const { data } = await api('/admin/statistics/purchases/');
  renderCards('purchases-cards', [
    { label: 'Résumés achetés (total)', value: fmt(data.total), cls: 'red' },
    { label: "Aujourd'hui", value: fmt(data.today), cls: 'red' },
    { label: 'Cette semaine', value: fmt(data.this_week), cls: 'red' },
    { label: 'Ce mois', value: fmt(data.this_month), cls: 'red' },
    { label: 'Montant total', value: money(data.amount_total), cls: 'red' },
    { label: "Montant aujourd'hui", value: money(data.amount_today), cls: 'red' },
    { label: 'Montant cette semaine', value: money(data.amount_this_week), cls: 'red' },
    { label: 'Montant ce mois', value: money(data.amount_this_month), cls: 'red' },
    { label: 'Panier moyen (période)', value: money(data.avg_basket), cls: 'red' },
  ]);
  lineChart('chart-purchases-daily', data.daily, 'count', 'Résumés achetés', '#e08a7f');
  const amounts = (data.amount_series.daily || []).map((d) => ({ date: d.date, total: d.total }));
  lineChart('chart-purchases-amounts', amounts, 'total', 'Montant (FC)', '#e08a7f');
}

/* ── Abonnements ──────────────────────────────────────────── */
async function loadSubscriptions() {
  const serviceId = $('filter-subscription-service')?.value;
  const params = {};
  if (serviceId) params.service_id = serviceId;

  const { data } = await api('/admin/statistics/subscriptions/', params);
  const rev = data.revenue;
  renderCards('subscriptions-cards', [
    { label: 'Abonnements actifs', value: fmt(data.active), cls: 'accent' },
    { label: 'Nouveaux abonnements', value: fmt(data.new_in_period), sub: 'sur la période', cls: 'accent' },
    { label: 'Renouvelés', value: 'N/A', sub: 'non traçable avec les modèles actuels', cls: 'orange' },
    { label: 'Expirés', value: fmt(data.expired), sub: `+${fmt(data.expired_in_period)} sur la période`, cls: 'orange' },
    { label: 'Annulés', value: fmt(data.cancelled), cls: 'red' },
    { label: 'Total abonnements', value: fmt(data.total), cls: 'accent' },
    { label: 'Revenus abonnements (total)', value: money(rev.amount_total), cls: 'red' },
    { label: 'Revenus (période)', value: money(rev.amount_in_period), cls: 'red' },
  ]);
  lineChart('chart-subscriptions-daily', data.daily, 'count', 'Abonnements', '#dcc789');
  const amounts = (rev.amount_series.daily || []).map((d) => ({ date: d.total, total: d.total }));
  lineChart('chart-subscriptions-revenue', amounts, 'total', 'Revenus (FC)', '#a9dfd8');
}

/* ── Revenus ──────────────────────────────────────────────── */
async function loadRevenue() {
  const serviceId = $('filter-revenue-service')?.value;
  const params = {};
  if (serviceId) params.service_id = serviceId;

  const { data } = await api('/admin/statistics/revenue/', params);
  const t = data.total;
  const evolution = data.evolution_percent === null || data.evolution_percent === undefined
    ? '—' : `${data.evolution_percent >= 0 ? '+' : ''}${data.evolution_percent} %`;
  const prevMoney = money(data.previous_period.amount_total);
  renderCards('revenue-cards', [
    { label: 'Achats résumés — quantité', value: fmt(data.purchases.quantity), cls: 'red' },
    { label: 'Achats résumés — montant', value: money(data.purchases.amount_total), sub: `${money(data.purchases.amount_in_period)} sur la période`, cls: 'red' },
    { label: 'Abonnements — quantité', value: fmt(data.subscriptions.quantity), cls: 'red' },
    { label: 'Abonnements — montant', value: money(data.subscriptions.amount_total), sub: `${money(data.subscriptions.amount_in_period)} sur la période`, cls: 'red' },
    { label: 'Revenu total', value: money(t.amount_total), sub: `${money(t.amount_in_period)} sur la période`, cls: 'red' },
    { label: 'Évolution vs période précédente', value: evolution, sub: `période précédente : ${prevMoney}`, cls: 'accent' },
  ]);
  const daily = t.daily || [];
  barChart('chart-revenue-daily',
    daily.map((d) => d.date),
    [
      { label: 'Achats résumés', data: daily.map((d) => d.purchases), backgroundColor: '#e08a7f' },
      { label: 'Abonnements', data: daily.map((d) => d.subscriptions), backgroundColor: '#a9dfd8' },
    ],
    true);
}

/* ── Filtres de section ───────────────────────────────────── */
function renderSectionFilters(name) {
  const container = $('section-filters');
  let html = '';
  if (name === 'transactions') {
    html = `
      <label for="filter-transaction-status">Statut</label>
      <select id="filter-transaction-status" onchange="loadSection('transactions')">
        <option value="">Tous</option>
        <option value="pending">Lancées</option>
        <option value="completed">Réussies</option>
        <option value="failed">Échouées</option>
        <option value="refunded">Annulées</option>
      </select>
      <label for="filter-transaction-type">Type</label>
      <select id="filter-transaction-type" onchange="loadSection('transactions')">
        <option value="">Tous</option>
        <option value="summary">Achat de résumé</option>
        <option value="service">Abonnement</option>
      </select>`;
  } else if (name === 'subscriptions' || name === 'revenue') {
    html = `
      <label for="filter-${name}-service">Type d'abonnement</label>
      <select id="filter-${name}-service" onchange="loadSection('${name}')">
        <option value="">Tous</option>
        ${(servicesCache || []).map((s) => `<option value="${s.id}">${escapeHtml(s.nom)}</option>`).join('')}
      </select>`;
  }
  container.innerHTML = html;
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => (
    { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

async function loadServices() {
  try {
    const res = await fetch(`${API_BASE}/services/`, {
      headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
    });
    if (res.ok) {
      const body = await res.json();
      servicesCache = Array.isArray(body) ? body : (body.results || []);
    }
  } catch (_) { /* silencieux : le filtre reste vide */ }
}

/* ── Exports (respectent la période et les filtres courants) ─ */
function exportParams() {
  const params = qs();
  if (currentSection === 'transactions') {
    const s = $('filter-transaction-status')?.value;
    const t = $('filter-transaction-type')?.value;
    if (s) params.set('status', s);
    if (t) params.set('type', t);
  }
  if (currentSection === 'subscriptions' || currentSection === 'revenue') {
    const sid = $(`filter-${currentSection}-service`)?.value;
    if (sid) params.set('service_id', sid);
  }
  return params;
}

async function downloadExport(path) {
  setStatus('loading', 'Préparation de l’export…');
  try {
    const res = await fetch(`${API_BASE}${path}?${exportParams()}`, {
      headers: accessToken ? { Authorization: `Bearer ${accessToken}` } : {},
    });
    if (!res.ok) throw new Error(`Erreur ${res.status}`);
    const blob = await res.blob();
    const filename = (res.headers.get('Content-Disposition') || '').match(/filename="([^"]+)"/)?.[1]
      || 'statistiques.xlsx';
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(a.href);
    setStatus(null);
  } catch (err) {
    setStatus('error', `Export impossible : ${err.message}`);
  }
}

/* ── Événements ───────────────────────────────────────────── */
function initEvents() {
  $('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const errorBox = $('login-error');
    errorBox.hidden = true;
    const submitBtn = $('login-submit');
    submitBtn.disabled = true;
    submitBtn.textContent = 'Connexion…';
    try {
      await login($('login-username').value.trim(), $('login-password').value);
      $('login-screen').style.display = 'none';
      $('dashboard').hidden = false;
      await loadServices();
      await showSection('overview');
    } catch (err) {
      errorBox.hidden = false;
      errorBox.textContent = err.message;
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = 'Se connecter';
    }
  });

  $('logout-btn').addEventListener('click', logout);

  document.querySelectorAll('.nav-item').forEach((btn) => {
    btn.addEventListener('click', () => showSection(btn.dataset.section));
  });

  $('period-select').addEventListener('change', () => {
    currentPeriod = $('period-select').value;
    const isCustom = currentPeriod === 'custom';
    $('custom-start').hidden = !isCustom;
    $('custom-end').hidden = !isCustom;
    loadSection(currentSection);
  });

  $('custom-start').addEventListener('change', () => {
    customStart = $('custom-start').value;
    loadSection(currentSection);
  });
  $('custom-end').addEventListener('change', () => {
    customEnd = $('custom-end').value;
    loadSection(currentSection);
  });

  $('export-excel').addEventListener('click', () =>
    downloadExport('/admin/statistics/export/excel/'));
  $('export-csv').addEventListener('click', () =>
    downloadExport('/admin/statistics/export/csv/?section=' + encodeURIComponent(currentSection)));
}

/* ── Démarrage ────────────────────────────────────────────── */
initEvents();
if (accessToken && refreshToken) {
  $('login-screen').style.display = 'none';
  $('dashboard').hidden = false;
  loadServices().then(() => showSection('overview')).catch(() => logout());
}
