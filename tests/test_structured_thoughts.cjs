/* Real headless browser tests. Dev-only dependency: Playwright. No internet. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { chromium } = require(process.env.DAGAMI_PLAYWRIGHT_PATH || 'playwright');
(async () => {
  const browser = await chromium.launch({headless:true, ...(process.env.DAGAMI_BROWSER_CHANNEL ? {channel:process.env.DAGAMI_BROWSER_CHANNEL}: {})});
  const page = await browser.newPage();
  await page.route('**/*', route => route.abort());
  await page.setContent('<!doctype html><body></body>');
  await page.addScriptTag({content:fs.readFileSync(path.join(__dirname,'../translations/structured_thoughts.js'),'utf8')});
  const results = await page.evaluate(async () => {
    const results = [];
    const check = (ok, name) => { if (!ok) throw new Error(name); results.push(name); };
    const fixture = () => {
      document.body.innerHTML = '<section><button data-testid="thinking-collapsible-trigger">Thought for 2s</button><article class="markdown-body" data-testid="thinking-collapsible-content" style="display:flex !important;color:blue"><h2 id="title">Plan</h2><ul><li>First <strong>step</strong></li><li>Second step</li></ul><a href="https://example.invalid/secret?token=x">Docs</a><pre style="white-space:pre"><code>const secret = 42;\n\n    return secret;</code><button>Copy</button></pre><table><tbody><tr><td>Cell</td></tr></tbody></table><p>  End  </p></article></section>';
      return document.querySelector('article');
    };
    let source = fixture(), sent = [], clicks = 0;
    source.querySelector('button').addEventListener('click',()=>clicks++);
    source.querySelector('a').addEventListener('click',e=>{e.preventDefault();clicks++});
    const originalHTML=source.innerHTML, originalStyle=source.getAttribute('style');
    const view = StructuredThoughts.createView(source, async text => {sent.push(text);return text.replace(/[A-Za-z]+/g,x=>'RU_'+x);});
    check(await view.show(), 'show structured translation');
    const overlay=view.overlay;
    check(['h2','ul','li','strong','a','pre','code','table','td'].every(t=>overlay.querySelector(t)), 'rich DOM tags retained');
    check(overlay.querySelector('code').textContent===source.querySelector('code').textContent, 'code bytes/indent/newlines retained');
    check(!sent.some(x=>x.includes('secret')||x.includes('Copy')||x.includes('https://')), 'code, controls and URLs excluded from service');
    check(overlay.querySelector('a').getAttribute('href')===source.querySelector('a').getAttribute('href'), 'link destination untouched');
    check(overlay.querySelector('h2').id!=='title' && source.querySelector('h2').id==='title','no duplicate IDs');
    overlay.querySelector('button').click();overlay.querySelector('a').click();
    check(clicks===2,'original copy and link handlers still work');
    check(source.innerHTML===originalHTML,'original subtree untouched');
    view.restore();
    check(source.getAttribute('style')===originalStyle && source.innerHTML===originalHTML&&!document.querySelector('.ag-thought-overlay'), 'EN restores exact style and DOM');
    check(await view.show(), 'repeat show');
    view.restore();check(source.innerHTML===originalHTML,'repeated toggles have no growth');
    const failure = StructuredThoughts.createView(source,async()=>{throw new Error('offline')});
    try {await failure.show();throw new Error('expected error')}catch(e){check(e.message==='offline','network error surfaced')}
    check(!failure.overlay && source.getAttribute('style')===originalStyle,'failed translation leaves English visible');
    let pending=[];
    const delayed=StructuredThoughts.createView(source,text=>new Promise(resolve=>pending.push(()=>resolve('RU '+text))));
    const task=delayed.show();delayed.restore();pending.forEach(fn=>fn());
    try{await task;throw new Error('expected cancellation')}catch(e){check(e.name==='AbortError','late response rejected after cancellation')}
    check(!delayed.overlay && source.getAttribute('style')===originalStyle,'late response cannot hide source');
    let active=0, maximum=0, calls=0, url='';
    const translate=StructuredThoughts.createTranslator('ru',async request=>{
      calls++; url=request; active++;maximum=Math.max(maximum,active);
      await new Promise(r=>setTimeout(r,4));active--;
      return {ok:true,json:async()=>[[['TR']]]};
    });
    const ac=new AbortController();
    await Promise.all(Array.from({length:8},(_,i)=>translate('node '+i,ac.signal)));
    check(maximum===2,'shared queue bound to two requests');
    const before=calls;await translate('node 1',ac.signal);
    check(calls===before,'cache avoids repeated request');
    const spaced=await translate(' \nunique \t',ac.signal);
    check(spaced===' \nTR \t','leading/trailing whitespace retained');
    let chunks=[];
    const split=StructuredThoughts.createTranslator('ru',async request=>{
      const q=new URL(request).searchParams.get('q');chunks.push(q);
      return {ok:true,json:async()=>[[[q]]]};
    });
    const unicode='a'.repeat(799)+'🚀'+'b'.repeat(900);
    check(await split(unicode,ac.signal)===unicode && chunks.every(x=>!/(?:[\uD800-\uDBFF]$|^[\uDC00-\uDFFF])/.test(x)),'long nodes split without breaking emoji');
    chunks=[];
    const rawCode='Before `password = 42` and ``more_code()`` https://example.invalid/private?q=secret\n```js\nconst token = 1;\n```';
    check(await split(rawCode,ac.signal)===rawCode && chunks.every(x=>!/(password|more_code|token|secret)/.test(x)),'plain Markdown code and literal URLs never reach service');
    chunks=[];const openFence='Before\n```py\nprivate_key = 42';
    check(await split(openFence,ac.signal)===openFence&&!chunks.some(x=>x.includes('private_key')),'open streaming code fence protected');
    ac.abort();const callCount=calls;
    try{await translate('cancelled',ac.signal);throw new Error('expected abort')}catch(e){check(e.name==='AbortError'&&calls===callCount,'aborted jobs never fetch')}
    // Exercise actual toolbar/observer code in a real DOM, with mock network.
    source=fixture(); // about:blank has no storage; opt-in defaults off.
    window.fetch=async request=>({ok:true,json:async()=>[[['RU '+new URL(request).searchParams.get('q')]]]});
    StructuredThoughts.install({target:'ru',button:'RU',buttonTitle:'Translate',autoOn:'Auto ON',autoOff:'Auto OFF',autoTitle:'Auto',originalButton:'EN',originalTitle:'English'});
    check(!document.querySelector('button button'),'no nested buttons in a collapsible trigger');
    document.querySelector('.ag-thought-toolbar [role=button]').click();
    await new Promise(r=>setTimeout(r,30));
    check(!!document.querySelector('.ag-thought-overlay'),'toolbar uses structured view');
    source.querySelector('h2').textContent='Streaming update';
    await new Promise(r=>setTimeout(r,30));
    check(!document.querySelector('.ag-thought-overlay')&&source.style.getPropertyValue('display')==='flex','streaming invalidates stale translation and restores source');
    window.dispatchEvent(new Event('pagehide'));
    check(!document.querySelector('.ag-thought-toolbar'),'page cleanup');
    return results;
  });
  assert(results.length>=23);
  console.log('PASS '+results.length+' real DOM format, code privacy, links, cancellation, streams and queue checks');
  await browser.close();
})().catch(error=>{console.error(error);process.exit(1)});
