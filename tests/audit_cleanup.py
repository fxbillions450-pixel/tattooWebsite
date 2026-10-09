"""Four confirmed audit defects and their regression boundaries.
Run after python3 tools/build.py. WIZARDS_BASELINE_HTML enables visual parity;
WIZARDS_AUDIT_URL exercises the real public deployment instead of local HTML.
WIZARDS_REQUIRE_WEBGL=1 fails instead of silently using the UI fallback.
"""
from pathlib import Path
import hashlib, json, os, unittest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
BASELINE = Path(os.environ.get('WIZARDS_BASELINE_HTML', str(ROOT/'baseline.html')))
OUTPUT = ROOT/'evidence'/'audit-cleanup'
ORDER = ['home', 'artist', 'work', 'ritual', 'booking']
GEOMETRY = """() => Object.fromEntries(['#app','.brand','.book-nav','.hero','.bottom-bar','.section-nav','.arrows','#panel'].map(s=>{const r=document.querySelector(s).getBoundingClientRect();return [s,[r.x,r.y,r.width,r.height]]}))"""

class AuditCleanup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        OUTPUT.mkdir(parents=True, exist_ok=True)
        cls.pw = sync_playwright().start()
        cls.browser = cls.pw.chromium.launch(headless=True, executable_path=os.environ.get('CHROMIUM_PATH') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else cls.pw.chromium.executable_path), args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
        cls.webgl = set()
    @classmethod
    def tearDownClass(cls):
        print('Audit browser:', cls.browser.version, 'WebGL:', cls.webgl, flush=True)
        cls.browser.close(); cls.pw.stop()
    def setUp(self):
        self.pages = []; self.errors = []
        self.page = self.fresh()
    def tearDown(self):
        for page in self.pages:
            page.close()
        self.assertEqual(self.errors, [])
    def fresh(self, width=1760, height=832, baseline=False, motion=False):
        page = self.browser.new_page(viewport={'width':width,'height':height}, has_touch=True, reduced_motion='no-preference' if motion else 'reduce')
        self.pages.append(page); page.on('pageerror', lambda e: self.errors.append(str(e)))
        init="(() => {window.__paintedText=[];const original=CanvasRenderingContext2D.prototype.fillText;CanvasRenderingContext2D.prototype.fillText=function(text,...args){window.__paintedText.push(String(text));return original.call(this,text,...args)}})()"
        page.add_init_script(init)
        live = os.environ.get('WIZARDS_AUDIT_URL')
        if live and not baseline:
            page.goto(live, wait_until='domcontentloaded')
        else:
            html = (BASELINE if baseline else ROOT/'index.html').read_text(encoding='utf-8')
            page.evaluate(init)
            page.set_content(html)
        page.wait_for_function('window.__NOIR_TEST__?.assetsWarmed')
        actual = page.evaluate('__NOIR_TEST__.webgl'); self.webgl.add(actual)
        if os.environ.get('WIZARDS_REQUIRE_WEBGL') == '1': self.assertTrue(actual, 'WebGL is required for this run')
        return page
    def go(self, name, page=None):
        page = page or self.page
        page.locator(f'.section-nav [data-section="{name}"]').click()
        page.wait_for_function('!__NOIR_TEST__.transitioning')
        page.wait_for_timeout(40)
        self.assertEqual(page.evaluate('__NOIR_TEST__.section'), name)
    def assert_visible_control(self, page, selector):
        result = page.locator(selector).evaluate("""e => {const r=e.getBoundingClientRect(),hit=document.elementFromPoint(r.x+r.width/2,r.y+r.height/2);return {x:r.x,y:r.y,right:r.right,bottom:r.bottom,width:r.width,height:r.height,hit:hit===e||e.contains(hit),vw:innerWidth,vh:innerHeight}}""")
        self.assertGreater(result['width'],0,selector);self.assertGreater(result['height'],0,selector)
        self.assertGreaterEqual(result['x'],0,selector);self.assertGreaterEqual(result['y'],0,selector)
        self.assertLessEqual(result['right'],result['vw']+1,selector);self.assertLessEqual(result['bottom'],result['vh']+1,selector)
        self.assertTrue(result['hit'], (selector,result))
    def test_01_short_landscape_controls_and_panels(self):
        for width,height in [(844,390),(740,360),(568,320),(1024,450)]:
            with self.subTest(size=(width,height)):
                page=self.fresh(width,height)
                self.assertEqual(page.locator('#app').evaluate('e=>e.clientHeight'),height)
                for name in ORDER:
                    self.go(name,page)
                    for selector in ['.brand','.book-nav','.section-nav [data-section="home"]','.section-nav [data-section="booking"]','#prev','#next']:
                        self.assert_visible_control(page,selector)
                    self.assertEqual(page.evaluate('scrollY+document.body.scrollTop+document.documentElement.scrollTop'),0)
                    if name!='home':
                        self.assert_visible_control(page,'.return-overview')
                        self.assert_visible_control(page,'.panel-close')
                        self.assertGreater(page.locator('#section-content').evaluate('e=>e.clientHeight'),80)
                    page.screenshot(path=str(OUTPUT/f'{name}-{width}x{height}.png'))
                page.locator('.send-button').scroll_into_view_if_needed()
                self.assert_visible_control(page,'.send-button')
                self.assertEqual(page.evaluate('scrollY+document.body.scrollTop+document.documentElement.scrollTop'),0)
    def test_02_landscape_menu_reachable(self):
        page=self.fresh(740,360);page.locator('.menu-toggle').click()
        for name in ['artist','work','ritual']:self.assert_visible_control(page,f'.topnav [data-section="{name}"]')
        page.locator('.topnav [data-section="work"]').click()
        self.assertEqual(page.evaluate('__NOIR_TEST__.section'),'work')
        self.assertEqual(page.locator('.menu-toggle').get_attribute('aria-expanded'),'false')
    def test_03_normal_layout_and_home_pixels_unchanged(self):
        if not BASELINE.exists():self.skipTest('Baseline HTML not supplied; no visual parity claim')
        for width,height in [(320,568),(390,844),(768,1024),(1366,768),(1760,832)]:
            with self.subTest(size=(width,height)):
                snapshots=[]
                # Compare settled pages sequentially. Keeping all ten WebGL
                # contexts alive can exhaust software-GPU resources. Save every
                # image/state so a mismatch is inspectable, never hidden by a tolerance.
                for baseline,label in [(True,'baseline'),(False,'fixed')]:
                    page=self.fresh(width,height,baseline=baseline)
                    try:
                        page.bring_to_front()
                        page.evaluate("""async () => {
                            await document.fonts.ready;
                            await Promise.all([...document.images].filter(i=>i.src).map(i=>i.decode().catch(()=>{})));
                            await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));
                        }""")
                        image=page.screenshot(animations='disabled',path=str(OUTPUT/f'home-parity-{label}-{width}x{height}.png'))
                        state=page.evaluate("""() => ({geometry:("""+GEOMETRY+""")(),diagnostics:window.__NOIR_TEST__,error:document.querySelector('#error-banner').hidden?null:document.querySelector('#error-banner').textContent})""")
                        (OUTPUT/f'home-parity-{label}-{width}x{height}.json').write_text(json.dumps(state,indent=2))
                        if os.environ.get('WIZARDS_REQUIRE_WEBGL')=='1':
                            self.assertTrue(state['diagnostics']['webgl'],'WebGL must survive screenshot capture')
                            self.assertIsNone(state['error'])
                        self.assertFalse(state['diagnostics']['transitioning'])
                        snapshots.append((state['geometry'],hashlib.sha256(image).hexdigest()))
                    finally:
                        page.close();self.pages.remove(page)
                self.assertEqual(snapshots[0],snapshots[1])
    def test_04_browser_back_closes_each_gallery_and_restores_route_focus(self):
        page=self.page
        for kind in ['rose','moth','skull','dagger']:
            self.go('artist');self.go('work');page.locator(f'[data-art="{kind}"]').click()
            self.assertTrue(page.locator('#art-dialog').evaluate('e=>e.open'))
            page.go_back();page.wait_for_function('__NOIR_TEST__.section==="artist"&&!document.querySelector("#art-dialog").open')
            self.assertEqual(page.evaluate('location.hash'),'#artist')
            page.wait_for_timeout(80)
            self.assertEqual(page.evaluate('document.activeElement.dataset.section'),'artist')
            page.go_forward();page.wait_for_function('__NOIR_TEST__.section==="work"')
            self.assertFalse(page.locator('#art-dialog').evaluate('e=>e.open'))
    def test_05_normal_close_and_escape_restore_card_focus(self):
        self.go('work');page=self.page
        for i,kind in enumerate(['rose','moth','skull','dagger']):
            card=page.locator(f'[data-art="{kind}"]');card.click()
            page.wait_for_function('document.querySelector(".dialog-art").complete&&document.querySelector(".dialog-art").naturalWidth===640')
            if i%2:page.keyboard.press('Escape')
            else:page.locator('#close-dialog').click()
            page.wait_for_function('document.activeElement.matches("[data-art]")')
            self.assertTrue(card.evaluate('e=>e===document.activeElement'))
    def test_06_hash_navigation_cannot_keep_stale_gallery(self):
        self.go('work');page=self.page;page.locator('.art-card').first.click()
        page.evaluate('location.hash="#ritual"')
        page.wait_for_function('__NOIR_TEST__.section==="ritual"&&!document.querySelector("#art-dialog").open')
        page.wait_for_timeout(80)
        self.assertEqual(page.evaluate('document.activeElement.dataset.section'),'ritual')
    def test_07_four_generated_footers_use_wizards_brand(self):
        text=self.page.evaluate('window.__paintedText')
        self.assertEqual(text.count('WIZARDS TATTOOS / ORIGINAL STUDY'),4)
        self.assertFalse(any('N Ø I R' in label or 'NØIR' in label or 'NOIR' in label for label in text))
    def test_08_only_gallery_footer_pixels_change(self):
        if not BASELINE.exists():self.skipTest('Baseline HTML not supplied')
        old=self.fresh(baseline=True);page=self.page
        for mobile in [False,True]:
            js='mobile=>NoirArt.makeTexture(mobile).toDataURL()'
            self.assertEqual(old.evaluate(js,mobile),page.evaluate(js,mobile))
        crop="""async kind=>{const image=new Image();image.src=NoirArt.study(kind);await image.decode();const c=document.createElement('canvas');c.width=640;c.height=720;c.getContext('2d').drawImage(image,0,0);return c.toDataURL()}"""
        for kind in ['rose','moth','skull','dagger']:self.assertEqual(old.evaluate(crop,kind),page.evaluate(crop,kind))
    def fill(self,name='QA Test',idea='A botanical sleeve test concept.',email='qa@example.com'):
        page=self.page;page.locator('input[name="name"]').fill(name);page.locator('input[name="email"]').fill(email)
        page.locator('select[name="placement"]').select_option(label='Full sleeve');page.locator('textarea[name="idea"]').fill(idea)
    def submit(self):self.page.locator('.send-button').click()
    def test_09_spaces_only_fields_rejected_and_errors_clear(self):
        self.go('booking');page=self.page;self.fill('    ','            ');self.submit()
        self.assertEqual(page.locator('.form-result').count(),0)
        for name in ['name','idea']:
            field=page.locator(f'#booking-form [name="{name}"]')
            self.assertTrue(field.evaluate('e=>e.validity.customError'));self.assertEqual(field.get_attribute('aria-invalid'),'true')
        self.fill();self.submit();self.assertEqual(page.locator('.form-result').count(),1)
    def test_10_trimmed_minimum_and_unicode_input(self):
        self.go('booking');self.fill('李','  abcdefghi  ');self.submit()
        self.assertEqual(self.page.locator('.form-result').count(),0)
        self.page.locator('textarea').fill('  abcdefghij  ');self.submit()
        self.assertIn('李',self.page.locator('.form-result').inner_text())
        self.assertIn('abcdefghij',self.page.locator('.form-result').inner_text())
    def test_11_valid_draft_survives_edit_resize_and_stays_text(self):
        self.go('booking');name='  Élodie 李  ';idea='  <img src=x onerror=alert(1)>\nBotanical sleeve.  '
        self.fill(name,idea);self.submit();page=self.page
        self.assertEqual(page.locator('.form-result').count(),1);self.assertIn('NOT SENT',page.locator('.form-result').inner_text())
        self.assertEqual(page.locator('.form-result img,.form-result script').count(),0)
        page.get_by_role('button',name='Edit your concept request').click()
        self.assertEqual(page.locator('input[name="name"]').input_value(),name);self.assertEqual(page.locator('textarea').input_value(),idea)
        page.set_viewport_size({'width':740,'height':360});page.wait_for_timeout(150)
        page.set_viewport_size({'width':390,'height':844});page.wait_for_timeout(150)
        self.assertEqual(page.locator('textarea').input_value(),idea)
    def test_12_native_email_and_empty_validation_preserved(self):
        self.go('booking');self.submit();self.assertEqual(self.page.locator('.form-result').count(),0)
        self.fill(email='not-email');self.submit();self.assertEqual(self.page.locator('.form-result').count(),0)
        self.assertTrue(self.page.locator('input[name="email"]').evaluate('e=>e.validity.typeMismatch'))

if __name__=='__main__':unittest.main(verbosity=2)
