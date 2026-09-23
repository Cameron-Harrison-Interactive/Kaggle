import sys,os,importlib.util,contextlib,io
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];os.chdir(ROOT);sys.path.insert(0,str(ROOT))
import kaggle_environments as ke,watch
sp=importlib.util.spec_from_file_location('meta','war/meta_v1.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);orig=m.agent;lines=[]
def wrapper(o,c):
 a=orig(o,c)
 if 10<=o['day']<=12 and o['hour'] in (12,16,20,22):
  st=m.STATE[0];f=o['farms'][0];p=o['private'];lines.append(('day/hour',o['day'],o['hour'],'seeds',p['seeds']))
  for wi,pl in st['plans'].items():
   k=st['ptrs'].get(wi,0);pp=([f['farmer']]+f['hands']);inv=p['inventories'][wi] if wi<len(p['inventories']) else {};lines.append((wi,pp[wi] if wi<len(pp) else None,inv,'left',pl[k:]))
 return a
e=ke.make(watch.env_name(),configuration={'seed':42},debug=True)
with contextlib.redirect_stdout(io.StringIO()):e.run([wrapper,'war/passbot.py'])
print('score',e.state[0].reward)
for l in lines:print(l)
