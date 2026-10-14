/* Start the site server first. Install playwright or provide DIC2_PLAYWRIGHT_PATH.
 * CHROME_PATH may point at installed Chrome; otherwise Playwright uses its browser.
 * Run: node project/verify_site.cjs
 */
const {chromium}=require(process.env.DIC2_PLAYWRIGHT_PATH||'playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(__dirname,'..'),out=path.join(root,'output/screenshots');fs.mkdirSync(out,{recursive:true});
(async()=>{
  const options={headless:true};if(process.env.CHROME_PATH)options.executablePath=process.env.CHROME_PATH;
  const browser=await chromium.launch(options),context=await browser.newContext({viewport:{width:1280,height:700},acceptDownloads:true}),page=await context.newPage(),errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto('http://127.0.0.1:8765/',{waitUntil:'networkidle'});
  assert.equal(await page.locator('#metric-rmse').textContent(),'8,376.45');
  await page.evaluate(()=>scrollTo(0,300));await page.screenshot({path:path.join(out,'startup-desktop.png')});
  await page.selectOption('#problem','boston');assert.equal(await page.locator('#feature-count').getAttribute('max'),'13');assert.equal(await page.locator('#metric-rmse').textContent(),'5.78');
  await page.locator('#feature-count').fill('2');await page.locator('#methods button').filter({hasText:'Exhaustive'}).click();assert.equal(await page.locator('#k-label').textContent(),'2');
  await page.screenshot({path:path.join(out,'boston-desktop.png'),fullPage:true});
  await page.selectOption('#problem','startup');const before=await page.locator('#prediction-output').textContent();await page.locator('#predictor-form input').first().fill('100000');assert.notEqual(await page.locator('#prediction-output').textContent(),before);
  const downloadPromise=page.waitForEvent('download');await page.locator('#download-results').click();const download=await downloadPromise;const dest=path.join(out,'downloaded_predictions.csv');await download.saveAs(dest);assert.equal(fs.readFileSync(dest,'utf8').trim().split(/\r?\n/).length,11);fs.unlinkSync(dest);
  await page.locator('#toggle-import').click();await page.setInputFiles('#csv-file',path.join(root,'site/custom_example.csv'));await page.selectOption('#target','target');await page.locator('#analyze-custom').click();await page.waitForFunction(()=>document.getElementById('problem').value==='custom');assert.ok(Number((await page.locator('#metric-rmse').textContent()).replace(/,/g,''))<1e-5);
  // Real fetch through the URL field, including the exact assignment's URL.
  await page.locator('#example-url').click();await page.locator('#load-url').click();await page.waitForFunction(()=>!document.getElementById('load-url').disabled,{},{timeout:30000});
  let remoteWorked=(await page.locator('#target-controls').getAttribute('hidden'))===null;
  if(!remoteWorked){await page.locator('#csv-url').fill('http://127.0.0.1:8765/startup.csv');await page.locator('#load-url').click();await page.waitForFunction(()=>!document.getElementById('load-url').disabled);}
  assert.equal(await page.locator('#target').inputValue(),'Profit');await page.locator('#analyze-custom').click();await page.waitForFunction(()=>document.getElementById('import-status').textContent.startsWith('已完成'));
  assert.ok((await page.locator('#metric-rmse').textContent()).startsWith('8,174.72'));
  await page.evaluate(()=>scrollTo(0,300));await page.screenshot({path:path.join(out,'custom-desktop.png')});
  let widths=[];for(const width of [320,390,768,1280]){await page.setViewportSize({width,height:800});await page.selectOption('#problem','startup');await page.evaluate(()=>scrollTo(0,0));const dim=await page.evaluate(()=>({w:document.documentElement.clientWidth,scroll:document.documentElement.scrollWidth}));assert.ok(dim.scroll<=dim.w+1,JSON.stringify({width,...dim}));widths.push(width);if(width===390)await page.screenshot({path:path.join(out,'startup-mobile.png'),fullPage:true});}
  assert.deepEqual(errors,[]);const result={passed:true,viewports:widths,two_problem_dropdown:true,method_k_prediction_download:true,custom_csv_recomputed:true,url_fetch_recomputed:true,exact_teacher_url_loaded:remoteWorked,page_errors:errors};fs.writeFileSync(path.join(root,'output/browser_verification.json'),JSON.stringify(result,null,2));console.log(result);await browser.close();
})().catch(error=>{console.error(error);process.exit(1);});
