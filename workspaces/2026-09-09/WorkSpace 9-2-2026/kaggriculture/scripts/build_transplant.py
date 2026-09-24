"""Build a 'transplant' engine: V46's robustness wrapper (align_hands +
terminal_market + weed repair) playing a TOP PLAYER's recorded 719-step
stream as its sole tape.

Usage: python3 scripts/build_transplant.py <tape_key:crop_dusta_tape|ryo_tape> <out.py>
"""
import json
import zlib
import base64
import re
import sys
import importlib.util
from importlib.machinery import SourceFileLoader

ROOT = '/home/user/kaggriculture'
tape_key = sys.argv[1] if len(sys.argv) > 1 else 'crop_dusta_tape'
out_path = sys.argv[2] if len(sys.argv) > 2 else '/tmp/cd_transplant.py'

ep = json.load(open(f'{ROOT}/analysis/top_replays/ep_100075619.json'))
tape = ep[tape_key][:719]

loader = SourceFileLoader('tmpmod', f'{ROOT}/topbots/main.py')
spec = importlib.util.spec_from_loader('tmpmod', loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)
modules = dict(m._V44_MODULES)

gf = modules['v44.gold_floor']
gf2 = gf.replace('ROUTES = ("default", "yarn_first", "yarn_second", "yarn_third")',
                 'ROUTES = ("cd_tape",)')
gf2 = gf2.replace('OPTIONAL_ROUTES = ("bakery_capital",)', 'OPTIONAL_ROUTES = ()')
pat = re.compile(r'def selected_route\(obs: Any, config: GoldFloorConfig\) -> str:.*?\n    return "default"\n', re.S)
gf2, n = pat.subn('def selected_route(obs: Any, config: GoldFloorConfig) -> str:\n    return "cd_tape"\n', gf2)
assert n == 1, 'selected_route patch failed'
modules['v44.gold_floor'] = gf2


def blob_expr(obj):
    b85 = base64.b85encode(zlib.compress(json.dumps(obj).encode())).decode()
    return '(\n' + repr(b85) + '\n)'


src = open(f'{ROOT}/topbots/v46_editable.py').read()
routes = {'cd_tape': tape, 'bakery_capital': m._V44_ROUTES['bakery_capital']}
out = src
end_marker = ')).decode("utf-8"))'
i = out.index('_V44_ROUTES = json.loads(zlib.decompress(base64.b85decode(')
j = out.index(end_marker, i) + len(end_marker)
out = out[:i] + '_V44_ROUTES = json.loads(zlib.decompress(base64.b85decode(' + blob_expr(routes) + ')).decode("utf-8"))' + out[j:]
i = out.index('_V44_MODULES = json.loads(zlib.decompress(base64.b85decode(')
j = out.index(end_marker, i) + len(end_marker)
out = out[:i] + '_V44_MODULES = json.loads(zlib.decompress(base64.b85decode(' + blob_expr(modules) + ')).decode("utf-8"))' + out[j:]
open(out_path, 'w').write(out)
print(f'{out_path}: {len(out)} bytes (tape={tape_key}, steps={len(tape)})')
