"""Real Chromium/WebGL release checks. Run after tools/build.py.
Optional WIZARDS_BASELINE_HTML enables paired render-work and screenshot evidence.
This does not claim physical-GPU FPS from a software-rendered test runner.
"""
from pathlib import Path
import json, os, statistics, time
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'evidence/render-release';OUT.mkdir(parents=True,exist_ok=True)
HTML=(ROOT/'index.html').read_text(encoding='utf-8')
checks=[]
def check(name, condition):
    checks.append({'name':name,'passed':bool(condition)})
    if not condition: raise AssertionError(name)
def ready(page):
    page.wait_for_function('window.__NOIR_TEST__?.assetsWarmed',timeout=45000)
    check('Real WebGL initialized',page.evaluate('window.__NOIR_TEST__.webgl'))
def settle(page):page.wait_for_function('!window.__NOIR_TEST__.transitioning',timeout=25000)
def make(browser, html=HTML, width=1760,height=832,dpr=1,arm='skin',reduced='no-preference'):
    p=browser.new_page(viewport={'width':width,'height':height},device_scale_factor=dpr,has_touch=True,reduced_motion=reduced)
    errors=[];p.on('pageerror',lambda e:errors.append(str(e)))
    p.route('https://wizards.test/**',lambda route:route.fulfill(status=200,body=html,content_type='text/html'))
    p.goto('https://wizards.test/?arm='+arm);ready(p)
    return p,errors

def profile(browser, html, name):
    p,errors=make(browser,html=html,dpr=2)
    p.evaluate('''() => {
      window.perfEvidence={rectReads:0,markerWrites:0,panelWrites:0,intervals:[]};
      const rect=Element.prototype.getBoundingClientRect;
      Element.prototype.getBoundingClientRect=function(){if(this.id==='panel')window.perfEvidence.rectReads++;return rect.call(this)};
      const obs=new MutationObserver(xs=>{for(const x of xs){if(x.target.classList.contains('hotspot'))window.perfEvidence.markerWrites++;if(x.target.id==='panel')window.perfEvidence.panelWrites++;}});
      obs.observe(document.getElementById('hotspots'),{subtree:true,attributes:true});obs.observe(document.getElementById('panel'),{attributes:true});
      let last=null;window.recording=true;
      function f(t){if(last!==null)window.perfEvidence.intervals.push(t-last);last=t;if(window.recording)requestAnimationFrame(f)}requestAnimationFrame(f);
      document.querySelector('.section-nav [data-section="artist"]').click();
    }''')
    settle(p);p.evaluate('window.recording=false');p.wait_for_timeout(30)
    data=p.evaluate('({perf:window.perfEvidence,info:window.__NOIR_TEST__.renderInfo,buffer:[scene.width,scene.height],frames:window.__NOIR_TEST__.frames})')
    samples=data['perf'].pop('intervals')
    data['rafSamples']=len(samples)
    if samples:data['softwareRafMedianMs']=statistics.median(samples);data['softwareRafP95Ms']=sorted(samples)[min(len(samples)-1,int(len(samples)*.95))]
    check(name+' no JS errors',not errors)
    p.screenshot(path=str(OUT/(name+'-artist.png')));p.close();return data

with sync_playwright() as p:
    exe=os.environ.get('CHROMIUM_PATH') or ('/usr/bin/chromium' if Path('/usr/bin/chromium').exists() else p.chromium.executable_path)
    browser=p.chromium.launch(executable_path=exe,headless=True,args=['--no-sandbox','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader'])
    result={'baseline':None,'current':None,'physicalDeviceTested':False}
    baseline=os.environ.get('WIZARDS_BASELINE_HTML')
    if baseline:result['baseline']=profile(browser,Path(baseline).read_text(encoding='utf-8'),'baseline')
    result['current']=profile(browser,HTML,'skin')
    data=result['current']
    check('Retina desktop DPR capped at 1.5',data['info']['pixelRatio']<=1.501)
    check('No per-frame panel rect reads',data['perf']['rectReads']==0)
    check('Hidden markers not updated per frame',data['perf']['markerWrites']<30)
    check('Idempotent panel visibility attributes',data['perf']['panelWrites']<16)
    check('Single draw call with compact 256 skin tile',data['info']['drawCallsPerFrame']==1 and data['info']['skinTextureSize']==256)
    if result['baseline']:
        old=result['baseline'];check('Desktop buffer pixel count reduced',data['buffer'][0]*data['buffer'][1]<old['buffer'][0]*old['buffer'][1])
        check('Marker writes reduced',data['perf']['markerWrites']<old['perf']['markerWrites'])
    for width,height in [(1760,832),(2560,1440),(390,844),(320,568),(430,932),(844,390)]:
        page,errors=make(browser,width=width,height=height,reduced='reduce')
        check(f'{width} switches removed',page.locator('.motion-btn,.color-settings,[data-color]').count()==0)
        check(f'{width} header fits',page.locator('.brand').bounding_box()['x']>=0 and page.locator('.brand').bounding_box()['width']<width)
        check(f'{width} no horizontal overflow',page.evaluate('document.documentElement.scrollWidth<=innerWidth'))
        page.screenshot(path=str(OUT/f'home-{width}.png'))
        page.locator('.section-nav [data-section="artist"]').click();settle(page)
        page.screenshot(path=str(OUT/f'artist-{width}.png'))
        check(f'{width} artist visible',page.locator('#section-title').is_visible())
        page.evaluate("document.querySelector('.section-nav [data-section=home]').click()")
        check(f'{width} return home',page.evaluate('window.__NOIR_TEST__.section')=='home')
        check(f'{width} error free',not errors);page.close()
    page,errors=make(browser,arm='original')
    check('Original material comparison available',page.evaluate('window.__NOIR_TEST__.renderInfo.material')=='original')
    page.locator('.section-nav [data-section="artist"]').click();settle(page);page.wait_for_timeout(450)
    page.screenshot(path=str(OUT/'original-arm-artist.png'))
    page.close()
    page,errors=make(browser)
    for i in range(4):page.locator('#scene').dispatch_event('wheel',{'deltaY':120,'deltaX':0,'bubbles':True,'cancelable':True})
    check('Continuous scroll reaches booking mid-flight',page.evaluate('window.__NOIR_TEST__.section==="booking"&&window.__NOIR_TEST__.transitioning'))
    page.locator('#scene').dispatch_event('wheel',{'deltaY':-120,'bubbles':True,'cancelable':True})
    check('Mid-flight reversal retained',page.evaluate('window.__NOIR_TEST__.section')=='ritual')
    page.emulate_media(reduced_motion='reduce');page.wait_for_function('window.__NOIR_TEST__.reduceMotion')
    check('OS reduced motion stops camera',not page.evaluate('window.__NOIR_TEST__.transitioning'))
    page.emulate_media(reduced_motion='no-preference');page.wait_for_function('!window.__NOIR_TEST__.reduceMotion')
    check('OS no-preference restores motion',not page.evaluate('window.__NOIR_TEST__.reduceMotion'))
    page.locator('.section-nav [data-section="home"]').click();settle(page)
    first=page.evaluate('window.__NOIR_TEST__.frames');page.wait_for_timeout(300)
    check('No idle render loop',page.evaluate('window.__NOIR_TEST__.frames')==first)
    check('Final JS errors absent',not errors);page.close();browser.close()
    result['checks']=checks
    (OUT/'validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))
