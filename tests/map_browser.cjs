// Run with the app on localhost:8501 and Playwright installed under .sites-runtime/browser-tools.
const { chromium } = require('../.sites-runtime/browser-tools/node_modules/playwright');
const assert = require('node:assert/strict');
const fs = require('node:fs');

(async () => {
  fs.mkdirSync('test-results', { recursive: true });
  const browser = await chromium.launch({
    headless: true,
    ...(process.env.BROWSER_EXECUTABLE ? { executablePath: process.env.BROWSER_EXECUTABLE } : {}),
  });
  try {
    const page = await browser.newPage({ viewport: { width: 1440, height: 1050 } });
    page.setDefaultTimeout(15000);
    const errors = [];
    page.on('pageerror', error => errors.push(error.message));
    await page.goto(process.env.APP_URL || 'http://127.0.0.1:8501');
    await page.getByRole('heading', { name: 'João Pessoa · Presidente 2026' }).waitFor();
    const frame = await (await page.locator('iframe').first().elementHandle()).contentFrame();
    await frame.waitForFunction(() => document.getElementById('result-count')?.textContent.includes('220 locais no mapa'));
    assert.ok(await frame.locator('.site-cluster').count() > 0, 'Nearby points must be clustered');
    assert.ok(await frame.locator('.leaflet-marker-icon').count() < 220, 'Overview must avoid drawing every point separately');
    const startZoom = await frame.evaluate(() => map.getZoom());
    await frame.getByRole('button', { name:'Aproximar mapa' }).click();
    assert.equal(await frame.evaluate(() => map.getZoom()), startZoom + 1);
    await frame.getByRole('button', { name:'Afastar mapa' }).click();
    assert.equal(await frame.evaluate(() => map.getZoom()), startZoom);
    await frame.locator('.site-cluster').first().click();
    await frame.waitForFunction(before => map.getZoom() > before, startZoom);
    await frame.getByRole('button', { name: 'Mostrar todos' }).click();
    assert.equal(await frame.evaluate(() => clusters.getLayers().length), 220);
    assert.ok(await frame.evaluate(() => map.getZoom()) <= startZoom, 'Reset must restore the overview even during a zoom interaction');
    await page.getByRole('heading', { name: 'João Pessoa · Presidente 2026' }).scrollIntoViewIfNeeded();
    await page.screenshot({ path: 'test-results/map-desktop.png', fullPage: true });

    const search = frame.getByLabel('Buscar local, endereço ou seção');
    await search.fill('sesquicentenario');
    await frame.locator('.leaflet-popup-content h2').filter({ hasText: 'SESQUICENTENÁRIO' }).waitFor();
    assert.match(await frame.locator('.leaflet-popup-content').innerText(), /Zona 1/);
    assert.match(await frame.locator('.leaflet-popup-content').innerText(), /ORESTES LISBOA/);
    await frame.locator('.leaflet-popup-close-button').click();
    await frame.locator('.site-marker').click();
    await frame.locator('.leaflet-popup-content').waitFor();
    assert.equal(await frame.locator('.leaflet-popup').count(), 1, 'Only one detail popup should be open');
    await frame.waitForFunction(() => getComputedStyle(document.querySelector('.leaflet-popup')).opacity === '1');
    await page.screenshot({ path: 'test-results/map-desktop-detail.png', fullPage: true });

    await search.fill('vila bancarios');
    await frame.locator('.popup-notice').filter({ hasText: 'BLOQUEADO' }).waitFor();
    await search.fill('euclides');
    await frame.waitForFunction(() => document.querySelector('#site-select option[value="77-1635"]'));
    await frame.locator('#site-select').selectOption('77-1635');
    await frame.locator('.leaflet-popup-content').filter({ hasText: '413 → 77' }).waitFor();
    assert.match(await frame.locator('.leaflet-popup-content').innerText(), /LUZIA SIMOES BARTOLINI/);

    await search.fill('fabiana');
    await frame.locator('#selection-note').waitFor();
    assert.match(await frame.locator('#selection-note').innerText(), /Sem coordenada válida/);
    assert.equal(await frame.locator('.site-marker, .site-cluster').count(), 0, 'Missing coordinates must never be guessed');
    await search.fill('local inexistente xyz');
    await frame.waitForFunction(() => document.getElementById('site-select').disabled);
    assert.equal(await frame.locator('#site-select').isDisabled(), true);
    await search.fill('114');
    await frame.waitForFunction(() => document.querySelectorAll('#site-select option').length > 1);
    const expected = await frame.evaluate(() => registry.locais.filter(s => [s.zona,s.numero,...s.secoes,...s.agregadas.map(a=>a.numero),...s.distribuidas].includes(114)).length);
    assert.equal(await frame.locator('#site-select option').count(), expected + 1);
    await frame.locator('#site-select').selectOption('1-1350');
    await frame.locator('.leaflet-popup-content h2').filter({ hasText: 'SESQUICENTENÁRIO' }).waitFor();

    for (const width of [390, 320]) {
      await page.setViewportSize({ width, height: 900 });
      await frame.getByRole('button', { name: 'Mostrar todos' }).click();
      await search.fill('sesquicentenario');
      await frame.locator('.leaflet-popup-content').waitFor();
      await frame.waitForTimeout(400); // Allow Leaflet's automatic pan to finish.
      const layout = await frame.evaluate(() => {
        const bounds = document.getElementById('map').getBoundingClientRect();
        const popup = document.querySelector('.leaflet-popup').getBoundingClientRect();
        const toolbar = document.querySelector('.toolbar').getBoundingClientRect();
        const zoom = document.querySelector('.zoom-controls').getBoundingClientRect();
        return { overflow: document.documentElement.scrollWidth > innerWidth, left: popup.left >= bounds.left, right: popup.right <= bounds.right, top: popup.top >= bounds.top, toolbarClear: toolbar.bottom <= bounds.top, zoomClear:zoom.bottom<=bounds.top };
      });
      assert.deepEqual(layout, { overflow:false, left:true, right:true, top:true, toolbarClear:true, zoomClear:true }, `Popup layout at ${width}px`);
      assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth), false);
      await page.screenshot({ path: `test-results/map-mobile-${width}.png`, fullPage:true });
    }
    await page.getByRole('tab', { name: 'Resultados', exact:true }).click();
    await page.getByText('219.023', { exact:true }).waitFor();
    await page.getByRole('tab', { name: 'Mapa', exact:true }).click();
    await frame.locator('#map').waitFor();
    assert.deepEqual(errors, [], 'No uncaught browser errors');
    console.log('OK: clusters, clicks, search, missing coordinates, blocked status, aggregated sections, tabs and responsive layout (1440/390/320).');
  } catch (error) {
    const failedPage = browser.contexts()[0]?.pages()[0];
    if (failedPage) {
      await failedPage.screenshot({ path:'test-results/map-failure.png', fullPage:true });
      const failedFrame = failedPage.frames().find(f => f !== failedPage.mainFrame());
      if (failedFrame) console.error(await failedFrame.evaluate(() => ({
        query:document.getElementById('search')?.value,
        count:document.getElementById('result-count')?.textContent,
        selection:document.getElementById('site-select')?.value,
        popups:document.querySelectorAll('.leaflet-popup').length,
      })));
    }
    throw error;
  } finally {
    await browser.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
