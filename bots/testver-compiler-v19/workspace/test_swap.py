import json, base64, zlib, importlib.util, ast, sys
from kaggle_environments import make

DATA = '/home/user/kaggriculture/V18 - Adapt-2-Survive/data'

# Load and encode tapes
with open(f'{DATA}/route_v18_opt_seat0_s16.json') as f:
    s16_s0 = json.load(f)
with open(f'{DATA}/route_v18_opt_seat1_s5.json') as f:
    s5_s1 = json.load(f)

s16_s0_enc = base64.b85encode(zlib.compress(json.dumps(s16_s0).encode()))
s5_s1_enc = base64.b85encode(zlib.compress(json.dumps(s5_s1).encode()))

# Write encoded tapes to files
with open('/tmp/tape_s0.bin', 'wb') as f:
    f.write(s16_s0_enc)
with open('/tmp/tape_s1.bin', 'wb') as f:
    f.write(s5_s1_enc)

print(f"Encoded tapes written to /tmp/")

# Build test agent code
test_code = f'''
import json, base64, zlib, copy, math

# Load tapes from files
with open("/tmp/tape_s0.bin", "rb") as f:
    _SEAT0_ACTIONS = json.loads(zlib.decompress(base64.b85decode(f.read())))
with open("/tmp/tape_s1.bin", "rb") as f:
    _SEAT1_ACTIONS = json.loads(zlib.decompress(base64.b85decode(f.read())))

print(f"Loaded tapes: SEAT0={{len(_SEAT0_ACTIONS)}}, SEAT1={{len(_SEAT1_ACTIONS)}}")

# Copy all functions from the original agent
from kaggriculture.V18_Adapt_2_Survive.submit import main as orig_main

# Override the tapes
import kaggriculture.V18_Adapt_2_Survive.submit.main as mod
mod._SEAT0_ACTIONS = _SEAT0_ACTIONS
mod._SEAT1_ACTIONS = _SEAT1_ACTIONS

agent = mod.agent
'''

# Actually, let's just directly modify the submit/main.py
# Read it, replace the tape loading with file-based loading

with open('/home/user/kaggriculture/V18 - Adapt-2-Survive/submit/main.py') as f:
    code = f.read()

# Find where tapes are loaded and replace with file-based loading
# The original code has:
# _SEAT0_ACTIONS = json.loads(zlib.decompress(base64.b85decode(
#     (
#     'BASE85STRING'
#     )
# )).decode("utf-8"))
# 
# We'll replace the BASE85STRING with file loading

# Find the start and end of SEAT0 tape data
s0_marker = "_SEAT0_ACTIONS = json.loads(zlib.decompress(base64.b85decode("
s0_start = code.find(s0_marker)
s0_data_start = code.find("('", s0_start) + 2  # After the opening quote
s0_data_end = code.find("')\n    )))\n_SEAT1", s0_data_start)
s0_end = code.find("))\n\n_PRICE_FLOOR", s0_data_end) + 2

print(f"SEAT0 tape data: positions {s0_data_start}-{s0_data_end}")

# Extract the structure before and after the tape data
prefix_s0 = code[:s0_data_start]
suffix_s0 = code[s0_data_end:]

# Build new SEAT0 loading code
new_s0_tape = f'''    f.read()
with open("/tmp/tape_s1.bin", "rb") as f:
    _SEAT1_ACTIONS = json.loads(zlib.decompress(base64.b85decode(f.read())))

_PRICE_FLOOR = 1'''

# Actually this is getting too complex. Let me just create a standalone test agent.
test_agent_code = f'''
import json, base64, zlib, copy, math, sys
sys.path.insert(0, "/home/user/kaggriculture/V18 - Adapt-2-Survive/submit")

# Load tapes from files
with open("/tmp/tape_s0.bin", "rb") as f:
    _SEAT0_ACTIONS = json.loads(zlib.decompress(base64.b85decode(f.read())))
with open("/tmp/tape_s1.bin", "rb") as f:
    _SEAT1_ACTIONS = json.loads(zlib.decompress(base64.b85decode(f.read())))

print(f"Loaded tapes: SEAT0={{len(_SEAT0_ACTIONS)}}, SEAT1={{len(_SEAT1_ACTIONS)}}", flush=True)

# Import everything else from the original module
from importlib import import_module
spec = importlib.util.spec_from_file_location("orig", "/home/user/kaggriculture/V18 - Adapt-2-Survive/submit/main.py")
orig = importlib.util.module_from_spec(spec)
spec.loader.exec_module(orig)

# Override tapes
orig._SEAT0_ACTIONS = _SEAT0_ACTIONS
orig._SEAT1_ACTIONS = _SEAT1_ACTIONS

agent = orig.agent

# Test
from kaggle_environments import make
test_seeds = [1, 2, 3]
total = 0
for seed in test_seeds:
    env = make("kaggriculture", configuration={{"episodeSteps": 720, "seed": seed}})
    steps = env.reset()
    env.run([agent, agent])
    score = env.steps[-1][0].reward + env.steps[-1][1].reward
    total += score
    print(f"Seed {{seed}}: ${{score:,.0f}}", flush=True)
print(f"Total: ${{total:,.0f}}", flush=True)
print(f"Baseline: $505,948", flush=True)
print(f"Delta: ${{total - 505948:+,.0f}}", flush=True)
'''

with open('/home/user/standalone_test.py', 'w') as f:
    f.write(test_agent_code)

print("Written standalone_test.py")
print("Running...")
