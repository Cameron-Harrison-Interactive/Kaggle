import sys,os,importlib.util,contextlib,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];os.chdir(ROOT);sys.path.insert(0,str(ROOT))
import kaggle_environments as ke,watch
sp=importlib.util.spec_from_file_location('meta','war/meta_v1.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);orig=m.agent;lines=[]
def quadrant(p):return ("N" if p[1]<5 else "S")+("W" if p[0]<5 else "E")
def wrapper(o,c):
 a=orig(o,c)
 if o['day']==11 and o['hour'] in (1,2):
  st=m.STATE[0];f=o['farms'][0];p=o['private']
  lines.append(('h',o['hour'],'seeds',dict(p['seeds']),'money',f['money']))
  tiles=f['tiles'];empty=[(x,y) for y in range(10) for x in range(10) if tiles[y][x] is None]
  lines.append(('empty NW:',[e for e in empty if quadrant(e)=='NW'],'NE:',[e for e in empty if quadrant(e)=='NE'],'SW:',[e for e in empty if quadrant(e)=='SW']))
  for wi,pl in sorted(st['plans'].items()):
   k=st['ptrs'].get(wi,0)
   lines.append(('w',wi,pl[k:k+16]))
 return a
e=ke.make(watch.env_name(),configuration={'seed':42},debug=True)
with contextlib.redirect_stdout(io.StringIO()):e.run([wrapper,'war/passbot.py'])
lines.append(('score',e.state[0].reward))
for l in lines:print(l)
