from pathlib import Path
import re, hashlib
r=Path(__file__).resolve().parents[1]
expected={'src/app.js':'f2676394c720f533c796fd897e468e181c02291e1c2d22e91afff48f14de41f6','src/engine.js':'45ee0cda0d6d14cfee494f368458c3f97c136b8f687ed11c3c33b79613c826c7','src/shell.html':'8a757df8741d364f8f6720fe992a86876ffe348846a1047df398c0f6937f54ef','src/styles.css':'4e787b303ed98a4a2c9bfeefada238e6dbbbfffdcfd639e64b8018ab8247b530'}
for name,digest in expected.items():
 assert hashlib.sha256((r/name).read_bytes()).hexdigest()==digest, 'Source changed: '+name
p=r/'src/shell.html';s=p.read_text()
s,n=re.subn(r'<div class="color-settings".*?</div><button class="motion-btn".*?</button>', '', s,flags=re.S);assert n==1
p.write_text(s)
p=r/'src/styles.css';s=p.read_text()
s,n=re.subn(r'\.color-settings\{.*?(?=\.arrows\{)', '',s);assert n==1
s,n=re.subn(r'\.color-btn\{width:24px;height:30px\}\.motion-btn\{[^}]*\}', '',s);assert n==1
p.write_text(s)
p=r/'src/app.js';s=p.read_text()
s=s.replace("const savedColor=store.get('noir-accent');if(savedColor==='purple')accent='purple';\nif(store.get('noir-reduced-motion')==='true')reduceMotion=true;\n",'')
s=re.sub(r"const store=\{get\(k\).*?\n",'',s)
s=s.replace("const cachedArt={};", "const cachedArt={};\nlet panelAnchor=null;\nconst connectorPath=$('#connector path');")
s=s.replace("scroll.innerHTML=markup(section);scroll.scrollTop=0;", "scroll.innerHTML=markup(section);scroll.scrollTop=0;panelAnchor=null;")
s=s.replace("app.classList.toggle('panel-visible',show);\n panel.inert=!show||!!transition;\n panel.setAttribute('aria-hidden',show?'false':'true');", "if(wasVisible!==show){app.classList.toggle('panel-visible',show);panel.setAttribute('aria-hidden',show?'false':'true');}\n const inert=!show||!!transition;if(panel.inert!==inert)panel.inert=inert;")
a=s.index('function updateOverlay(){');b=s.index('\nfunction draw()',a)
s=s[:a]+'''function updateOverlay(){
 if(!engine)return;
 const isMobile=mobile(),showPanel=section!=='home'&&app.classList.contains('panel-visible');
 // Hidden markers need neither projection nor DOM writes while the camera travels.
 // Read the panel's untransformed destination once per mount/resize, not per frame.
 if(showPanel&&!isMobile&&!panelAnchor)panelAnchor={x:panel.offsetLeft,y:panel.offsetTop+25};
 if(!transition){
  const offset=isMobile?[-22,-22]:[-12,-23];
  for(const {el,point} of hotspotNodes){
   if(section!=='home'&&(isMobile||el.dataset.section!==section))continue;
   const p=engine.project(point);
   const transform=`translate3d(${p.x+offset[0]}px,${p.y+offset[1]}px,0)`;
   const visibility=p.depth<.1||p.x<15||p.x>innerWidth-18||p.y<90||p.y>innerHeight-95?'hidden':'visible';
   if(el.style.transform!==transform)el.style.transform=transform;
   if(el.style.visibility!==visibility)el.style.visibility=visibility;
  }
 }
 if(showPanel&&!isMobile&&panelAnchor){
  const p=engine.project(surface(sections[section])),{x:endX,y:endY}=panelAnchor;
  const path=`M ${p.x} ${p.y} L ${p.x+35} ${p.y} L ${endX-25} ${endY} L ${endX} ${endY}`;
  if(connectorPath.getAttribute('d')!==path)connectorPath.setAttribute('d',path);
 }
}'''+s[b:]
a=s.index('function updateAccent()');b=s.index("document.addEventListener('click'",a)
s=s[:a]+'''function updateMotion(){
 document.body.classList.toggle('reduce-motion',reduceMotion);
 if(reduceMotion&&transition){cam=motion.reset(pose(section));transition=null;cancelAnimationFrame(raf);raf=0;lastFrame=null;draw();finish()}
}
'''+s[b:]
s=re.sub(r" const color=event.target.closest\('\[data-color\]'\);.*?\n",'',s)
s=re.sub(r"\$\('\.motion-btn'\)\.addEventListener\('click'.*?\n",'',s)
s=s.replace('resizeFrame=0;if(!motion)return;', 'resizeFrame=0;panelAnchor=null;if(!motion)return;')
s=s.replace('else if(transition)requestFrame();', 'else if(transition)requestFrame();else draw();')
s=s.replace("e=>{if(e.matches){reduceMotion=true;updateMotion()}}", "e=>{reduceMotion=e.matches;updateMotion()}")
s=s.replace('engine=NoirEngine.create(canvas,texture);updateAccent();draw()', 'engine=NoirEngine.create(canvas,texture);draw()')
s=s.replace("triangles:window.NOIR_MESH.triangleCount", "triangles:window.NOIR_MESH.triangleCount,renderInfo:engine?.diagnostics")
p.write_text(s)
p=r/'src/engine.js';s=p.read_text().replace('const fragment=`','const originalFragment=`',1)
a=s.index('  function create(canvas,texture)')
skin='''  // A compact, repeatable material tile: RG = subtle normal detail, B = tone.
  // Generated once; mipmaps filter pores instead of per-fragment random shimmer.
  function skinTile(gl){
    const size=256,bytes=new Uint8Array(size*size*4);let seed=72831;
    const rand=()=>{seed=(Math.imul(seed,1664525)+1013904223)>>>0;return seed/4294967296};
    for(let y=0;y<size;y++)for(let x=0;x<size;x++){
      const i=(y*size+x)*4,grain=rand();
      bytes[i]=116+Math.floor(rand()*24);bytes[i+1]=116+Math.floor(rand()*24);
      bytes[i+2]=Math.round(128+16*Math.sin(x*Math.PI/32)*Math.cos(y*Math.PI/64)+(grain-.5)*34);
      bytes[i+3]=255;
    }
    const tex=gl.createTexture();gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,tex);
    gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,size,size,0,gl.RGBA,gl.UNSIGNED_BYTE,bytes);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.REPEAT);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.REPEAT);
    gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
    gl.generateMipmap(gl.TEXTURE_2D);gl.activeTexture(gl.TEXTURE0);return tex;
  }
  const skinFragment=`precision highp float;
    varying vec3 vNormal,vWorld,vLocal;uniform sampler2D uTattoo,uSkin;
    uniform vec3 uEye,uAccent;uniform float uActiveY,uActive;
    void main(){
      vec3 n=normalize(vNormal),v=normalize(uEye-vWorld);
      float cx=mix(.09,-.07,smoothstep(-1.5,1.,vLocal.y));
      float ang=atan(vLocal.x-cx,(vLocal.z+.005)*1.1);
      vec2 uv=vec2(ang/6.2831853+.5,(3.65-vLocal.y)/7.85);
      vec3 ink=texture2D(uTattoo,uv).rgb;
      vec3 detail=texture2D(uSkin,uv*vec2(9.,18.)).rgb;
      vec3 tangent=normalize(vec3(n.z,0.,-n.x)+vec3(.0001,0.,0.));
      n=normalize(n+.14*(tangent*(detail.r-.5)+cross(n,tangent)*(detail.g-.5)));
      // Original artwork remains intact; pigment modulates a warm skin base.
      float pigment=pow(clamp((ink.r-.04)/.76,0.,1.),.82);
      vec3 skin=mix(vec3(.026,.022,.022),vec3(.70,.49,.39),pigment);
      skin*=.96+detail.b*.08;
      vec3 l1=normalize(vec3(-3.8,5.,6.)-vWorld),l2=normalize(vec3(4.,0.,3.)-vWorld);
      float light=.20+max(dot(n,l1),0.)*1.15+max(dot(n,l2),0.)*.20;
      float spec=pow(max(dot(n,normalize(l1+v)),0.),32.)*.09;
      float fres=pow(1.-max(dot(n,v),0.),3.5),rim=max(dot(n,normalize(vec3(4.,2.,-3.))),0.);
      vec3 color=skin*light+vec3(.78,.70,.65)*spec;
      color+=fres*(vec3(.11,.095,.085)+uAccent*rim*.30);
      float dy=(vLocal.y-uActiveY)/.22;
      color+=uAccent*exp(-dy*dy)*uActive*fres*.075;
      gl_FragColor=vec4(pow(max(color,vec3(0.)),vec3(.83)),1.-smoothstep(2.99,3.57,vLocal.y));
    }`;
'''
s=s[:a]+skin+s[a:]
s=s.replace('preserveDrawingBuffer:true','preserveDrawingBuffer:false')
s=s.replace("const data=window.NOIR_MESH;", "const data=window.NOIR_MESH;\n    const material=new URLSearchParams(location.search).get('arm')==='original'?'original':'skin';")
s=s.replace('shader(gl,gl.FRAGMENT_SHADER,fragment)', "shader(gl,gl.FRAGMENT_SHADER,material==='original'?originalFragment:skinFragment)")
s=s.replace("'uModel','uView','uProjection','uEye','uAccent','uTattoo','uActiveY','uActive'", "'uModel','uView','uProjection','uEye','uAccent','uTattoo','uSkin','uActiveY','uActive'")
s=s.replace('gl.uniform1i(u.uTattoo,0);', "gl.uniform1i(u.uTattoo,0);\n    if(material==='skin'){skinTile(gl);gl.uniform1i(u.uSkin,1)}")
s=s.replace('accent=[.94,.20,.29]', 'accent=[.937,.20,.286]')
s=s.replace("const dpr=Math.min(devicePixelRatio||1,width<761?1.5:1.7);", "// Fixed budget, never resized mid-flight. DOM text keeps native resolution.\n      const dpr=width<761?Math.min(devicePixelRatio||1,1.5):Math.min(devicePixelRatio||1,1.5,Math.sqrt(4500000/(width*height)));")
a=s.index('      const focus=world([0,cam.y,0]);');b=s.index('      gl.uniformMatrix4fv(u.uView',a)
s=s[:a]+'''      const fx=-cam.y*st,fy=cam.y*ct,sinT=Math.sin(cam.theta),cosT=Math.cos(cam.theta),sinP=Math.sin(cam.phi),cosP=Math.cos(cam.phi);
      eye[0]=fx+sinT*cosP*cam.radius;eye[1]=fy+sinP*cam.radius;eye[2]=cosT*cosP*cam.radius;
      forward[0]=-sinT*cosP;forward[1]=-sinP;forward[2]=-cosT*cosP;
      right[0]=cosT;right[1]=0;right[2]=-sinT;
      up[0]=-sinT*sinP;up[1]=cosP;up[2]=-cosT*sinP;
      const view=viewBuffer;
      view[0]=right[0];view[1]=up[0];view[2]=-forward[0];view[3]=0;
      view[4]=0;view[5]=up[1];view[6]=-forward[1];view[7]=0;
      view[8]=right[2];view[9]=up[2];view[10]=-forward[2];view[11]=0;
      view[12]=-V.dot(right,eye);view[13]=-V.dot(up,eye);view[14]=V.dot(forward,eye);view[15]=1;
      shiftX=cam.sx;shiftY=cam.sy;const f=1/tan,near=.1,far=80,proj=projectionBuffer;
      proj[0]=f/aspect;proj[5]=f;proj[8]=shiftX;proj[9]=shiftY;proj[10]=(far+near)/(near-far);proj[11]=-1;proj[14]=2*far*near/(near-far);
'''+s[b:]
s=s.replace('world,get gl(){return gl}',"world,get diagnostics(){return{material,bufferWidth:canvas.width,bufferHeight:canvas.height,pixelRatio:canvas.width/width,preserved:false,drawCallsPerFrame:1,skinTextureSize:material==='skin'?256:0}},get gl(){return gl}")
p.write_text(s)
p=r/'tests/browser_scroll.py';s=p.read_text().replace("self.page.locator('.motion-btn').click()", "self.page.emulate_media(reduced_motion='reduce');self.page.wait_for_function('window.__NOIR_TEST__.reduceMotion')");p.write_text(s)
