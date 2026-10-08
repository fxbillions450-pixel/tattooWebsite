from pathlib import Path
import hashlib,json
root=Path(__file__).resolve().parents[1]
html=(root/'src'/'shell.html').read_text()
html=html.replace('<!-- STYLE -->','<style>\n'+(root/'src'/'styles.css').read_text()+'\n</style>')
for marker,name in [('MESH','mesh.js'),('ARTWORK','artwork.js'),('ENGINE','engine.js'),('MOTION','motion.js'),('APP','app.js')]:
 html=html.replace('<!-- '+marker+' -->','<script>\n'+(root/'src'/name).read_text()+'\n</script>')
(root/'index.html').write_text(html)
(root/'public'/'index.html').write_text(html)
(root/'build-manifest.json').write_text(json.dumps({'file':'index.html','bytes':len(html.encode()),'sha256':hashlib.sha256(html.encode()).hexdigest(),'networkDependencies':0,'externalAssets':0},indent=2))
print('Built standalone website:',len(html.encode()),'bytes')
