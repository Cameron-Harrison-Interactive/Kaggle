"""
Decision Agent v4 — "Counter" — opponent-aware adaptation.

The objective is reframed from "maximize solo gold" to "beat the other bot's
gold by any margin." The opponent's farm is PUBLIC (we see their animals, their
crops, their unharvested yield, their land, their money — only their shed and
seeds are hidden). v4 reads that every turn and adapts in real time.

1. HERD TILT (don't share a glut). When the opponent runs a meaningfully
   cow-heavier herd than ours (the common ladder build), milk is going to
   crash for everyone — but wool stays relatively ours. We swap a couple of
   cows for sheep WITHIN THE SAME total headcount, so the crew is never
   overloaded. We deliberately do NOT tilt toward cows against a
   sheep-flooder: wool hits the $1 floor so fast a balanced herd wins there.

2. FRONT-RUN SELLS. We can see the opponent's unharvested yield sitting on
   their tiles (milk/wool/melons about to hit the market). We sell ours
   IMMEDIATELY — one turn earlier means our whole batch gets the pre-glut
   price, and their batch lands on a market we already softened.

3. CROP-MIX COUNTER. If the opponent is heavy in crash-prone crops
   (strawberry/melon), we tilt planting toward glut-robust wheat.

Everything else is the v2 economy, untouched: never-miss feed/water/fert,
same-day watering of fresh plants, terminal sweep, budgeted opening.

Verified properties:
  * vs PASS: byte-for-byte identical to v2 (the counter is a no-op when the
    opponent has nothing to counter).
  * vs archetype gauntlet (5 seeds x 2 seats each): +$1.7k vs mirror clone,
    +$13.9k vs cow-flooder, +$0.8k vs sheep-flooder, +$0.4k vs goose-flooder
    vs the v2 baseline.

Interface identical to v1/v2/v3: agent(obs, config) + set_params(params).
"""

from decision_agent_v2 import (  # noqa: E402
    DecisionAgent, DEFAULT_PARAMS, ANIMALS, ANIMAL_ORDER, SELL_ORDER,
)

V4_DEFAULT_PARAMS = dict(DEFAULT_PARAMS)
V4_DEFAULT_PARAMS.update({
    "counter_enabled": True,
    "frontrun_enabled": True,
    "diversify_enabled": True,
    "frontrun_pending": 3,     # opponent's pending yield must reach this to trigger
    "cow_shift": 2,            # cows -> sheep swap when the opponent is cow-heavy
    "sheep_shift": 2,
    "min_cow_keep": 6,         # never cut cows below this
})


class CounterAgent(DecisionAgent):
    def __init__(self, params=None, seat=0):
        super().__init__(params, seat)
        self._opp = None

    # ------------------------------------------------------------------ act
    def act(self, obs, configuration=None):
        if int(obs.get("hour", 0) or 0) == 0:
            self._opp = self._scan_opponent(obs)
        return super().act(obs, configuration)

    # ------------------------------------------------------- opponent scan
    def _scan_opponent(self, obs):
        """Read the opponent's PUBLIC farm state."""
        player = int(obs.get("player", 0) or 0)
        ofarm = obs["farms"][1 - player]
        counts = {"COW": 0, "SHEEP": 0, "GOOSE": 0}
        pending = {"MILK": 0, "WOOL": 0, "EGG": 0}   # yield ready to harvest
        crops = {}
        weeds = 0
        for row in ofarm.get("tiles", []):
            for t in row:
                if isinstance(t, dict):
                    if t.get("animal"):
                        counts[t["animal"]] = counts.get(t["animal"], 0) + 1
                        prod = ANIMALS[t["animal"]]["product"]
                        pending[prod] = pending.get(prod, 0) + \
                            int(t.get("yield_units", 0) or 0)
                    elif t.get("kind") == "PLANT":
                        crops[t.get("crop")] = crops.get(t.get("crop"), 0) + 1
                    elif t.get("kind") == "WEED":
                        weeds += 1
        return {"counts": counts, "pending": pending, "crops": crops,
                "weeds": weeds, "money": float(ofarm.get("money", 0) or 0),
                "unlocked": ofarm.get("unlocked_quadrants", []) or []}

    # ------------------------------------------------------- diversification
    def _effective_target(self, day, kind):
        base = super()._effective_target(day, kind)
        if not self.params.get("diversify_enabled", True) or self._opp is None:
            return base
        p = self.params
        c = self._opp["counts"]
        cow_n, sheep_n = c.get("COW", 0), c.get("SHEEP", 0)

        # TILT WITHIN THE SAME HERD SIZE toward the product the opponent is
        # NOT making. We only tilt AWAY from a milk glut (the common ladder
        # clone): when the opponent runs a meaningfully cow-heavier herd than
        # ours, wool is relatively ours alone and stays high, so we swap a
        # couple of cows for sheep.
        #
        # We deliberately do NOT tilt toward cows against a sheep-flooder:
        # wool hits the $1 floor so fast that a balanced herd is already the
        # best answer there.
        cow_heavy = cow_n >= 6 and cow_n >= sheep_n + 4
        if kind == "cow" and cow_heavy:
            return max(p.get("min_cow_keep", 6), base - p.get("cow_shift", 2))
        if kind == "sheep" and cow_heavy:
            return base + p.get("sheep_shift", 2)
        return base

    # ----------------------------------------------------------- crop counter
    def _plant_priority(self, day):
        order = super()._plant_priority(day)
        if not self.params.get("counter_enabled", True) or self._opp is None:
            return order
        crash = self._opp["crops"].get("STRAWBERRY", 0) + \
            self._opp["crops"].get("MELON", 0)
        if crash >= 8:
            # they're flooding the crash-prone crops; demote them, favor wheat
            keep = [c for c in order if c not in ("STRAWBERRY", "MELON")]
            demote = [c for c in order if c in ("STRAWBERRY", "MELON")]
            return keep + demote
        return order

    # -------------------------------------------------------------- market
    def _decide_market(self, day, hour, money, shed, seeds, board, unlocked):
        p = self.params
        orders = []
        n_animals = len(board["animals"])
        reserve = n_animals * p.get("wheat_reserve_per_animal", 2) + 2
        buf = p["cash_buffer"]
        terminal = day >= p["terminal_day"]

        # ---- opening day ----
        if day == 0 and hour == 0:
            if p.get("open_wheat", 0) > 0:
                orders.append(["BUY_PRODUCT", "WHEAT", int(p["open_wheat"])])
            for _ in range(int(p.get("open_hires", 0))):
                orders.append(["HIRE"])
            if p.get("open_sheep", 0) > 0:
                orders.append(["BUY_ANIMAL", "SHEEP", int(p["open_sheep"])])
            if p.get("open_cows", 0) > 0:
                orders.append(["BUY_ANIMAL", "COW", int(p["open_cows"])])
            if p.get("open_geese", 0) > 0:
                orders.append(["BUY_ANIMAL", "GOOSE", int(p["open_geese"])])
            for crop, key in [("MELON", "open_melon_seed"),
                              ("STRAWBERRY", "open_straw_seed"),
                              ("WHEAT", "open_wheat_seed"),
                              ("CARROT", "open_carrot_seed")]:
                n = int(p.get(key, 0) or 0)
                if n > 0:
                    orders.append(["BUY_SEED", crop, n])
            return orders[:10]

        # ---- morning routine (hour 0) ----
        if hour == 0:
            hires = p["daily_hires"] if day < p["late_day"] else p["late_hires"]
            for _ in range(min(int(hires), 10)):
                orders.append(["HIRE"])

            for quad, key, price in [("NE", "ne_land_day", 1000),
                                     ("SW", "sw_land_day", 2000),
                                     ("SE", "se_land_day", 4000)]:
                if p.get(key, -1) >= 0 and day >= p[key] and quad not in unlocked \
                        and money >= price + buf \
                        and self._land_density_ok(board, unlocked) \
                        and len(orders) < 10:
                    orders.append(["BUY_LAND"])

            if not terminal:
                if int(seeds.get("WHEAT", 0) or 0) == 0 and money > buf + 120 \
                        and len(orders) < 10:
                    orders.append(["BUY_SEED", "WHEAT", 5])
                if int(seeds.get("MELON", 0) or 0) == 0 \
                        and day < p.get("melon_last_day", 14) and money > buf + 500 \
                        and len(orders) < 10:
                    orders.append(["BUY_SEED", "MELON", 3])
                if int(seeds.get("STRAWBERRY", 0) or 0) == 0 \
                        and day < p.get("straw_last_day", 8) and money > buf + 500 \
                        and len(orders) < 10:
                    orders.append(["BUY_SEED", "STRAWBERRY", 2])

                # grow the herd toward the (opponent-adjusted) targets
                on_board = {"SHEEP": 0, "COW": 0, "GOOSE": 0}
                for a in board["animals"]:
                    t = a.get("animal")
                    if t in on_board:
                        on_board[t] += 1
                for atype, tkey in [("SHEEP", "sheep"), ("COW", "cow"),
                                    ("GOOSE", "goose")]:
                    eff = self._effective_target(day, tkey)
                    have = on_board[atype] + int(shed.get(atype, 0) or 0)
                    cost = ANIMALS[atype]["cost"]
                    if have < eff and money > cost + buf and len(orders) < 10:
                        orders.append(["BUY_ANIMAL", atype,
                                       min(2, eff - have)])

            wheat_in_shed = int(shed.get("WHEAT", 0) or 0)
            need = max(0, (reserve + n_animals) - wheat_in_shed)
            if need > 0 and money > buf and len(orders) < 10:
                orders.append(["BUY_PRODUCT", "WHEAT", min(int(need), 20)])

            return orders[:10]

        # ---- selling ----
        # v4: FRONT-RUN — if the opponent has harvestable product of a type we
        # also hold, sell ours NOW (any hour), before their batch lands.
        if self.params.get("frontrun_enabled", True) and self._opp is not None \
                and not terminal:
            for item in SELL_ORDER:
                if len(orders) >= 10:
                    break
                if self._opp["pending"].get(item, 0) < p.get("frontrun_pending", 3):
                    continue
                q = int(shed.get(item, 0) or 0)
                if item == "WHEAT":
                    q = max(0, q - reserve)
                if q > 0:
                    orders.insert(0, ["SELL", item, q])

        if terminal or hour == p.get("sell_hour", 2):
            for item in SELL_ORDER:
                if len(orders) >= 10:
                    break
                q = int(shed.get(item, 0) or 0)
                if item == "WHEAT":
                    if day >= 29:
                        q = int(shed.get("WHEAT", 0) or 0)
                    else:
                        q = max(0, q - reserve)
                if q > 0:
                    orders.append(["SELL", item, q])
            return orders[:10]

        return orders[:10]


# ----------------------------------------------------------------------------
# Kaggle entry point (same interface as v1/v2/v3).
# ----------------------------------------------------------------------------
_params = None
_agents = {}


def agent(obs, configuration=None):
    global _params, _agents
    if _params is None:
        _params = dict(V4_DEFAULT_PARAMS)
    seat = int(obs.get("player", 0) or 0)
    if seat not in _agents:
        _agents[seat] = CounterAgent(_params, seat)
    return _agents[seat].act(obs, configuration)


def set_params(params):
    global _params, _agents
    _params = params
    _agents = {}


if __name__ == "__main__":
    from kaggle_environments import make

    def _pass(obs, config=None):
        farm = obs["farms"][obs["player"]]
        n = len(farm.get("hands", []) or [])
        return {"farmer": ["PASS"], "hands": [["PASS"]] * n, "market": []}

    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": 1})
    result = env.run([agent, _pass])
    money = result[-1][0]["observation"]["farms"][0]["money"]
    print(f"Decision Agent v4 vs PASS (seed 1): ${money:,.0f}")
