'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const {WheelIntent}=require('../src/scroll.js');

test('render-delayed decaying events cannot become fresh gestures', () => {
 const g=new WheelIntent(), results=[];
 for(let i=0;i<45;i++)if(g.read(120*(.88**i),i*300).step)results.push(i);
 assert.deepEqual(results,[0]);
});
test('late decay cannot re-arm navigation, but renewed deliberate input can', () => {
 const g=new WheelIntent();g.read(120,0);
 assert.equal(g.read(105,700).step,0);assert.equal(g.read(90,1400).step,0);
 assert.equal(g.read(120,1700,false).step,1);
});
