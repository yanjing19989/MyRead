// Utilities, API and shared state
const $ = (sel, el=document) => el.querySelector(sel);
const $$ = (sel, el=document) => Array.from(el.querySelectorAll(sel));
const fmt = (n) => new Intl.NumberFormat('zh-CN').format(n);
// fmtSize: format bytes into adaptive units (B, KB, MB, GB, TB)
const fmtSize = (bytes) => {
    const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
    let u = 0;
    let val = Number(bytes);
    while (val >= 1024 && u < units.length - 1) {
        val = val / 1024;
        u++;
    }
    return `${val.toFixed(2)} ${units[u]}`;
};
const api = async (url, opts={}) => {
    const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
    if (!res.ok) throw new Error(await res.text());
    const ct = res.headers.get('content-type') || '';
    if (ct.includes('application/json')) return res.json();
    return res.text();
};

function normPath(p){ return (p || '').replace(/\\/g, '/').replace(/\/\/+$/,''); }
function lowerPath(p){ return normPath(p).toLowerCase(); }
function parentDirPath(p){ const n = normPath(p); const idx = n.lastIndexOf('/'); return idx <= 0 ? '' : n.slice(0, idx); }

const state = {
    albumRootPath: null,
    treeKeyword: '',
    tree: [],
    albumMap: new Map(),
    gridItems: [],
    gridParent: null,
    gridAncestors: [],
};

function logLine(text, cls='') {
    const el = document.createElement('div');
    if (cls) el.className = cls;
    el.textContent = `[${new Date().toLocaleTimeString()}] ${text}`;
    const log = $('#log');
    if (!log) return;
    log.appendChild(el);
    log.scrollTop = log.scrollHeight;
}

function sseConnect() {
    try {
        const es = new EventSource('/api/events/stream');
        es.onmessage = (ev) => {
            try {
                const data = JSON.parse(ev.data);
                if (data && data.path) {
                    if (data.status === 'start') logLine(`开始扫描: ${data.path}`);
                    else if (data.status === 'done') logLine(`完成扫描: ${data.path}`, 'ok');
                    else if (data.status === 'skip') logLine(`跳过: ${data.path} (${data.reason})`, 'warn');
                    else logLine(JSON.stringify(data));
                }
            } catch {}
        };
        es.onerror = () => {};
    } catch {}
}

export { $, $$, fmt, fmtSize, api, normPath, lowerPath, parentDirPath, state, logLine, sseConnect };
