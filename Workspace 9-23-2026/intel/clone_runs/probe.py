import sys,os,json,gzip,contextlib,io,collections
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.chdir(ROOT);sys.path.insert(0,str(ROOT))
def summary(s,seat=0):
 for d in range(8,21):
  sts=[(j,x) for j,x in enumerate(s) if x[0]['observation'].get('day')==d]
  j,last=sts[-1];f=last[0]['observation']['farms'][seat];c=collections.Counter('EMPTY' if t is None else t.get('crop',t.get('kind')) if isinstance(t,dict) else t for r in f['tiles'] for t in r)
  ac=collections.Counter();pl=collections.Counter();sell=0
  for j,x in sts:
   # action at j+1 was chosen from observation at j
   if j+1>=len(s):continue
   a=s[j+1][seat].get('action') or {}
   for v in [a.get('farmer')]+(a.get('hands') or []):
    if v:ac[v[0]]+=1
    if v and v[0]=='PLANT':pl[v[1]]+=1
   sell+=sum(m[2] for m in a.get('market',[]) if m[:2]==['SELL','MELON'])
  print(d,'$',f['money'],'hands',len(f['hands']),'W',c['WEED'],'E',c['EMPTY'],'WH',c['WHEAT'],'ST',c['STRAWBERRY'],'ME',c['MELON'],'WTR',ac['WATER'],'DIG',ac['DIG'],'FERT',ac['FERTILIZE'],'HV',ac['HARVEST'],'DROP',ac['DROP'],'SELLM',sell,'PL',dict(pl))
if __name__=='__main__':
 seed=int(sys.argv[1]) if len(sys.argv)>1 else 42;tag=sys.argv[2] if len(sys.argv)>2 else 'latest'
 import kaggle_environments as ke,watch
 env=ke.make(watch.env_name(),configuration={'seed':seed},debug=True)
 with contextlib.redirect_stdout(io.StringIO()):env.run([sys.argv[3] if len(sys.argv)>3 else 'war/meta_v1.py','war/passbot.py'])
 print('score',env.state[0].reward)
 with gzip.open(f'intel/clone_runs/{tag}_{seed}.json.gz','wt') as f:json.dump(env.steps,f)
 summary(env.steps)
