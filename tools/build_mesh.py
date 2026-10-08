"""Create an original, smoothly blended anatomical blockout. No external assets."""
from pathlib import Path
import numpy as np
from scipy.interpolate import PchipInterpolator
from skimage.measure import marching_cubes
import base64, json

ROOT = Path(__file__).resolve().parents[1]
step = .032
xs=np.arange(-1.1,1.31,step,dtype=np.float32)
ys=np.arange(-4.25,3.82,step,dtype=np.float32)
zs=np.arange(-.82,.87,step,dtype=np.float32)
X,Y,Z=np.meshgrid(xs,ys,zs,indexing='ij')

def ell(c,r):
    q0=(X-c[0])/r[0]; q1=(Y-c[1])/r[1]; q2=(Z-c[2])/r[2]
    k0=np.sqrt(q0*q0+q1*q1+q2*q2)
    k1=np.sqrt((q0/r[0])**2+(q1/r[1])**2+(q2/r[2])**2)
    return k0*(k0-1)/np.maximum(k1,1e-8)

def union(a,b,k=.10):
    h=np.maximum(k-np.abs(a-b),0)/k
    return np.minimum(a,b)-h*h*k*.25

def capsule(a,b,r0,r1):
    pa=[X-a[0],Y-a[1],Z-a[2]]; ba=np.array(b)-a
    t=np.clip(sum(pa[i]*ba[i] for i in range(3))/np.dot(ba,ba),0,1)
    d=np.sqrt(sum((pa[i]-ba[i]*t)**2 for i in range(3)))
    return d-(r0+(r1-r0)*t)

yp=np.array([-2.12,-1.8,-1.3,-.6,.05,.6,1.2,2.0,2.7,3.22,3.56])
rp=np.array([.235,.255,.29,.385,.448,.367,.424,.528,.575,.47,.08])
xp=np.array([.075,.09,.095,.05,-.015,-.065,-.10,-.1,-.06,.015,.03])
zp=np.array([.025,.015,.01,0,-.025,-.03,-.025,0,.015,.025,.025])
r=PchipInterpolator(yp,rp)(np.clip(Y,yp[0],yp[-1]))
cx=PchipInterpolator(yp,xp)(np.clip(Y,yp[0],yp[-1]))
cz=PchipInterpolator(yp,zp)(np.clip(Y,yp[0],yp[-1]))
# Forearm is flatter than upper arm; subtle asymmetric muscle planes.
rz=r*(.84+.09*np.clip((Y-.5)/2,0,1))
theta=np.arctan2(X-cx,Z-cz)
mod=.016*np.sin(theta*3+Y*.4)*np.exp(-((Y-.3)/2.5)**2)
d=(np.sqrt(((X-cx)/r)**2+((Z-cz)/rz)**2)-1)*r+mod
d=np.maximum(d,np.maximum(-2.20-Y,Y-3.55))
# Continuous wrist, metacarpals and palm, palm facing away from viewer.
d=union(d,ell((.07,-2.26,.015),(.30,.43,.22)),.15)
d=union(d,ell((.005,-2.55,.015),(.415,.49,.19)),.13)
# Dorsal metacarpal ridges.
for xx in [-.265,-.072,.128,.32]:
    d=union(d,capsule([xx*.75,-2.31,.06],[xx,-2.86,.035],.108,.104),.085)
# Four relaxed fingers, slightly curled towards the palm.
fingers=[(-.30,-2.78,.79,.102),(-.088,-2.85,1.07,.115),(.135,-2.84,1.00,.111),(.338,-2.77,.84,.098)]
for i,(xx,yy,length,rr) in enumerate(fingers):
    p0=[xx,yy,.01]; p1=[xx+(i-1.3)*.019,yy-length*.45,-.015]
    p2=[p1[0]+(i-1.3)*.012,yy-length*.78,-.13]
    p3=[p2[0],yy-length,-.245]
    d=union(d,capsule(p0,p1,rr,rr*.92),.075)
    d=union(d,capsule(p1,p2,rr*.92,rr*.80),.048)
    d=union(d,capsule(p2,p3,rr*.80,rr*.68),.038)
# Opposed thumb and thenar mass.
d=union(d,ell((.315,-2.30,-.04),(.255,.34,.215)),.12)
thumb=[[.38,-2.29,-.005],[.63,-2.53,-.085],[.75,-2.81,-.21],[.74,-3.02,-.29]]
for j in range(3): d=union(d,capsule(thumb[j],thumb[j+1],.135-j*.016,.122-j*.017),.07)
verts,faces,normals,_=marching_cubes(d,level=0,spacing=(step,step,step),gradient_direction='ascent')
verts+=np.array([xs[0],ys[0],zs[0]])
# Use area-weighted geometric normals, smooth from the sampled distance field.
# skimage normals point into the solid for this sign convention, so invert them.
normals=-normals
# Camera-facing normals checked against a known outer point.
sel=np.argmax(verts[:,2]);
if normals[sel,2]<0: normals=-normals
# Quantize vertex payload to reduce the standalone file; normalized positions decode exactly enough.
scale=6000
p=(np.round(verts*scale)).astype('<i2')
n=(np.clip(normals,-1,1)*32767).astype('<i2')
f=faces.astype('<u2') if len(verts)<65536 else faces.astype('<u4')
mesh={"positions":base64.b64encode(p.tobytes()).decode(),"normals":base64.b64encode(n.tobytes()).decode(),"indices":base64.b64encode(f.tobytes()).decode(),"indexBytes":f.dtype.itemsize,"scale":scale,"vertexCount":len(verts),"triangleCount":len(faces)}
(ROOT/'src'/'mesh.js').write_text('window.NOIR_MESH='+json.dumps(mesh,separators=(',',':'))+';\n')
(ROOT/'tools'/'mesh-info.json').write_text(json.dumps({k:v for k,v in mesh.items() if k not in ['positions','normals','indices']},indent=2))
print('Original model:', len(verts), 'vertices;',len(faces),'triangles;', (ROOT/'src'/'mesh.js').stat().st_size,'bytes')
