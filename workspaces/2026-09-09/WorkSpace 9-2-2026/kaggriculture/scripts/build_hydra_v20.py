"""Build Hydra v20: v18.8 tape economy + race-liquidation market head.

Hybrid of the three lineages:
  - body: v18.8 Adapt-2-Survive tape (the $148k-mean solo economy)
  - head: race-mode liquidation (goose v7e race detection + v11-style
    continuous selling) — SELLS-ONLY overlay, day >= 12, buys untouched
    (v13.1 cash-choreography law), shed-empty self-netting
  - tail: terminal sweep at step >= 717 (v14.1, +$1.1k measured)

Engine facts used:
  - SELL orders with empty shed are rejected (no double-sell risk)
  - sales execute per-unit lockstep; earlier posts => higher prices
  - sells never move units (position/choreography safe)
"""
import os

SRC = "topbots/history/v18_8_main.py"
OUT = "topbots/hydra_v20.py"

src = open(SRC).read()


def rep(old, new, tag):
    global src
    assert old in src, f"[{tag}] anchor missing"
    assert src.count(old) == 1, f"[{tag}] anchor not unique"
    src = src.replace(old, new, 1)
    print("ok:", tag)


RACE_FUNCS = '''

# ---------------- Hydra v20: race liquidation + terminal sweep ----------------

def _hydra_race(obs):
    """True when the opponent is an active bot (not a pass/farm-sitter).
    Engine-legal: obs.farms exposes both farms to each player."""
    try:
        fs = obs.get("farms") or []
        if len(fs) > 1:
            opp = fs[1 - int(obs.get("player") or 0)]
            if opp is None:
                return False
            if (len(opp.get("hands") or []) > 0
                    or (opp.get("money") or 0) > 4200):
                return True
            np_ = 0
            for row in (opp.get("tiles") or []):
                for t in row:
                    if isinstance(t, dict) and (t.get("kind") == "PLANT"
                                                or t.get("animal")):
                        np_ += 1
                        if np_ >= 2:
                            return True
        return False
    except Exception:
        return False


_HYDRA_KEEP_WHEAT = 30  # feed reserve: the tape's animals eat from the shed


def _race_liquidation(obs, action):
    """H2H race mode (day >= 12): liquidate every premium good in the shed
    immediately at market price. Prices decay monotonically when an active
    opponent dumps the same lines; the tape's scripted batch sells land into
    the crash. Liquidating at harvest-time grabs the pre-crash price. The
    tape's own later sells become no-ops (engine rejects empty-shed sells),
    so no debt bookkeeping is needed. BUYS and labor are never touched."""
    try:
        step = int(obs.get("step", 0) or 0)
        day = step // 24
        if day < 12:
            return action
        if not _hydra_race(obs):
            return action
        farm = _farm(obs, _seat(obs))
        n_anim = _count_animal(farm)
        shed = _get(_get(obs, "private", {}) or {}, "shed", {}) or {}
        market_act = [o for o in (list(action.get("market") or []))]
        # protect the tape's own BUY orders (choreography); drop nothing
        slots_used = len(market_act)
        keep_wheat = max(_HYDRA_KEEP_WHEAT, n_anim + 12)
        PREMIUM = ("STRAWBERRY", "MELON", "TOMATO", "CARROT", "EGG", "MILK",
                   "WOOL", "FERTILIZER")
        for item in PREMIUM:
            have = int(shed.get(item, 0) or 0)
            if have <= 0:
                continue
            if slots_used >= 10:
                break
            market_act.append(["SELL", item, have])
            slots_used += 1
        # wheat: sell only the surplus above the feed reserve, at the end
        wh = int(shed.get("WHEAT", 0) or 0)
        if wh > keep_wheat and slots_used < 10:
            market_act.append(["SELL", "WHEAT", wh - keep_wheat])
            slots_used += 1
        action["market"] = market_act[:10]
    except Exception:
        pass
    return action


def _terminal_sweep(obs, action):
    """Final 3 steps: bank nothing, liquidate EVERYTHING (v14.1 Terminal
    Sweep). Any good left in the shed at step 720 is worth $0."""
    try:
        step = int(obs.get("step", 0) or 0)
        if step < 717:
            return action
        shed = _get(_get(obs, "private", {}) or {}, "shed", {}) or {}
        market_act = [o for o in (list(action.get("market") or []))
                      if not (isinstance(o, list) and o and o[0] == "SELL")]
        slots = len(market_act)
        for item in ("STRAWBERRY", "MELON", "WHEAT", "WOOL", "MILK", "EGG",
                     "TOMATO", "CARROT", "FERTILIZER"):
            have = int(shed.get(item, 0) or 0)
            if have > 0 and slots < 10:
                market_act.append(["SELL", item, have])
                slots += 1
        action["market"] = market_act[:10]
    except Exception:
        pass
    return action

'''

rep('''def _base_agent(obs, configuration=None):
    """Adapt-2-Survive: exact route labor + adaptive crops/animals/market."""''',
    RACE_FUNCS + '''

def _base_agent(obs, configuration=None):
    """Hydra v20: tape labor + adaptive layers + race liquidation + sweep."""''',
    "inject race funcs")

rep('''        action = _repay_crash_debt(obs, action)
        action = _adapt_animals(obs, action)
        action = _adapt_crops(obs, action)
        action = _adapt_market(obs, action)
        return _align_hands(_rank_sell_slots(obs, action, configuration), obs)''',
    '''        action = _repay_crash_debt(obs, action)
        action = _adapt_animals(obs, action)
        action = _adapt_crops(obs, action)
        action = _adapt_market(obs, action)
        action = _race_liquidation(obs, action)
        action = _terminal_sweep(obs, action)
        return _align_hands(_rank_sell_slots(obs, action, configuration), obs)''',
    "wire layers")

os.makedirs(os.path.dirname(OUT), exist_ok=True)
compile(src, OUT, "exec")
open(OUT, "w").write(src)
print("built", OUT, len(src), "bytes")
