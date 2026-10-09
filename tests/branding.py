"""Build first: python3 tools/build.py. Then run python3 tests/branding.py."""
from pathlib import Path
import json, os
from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/wizards';OUT.mkdir(parents=True,exist_ok=True)
errors=[];results=[]
with sync_playwright() as p:
 browser=p.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else p.chromium.executable_path),headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
 for w,h in [(320,740),(375,812),(390,844),(760,900),(761,900),(1024,768),(1760,832)]:
  page=browser.new_page(viewport={'width':w,'height':h},reduced_motion='reduce',has_touch=w<=760)
  page.on('pageerror',lambda error:errors.append(str(error)))
  page.set_content((ROOT/'index.html').read_text(encoding='utf-8'));page.wait_for_function('window.__NOIR_TEST__?.assetsWarmed')
  webgl=page.evaluate('window.__NOIR_TEST__.webgl')
  if os.environ.get('REQUIRE_WEBGL')=='1': assert webgl, 'WebGL is required for CI verification'
  assert page.title().startswith('Wizards Tattoos —')
  assert 'NOIR' not in page.locator('body').inner_text() and 'NØIR' not in page.locator('body').inner_text()
  logo=page.locator('.brand-logo').first
  assert logo.evaluate('e=>e.complete&&e.naturalWidth===150&&e.naturalHeight===150')
  nodes=['.brand','.topnav','.book-nav','.menu-toggle'];boxes=[]
  for selector in nodes:
   node=page.locator(selector)
   if node.is_visible():
    box=node.bounding_box();assert box['x']>=-1 and box['x']+box['width']<=w+1,(w,selector,box)
    boxes.append((selector,box))
  boxes.sort(key=lambda item:item[1]['x'])
  for (a,ba),(b,bb) in zip(boxes,boxes[1:]):assert ba['x']+ba['width']<=bb['x']+1,(w,a,b,ba,bb)
  assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),w
  if w in [390,1760]:page.screenshot(path=str(OUT/f'home-{w}.png'))
  page.locator('.section-nav [data-section="artist"]').click();page.wait_for_function('window.__NOIR_TEST__.section==="artist"&&!window.__NOIR_TEST__.transitioning')
  page.locator('.brand').click();page.wait_for_function('window.__NOIR_TEST__.section==="home"')
  if w<=760:
   page.locator('.menu-toggle').click();assert page.locator('.topnav').is_visible()
   page.locator('.topnav [data-section="work"]').click();page.wait_for_function('window.__NOIR_TEST__.section==="work"')
  results.append({'viewport':[w,h],'webgl':webgl,'logo_loaded':True,'header_without_overlap':True,'brand_home_link':True,'mobile_menu':w<=760})
  page.close()
 browser.close()
assert not errors,errors
(OUT/'validation.json').write_text(json.dumps({'checks':results,'page_errors':errors,'physical_device_tested':False},indent=2)+'\n')
print('PASS: branding, embedded logo, header fit and navigation at',len(results),'viewports')
