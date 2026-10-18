// Visual refinement verification. Uses the existing isolated synthetic test backend.
// No customer database or real credentials. Optional screenshots are for local QA only.
const { chromium, expect } = require('@playwright/test');
const { spawn } = require('node:child_process');
const path = require('node:path');
const crypto = require('node:crypto');
const fs = require('node:fs');
const root=path.resolve(__dirname,'../..');
const python=process.env.AEGIS_PYTHON||path.join(root,'.venv',process.platform==='win32'?'Scripts/python.exe':'bin/python');
const password=crypto.randomBytes(24).toString('base64url');
const env={...process.env,AEGIS_E2E_PASSWORD:password,API_PROXY_TARGET:'http://127.0.0.1:8010'};
const children=[];
async function main(){
 const browser=await chromium.launch({headless:true,...(process.env.AEGIS_BROWSER_EXECUTABLE?{executablePath:process.env.AEGIS_BROWSER_EXECUTABLE,args:JSON.parse(process.env.AEGIS_BROWSER_ARGS||'[]')}: {})});
 try{
  children.push(spawn(python,['-m','uvicorn','browser_server:create','--factory','--app-dir','tests','--host','127.0.0.1','--port','8010','--no-proxy-headers'],{cwd:path.join(root,'backend'),env,stdio:'ignore'}));
  children.push(spawn(process.execPath,['node_modules/vite/bin/vite.js','--port','5174'],{cwd:path.join(root,'frontend'),env,stdio:'ignore'}));
  for(let attempt=0;attempt<120;attempt++){
   if(children.some(c=>c.exitCode!==null))throw Error('Isolated server exited; check ports 8010 and 5174');
   try{if((await fetch('http://127.0.0.1:5174/api/v1/health/live')).ok)break}catch{}
   if(attempt===119)throw Error('Startup timeout');
   await new Promise(r=>setTimeout(r,250));
  }
  const page=await browser.newPage({viewport:{width:1280,height:900}}),errors=[];
  page.on('pageerror',error=>errors.push(error.message));
  await page.goto('http://127.0.0.1:5174/');
  expect(await page.locator('.agent-avatar').count()).toBe(0);
  await page.goto('http://127.0.0.1:5174/login');
  expect(await page.locator('.agent-avatar').count()).toBe(0);
  await page.getByLabel('Email',{exact:true}).fill('synthetic-admin@example.com');
  await page.getByLabel('Password',{exact:true}).fill(password);
  await page.getByRole('button',{name:'Sign in',exact:true}).click();
  await expect(page.getByRole('heading',{name:'Your lending workspace'})).toBeVisible();
  expect(await page.locator('.agent-avatar').count()).toBe(0);
  await page.getByRole('link',{name:'Assistant',exact:true}).click();
  const avatar=page.locator('.chat-header .agent-avatar img');
  await expect(avatar).toBeVisible();
  await expect.poll(()=>avatar.evaluate(img=>img.complete&&img.naturalWidth>0)).toBeTruthy();
  expect(await avatar.getAttribute('src')).toBe('/agents/chatbot-3d.png');
  const alpha=await avatar.evaluate(img=>{
   const canvas=document.createElement('canvas');canvas.width=img.naturalWidth;canvas.height=img.naturalHeight;
   const ctx=canvas.getContext('2d');ctx.drawImage(img,0,0);const data=ctx.getImageData(0,0,canvas.width,canvas.height).data;
   let clear=0,opaque=0,partial=0;for(let i=3;i<data.length;i+=4){if(data[i]===0)clear++;else if(data[i]===255)opaque++;else partial++}
   return {width:canvas.width,height:canvas.height,clear,opaque,partial,corners:[data[3],data[(canvas.width-1)*4+3],data[(canvas.width*(canvas.height-1))*4+3],data[data.length-1]]};
  });
  expect(alpha.clear).toBeGreaterThan(0);expect(alpha.opaque).toBeGreaterThan(0);expect(alpha.corners).toEqual([0,0,0,0]);
  const header=page.locator('.chat-header');
  for(const [name,color,foreground] of [['light','#ffffff','#152c40'],['dark','#132e43','#ffffff']]){
   // Background override is confined to this test, not a new application theme.
   await header.evaluate((el,{color,foreground})=>{el.style.backgroundColor=color;el.style.color=foreground;el.querySelector('.muted').style.color=foreground},{color,foreground});
   expect(await page.locator('.agent-avatar').evaluate(el=>getComputedStyle(el).backgroundColor)).toBe('rgba(0, 0, 0, 0)');
   expect(await avatar.evaluate(img=>getComputedStyle(img).objectFit)).toBe('contain');
   await expect(avatar).toBeVisible();
   if(process.env.AEGIS_AVATAR_SCREENSHOTS){fs.mkdirSync(process.env.AEGIS_AVATAR_SCREENSHOTS,{recursive:true});await header.screenshot({path:path.join(process.env.AEGIS_AVATAR_SCREENSHOTS,name+'.png')})}
  }
  await page.setViewportSize({width:390,height:844});
  await expect(avatar).toBeVisible();expect(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth)).toBeTruthy();
  await page.emulateMedia({reducedMotion:'reduce'});
  expect(await avatar.evaluate(img=>getComputedStyle(img).animationName)).toBe('none');
  await page.getByRole('button',{name:'Minimize',exact:true}).click();expect(await page.locator('.agent-avatar').count()).toBe(0);
  await page.getByRole('button',{name:'Open chat',exact:true}).click();await expect(avatar).toBeVisible();
  await page.route('**/agents/chatbot-3d.png',route=>route.abort());
  await page.getByRole('button',{name:'Minimize',exact:true}).click();await page.getByRole('button',{name:'Open chat',exact:true}).click();
  await expect(page.locator('.agent-fallback')).toBeVisible();await expect(page.getByLabel('Your question')).toBeEditable();
  expect(errors).toEqual([]);
  console.log(JSON.stringify({result:'PASS',checks:['chatbot-only placement','real PNG load','alpha channel','light header','dark header','mobile overflow','reduced motion','minimize/reopen','failed-image fallback','no page errors'],alpha},null,2));
 }finally{await browser.close();for(const child of children)child.kill()}
}
main().catch(error=>{console.error(error.message);process.exitCode=1;for(const child of children)child.kill()});
