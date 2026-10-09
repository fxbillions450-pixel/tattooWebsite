from pathlib import Path
p=Path('tests/fallback_notice.py');s=p.read_text()
old='  p.wait_for_function("id=>__NOIR_TEST__.section===id&&!__NOIR_TEST__.transitioning",arg=section)'
assert s.count(old)==1
s=s.replace(old,old+'''
  p.evaluate("() => new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))")
  if section!='home':p.wait_for_function("getComputedStyle(document.querySelector('#panel')).transform==='matrix(1, 0, 0, 1, 0, 0)' && getComputedStyle(document.querySelector('#panel')).opacity==='1'")''')
old="    for sel in ['#scene','.topbar','.bottom-bar','#panel','.return-overview']:"
assert s.count(old)==1
s=s.replace(old,"    for sel in ['#scene','.topbar','.bottom-bar']+(['.hero','.explore'] if section=='home' else ['#panel','.return-overview']):")
p.write_text(s)
