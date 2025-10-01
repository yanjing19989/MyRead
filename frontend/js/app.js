import { $, $$, fmt, api, normPath, lowerPath, parentDirPath, state, logLine, sseConnect } from './lib.js';

let treeSearchTimer = null;

async function loadAlbums(options = {}) {
    const { forceRoot = false } = options;
    const keyword = $('#treeSearch')?.value?.trim() || '';
    try {
        const [treeItems, childrenData] = await Promise.all([
            loadAlbumsTree(null, keyword),
            loadAlbumsChildren(state.albumRootPath, keyword),
        ]);
        state.treeKeyword = keyword;
        state.tree = treeItems;
        state.albumMap = rebuildAlbumMap(treeItems);
        state.gridItems = childrenData.items || [];
        state.gridParent = childrenData.parent || null;
        state.gridAncestors = childrenData.ancestors || [];
        renderAlbums();
        renderAlbumTree();
    } catch (err) {
        console.error('加载相册失败', err);
        if (state.albumRootPath && !forceRoot) {
            state.albumRootPath = null;
            await loadAlbums({ forceRoot: true });
            return;
        }
        logLine(`加载相册失败: ${err}`, 'err');
    }
}

async function loadAlbumsChildren(parentPath = null, keyword = '') {
    const url = new URL('/api/albums', window.location.origin);
    url.searchParams.set('scope', 'children');
    url.searchParams.set('sort_by', 'name');
    url.searchParams.set('order', 'asc');
    if (parentPath) url.searchParams.set('parent_path', parentPath);
    if (keyword) url.searchParams.set('keyword', keyword);
    const data = await api(url.pathname + url.search);
    return data;
}

async function loadAlbumsTree(parentPath = null, keyword = '') {
    const url = new URL('/api/albums', window.location.origin);
    url.searchParams.set('scope', 'tree');
    if (parentPath) url.searchParams.set('parent_path', parentPath);
    if (keyword) url.searchParams.set('keyword', keyword);
    const data = await api(url.pathname + url.search);
    return data.items || [];
}

function rebuildAlbumMap(nodes, map = new Map()) {
    for (const node of nodes || []) {
        const album = node?.album;
        if (album?.path) map.set(lowerPath(album.path), album);
        if (node?.children?.length) rebuildAlbumMap(node.children, map);
    }
    return map;
}

function openAlbum(path) {
    state.albumRootPath = path || null;
    loadAlbums().catch(err => console.error('切换相册失败', err));
}

function renderAlbums() {
    const grid = $('#albumsGrid');
    if (!grid) return;
    grid.innerHTML = '';
    const items = state.gridItems || [];
    if (!items.length) {
        const empty = document.createElement('div');
        empty.className = 'hint';
        const emptyText = state.treeKeyword
            ? '未找到匹配的相册。'
            : (state.albumRootPath ? '该目录下暂无相册。' : '暂无相册，请在上方添加路径并扫描。');
        empty.textContent = emptyText;
        grid.appendChild(empty);
        updateAlbumsNav();
        return;
    }

    updateAlbumsNav();

    for (const album of items) {
        const card = document.createElement('div');
        card.className = 'card';
        const coverUrl = `/api/albums/${album.id}/cover?w=300&h=400&fit=cover`;
        card.innerHTML = `
            <div class="thumb"><img loading="lazy" src="${coverUrl}" alt="cover"></div>
            <div class="meta">
                <div class="name" title="${album.name}">${album.name}</div>
                <div class="sub">类型: ${album.type} · 页数: ${fmt(album.file_count)}</div>
            </div>
        `;
        if (album.type === 'folder') {
            card.classList.add('is-folder');
            card.onclick = () => openAlbum(album.path);
        }
        grid.appendChild(card);
    }
}

function updateAlbumsNav() {
    const nav = $('#albumsNav');
    const crumb = $('#albumsCrumb');
    const backBtn = $('#albumsBackBtn');
    if (!nav || !crumb || !backBtn) return;
    const parent = state.gridParent;
    const ancestors = state.gridAncestors || [];
    if (!parent) {
        nav.style.display = 'none';
        crumb.textContent = '';
        backBtn.onclick = null;
        return;
    }

    nav.style.display = '';
    crumb.innerHTML = '';
    const segments = [...ancestors, parent];
    segments.forEach((album, idx) => {
        const seg = document.createElement('span');
        seg.className = 'seg';
        seg.textContent = album.name || album.path;
        seg.title = album.path;
        seg.onclick = () => openAlbum(album.path);
        crumb.appendChild(seg);
        if (idx < segments.length - 1) {
            const sep = document.createElement('span');
            sep.textContent = '/';
            sep.style.opacity = 0.6;
            sep.style.margin = '0 4px';
            crumb.appendChild(sep);
        }
    });

    backBtn.onclick = () => {
        const prev = ancestors.length ? ancestors[ancestors.length - 1] : null;
        openAlbum(prev ? prev.path : null);
    };
}

function renderAlbumTree() {
    const treeBox = $('#albumTree');
    if (!treeBox) return;
    treeBox.innerHTML = '';
    const nodes = state.tree || [];
    if (!nodes.length) {
        $('#treeEmpty').style.display = '';
        return;
    }
    $('#treeEmpty').style.display = 'none';
    const folderIcon = '📁';
    const zipIcon = '🗜️';
    const activePaths = new Set();
    if (state.gridParent?.path) activePaths.add(lowerPath(state.gridParent.path));
    for (const anc of state.gridAncestors || []) {
        if (anc?.path) activePaths.add(lowerPath(anc.path));
    }
    const expandAll = !!state.treeKeyword;

    const sortNodes = (list) => {
        return [...(list || [])].sort((a, b) => {
            const an = (a.album?.name || a.album?.path || '').toLowerCase();
            const bn = (b.album?.name || b.album?.path || '').toLowerCase();
            return an.localeCompare(bn, 'zh-CN');
        });
    };

    const renderNode = (node, depth = 0) => {
        const album = node.album || {};
        const row = document.createElement('div');
        row.className = 'trow';
        const nodeKey = album.path ? lowerPath(album.path) : '';
        const isActive = state.albumRootPath && nodeKey === lowerPath(state.albumRootPath);
        if (isActive) {
            row.classList.add('active');
        }
        const hasChildren = Array.isArray(node.children) && node.children.length > 0;
        const toggle = document.createElement('span');
        toggle.className = 'toggle';
        const shouldExpand = expandAll || depth === 0 || activePaths.has(nodeKey) || isActive;
        toggle.textContent = hasChildren ? (shouldExpand ? '▾' : '▸') : '';
        const icon = document.createElement('span');
        icon.className = 'ticon';
        icon.textContent = album.type === 'zip' ? zipIcon : folderIcon;
        const name = document.createElement('div');
        name.className = 'tname';
        name.title = album.path || '';
        name.textContent = album.name || (album.path ? album.path.split('/').pop() : '');
        const meta = document.createElement('div');
        meta.className = 'tmeta';
        meta.textContent = `${album.type || ''} · ${fmt(album.file_count || 0)} 页`;
        row.append(toggle, icon, name, meta);

        const childrenBox = document.createElement('div');
        childrenBox.className = 'tchildren';
        childrenBox.style.display = shouldExpand ? '' : 'none';
        if (hasChildren) {
            toggle.style.cursor = 'pointer';
            toggle.onclick = (ev) => {
                ev.stopPropagation();
                const open = childrenBox.style.display === 'none';
                childrenBox.style.display = open ? '' : 'none';
                toggle.textContent = open ? '▾' : '▸';
            };
            sortNodes(node.children).forEach(child => childrenBox.appendChild(renderNode(child, depth + 1)));
        }

        row.ondblclick = () => {
            if (album.type === 'folder') {
                openAlbum(album.path);
            }
        };

        const wrap = document.createElement('div');
        wrap.appendChild(row);
        wrap.appendChild(childrenBox);
        return wrap;
    };

    sortNodes(nodes).forEach(node => treeBox.appendChild(renderNode(node, 0)));
    bindTreeSearch();
}

function bindTreeSearch() {
    const search = $('#treeSearch');
    if (!search || search._bound) return;
    search._bound = true;
    search.addEventListener('input', () => {
        if (treeSearchTimer) clearTimeout(treeSearchTimer);
        treeSearchTimer = setTimeout(() => {
            loadAlbums();
        }, 250);
    });
}

async function scanPaths(paths, recursive) {
    if (!paths || !paths.length) return;
    $('#scanBtn').disabled = true;
    try {
        await api('/api/albums/scan', {
            method: 'POST',
            body: JSON.stringify({ paths, options: { folder: { recursive: !!recursive } } })
        });
    } finally {
        $('#scanBtn').disabled = false;
    }
    await loadAlbums();
}

// UI events
function bindUi() {
    $('#scanBtn').onclick = async () => {
        const v = $('#pathInput').value.trim();
        if (!v) return alert('请输入绝对路径');
        const paths = v.split(';').map(s => s.trim()).filter(Boolean);
        const recursive = $('#recursiveCb').checked;
        logLine(`提交扫描: ${paths.join('; ')} 递归=${recursive}`);
        try {
            await scanPaths(paths, recursive);
            logLine('扫描请求已提交', 'ok');
        } catch (e) {
            logLine(`扫描失败: ${e}`, 'err');
            alert('扫描失败');
        }
    };

    $('#refreshBtn').onclick = async () => {
        $('#refreshBtn').disabled = true;
        try {
            const res = await api('/api/albums/refresh', { method: 'POST' });
            logLine(`刷新完成: 检查=${res.checked} 删除=${res.removed}`, res.removed ? 'warn' : 'ok');
            await loadAlbums();
        } catch (e) {
            logLine(`刷新失败: ${e}`, 'err');
            alert('刷新失败');
        } finally {
            $('#refreshBtn').disabled = false;
        }
    };
}

// init
(async function init(){
    sseConnect();
    bindUi();
    await loadAlbums();
})();

export { loadAlbums, openAlbum };
