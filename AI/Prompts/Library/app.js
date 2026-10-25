// Prompt Library: renders prompts.json (made by build.py) as a searchable, filterable list.
(() => {
  'use strict';

  // Known categories. A prompt with any other category still shows, in a neutral colour.
  const CATEGORIES = {
    personal: { label: 'Personal', hue: 265 },
    work: { label: 'Work', hue: 215 },
    learning: { label: 'Learning', hue: 150 },
    image: { label: 'Image', hue: 330 },
  };
  // A [fill-in] blank, but not one right after a slash, which is URL syntax like loremflickr.com/800/600/[keyword]
  const PLACEHOLDER = /(?<!\/)\[([^\[\]\n]{1,80})\]/g;
  const THEME_KEY = 'prompt-library-theme';

  const $ = (sel) => document.querySelector(sel);
  const grid = $('#grid'), chips = $('#chips'), search = $('#q'), status = $('#status');
  const dlg = $('#dlg'), toast = $('#toast');

  const state = { prompts: [], category: 'all', query: '', current: null, values: {} };
  const chipEls = new Map();

  function h(tag, attrs, ...children) {
    const node = document.createElement(tag);
    for (const [key, value] of Object.entries(attrs || {})) {
      if (value == null || value === false) continue;
      if (key === 'class') node.className = value;
      else if (key === 'style') node.style.cssText = value;
      else if (key.startsWith('on')) node.addEventListener(key.slice(2), value);
      else node.setAttribute(key, value === true ? '' : value);
    }
    for (const child of children.flat()) if (child != null && child !== false) node.append(child);
    return node;
  }

  function catInfo(key) {
    return CATEGORIES[key] || { label: key ? key[0].toUpperCase() + key.slice(1) : 'Other', hue: 35 };
  }

  const badge = (key) => h('span', { class: 'badge', style: `--h:${catInfo(key).hue}` }, catInfo(key).label);

  // ---- placeholders ----

  function placeholders(text) {
    return [...new Set([...text.matchAll(PLACEHOLDER)].map((m) => m[1].trim()))];
  }

  function fill(text, values) {
    return text.replace(PLACEHOLDER, (whole, name) => values[name.trim()]?.trim() || whole);
  }

  // The prompt as DOM nodes, with blanks highlighted and filled values marked.
  function renderPrompt(text, values) {
    const out = [];
    let last = 0;
    for (const m of text.matchAll(PLACEHOLDER)) {
      out.push(text.slice(last, m.index));
      const value = values[m[1].trim()]?.trim();
      out.push(value ? h('span', { class: 'filled' }, value) : h('mark', { class: 'ph' }, m[0]));
      last = m.index + m[0].length;
    }
    out.push(text.slice(last));
    return out;
  }

  // ---- list ----

  function haystack(p) {
    return [p.title, p.description, p.prompt, catInfo(p.category).label, ...p.tags].join('\n').toLowerCase();
  }

  function buildChips() {
    const keys = [...new Set([...Object.keys(CATEGORIES), ...state.prompts.map((p) => p.category)])]
      .filter((key) => state.prompts.some((p) => p.category === key));
    for (const key of ['all', ...keys]) {
      const count = h('span', { class: 'count' });
      const chip = h('button', {
        type: 'button',
        class: 'chip',
        style: key === 'all' ? null : `--h:${catInfo(key).hue}`,
        onclick: () => { state.category = key; render(); },
      }, key === 'all' ? null : h('span', { class: 'dot' }), key === 'all' ? 'All' : catInfo(key).label, count);
      chipEls.set(key, { chip, count });
      chips.append(chip);
    }
  }

  function card(p) {
    const blanks = placeholders(p.prompt).length;
    const open = () => openPrompt(p);
    return h('article', { class: 'card', style: `--h:${catInfo(p.category).hue}` },
      h('div', { class: 'card-top' },
        badge(p.category),
        blanks ? h('span', { class: 'hint' }, `${blanks} blank${blanks > 1 ? 's' : ''} to fill`) : null),
      h('h3', {}, h('button', { type: 'button', class: 'title-btn', onclick: open }, p.title)),
      p.description ? h('p', { class: 'desc' }, p.description) : null,
      h('pre', { class: 'preview', onclick: open }, renderPrompt(p.prompt, {})),
      h('div', { class: 'card-foot' },
        h('div', { class: 'tags' }, p.tags.map((t) => h('button', { type: 'button', class: 'tag', onclick: () => setQuery(t) }, `#${t}`))),
        h('div', { class: 'actions' },
          h('button', { type: 'button', class: 'btn ghost sm', onclick: open }, 'Open'),
          h('button', { type: 'button', class: 'btn primary sm', onclick: () => copy(p.prompt, 'Prompt copied') }, 'Copy'))));
  }

  function render() {
    const terms = state.query.toLowerCase().split(/\s+/).filter(Boolean);
    const matched = state.prompts.filter((p) => terms.every((t) => p._hay.includes(t)));
    const shown = matched.filter((p) => state.category === 'all' || p.category === state.category);

    for (const [key, { chip, count }] of chipEls) {
      chip.setAttribute('aria-pressed', String(key === state.category));
      count.textContent = key === 'all' ? matched.length : matched.filter((p) => p.category === key).length;
    }

    const where = state.category === 'all' ? '' : ` in ${catInfo(state.category).label}`;
    const what = state.query.trim() ? ` matching “${state.query.trim()}”` : '';
    status.textContent = `${shown.length} prompt${shown.length === 1 ? '' : 's'}${where}${what}`;

    grid.replaceChildren(...(shown.length ? shown.map(card) : [
      h('div', { class: 'empty' }, h('strong', {}, 'No prompts found'), h('p', {}, 'Try another search or category.')),
    ]));
  }

  function setQuery(q) {
    search.value = q;
    state.query = q;
    if (dlg.open) dlg.close();
    render();
    search.focus();
  }

  // ---- detail dialog ----

  function field(name, i) {
    const id = `blank-${i}`;
    const options = name.includes('/') ? name.split('/').map((s) => s.trim()).filter(Boolean) : [];
    return h('label', { class: 'field' },
      h('span', {}, name),
      h('input', {
        id,
        type: 'text',
        autocomplete: 'off',
        placeholder: options.length ? options.join(' · ') : name,
        list: options.length ? `${id}-options` : null,
        oninput: (e) => { state.values[name] = e.target.value; updatePreview(); },
      }),
      options.length ? h('datalist', { id: `${id}-options` }, options.map((o) => h('option', { value: o }))) : null);
  }

  function updatePreview() {
    $('#dlg-prompt').replaceChildren(...renderPrompt(state.current.prompt, state.values));
  }

  function openPrompt(p) {
    state.current = p;
    state.values = {};
    $('#dlg-cat').replaceChildren(badge(p.category));
    $('#dlg-title').textContent = p.title;
    const desc = $('#dlg-desc');
    desc.textContent = p.description;
    desc.hidden = !p.description;

    const names = placeholders(p.prompt);
    const fields = $('#dlg-fields');
    fields.hidden = !names.length;
    fields.replaceChildren(...(names.length ? [
      h('p', { class: 'fields-title' }, 'Fill in the blanks (optional). Empty ones stay as they are.'),
      h('div', { class: 'fields-grid' }, names.map(field)),
    ] : []));
    $('#dlg-reset').hidden = !names.length;
    $('#dlg-tags').replaceChildren(...p.tags.map((t) => h('button', { type: 'button', class: 'tag', onclick: () => setQuery(t) }, `#${t}`)));

    updatePreview();
    if (location.hash !== `#${p.id}`) history.replaceState(null, '', `#${p.id}`);
    if (!dlg.open) dlg.showModal();
    $('.dlg-body').scrollTop = 0;
  }

  function openFromHash() {
    const id = decodeURIComponent(location.hash.slice(1));
    const p = id && state.prompts.find((x) => x.id === id);
    if (p) openPrompt(p);
  }

  dlg.addEventListener('close', () => {
    state.current = null;
    if (location.hash) history.replaceState(null, '', location.pathname + location.search);
  });
  dlg.addEventListener('click', (e) => { if (e.target === dlg) dlg.close(); });
  $('#dlg-close').addEventListener('click', () => dlg.close());
  $('#dlg-copy').addEventListener('click', () => copy(fill(state.current.prompt, state.values), 'Prompt copied'));
  $('#dlg-link').addEventListener('click', () => copy(location.href, 'Link copied'));
  $('#dlg-reset').addEventListener('click', () => {
    state.values = {};
    for (const input of $('#dlg-fields').querySelectorAll('input')) input.value = '';
    updatePreview();
  });

  // ---- clipboard + toast ----

  async function copy(text, message) {
    try {
      await navigator.clipboard.writeText(text);
    } catch {
      // Older browsers / non-https: fall back to a hidden textarea (inside the dialog when it's open, since the page behind is inert)
      const ta = h('textarea', { style: 'position:fixed;opacity:0' });
      ta.value = text;
      (dlg.open ? dlg : document.body).append(ta);
      ta.select();
      document.execCommand('copy');
      ta.remove();
    }
    showToast(message);
  }

  let toastTimer;
  function showToast(message) {
    toast.textContent = message;
    clearTimeout(toastTimer);
    if (toast.showPopover) {
      if (toast.matches(':popover-open')) toast.hidePopover();
      toast.showPopover(); // re-show so it stacks above an open dialog
    } else {
      toast.classList.add('show');
    }
    toastTimer = setTimeout(() => (toast.hidePopover ? toast.hidePopover() : toast.classList.remove('show')), 1800);
  }

  // ---- search, keyboard, theme ----

  search.addEventListener('input', () => { state.query = search.value; render(); });

  document.addEventListener('keydown', (e) => {
    const typing = /^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement?.tagName);
    if (e.key === '/' && !typing && !dlg.open) {
      e.preventDefault();
      search.focus();
    }
  });

  window.addEventListener('hashchange', openFromHash);

  $('#theme').addEventListener('click', () => {
    const root = document.documentElement;
    const dark = root.dataset.theme ? root.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    root.dataset.theme = dark ? 'light' : 'dark';
    try { localStorage.setItem(THEME_KEY, root.dataset.theme); } catch {}
  });

  // ---- load ----

  fetch('prompts.json', { cache: 'no-cache' })
    .then((r) => { if (!r.ok) throw new Error(`HTTP ${r.status}`); return r.json(); })
    .then((data) => {
      state.prompts = data.prompts.map((p) => ({ ...p, tags: p.tags || [], _hay: haystack({ ...p, tags: p.tags || [] }) }));
      buildChips();
      render();
      openFromHash();
    })
    .catch((err) => {
      console.error(err);
      status.textContent = '';
      grid.replaceChildren(h('div', { class: 'empty' },
        h('strong', {}, 'Couldn’t load prompts.json'),
        h('p', {}, 'Run build.py to create it, then open this page through a local server (python -m http.server), not as a file.')));
    });
})();
