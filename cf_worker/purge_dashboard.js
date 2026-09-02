// Purge dashboard — static HTML served at GET /__purge/dashboard.
// Browser se seedha header nahi bhej sakte (form/URL), isliye page ke andar
// fetch() use kiya jata hai jo X-Purge-Key header ke saath POST /__purge karta hai.
// Worker me sirf: import { PURGE_DASHBOARD_HTML } from "./purge_dashboard.js";
export const PURGE_DASHBOARD_HTML = `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Cache Purge</title>
<style>
  :root { --bg:#0b0f17; --panel:#121826; --border:#1e2740; --text:#e5e9f2; --muted:#8b94ad; --accent:#38bdf8; --ok:#22c55e; --err:#ef4444; }
  * { box-sizing:border-box; margin:0; padding:0; }
  body { background:var(--bg); color:var(--text); font-family:system-ui,-apple-system,Segoe UI,Roboto,sans-serif; min-height:100vh; display:flex; align-items:center; justify-content:center; padding:24px; }
  .card { background:var(--panel); border:1px solid var(--border); border-radius:16px; padding:32px; width:100%; max-width:520px; box-shadow:0 20px 50px rgba(0,0,0,.45); }
  h1 { font-size:22px; display:flex; align-items:center; gap:10px; margin-bottom:4px; }
  .sub { color:var(--muted); font-size:13px; margin-bottom:24px; }
  label { display:block; font-size:13px; color:var(--muted); margin:16px 0 6px; }
  input[type=password], input[type=text] { width:100%; background:#0b0f17; border:1px solid var(--border); color:var(--text); border-radius:10px; padding:11px 12px; font-size:14px; outline:none; }
  input:focus { border-color:var(--accent); }
  .chips { display:flex; flex-wrap:wrap; gap:8px; margin-top:16px; }
  .chip { background:#0b0f17; border:1px solid var(--border); color:var(--muted); border-radius:999px; padding:6px 12px; font-size:12px; cursor:pointer; transition:.15s; }
  .chip:hover { color:var(--text); border-color:var(--accent); }
  .chip.active { background:var(--accent); color:#04222e; border-color:var(--accent); font-weight:600; }
  .actions { display:flex; gap:10px; margin-top:22px; }
  button { flex:1; border:none; border-radius:10px; padding:13px; font-size:14px; font-weight:600; cursor:pointer; transition:.15s; }
  #purgeBtn { background:var(--accent); color:#04222e; }
  #purgeBtn:hover { filter:brightness(1.1); }
  #purgeBtn:disabled { opacity:.5; cursor:not-allowed; }
  #allBtn { background:#0b0f17; color:var(--muted); border:1px solid var(--border); }
  #allBtn:hover { color:var(--err); border-color:var(--err); }
  .result { margin-top:18px; border-radius:10px; padding:12px 14px; font-family:ui-monospace,monospace; font-size:12.5px; white-space:pre-wrap; word-break:break-word; display:none; }
  .result.ok { display:block; background:rgba(34,197,94,.08); border:1px solid rgba(34,197,94,.35); color:var(--ok); }
  .result.err { display:block; background:rgba(239,68,68,.08); border:1px solid rgba(239,68,68,.35); color:var(--err); }
  .hidden { display:none; }
  .mode { margin-top:8px; }
</style>
</head>
<body>
<div class="card">
  <h1>🧹 Cache Purge</h1>
  <div class="sub">Workers Cache selective invalidation — <span id="host"></span></div>

  <label for="key">Purge Key</label>
  <input type="password" id="key" placeholder="X-Purge-Key" autocomplete="off">

  <label>Purge Mode</label>
  <div class="mode">
    <div class="chips" id="modeChips">
      <span class="chip active" data-mode="tags">Tags</span>
      <span class="chip" data-mode="paths">Path Prefixes</span>
    </div>
  </div>

  <label for="value">Value (comma separated)</label>
  <input type="text" id="value" placeholder="e.g. titles, names  OR  /v1/content/, /v1/trending">

  <label>Quick Tag Shortcuts</label>
  <div class="chips" id="shortcuts"></div>

  <div class="actions">
    <button id="purgeBtn">Purge Now</button>
    <button id="allBtn">Purge Everything</button>
  </div>

  <div class="result" id="result"></div>
</div>

<script>
(function () {
  const hostEl = document.getElementById('host');
  hostEl.textContent = location.host;
  const resultEl = document.getElementById('result');
  const valueEl = document.getElementById('value');
  const keyEl = document.getElementById('key');
  const shortcutsEl = document.getElementById('shortcuts');
  const purgeBtn = document.getElementById('purgeBtn');
  const allBtn = document.getElementById('allBtn');
  let mode = 'tags';
  const TAGS = [
    'titles','names','search','chart','interests',
    'home','trending','similar','tv-stream','latest-uploads',
    'content','categories','category','apk'
  ];

  TAGS.forEach(function (t) {
    const c = document.createElement('span');
    c.className = 'chip';
    c.textContent = t;
    c.onclick = function () {
      valueEl.value = t;
    };
    shortcutsEl.appendChild(c);
  });

  document.querySelectorAll('#modeChips .chip').forEach(function (chip) {
    chip.onclick = function () {
      document.querySelectorAll('#modeChips .chip').forEach(function (x) { x.classList.remove('active'); });
      chip.classList.add('active');
      mode = chip.dataset.mode;
      valueEl.placeholder = mode === 'tags' ? 'e.g. titles, names' : 'e.g. /v1/content/, /v1/trending';
    };
  });

  function show(text, ok) {
    resultEl.className = 'result ' + (ok ? 'ok' : 'err');
    resultEl.textContent = text;
  }

  async function doPurge(body) {
    const key = keyEl.value.trim();
    if (!key) { show('⚠️ Purge key daalo.', false); return; }
    purgeBtn.disabled = true;
    show('Purging…', true);
    try {
      const res = await fetch('/__purge', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-Purge-Key': key },
        body: JSON.stringify(body)
      });
      const data = await res.json().catch(function () { return { error: 'invalid response' }; });
      if (res.ok) show('✅ ' + JSON.stringify(data, null, 2), true);
      else show('❌ HTTP ' + res.status + '\n' + JSON.stringify(data, null, 2), false);
    } catch (e) {
      show('❌ Network error: ' + e.message, false);
    } finally {
      purgeBtn.disabled = false;
    }
  }

  purgeBtn.onclick = function () {
    const raw = valueEl.value.trim();
    if (!raw) { show('⚠️ Value daalo.', false); return; }
    const parts = raw.split(',').map(function (s) { return s.trim(); }).filter(Boolean);
    const body = mode === 'tags' ? { tags: parts } : { pathPrefixes: parts };
    doPurge(body);
  };

  allBtn.onclick = function () {
    if (!confirm('Poora cache purge karna hai? Yeh sab cached responses delete kar dega.')) return;
    doPurge({ purgeEverything: true });
  };
})();
</script>
</body>
</html>`;
