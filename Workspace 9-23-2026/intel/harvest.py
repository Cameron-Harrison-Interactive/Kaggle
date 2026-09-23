#!/usr/bin/env python3
"""Batch replay harvester: download N episodes, extract compact intel, delete raw.
Usage: python3 harvest.py [N]   (state: /home/user/intel/queue.json + eps/*.json.gz + fails.txt)
"""
import subprocess, json, os, sys, glob, time

N = int(sys.argv[1]) if len(sys.argv) > 1 else 40
INTEL = "/home/user/intel"
TMP = "/tmp/replays"
os.makedirs(TMP, exist_ok=True)
queue = json.load(open(f"{INTEL}/queue.json"))
done = {int(os.path.basename(f)[3:-8]) for f in glob.glob(f"{INTEL}/eps/ep_*.json.gz")}
fails = {}
if os.path.exists(f"{INTEL}/fails.json"):
    fails = json.load(open(f"{INTEL}/fails.json"))

todo = [e for e in map(int, queue.keys()) if e not in done and fails.get(str(e), 0) < 3]
print(f"queue={len(queue)} done={len(done)} todo={len(todo)} processing={min(N,len(todo))}")
t0 = time.time()
ok = 0
for i, eid in enumerate(todo[:N]):
    try:
        subprocess.run(["python3","-m","kaggle","competitions","replay",str(eid),"-p",TMP,"-q"],
                       capture_output=True, timeout=120)
        cands = glob.glob(f"{TMP}/*{eid}*")
        if not cands:
            raise RuntimeError("no file")
        r = subprocess.run(["python3", f"{INTEL}/extract.py", cands[0]],
                           capture_output=True, text=True, timeout=120)
        if r.returncode != 0:
            raise RuntimeError(r.stderr[-200:])
        ok += 1
        for c in cands: os.remove(c)
    except Exception as e:
        fails[str(eid)] = fails.get(str(eid), 0) + 1
        for c in glob.glob(f"{TMP}/*{eid}*"): os.remove(c)
        print(f"  FAIL {eid}: {e}")
json.dump(fails, open(f"{INTEL}/fails.json","w"))
print(f"extracted {ok}/{min(N,len(todo))} in {time.time()-t0:.0f}s; total done={len(done)+ok}, remaining={len(todo)-ok}")
