#!/usr/bin/env python3
"""
watch.py - run a match and generate a visual, self-contained HTML replay.

Usage (from the workspace root):
    python watch.py                     # astra_live20 (experiment) vs passbot, seed 42
    python watch.py --a v21 --b tetsu   # use bot nicknames
    python watch.py --a war/astra_live20.py --b war/astra_live18.py --seed 101
    python watch.py --list              # list known bots

Requires: kaggle_environments==1.32.7 (auto-installed if missing).
Output:   matches/replay_*.html - open in any browser (fully offline),
          or preview it right in the workspace file viewer.
"""
import argparse
import importlib.util
import io
import contextlib
import json
import os
import subprocess
import sys
import time
import webbrowser

ROOT = os.path.dirname(os.path.abspath(__file__))

BOTS = {
    "live20": "war/astra_live20.py",        # active experiment line
    "live20_1": "war/astra_live20_1.py",    # R34 opening redesign (NE-first + late strb) - LINE BEST
    "live20_2": "war/astra_live20_2.py",    # R35 d0-NE experiment - MEASURED REJECTED, record only
    "live20_3": "war/astra_live20_3.py",    # R37 tape fixes (= v23)
    "live20_4": "war/astra_live20_4.py",    # R38 market control (= v24)
    "live20_5": "war/astra_live20_5.py",    # R39 sell floor + quantity restriction (= v25)
    "live20_6": "war/astra_live20_6.py",    # R40 floor power-check + pocket cap (= v26, LIVE)
    "live20_7": "war/astra_live20_7.py",    # R41 factory-first swap - MEASURED REJECTED, record only
    "live20_8": "war/astra_live20_8.py",    # R42+R45 (= v27/v28, LINE BEST)
    "live20_9": "war/astra_live20_9.py",    # R48 cows-first crash ramp - MEASURED REJECTED both metrics
    "live20_10": "war/astra_live20_10.py",  # R51a final liquidation = v29 LINE BEST (ref 56243015)
    "live20_11": "war/astra_live20_11.py",  # R51b care-crew v2 - MEASURED REJECTED, record only
    "live20_12": "war/astra_live20_12.py",  # R52a merged animal sweep (single traversal)
    "live20_13": "war/astra_live20_13.py",  # R52b work-aware crew floor (on v29)
    "live20_14": "war/astra_live20_14.py",  # R52a merged sweep + R52b crew floor
    "live20_17": "war/astra_live20_17.py",  # R53 endgame leak fixes (seed cap + final-day cargo)
    "live20_18": "war/astra_live20_18.py",  # R53a seed buy cap (endgame leak)
    "live20_19": "war/astra_live20_19.py",  # R53a + opportunistic final-day drop
    "live20_20": "war/astra_live20_20.py",  # R54a price-conditional cow ceiling (herd-mix pivot)
    "live20_21": "war/astra_live20_21.py",  # R55 14th hand (crew 15)
    "live20_22": "war/astra_live20_22.py",  # R56a reserve fertilizer against the opportunity
    "live20_23": "war/astra_live20_23.py",  # R56b fert target cap 8 -> 40 (stock-limited)
    "live20_24": "war/astra_live20_24.py",  # R56c strawberry-only fert priority
    "live20_25": "war/astra_live20_25.py",  # R56d strawberry fert in watered quads only (NW/NE)
    "live20_26": "war/astra_live20_26.py",  # R57 paired WATER+FERT, budget starts 2, +1 per 5 successes
    "live20_27": "war/astra_live20_27.py",  # R57b paired WATER+FERT strawberries only, ratchet on carry
    "live20_28": "war/astra_live20_28.py",  # R58 no strawberry in SW (ever)
    "live20_29": "war/astra_live20_29.py",  # R58b SW = carrot/wheat instead of strawberry
    "live20_30": "war/astra_live20_30.py",  # R59 SE = wheat/carrot, no strawberry
    "live20_31": "war/astra_live20_31.py",  # R59b SE -> wheat/carrot from d20 only
    "live20_32": "war/astra_live20_32.py",  # R60 ripe tiles get stop-priority 0 (routing fix)
    "live20_33": "war/astra_live20_33.py",  # R61 drop only when loaded/shed-near-cap (EOD auto-dump)
    "live20_34": "war/astra_live20_34.py",  # R62 NW scripted animal route (care first, installs after)
    "live20_35": "war/astra_live20_35.py",  # R63 NE wheat d7 + 4/day strb rotate KEEP +6.2k
    "live20_36": "war/astra_live20_36.py",  # R64 NE 2-tile water+fert KEEP +3.0k vs 35
    "live20_37": "war/astra_live20_37.py",  # R65 all NE tick strb fert REJECT -4.2k vs 36
    "live20_38": "war/astra_live20_38.py",  # R66 NE half/rest plant WASH +462 3-3 vs 36
    "live20_39": "war/astra_live20_39.py",  # R67 budgeted all-fert REJECT -8.5k vs 36
    "live20_40": "war/astra_live20_40.py",  # R68 NE packed crop walk KEEP +4.4k vs 36, H2H 10-2
    "live20_41": "war/astra_live20_41.py",  # R69 SW packed crop walk KEEP +1.7k vs 40, H2H 8-4
    "live20_42": "war/astra_live20_42.py",  # R70 SE walk+carrot overlay REJECT H2H 3-9 vs 41
    "live20_43": "war/astra_live20_43.py",  # R71 SE 4-crop mix WASH solo +943 H2H 6-6 vs 41
    "live20_44": "war/astra_live20_44.py",  # R72 SE 4-animal row REJECT H2H 2-10 vs 41
    "live20_45": "war/astra_live20_45.py",  # R73 survival-water after harvest REJECT s42 -8k
    "live20_46": "war/astra_live20_46.py",  # R74 +5 shed-ring sheep REJECT s42 -6.9k
    "live20_47": "war/astra_live20_47.py",  # R75 leftover CARE shed ring WASH +0 (A already books those 4)
    "live20_48": "war/astra_live20_48.py",  # R76 water-not-harvest REJECT s42 -1.8k weeds UP
    "live20_49": "war/astra_live20_49.py",  # R77 strb cap 16 REJECT H2H 3-9 vs 41, s42 -14k
    "live20_50": "war/astra_live20_50.py",  # R78 strb 8 + mix REJECT H2H 4-8, s42 solo -28k
    "live20_51": "war/astra_live20_51.py",  # R79 KEEP H2H 9-3 vs 41; solo 101,894 (-23k vs pass)
    "live20_52": "war/astra_live20_52.py",  # R80 far NW animals REJECT s42 -17k; d7 already 6 animals 0 wheat
    "live20_53": "war/astra_live20_53.py",  # R81 force SE d13 REJECT H2H both seats vs 51 (no coverage)
    "live20_54": "war/astra_live20_54.py",  # R82 lean-in @180 REJECT H2H 5-7 vs 41 (51 was 9-3)
    "live20_55": "war/astra_live20_55.py",  # R83 hybrid+tomato REJECT s42 45k (herd stuck at 4, 2 quads)
    "live20_56": "war/astra_live20_56.py",  # R84 scatter: 1-2 animals on each crop walk, Q prefix, no shed
    "live20_57": "war/astra_live20_57.py",  # R85 town-horizon: every shop type, remaining-days drain
    "live20_58": "war/astra_live20_58.py",  # R86 shop routes + sell-day calendar
    "live20_59": "war/astra_live20_59.py",  # R87 weed-route: survival water first, DIG, far-NW wheat
    "live20_60": "war/astra_live20_60.py",  # R88 SE-float crew: extra 3 Q on owned quads until SE opens
    "live20_61": "war/astra_live20_61.py",  # R89: no-match berry opp, fill SW, NE d7, shop animals
    "live20_62": "war/astra_live20_62.py",  # R90: coverage-first dirt before harvest/fert
    "live20_63": "war/astra_live20_63.py",  # R91: never SE
    "live20_64": "war/astra_live20_64.py",  # R92: d0 berry mix on NW
    "live20_65": "war/astra_live20_65.py",  # R93: 150k opening clone
    "live20_68": "war/astra_live20_68.py",  # R94c: crew cap 13
    "live20_69": "war/astra_live20_69.py",  # R95: fert-skip only d8-20
    "live20_70": "war/astra_live20_70.py",  # R95: 67+hire cap 12
    "live20_71": "war/astra_live20_71.py",  # R96: hold dead wool, no sheep into crash
    "live20_72": "war/astra_live20_72.py",  # R97: keep factory through d22, milk gate
    "live20_73": "war/astra_live20_73.py",  # R98: 1-shop 33 if opp already 30
    "live20_74": "war/astra_live20_74.py",  # R99: strb seed 8/day when factory behind
    "live20_75": "war/astra_live20_75.py",  # R100: no tomato while berry factory behind
    "live20_76": "war/astra_live20_76.py",  # R101: strb cash before carrot while behind
    "live20_77": "war/astra_live20_77.py",  # R102c: goose-2 if opp already 25 berries
    "live20_78": "war/astra_live20_78.py",  # R103: strb d8 if opp already 8 berries
    "live20_79": "war/astra_live20_79.py",  # R104: 150k opening on 78 market brain
    "live20_80": "war/astra_live20_80.py",  # R105: land urgent cuw>=2 WASH +0
    "live20_81": "war/astra_live20_81.py",  # R105b REJECT 9-3 vs 41, broke after land
    "live20_82": "war/astra_live20_82.py",  # R106: new land opens as berries
    "live20_83": "war/astra_live20_83.py",  # R107b melon12 WASH; R107 NW-berries REJECT
    "live20_84": "war/astra_live20_84.py",  # R108 rejects
    "live20_85": "war/astra_live20_85.py",  # R109 KEEP land-berry straw>=160
    "live20_86": "war/astra_live20_86.py",  # R110: extra cow only if milk>=160
    "live20_87": "war/astra_live20_87.py",  # R111 KEEP 8 sheep yarn wool>=160
    "live20_88": "war/astra_live20_88.py",  # R138 snapshot. Use horizon_v1.
    "horizon_v1": "war/horizon_line_v1.py",  # Horizon-Line-V1 posted v43. 10 berries by d6. vs 65 9-3.
    "live20_67": "war/astra_live20_67.py",  # R94b: skip non-berry fert when straw rich
    "live20_66": "war/astra_live20_66.py",  # R94: NE berries d7 micro
    "live19": "war/astra_live19.py",        # v21 chassis (with debug log)
    "v21":    "submit/v21_champion.py",     # LIVE submission (ref 56153311)
    "v20":    "submit/old/v20_champion.py",
    "v19":    "submit/old/v19_champion.py",
    "v58":    "submit/old/v58_champion.py",
    "live18": "war/astra_live18.py",
    "tetsu":  "war/nb3_tetsu_r5.py",
    "elite":  "war/taped.py",            # taped elite route 0 (169k solo class - the ladder wall)
    "pass":   "war/passbot.py",
}

CROPS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
         "EGG", "MILK", "WOOL", "FERTILIZER")


def resolve(spec):
    if spec in BOTS:
        p = os.path.join(ROOT, BOTS[spec])
    else:
        p = os.path.abspath(spec)
        if not os.path.isfile(p):
            # bare nickname: try war/ then submit/ so new experiment files
            # work without editing this table every round
            for sub in ("war", "submit", os.path.join("submit", "old")):
                c = os.path.join(ROOT, sub, spec + ".py")
                if os.path.isfile(c):
                    p = c
                    break
    if not os.path.isfile(p):
        sys.exit("bot not found: %s" % spec)
    return p


def ensure_env():
    try:
        import kaggle_environments  # noqa
        return
    except ImportError:
        pass
    print("installing kaggle_environments==1.32.7 ...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "-q",
                           "kaggle_environments==1.32.7"])


def env_name():
    import kaggle_environments as ke
    base = os.path.join(os.path.dirname(ke.__file__), "envs")
    cand = [x for x in sorted(os.listdir(base))
            if x.startswith("kaggr") and "beginner" not in x]
    if not cand:
        sys.exit("kaggressure env not found")
    return json.load(open(os.path.join(base, cand[0],
                                       cand[0] + ".json")))["name"]


def tile_token(t, day):
    if not isinstance(t, dict):
        return "."
    k = t.get("kind")
    if k == "WEED":
        return "X"
    if k == "PLANT":
        s = t["crop"][0]
        if t.get("watered_today"):
            s += "w"
        if int(t.get("fertilized_until_day", -1)) >= day:
            s += "f"
        y = int(t.get("yield_units", 0) or 0)
        if y:
            s += str(y)
        return s
    if k in ("COOP", "PASTURE"):
        head = "c" if k == "COOP" else "p"
        an = t.get("animal")
        if not an:
            return head
        s = head + an[0] + str(int(t.get("yield_units", 0) or 0))
        if not t.get("fed_today"):
            s += "!"
        return s
    return "?"


def orders_of(step, p):
    a = step[p].get("action")
    out = []
    if isinstance(a, dict):
        for o in a.get("market", []) or []:
            if isinstance(o, list) and len(o) >= 3:
                out.append("%s %s x%s" % (o[0], o[1], o[2]))
            elif isinstance(o, list) and len(o) == 2:
                out.append("%s %s" % (o[0], o[1]))
    return out[:6]


def run_match(path_a, path_b, seed):
    import kaggle_environments as ke
    name = env_name()
    env = ke.make(name, configuration={"seed": seed}, debug=True)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([path_a, path_b])
    frames = []
    for step in env.steps:
        obs = (step[0] or {}).get("observation") or {}
        if "farms" not in obs:
            continue
        day = int(obs.get("day", 0))
        hour = int(obs.get("hour", 0))
        px = (obs.get("market", {}) or {}).get("prices", {}) or {}
        farms = obs["farms"]
        fr = {"d": day, "h": hour,
              "px": {k: px.get(k) for k in CROPS},
              "p": [], "ord": []}
        for f in farms[:2]:
            tiles = []
            for row in f.get("tiles", []):
                for t in row:
                    tiles.append(tile_token(t, day))
            fr["p"].append({
                "m": float(f.get("money", 0)),
                "q": list(f.get("unlocked_quadrants", ["NW"])),
                "n": 1 + len(f.get("hands") or []),
                "t": tiles})
        for p in (0, 1):
            fr["ord"].append(orders_of(step, p))
        frames.append(fr)
    rewards = [float(env.state[0].reward), float(env.state[1].reward)]
    return frames, rewards


HTML = r"""<!doctype html>
<html><head><meta charset="utf-8"><title>Kaggressure replay</title>
<style>
:root{--bg:#14171c;--fg:#dfe6ee;--mut:#8b98a8;--pan:#1c2129;--line:#2c333f}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--fg);font:14px/1.45 -apple-system,"Segoe UI",Roboto,Arial,sans-serif;padding:14px}
h1{font-size:17px;font-weight:650}
#sub{color:var(--mut);font-size:12px;margin:2px 0 10px}
#controls{display:flex;gap:8px;align-items:center;background:var(--pan);border:1px solid var(--line);border-radius:10px;padding:8px 10px;margin-bottom:12px}
button,select{background:#262d38;color:var(--fg);border:1px solid var(--line);border-radius:7px;padding:5px 11px;font-size:13px;cursor:pointer}
button:hover{background:#323b49}
#slider{flex:1;accent-color:#5aa2e8}
#clock{font-variant-numeric:tabular-nums;font-weight:650;min-width:120px;text-align:right}
#boards{display:flex;gap:16px;flex-wrap:wrap;margin-bottom:12px}
.wrap{background:var(--pan);border:1px solid var(--line);border-radius:10px;padding:10px}
.pname{font-weight:650;font-size:14px;margin-bottom:2px}
.stats{color:var(--mut);font-size:12px;margin-bottom:8px;font-variant-numeric:tabular-nums}
.board{display:grid;grid-template-columns:repeat(10,26px);grid-auto-rows:26px;gap:2px;position:relative}
.cell{position:relative;border-radius:4px;background:#6e5136;font-size:10px;display:flex;align-items:center;justify-content:center;color:#10131a;font-weight:700}
.cell .w{position:absolute;left:2px;bottom:2px;width:5px;height:5px;border-radius:50%;background:#3f9dff}
.cell .f{position:absolute;right:2px;top:2px;width:5px;height:5px;border-radius:50%;background:#43d16a}
.lock{position:absolute;background:rgba(8,10,14,.72);border-radius:4px}
#chartwrap{background:var(--pan);border:1px solid var(--line);border-radius:10px;padding:10px;margin-bottom:12px}
#chart{width:100%;height:150px;display:block}
#ticker{background:var(--pan);border:1px solid var(--line);border-radius:10px;padding:10px;font:12px/1.6 ui-monospace,Consolas,monospace;color:var(--mut);min-height:64px;white-space:pre-wrap}
#legend{margin-top:10px;display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--mut)}
.lg{display:flex;gap:5px;align-items:center}
.sw{width:13px;height:13px;border-radius:3px;display:inline-block}
#err{color:#ff7b72;font:12px ui-monospace,monospace;margin-top:8px}
</style></head><body>
<h1 id="title"></h1><div id="sub"></div>
<div id="controls">
  <button id="play">&#9654; play</button>
  <button id="prev">&#8630; -1d</button>
  <select id="speed">
    <option value="500">0.5x</option><option value="250" selected>1x</option>
    <option value="120">2x</option><option value="50">5x</option>
  </select>
  <input id="slider" type="range" min="0" max="0" value="0">
  <span id="clock"></span>
</div>
<div id="boards">
  <div class="wrap"><div class="pname" id="pn0"></div><div class="stats" id="st0"></div><div class="board" id="b0"></div></div>
  <div class="wrap"><div class="pname" id="pn1"></div><div class="stats" id="st1"></div><div class="board" id="b1"></div></div>
</div>
<div id="chartwrap"><svg id="chart" viewBox="0 0 1000 150" preserveAspectRatio="none"></svg></div>
<div id="ticker"></div>
<div id="legend"></div>
<div id="err"></div>
<script>
try{
var R = __DATA__;
var SHED = {"4,4":1,"5,4":1,"4,5":1,"5,5":1};
var COL = {"W":"#e6c86e","C":"#f79b4a","T":"#e15b5b","S":"#f272a8","M":"#66bf66","X":"#4a4339","c":"#c9a27a","p":"#9fc0ae",".":"#6e5136"};
var NAME = {"W":"WHEAT","C":"CARROT","T":"TOMATO","S":"STRAW","M":"MELON"};
var AN = {"G":"GOOSE","C":"COW","S":"SHEEP"};
var cells=[[],[]], locks=[[],[]];
var boards=[document.getElementById("b0"),document.getElementById("b1")];
for(var p=0;p<2;p++){
  for(var i=0;i<100;i++){
    var d=document.createElement("div");d.className="cell";
    var b=document.createElement("span");d.appendChild(b);
    var w=document.createElement("div");w.className="w";w.style.display="none";d.appendChild(w);
    var f=document.createElement("div");f.className="f";f.style.display="none";d.appendChild(f);
    boards[p].appendChild(d);cells[p].push({d:d,b:b,w:w,f:f});
  }
  var qdef=[["NW",0,0],["NE",50,0],["SW",0,50],["SE",50,50]];
  for(var q=0;q<4;q++){
    var L=document.createElement("div");L.className="lock";
    L.style.left=qdef[q][1]+"%";L.style.top=qdef[q][2]+"%";
    L.style.width="50%";L.style.height="50%";L.style.display="none";
    boards[p].appendChild(L);locks[p].push(L);
  }
}
var lockedAt = function(q,x,y){ return q.indexOf((y<5?"N":"S")+(x<5?"W":"E"))<0; };
function frame(i){
  var F=R.frames[i];
  for(var p=0;p<2;p++){
    var P=F.p[p];if(!P)continue;
    var plants=0,animals=0,weeds=0;
    for(var j=0;j<100;j++){
      var x=j%10,y=(j-x)/10,tk=P.t[j],c=cells[p][j];
      var shed=SHED[x+","+y];
      var head=tk.charAt(0);
      if(shed){c.d.style.background="#343a44";c.b.textContent="";c.w.style.display="none";c.f.style.display="none";continue;}
      c.d.style.background=COL[head]||"#6e5136";
      c.w.style.display="none";c.f.style.display="none";
      var txt="";
      if(head==="X"){txt="\u2715";weeds++;}
      else if(head==="."||head==="?"){txt="";}
      else if(head==="W"||head==="C"||head==="T"||head==="S"||head==="M"){
        plants++;
        var k=1,yv=0;
        for(;k<tk.length;k++){var ch=tk.charAt(k);if(ch==="w")c.w.style.display="block";else if(ch==="f")c.f.style.display="block";else break;}
        if(k<tk.length)yv=parseInt(tk.slice(k),10)||0;
        txt=yv>0?String(yv):"";
      } else if(head==="c"||head==="p"){
        if(tk.length>1){animals++;txt=tk.charAt(1);var k2=2,yv2=0;
          for(;k2<tk.length;k2++){var ch2=tk.charAt(k2);if(ch2>="0"&&ch2<="9"){}else break;}
          yv2=parseInt(tk.slice(2,k2),10)||0;
          if(tk.charAt(k2)==="!"){c.d.style.outline="2px solid #ff5f52";}else{c.d.style.outline="none";}
          txt=txt+(yv2>0?yv2:"");
        } else {txt="";c.d.style.outline="none";}
      }
      c.b.textContent=txt;
    }
    var q=P.q||["NW"];
    for(var q2=0;q2<4;q2++){locks[p][q2].style.display="block";}
    for(var q3=0;q3<q.length;q3++){
      var idx=["NW","NE","SW","SE"].indexOf(q[q3]);
      if(idx>=0)locks[p][idx].style.display="none";
    }
    document.getElementById("st"+p).innerHTML=
      "$"+Math.round(P.m).toLocaleString()+" &middot; crew "+P.n+
      " &middot; crops "+plants+" &middot; animals "+animals+" &middot; weeds "+weeds;
  }
  var pxs=[];for(var kk=0;kk<R.crops.length;kk++){var ck=R.crops[kk];pxs.push(ck+" "+(F.px&&F.px[ck]!=null?F.px[ck]:"-"));}
  document.getElementById("ticker").textContent=
    "market: "+pxs.join("   ")+"\nP0 "+(F.ord[0]||[]).join(" | ")+
    (F.ord[0]&&F.ord[0].length?"":"(no market orders)")+
    "\nP1 "+(F.ord[1]||[]).join(" | ")+(F.ord[1]&&F.ord[1].length?"":"(no market orders)");
  document.getElementById("clock").textContent="Day "+F.d+" \u00b7 Hour "+String(F.h).padStart(2,"0");
  document.getElementById("slider").value=i;
  mark.setAttribute("cx",(i/Math.max(1,R.frames.length-1)*1000));
  mark.setAttribute("cy",(150-Math.max(0,F.p[0]?F.p[0].m:0)/R.ymax*140));
}
var svg=document.getElementById("chart");
var mkline=function(idx,color){
  var pts=[],n=R.frames.length;
  for(var i=0;i<n;i++){var m=R.frames[i].p[idx]?R.frames[i].p[idx].m:0;
    pts.push((i/Math.max(1,n-1)*1000)+","+(150-Math.max(0,m)/R.ymax*140));}
  var pl=document.createElementNS("http://www.w3.org/2000/svg","polyline");
  pl.setAttribute("points",pts.join(" "));pl.setAttribute("fill","none");
  pl.setAttribute("stroke",color);pl.setAttribute("stroke-width","2");svg.appendChild(pl);
};
mkline(0,"#5aa2e8");mkline(1,"#e8a35a");
var mark=document.createElementNS("http://www.w3.org/2000/svg","circle");
mark.setAttribute("r","4");mark.setAttribute("fill","#fff");svg.appendChild(mark);
document.getElementById("pn0").textContent=R.names[0]+"  (left)";
document.getElementById("pn1").textContent=R.names[1]+"  (right)";
document.getElementById("title").textContent="Kaggressure \u00b7 "+R.names[0]+" vs "+R.names[1]+" \u00b7 seed "+R.seed;
document.getElementById("sub").textContent="final: "+R.names[0]+" $"+Math.round(R.rewards[0]).toLocaleString()+
  "   |   "+R.names[1]+" $"+Math.round(R.rewards[1]).toLocaleString()+
  "   \u00b7 "+R.frames.length+" steps \u00b7 drag the slider or press play";
var lg=document.getElementById("legend");
var items=[["#e6c86e","wheat"],["#f79b4a","carrot"],["#e15b5b","tomato"],["#f272a8","strawberry"],
  ["#66bf66","melon"],["#4a4339","weed"],["#c9a27a","coop+goose"],["#9fc0ae","pasture+cow/sheep"],
  ["#343a44","shed"],["#6e5136","dirt"],["#3f9dff","\u2022 watered today"],["#43d16a","\u2022 fertilized"],["#ff5f52","outline: unfed animal"]];
for(var li=0;li<items.length;li++){
  var s=document.createElement("span");s.className="sw";s.style.background=items[li][0];
  var t=document.createElement("span");t.textContent=items[li][1];
  var w2=document.createElement("span");w2.className="lg";w2.appendChild(s);w2.appendChild(t);
  lg.appendChild(w2);
}
var slider=document.getElementById("slider");
slider.max=R.frames.length-1;
slider.addEventListener("input",function(){stop();frame(+slider.value);});
var timer=null;
function stop(){if(timer){clearInterval(timer);timer=null;document.getElementById("play").innerHTML="&#9654; play";}}
document.getElementById("play").onclick=function(){
  if(timer){stop();return;}
  var i=+slider.value;if(i>=R.frames.length-1)i=0;
  document.getElementById("play").innerHTML="&#10073;&#10073; pause";
  timer=setInterval(function(){
    i++;if(i>=R.frames.length-1){i=R.frames.length-1;stop();}
    frame(i);
  },+document.getElementById("speed").value);
};
document.getElementById("prev").onclick=function(){stop();var i=+slider.value;var F=R.frames[i];
  var target=F.d-1;if(target<0)target=0;
  for(var j=i;j>=0;j--){if(R.frames[j].d<=target&&R.frames[j].h===0){frame(j);return;}}
  frame(0);};
document.getElementById("speed").onchange=function(){if(timer){stop();document.getElementById("play").click();}};
frame(0);
}catch(e){document.getElementById("err").textContent="render error: "+e;}
</script></body></html>
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--a", default="live20")
    ap.add_argument("--b", default="pass")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--lite", action="store_true",
                    help="half-resolution replay (~400KB - for the "
                         "in-app preview proxy that rejects ~800KB)")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()
    if args.list:
        for k, v in sorted(BOTS.items()):
            print("%-8s %s" % (k, v))
        return
    path_a, path_b = resolve(args.a), resolve(args.b)
    ensure_env()
    print("running %s vs %s (seed %d) ..." %
          (os.path.basename(path_a), os.path.basename(path_b), args.seed))
    t0 = time.time()
    frames, rewards = run_match(path_a, path_b, args.seed)
    print("match done in %.1fs - final: A $%.0f  B $%.0f  (%d frames)" %
          (time.time() - t0, rewards[0], rewards[1], len(frames)))
    if args.lite:
        frames = frames[::2]
    ymax = 1.0
    for f in frames:
        for p in f["p"]:
            ymax = max(ymax, p["m"])
    data = {
        "names": [os.path.basename(path_a), os.path.basename(path_b)],
        "seed": args.seed, "frames": frames, "rewards": rewards,
        "crops": list(CROPS), "ymax": ymax,
    }
    html = HTML.replace("__DATA__", json.dumps(data, separators=(",", ":")))
    os.makedirs(os.path.join(ROOT, "matches"), exist_ok=True)
    out = os.path.join(ROOT, "matches", "replay_%s-vs-%s_s%d_%s%s.html" %
                       (os.path.splitext(os.path.basename(path_a))[0],
                        os.path.splitext(os.path.basename(path_b))[0],
                        args.seed, time.strftime("%H%M%S"),
                        "_lite" if args.lite else ""))
    with open(out, "w") as fh:
        fh.write(html)
    print("replay written: %s  (%.1f KB)" % (out, os.path.getsize(out) / 1024))
    try:
        webbrowser.open("file://" + out)
    except Exception:
        pass


if __name__ == "__main__":
    main()
