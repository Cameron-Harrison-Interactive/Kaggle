"""Emit topbots/v6h.py: v4_fr1 skeleton + fitted ramp + fitted tape (pure replay)."""
import ast
import importlib.util
import io
import json
import os

ROOT = "/home/user/WorkSpace 9-2-2026"
real = [d for d in os.listdir(ROOT)
        if os.path.isdir(os.path.join(ROOT, d))
        and os.path.isdir(os.path.join(ROOT, d, "topbots"))][0]
os.chdir(os.path.join(ROOT, real))

champ_src = io.open("topbots/v4_fr1.py", encoding="utf-8").read()
spec = json.loads(
    champ_src.split("tape_author3 spec ")[1].split("). Pure replay")[0])
RAMP = [4, 3, 3, 4, 4, 5, 7, 8, 9, 10, 10, 10, 11, 10, 12, 10, 11, 10,
        10, 11, 12, 10, 12, 12, 10, 12, 10, 9, 9, 9]

os.environ["TAPE_SPEC"] = json.dumps({**spec, "ramp": RAMP})
os.environ["TAPE_OUT"] = ""
mod = importlib.util.spec_from_file_location("auth_emit", "_ref/tape_author3.py")
m = importlib.util.module_from_spec(mod)
mod.loader.exec_module(m)
tape = m.author()

Q = chr(39) * 3                     # the triple-quote, no literal in this file
MARK = "TAPE = json.loads(r" + Q

head_end = champ_src.index(MARK)
head = champ_src[:head_end]
ds0 = head.index("tape_author3 spec ") + len("tape_author3 spec ")
ds1 = head.index("). Pure replay")
new_head = head[:ds0] + json.dumps({**spec, "ramp": RAMP}) + head[ds1:]

open_q = champ_src.index(Q, head_end + len(MARK) - len(Q))
close_q = champ_src.index(Q, open_q + 3)
tail = champ_src[close_q + 3:]

body = json.dumps(tape, separators=(",", ":"))
bot = new_head + MARK + body + Q + tail
io.open("topbots/v6h.py", "w", encoding="utf-8").write(bot)

v6h_src = io.open("topbots/v6h.py", encoding="utf-8").read()
vt = json.loads(v6h_src.split(MARK)[1].split(Q)[0])
assert vt == tape, "round-trip mismatch"
ast.parse(v6h_src)
print("v6h.py written:", os.path.getsize("topbots/v6h.py"), "bytes, parses OK")
print("docstring ramp:", json.loads(
    v6h_src.split("tape_author3 spec ")[1].split("). Pure replay")[0])["ramp"] == RAMP)
