"""
spy.py — live opponent intelligence (the "know who you're fighting" layer).

Kaggle strips opponent NAMES from the observation (verified: obs contains only
player/farms/private/market/town/day/hour). But it hands us the opponent's
ENTIRE farm every hour: money, all 100 tiles (animals with placed_day, crops
with planted_day), unlocks, hires, plus the shared market inventory.

Behavior = identity. This module measures the opponent live and predicts:
  * WHEN they sell (money-jump histogram -> dump hours)
  * WHAT they dump next 48h (production forecast from their tiles)
  * HOW strong they are (money-curve checkpoints)
  * WHICH ladder archetype they play like (fingerprint vs harvested
    real-ladder episode library — 300+ games pulled from our submissions)

and turns that into concrete counters used by economy.py:
  * pre-sell crash-prone goods 1h BEFORE their dump hour
  * drop price gates when a glut they cause is imminent (holding = $1 later)
  * tilt herd/crop mix away from items they flood
  * expand harder vs weak opponents

All state lives in module-level singleton SPY; agent.py calls SPY.update(obs)
once per hour at the top of agent(). Deterministic, no RNG, O(tiles) per call.
"""

from .board import CROPS, ANIMALS  # engine constants (verbatim)

MARKET_I0 = 10000  # engine MARKET_I0 (verified kaggriculture.py:38)

# ---------------------------------------------------------------------------
# Market crash model (from engine MARKET_PARAMS, exact):
#   price = base - amp * shape(above_func, inv - I0), floored at 1
# "crash units" = units of oversupply (inv - I0) at which price hits ~$1.
# Items with small crash-units are RACE items: whoever sells later eats floor.
# ---------------------------------------------------------------------------
CRASH_UNITS = {
    # item: (approx units over I0 to reach $1, per-unit marginal loss at start)
    "STRAWBERRY": (157, 1.92),   # linear 1.6, T=100
    "MILK":       (151, 2.10),   # linear 1.6, T=122
    "WOOL":       (137, 5.78),   # sq 3.2, T=105 (quadratic: dies fast)
    "MELON":      (254, 0.004),  # sq 3.6, T=300 (flat early, cliff later)
    "TOMATO":     (647, 2.55),   # sqrt .6 T=200 (sqrt: front-loaded loss)
    "FERTILIZER": (2000, 0.20),  # linear .4 T=200; town NEVER consumes it
    "CARROT":     (1400, 1.16),  # sqrt
    "EGG":        (20000, 1.72), # log ~ never crashes (amp drops per unit)
    "WHEAT":      (20000, 0.83), # log ~ never crashes
}
# Items worth racing on (sell before opponent's dump lands):
RACE_ITEMS = {"WOOL", "MILK", "STRAWBERRY", "MELON", "TOMATO", "FERTILIZER"}

# Strength checkpoints (day -> (their money, class)); tuned from harvested
# real-ladder games (see analysis/opponent_library.json).
# Strength checkpoints — calibrated from 313 real ladder episodes
# (analysis/episode_profiles.jsonl, harvested from our submissions' games):
#   top-quartile opponents (avg final $118k): D10 money $11,976
#   bottom-quartile (avg final $45k):         D10 money  $6,286
STRENGTH_D10 = {"weak": 7000, "normal": 12000}

# Real-ladder archetype library (313 episodes, 279 unique opponents; 91% of
# games fall in the top two buckets). Live classification uses ONLY features
# visible in obs (hands, quads, herd, their money curve, fert pressure):
#   FERT_FACTORY   151 games  avg $87,170  10+ hands, fert flood
#   BIG_CREW       135 games  avg $78,798  10+ hands, moderate fert
#   HERD_HEAVY       6 games  avg $55,955  12+ animals, few hands
#   WHEAT_MERCHANT   2 games  avg $44,712  wheat sells > 800
#   STRAWBERRY       1 game   avg $96,431  straw sells > 100
#   PASSISH          5 games  avg $12,250  final < $20k (does nothing)
# Ladder sell timing (revenue-weighted, from opponent money jumps):
#   H1 holds 41.4% of ALL sell revenue (post-overnight-drop dump hour);
#   H17-H23 tail ~26% (continuous sellers). Our sell volley fires every hour,
#   sells-first in the order list, so H0/H1 lands BEFORE their wave; the spy
#   tracks the opponent's actual dump-hour histogram live and pre-sells 1h
#   ahead of THEIR mode (pre_sell_now).
ARCHETYPE_LIB = {
    "FERT_FACTORY":   {"min_hands": 10},
    "BIG_CREW":       {"min_hands": 10},
    "HERD_HEAVY":     {"min_herd": 12},
    "PASSISH":        {"max_d10_money": 5000},
}

# ---------------------------------------------------------------------------
# Town drain model (engine SHOPS + _town_consume, verified):
#   every 4 steps (=6x/day) each unlocked shop consumes 1 of each of its
#   products (2 each for single-product shops); town center consumes 1 of
#   every product except FERTILIZER per day. FERTILIZER HAS ZERO DEMAND —
#   it floors at 494 units sold, always.
#   Sustainable sell rate per item = drain rate; producing above it crashes
#   the shared price (WOOL floors at 58 net units, MILK 75, STRAW 61,
#   MELON 157, EGG/WHEAT effectively never).
# ---------------------------------------------------------------------------
SHOP_PRODUCTS = {
    "BAKERY":         ("EGG", "WHEAT"),
    "PIZZA_SHOP":     ("MILK", "TOMATO", "WHEAT"),
    "BRUNCH_SPOT":    ("EGG", "WHEAT", "STRAWBERRY"),
    "YARN_STORE":     ("WOOL",),
    "ICE_CREAM_SHOP": ("STRAWBERRY", "MILK", "WHEAT"),
    "PET_CAFE":       ("CARROT",),
    "SMOOTHIE_SHOP":  ("STRAWBERRY", "MILK"),
    "FARMERS_MARKET": ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY"),
}
_DRAIN_ITEMS = ("WHEAT", "CARROT", "TOMATO", "STRAWBERRY", "MELON",
                "EGG", "MILK", "WOOL")


def shop_drain(town):
    """Per-item sustainable units/day the town consumes right now.

    Live from obs.town['unlocked_shops'] — the seed's shop RNG decides the
    whole economy (a seed with 0 YARN_STOREs makes sheep near-worthless:
    BT sold exactly 59 wool on such a seed = the floor point).
    """
    drain = {it: 1 for it in _DRAIN_ITEMS}  # town center: 1/day each
    for s in (town or {}).get("unlocked_shops", []) or []:
        prods = SHOP_PRODUCTS.get(s, ())
        for it in prods:
            drain[it] = drain.get(it, 0) + (12 if len(prods) == 1 else 6)
    return drain


def _tile_items(tiles):
    """Census of opponent tiles -> (herd, crops, buildings, planted/crop days)."""
    herd, crops, buildings = {}, {}, {"PASTURE": 0, "COOP": 0}
    for row in tiles:
        for t in row:
            if not isinstance(t, dict):
                continue
            a = t.get("animal")
            if a:
                herd[a] = herd.get(a, 0) + 1
            c = t.get("crop")
            if c:
                crops[c] = crops.get(c, 0) + 1
            k = t.get("kind")
            if k in buildings:
                buildings[k] += 1
    return herd, crops, buildings


def _forecast(opp_farm, day, horizon=48):
    """Units per product the opponent will YIELD within `horizon` hours.

    Uses their visible tiles: animals (placed_day + cadence) and crops
    (planted_day + cadence). Rough by design — we need dump sizing + timing,
    not exact units.
    """
    out = {}
    tiles = opp_farm.get("tiles") or []
    for row in tiles:
        for t in row:
            if not isinstance(t, dict):
                continue
            if t.get("animal"):
                spec = ANIMALS[t["animal"]]
                first, iv = spec["first"], spec["interval"]
                start = t.get("placed_day", 0) + first
                # next yield day strictly after today
                if iv <= 0 or day < start:
                    continue
                k = (day - start) // iv + 1
                nxt = start + k * iv
                if (nxt - day) * 24 <= horizon:
                    p = spec["product"]
                    out[p] = out.get(p, 0) + max(1, spec["max_held"] // 2)
            elif t.get("crop"):
                spec = CROPS[t["crop"]]
                first, iv = spec["first"], spec["interval"]
                start = t.get("planted_day", 0) + first
                if not spec["ongoing"]:
                    # one-shot crops (WHEAT/CARROT/MELON): single yield window
                    if 0 <= start - day <= horizon // 24:
                        p = t["crop"]
                        out[p] = out.get(p, 0) + spec["max_yield"]
                else:
                    if day < start or iv <= 0:
                        continue
                    k = (day - start) // iv + 1
                    nxt = start + k * iv
                    if (nxt - day) * 24 <= horizon:
                        p = t["crop"]
                        out[p] = out.get(p, 0) + spec["max_yield"]
    return out


class Spy:
    """Tracks the opponent across one episode. agent.py: SPY.update(obs)."""

    def __init__(self):
        self.reset()

    def reset(self):
        self.step = -1
        self.money_hist = []            # opponent money per step
        self.sell_jumps = []            # (day, hour, revenue) money-up events
        self.hour_hist = {}             # hour -> total observed sell revenue
        self.unlock_days = []           # (day, n_quads)
        self.hands_hist = []            # (day, n_hands)
        self.prev_herd = {}
        self.first_hire_day = None
        self.prev_money = None
        self.last_board = None

    # ------------------------------------------------------------------ #
    def update(self, obs, board=None):
        step = int(obs.get("step", 0))
        if step <= self.step:
            # new episode (kaggle reuses process across episodes)
            self.reset()
            self.step = step
        elif step == self.step:
            return self
        else:
            self.step = step

        opp = obs["farms"][1 - int(obs.get("player", 0))]
        day, hour = int(obs.get("day", 0)), int(obs.get("hour", 0))
        money = float(opp.get("money", 0))

        if self.prev_money is not None:
            dm = money - self.prev_money
            if dm > 60:  # pure revenue inflow (buys/hires only subtract)
                self.sell_jumps.append((day, hour, dm))
                self.hour_hist[hour] = self.hour_hist.get(hour, 0.0) + dm
        self.prev_money = money
        self.money_hist.append(money)

        nq = len(opp.get("unlocked_quadrants", []))
        if not self.unlock_days or self.unlock_days[-1][1] != nq:
            self.unlock_days.append((day, nq))

        nh = len(opp.get("hands", []))
        if nh > 0 and self.first_hire_day is None:
            self.first_hire_day = day
        self.hands_hist.append((day, nh))

        herd, _, _ = _tile_items(opp.get("tiles") or [])
        self.prev_herd = herd
        self.last_board = board
        self.day, self.hour = day, hour
        self.opp_farm = opp
        self.herd_now = herd
        return self

    # ------------------------------------------------------------------ #
    # WHEN do they sell
    def dump_hours(self, min_revenue=2000):
        """Hours where opponent historically dumped >= min_revenue total."""
        return {h: r for h, r in self.hour_hist.items() if r >= min_revenue}

    def peak_dump_hour(self):
        if not self.hour_hist:
            return None
        return max(self.hour_hist.items(), key=lambda kv: kv[1])[0]

    def sells_in_waves(self):
        """True if their revenue concentrates in few hours (vs continuous)."""
        tot = sum(self.hour_hist.values())
        if tot < 3000:
            return False
        best = max(self.hour_hist.values())
        return best >= 0.30 * tot  # one hour holds >=30% of all revenue

    # WHAT do they dump next 48h
    def dump_forecast(self, horizon=48):
        return _forecast(self.opp_farm, self.day, horizon)

    # HOW strong
    def strength(self):
        """weak | normal | strong — mid-game tempo classification.

        Calibrated on 313 real episodes: revenue-by-D10 separates top from
        bottom only 1.2x (everyone plays similar openings); the real gap is
        D10-D20 revenue rate (1.5x) and crew size (12.5 vs 11.2 hands).
        Money-at-D10 is deliberately NOT used: aggressive bots SPEND cash
        early (breaking_tie holds $436 at D7 yet finishes $130k+).
        """
        if len(self.money_hist) < 24 * 12:
            return "unknown"
        # trailing 5-day revenue rate (positive money jumps only)
        rev5 = sum(r for _, _, r in self.sell_jumps[-120:]) \
            if len(self.sell_jumps) else 0
        hands = max((h for _, h in self.hands_hist), default=0)
        if rev5 > 45000 or hands >= 13:
            return "strong"
        if rev5 < 12000 and hands <= 6:
            return "weak"
        return "normal"

    # WHO are they playing like (real-ladder archetype, live classification)
    def archetype(self, board=None):
        """Match opponent to a harvested real-ladder archetype.

        Features (all visible in obs): hands count, quad count, herd size,
        fert market pressure, their D10 money. Order matters — checked
        against the 313-episode library's distinguishing features.
        """
        hands = max((h for _, h in self.hands_hist), default=0)
        herd = sum(self.herd_now.values()) if self.herd_now else 0
        fert_inv = None
        if board is not None:
            if isinstance(board, dict):
                fert_inv = (board.get("market", {}).get("inventory", {})
                            .get("FERTILIZER", MARKET_I0))
            else:
                fert_inv = board.market_inv("FERTILIZER")
        fert_pressure = (fert_inv - MARKET_I0) if fert_inv is not None else 0
        d10 = self.money_hist[min(len(self.money_hist) - 1, 24 * 10)] \
            if len(self.money_hist) > 24 * 8 else None

        if d10 is not None and d10 < ARCHETYPE_LIB["PASSISH"]["max_d10_money"] \
                and hands <= 2:
            return "PASSISH"
        if hands >= 10 and fert_pressure > 300:
            return "FERT_FACTORY"
        if hands >= 10:
            return "BIG_CREW"
        if herd >= ARCHETYPE_LIB["HERD_HEAVY"]["min_herd"]:
            return "HERD_HEAVY"
        return "SMALL_MIXED"

    # saturation of shared market (both players' cumulative dumps)
    def pressure(self, item, board):
        inv = board.market_inv(item)
        return inv - MARKET_I0  # >0 oversupplied, price below base

    def item_dead(self, item, board):
        """Price effectively crashed; holding/selling later earns ~$1/unit."""
        cu = CRASH_UNITS.get(item, (10000, 1.0))[0]
        return self.pressure(item, board) >= cu * 0.8

    # ------------------------------------------------------------------ #
    # COUNTER RECOMMENDATIONS (consumed by economy.py)
    def pre_sell_now(self, item, board):
        """True => sell ALL of `item` this hour, ahead of an imminent dump.

        Triggers:
          a) next hour is one of their historical dump hours (wave seller), or
          b) they will yield `item` within 24h and item is race-prone, or
          c) item is near crash anyway (holding is dead money).
        """
        if item not in RACE_ITEMS:
            return False
        if self.item_dead(item, board):
            return True
        nxt = (self.hour + 1) % 24
        if nxt in self.dump_hours():
            return True
        fc = self.dump_forecast(24)
        if fc.get(item, 0) >= 3:  # meaningful wave incoming tomorrow
            return True
        return False

    def dump_forecast_by_item(self, horizon=48):
        return self.dump_forecast(horizon)

    # Mix tilt: away from items opponent floods
    def herd_tilt(self, base):
        """Adjust (sheep, cow, goose) targets away from their flood items."""
        f = self.dump_forecast(72)
        # goose=EGG(log curve, never crashes) is the safe tilt
        score = {"SHEEP": f.get("WOOL", 0), "COW": f.get("MILK", 0),
                 "GOOSE": f.get("EGG", 0) * 0.2}
        if not any(score.values()):
            return base
        worst = max(score, key=lambda k: score[k])
        if score[worst] < 8:
            return base
        s, c, g = base
        if worst == "SHEEP" and s > 3: s, g = s - 1, g + 1
        if worst == "COW"   and c > 3: c, g = c - 1, g + 1
        return (s, c, g)

    def expand_greed(self):
        """Opponent weak => we can safely pay for 4th land / extra hires."""
        return self.strength() == "weak"


SPY = Spy()
