'use strict';
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
function create(path,width,height,dpr){
 const out={matrices:{},attrs:null};let next=10;const constants=new Map();
 const methods={getShaderParameter:()=>true,getProgramParameter:()=>true,getExtension:()=>null,getUniformLocation:(_,s)=>s,getAttribLocation:()=>0,isContextLost:()=>false,uniformMatrix4fv:(key,transpose,data)=>out.matrices[key]=Array.from(data),viewport:(...v)=>out.viewport=v};
 const gl=new Proxy(methods,{get(o,k){if(k in o)return o[k];if(/^[A-Z_0-9]+$/.test(k)){if(!constants.has(k))constants.set(k,next++);return constants.get(k)}return()=>({})}});
 const canvas={clientWidth:width,clientHeight:height,width:300,height:150,getContext:(name,attrs)=>{out.attrs=attrs;return gl}};
 const mesh={positions:Buffer.from(new Int16Array([0,0,0]).buffer).toString('base64'),normals:Buffer.from(new Int16Array([0,32767,0]).buffer).toString('base64'),indices:Buffer.from(new Uint16Array([0,0,0]).buffer).toString('base64'),indexBytes:2,scale:1};
 const env={window:{NOIR_MESH:mesh},location:{search:'?arm=original'},URLSearchParams,devicePixelRatio:dpr,atob:s=>Buffer.from(s,'base64').toString('binary'),Float32Array,Int16Array,Uint16Array,Uint32Array,Uint8Array,Math};vm.runInNewContext(fs.readFileSync(path,'utf8'),env);const engine=env.window.NoirEngine.create(canvas,{});return{engine,out,canvas};
}
const newer=process.argv[2]||'src/engine.js',older=process.argv[3];
if(older){
 const a=create(older,1760,832,1),b=create(newer,1760,832,1);let max=0;
 for(let i=0;i<100;i++){
  const pose={theta:-3+6*i/99,phi:-.1+.2*(i%7)/6,radius:4.2+(i%13)*.7,y:-2.15+(i%11)*.427,sx:.47,sy:0};a.engine.render(pose);b.engine.render(pose);
  for(const key of ['uView','uProjection','uModel'])for(let j=0;j<16;j++)max=Math.max(max,Math.abs(a.out.matrices[key][j]-b.out.matrices[key][j]));
  for(const point of [[0,3,0],[0,-3,0],[.2,1.4,.4]]){const ap=a.engine.project(point),bp=b.engine.project(point);assert.ok(Math.abs(ap.x-bp.x)<1e-7);assert.ok(Math.abs(ap.y-bp.y)<1e-7)}
 }
 assert.ok(max<1e-6,`matrix drift ${max}`);console.log('PASS: 100 camera matrices and 300 projected points match the original; max float error',max);
}
for(const [width,height,dpr] of [[1760,832,2],[3840,2160,2],[390,844,3]]){
 const {canvas,out}=create(newer,width,height,dpr);
 assert.equal(out.attrs.preserveDrawingBuffer,false);
 if(width>760)assert.ok(canvas.width*canvas.height<=4510000);
 else assert.equal(canvas.width,585);
 console.log('PASS:',width,height,dpr,'drawing buffer',canvas.width,canvas.height);
}
