/* Minimal WebGL renderer. No CDN, framework, runtime fetch or external dependency. */
window.NoirEngine = (()=>{
  const V={add:(a,b)=>a.map((v,i)=>v+b[i]),sub:(a,b)=>a.map((v,i)=>v-b[i]),mul:(a,s)=>a.map(v=>v*s),dot:(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0),cross:(a,b)=>[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],norm:a=>{let l=Math.hypot(...a);return a.map(v=>v/(l||1))}};
  const tilt=-.19,ct=Math.cos(tilt),st=Math.sin(tilt);
  const world=p=>[p[0]*ct-p[1]*st,p[0]*st+p[1]*ct,p[2]];
  const local=p=>[p[0]*ct+p[1]*st,-p[0]*st+p[1]*ct,p[2]];
  function decode(s,T){const b=atob(s),a=new Uint8Array(b.length);for(let i=0;i<b.length;i++)a[i]=b.charCodeAt(i);return new T(a.buffer)}
  function shader(gl,type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS)){const log=gl.getShaderInfoLog(s);gl.deleteShader(s);throw new Error(log)}return s}
  const vertex=`precision highp float;
    attribute vec3 aPosition;attribute vec3 aNormal;uniform mat4 uModel,uView,uProjection;varying vec3 vNormal,vWorld,vLocal;
    void main(){vec4 w=uModel*vec4(aPosition,1.);vLocal=aPosition;vWorld=w.xyz;vNormal=mat3(uModel)*aNormal;gl_Position=uProjection*uView*w;}`;
  const fragment=`precision highp float;
    varying vec3 vNormal,vWorld,vLocal;uniform sampler2D uTattoo;uniform vec3 uEye,uAccent;uniform float uActiveY,uActive;
    float hash(vec3 p){return fract(sin(dot(p,vec3(127.1,311.7,74.7)))*43758.5453);}
    void main(){
      vec3 n=normalize(vNormal);vec3 v=normalize(uEye-vWorld);
      float cx=mix(.09,-.07,smoothstep(-1.5,1.,vLocal.y));
      float ang=atan(vLocal.x-cx,(vLocal.z+.005)*1.1);
      vec2 uv=vec2(ang/6.2831853+.5,(3.65-vLocal.y)/7.85);
      vec3 ink=texture2D(uTattoo,uv).rgb;
      float pores=hash(floor(vLocal*280.));
      vec3 skin=vec3(.62,.572,.55)*mix(.105,1.02,ink.r);
      skin*=.965+pores*.07;
      vec3 l1=normalize(vec3(-3.8,5.,6.)-vWorld),l2=normalize(vec3(4.,.0,3.)-vWorld);
      float light=.18+max(dot(n,l1),0.)*1.25+max(dot(n,l2),0.)*.22;
      float spec=pow(max(dot(n,normalize(l1+v)),0.),43.)*.115;
      float fres=pow(1.-max(dot(n,v),0.),3.5);
      float rim=max(dot(n,normalize(vec3(4.,2.,-3.))),0.);
      vec3 color=skin*light+vec3(.7,.67,.67)*spec;
      color+=fres*(vec3(.11,.10,.10)+uAccent*rim*.30);
      float selected=exp(-pow((vLocal.y-uActiveY)/.22,2.));
      color+=uAccent*selected*uActive*fres*.075;
      float fade=1.-smoothstep(2.99,3.57,vLocal.y);
      color=pow(max(color,vec3(0.)),vec3(.83));
      gl_FragColor=vec4(color,fade);
    }`;
  function create(canvas,texture){
    const gl=canvas.getContext('webgl',{alpha:true,antialias:true,powerPreference:'high-performance',premultipliedAlpha:false,preserveDrawingBuffer:true});
    if(!gl)throw new Error('WebGL is not available');
    const data=window.NOIR_MESH;
    const raw=decode(data.positions,Int16Array),rn=decode(data.normals,Int16Array);
    const p=new Float32Array(raw.length),n=new Float32Array(rn.length);
    for(let i=0;i<raw.length;i++){p[i]=raw[i]/data.scale;n[i]=rn[i]/32767}
    const idx=decode(data.indices,data.indexBytes===2?Uint16Array:Uint32Array);
    if(data.indexBytes===4&&!gl.getExtension('OES_element_index_uint'))throw new Error('32-bit element arrays unavailable');
    const program=gl.createProgram();gl.attachShader(program,shader(gl,gl.VERTEX_SHADER,vertex));gl.attachShader(program,shader(gl,gl.FRAGMENT_SHADER,fragment));gl.linkProgram(program);if(!gl.getProgramParameter(program,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(program));gl.useProgram(program);
    for(const [name,arr]of [['aPosition',p],['aNormal',n]]){const b=gl.createBuffer();gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.bufferData(gl.ARRAY_BUFFER,arr,gl.STATIC_DRAW);const loc=gl.getAttribLocation(program,name);gl.enableVertexAttribArray(loc);gl.vertexAttribPointer(loc,3,gl.FLOAT,false,0,0)}
    const ib=gl.createBuffer();gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER,ib);gl.bufferData(gl.ELEMENT_ARRAY_BUFFER,idx,gl.STATIC_DRAW);
    const tex=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,tex);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGB,gl.RGB,gl.UNSIGNED_BYTE,texture);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);
    const anis=gl.getExtension('EXT_texture_filter_anisotropic');if(anis)gl.texParameterf(gl.TEXTURE_2D,anis.TEXTURE_MAX_ANISOTROPY_EXT,Math.min(4,gl.getParameter(anis.MAX_TEXTURE_MAX_ANISOTROPY_EXT)));
    const u={};for(const name of ['uModel','uView','uProjection','uEye','uAccent','uTattoo','uActiveY','uActive'])u[name]=gl.getUniformLocation(program,name);
    const model=new Float32Array([ct,st,0,0,-st,ct,0,0,0,0,1,0,0,0,0,1]);gl.uniformMatrix4fv(u.uModel,false,model);gl.uniform1i(u.uTattoo,0);
    gl.enable(gl.DEPTH_TEST);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);gl.disable(gl.CULL_FACE);
    let width=1,height=1,eye=[0,0,12],right=[1,0,0],up=[0,1,0],forward=[0,0,-1],aspect=1,shiftX=0,shiftY=0,tan=Math.tan(43*Math.PI/360),frames=0,accent=[.94,.20,.29];
    function resize(){
      width=Math.max(1,canvas.clientWidth);height=Math.max(1,canvas.clientHeight);
      const dpr=Math.min(devicePixelRatio||1,width<761?1.5:1.7);
      const w=Math.max(1,Math.round(width*dpr)),h=Math.max(1,Math.round(height*dpr));
      // Avoid reallocating the drawing buffer on unchanged resize notifications.
      if(canvas.width!==w)canvas.width=w;if(canvas.height!==h)canvas.height=h;
      gl.viewport(0,0,w,h);aspect=width/height;
    }
    // Uniform buffers are reused instead of allocating typed arrays every frame.
    const viewBuffer=new Float32Array(16),projectionBuffer=new Float32Array(16);
    const eyeBuffer=new Float32Array(3),accentBuffer=new Float32Array(3);
    function render(cam,active){
      if(gl.isContextLost())return;
      gl.clearColor(0,0,0,0);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
      const focus=world([0,cam.y,0]);
      eye=V.add(focus,[Math.sin(cam.theta)*Math.cos(cam.phi)*cam.radius,Math.sin(cam.phi)*cam.radius,Math.cos(cam.theta)*Math.cos(cam.phi)*cam.radius]);
      forward=V.norm(V.sub(focus,eye));right=V.norm(V.cross(forward,[0,1,0]));up=V.cross(right,forward);
      const z=V.mul(forward,-1);const view=viewBuffer;view.set([right[0],up[0],z[0],0,right[1],up[1],z[1],0,right[2],up[2],z[2],0,-V.dot(right,eye),-V.dot(up,eye),-V.dot(z,eye),1]);
      shiftX=cam.sx;shiftY=cam.sy;const f=1/tan,near=.1,far=80;const proj=projectionBuffer;proj.set([f/aspect,0,0,0,0,f,0,0,shiftX,shiftY,(far+near)/(near-far),-1,0,0,2*far*near/(near-far),0]);
      gl.uniformMatrix4fv(u.uView,false,view);gl.uniformMatrix4fv(u.uProjection,false,proj);eyeBuffer.set(eye);accentBuffer.set(accent);gl.uniform3fv(u.uEye,eyeBuffer);gl.uniform3fv(u.uAccent,accentBuffer);gl.uniform1f(u.uActiveY,active?.y||0);gl.uniform1f(u.uActive,active?1:0);gl.drawElements(gl.TRIANGLES,idx.length,data.indexBytes===2?gl.UNSIGNED_SHORT:gl.UNSIGNED_INT,0);frames++;
    }
    function project(pt){const q=V.sub(world(pt),eye),depth=V.dot(q,forward);return{x:((V.dot(q,right)/(depth*tan*aspect)-shiftX)*.5+.5)*width,y:(.5-(V.dot(q,up)/(depth*tan)-shiftY)*.5)*height,depth}}
    // Exact triangle picking on the original mesh, performed only on clicks.
    function pick(x,y){const dx=(x/width*2-1+shiftX)*tan*aspect,dy=(1-y/height*2+shiftY)*tan;
      const ro=local(eye),rd=V.norm(local(V.add(forward,V.add(V.mul(right,dx),V.mul(up,dy)))));
      let nearest=Infinity,point=null;
      for(let i=0;i<idx.length;i+=3){const ia=idx[i]*3,ib=idx[i+1]*3,ic=idx[i+2]*3;const ax=p[ia],ay=p[ia+1],az=p[ia+2];
        const e1x=p[ib]-ax,e1y=p[ib+1]-ay,e1z=p[ib+2]-az,e2x=p[ic]-ax,e2y=p[ic+1]-ay,e2z=p[ic+2]-az;
        const hx=rd[1]*e2z-rd[2]*e2y,hy=rd[2]*e2x-rd[0]*e2z,hz=rd[0]*e2y-rd[1]*e2x,det=e1x*hx+e1y*hy+e1z*hz;
        if(Math.abs(det)<1e-8)continue;const inv=1/det,tx=ro[0]-ax,ty=ro[1]-ay,tz=ro[2]-az,uu=(tx*hx+ty*hy+tz*hz)*inv;if(uu<0||uu>1)continue;
        const qx=ty*e1z-tz*e1y,qy=tz*e1x-tx*e1z,qz=tx*e1y-ty*e1x,vv=(rd[0]*qx+rd[1]*qy+rd[2]*qz)*inv;if(vv<0||uu+vv>1)continue;
        const t=(e2x*qx+e2y*qy+e2z*qz)*inv;if(t>.01&&t<nearest){nearest=t;point=V.add(ro,V.mul(rd,t))}
      }return point;
    }
    resize();return{render,resize,project,pick,setAccent:c=>{accent=c},get frames(){return frames},get size(){return{width,height}},world,get gl(){return gl}};
  }
  return{create,world};
})();
