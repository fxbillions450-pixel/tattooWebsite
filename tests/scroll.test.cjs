'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {WheelIntent, normalizeWheel, canScroll} = require('../src/scroll.js');

test('pixel, line and page units normalize without losing direction', () => {
 assert.deepEqual(normalizeWheel({deltaX:2,deltaY:-40,deltaMode:0}),{x:2,y:-40});
 assert.equal(normalizeWheel({deltaX:0,deltaY:3,deltaMode:1}).y,48);
 assert.equal(normalizeWheel({deltaX:0,deltaY:-1,deltaMode:2},720).y,-720);
});
test('native content scrolls only when it has room in the requested direction', () => {
 const element={scrollHeight:600,clientHeight:300,scrollTop:0};
 assert.equal(canScroll(element,-1),false);assert.equal(canScroll(element,1),true);
 element.scrollTop=150;assert.equal(canScroll(element,-1),true);assert.equal(canScroll(element,1),true);
 element.scrollTop=300;assert.equal(canScroll(element,1),false);assert.equal(canScroll(element,-1),true);
 element.scrollTop=-20;assert.equal(canScroll(element,-1),false);
 element.scrollTop=299.8;assert.equal(canScroll(element,1),false);
 assert.equal(canScroll(null,1),false);
 assert.equal(canScroll({scrollHeight:300,clientHeight:300,scrollTop:0},1),false);
});
test('a 40px notch navigates back from the artist panel top', () => {
 assert.deepEqual(new WheelIntent().read(-40,0,false),{prevent:true,step:-1});
});
test('one standard three-line notch navigates', () => {
 const d=normalizeWheel({deltaX:0,deltaY:-3,deltaMode:1}).y;
 assert.equal(new WheelIntent().read(d,0,false).step,-1);
});
test('slow subthreshold mouse notches accumulate instead of being discarded forever', () => {
 const g=new WheelIntent();assert.equal(g.read(-20,0).step,0);assert.equal(g.read(-20,240).step,-1);
});
test('old unfinished input expires after a genuine pause', () => {
 const g=new WheelIntent();g.read(20,0);assert.equal(g.read(20,800).step,0);
});
test('small trackpad deltas accumulate within a stroke', () => {
 const g=new WheelIntent();for(let i=0;i<4;i++)assert.equal(g.read(8,i*16).step,0);
 assert.equal(g.read(8,64).step,1);
});
test('decaying trackpad momentum never skips a second section', () => {
 const g=new WheelIntent(), results=[];
 for(let i=0;i<120;i++){const d=120*Math.exp(-i/20);if(g.read(d,i*16).step)results.push(i);}
 assert.deepEqual(results,[0]);
});
test('continuous deliberate wheel input re-arms rather than staying locked forever', () => {
 const g=new WheelIntent(),results=[];
 for(let i=0;i<24;i++)if(g.read(120,i*100).step)results.push(i);
 assert.deepEqual(results,[0,7,14,21]);
});
test('a deliberate reversal can redirect an in-progress camera journey', () => {
 const g=new WheelIntent();assert.equal(g.read(120,0).step,1);assert.equal(g.read(-80,70).step,-1);
});
test('an opposite-sign jitter does not unlock forward momentum', () => {
 const g=new WheelIntent();g.read(120,0);
 assert.equal(g.read(-2,16).step,0);assert.equal(g.read(70,32).step,0);
});
test('a gentle but sustained reverse is recognized', () => {
 const g=new WheelIntent();g.read(100,0);
 assert.equal(g.read(-12,16).step,0);assert.equal(g.read(-12,32).step,0);assert.equal(g.read(-12,48).step,-1);
});
test('reading consumes the gesture even when content reaches its bottom', () => {
 const g=new WheelIntent();assert.deepEqual(g.read(120,0,true),{prevent:false,step:0});
 assert.deepEqual(g.read(80,30,false),{prevent:true,step:0});
 assert.deepEqual(g.read(40,60,false),{prevent:true,step:0});
 assert.deepEqual(g.read(120,300,false),{prevent:true,step:1});
});
test('reaching panel top does not immediately throw the reader home', () => {
 const g=new WheelIntent();assert.equal(g.read(-120,0,true).prevent,false);
 assert.equal(g.read(-80,30,false).step,0);assert.equal(g.read(-50,60,false).step,0);
 assert.equal(g.read(-40,350,false).step,-1);
});
test('a navigation stroke cannot start scrolling a newly revealed panel', () => {
 const g=new WheelIntent();g.read(120,0,false);
 assert.deepEqual(g.read(80,40,true),{prevent:true,step:0});
});
test('native reading reversal stays native while content has room', () => {
 const g=new WheelIntent();g.read(12,0,true);assert.equal(g.read(-6,16,true).prevent,false);
});
test('reset clears stale input after click navigation or tab changes', () => {
 const g=new WheelIntent();g.read(120,0);g.reset();assert.equal(g.read(120,50).step,1);
});
test('zero, non-finite values and subpixel noise do not navigate', () => {
 const g=new WheelIntent();for(const d of [0,.1,-.1,NaN,Infinity,-Infinity])assert.equal(g.read(d,0).step,0);
});
