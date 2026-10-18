// Real browser workflow. Uses an isolated synthetic backend; never connects to the user's MySQL.
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
  // Check browser availability before starting servers.
  const browser=await chromium.launch({headless:true});
  try{
    children.push(spawn(python,['-m','uvicorn','browser_server:create','--factory','--app-dir','tests','--host','127.0.0.1','--port','8010','--no-proxy-headers'],{cwd:path.join(root,'backend'),env,stdio:'ignore'}));
    children.push(spawn(process.execPath,['node_modules/vite/bin/vite.js','--port','5174'],{cwd:path.join(root,'frontend'),env,stdio:'ignore'}));
    for(let attempt=0;attempt<120;attempt++){
      if(children.some(c=>c.exitCode!==null))throw Error('Test server exited; check ports 8010 and 5174.');
      try{if((await fetch('http://127.0.0.1:5174/api/v1/health/live')).ok)break}catch{}
      if(attempt===119)throw Error('Test server startup timeout');
      await new Promise(r=>setTimeout(r,250));
    }
    const page=await browser.newPage({viewport:{width:1365,height:900}});
    const errors=[];page.on('pageerror',e=>errors.push(e.message));
    await page.goto('http://127.0.0.1:5174/register');
    await page.getByLabel('Email',{exact:true}).fill('synthetic-customer@example.com');
    await page.getByLabel('Password',{exact:true}).fill(password);
    await page.getByRole('button',{name:'Register & sign in'}).click();
    await expect(page.getByRole('heading',{name:'Your lending workspace'})).toBeVisible();
    await page.getByRole('link',{name:'Products',exact:true}).click();
    await page.getByRole('link',{name:'Estimate & apply'}).first().click();
    await page.getByRole('button',{name:'Calculate estimate'}).click();
    await expect(page.getByText('Estimate calculated.')).toBeVisible();
    await page.getByRole('button',{name:'Create application draft'}).click();
    await page.getByRole('button',{name:'Edit saved draft'}).click();
    await page.getByLabel('Requested amount',{exact:true}).fill('120000');
    await page.getByRole('button',{name:'Save revised draft'}).click();
    await expect(page.getByRole('button',{name:'Edit saved draft'})).toBeVisible();
    await page.getByRole('button',{name:'Submit for review'}).click();
    await expect(page.getByText('submitted',{exact:true}).first()).toBeVisible();
    await page.getByRole('link',{name:'Appointments',exact:true}).click();
    await page.getByRole('button',{name:'Book appointment'}).click();
    await expect(page.getByText('Appointment booked.')).toBeVisible();
    expect(await page.locator('img[src*="agents/"]').count()).toBe(0);
    await page.getByRole('link',{name:'Assistant',exact:true}).click();
    const avatar=page.getByAltText('Illustrated AegisLend banking assistant in a navy blazer');
    await expect(avatar).toBeVisible();
    await expect.poll(()=>avatar.evaluate(image=>image.complete&&image.naturalWidth>0)).toBeTruthy();
    await page.getByRole('button',{name:'Minimize'}).click();
    await expect(avatar).toHaveCount(0);
    await page.getByRole('button',{name:'Open chat'}).click();
    await page.getByRole('button',{name:'Ask the assistant'}).click();
    await expect(page.getByText('Academic demonstration policy',{exact:false}).first()).toBeVisible();
    await page.getByRole('button',{name:'Sign out'}).click();
    await page.getByLabel('Email',{exact:true}).fill('synthetic-admin@example.com');
    await page.getByLabel('Password',{exact:true}).fill(password);
    await page.getByRole('button',{name:'Sign in',exact:true}).click();
    await page.getByRole('link',{name:'Admin',exact:true}).click();
    await page.locator('a[href="/admin/applications"]').first().click();
    await page.getByLabel('Required human review note').fill('Synthetic authorized human review');
    await page.getByRole('button',{name:'under review',exact:true}).click();
    await expect(page.getByRole('button',{name:'approved',exact:true})).toBeVisible();
    await page.getByLabel('Required human review note').fill('Approved for academic demonstration only');
    await page.getByRole('button',{name:'approved',exact:true}).click();
    await page.getByRole('link',{name:'Admin',exact:true}).click();
    await page.locator('a[href="/admin/security"]').first().click();
    await page.getByRole('button',{name:'Generate controlled probe'}).click();
    await expect(page.getByRole('heading',{name:'demo probe'})).toBeVisible();
    await page.setViewportSize({width:390,height:844});
    await page.getByRole('button',{name:'Menu',exact:true}).click();
    await expect(page.getByRole('link',{name:'Dashboard',exact:true})).toBeVisible();
    expect(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth)).toBeTruthy();
    await page.emulateMedia({reducedMotion:'reduce'});
    expect(await page.evaluate(()=>matchMedia('(prefers-reduced-motion: reduce)').matches)).toBeTruthy();
    expect(errors).toEqual([]);
    console.log('PASS: browser registration, login, eligibility, application, appointment, sources, admin review, IDS probe and mobile overflow checks');
  }finally{await browser.close();for(const child of children)child.kill();}
}
main().catch(e=>{console.error(e.message);process.exitCode=1;for(const child of children)child.kill()});
