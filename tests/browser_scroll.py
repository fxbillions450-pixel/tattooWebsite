"""NOIR continuous input regressions. Run: python tests/browser_scroll.py
Uses Chromium WebGL, trusted wheel/touch events, file:// and local HTTP.
CHROMIUM_PATH optionally chooses an installed Chromium executable.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import json, os, threading, unittest
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
class QuietHandler(SimpleHTTPRequestHandler):
 def log_message(self,*args): pass

class ScrollFlow(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(ROOT)))
  threading.Thread(target=cls.server.serve_forever,daemon=True).start()
  cls.url=f'http://127.0.0.1:{cls.server.server_port}/index.html'
  cls.pw=sync_playwright().start()
  exe=os.environ.get('CHROMIUM_PATH') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else cls.pw.chromium.executable_path)
  cls.browser=cls.pw.chromium.launch(executable_path=exe,headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
  cls.evidence=[]
 @classmethod
 def tearDownClass(cls):
  (ROOT/'evidence').mkdir(exist_ok=True)
  (ROOT/'evidence'/'scroll-flow-browser.json').write_text(json.dumps(cls.evidence,indent=2))
  cls.browser.close();cls.pw.stop();cls.server.shutdown();cls.server.server_close()
 def setUp(self):
  self.errors=[]
  self.page=self.browser.new_page(viewport={'width':1440,'height':900},has_touch=True,reduced_motion='no-preference')
  self.page.on('pageerror',lambda e:self.errors.append(str(e)))
  self.page.goto(self.url)
  self.ready()
 def tearDown(self):
  self.page.close();self.assertEqual(self.errors,[])
 def ready(self):
  self.page.wait_for_function('window.__NOIR_TEST__?.assetsWarmed',timeout=20000)
  self.assertTrue(self.state()['webgl'])
 def state(self): return self.page.evaluate('window.__NOIR_TEST__')
 def go(self,id):
  self.page.locator(f'.section-nav [data-section="{id}"]').click()
  self.page.wait_for_function('!window.__NOIR_TEST__.transitioning',timeout=20000)
  self.page.wait_for_timeout(260)
 def stroke(self,values,offsets=None,x=710,y=420):
  """Trusted input, preserving capture cadence despite software-GPU delivery delays."""
  offsets=offsets or [i*55 for i in range(len(values))]
  self.page.mouse.move(x,y)
  self.page.evaluate("""() => {
   window.__flow=[]; window.__flowListener=e=>window.__flow.push({
    delta:e.deltaY,stamp:e.timeStamp,trusted:e.isTrusted,...window.__NOIR_TEST__});
   document.getElementById('app').addEventListener('wheel',window.__flowListener,{passive:true});
  }""")
  origin,base=self.page.evaluate('[performance.timeOrigin,performance.now()]')
  cdp=self.page.context.new_cdp_session(self.page)
  try:
   for offset,value in zip(offsets,values):
    cdp.send('Input.dispatchMouseEvent',{'type':'mouseWheel','x':x,'y':y,'deltaX':0,'deltaY':value,'timestamp':(origin+base+offset)/1000})
   self.page.wait_for_function(f'window.__flow.length >= {len(values)}',timeout=15000)
   self.page.wait_for_timeout(40)
   trace=self.page.evaluate('window.__flow')
   self.assertEqual(len(trace),len(values));self.assertTrue(all(e['trusted'] for e in trace))
   self.evidence.append({'test':self.id(),'url':self.page.url,'events':trace})
   return trace
  finally:
   self.page.evaluate("document.getElementById('app').removeEventListener('wheel',window.__flowListener)");cdp.detach()
 def test_01_rapid_notches_pass_sections_before_landing(self):
  trace=self.stroke([120,120,120],[0,55,110])
  self.assertEqual([e['section'] for e in trace],['artist','work','ritual'])
  self.assertTrue(all(e['transitioning'] for e in trace))
  self.assertEqual(self.state()['section'],'ritual')
 def test_02_immediate_reversal_during_motion(self):
  self.stroke([120,120,120,-120,-120,-120],[0,45,90,135,180,225])
  self.assertEqual(self.state()['section'],'home')
 def test_03_gentle_continuation_is_registered(self):
  trace=self.stroke([120]+[20]*10)
  self.assertEqual(self.state()['section'],'ritual')
  self.assertTrue(trace[-1]['transitioning'])
 def test_04_stop_input_does_not_queue_more_sections(self):
  self.stroke([120,120]);self.assertEqual(self.state()['section'],'work')
  self.page.wait_for_function('!window.__NOIR_TEST__.transitioning',timeout=20000)
  self.page.wait_for_timeout(450);self.assertEqual(self.state()['section'],'work')
 def test_05_file_and_http_have_same_input_results(self):
  self.stroke([120,120,-120]);expected=self.state()['section']
  self.page.goto((ROOT/'index.html').as_uri());self.ready()
  self.stroke([120,120,-120]);self.assertEqual(self.state()['section'],expected)
 def test_06_artist_panel_top_scroll_returns_home(self):
  self.go('artist');self.page.locator('#section-content h2').hover()
  self.page.mouse.wheel(0,-40)
  self.page.wait_for_function("window.__NOIR_TEST__.section==='home'")
 def test_07_native_reading_and_boundary_remain_usable(self):
  self.go('work');content=self.page.locator('#section-content');content.evaluate('e=>e.scrollTop=80');content.hover()
  self.page.mouse.wheel(0,100)
  self.page.wait_for_function("document.querySelector('#section-content').scrollTop>80")
  self.assertEqual(self.state()['section'],'work')
  self.page.wait_for_timeout(230);content.evaluate('e=>e.scrollTop=e.scrollHeight')
  self.page.mouse.wheel(0,120)
  self.page.wait_for_function("window.__NOIR_TEST__.section==='ritual'")
 def test_08_modal_editable_zoom_and_horizontal_inputs_are_not_hijacked(self):
  self.go('booking');self.page.locator('input[name=name]').hover();self.page.mouse.wheel(0,-120)
  self.page.wait_for_timeout(80);self.assertEqual(self.state()['section'],'booking')
  for args in [{'deltaY':-120,'ctrlKey':True},{'deltaY':-120,'metaKey':True},{'deltaY':-20,'deltaX':120}]:
   self.page.locator('#app').dispatch_event('wheel',dict(bubbles=True,cancelable=True,**args))
  self.assertEqual(self.state()['section'],'booking')
  self.go('work');self.page.locator('.art-card').first.click();self.page.mouse.wheel(0,-120)
  self.page.wait_for_timeout(80);self.assertEqual(self.state()['section'],'work')
 def test_09_touch_long_drag_and_reverse_before_landing(self):
  self.page.set_viewport_size({'width':390,'height':844});self.page.wait_for_timeout(150)
  cdp=self.page.context.new_cdp_session(self.page)
  try:
   cdp.send('Input.dispatchTouchEvent',{'type':'touchStart','touchPoints':[{'x':300,'y':550}]})
   for y in [490,430,370,310,250]:
    cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':300,'y':y}]})
   self.assertEqual(self.state()['section'],'ritual');self.assertTrue(self.state()['transitioning'])
   cdp.send('Input.dispatchTouchEvent',{'type':'touchMove','touchPoints':[{'x':300,'y':330}]})
   self.assertEqual(self.state()['section'],'work')
   cdp.send('Input.dispatchTouchEvent',{'type':'touchEnd','touchPoints':[]})
  finally: cdp.detach()
 def test_10_reduced_motion_keeps_navigation(self):
  self.page.emulate_media(reduced_motion='reduce');self.page.wait_for_function('window.__NOIR_TEST__.reduceMotion');self.assertTrue(self.state()['reduceMotion'])
  self.stroke([120,120,120]);self.assertEqual(self.state()['section'],'ritual');self.assertFalse(self.state()['transitioning'])
 def test_11_header_and_footer_are_not_dead_zones(self):
  self.go('artist');self.page.locator('.topnav').hover();self.page.mouse.wheel(0,-120)
  self.page.wait_for_function("window.__NOIR_TEST__.section==='home'")
  self.page.wait_for_timeout(200);self.page.locator('.settings').hover();self.page.mouse.wheel(0,120)
  self.page.wait_for_function("window.__NOIR_TEST__.section==='artist'")
 def test_12_browser_history_and_direct_click_still_work(self):
  self.stroke([120,120]);self.go('booking');self.stroke([-120]);self.assertEqual(self.state()['section'],'ritual')
  self.page.go_back();self.page.wait_for_function("window.__NOIR_TEST__.section==='booking'")
 def test_13_small_wheel_units_accumulate(self):
  self.go('artist');self.stroke([-20,-20],[0,240]);self.assertEqual(self.state()['section'],'home')
 def test_14_menu_blocks_mobile_navigation(self):
  self.page.set_viewport_size({'width':390,'height':844});self.go('artist')
  self.page.locator('.menu-toggle').click();self.stroke([-120],x=200,y=300)
  self.assertEqual(self.state()['section'],'artist')

if __name__=='__main__':unittest.main(verbosity=2)
