"""Transition-tracked verification for astra candidates.

kaggle_environments convention (empirical): steps has ONE entry per turn.
  steps[t].action        = action chosen at turn t
  steps[t].observation   = the PRE-action obs the agent saw at turn t
  steps[t+1].observation = post-state of turn t
"""
import io, contextlib
import kaggle_environments as ke

ENV = "kagg" + "riculture"

def run(bot, seed=42):
    env = ke.make(ENV, configuration={"seed": seed}, debug=False)
    with contextlib.redirect_stdout(io.StringIO()):
        env.run([bot, "/tmp/passbot.py"])
    return env.steps

def obs_at(steps, t):
    return steps[t][0]["observation"]["farms"][0]

def units_at(steps, t):
    act = steps[t][0].get("action") or {}
    o = obs_at(steps, t)
    poss = [tuple(o["farmer"])] + [tuple(p) for p in (o.get("hands") or [])]
    acts = [act.get("farmer")] + list(act.get("hands") or [])
    return acts, poss

def tile_at(steps, t, pos):
    tl = obs_at(steps, t)["tiles"][pos[1]][pos[0]]
    return tl if isinstance(tl, dict) else {}

def verify(bot, seed=42, trace_n=10):
    steps = run(bot, seed)
    n = len(steps)
    assert steps[0][0].get("action") is not None, "steps[0] lacks action?"
    print(f"convention check: {n} steps, one per turn, action at [0] — OK")

    events = []
    for t in range(n):
        day, hour = t // 24, t % 24
        acts, poss = units_at(steps, t)
        for wi, a in enumerate(acts):
            if not a or a[0] != "PLANT" or wi >= len(poss):
                continue
            pos = poss[wi]
            crop = a[1] if len(a) > 1 else "?"
            ok = False
            if t + 1 < n:
                post = tile_at(steps, t + 1, pos)
                ok = (post.get("kind") == "PLANT" and post.get("crop") == crop
                      and post.get("planted_day") == day)
            nxt, nxt_pos = "-", None
            if t + 1 < n:
                a2, p2 = units_at(steps, t + 1)
                if wi < len(a2) and a2[wi]:
                    nxt = a2[wi][0]
                    nxt_pos = p2[wi] if wi < len(p2) else None
            water_conf = False
            if nxt == "WATER" and t + 2 < n:
                pre_w = tile_at(steps, t + 1, pos)
                post_w = tile_at(steps, t + 2, pos)
                water_conf = (pre_w.get("watered_today") is False
                              and post_w.get("watered_today") is True)
            m = (day + 1) * 24
            surv = "n/a"
            if m < n:
                tl = tile_at(steps, m, pos)
                if tl.get("kind") == "WEED":
                    surv = "DIED"
                elif tl.get("kind") == "PLANT" and tl.get("planted_day") == day:
                    surv = "surv(w)" if tl.get("consecutive_unwatered", 9) == 0 else "surv(unw!)"
                else:
                    surv = "harvested/gone"
            events.append(dict(day=day, hour=hour, w=wi, pos=pos, crop=crop,
                               ok=ok, nxt=nxt, nxt_pos=nxt_pos,
                               wconf=water_conf, surv=surv))

    fail_water = noop_water = total_water = 0
    for t in range(n):
        acts, poss = units_at(steps, t)
        for wi, a in enumerate(acts):
            if not a or a[0] != "WATER" or wi >= len(poss):
                continue
            total_water += 1
            pre = tile_at(steps, t, poss[wi])
            if pre.get("kind") != "PLANT":
                fail_water += 1
            elif pre.get("watered_today"):
                noop_water += 1

    att = len(events)
    suc = sum(e["ok"] for e in events)
    fu = sum(1 for e in events if e["ok"] and e["nxt"] == "WATER")
    wconf = sum(1 for e in events if e["ok"] and e["wconf"])
    deaths = sum(1 for e in events if e["surv"] == "DIED")
    unw = sum(1 for e in events if e["surv"] == "surv(unw!)")
    print(f"PLANT attempts: {att}")
    print(f"Successful PLANTs: {suc}")
    print(f"Confirmed next-turn WATER follow-ups: {fu} "
          f"(watered_today False->True transition verified: {wconf})")
    print(f"Failed WATER actions: {fail_water} invalid-target + "
          f"{noop_water} no-op (pre-state already watered), "
          f"of {total_water} total WATERs")
    print(f"Fresh-plant deaths at daily refresh: {deaths} "
          f"(plus {unw} survived-but-unwatered)")
    print(f"\nper-event trace (first {trace_n}):")
    for e in events[:trace_n]:
        print(f"  d{e['day']:>2} h{e['hour']:>2} w{e['w']} {e['pos']} {e['crop']:<10} "
              f"ok={e['ok']} next={e['nxt']}@{e['nxt_pos']} water_conf={e['wconf']} {e['surv']}")
    anom = [e for e in events if (not e["ok"]) or e["surv"] in ("DIED", "surv(unw!)")]
    print(f"\nanomalies ({len(anom)}):")
    for e in anom[:12]:
        print(f"  d{e['day']} h{e['hour']} w{e['w']} {e['pos']} {e['crop']} "
              f"ok={e['ok']} next={e['nxt']} {e['surv']}")
    f = obs_at(steps, n - 1)
    print(f"\nfinal: ${f['money']:,.0f}  crew {len(f.get('hands', []))}  "
          f"quads {f.get('unlocked_quadrants')}")

if __name__ == "__main__":
    import sys
    verify(sys.argv[1] if len(sys.argv) > 1 else "astra_live2.py")
