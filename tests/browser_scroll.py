"""Run: python tests/browser_scroll.py [path-to-index.html]
Requires Playwright and Chromium. Uses set_content, so no server/network is needed.
Real mouse-wheel/native scrolling and CDP touch input; no input-controller mocks.
Timing-sensitive strokes use CDP capture timestamps so software rendering or
protocol round trips cannot silently turn one stroke into several fresh gestures.
"""
from pathlib import Path
import json, os, sys, unittest
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
HTML = Path(sys.argv.pop(1)) if len(sys.argv) > 1 else ROOT / 'index.html'

class ScrollBrowserTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.pw = sync_playwright().start()
  cls.browser = cls.pw.chromium.launch(executable_path=os.environ.get('CHROMIUM_PATH') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else cls.pw.chromium.executable_path), headless=True, args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  cls.webgl = set()
 @classmethod
 def tearDownClass(cls):
  print('Actual WebGL availability in browser runs:', cls.webgl)
  cls.browser.close(); cls.pw.stop()
 def setUp(self):
  self.page = self.browser.new_page(viewport={'width':1760,'height':832}, has_touch=True, reduced_motion='reduce')
  self.errors=[];self.page.on('pageerror',lambda e:self.errors.append(str(e)))
  self.page.set_content(HTML.read_text(encoding='utf-8'))
  self.page.wait_for_function('window.__NOIR_TEST__?.assetsWarmed')
  self.webgl.add(self.page.evaluate('window.__NOIR_TEST__.webgl'))
 def tearDown(self):
  self.page.close();self.assertEqual(self.errors,[])
 def section(self):return self.page.evaluate('window.__NOIR_TEST__.section')
 def go(self,section):
  self.page.locator(f'.section-nav [data-section={section}]').click()
  self.page.wait_for_function('!window.__NOIR_TEST__.transitioning');self.page.wait_for_timeout(250)
 def wheel(self,delta,selector=None,pause=230):
  if selector:self.page.locator(selector).hover()
  else:self.page.mouse.move(850,420)
  self.page.mouse.wheel(0,delta);self.page.wait_for_timeout(pause)
 def native_stroke(self,events,selector=None):
  """Replay trusted native wheel events with specified (offset_ms, delta) pairs.

  Preserve capture cadence even if the software GPU delays event delivery.
  This does not patch the clock, router, camera, DOM scrollTop or event handler.
  """
  if selector:
   self.page.locator(selector).hover()
   box=self.page.locator(selector).bounding_box();x=box['x']+box['width']/2;y=box['y']+min(70,box['height']/2)
  else:x,y=850,420;self.page.mouse.move(x,y)
  self.page.evaluate("""() => {
   window.__wheelEvidence=[];
   window.__recordWheel=e=>window.__wheelEvidence.push({stamp:e.timeStamp,delivered:performance.now(),delta:e.deltaY,trusted:e.isTrusted});
   window.addEventListener('wheel',window.__recordWheel,{capture:true,passive:true});
  }""")
  origin,base=self.page.evaluate('[performance.timeOrigin,performance.now()]')
  cdp=self.page.context.new_cdp_session(self.page);previous=0
  try:
   for offset,delta in events:
    self.page.wait_for_timeout(max(0,offset-previous));previous=offset
    cdp.send('Input.dispatchMouseEvent',{'type':'mouseWheel','x':x,'y':y,'deltaX':0,'deltaY':delta,'timestamp':(origin+base+offset)/1000})
   self.page.wait_for_function('window.__wheelEvidence.length >= '+str(len(events)))
   evidence=self.page.evaluate('window.__wheelEvidence')
   self.assertEqual(len(evidence),len(events))
   for record,(offset,delta) in zip(evidence,events):
    self.assertTrue(record['trusted']);self.assertAlmostEqual(record['delta'],delta,places=4)
    self.assertAlmostEqual(record['stamp']-evidence[0]['stamp'],offset-events[0][0],delta=2)
   print('Trusted wheel capture/delivery evidence:',json.dumps(evidence),flush=True)
  finally:
   self.page.evaluate("window.removeEventListener('wheel',window.__recordWheel,true)")
   cdp.detach()
 def top(self,value=0):self.page.locator('#section-content').evaluate('(e,y)=>e.scrollTop=y',value)
 def native_top(self):return self.page.locator('#section-content').evaluate('e=>e.scrollTop')
 def touch(self,selector,dy):
  box=self.page.locator(selector).bounding_box();x=box['x']+box['width']/2;y=box['y']+min(80,box['height']/3)
  cdp=self.page.context.new_cdp_session(self.page)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':x,'y':y}]})
  for i in range(1,7):
   cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':x,'y':y+dy*i/6}]});self.page.wait_for_timeout(25)
  cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]});self.page.wait_for_timeout(250);cdp.detach()
 def test_01_artist_panel_top_returns_home(self):
  self.go('artist');self.wheel(-40,'#section-content h2');self.assertEqual(self.section(),'home')
 def test_02_forward_and_reverse_all_sections(self):
  for name in ['artist','work','ritual','booking']:
   self.wheel(120);self.assertEqual(self.section(),name)
  for name in ['ritual','work','artist','home']:
   self.wheel(-120);self.assertEqual(self.section(),name)
 def test_03_header_is_not_a_dead_zone(self):
  self.go('artist');self.wheel(-120,'.topnav');self.assertEqual(self.section(),'home')
 def test_04_settings_are_not_a_dead_zone(self):
  self.go('artist');self.wheel(-120,'.settings');self.assertEqual(self.section(),'home')
 def test_05_small_slow_notches_accumulate(self):
  self.go('artist');self.native_stroke([(0,-20),(240,-20)]);self.assertEqual(self.section(),'home')
 def test_06_native_content_reading_keeps_section(self):
  self.go('work');self.top(100);self.wheel(70,'#section-content');self.assertEqual(self.section(),'work');self.assertGreater(self.native_top(),100)
  self.wheel(-60,'#section-content');self.assertEqual(self.section(),'work')
 def test_07_fresh_scroll_at_panel_bottom_advances(self):
  self.go('work');self.top(100000);self.wheel(120,'#section-content');self.assertEqual(self.section(),'ritual')
 def test_08_reading_does_not_leak_at_a_boundary(self):
  self.go('artist');self.top(50)
  self.native_stroke([(0,-100),(60,-70),(110,-40)],'#section-content')
  self.assertEqual(self.section(),'artist')
  self.page.wait_for_timeout(250);self.wheel(-40,'#section-content');self.assertEqual(self.section(),'home')
 def test_09_trackpad_tail_does_not_skip(self):
  self.native_stroke([(i*18,120*(.88**i)) for i in range(45)])
  self.assertEqual(self.section(),'artist')
 def test_10_continued_deliberate_scroll_does_not_lock(self):
  self.page.mouse.move(850,420)
  for i in range(16):self.page.mouse.wheel(0,120);self.page.wait_for_timeout(100)
  self.assertIn(self.section(),['ritual','booking'])
 def test_11_controls_modal_zoom_and_horizontal_are_preserved(self):
  self.go('booking');self.wheel(-120,'input[name=name]');self.assertEqual(self.section(),'booking')
  self.page.locator('#app').dispatch_event('wheel',{'deltaY':-120,'ctrlKey':True,'bubbles':True,'cancelable':True});self.assertEqual(self.section(),'booking')
  self.page.locator('#app').dispatch_event('wheel',{'deltaY':-20,'deltaX':120,'bubbles':True,'cancelable':True});self.assertEqual(self.section(),'booking')
  self.go('work');self.page.locator('.art-card').first.click();self.page.mouse.wheel(0,-160);self.page.wait_for_timeout(100);self.assertEqual(self.section(),'work')
 def test_12_click_then_scroll_has_no_stale_gesture(self):
  self.wheel(120,pause=40);self.go('work');self.wheel(-120);self.assertEqual(self.section(),'artist')
 def test_13_line_mode_is_supported(self):
  self.go('artist');self.page.locator('#section-content').dispatch_event('wheel',{'deltaY':-3,'deltaX':0,'deltaMode':1,'bubbles':True,'cancelable':True});self.assertEqual(self.section(),'home')
 def test_14_mobile_touch_panel_top_returns_home(self):
  self.page.set_viewport_size({'width':390,'height':844});self.go('artist');self.top(0);self.touch('#section-content',90);self.assertEqual(self.section(),'home')
 def test_15_mobile_native_reading_stays_in_panel(self):
  self.page.set_viewport_size({'width':390,'height':844});self.go('work');self.top(150);self.touch('#section-content',-70);self.assertEqual(self.section(),'work');self.assertGreater(self.native_top(),150)
 def test_16_mobile_menu_blocks_navigation(self):
  self.page.set_viewport_size({'width':390,'height':844});self.go('artist');self.page.locator('.menu-toggle').click();self.page.locator('#app').dispatch_event('wheel',{'deltaY':-120,'bubbles':True,'cancelable':True});self.assertEqual(self.section(),'artist')
 def test_17_touch_swipe_only_advances_once(self):
  self.page.set_viewport_size({'width':390,'height':844});self.touch('#home-content',-100);self.assertEqual(self.section(),'artist')
 def test_18_keyboard_navigation_still_works(self):
  self.page.keyboard.press('PageDown');self.assertEqual(self.section(),'artist');self.page.keyboard.press('PageUp');self.assertEqual(self.section(),'home')

 def motion_page(self):
  if not self.page.evaluate('window.__NOIR_TEST__.webgl'):self.skipTest('WebGL not available in this browser runtime')
  self.page.close()
  self.page = self.browser.new_page(viewport={'width':1760,'height':832}, has_touch=True, reduced_motion='no-preference')
  self.page.on('pageerror',lambda e:self.errors.append(str(e)))
  self.page.set_content(HTML.read_text(encoding='utf-8'))
  self.page.wait_for_function('window.__NOIR_TEST__?.assetsWarmed')
  self.assertFalse(self.page.evaluate('window.__NOIR_TEST__.reduceMotion'))
 def test_19_wheel_reversal_keeps_real_camera_continuous(self):
  self.motion_page();self.page.mouse.move(850,420)
  self.page.mouse.wheel(0,120);self.page.wait_for_timeout(100)
  self.assertEqual(self.section(),'artist');self.assertTrue(self.page.evaluate('window.__NOIR_TEST__.transitioning'))
  self.page.mouse.wheel(0,-120);self.page.wait_for_timeout(50)
  self.assertEqual(self.section(),'home')
  self.page.wait_for_function('!window.__NOIR_TEST__.transitioning',timeout=15000)
  self.assertAlmostEqual(self.page.evaluate('window.__NOIR_TEST__.camera.radius'),11.9)
 def test_20_artist_panel_can_return_home_with_real_camera(self):
  self.motion_page();self.go('artist')
  self.wheel(-40,'#section-content h2',pause=50);self.assertEqual(self.section(),'home')
  self.page.wait_for_function('!window.__NOIR_TEST__.transitioning',timeout=15000)
  self.assertFalse(self.page.evaluate('window.__NOIR_TEST__.panelVisible'))

if __name__=='__main__':unittest.main(verbosity=2)
