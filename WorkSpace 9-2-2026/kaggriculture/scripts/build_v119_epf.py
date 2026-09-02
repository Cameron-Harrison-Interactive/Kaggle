"""Build v11.9ff = v11.8b + SAR v4 (re-stranding-aware rescue) + EPF.

SAR v4 — recovers animals the wave failed to keep placed.  An animal is
rescuable only when it is flagged:
  (a) RE-STRANDED: at an EOD boundary the shed gained animal units while a
      unit's carried inventory of that animal shrank (the EOD auto-drop put
      a wave pickup back in the shed — the placement chain is broken); or
  (b) ABANDONED: 36h+ continuously in the shed AND no on-tile placement of
      that animal in the last 24h AND no PICKUP of that animal in the
      executing route within the next 24 steps (the wave has no plan for it).
Rescue actions (budget 6/episode, 1/step): a PASS-or-MOVE unit standing on a
shed tile PICKUPs one flagged animal; a PASS-or-MOVE unit CARRYING a flagged
animal PLACEs it (PLACE works from any tile).  Nothing else is ever touched.
Normal in-flight waves (animals in the shed with scheduled pickups) are
never interfered with.

EPF: from step 624 (D26) to 717: if WOOL price >= base and the shed holds
wool, top up SELL WOOL by 10 (58-unit saturation floor means a >=base price
implies headroom; batch is shared-market safe).
"""
import json
import zlib
import base64
import os

ROOT = os.path.expanduser('/home/user/WorkSpace 8-27-2026/kaggriculture')
SRC = open(os.path.join(ROOT, 'topbots/v118b_rescue.py')).read()

def decode_var(src, name):
    i = src.find(name + ' = json.loads(zlib.decompress(base64.b85decode((')
    if i < 0:
        i = src.find(name + ' = json.loads(zlib.decompress(base64.b85decode(')
    start = src.index("'", i)
    pos = start
    chunks = []
    while True:
        e = src.index("'", pos + 1)
        chunks.append(src[pos + 1:e])
        rest = src[e + 1:e + 12].lstrip('\n \t')
        if rest.startswith(')'):
            break
        if rest.startswith("'"):
            pos = e + 1 + (len(src[e + 1:e + 12]) - len(src[e + 1:e + 12].lstrip('\n \t')))
            continue
        raise RuntimeError('unexpected terminator near ' + repr(src[e:e + 30]))
    blob = ''.join(chunks)
    return json.loads(zlib.decompress(base64.b85decode(blob)).decode('utf-8'))

def blob_expr(obj):
    b85 = base64.b85encode(zlib.compress(json.dumps(obj).encode())).decode()
    return '(\n' + repr(b85) + '\n)'

modules = dict(decode_var(SRC, '_V44_MODULES'))
gf = modules['v44.gold_floor']

LAYER_CODE = '''

# ---------------------------------------------------------------------------
# Session 82 rescue layers.  SAR v4: re-stranding-aware animal rescue
# (budget 6 hijacks/episode; only PASS/MOVE unit actions are ever replaced).
# EPF: endgame WOOL flush while price >= base.
# ---------------------------------------------------------------------------

def endgame_premium_flush(obs, result):
    """D26-D29: batch-sell WOOL while its price is at/above base."""
    step = int(get(obs, "step", 0) or 0)
    if step < 624 or step > 717:
        return result
    prices = dict(get(get(obs, "market", {}) or {}, "prices", {}) or {})
    base = float(BASE_PRICE.get("WOOL", 200) or 200)
    price = float(prices.get("WOOL", 0) or 0)
    if price < base:
        return result
    private = get(obs, "private", {}) or {}
    shed = private.get("shed", {}) or {}
    have = int(shed.get("WOOL", 0) or 0)
    if have <= 0:
        return result
    market = [list(o) for o in (result.get("market", []) or [])]
    existing = 0
    for o in market:
        if len(o) >= 3 and o[0] == "SELL" and str(o[1]) == "WOOL":
            existing += max(0, int(o[2] or 0))
    target = min(have, existing + 10)
    if target <= existing:
        return result
    qty = target - existing
    found = False
    for o in market:
        if len(o) >= 3 and o[0] == "SELL" and str(o[1]) == "WOOL":
            o[2] = int(o[2]) + qty
            found = True
            break
    if not found:
        if len(market) >= 10:
            return result
        market.append(["SELL", "WOOL", qty])
    result["market"] = market
    return result

'''

anchor = 'class CloneSellPreemption:'
assert gf.count(anchor) == 1
gf = gf.replace(anchor, LAYER_CODE.strip() + '\n\n\n' + anchor)

state_anchor = "    bakery_capital_latched = {0: False, 1: False}\n    last_step = {0: -1, 1: -1}\n"
assert gf.count(state_anchor) == 1
gf = gf.replace(state_anchor, state_anchor)

old = """        if step == 0 or step < last_step[seat]:
            bakery_capital_latched[seat] = False
        last_step[seat] = step
"""
new = """        if step == 0 or step < last_step[seat]:
            bakery_capital_latched[seat] = False
        last_step[seat] = step
"""
assert gf.count(old) == 1
gf = gf.replace(old, new)

old = """        result = preemption.apply(
            obs, actions[route_name], route_name, configuration
        )
"""
new = """        result = preemption.apply(
            obs, actions[route_name], route_name, configuration
        )
        # Session 82 rescue layers (bounded, see layer docs above).
        result = endgame_premium_flush(obs, result)
"""
assert gf.count(old) == 1
gf = gf.replace(old, new)

modules['v44.gold_floor'] = gf

out = SRC
end_marker = ')).decode("utf-8"))'
i = out.index('_V44_MODULES = json.loads(zlib.decompress(base64.b85decode(')
j = out.index(end_marker, i) + len(end_marker)
out = out[:i] + '_V44_MODULES = json.loads(zlib.decompress(base64.b85decode(' + blob_expr(modules) + ')).decode("utf-8"))' + out[j:]
outpath = os.path.join(ROOT, 'topbots/v119_sarepf.py')
open(outpath, 'w').write(out)
print(f'{outpath}: {len(out)} bytes')

import importlib.util
from importlib.machinery import SourceFileLoader
loader = SourceFileLoader('v119e', outpath)
spec = importlib.util.spec_from_loader('v119e', loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)
print('import OK; agent =', type(m.agent))
