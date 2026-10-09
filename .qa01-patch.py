from pathlib import Path
root=Path(__file__).parent
p=root/'src/shell.html';s=p.read_text()
old='<div class="error-banner" id="error-banner" hidden></div>'
assert s.count(old)==1
s=s.replace(old,'')
notice='''<div class="error-banner" id="error-banner" role="region" aria-label="3D availability notice" hidden><p id="error-message" role="status"></p><button id="dismiss-error" type="button" aria-label="Dismiss 3D notice"><span aria-hidden="true">×</span></button></div>'''
s=s.replace('</header>\n<main','</header>\n'+notice+'\n<main',1);p.write_text(s)
p=root/'src/app.js';s=p.read_text()
anchor="canvas.addEventListener('webglcontextlost',e=>"
assert s.count(anchor)==1
helper='''// Fallback notices occupy a layout row, never an overlay. Dismissal is local
// to this page; it does not hide future context-loss messages or change motion.
function showFallbackNotice(message){
 app.classList.add('no-webgl');
 $('#error-message').textContent=message;
 $('#error-banner').hidden=false;
}
$('#dismiss-error').addEventListener('click',()=>{
 const notice=$('#error-banner'),hadFocus=notice.contains(document.activeElement);
 notice.hidden=true;
 if(hadFocus)document.querySelector('.section-nav [data-section="'+section+'"]')?.focus({preventScroll:true});
});
'''
s=s.replace(anchor,helper+anchor,1)
s=s.replace("$('#error-banner').textContent='The 3D context was interrupted. Navigation and section content are still available. Reload to restore the arm.';$('#error-banner').hidden=false;app.classList.add('no-webgl');", "showFallbackNotice('The 3D context was interrupted. Navigation and section content are still available. Reload to restore the arm.');")
s=s.replace("app.classList.add('no-webgl');$('#error-banner').textContent='3D is unavailable in this browser. All sections remain accessible from the menu.';$('#error-banner').hidden=false", "showFallbackNotice('3D is unavailable in this browser. All sections remain accessible from the menu.')")
assert "$('#error-banner').textContent" not in s;p.write_text(s)
p=root/'src/styles.css';s=p.read_text()
s+='''

/* QA-01: no-WebGL status gets its own intrinsic-height row. These rules
   never apply to the approved 3D composition or its scroll/camera hot path. */
#app.no-webgl{display:grid;grid-template-columns:minmax(0,1fr);grid-template-rows:auto auto minmax(0,1fr) auto;grid-template-areas:"header" "notice" "content" "footer";min-height:0}
.no-webgl .topbar{position:relative;grid-area:header}
.no-webgl .error-banner{grid-area:notice;position:relative;inset:auto;transform:none;max-width:none;margin:0 max(5%,env(safe-area-inset-right)) 8px max(5%,env(safe-area-inset-left));padding:8px 8px 8px 14px;display:flex;align-items:center;gap:12px;text-align:left}
.no-webgl .error-banner[hidden]{display:none}
.no-webgl #error-message{margin:0;min-width:0;flex:1;line-height:1.5;overflow-wrap:anywhere}
.no-webgl #dismiss-error{flex:0 0 44px;width:44px;height:44px;padding:0;font-size:22px;border:1px solid var(--line);border-radius:2px}
.no-webgl #dismiss-error:hover{border-color:var(--accent)}
.no-webgl #dismiss-error:focus-visible{outline-offset:2px}
.no-webgl #main-content{grid-area:content;position:relative;min-width:0;min-height:0}
.no-webgl .return-overview{top:0;min-height:40px}
.no-webgl #panel{top:44px;bottom:8px;max-height:none}
.no-webgl .panel-shell{height:100%;max-height:100%;min-height:0;display:flex;flex-direction:column}
.no-webgl .panel-top{flex:0 0 auto}
.no-webgl .panel-scroll{flex:1;min-height:0;max-height:none}
.no-webgl .hero{top:8px}
.no-webgl .hero h1{font-size:clamp(54px,10svh,110px)}
.no-webgl .model-meta,.no-webgl .location-caption,.no-webgl #connector,.no-webgl .scroll-cue{display:none}
.no-webgl .bottom-bar{grid-area:footer;position:relative;left:auto;right:auto;bottom:auto;margin:0 max(5%,env(safe-area-inset-right)) max(8px,env(safe-area-inset-bottom)) max(5%,env(safe-area-inset-left))}
@media(max-height:480px){
 .no-webgl .hero h1{font-size:clamp(24px,8svh,40px);margin:8px 0}
 .no-webgl .hero .intro{display:none}
}
'''
p.write_text(s)
