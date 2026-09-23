import sys,gzip,json,collections
tag,seed=sys.argv[1],sys.argv[2]
s=json.load(gzip.open(f'intel/clone_runs/{tag}_{seed}.json.gz','rt'));s=s['steps'] if isinstance(s,dict) else s
for day in range(16,30):
 sts=[(j,x) for j,x in enumerate(s) if x[0]['observation'].get('day')==day]
 if not sts:continue
 j,last=sts[-1];f=last[0]['observation']['farms'][0]
 c=collections.Counter('EMPTY' if t is None else t.get('crop',t.get('kind')) if isinstance(t,dict) else t for r in f['tiles'] for t in r)
 ac=collections.Counter();pl=collections.Counter()
 for j,x in sts:
  if j+1>=len(s):continue
  a=s[j+1][0].get('action') or {}
  for v in [a.get('farmer')]+(a.get('hands') or []):
   if v:ac[v[0]]+=1
   if v and v[0]=='PLANT':pl[v[1]]+=1
 print(day,'$',int(f['money']),'W',c['WEED'],'E',c['EMPTY'],'WH',c['WHEAT'],'ST',c['STRAWBERRY'],'TO',c['TOMATO'],'WTR',ac['WATER'],'DIG',ac['DIG'],'FRT',ac['FERTILIZE'],'HV',ac['HARVEST'],'PL',dict(pl))
