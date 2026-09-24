import sys, importlib.util, os, traceback
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
from sim import GameSim
def load(path, name):
    s = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
print("sys.path[:3]:", sys.path[:3])
bb = load(os.path.join(ROOT, "topbots", "v1112fr.py"), "bb_dbg2")
sim = GameSim(seed=1)
o = sim.obs(0)
try:
    a = bb.agent(o, None)
    print("step0 action:", str(a)[:150])
except Exception:
    traceback.print_exc()
