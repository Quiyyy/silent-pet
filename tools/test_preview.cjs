// Optional browser regression. Requires the playwright package and an installed browser.
// PREVIEW_URL selects a running local preview; PLAYWRIGHT_CHANNEL may select chrome.
const {chromium}=require('playwright');
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const root=path.resolve(process.argv[2]||'output/browser-tests');
fs.mkdirSync(path.join(root,'qa'),{recursive:true});
const url=process.env.PREVIEW_URL||'http://127.0.0.1:8768/preview/';
(async()=>{
 const browser=await chromium.launch({headless:true,chromiumSandbox:true,...process.env.PLAYWRIGHT_CHANNEL?{channel:process.env.PLAYWRIGHT_CHANNEL}:{}});
 const context=await browser.newContext({viewport:{width:1360,height:1050},deviceScaleFactor:1,reducedMotion:'no-preference'});
 const page=await context.newPage();const errors=[];page.on('pageerror',e=>errors.push(e.message));
 const report={browser:browser.version(),mode:'isolated headless Chrome on local owned preview; not native Codex UI',checks:{}};
 const canvas=page.locator('#pet');
 const state=()=>canvas.evaluate(e=>({...e.dataset}));
 const sample=ms=>page.evaluate(ms=>new Promise(resolve=>{
  const entries=[],start=performance.now();let last='';
  function tick(now){const e=document.querySelector('#pet'),value=JSON.stringify({...e.dataset});
   if(value!==last){entries.push({at:now-start,...e.dataset});last=value;}
   if(now-start>=ms)resolve(entries);else requestAnimationFrame(tick);
  }requestAnimationFrame(tick);
 }),ms);
 const point=async()=>{const b=await canvas.boundingBox();return {x:b.x+b.width*.52,y:b.y+b.height*.66};};
 const reset=async()=>{await page.locator('#interactive').click();await page.mouse.move(10,10);};
 try{
  await page.goto(url);await page.waitForFunction(()=>document.querySelector('#pet').dataset.state);
  assert.equal(await page.locator('#states button').count(),9);assert.equal(await page.locator('#directions button').count(),16);
  const states=['idle','running-right','running-left','waving','jumping','failed','waiting','running','review'];
  for(let i=0;i<states.length;i++){await page.locator('#states button').nth(i).click();assert.equal((await state()).state,states[i]);}
  report.checks.all_nine_state_buttons=true;
  await page.locator('#states button').nth(3).click();
  assert((await page.locator('#hint').innerText()).includes('首次唤醒'));
  const wave=await sample(950);assert.equal(new Set(wave.map(x=>x.frame)).size,4);
  await page.screenshot({path:path.join(root,'qa/browser-wave.png')});
  report.checks.wave_four_frames_and_trigger_hint=true;
  for(let i=0;i<16;i++){await page.locator('#directions button').nth(i).click();assert.equal((await state()).frame,String(i));}
  report.checks.all_sixteen_directions=true;
  await page.locator('#states button').nth(1).click();
  const right=await sample(1250);assert.equal(new Set(right.map(x=>x.frame)).size,8);
  await page.screenshot({path:path.join(root,'qa/browser-right.png')});
  await page.locator('#states button').nth(2).click();
  const left=await sample(1250);assert.equal(new Set(left.map(x=>x.frame)).size,8);
  report.checks.right_and_left_visit_all_eight_frames={right,left};
  await reset();let p=await point();await page.mouse.move(p.x,p.y);
  const hover=await sample(5100);const active=hover.filter(x=>x.kind==='affection');
  assert(active.length>0);assert(active[0].at>=350 && active[0].at<900);
  const end=hover.find(x=>x.at>active[0].at && x.kind!=='affection');
  const span=end.at-active[0].at;assert(span>=2250&&span<=2550);
  assert.equal((await state()).reactionId,'1');
  report.checks.hover_dwell_and_one_shot={observed_dwell_ms:active[0].at,observed_response_ms:span,reaction_count_after_5s:1,frames:active};
  await reset();p=await point();await page.mouse.click(p.x,p.y);await page.waitForFunction(()=>document.querySelector('#pet').dataset.kind==='affection');
  await page.mouse.click(p.x,p.y);await page.mouse.click(p.x,p.y);
  assert.equal((await state()).reactionId,'1');report.checks.rapid_click_does_not_restart=true;
  await page.mouse.move(p.x,p.y);await page.mouse.down();await page.mouse.move(p.x+45,p.y,{steps:8});
  assert.equal((await state()).kind,'drag');assert.equal((await state()).state,'running-right');
  const dragging=await sample(1250);assert.equal(new Set(dragging.map(x=>x.frame)).size,8);
  await page.mouse.move(p.x-30,p.y,{steps:12});assert.equal((await state()).state,'running-left');
  await page.mouse.up();assert.notEqual((await state()).kind,'affection');assert.equal((await state()).reactionId,'1');
  report.checks.actual_drag_capture_direction_and_release_no_click=true;
  await page.locator('#activity').selectOption('waiting');p=await point();await page.mouse.click(p.x,p.y);
  assert.equal((await state()).kind,'task');assert.equal((await state()).state,'waiting');report.checks.task_priority=true;
  await page.locator('#reduced-motion').check();await page.locator('#activity').selectOption('running');
  const reduced=await sample(500);assert(reduced.every(x=>x.frame==='0'));report.checks.reduced_motion=true;
  await page.locator('#activity').selectOption('idle');await page.locator('#reduced-motion').uncheck();
  await page.locator('#background').selectOption('dark');await page.locator('#zoom').selectOption('2');
  const box=await canvas.boundingBox();assert.equal(box.width,384);assert.equal(box.height,416);
  await page.screenshot({path:path.join(root,'qa/browser-dark-2x.png')});report.checks.dark_and_2x=true;
  await page.locator('#zoom').selectOption('1');await page.locator('#reset-position').click();
  await reset();await canvas.focus();await page.keyboard.press('Enter');await page.waitForFunction(()=>document.querySelector('#pet').dataset.kind==='affection');
  await page.keyboard.press('Escape');assert.notEqual((await state()).kind,'affection');report.checks.keyboard_activation_and_cancel=true;
  assert.deepEqual(errors,[]);report.console_errors=errors;report.ok=true;
 }catch(e){report.ok=false;report.error=e.stack;await page.screenshot({path:path.join(root,'qa/browser-failure.png')});throw e;}
 finally{fs.writeFileSync(path.join(root,'qa/browser-tests.json'),JSON.stringify(report,null,2));await browser.close();}
 console.log(JSON.stringify({ok:report.ok,checks:Object.keys(report.checks),console_errors:errors}));
})().catch(e=>{console.error(e.message);process.exitCode=1;});
