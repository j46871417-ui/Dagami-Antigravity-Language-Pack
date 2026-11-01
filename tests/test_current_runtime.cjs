/* Offline UI translation acceptance: protect editor, model output and identifiers. */
const assert = require('node:assert/strict');
const {spawnSync} = require('node:child_process');
const {chromium} = require(process.env.DAGAMI_PLAYWRIGHT_PATH || 'playwright');
(async () => {
  const built = spawnSync(process.env.DAGAMI_TEST_PYTHON || 'python', ['-X', 'utf8', '-c',
    'import dagami_translator_builder as b;print(b.build_runtime_translator_js("ru", {"Fixture new label":"Новая метка"}))'],
    {cwd:require('node:path').join(__dirname, '..'), encoding:'utf8', maxBuffer:4*1024*1024});
  assert.equal(built.status, 0, built.stderr);
  const browser = await chromium.launch({headless:true, ...(process.env.DAGAMI_BROWSER_CHANNEL ? {channel:process.env.DAGAMI_BROWSER_CHANNEL}: {})});
  try {
    const page = await browser.newPage();
    let requests = 0;
    await page.route('**/*', route => {requests++; return route.abort();});
    await page.setContent('<!doctype html><body><button id="ui">Fixture new label</button><div contenteditable="true" id="input">Reading</div><code id="code">Reading</code><article class="markdown-body" id="model">Reading</article><div data-message-author-role="user" id="user">Reading</div><div id="unrelated" data-command="antigravity.openSettings">ID untouched</div></body>');
    await page.addScriptTag({content:built.stdout});
    await page.waitForFunction(() => document.querySelector('#ui').textContent === 'Новая метка');
    for (const id of ['input', 'code', 'model', 'user']) assert.equal(await page.locator('#'+id).textContent(), 'Reading', id);
    assert.equal(await page.locator('#unrelated').getAttribute('data-command'), 'antigravity.openSettings');
    await page.evaluate(() => {
      const b = document.createElement('button'); b.id='dynamic'; b.textContent='Fixture new label'; document.body.append(b);
    });
    await page.waitForFunction(() => document.querySelector('#dynamic').textContent === 'Новая метка');
    assert.equal(requests, 0, 'UI labels must not call an online translation service');
    console.log('PASS: current runtime translates static/dynamic UI and preserves input, code, model text and identifiers; no network');
  } finally {await browser.close();}
})().catch(error => {console.error(error);process.exitCode=1;});
