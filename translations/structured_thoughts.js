/* Structured translation: original DOM stays owned by Antigravity/React. */
const StructuredThoughts = (() => {
  'use strict';
  const OMIT = 'pre,code,script,style,textarea,input,select,button,[role="button"],svg,math,[contenteditable],.monaco-editor,.cm-editor,.xterm,.token,.prism,.shiki,.code-block,[data-language],.notranslate,[data-notranslate],.ag-thought-toolbar';
  const abortError = () => new DOMException('Cancelled', 'AbortError');
  const stopEvt = e => { e.preventDefault(); e.stopPropagation(); };

  function textPairs(original, clone) {
    const pairs = [];
    function visit(a, b) {
      if (a.nodeType === 1 && a.matches(OMIT)) return;
      if (a.nodeType === 3) {
        if (a.nodeValue.trim()) pairs.push([a, b]);
        return;
      }
      for (let i = 0; i < a.childNodes.length; i++) visit(a.childNodes[i], b.childNodes[i]);
    }
    visit(original, clone);
    return pairs;
  }

  function createView(content, translate) {
    let overlay = null, controller = null, generation = 0, saved = null;
    function restore() {
      generation++;
      if (controller) controller.abort();
      controller = null;
      if (overlay) overlay.remove();
      overlay = null;
      if (saved && content.style.getPropertyValue('display') === 'none' &&
          content.style.getPropertyPriority('display') === 'important') {
        if (content.getAttribute('style') === saved.hiddenStyle) {
          if (saved.raw === null) content.removeAttribute('style');
          else content.setAttribute('style', saved.raw);
        } else if (saved.value) content.style.setProperty('display', saved.value, saved.priority);
        else content.style.removeProperty('display');
      }
      saved = null;
    }
    async function show() {
      restore();
      if (!content.isConnected || !content.parentNode || content.matches(OMIT)) return false;
      const epoch = generation, current = new AbortController();
      controller = current;
      const clone = content.cloneNode(true), pairs = textPairs(content, clone);
      clone.classList.add('ag-thought-overlay');
      // Avoid duplicate IDs and test selectors; maintain local ARIA references.
      const ids = new Map(), elements = [clone, ...clone.querySelectorAll('*')];
      const nonce = 'ag-copy-' + Math.random().toString(36).slice(2) + '-';
      for (const el of elements) {
        if (el.id) { const id = nonce + ids.size; ids.set(el.id, id); el.id = id; }
        el.removeAttribute('data-testid');
      }
      for (const el of elements) for (const attr of ['aria-labelledby', 'aria-describedby', 'for']) {
        if (el.hasAttribute(attr)) el.setAttribute(attr, el.getAttribute(attr).split(/\s+/).map(x => ids.get(x) || x).join(' '));
      }
      // Existing copy buttons and React links retain their original handlers.
      const originals = [content, ...content.querySelectorAll('*')];
      const originalByClone = new WeakMap();
      elements.forEach((el, i) => {
        originalByClone.set(el, originals[i]);
        // cloneNode copies inline HTML event attributes, but no React handlers.
        for (const attr of Array.from(el.attributes)) if (/^on/i.test(attr.name)) el.removeAttribute(attr.name);
      });
      for (const type of ['click', 'auxclick', 'dblclick']) clone.addEventListener(type, e => {
        const target = e.target.nodeType === 1 ? e.target : e.target.parentElement;
        const original = originalByClone.get(target);
        stopEvt(e);
        if (original && original.isConnected) original.dispatchEvent(new MouseEvent(type, {
          bubbles: true, cancelable: true, view: window, detail: e.detail,
          button: e.button, buttons: e.buttons, ctrlKey: e.ctrlKey,
          metaKey: e.metaKey, shiftKey: e.shiftKey, altKey: e.altKey
        }));
      });
      clone.addEventListener('keydown', e => {
        const original = originalByClone.get(e.target);
        stopEvt(e);
        if (!original || !original.isConnected) return;
        if (original.matches('[role="button"]') && (e.key === 'Enter' || e.key === ' ')) original.click();
        else original.dispatchEvent(new KeyboardEvent('keydown', {
          bubbles: true, cancelable: true, key: e.key, code: e.code,
          ctrlKey: e.ctrlKey, metaKey: e.metaKey, shiftKey: e.shiftKey, altKey: e.altKey
        }));
      });
      let changed = false;
      const grouped = new Set(), groups = new Map();
      for (const pair of pairs) {
        const block = pair[0].parentElement.closest('p,li,td,th,h1,h2,h3,h4,h5,h6');
        if (block && content.contains(block) && block.querySelector('code:not(pre code)')) {
          if (!groups.has(block)) groups.set(block, []);
          groups.get(block).push(pair); grouped.add(pair);
        }
      }
      try {
        // A shared translator limits all views to two network requests at once.
        await Promise.all([
          ...Array.from(groups.values()).map(async group => {
            const mark = i => '\uE002' + i + '\uE003';
            const input = group.map(([from], i) => mark(i) + from.nodeValue).join('') + mark(group.length);
            const result = await translate(input, current.signal);
            if (current.signal.aborted || generation !== epoch) throw abortError();
            let cursor = 0;
            const values = [];
            for (let i = 0; i <= group.length; i++) {
              const token = mark(i), index = result.indexOf(token, cursor);
              if (index < 0 || result.indexOf(token, index + token.length) >= 0) throw new Error('Translation lost a DOM marker');
              if (i) values.push(result.slice(cursor, index));
              else if (index) values.push(result.slice(0, index));
              cursor = index + token.length;
            }
            const prefix = values.length > group.length ? values.shift() : '';
            values[0] = prefix + values[0];
            if (cursor !== result.length) values[values.length - 1] += result.slice(cursor);
            group.forEach(([from, to], i) => { to.nodeValue = values[i]; if (values[i] !== from.nodeValue) changed = true; });
          }),
          ...pairs.filter(pair => !grouped.has(pair)).map(async ([from, to]) => {
          const result = await translate(from.nodeValue, current.signal);
          if (current.signal.aborted || generation !== epoch) throw abortError();
          if (result !== from.nodeValue) changed = true;
          to.nodeValue = result;
        })]);
        if (!changed || generation !== epoch || current.signal.aborted || !content.isConnected) return false;
        saved = { value: content.style.getPropertyValue('display'), priority: content.style.getPropertyPriority('display'), raw: content.getAttribute('style') };
        content.parentNode.insertBefore(clone, content.nextSibling);
        overlay = clone;
        content.style.setProperty('display', 'none', 'important');
        saved.hiddenStyle = content.getAttribute('style');
        return true;
      } catch (error) {
        current.abort();
        throw error;
      }
    }
    return { show, restore, dispose: restore, get overlay() { return overlay; } };
  }

  function createTranslator(target, fetcher = fetch) {
    const cache = new Map(), waiting = [];
    let active = 0;
    function drain() {
      while (active < 2 && waiting.length) {
        const job = waiting.shift();
        job.signal.removeEventListener('abort', job.cancel);
        if (job.signal.aborted) { job.reject(abortError()); continue; }
        active++;
        Promise.resolve().then(job.run).then(job.resolve, job.reject).finally(() => { active--; drain(); });
      }
    }
    function enqueue(run, signal) {
      return new Promise((resolve, reject) => {
        if (signal.aborted) { reject(abortError()); return; }
        const job = { run, signal, resolve, reject };
        job.cancel = () => {
          const i = waiting.indexOf(job);
          if (i >= 0) { waiting.splice(i, 1); reject(abortError()); }
        };
        signal.addEventListener('abort', job.cancel, { once: true });
        waiting.push(job); drain();
      });
    }
    async function part(text, signal) {
      const match = text.match(/^(\s*)([\s\S]*?)(\s*)$/), core = match[2];
      if (!core) return text;
      if (signal.aborted) throw abortError();
      if (cache.has(core)) return match[1] + cache.get(core) + match[3];
      const translated = await enqueue(async () => {
        const timeout = new AbortController();
        const cancel = () => timeout.abort();
        signal.addEventListener('abort', cancel, { once: true });
        const timer = setTimeout(cancel, 15000);
        try {
          if (signal.aborted) throw abortError();
          const url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=' +
            encodeURIComponent(target) + '&dt=t&q=' + encodeURIComponent(core);
          const response = await fetcher(url, { signal: timeout.signal, credentials: 'omit' });
          if (!response.ok) throw new Error('Translation HTTP failure');
          const data = await response.json();
          if (!Array.isArray(data) || !Array.isArray(data[0])) throw new Error('Bad translation response');
          const result = data[0].map(x => typeof x[0] === 'string' ? x[0] : '').join('');
          if (!result || signal.aborted) throw abortError();
          if (cache.size >= 400) cache.delete(cache.keys().next().value);
          cache.set(core, result);
          return result;
        } finally { clearTimeout(timer); signal.removeEventListener('abort', cancel); }
      }, signal);
      return match[1] + translated + match[3];
    }
    async function prose(text, signal) {
      // Prefer word boundaries; very long unbroken tokens use code points.
      const words = text.match(/\s+|[^\s]+/gu) || [];
      let chunk = '', output = '';
      for (const word of words) {
        if (chunk && chunk.length + word.length > 800) {
          output += await part(chunk, signal); chunk = '';
        }
        for (const char of word) {
          if (chunk.length + char.length > 800) { output += await part(chunk, signal); chunk = ''; }
          chunk += char;
        }
      }
      return output + (chunk ? await part(chunk, signal) : '');
    }
    return async function translate(text, signal) {
      // Opaque markers keep a sentence intact without sending code or URLs.
      const protectedText = /```[\s\S]*?(?:```|$)|~~~[\s\S]*?(?:~~~|$)|(`+)[\s\S]*?(?:\1|$)|https?:\/\/[^\s<>()]+/g;
      const saved = [], nonce = Math.random().toString(10).slice(2);
      const marker = i => '\uE000' + nonce + ':' + i + '\uE001';
      const masked = text.replace(protectedText, value => { const id = saved.push(value) - 1; return marker(id); });
      let result = await prose(masked, signal);
      for (let i = 0; i < saved.length; i++) {
        const token = marker(i);
        if (result.split(token).length !== 2) throw new Error('Translation lost a code marker');
        result = result.replace(token, saved[i]);
      }
      return result;
    };
  }

  function install(config) {
    const translate = createTranslator(config.target), states = new Set(), byTrigger = new WeakMap();
    const key = 'ag_thoughts_auto_translate';
    let closed = false;
    function auto() { try { return localStorage.getItem(key) === 'true'; } catch { return false; } }
    function scan() {
      if (closed || window.__ag_renderThought) return;
      for (const state of states) if (!state.trigger.isConnected) {
        state.dispose(); states.delete(state);
      }
      for (const trigger of document.querySelectorAll('[data-testid="thinking-collapsible-trigger"]')) {
        if (byTrigger.has(trigger)) continue;
        const parent = trigger.closest('[data-testid="thinking-collapsible-trigger"]').parentElement;
        if (!parent) continue;
        const toolbar = document.createElement('span');
        toolbar.className = 'ag-thought-toolbar';
        toolbar.style.cssText = 'display:inline-flex !important; flex-flow:row nowrap !important; gap:4px !important; white-space:nowrap !important; margin-left:8px !important; vertical-align:middle !important;';
        // Triggers may themselves be buttons; avoid invalid nested buttons.
        const button = document.createElement('span'), toggle = document.createElement('span');
        for (const el of [button, toggle]) {
          el.setAttribute('role', 'button'); el.tabIndex = 0;
          el.addEventListener('keydown', e => {
            if (e.key === 'Enter' || e.key === ' ') { stopEvt(e); el.click(); }
          });
          el.style.cssText = 'display:inline-flex !important; white-space:nowrap !important; padding:2px 6px !important; border:1px solid #8886 !important; border-radius:5px !important; cursor:pointer !important; font-size:11px !important;';
          for (const event of ['mousedown', 'pointerdown']) el.addEventListener(event, stopEvt);
          toolbar.appendChild(el);
        }
        let view = null, observer = null, busy = false, epoch = 0, timer = null;
        function label(translated = false) {
          button.textContent = busy ? '⏹' : (translated ? config.originalButton : config.button);
          button.title = busy ? (config.cancelTitle || 'Cancel') : (translated ? config.originalTitle : config.buttonTitle);
          toggle.textContent = auto() ? config.autoOn : config.autoOff;
          toggle.title = config.autoTitle;
          toggle.setAttribute('aria-pressed', String(auto()));
        }
        function reset() {
          epoch++; busy = false;
          if (timer) clearTimeout(timer);
          if (view) view.restore();
          label();
        }
        function content() {
          for (const selector of ['[data-testid="thinking-collapsible-content"]', '.markdown-body', '.rendered-markdown', '.cursor-edit']) {
            const el = parent.querySelector(selector);
            if (el && !el.classList.contains('ag-thought-overlay') && !el.contains(trigger) && !trigger.contains(el)) return el;
          }
          const next = trigger.nextElementSibling;
          return next && !next.matches(OMIT) ? next : null;
        }
        async function show() {
          const el = content();
          if (!el) return;
          if (view) view.dispose();
          if (observer) observer.disconnect();
          view = createView(el, translate);
          const current = ++epoch;
          observer = new MutationObserver(() => {
            reset();
            if (auto()) timer = setTimeout(show, 800);
          });
          observer.observe(el, { childList: true, characterData: true, subtree: true, attributes: true, attributeFilter: ['href', 'src', 'hidden', 'data-state', 'aria-hidden', 'class'] });
          busy = true; label();
          try {
            const shown = await view.show();
            if (current === epoch) { busy = false; label(shown); }
          } catch (error) {
            if (current === epoch) {
              busy = false; label();
              if (error.name !== 'AbortError') button.title = config.errorTitle || 'Could not translate. Try again.';
            }
          }
        }
        button.addEventListener('click', e => {
          stopEvt(e);
          if (busy || (view && view.overlay)) reset(); else show();
        });
        toggle.addEventListener('click', e => {
          stopEvt(e);
          try { localStorage.setItem(key, auto() ? 'false' : 'true'); } catch {}
          for (const state of states) state.label();
          if (auto()) show();
          else for (const state of states) state.reset();
        });
        trigger.appendChild(toolbar); label();
        const state = { trigger, label, reset, dispose() { reset(); if (observer) observer.disconnect(); toolbar.remove(); byTrigger.delete(trigger); } };
        byTrigger.set(trigger, state); states.add(state);
        if (auto()) timer = setTimeout(show, 600);
      }
    }
    const interval = setInterval(scan, 500); scan();
    window.addEventListener('pagehide', () => { closed = true; clearInterval(interval); for (const state of states) state.dispose(); }, { once: true });
  }
  return { textPairs, createView, createTranslator, install };
})();
