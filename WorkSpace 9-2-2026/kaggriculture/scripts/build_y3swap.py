"""Build V46 variants with V48's rewritten yarn_third tape swapped in."""
import json, zlib, base64, importlib.util
from importlib.machinery import SourceFileLoader

BASE = '/home/user/kaggriculture'
v48 = json.load(open(BASE + '/topbots/v48_routes_decoded.json'))
y3 = v48['yarn_third']

loader = SourceFileLoader('y3m', BASE + '/topbots/main.py')
spec = importlib.util.spec_from_loader('y3m', loader)
m = importlib.util.module_from_spec(spec)
loader.exec_module(m)
routes = dict(m._V44_ROUTES)
routes['yarn_third'] = y3

def build(out_path, base_file):
    src = open(base_file).read()
    b85 = base64.b85encode(zlib.compress(json.dumps(routes).encode())).decode()
    endm = ')).decode("utf-8"))'
    i = src.index('_V44_ROUTES = json.loads(zlib.decompress(base64.b85decode(')
    j = src.index(endm, i) + len(endm)
    out = src[:i] + '_V44_ROUTES = json.loads(zlib.decompress(base64.b85decode((\n' + repr(b85) + '\n))).decode("utf-8"))' + src[j:]
    open(out_path, 'w').write(out)
    print(out_path, len(out))

build('/tmp/y3_stock.py', BASE + '/topbots/main.py')
build('/tmp/y3_w9.py', BASE + '/topbots/w9_wheat_maker.py')
