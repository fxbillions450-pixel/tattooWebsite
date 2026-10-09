from pathlib import Path
import base64, hashlib, json

root = Path(__file__).resolve().parents[1]
html = (root / 'src/shell.html').read_text(encoding='utf-8')
styles = (root / 'src/styles.css').read_text(encoding='utf-8') + '\n\n' + (root / 'src/brand.css').read_text(encoding='utf-8')
html = html.replace('<!-- STYLE -->', '<style>\n' + styles + '\n</style>')
logo = (root / 'assets/wizards-instagram-logo.jpg').read_bytes()
if not logo.startswith(b'\xff\xd8\xff'):
    raise ValueError('Brand logo must be the checked-in JPEG image')
html = html.replace('__WIZARDS_LOGO_URI__', 'data:image/jpeg;base64,' + base64.b64encode(logo).decode('ascii'))
for marker, name in [('MESH', 'mesh.js'), ('ARTWORK', 'artwork.js'), ('ENGINE', 'engine.js'), ('MOTION', 'motion.js'), ('SCROLL', 'scroll.js'), ('APP', 'app.js')]:
    html = html.replace('<!-- ' + marker + ' -->', '<script>\n' + (root / 'src' / name).read_text(encoding='utf-8') + '\n</script>')
data = html.encode('utf-8')
(root / 'public').mkdir(exist_ok=True)
(root / 'index.html').write_bytes(data)
(root / 'public/index.html').write_bytes(data)
(root / 'build-manifest.json').write_text(json.dumps({'file': 'index.html', 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'networkDependencies': 0, 'externalAssets': 0}, indent=2), encoding='utf-8')
print('Built standalone website:', len(data), 'bytes')
