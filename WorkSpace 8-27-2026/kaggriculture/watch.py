"""
watch.py — replay viewer for main.py vs the v25 tape (or any two agents).

Runs the match through the bit-exact in-memory simulator (GameSim, verified
against the real engine), records EVERY step of both farms, and writes a
self-contained `watch.html` you can open in any browser.  The page animates
the whole game side by side — our farm on the left, the opponent on the
right — with money, market prices, town shops and the live action feed, plus
play/pause / speed / scrub controls.  No network, no external files: the game
is embedded as JSON inside the HTML, so it works offline.

Usage:
    python3 watch.py            # main.py vs v25 tape, seeds 1,2,3
    python3 watch.py 1 7        # just seeds 1 and 7
    python3 watch.py 1 --mirror # main.py vs the mirror archetype

Output: watch.html (open it, or it is shown in the workspace viewer).

Why this exists: the ladder's "gap" to the v25 tape is a *visual* problem as
much as a scoring one — you need to SEE where the tape plants 38 strawberries
and we plant 9, where its hands are at hour 6 and ours are not, and where the
cash goes.  Watch the replay, tell me what looks wrong, and I will fix it.
"""
import sys, os, re, json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "scripts"))
sys.path.insert(0, os.path.join(HERE, "agent"))

from sim import GameSim
import main as M
import decision_agent_v2 as v2


# ---------------------------------------------------------------- opponents
def pass_agent(obs, cfg=None):
    farm = obs["farms"][obs["player"]]
    n = len(farm.get("hands", []) or [])
    return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}


class TapeAgent:
    """Replay the fixed v25 tape verbatim (works in either seat)."""
    def __init__(self, actions):
        self.actions, self.step = actions, 0
    def __call__(self, obs):
        if self.step < len(self.actions):
            t = self.actions[self.step]
            self.step += 1
            n = len(obs["farms"][obs["player"]].get("hands", []) or [])
            hands = list(t.get("hands") or [])
            while len(hands) < n:
                hands.append(["PASS"])
            return {"market": list(t.get("market") or []),
                    "farmer": t.get("farmer") or ["PASS"], "hands": hands[:n]}
        return {"farmer": ["PASS"], "hands": [], "market": []}


def load_tape():
    src = open(os.path.join(HERE, "agent", "main_v25_wheat16.py")).read()
    m = re.search(r"_SEAT0_ACTIONS = json.loads\(\'(.*?)\'\)", src, re.S)
    return json.loads(m.group(1))


def v2_agent(params):
    cls = v2.CounterAgent if hasattr(v2, "CounterAgent") else v2.DecisionAgent
    inst = cls(params, seat=0)
    return lambda obs, config=None: inst.act(obs, config)


ARCHETYPES = {
    "mirror":   dict(v2.DEFAULT_PARAMS),
    "cowbot":   {**dict(v2.DEFAULT_PARAMS), "final_cow": 14, "final_sheep": 0,
                 "target_sheep": 0, "open_sheep": 0},
    "sheepbot": {**dict(v2.DEFAULT_PARAMS), "final_cow": 2, "final_sheep": 12,
                 "open_cows": 2, "open_sheep": 3},
    "goosebot": {**dict(v2.DEFAULT_PARAMS), "final_cow": 4, "final_sheep": 2,
                 "target_goose": 3, "final_goose": 10},
    "cropbot":  {**dict(v2.DEFAULT_PARAMS), "final_cow": 4, "final_sheep": 2,
                 "open_cows": 1, "open_sheep": 1},
}


# ------------------------------------------------------------- state encode
TILE = {"WHEAT": "w", "CARROT": "c", "TOMATO": "t", "STRAWBERRY": "s",
        "MELON": "m"}


def enc_tile(t):
    if t is None:
        return "."
    if t == "LOCKED":
        return "#"
    if isinstance(t, dict):
        k = t.get("kind")
        if k == "PLANT":
            return TILE.get(t.get("crop"), "?")
        if k == "WEED":
            return "x"
        if k in ("PASTURE", "COOP"):
            a = t.get("animal")
            if a == "COW":
                return "C"
            if a == "SHEEP":
                return "S"
            if a == "GOOSE":
                return "G"
            return "p" if k == "PASTURE" else "o"
    return "?"


def encode_farm(tiles):
    return "".join(enc_tile(t) for row in tiles for t in row)


def summarize_action(act):
    """Compact human-readable summary of one player's action."""
    if not isinstance(act, dict):
        return "-"
    parts = []
    f = act.get("farmer")
    if isinstance(f, list) and f and f[0] != "PASS":
        parts.append("F:" + ",".join(str(x) for x in f))
    hands = [h for h in (act.get("hands") or []) if isinstance(h, list)
             and h and h[0] != "PASS"]
    if hands:
        ops = {}
        for h in hands:
            ops[h[0]] = ops.get(h[0], 0) + 1
        parts.append("H:" + ",".join(f"{k}x{v}" for k, v in sorted(ops.items())))
    for o in (act.get("market") or []):
        if isinstance(o, list) and o:
            parts.append("M:" + ",".join(str(x) for x in o))
    return " | ".join(parts) if parts else "-"


def run_match(agent0, agent1, seed):
    """Run one match, recording a frame per step (frame i = state after i steps)."""
    # main.py no longer has set_params (V41 has its own state)
    pass
    sim = GameSim(seed=seed)
    frames = []

    def snap(a0, a1):
        o = sim.state[0].observation
        obs0 = sim.obs(0)
        obs1 = sim.obs(1)
        return {
            "day": int(o.day), "hour": int(o.hour),
            "m0": float(obs0["farms"][0]["money"]),
            "m1": float(obs1["farms"][1]["money"]),
            "b0": encode_farm(obs0["farms"][0]["tiles"]),
            "b1": encode_farm(obs1["farms"][1]["tiles"]),
            "prices": dict(o.market["prices"]),
            "shops": list(o.town["unlocked_shops"]),
            "a0": summarize_action(a0), "a1": summarize_action(a1),
        }

    frames.append(snap({"market": [], "farmer": ["PASS"], "hands": []},
                       {"market": [], "farmer": ["PASS"], "hands": []}))
    for _ in range(sim.configuration["episodeSteps"]):
        obs0 = sim.obs(0)
        a0 = agent0(obs0)
        obs1 = sim.obs(1)
        a1 = agent1(obs1)
        sim.step(a0, a1)
        frames.append(snap(a0, a1))
    return frames, sim.money(0), sim.money(1)


# ------------------------------------------------------------------- HTML
PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Kaggriculture watch — __TITLE__</title>
<style>
:root{--bg:#0e1116;--panel:#161b22;--line:#2a313c;--fg:#dbe2ea;--dim:#8b98a8;
--green:#3fb950;--red:#f85149;--gold:#d29922;}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);
 font:13px/1.45 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;padding:14px}
h1{font-size:15px;margin:0 0 10px}
.controls{display:flex;flex-wrap:wrap;gap:10px;align-items:center;margin-bottom:10px}
button,select{background:#21262d;color:var(--fg);border:1px solid var(--line);
 border-radius:6px;padding:6px 10px;cursor:pointer;font:inherit}
button:hover{background:#2c333c}
input[type=range]{width:260px}
.moneyline{display:flex;gap:24px;margin:8px 0;flex-wrap:wrap}
.moneyline .m0{color:var(--green);font-weight:700}
.moneyline .m1{color:var(--red);font-weight:700}
.boards{display:flex;gap:16px;flex-wrap:wrap}
.side{background:var(--panel);border:1px solid var(--line);border-radius:8px;padding:10px}
.side h2{font-size:13px;margin:0 0 8px}
.grid{display:grid;grid-template-columns:repeat(10,26px);gap:2px}
.cell{width:26px;height:26px;border-radius:4px;background:#1b222c;
 display:flex;align-items:center;justify-content:center;font-weight:700;color:#0b0e13}
.cell.w{background:#d2a24c}.cell.c{background:#e07a3f}.cell.t{background:#e05a5a}
.cell.s{background:#d95f8a}.cell.m{background:#7cc95f}.cell.x{background:#3a3f47}
.cell.C,.cell.S,.cell.G{background:#b8a06a;color:#161616}
.cell.p,.cell.o{background:#4a3f2c;color:#8a7550}
.cell.#{background:#0a0d11;border:1px dashed #2a313c}.cell.{background:#10161f}
.prices{margin-top:10px;display:flex;gap:8px;flex-wrap:wrap}
.prices span{background:#21262d;border:1px solid var(--line);border-radius:5px;
 padding:2px 7px;white-space:nowrap}
.prices b{color:var(--gold)}
.feed{margin-top:10px;border-top:1px solid var(--line);padding-top:8px}
.feed div{white-space:pre-wrap;word-break:break-word;color:var(--dim)}
.feed b{color:var(--fg)}
.legend{color:var(--dim);margin-top:8px}
.win{color:var(--green)}.lose{color:var(--red)}
</style></head><body>
<h1>Kaggriculture watch — __TITLE__</h1>
<div class="controls">
 <label>seed <select id="seed"></select></label>
 <button id="play">&#9654; play</button>
 <button id="stepB">&#9664; -1</button>
 <button id="stepF">+1 &#9654;</button>
 <button id="dayB">-1 day</button>
 <button id="dayF">+1 day</button>
 <input type="range" id="scrub" min="0" value="0">
 <label>speed <select id="speed"><option value="6">1x</option>
   <option value="3">2x</option><option value="1">6x</option>
   <option value="0">max</option></select></label>
 <span id="clock"></span>
</div>
<div class="moneyline">
 <span class="m0" id="m0">$0</span><span class="m1" id="m1">$0</span>
 <span id="verdict"></span>
</div>
<div class="boards">
 <div class="side"><h2 class="m0">&#9679; OUR BOT (main.py)</h2><div class="grid" id="g0"></div>
   <div class="feed"><b>action</b><div id="a0"></div></div></div>
 <div class="side"><h2 class="m1">&#9679; __OPP__</h2><div class="grid" id="g1"></div>
   <div class="feed"><b>action</b><div id="a1"></div></div></div>
</div>
<div class="prices" id="prices"></div>
<div class="feed" id="shops"></div>
<div class="legend">tiles: w=wheat c=carrot t=tomato s=strawberry m=melon x=weed
 C=cow S=sheep G=goose p/o=empty pasture/coop #=locked .=empty</div>
<script>
const DATA=__DATA__;
const S={};
for(const f of DATA.frames){ (S[f.seed]=S[f.seed]||[]).push(f); }
const seeds=Object.keys(S).map(Number).sort((a,b)=>a-b);
const sel=document.getElementById('seed');
for(const s of seeds){const o=document.createElement('option');o.value=s;o.textContent='seed '+s;sel.appendChild(o);}
let cur=0, playing=false, timer=null, ms=180;
const g0=document.getElementById('g0'), g1=document.getElementById('g1');
const m0=document.getElementById('m0'), m1=document.getElementById('m1');
const a0=document.getElementById('a0'), a1=document.getElementById('a1');
const pr=document.getElementById('prices'), sh=document.getElementById('shops');
const clock=document.getElementById('clock'), scrub=document.getElementById('scrub');
const verdict=document.getElementById('verdict');
function mk(){const d=document.createElement('div');d.className='cell';return d;}
function build(){g0.innerHTML='';g1.innerHTML='';
 for(let i=0;i<100;i++){g0.appendChild(mk());g1.appendChild(mk());}}
build();
function show(){
 const F=S[sel.value]; if(!F) return;
 const f=F[cur];
 scrub.max=F.length-1; scrub.value=cur;
 clock.textContent=`day ${f.day}  hour ${f.hour}`;
 m0.textContent='$'+Math.round(f.m0).toLocaleString();
 m1.textContent='$'+Math.round(f.m1).toLocaleString();
 const diff=Math.round(f.m0-f.m1);
 verdict.textContent= diff>=0? `(leading +$${diff.toLocaleString()})`
                            : `(behind $${diff.toLocaleString()})`;
 verdict.className= diff>=0?'win':'lose';
 const mkTxt=(board,grid)=>{ for(let i=0;i<100;i++){
   const ch=board[i]; const c=grid.children[i];
   c.textContent= ch==='.'?'':ch; c.className='cell '+ch; }};
 mkTxt(f.b0,g0); mkTxt(f.b1,g1);
 a0.textContent=f.a0; a1.textContent=f.a1;
 pr.innerHTML=''; for(const k in f.prices){
   const s=document.createElement('span'); s.innerHTML=k+' <b>$'+f.prices[k]+'</b>'; pr.appendChild(s);}
 sh.innerHTML='<b>town shops:</b> '+ (f.shops.length? f.shops.join(', '):'(none yet)');
}
function setCur(n){const F=S[sel.value]; if(!F)return; cur=Math.max(0,Math.min(F.length-1,n)); show();}
function play(){playing=!playing;
 document.getElementById('play').textContent= playing?'\u23f8 pause':'\u25b6 play';
 if(playing){clearInterval(timer);
  timer=setInterval(()=>{const F=S[sel.value]; if(cur>=F.length-1){play();return;} setCur(cur+1);}, ms);}
 else clearInterval(timer);}
sel.onchange=()=>{cur=0;show();};
document.getElementById('play').onclick=play;
document.getElementById('stepF').onclick=()=>setCur(cur+1);
document.getElementById('stepB').onclick=()=>setCur(cur-1);
document.getElementById('dayF').onclick=()=>setCur(cur+24);
document.getElementById('dayB').onclick=()=>setCur(cur-24);
scrub.oninput=()=>setCur(Number(scrub.value));
document.getElementById('speed').onchange=e=>{ms=[0,60,100,180][Number(e.target.value)];};
show();
</script></body></html>
"""


def build_html(matches, opp_label):
    data = {"frames": []}
    for seed, frames, m0, m1 in matches:
        for f in frames:
            f = dict(f)
            f["seed"] = seed
            data["frames"].append(f)
    js = json.dumps(data, separators=(",", ":"))
    html = PAGE.replace("__DATA__", js).replace("__OPP__", opp_label)
    html = html.replace("__TITLE__", f"main.py vs {opp_label}")
    return html


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opp_label = "V25 TAPE"
    opp_maker = lambda: TapeAgent(load_tape())
    if "--mirror" in sys.argv:
        opp_label = "mirror archetype"
        opp_maker = lambda: v2_agent(ARCHETYPES["mirror"])
    seeds = [int(a) for a in args if a.isdigit()] or [1, 2, 3]

    matches = []
    for seed in seeds:
        print(f"running seed {seed} vs {opp_label} ...", file=sys.stderr)
        frames, m0, m1 = run_match(lambda o: M.agent(o), opp_maker(), seed)
        matches.append((seed, frames, m0, m1))
        print(f"  final: ours ${m0:,.0f}   {opp_label} ${m1:,.0f}   "
              f"margin {m0-m1:+,.0f}", file=sys.stderr)

    html = build_html(matches, opp_label)
    out = os.path.join(HERE, "watch.html")
    with open(out, "w") as fh:
        fh.write(html)
    print(f"wrote {out} ({len(html)/1024:.0f} KB)", file=sys.stderr)
    print(out)


if __name__ == "__main__":
    main()
