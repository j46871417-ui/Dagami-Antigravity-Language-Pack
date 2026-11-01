/* Real browser lifecycle regression: automatic translation, no external network. */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {chromium} = require(process.env.DAGAMI_PLAYWRIGHT_PATH || 'playwright');
const engine = fs.readFileSync(path.join(__dirname, '../translations/structured_thoughts.js'), 'utf8');
const config = {target:'ru',button:'RU',buttonTitle:'Translate',autoOn:'Auto ON',autoOff:'Auto OFF',autoTitle:'Auto',originalButton:'EN',originalTitle:'English'};
const block = (id, text) => `<section id="${id}"><button data-testid="thinking-collapsible-trigger">Thought for 2s</button>${text === null ? '' : `<article data-testid="thinking-collapsible-content"><p>${text}</p></article>`}</section>`;
(async () => {
  const browser = await chromium.launch({headless:true, ...(process.env.DAGAMI_BROWSER_CHANNEL ? {channel:process.env.DAGAMI_BROWSER_CHANNEL}: {})});
  let checks = 0;
  try {
    const page = await browser.newPage();
    await page.route('**/*', route => route.abort());
    await page.setContent(block('one', 'First thought')+block('two', 'Second thought'));
    await page.evaluate(() => {
      Object.defineProperty(window, 'localStorage', {configurable:true, get() {throw new DOMException('Blocked', 'SecurityError');}});
      window.sent = [];
      window.fetch = async url => {
        const text = new URL(url).searchParams.get('q'); window.sent.push(text);
        return {ok:true, json:async()=>[[['RU '+text]]]};
      };
    });
    await page.addScriptTag({content:engine});
    await page.evaluate(cfg => StructuredThoughts.install(cfg), config);
    await page.waitForTimeout(700);
    assert.equal(await page.evaluate(() => sent.length), 0, 'No automatic sending before opt-in'); checks++;
    await page.locator('#one .ag-thought-toolbar [role="button"]').nth(1).click();
    await page.waitForFunction(() => document.querySelectorAll('.ag-thought-overlay').length === 2);
    assert.equal(await page.locator('.ag-thought-toolbar [aria-pressed="true"]').count(), 2, 'Storage failure must not prevent opt-in on all blocks'); checks++;
    assert.match(await page.locator('#two .ag-thought-overlay').textContent(), /RU Second thought/); checks++;
    // Trigger exists before React mounts the actual thought body.
    await page.evaluate(html => document.body.insertAdjacentHTML('beforeend', html), block('delayed', null));
    await page.waitForTimeout(1400);
    await page.evaluate(() => document.querySelector('#delayed').insertAdjacentHTML('beforeend', '<article data-testid="thinking-collapsible-content"><p>Late body</p></article>'));
    await page.waitForFunction(() => document.querySelector('#delayed .ag-thought-overlay')?.textContent.includes('RU Late body'));
    checks++;
    // React replaces content while retaining the same trigger, leaving our old copy behind.
    await page.evaluate(() => {
      const old = document.querySelector('#delayed [data-testid="thinking-collapsible-content"]');
      const next = document.createElement('article'); next.setAttribute('data-testid','thinking-collapsible-content'); next.innerHTML='<p>Replacement body</p>';
      old.parentNode.append(next); old.remove();
    });
    await page.waitForFunction(() => document.querySelector('#delayed .ag-thought-overlay')?.textContent.includes('RU Replacement body'));
    assert.equal(await page.locator('#delayed .ag-thought-overlay').count(), 1, 'Never translate our own orphaned copy'); checks++;
    await page.evaluate(() => document.querySelector('#one [data-testid="thinking-collapsible-content"] p').textContent='Final streaming text');
    await page.waitForFunction(() => document.querySelector('#one .ag-thought-overlay')?.textContent.includes('RU Final streaming text'));
    checks++;
    // EN restores this thought without an immediate loop back to RU.
    await page.locator('#one .ag-thought-toolbar [role="button"]').first().click();
    await page.waitForTimeout(1100);
    assert.equal(await page.locator('#one .ag-thought-overlay').count(), 0); checks++;
    // Disabling Auto cancels both pending work and following updates/new thoughts.
    await page.evaluate(() => document.querySelector('#two [data-testid="thinking-collapsible-content"] p').textContent='Must not send after disable');
    await page.locator('#two .ag-thought-toolbar [role="button"]').nth(1).click();
    const count = await page.evaluate(() => sent.length);
    await page.evaluate(html => document.body.insertAdjacentHTML('beforeend', html), block('off', 'Never send'));
    await page.waitForTimeout(1500);
    assert.equal(await page.evaluate(() => sent.length), count); checks++;
    assert.equal(await page.locator('.ag-thought-overlay').count(), 0); checks++;
    await page.evaluate(() => window.dispatchEvent(new Event('pagehide')));
    assert.equal(await page.locator('.ag-thought-toolbar').count(), 0); checks++;
    await page.close();
    // A real origin verifies persisted opt-in and cross-window preference changes.
    const stored = await browser.newPage();
    await stored.route('**/*', route => route.fulfill({contentType:'text/html',body:block('persisted','Stored preference')}));
    await stored.goto('https://thought-auto.invalid/');
    await stored.evaluate(() => {
      localStorage.setItem('ag_thoughts_auto_translate','true');
      window.sent=[];
      window.fetch=async url => {
        const text=new URL(url).searchParams.get('q');sent.push(text);
        if (window.pauseNext) return new Promise(resolve => {window.finishPending=()=>resolve({ok:true,json:async()=>[[['Late translation']]]});});
        return {ok:true,json:async()=>[[['RU '+text]]]};
      };
    });
    await stored.addScriptTag({content:engine});
    await stored.evaluate(cfg => StructuredThoughts.install(cfg), config);
    await stored.waitForFunction(() => !!document.querySelector('.ag-thought-overlay'));
    checks++;
    await stored.evaluate(() => window.dispatchEvent(new StorageEvent('storage', {key:'ag_thoughts_auto_translate',newValue:'false'})));
    await stored.waitForFunction(() => !document.querySelector('.ag-thought-overlay'));
    assert.equal(await stored.locator('.ag-thought-toolbar [aria-pressed="false"]').count(), 1); checks++;
    // A response that arrives after Auto was disabled must never hide the original.
    await stored.evaluate(() => {
      document.querySelector('[data-testid="thinking-collapsible-content"] p').textContent='In-flight original';
      window.pauseNext=true;
    });
    await stored.locator('.ag-thought-toolbar [role="button"]').nth(1).click();
    await stored.waitForFunction(() => typeof window.finishPending === 'function');
    await stored.locator('.ag-thought-toolbar [role="button"]').nth(1).click();
    await stored.evaluate(() => window.finishPending());
    await stored.waitForTimeout(100);
    assert.equal(await stored.locator('.ag-thought-overlay').count(), 0); checks++;
    assert.equal(await stored.locator('[data-testid="thinking-collapsible-content"]').evaluate(el => el.style.getPropertyValue('display')), ''); checks++;
    await stored.evaluate(() => window.dispatchEvent(new Event('pagehide')));
    await stored.close();
    console.log(`PASS ${checks} automatic translation checks: opt-in, blocked storage, existing/new/delayed/replaced/streaming thoughts, disable and persistence`);
  } finally {await browser.close();}
})().catch(error => {console.error(error);process.exitCode=1;});
