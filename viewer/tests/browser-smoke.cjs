const {chromium}=require('@playwright/test');
(async()=>{
const b=await chromium.launch({executablePath:process.env.CHROMIUM_PATH || '/usr/bin/chromium',headless:true,args:['--no-sandbox','--enable-unsafe-swiftshader','--use-angle=swiftshader']});
const p=await b.newPage({viewport:{width:1440,height:1050}});const errors=[];p.on('pageerror',e=>errors.push(e.message));
await p.goto(process.env.VIEWER_URL || 'http://127.0.0.1:4173');await p.waitForFunction(()=>!document.querySelector('#asset-status').textContent,{timeout:30000});
console.log('animation:',await p.locator('#animation-info').textContent());
console.log('cameras:',await p.locator('#camera').textContent());
await p.locator('#play').click();await p.locator('#timeline').fill('2.5');await p.locator('#timeline').dispatchEvent('input');

await p.locator('#camera').selectOption('0');await p.waitForTimeout(200);
await p.locator('#play').click();await p.waitForTimeout(3000);console.log('time:',await p.locator('#timeline').inputValue());if((await p.locator('#timeline').inputValue())<=2.5)throw new Error('Real asset animation stopped');
await p.locator('[data-mode="image"]').click();
await p.waitForFunction(()=>document.querySelector('#render-image').naturalWidth===480);
await p.locator('[data-mode="video"]').click();
await p.waitForFunction(()=>{const v=document.querySelector('#render-video');return v.readyState>=2 && v.videoWidth===480 && Math.abs(v.duration-6)<0.05});
await p.locator('#render-video').evaluate(v=>{v.muted=true;return v.play()});
await p.waitForFunction(()=>document.querySelector('#render-video').currentTime>0.1);
console.log('PASS actual PNG decode and six-second MP4 playback.');
await p.setViewportSize({width:390,height:844});
if(await p.evaluate(()=>document.documentElement.scrollWidth>innerWidth))throw new Error('Mobile layout overflows');
if(errors.length)throw new Error(errors.join('\n'));console.log('PASS real GLB loading, imported camera, animated timeline advance.');
await b.close();})().catch(e=>{console.error(e);process.exit(1)});
