'use strict';
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {Controller, shortestAngle, KEYS} = require('../src/motion.js');
const report=[];
const test=(name,f)=>{try{f();report.push({test:name,passed:true});console.log('PASS:',name)}catch(e){report.push({test:name,passed:false,detail:e.message});console.error('FAIL:',name,e.message)}};
const pose=(id,mobile=false)=>id==='home'?{theta:.39,phi:.025,radius:mobile?14.6:11.9,y:-.25,sx:-.40,sy:mobile?.15:0}:
({theta:{artist:-.55,work:.75,ritual:-.95,booking:1.02}[id],phi:id==='booking'?-.1:.015,radius:mobile?5.4:id==='booking'?4.2:5.05,y:{artist:2.12,work:.08,ritual:-1.24,booking:-2.15}[id],sx:mobile?-.04:.47,sy:mobile?-.46:0});
const ids=['home','artist','work','ritual','booking'];
for(const mobile of [false,true])for(const a of ids)for(const b of ids){
 if(a===b)continue;
 test(`${mobile?'mobile':'desktop'} ${a} -> ${b}: bounded path and exact endpoint`,()=>{
  const start=pose(a,mobile),end=pose(b,mobile),c=new Controller(start);c.retarget(end);
  let n=0;
  while(c.active&&n++<250){c.step(1/60);for(const key of KEYS){assert.ok(Number.isFinite(c.pose[key]));const low=Math.min(start[key],end[key]),high=Math.max(start[key],end[key]);assert.ok(c.pose[key]>=low-1e-9&&c.pose[key]<=high+1e-9,`${key} overshoot`)} }
  assert.ok(!c.active);for(const key of KEYS)assert.ok(Math.abs(c.pose[key]-end[key])<1e-12);
 });
}
test('Retarget preserves position, velocity and acceleration exactly',()=>{
 const c=new Controller(pose('home'));c.retarget(pose('artist'));for(let i=0;i<25;i++)c.step(1/60);
 const before=c.snapshot();c.retarget(pose('booking'));const after=c.snapshot();
 for(const key of KEYS)for(const property of ['x','v','a'])assert.equal(after[key][property],before[key][property]);
});
test('Repeated target does not restart easing',()=>{
 const c=new Controller(pose('home'));c.retarget(pose('work'));for(let i=0;i<30;i++)c.step(1/60);const snap=c.snapshot();c.retarget(pose('work'));assert.deepEqual(c.snapshot(),snap);
});
test('30/60/120/144 Hz agree at one second',()=>{
 const samples=[30,60,120,144].map(hz=>{const c=new Controller(pose('home'));c.retarget(pose('ritual'));for(let i=0;i<hz;i++)c.step(1/hz);return c.snapshot()});
 for(const sample of samples)for(const key of KEYS)for(const p of ['x','v','a'])assert.ok(Math.abs(sample[key][p]-samples[0][key][p])<1e-10);
});
test('Retarget and reverse continue with unchanged tangent/curvature',()=>{
 const c=new Controller(pose('home'));c.retarget(pose('artist'));for(let i=0;i<30;i++)c.step(1/60);
 const before=c.snapshot();c.retarget(pose('home'));c.step(1e-6);const after=c.snapshot();
 for(const key of KEYS){assert.ok(Math.abs((after[key].x-before[key].x)/1e-6-before[key].v)<.0001);assert.ok(Math.abs((after[key].v-before[key].v)/1e-6-before[key].a)<.001)}
});
test('Long frame is bounded instead of jumping to the endpoint',()=>{
 const a=new Controller(pose('home')),b=new Controller(pose('home'));a.retarget(pose('booking'));b.retarget(pose('booking'));a.step(30);b.step(.064);assert.deepEqual(a.snapshot(),b.snapshot());assert.ok(a.active);
});
test('Zero delta freezes the complete motion state',()=>{
 const c=new Controller(pose('home'));c.retarget(pose('artist'));c.step(.2);const snap=c.snapshot();c.step(0);assert.deepEqual(c.snapshot(),snap);
});
test('Crossing the angular seam takes 20 degrees, not 340',()=>{
 const d=Math.PI/180;assert.ok(Math.abs(shortestAngle(170*d,-170*d)-190*d)<1e-12);assert.ok(Math.abs(shortestAngle(-170*d,170*d)+190*d)<1e-12);
});
test('No zoom pulse on same-radius section journeys',()=>{
 const c=new Controller(pose('artist'));c.retarget(pose('ritual'));for(let i=0;i<180;i++){c.step(1/60);assert.ok(Math.abs(c.pose.radius-5.05)<1e-12)}
});
test('500 rapid retargets stay finite and within authored radial/vertical bounds',()=>{
 const c=new Controller(pose('home'));for(let i=0;i<500;i++){c.retarget(pose(ids[(i*37)%5],i%3===0));c.step(1/60);assert.ok(c.pose.radius>=4.2-1e-9&&c.pose.radius<=14.6+1e-9);assert.ok(c.pose.y>=-2.15-1e-9&&c.pose.y<=2.12+1e-9);for(const k of KEYS)assert.ok(Number.isFinite(c.pose[k]))}
 c.retarget(pose('work'));for(let i=0;i<240;i++)c.step(1/60);assert.ok(!c.active);
});
test('Reset/reduced motion zeros derivatives and leaves no idle movement',()=>{
 const c=new Controller(pose('home'));c.retarget(pose('artist'));c.step(.064);c.reset(pose('work'));const snap=c.snapshot();c.step(1/60);assert.deepEqual(c.snapshot(),snap);assert.ok(!c.active);for(const s of Object.values(snap)){assert.equal(s.v,0);assert.equal(s.a,0)}
});
test('Invalid numbers are rejected before corrupting the camera',()=>{
 assert.throws(()=>new Controller({...pose('home'),radius:0}));assert.throws(()=>new Controller({...pose('home'),theta:NaN}));const c=new Controller(pose('home'));assert.throws(()=>c.step(-1));assert.throws(()=>c.step(Infinity));
});
fs.mkdirSync(path.join(__dirname,'../evidence'),{recursive:true});
fs.writeFileSync(path.join(__dirname,'../evidence/motion-tests.json'),JSON.stringify({passed:report.filter(r=>r.passed).length,failed:report.filter(r=>!r.passed).length,tests:report},null,2));
if(report.some(r=>!r.passed))process.exitCode=1;
