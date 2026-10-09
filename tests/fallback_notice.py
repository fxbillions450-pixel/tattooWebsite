"""QA-01: layout, keyboard dismissal, recovery, and unchanged healthy 3D view.
Run python3 tests/fallback_notice.py. Requires Playwright and Pillow.
WIZARDS_BASELINE_HTML supplies pre-fix HTML; WIZARDS_AUDIT_URL tests live.
WIZARDS_REQUIRE_WEBGL=1 fails rather than skips real rendering checks.
WIZARDS_TEST_SET_CONTENT=1 is only for restricted local browser runtimes.
"""
from pathlib import Path
from io import BytesIO
import json, os, unittest
from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASELINE=Path(os.environ.get('WIZARDS_BASELINE_HTML',str(ROOT/'baseline.html')))
OUT=ROOT/'evidence'/'fallback-notice';OUT.mkdir(parents=True,exist_ok=True)
SIZES=[(500,757),(844,390),(740,360),(568,320),(320,568),(390,844),(1180,757),(1760,832)]
DISABLE_GL="""(() => {const get=HTMLCanvasElement.prototype.getContext;
HTMLCanvasElement.prototype.getContext=function(type,...args){
 if(['webgl','webgl2','experimental-webgl'].includes(type))return null;
 return get.call(this,type,...args);
};})()"""
RECT="""e=>{const r=e.getBoundingClientRect();return {left:r.left,top:r.top,right:r.right,bottom:r.bottom,width:r.width,height:r.height}}"""

def intersects(a,b):
 return min(a['right'],b['right'])-max(a['left'],b['left'])>1 and min(a['bottom'],b['bottom'])-max(a['top'],b['top'])>1

class FallbackNotice(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pw=sync_playwright().start()
  exe=os.environ.get('CHROMIUM_PATH') or cls.pw.chromium.executable_path
  cls.browser=cls.pw.chromium.launch(executable_path=exe,headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  cls.evidence=[]
 @classmethod
 def tearDownClass(cls):
  (OUT/'results.json').write_text(json.dumps({'browser':cls.browser.version,'observations':cls.evidence},indent=2))
  cls.browser.close();cls.pw.stop()
 def setUp(self): self.pages=[];self.errors=[]
 def tearDown(self):
  for page in self.pages:page.close()
  self.assertEqual(self.errors,[])
 def fresh(self,size=(500,757),fallback=True,baseline=False):
  p=self.browser.new_page(viewport=dict(zip(['width','height'],size)),reduced_motion='reduce')
  self.pages.append(p);p.on('pageerror',lambda e:self.errors.append(str(e)))
  path=BASELINE if baseline else ROOT/'index.html'
  if os.environ.get('WIZARDS_TEST_SET_CONTENT')=='1':
   if fallback:p.evaluate(DISABLE_GL)
   p.set_content(path.read_text(encoding='utf-8'))
  else:
   if fallback:p.add_init_script(DISABLE_GL)
   p.goto(path.as_uri() if baseline else os.environ.get('WIZARDS_AUDIT_URL',path.as_uri()))
  p.wait_for_function('window.__NOIR_TEST__?.assetsWarmed',timeout=25000)
  p.wait_for_function("getComputedStyle(document.querySelector('.loading')).visibility==='hidden'")
  if fallback:self.assertFalse(p.evaluate('__NOIR_TEST__.webgl'))
  return p
 def go(self,p,section):
  p.locator(f'.section-nav [data-section="{section}"]').click()
  p.wait_for_function("id=>__NOIR_TEST__.section===id&&!__NOIR_TEST__.transitioning",arg=section)
  p.evaluate("() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))")
  if section!='home':p.wait_for_function("getComputedStyle(document.querySelector('#panel')).transform==='matrix(1, 0, 0, 1, 0, 0)' && getComputedStyle(document.querySelector('#panel')).opacity==='1'")
 def rect(self,p,selector):return p.locator(selector).evaluate(RECT)
 def no_overlap(self,p,section,save=False):
  notice=self.rect(p,'#error-banner')
  targets=['.topbar','.bottom-bar','.hero h1','.explore'] if section=='home' else ['.topbar','.return-overview','#panel','#section-content','.bottom-bar']
  for selector in targets:
   r=self.rect(p,selector);self.assertFalse(intersects(notice,r),(section,selector,notice,r))
  # Test control centers, not just DOM visibility (an overlay would intercept).
  controls=['.brand','.book-nav','#next' if section!='booking' else '#prev']
  controls+=['.explore'] if section=='home' else ['.return-overview','.panel-close']
  controls+=['.section-nav [data-section="'+s+'"]' for s in ['home','artist','work','ritual','booking']]
  for selector in controls:
   e=p.locator(selector);r=e.evaluate(RECT)
   self.assertGreaterEqual(r['left'],-1);self.assertLessEqual(r['right'],p.viewport_size['width']+1)
   self.assertGreaterEqual(r['top'],-1);self.assertLessEqual(r['bottom'],p.viewport_size['height']+1)
   self.assertTrue(e.evaluate("e=>{const r=e.getBoundingClientRect();return e.contains(document.elementFromPoint(r.x+r.width/2,r.y+r.height/2))}"),selector)
  self.assertEqual(p.evaluate('document.documentElement.scrollWidth<=innerWidth'),True)
  self.assertEqual(p.evaluate('scrollY'),0)
  if section!='home':
   content=self.rect(p,'#section-content');self.assertGreater(content['height'],30)
   self.assertLessEqual(self.rect(p,'#panel')['bottom'],self.rect(p,'.bottom-bar')['top'])
  if save:p.screenshot(path=str(OUT/f'{section}-{p.viewport_size["width"]}x{p.viewport_size["height"]}.png'))
 def test_01_reproduce_report_on_original_build(self):
  if not BASELINE.exists():self.skipTest('Original build not supplied')
  for size in [(500,757),(844,390)]:
   p=self.fresh(size,baseline=True);self.go(p,'booking');notice=self.rect(p,'#error-banner')
   self.assertTrue(any(intersects(notice,self.rect(p,s)) for s in ['.return-overview','#panel']))
   self.evidence.append({'baseline_overlap_reproduced':size});p.close();self.pages.remove(p)
 def test_02_notice_reserves_space_all_sections_and_sizes(self):
  for size in SIZES:
   p=self.fresh(size)
   for section in ['home','artist','work','ritual','booking']:
    with self.subTest(size=size,section=section):
     self.go(p,section);self.no_overlap(p,section,section in ['home','booking'])
   self.evidence.append({'fallback_layout_pass':size,'sections':5});p.close();self.pages.remove(p)
 def test_03_dismiss_preserves_content_route_and_reclaims_space(self):
  p=self.fresh();self.go(p,'booking');p.locator('[name=name]').fill('QA Test')
  before=self.rect(p,'#panel')['height'];p.locator('#dismiss-error').click()
  self.assertTrue(p.locator('#error-banner').is_hidden());self.assertEqual(p.evaluate('__NOIR_TEST__.section'),'booking')
  self.assertGreater(self.rect(p,'#panel')['height'],before)
  self.assertEqual(p.locator('[name=name]').input_value(),'QA Test')
  p.set_viewport_size({'width':844,'height':390});self.go(p,'work');self.go(p,'artist')
  self.assertTrue(p.locator('#error-banner').is_hidden());self.assertTrue(p.locator('#app').evaluate("e=>e.classList.contains('no-webgl')"))
 def test_04_keyboard_dismiss_restores_visible_focus(self):
  p=self.fresh();self.go(p,'artist');p.locator('#dismiss-error').focus();p.keyboard.press('Enter')
  self.assertTrue(p.locator('#error-banner').is_hidden())
  self.assertEqual(p.evaluate("document.activeElement.getAttribute('data-section')"),'artist')
  self.assertEqual(p.evaluate('scrollY'),0);p.keyboard.press('Tab')
  self.assertEqual(p.evaluate("document.activeElement.getAttribute('data-section')"),'work')
 def test_05_menu_and_panel_scroll_with_notice_visible(self):
  p=self.fresh();p.locator('.menu-toggle').click();p.locator('.topnav [data-section=work]').click()
  self.assertEqual(p.locator('.menu-toggle').get_attribute('aria-expanded'),'false')
  content=p.locator('#section-content');content.hover();p.mouse.wheel(0,120)
  p.wait_for_function("document.querySelector('#section-content').scrollTop>0")
  self.assertEqual(p.evaluate('__NOIR_TEST__.section'),'work')
  self.go(p,'artist');p.locator('#section-content h2').hover();p.mouse.wheel(0,-120)
  p.wait_for_function("__NOIR_TEST__.section==='home'")
 def test_06_gallery_and_demo_form_remain_usable(self):
  p=self.fresh((844,390));self.go(p,'work')
  for kind in ['rose','moth','skull','dagger']:
   p.locator(f'[data-art={kind}]').click();self.assertTrue(p.locator('#art-dialog').evaluate('e=>e.open'))
   p.keyboard.press('Escape');self.assertFalse(p.locator('#art-dialog').evaluate('e=>e.open'))
  self.go(p,'booking');p.locator('[name=name]').fill('QA Test');p.locator('[name=email]').fill('qa@example.com')
  p.locator('[name=placement]').select_option(label='Full sleeve');p.locator('[name=idea]').fill('A botanical sleeve test concept')
  p.locator('.send-button').click();self.assertIn('NOT SENT',p.locator('.form-result').inner_text())
  p.get_by_role('button',name='Edit your concept request').click()
  self.assertEqual(p.locator('[name=name]').input_value(),'QA Test');self.no_overlap(p,'booking')
 def test_07_long_context_loss_message_uses_same_safe_layout(self):
  p=self.fresh((320,568));self.go(p,'booking');p.locator('#dismiss-error').click()
  # Exercise the shared DOM handler independently of a GPU in the fallback tests.
  p.locator('#scene').dispatch_event('webglcontextlost',{'cancelable':True})
  self.assertIn('interrupted',p.locator('#error-message').inner_text());self.no_overlap(p,'booking')
  self.assertEqual(p.locator('#error-message').get_attribute('role'),'status')
 def require_gl(self,p):
  if not p.evaluate('__NOIR_TEST__.webgl'):
   if os.environ.get('WIZARDS_REQUIRE_WEBGL')=='1':self.fail('Required real WebGL context unavailable')
   self.skipTest('No local WebGL; rendered regression must run in WebGL-enabled CI')
 def test_08_healthy_webgl_geometry_and_pixels_unchanged(self):
  if not BASELINE.exists():self.skipTest('Original build not supplied')
  for size in [(390,844),(844,390),(1760,832)]:
   old=self.fresh(size,fallback=False,baseline=True);new=self.fresh(size,fallback=False)
   self.require_gl(old);self.require_gl(new)
   self.assertTrue(new.locator('#error-banner').is_hidden())
   for section in ['home','artist']:
    self.go(old,section);self.go(new,section)
    for sel in ['#scene','.topbar','.bottom-bar']+(['.hero','.explore'] if section=='home' else ['#panel','.return-overview']):
     self.assertEqual(self.rect(old,sel),self.rect(new,sel))
    a=Image.open(BytesIO(old.screenshot(animations='disabled'))).convert('RGB')
    b=Image.open(BytesIO(new.screenshot(animations='disabled'))).convert('RGB')
    diff=ImageChops.difference(a,b);peak=max(hi for lo,hi in diff.getextrema())
    self.assertLessEqual(peak,1,'Healthy 3D appearance changed')
    self.evidence.append({'healthy_visual_parity':size,'section':section,'max_channel_difference':peak})
   for p in [old,new]:p.close();self.pages.remove(p)
 def test_09_real_webgl_context_loss_enters_safe_fallback(self):
  p=self.fresh((500,757),fallback=False);self.require_gl(p);self.go(p,'booking')
  available=p.evaluate("""() => {const gl=document.querySelector('#scene').getContext('webgl');
 const extension=gl.getExtension('WEBGL_lose_context');if(!extension)return false;
 extension.loseContext();return true;}""")
  self.assertTrue(available);p.wait_for_function('!__NOIR_TEST__.webgl')
  self.assertIn('interrupted',p.locator('#error-message').inner_text());self.no_overlap(p,'booking')
  p.locator('#dismiss-error').click();self.go(p,'home');self.go(p,'work')
  self.assertEqual(p.evaluate('__NOIR_TEST__.section'),'work')

if __name__=='__main__':unittest.main(verbosity=2)
