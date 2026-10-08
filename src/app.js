(() => {
'use strict';
const $=(s,r=document)=>r.querySelector(s), $$=(s,r=document)=>[...r.querySelectorAll(s)];
const app=$('#app'),canvas=$('#scene'),panel=$('#panel'),scroll=$('#section-content'),status=$('#status');
const order=['home','artist','work','ritual','booking'];
const sections={
 artist:{number:'01',label:'THE ARTIST',place:'UPPER ARM',y:2.12,theta:-.55,r:.535,title:'No replicas.<br>Only originals.'},
 work:{number:'02',label:'SELECTED WORK',place:'OUTER FOREARM',y:.08,theta:.75,r:.455,title:'Made to be<br>part of you.'},
 ritual:{number:'03',label:'THE RITUAL',place:'INNER FOREARM',y:-1.24,theta:-.95,r:.30,title:'Nothing rushed.<br>Nothing ordinary.'},
 booking:{number:'04',label:'BEGIN YOUR PIECE',place:'THE WRIST',y:-2.15,theta:1.02,r:.285,title:'Your story.<br>Our next chapter.'}
};
let section='home',engine=null,transition=null,raf=0,cam=null,accent='red',reduceMotion=matchMedia('(prefers-reduced-motion: reduce)').matches;
let pointerDown=null,artOrigin=null;
let motion=null,lastFrame=null,panelSection=null,panelExitUntil=0,assetsWarmed=false,panelNeedsContent=true;

const cachedArt={};
const store={get(k){try{return localStorage.getItem(k)}catch{return null}},set(k,v){try{localStorage.setItem(k,v)}catch{}}};
const savedColor=store.get('noir-accent');if(savedColor==='purple')accent='purple';
if(store.get('noir-reduced-motion')==='true')reduceMotion=true;
const mobile=()=>innerWidth<=760;
function pose(id){if(id==='home')return{theta:.39,phi:.025,radius:mobile()?14.6:11.9,y:-.25,sx:mobile()?-.40:-.40,sy:mobile()?.15:0};const s=sections[id];return{theta:s.theta,phi:id==='booking'?-.1:.015,radius:mobile()?5.4:(id==='booking'?4.2:5.05),y:s.y,sx:mobile()?-.04:.47,sy:mobile()?-.46:0}}
function surface(s){return[Math.sin(s.theta)*s.r+(s.y>1?-.07:.07),s.y,Math.cos(s.theta)*s.r*.90]}
for(const [id,s]of Object.entries(sections)){const b=document.createElement('button');b.className='hotspot';b.dataset.section=id;b.setAttribute('aria-label',`${s.number}. ${s.label.toLowerCase()}, ${s.place.toLowerCase()}. Zoom to section.`);b.innerHTML=`<span class="dot"></span><span class="leader"></span><span class="hot-label"><em>${s.number}</em>${s.label}</span>`;$('#hotspots').append(b)}
const hotspotNodes=$$('.hotspot').map(el=>({el,point:surface(sections[el.dataset.section])}));
function study(kind){return cachedArt[kind]||(cachedArt[kind]=NoirArt.study(kind))}
function markup(id){
 const s=sections[id],heading=`<h2 id="section-title" tabindex="-1">${s.title}</h2>`;
 if(id==='artist')return heading+`<p class="description">An individual language, written in ink. Bold blackwork. Considered composition. An obsession with the space between.</p><div class="tags"><span class="tag">BLACKWORK</span><span class="tag">ORNAMENTAL</span><span class="tag">CUSTOM SLEEVES</span></div><p class="quote">“The best piece is the one that could only belong to you.”</p><p class="description">A place for the artist's story, philosophy and personal approach. Here, the sleeve is more than a portfolio. It's the way in.</p><a class="panel-link" href="#work" data-section="work">Explore the work <span aria-hidden="true">↗</span></a><p class="panel-foot">CONCEPT COPY / ARTIST IDENTITY TO BE ADDED</p>`;
 if(id==='work')return heading+`<p class="description">A collection of original sleeve studies.<br>Select a piece to take a closer look.</p><div class="gallery">${[['rose','BOTANICAL','BLACKWORK / STUDY 01'],['moth','NOCTURNE','ORNAMENTAL / STUDY 02'],['skull','MEMENTO','ILLUSTRATIVE / STUDY 03'],['dagger','DEVOTION','LINEWORK / STUDY 04']].map(([kind,title,sub])=>`<button class="art-card" data-art="${kind}" data-title="${title}" aria-label="Open ${title.toLowerCase()} artwork"><img class="art-image" src="${study(kind)}" alt="${title.toLowerCase()} blackwork concept, drawn on warm-gray paper"><span class="card-info">${title}<small>${sub}</small></span></button>`).join('')}</div><p class="panel-foot">ORIGINAL PROCEDURAL STUDIES / NOT COMPLETED TATTOOS</p><a class="panel-link" href="#ritual" data-section="ritual">Behind the piece <span aria-hidden="true">↗</span></a>`;
 if(id==='ritual')return heading+`<div class="ritual-step"><span>01</span><div><h3>The conversation.</h3><p>Your idea, your placement, your intention. Every piece begins with understanding what it should mean to you.</p></div></div><div class="ritual-step"><span>02</span><div><h3>The composition.</h3><p>A custom design that follows the body, not a template. Shape, contrast and negative space, considered together.</p></div></div><div class="ritual-step"><span>03</span><div><h3>The session.</h3><p>A focused appointment. Space to settle in, ask questions and watch the artwork become part of you.</p></div></div><a class="panel-link" href="#booking" data-section="booking">Begin your piece <span aria-hidden="true">↗</span></a><p class="panel-foot">ILLUSTRATIVE STUDIO PROCESS / FINAL DETAILS TO BE CONFIRMED</p>`;
 return heading+`<p class="description">Every piece begins with an idea.<br>Tell us a little about yours.</p><form class="booking-form" id="booking-form"><div class="form-row"><label>Your name<input name="name" autocomplete="name" required maxlength="80" placeholder="Your name"></label><label>Email address<input type="email" name="email" autocomplete="email" required maxlength="254" placeholder="you@email.com"></label></div><label>Placement<select name="placement" required><option value="" disabled selected>Choose a placement</option><option>Full sleeve</option><option>Upper arm</option><option>Forearm</option><option>Another placement</option></select></label><label>The idea<textarea name="idea" required minlength="10" maxlength="1600" placeholder="The story, the style, what you have in mind..."></textarea></label><button class="send-button" type="submit">PREVIEW YOUR REQUEST <span aria-hidden="true">↗</span></button><p class="demo-note">DEMO ONLY. Nothing is sent, saved or booked. Please use fictional details while exploring.</p></form>`;
}
function updateNavigation(){
 app.classList.toggle('focused',section!=='home');
 $('#home-content').inert=section!=='home';
 $$('.topnav [data-section],.section-nav [data-section]').forEach(el=>{if(el.dataset.section===section)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current')});
 $$('.hotspot').forEach(el=>el.classList.toggle('selected',el.dataset.section===section));
 $('#prev').disabled=section==='home';$('#next').disabled=section==='booking';
 app.classList.remove('menu-open');$('.menu-toggle').setAttribute('aria-expanded','false');$('.menu-toggle').setAttribute('aria-label','Open navigation');
}
function mountPanelContent(){
 if(section==='home'||(panelSection===section&&!panelNeedsContent))return;
 const s=sections[section];
 $('.section-number').textContent=s.number;$('#panel-label').textContent=s.label;
 $('.big-index').textContent=s.number;$('.location-name').innerHTML=s.place+'<br>'+s.label;
 scroll.innerHTML=markup(section);scroll.scrollTop=0;
 panelSection=section;panel.dataset.contentSection=section;panelNeedsContent=false;
}
function panelVisibility(show){
 const wasVisible=app.classList.contains('panel-visible');
 if(!show&&wasVisible)panelExitUntil=performance.now()+(reduceMotion?0:220);
 app.classList.toggle('panel-visible',show);
 panel.inert=!show||!!transition;
 panel.setAttribute('aria-hidden',show?'false':'true');
}
function revealPanel(now,force=false){
 if(section==='home')return;
 if(!force&&(now<panelExitUntil||!motion.nearDestination))return;
 mountPanelContent();panelVisibility(true);
}
function finish(){
 transition=null;app.classList.remove('transitioning');
 if(section!=='home')revealPanel(performance.now(),true);else panelVisibility(false);
 status.textContent=section==='home'?'Full sleeve. Select a tattoo or use the section menu.':`${sections[section].label}. Camera settled. Section content is ready.`;
 updateOverlay();
}
function requestFrame(){if(!raf&&!document.hidden)raf=requestAnimationFrame(animate)}
function navigate(id,{history=true,immediate=false}={}){
 if(!motion||!order.includes(id))return;
 // Repeated clicks and popstate/hashchange for the same target are idempotent.
 if(id===section&&!immediate){if(!transition&&id!=='home'&&!app.classList.contains('panel-visible'))finish();return}
 if(panel.contains(document.activeElement))document.querySelector('.section-nav [data-section="'+id+'"]')?.focus({preventScroll:true});
 const target=pose(id);section=id;panelNeedsContent=true;panelVisibility(false);updateNavigation();
 if(history&&location.hash!=='#'+id)window.history.pushState({section:id},'', '#'+id);
 if(reduceMotion||immediate||!engine){
  cam=motion.reset(target);transition=null;if(raf)cancelAnimationFrame(raf);raf=0;lastFrame=null;draw();finish();return;
 }
 const wasMoving=!!transition;
 motion.retarget(target);transition={to:target};
 if(!wasMoving)lastFrame=performance.now();
 app.classList.add('transitioning');
 status.textContent=`Moving to ${id==='home'?'the full sleeve':sections[id].label.toLowerCase()}.`;
 requestFrame();
}
function animate(now){
 raf=0;if(!transition||document.hidden){lastFrame=null;return}
 const dt=lastFrame===null?0:Math.max(0,(now-lastFrame)/1000);lastFrame=now;
 cam=motion.step(dt);
 if(!motion.active){draw();finish();lastFrame=null;return}
 revealPanel(now);draw();requestFrame();
}
function updateOverlay(){
 if(!engine)return;
 // Read layout once, BEFORE writing projected marker coordinates.
 const box=section!=='home'&&app.classList.contains('panel-visible')&&!mobile()?panel.getBoundingClientRect():null;
 const offset=mobile()?[-22,-22]:[-12,-23];
 for(const {el,point} of hotspotNodes){
  const p=engine.project(point);
  el.style.transform=`translate3d(${p.x+offset[0]}px,${p.y+offset[1]}px,0)`;
  el.style.visibility=p.depth<.1||p.x<15||p.x>innerWidth-18||p.y<90||p.y>innerHeight-95?'hidden':'visible';
 }
 if(box){const p=engine.project(surface(sections[section])),endX=box.left,endY=box.top+25;
  $('#connector path').setAttribute('d',`M ${p.x} ${p.y} L ${p.x+35} ${p.y} L ${endX-25} ${endY} L ${endX} ${endY}`);
 }
}
function draw(){if(engine&&cam){engine.render(cam,sections[section]);updateOverlay()}}
function changeStep(d){const index=order.indexOf(section);navigate(order[Math.max(0,Math.min(order.length-1,index+d))])}
function updateAccent(){const purple=accent==='purple',hex=purple?'#a877ec':'#ef3349',rgb=purple?'168,119,236':'239,51,73';document.documentElement.style.setProperty('--accent',hex);document.documentElement.style.setProperty('--accent-rgb',rgb);$$('[data-color]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.color===accent)));engine?.setAccent(purple?[.659,.467,.925]:[.937,.20,.286]);draw()}
function updateMotion(){document.body.classList.toggle('reduce-motion',reduceMotion);$('.motion-btn').setAttribute('aria-pressed',String(reduceMotion));$('.motion-btn').setAttribute('aria-label',reduceMotion?'Enable camera motion':'Use reduced motion');$('.motion-label').textContent=reduceMotion?'MOTION OFF':'MOTION ON';if(reduceMotion&&transition){cam=motion.reset(pose(section));transition=null;cancelAnimationFrame(raf);raf=0;lastFrame=null;draw();finish()}}
document.addEventListener('click',event=>{
 const target=event.target.closest('[data-section]');if(target){event.preventDefault();navigate(target.dataset.section);return}
 const color=event.target.closest('[data-color]');if(color){accent=color.dataset.color;store.set('noir-accent',accent);updateAccent();return}
 const art=event.target.closest('[data-art]');if(art){artOrigin=art;$('#dialog-title').textContent=art.dataset.title+' / SLEEVE STUDY';$('.dialog-art').src=study(art.dataset.art);$('.dialog-art').alt=art.dataset.title.toLowerCase()+' blackwork concept artwork';$('#art-dialog').showModal()}
});
$('.menu-toggle').addEventListener('click',()=>{const open=!app.classList.contains('menu-open');app.classList.toggle('menu-open',open);$('.menu-toggle').setAttribute('aria-expanded',String(open));$('.menu-toggle').setAttribute('aria-label',open?'Close navigation':'Open navigation')});
$('.motion-btn').addEventListener('click',()=>{reduceMotion=!reduceMotion;store.set('noir-reduced-motion',String(reduceMotion));updateMotion()});
$('#prev').addEventListener('click',()=>changeStep(-1));$('#next').addEventListener('click',()=>changeStep(1));
$('#close-dialog').addEventListener('click',()=>$('#art-dialog').close());$('#art-dialog').addEventListener('close',()=>artOrigin?.focus());
$('#art-dialog').addEventListener('click',e=>{if(e.target===$('#art-dialog')){const r=e.target.getBoundingClientRect();if(e.clientX<r.left||e.clientX>r.right||e.clientY<r.top||e.clientY>r.bottom)e.target.close()}});
window.addEventListener('popstate',()=>{const id=location.hash.slice(1);navigate(order.includes(id)?id:'home',{history:false})});
window.addEventListener('hashchange',()=>{const id=location.hash.slice(1);if(order.includes(id)&&id!==section)navigate(id,{history:false})});
$('.skip-link').addEventListener('click',e=>{e.preventDefault();if(section==='home')navigate('artist',{immediate:true});scroll.focus()});
document.addEventListener('keydown',e=>{if($('#art-dialog').open)return;if(e.key==='Escape'){if(app.classList.contains('menu-open')){$('.menu-toggle').click();return}navigate('home');return}if(e.target.closest('input,textarea,select,[contenteditable]'))return;if(e.key==='ArrowRight'||e.key==='PageDown'){e.preventDefault();changeStep(1)}else if(e.key==='ArrowLeft'||e.key==='PageUp'){e.preventDefault();changeStep(-1)}else if(e.key==='Home'&&!e.target.closest('#panel')){e.preventDefault();navigate('home')}});
// Boundary-aware wheel/touch navigation; the motion controller remains the sole camera owner.
NoirScroll.install({app,content:scroll,step:changeStep,getSection:()=>section,
 blocked:()=>!assetsWarmed||app.classList.contains('menu-open')||$('#art-dialog').open});
canvas.addEventListener('pointerdown',e=>{if(!e.isPrimary){pointerDown=null;return}pointerDown={x:e.clientX,y:e.clientY,time:performance.now(),type:e.pointerType,id:e.pointerId,moved:false};canvas.setPointerCapture(e.pointerId)});
canvas.addEventListener('pointerup',e=>{if(!pointerDown)return;const dx=e.clientX-pointerDown.x,dy=e.clientY-pointerDown.y;const elapsed=performance.now()-pointerDown.time;
 if(pointerDown.type!=='touch'&&Math.abs(dy)>55&&Math.abs(dy)>Math.abs(dx)*1.2&&elapsed<950){changeStep(dy<0?1:-1)}else if(!pointerDown.moved&&Math.hypot(dx,dy)<12&&elapsed<600&&engine){const p=engine.pick(e.clientX,e.clientY);if(p){const id=p[1]>1.13?'artist':p[1]>-.65?'work':p[1]>-1.73?'ritual':'booking';navigate(id)}}pointerDown=null});
canvas.addEventListener('pointercancel',()=>{pointerDown=null});
canvas.addEventListener('pointermove',e=>{if(pointerDown&&pointerDown.id===e.pointerId&&Math.hypot(e.clientX-pointerDown.x,e.clientY-pointerDown.y)>=12)pointerDown.moved=true;if(e.pointerType==='touch'||!engine)return;const top=engine.project([0,3,0]),bottom=engine.project([0,-3.6,0]);const t=Math.max(0,Math.min(1,(e.clientY-top.y)/(bottom.y-top.y)));const center=top.x+(bottom.x-top.x)*t;canvas.classList.toggle('pickable',Math.abs(e.clientX-center)<(mobile()?80:100)&&e.clientY>Math.min(top.y,bottom.y)&&e.clientY<Math.max(top.y,bottom.y))});
scroll.addEventListener('submit',e=>{if(e.target.id!=='booking-form')return;e.preventDefault();const form=e.target;if(!form.reportValidity())return;const values=new FormData(form);const result=document.createElement('div');result.className='form-result';result.setAttribute('role','status');const heading=document.createElement('b');heading.textContent='Your concept request, previewed.';const details=document.createElement('p');details.textContent=`${String(values.get('name')).trim()} · ${values.get('placement')}\n${values.get('email')}\n\n${values.get('idea')}`;details.style.whiteSpace='pre-wrap';const note=document.createElement('p');note.className='demo-note';note.textContent='NOT SENT. This demo has no booking backend. These details exist only on this screen and disappear when you leave the section.';const reset=document.createElement('button');reset.className='panel-link';reset.type='button';reset.textContent='Edit your concept request';reset.addEventListener('click',()=>{result.replaceWith(form);form.querySelector('input').focus()});result.append(heading,details,note,reset);form.replaceWith(result);scroll.scrollTop=scroll.scrollHeight});
let resizeFrame=0;
addEventListener('resize',()=>{
 if(resizeFrame)return;
 resizeFrame=requestAnimationFrame(()=>{
  resizeFrame=0;if(!motion)return;
  if(engine)engine.resize();
  const target=pose(section);
  if(reduceMotion||!engine){cam=motion.reset(target);transition=null;cancelAnimationFrame(raf);raf=0;lastFrame=null;draw();finish();return}
  // Height-only changes do not restart a journey. Breakpoint changes smoothly
  // reframe from the current derivatives instead of copying a destination pose.
  motion.retarget(target);
  if(motion.active){
   if(!transition)lastFrame=performance.now();
   transition={to:target};app.classList.add('transitioning');panel.inert=true;requestFrame();
  }
  draw();
 });
});
document.addEventListener('visibilitychange',()=>{
 lastFrame=null;
 if(document.hidden){if(raf)cancelAnimationFrame(raf);raf=0}
 else if(transition)requestFrame();
});
canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();$('#error-banner').textContent='The 3D context was interrupted. Navigation and section content are still available. Reload to restore the arm.';$('#error-banner').hidden=false;app.classList.add('no-webgl');transition=null;cancelAnimationFrame(raf);raf=0;engine=null;finish()});
matchMedia('(prefers-reduced-motion: reduce)').addEventListener('change',e=>{if(e.matches){reduceMotion=true;updateMotion()}});
// Read-only diagnostics used by the included browser regression tests.
Object.defineProperty(window,'__NOIR_TEST__',{get:()=>({section,transitioning:!!transition,camera:{...cam},motion:motion?.snapshot(),panelSection,assetsWarmed,frames:engine?.frames||0,webgl:!!engine,accent,reduceMotion,panelVisible:app.classList.contains('panel-visible'),vertices:window.NOIR_MESH.vertexCount,triangles:window.NOIR_MESH.triangleCount})});
window.__NOIR_PROJECT_POINT__=p=>engine?.project(p);
async function start(){
 cam=pose('home');motion=new NoirMotion.Controller(cam);cam=motion.pose;
 try{const texture=NoirArt.makeTexture(mobile());engine=NoirEngine.create(canvas,texture);updateAccent();draw()}
 catch(error){console.error('NOIR 3D setup:',error);app.classList.add('no-webgl');$('#error-banner').textContent='3D is unavailable in this browser. All sections remain accessible from the menu.';$('#error-banner').hidden=false}
 for(const kind of ['rose','moth','skull','dagger']){
  const image=new Image();image.src=study(kind);
  try{await image.decode()}catch{/* The cached data URL remains usable as a fallback. */}
 }
 assetsWarmed=true;
 updateMotion();app.classList.add('ready');updateNavigation();panelVisibility(false);
 const requested=location.hash.slice(1);if(order.includes(requested)&&requested!=='home')navigate(requested,{history:false,immediate:true});else if(!requested)window.history.replaceState({section:'home'},'','#home');
 status.textContent='Experience ready. Use the menu, scroll, or select a point on the arm.';
}
requestAnimationFrame(()=>setTimeout(start,40));
})();
