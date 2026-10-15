"""
Dagami Antigravity Language Pack — Dynamic Runtime Translator Builder.
Generates JavaScript code injected into dist/preload.js for any supported language.
"""

import json
from pathlib import Path

REPO_ROOT = Path(__file__).parent
LANG_ROOT = REPO_ROOT / "translations" / "languages"
PRELOAD_MARKER = "// Antigravity UI Runtime Localizer"

RULE_TEMPLATES = {
    "ru": [
        ('^([0-9]+)\\s*lines?\\s*added$', 'return "Добавлено строк: " + m[1];'),
        ('^([0-9]+)\\s*lines?\\s*removed$', 'return "Удалено строк: " + m[1];'),
        ('^([0-9]+)\\s*lines?\\s*changed$', 'return "Изменено строк: " + m[1];'),
        ('^([0-9]+)\\s+agents?\\s+running$', 'return "Запущено агентов: " + m[1];'),
        ('^([0-9]+)\\s+of\\s+([0-9]+)$', 'return m[1] + " из " + m[2];'),
        ('^([0-9]+)\\s+items?$', 'return m[1] + " эл.";'),
    ],
    "zh": [
        ('^([0-9]+)\\s*lines?\\s*added$', 'return "添加了 " + m[1] + " 行";'),
        ('^([0-9]+)\\s*lines?\\s*removed$', 'return "删除了 " + m[1] + " 行";'),
        ('^([0-9]+)\\s*lines?\\s*changed$', 'return "修改了 " + m[1] + " 行";'),
        ('^([0-9]+)\\s+agents?\\s+running$', 'return m[1] + " 个智能体运行中";'),
        ('^([0-9]+)\\s+of\\s+([0-9]+)$', 'return m[1] + " / " + m[2];'),
        ('^([0-9]+)\\s+items?$', 'return m[1] + " 项";'),
    ],
    "es": [
        ('^([0-9]+)\\s*lines?\\s*added$', 'return "Líneas añadidas: " + m[1];'),
        ('^([0-9]+)\\s*lines?\\s*removed$', 'return "Líneas eliminadas: " + m[1];'),
        ('^([0-9]+)\\s*lines?\\s*changed$', 'return "Líneas modificadas: " + m[1];'),
        ('^([0-9]+)\\s+agents?\\s+running$', 'return "Agentes activos: " + m[1];'),
        ('^([0-9]+)\\s+of\\s+([0-9]+)$', 'return m[1] + " de " + m[2];'),
        ('^([0-9]+)\\s+items?$', 'return m[1] + " elementos";'),
    ],
    "ja": [
        ('^([0-9]+)\\s*lines?\\s*added$', 'return m[1] + " 行追加";'),
        ('^([0-9]+)\\s*lines?\\s*removed$', 'return m[1] + " 行削除";'),
        ('^([0-9]+)\\s*lines?\\s*changed$', 'return m[1] + " 行変更";'),
        ('^([0-9]+)\\s+agents?\\s+running$', 'return m[1] + " 件のエージェントが実行中";'),
        ('^([0-9]+)\\s+of\\s+([0-9]+)$', 'return m[1] + " / " + m[2];'),
        ('^([0-9]+)\\s+items?$', 'return m[1] + " 件";'),
    ],
}


def get_language_metadata(lang_code: str) -> dict:
    meta_path = LANG_ROOT / lang_code / "metadata.json"
    if meta_path.exists():
        with open(meta_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "code": lang_code,
        "name": lang_code.upper(),
        "nativeName": lang_code.upper(),
        "version": "1.0.0",
        "translatorTarget": lang_code,
        "flag": "🌐",
        "buttonLabel": f"🌐 {lang_code.upper()}",
        "buttonTitle": f"Translate thoughts to {lang_code}",
        "autoLabelOn": "⚡ Auto: ON",
        "autoLabelOff": "⚡ Auto: OFF",
        "autoTitle": "Auto translate thoughts",
        "originalButton": "🌐 EN",
        "originalTitle": "Show original English text",
        "vscodeLocale": lang_code,
    }


def get_language_dictionary(lang_code: str) -> dict:
    dict_path = LANG_ROOT / lang_code / "dict.json"
    if dict_path.exists():
        with open(dict_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def build_runtime_translator_js(lang_code: str = "ru") -> str:
    meta = get_language_metadata(lang_code)
    dictionary = get_language_dictionary(lang_code)

    target_lang = meta.get("translatorTarget", lang_code)
    btn_label = meta.get("buttonLabel", f"🌐 {lang_code.upper()}")
    btn_title = meta.get("buttonTitle", f"Translate thoughts to {meta.get('nativeName', lang_code)}")
    auto_on = meta.get("autoLabelOn", "⚡ Auto: ON")
    auto_off = meta.get("autoLabelOff", "⚡ Auto: OFF")
    auto_title = meta.get("autoTitle", "Auto translate thoughts")
    orig_btn = meta.get("originalButton", "🌐 EN")
    orig_title = meta.get("originalTitle", "Show original English text")

    rules = RULE_TEMPLATES.get(lang_code, RULE_TEMPLATES.get("en", [
        ('^([0-9]+)\\s*lines?\\s*added$', 'return m[1] + " lines added";'),
        ('^([0-9]+)\\s*lines?\\s*removed$', 'return m[1] + " lines removed";'),
        ('^([0-9]+)\\s+of\\s+([0-9]+)$', 'return m[1] + " of " + m[2];'),
    ]))

    rules_js_lines = []
    for pattern, repl in rules:
        rules_js_lines.append(f"""    {{
      regex: /{pattern}/i,
      replace: function (m) {{ {repl} }}
    }}""")
    rules_js_str = ",\n".join(rules_js_lines)

    dict_json = json.dumps(dictionary, ensure_ascii=False, indent=2)

    js_code = f"""{PRELOAD_MARKER}
/**
 * Dagami Antigravity Language Pack — {meta.get('name', lang_code)} ({meta.get('nativeName', lang_code)})
 * Telegram: https://t.me/+8qU7020rMF84OWNi
 * Donation: https://pay.cloudtips.ru/p/671fda86
 */
(function () {{
  'use strict';

  const TARGET_LANG = {json.dumps(target_lang)};
  const BUTTON_LABEL = {json.dumps(btn_label)};
  const BUTTON_TITLE = {json.dumps(btn_title)};
  const AUTO_LABEL_ON = {json.dumps(auto_on)};
  const AUTO_LABEL_OFF = {json.dumps(auto_off)};
  const AUTO_TITLE = {json.dumps(auto_title)};
  const ORIG_BUTTON = {json.dumps(orig_btn)};
  const ORIG_TITLE = {json.dumps(orig_title)};

  const DICT = {dict_json};

  const RULES = [
{rules_js_str}
  ];

  const IGNORE_TAGS = new Set([
    'SCRIPT', 'STYLE', 'CODE', 'PRE', 'TEXTAREA', 'INPUT'
  ]);

  function isIgnored(node) {{
    if (!node) return true;
    let el = node.nodeType === Node.ELEMENT_NODE ? node : node.parentElement;
    while (el) {{
      if (IGNORE_TAGS.has(el.tagName)) return true;
      if (
        el.classList &&
        (el.classList.contains('token') ||
         el.classList.contains('prism') ||
         el.classList.contains('monaco-editor') ||
         el.classList.contains('cm-editor') ||
         el.classList.contains('xterm'))
      ) {{
        return true;
      }}
      if (el.getAttribute && el.getAttribute('data-notranslate') !== null) {{
        return true;
      }}
      el = el.parentElement;
    }}
    return false;
  }}

  function translateString(text) {{
    if (typeof text !== 'string') return null;
    const trimmed = text.trim();
    if (!trimmed) return null;

    const startSpace = text.match(/^\\s*/)[0];
    const endSpace = text.match(/\\s*$/)[0];

    for (let i = 0; i < RULES.length; i++) {{
      const match = trimmed.match(RULES[i].regex);
      if (match) {{
        return startSpace + RULES[i].replace(match) + endSpace;
      }}
    }}

    if (DICT[trimmed]) {{
      return startSpace + DICT[trimmed] + endSpace;
    }}

    return null;
  }}

  function translateNode(node) {{
    if (!node) return;
    if (node.nodeType === Node.TEXT_NODE) {{
      if (isIgnored(node)) return;
      const translated = translateString(node.nodeValue);
      if (translated && translated !== node.nodeValue) {{
        node.nodeValue = translated;
      }}
    }} else if (node.nodeType === Node.ELEMENT_NODE) {{
      if (isIgnored(node)) return;

      if (node.hasAttribute('placeholder')) {{
        const trans = translateString(node.getAttribute('placeholder'));
        if (trans) node.setAttribute('placeholder', trans);
      }}
      if (node.hasAttribute('title')) {{
        const trans = translateString(node.getAttribute('title'));
        if (trans) node.setAttribute('title', trans);
      }}
      if (node.hasAttribute('aria-label')) {{
        const trans = translateString(node.getAttribute('aria-label'));
        if (trans) node.setAttribute('aria-label', trans);
      }}

      for (let child = node.firstChild; child; child = child.nextSibling) {{
        translateNode(child);
      }}
    }}
  }}

  try {{
    const origNodeValueDesc = Object.getOwnPropertyDescriptor(Node.prototype, 'nodeValue');
    if (origNodeValueDesc && origNodeValueDesc.set) {{
      const origSet = origNodeValueDesc.set;
      Object.defineProperty(Node.prototype, 'nodeValue', {{
        get: origNodeValueDesc.get,
        set: function (val) {{
          if (this.nodeType === Node.TEXT_NODE && typeof val === 'string' && !isIgnored(this)) {{
            const trans = translateString(val);
            if (trans) val = trans;
          }}
          return origSet.call(this, val);
        }},
        configurable: true,
        enumerable: true
      }});
    }}

    const origTextContentDesc = Object.getOwnPropertyDescriptor(Node.prototype, 'textContent');
    if (origTextContentDesc && origTextContentDesc.set) {{
      const origTextSet = origTextContentDesc.set;
      Object.defineProperty(Node.prototype, 'textContent', {{
        get: origTextContentDesc.get,
        set: function (val) {{
          if (typeof val === 'string' && !isIgnored(this)) {{
            const trans = translateString(val);
            if (trans) val = trans;
          }}
          return origTextSet.call(this, val);
        }},
        configurable: true,
        enumerable: true
      }});
    }}
  }} catch (e) {{
    console.warn('[DagamiLang] Hook setup error:', e);
  }}

  function startObserver() {{
    const observer = new MutationObserver((mutations) => {{
      for (let i = 0; i < mutations.length; i++) {{
        const m = mutations[i];
        if (m.type === 'childList') {{
          for (let j = 0; j < m.addedNodes.length; j++) {{
            translateNode(m.addedNodes[j]);
          }}
        }} else if (m.type === 'characterData') {{
          translateNode(m.target);
        }} else if (m.type === 'attributes') {{
          if (['placeholder', 'title', 'aria-label'].includes(m.attributeName)) {{
            const val = m.target.getAttribute(m.attributeName);
            const trans = translateString(val);
            if (trans && trans !== val) {{
              m.target.setAttribute(m.attributeName, trans);
            }}
          }}
        }}
      }}
    }});

    observer.observe(document.documentElement, {{
      childList: true,
      subtree: true,
      characterData: true,
      attributes: true,
      attributeFilter: ['placeholder', 'title', 'aria-label']
    }});

    setInterval(() => {{
      translateNode(document.body);
    }}, 200);

    translateNode(document.body || document.documentElement);
  }}

  if (document.readyState === 'loading') {{
    document.addEventListener('DOMContentLoaded', startObserver);
  }} else {{
    startObserver();
  }}

  // =========================================================================
  // Dynamic On-the-Fly Thinking / Thought Process Translator
  // =========================================================================
  (function () {{
    const STORAGE_KEY_AUTO = 'ag_thoughts_auto_translate';
    const CACHE = new Map();

    function isAutoTranslate() {{
      try {{
        return localStorage.getItem(STORAGE_KEY_AUTO) === 'true';
      }} catch (e) {{
        return false;
      }}
    }}

    function setAutoTranslate(val) {{
      try {{
        localStorage.setItem(STORAGE_KEY_AUTO, val ? 'true' : 'false');
      }} catch (e) {{}}
    }}

    async function translateText(text) {{
      if (!text || !text.trim()) return text;
      const trimmed = text.trim();
      if (CACHE.has(trimmed)) return CACHE.get(trimmed);

      try {{
        const url = 'https://translate.googleapis.com/translate_a/single?client=gtx&sl=en&tl=' + encodeURIComponent(TARGET_LANG) + '&dt=t&q=' + encodeURIComponent(trimmed);
        const res = await fetch(url);
        if (!res.ok) throw new Error('HTTP ' + res.status);
        const data = await res.json();
        if (Array.isArray(data) && Array.isArray(data[0])) {{
          const translated = data[0].map(function (item) {{ return item[0] || ''; }}).join('');
          if (translated) {{
            CACHE.set(trimmed, translated);
            return translated;
          }}
        }}
      }} catch (e) {{
        console.warn('[DagamiLang] Thought translation error:', e);
      }}
      return text;
    }}

    function processThinkingBlock(triggerEl) {{
      if (!triggerEl || triggerEl.dataset.hasTranslateControls) return;
      triggerEl.dataset.hasTranslateControls = 'true';

      var collapsible = triggerEl.closest('[data-testid="thinking-collapsible-trigger"]') || triggerEl;
      var parentContainer = collapsible.parentElement;
      if (!parentContainer) return;

      var toolbar = document.createElement('span');
      toolbar.className = 'ag-thought-toolbar';
      toolbar.style.cssText = 'display:inline-flex; align-items:center; gap:6px; margin-left:10px; font-size:11px; font-family:sans-serif; vertical-align:middle; z-index:10;';

      // 1. Target Lang / EN Button
      var btnTranslate = document.createElement('button');
      btnTranslate.type = 'button';
      btnTranslate.className = 'ag-btn-lang';
      btnTranslate.innerText = BUTTON_LABEL;
      btnTranslate.title = BUTTON_TITLE;
      btnTranslate.style.cssText = 'padding:1px 6px; border-radius:4px; border:1px solid rgba(128,128,128,0.3); background:rgba(128,128,128,0.1); cursor:pointer; font-size:11px; color:inherit; font-weight:bold;';

      // 2. Auto toggle
      var btnAuto = document.createElement('button');
      btnAuto.type = 'button';
      btnAuto.className = 'ag-btn-auto';

      function updateAutoBtn() {{
        var auto = isAutoTranslate();
        btnAuto.innerText = auto ? AUTO_LABEL_ON : AUTO_LABEL_OFF;
        btnAuto.style.cssText = 'padding:1px 6px; border-radius:4px; border:1px solid ' + (auto ? '#22c55e' : 'rgba(128,128,128,0.3)') + '; background:' + (auto ? 'rgba(34,197,94,0.15)' : 'rgba(128,128,128,0.1)') + '; color:' + (auto ? '#16a34a' : 'inherit') + '; cursor:pointer; font-size:11px;';
        btnAuto.title = AUTO_TITLE;
      }}
      updateAutoBtn();

      btnAuto.onclick = function (e) {{
        e.stopPropagation();
        setAutoTranslate(!isAutoTranslate());
        var allBtns = document.querySelectorAll('.ag-btn-auto');
        for (var i = 0; i < allBtns.length; i++) {{
          var auto = isAutoTranslate();
          allBtns[i].innerText = auto ? AUTO_LABEL_ON : AUTO_LABEL_OFF;
          allBtns[i].style.borderColor = auto ? '#22c55e' : 'rgba(128,128,128,0.3)';
          allBtns[i].style.backgroundColor = auto ? 'rgba(34,197,94,0.15)' : 'rgba(128,128,128,0.1)';
          allBtns[i].style.color = auto ? '#16a34a' : 'inherit';
        }}
        if (isAutoTranslate()) {{
          doTranslate();
        }}
      }};

      var isTranslated = false;
      var originalText = null;

      async function doTranslate() {{
        var contentEl = parentContainer.querySelector('.cursor-edit') || parentContainer.querySelector('pre') || parentContainer;
        if (!contentEl) return;

        if (!originalText) {{
          originalText = contentEl.innerText;
        }}

        btnTranslate.innerText = '⏳ ...';
        var tr = await translateText(originalText);
        if (tr && tr !== originalText) {{
          contentEl.innerText = tr;
          isTranslated = true;
          btnTranslate.innerText = ORIG_BUTTON;
          btnTranslate.title = ORIG_TITLE;
          btnTranslate.style.backgroundColor = 'rgba(59, 130, 246, 0.2)';
          btnTranslate.style.borderColor = '#3b82f6';
        }} else {{
          btnTranslate.innerText = BUTTON_LABEL;
        }}
      }}

      function doShowEnglish() {{
        var contentEl = parentContainer.querySelector('.cursor-edit') || parentContainer.querySelector('pre') || parentContainer;
        if (contentEl && originalText) {{
          contentEl.innerText = originalText;
          isTranslated = false;
          btnTranslate.innerText = BUTTON_LABEL;
          btnTranslate.title = BUTTON_TITLE;
          btnTranslate.style.backgroundColor = 'rgba(128,128,128,0.1)';
          btnTranslate.style.borderColor = 'rgba(128,128,128,0.3)';
        }}
      }}

      btnTranslate.onclick = function (e) {{
        e.stopPropagation();
        if (isTranslated) {{
          doShowEnglish();
        }} else {{
          doTranslate();
        }}
      }};

      toolbar.appendChild(btnTranslate);
      toolbar.appendChild(btnAuto);
      triggerEl.appendChild(toolbar);

      if (isAutoTranslate()) {{
        setTimeout(doTranslate, 600);
      }}
    }}

    function scanForThinkingBlocks() {{
      var triggers = document.querySelectorAll('[data-testid="thinking-collapsible-trigger"]');
      for (var i = 0; i < triggers.length; i++) {{
        processThinkingBlock(triggers[i]);
      }}
    }}

    setInterval(scanForThinkingBlocks, 500);
  }})();

  console.log('[DagamiLang] ' + {json.dumps(meta.get('name', lang_code))} + ' pack active with ' + Object.keys(DICT).length + ' strings');
}})();
"""
    return js_code
