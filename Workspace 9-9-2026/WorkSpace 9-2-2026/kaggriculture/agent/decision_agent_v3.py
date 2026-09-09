"""
Decision Agent v3 — "Adaptive" — the live thinking bot.

Builds on decision_agent_v2 (the clean-room reactive economy) and adds the two
planning layers from scripts/planner.py, wired into the live loop:

1. CAPACITY-AWARE (every morning, hour 0):
   Estimates today's workload (feed/water/fert/harvest/care/dig) against the
   crew's 24-hours-each capacity.
     * OVERLOADED  -> drop CARE first, then PLANT (critical tasks always run),
                      and hire extra hands (cheap: fib costs 5/8/13...) if
                      money allows.
     * SLACK       -> consider ONE extra animal, but only if the lookahead
                      says it pays (below).

2. LOOKAHEAD (what-if before big buys):
   Reconstructs the live game state (sim.GameSim.from_obs), clones it, and
   simulates "buy a cow / buy a sheep" a few days forward with the opponent
   frozen. Commits only when the simulated outcome beats doing nothing.
   Uses terminal_value so short horizons still see an animal's future worth.

Everything is gated so a live match never crashes and never blows the time
limit: lookahead runs at most once per day (hour 0), only when there is slack
and money, every `lookahead_every` days, with a try/except fallback to the
plain v2 behaviour. If the sim/planner modules can't be imported (e.g. a
single-file submission), the agent degrades gracefully to v2 + capacity logic.

Params = v2 DEFAULT_PARAMS plus:
    worker_cap            max workers/hands we will ever hire per day
    slack_buy_threshold   buy an animal only when daily slack > this fraction
    lookahead_enabled     master switch for the what-if layer
    lookahead_days        simulation horizon (days)
    lookahead_every       run the what-if at most every N days
    lookahead_min_money   skip lookahead when cash is below this
    animal_headroom       allow total animals up to final targets + this
"""

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_SCRIPTS = os.path.join(_HERE, "..", "scripts")
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

from decision_agent_v2 import (  # noqa: E402
    DecisionAgent, DEFAULT_PARAMS, ANIMALS, ANIMAL_ORDER, SELL_ORDER,
    BASE_PRICE, manhattan,
)

try:
    from sim import GameSim  # noqa: E402
    import planner as _planner  # noqa: E402
    HAVE_SIM = True
except Exception:  # pragma: no cover - graceful degradation
    HAVE_SIM = False

# fib hire costs (farmHandCostMult=1): hire #k today costs FIB[k], FIB[0]=1
FIB = [1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89, 144, 233]


V3_DEFAULT_PARAMS = dict(DEFAULT_PARAMS)
V3_DEFAULT_PARAMS.update({
    "extra_hires_max": 3,
    "slack_buy_threshold": 0.45,
    "lookahead_enabled": True,
    "lookahead_days": 10,
    "lookahead_every": 2,
    "lookahead_min_money": 900,
    "animal_headroom": 2,
    "animal_min_net": 150,     # direct-estimator margin ($) to add an animal
    "decision_mode": "direct",  # "direct" (net-value calc) or "whatif" (rollout)
    "expansion_enabled": False,  # master switch for opportunistic expansion
    "debug_plan": False,
})


class AdaptiveAgent(DecisionAgent):
    def __init__(self, params=None, seat=0):
        super().__init__(params, seat)
        self._plan = {}
        self._obs = None
        self._last_lookahead_day = -99

    # ----------------------------------------------------------------- act
    def act(self, obs, configuration=None):
        self._obs = obs
        day = int(obs.get("day", 0) or 0)
        hour = int(obs.get("hour", 0) or 0)
        if hour == 0:
            self._plan = self._make_day_plan(obs)
        return super().act(obs, configuration)

    # -------------------------------------------------------- day planning
    # Hands are cleared at end of day, so at hour 0 the board has only the
    # farmer. Morning hires spawn on the shed-access tiles in NWSE order, so
    # the planner seeds worker positions with the farmer + planned spawns.
    _SPAWN_TILES = [(5, 4), (4, 5), (5, 5), (4, 4)]

    def _estimate_workload(self, obs, board, worker_positions):
        def steps_for(tasks):
            tot = 0
            for (tx, ty) in tasks:
                tot += min(manhattan(w, (tx, ty)) for w in worker_positions) + 1
            return tot

        feed = [(a["x"], a["y"]) for a in board["animals"] if not a["fed_today"]]
        water = [(pl["x"], pl["y"]) for pl in board["plants"] if not pl["watered_today"]]
        fert = [(a["x"], a["y"]) for a in board["animals"] if a["fertilizer_available"]]
        care = [(a["x"], a["y"]) for a in board["animals"] if not a["cared_today"]]
        harvest = [(pl["x"], pl["y"]) for pl in board["plants"] if pl["yield_units"] > 0] + \
                  [(a["x"], a["y"]) for a in board["animals"] if a["yield_units"] >= 2]
        dig = list(board["weeds"])
        est = {
            "feed": steps_for(feed), "water": steps_for(water),
            "fert": steps_for(fert), "care": steps_for(care),
            "harvest": steps_for(harvest), "dig": steps_for(dig),
        }
        est["critical"] = est["feed"] + est["water"] + est["fert"]
        return est

    def _make_day_plan(self, obs):
        p = self.params
        player = int(obs.get("player", 0) or 0)
        farm = obs["farms"][player]
        day = int(obs.get("day", 0) or 0)
        money = float(farm.get("money", 0) or 0)

        board = self._scan_board(farm["tiles"],
                                 set(farm.get("unlocked_quadrants", []) or []))
        planned = p["daily_hires"] if day < p["late_day"] else p["late_hires"]

        # worker positions: farmer + planned hires at their spawn tiles
        workers = [tuple(farm.get("farmer", [4, 4]))]
        for k in range(planned):
            workers.append(self._SPAWN_TILES[k % len(self._SPAWN_TILES)])

        est = self._estimate_workload(obs, board, workers)
        critical = est["critical"]
        capacity = len(workers) * 24

        plan = {"extra_hires": 0, "consider_animal": False,
                "over": 0, "slack": 0, "critical": critical, "capacity": capacity}

        # Defensive hiring: if the CRITICAL work (feed/water/fert — the
        # never-miss jobs) alone exceeds capacity, hire extra hands (cheap)
        # until it fits. This is the only place we touch hiring; the priority
        # chain already handles the flexible work (care/plant/dig) gracefully.
        hires_today = int(farm.get("hires_today", 0) or 0)
        max_extra = p.get("extra_hires_max", 3)
        while critical > capacity and plan["extra_hires"] < max_extra:
            idx = hires_today + planned + plan["extra_hires"]
            cost = FIB[idx] if idx < len(FIB) else FIB[-1]
            if money < cost + p["cash_buffer"]:
                break
            workers.append(self._SPAWN_TILES[len(workers) % len(self._SPAWN_TILES)])
            plan["extra_hires"] += 1
            capacity += 24
            est = self._estimate_workload(obs, board, workers)
            critical = est["critical"]

        plan["over"] = max(0, critical - capacity)
        plan["slack"] = max(0, capacity - critical)

        # Expansion: comfortable margin on the critical work means we can
        # absorb one more animal's daily chores — let the what-if decide.
        if plan["slack"] > p.get("slack_buy_threshold", 0.45) * capacity \
                and 3 <= day < p.get("terminal_day", 28):
            plan["consider_animal"] = True
        if p.get("debug_plan"):
            print(f"[v3 day {day}] workers={len(workers)} cap={capacity} "
                  f"crit={critical} slack={plan['slack']} "
                  f"extra_hires={plan['extra_hires']} consider_animal={plan['consider_animal']}")
        return plan

    # ------------------------------------------------------------ market
    def _decide_market(self, day, hour, money, shed, seeds, board, unlocked):
        p = self.params
        orders = []
        n_animals = len(board["animals"])
        reserve = n_animals * p.get("wheat_reserve_per_animal", 2) + 2
        buf = p["cash_buffer"]
        terminal = day >= p["terminal_day"]
        plan = getattr(self, "_plan", {}) or {}

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
            # v3: capacity-driven extra hires
            for _ in range(min(plan.get("extra_hires", 0), 10 - len(orders))):
                orders.append(["HIRE"])

            # land (density-gated as in v2)
            for quad, key, price in [("NE", "ne_land_day", 1000),
                                     ("SW", "sw_land_day", 2000),
                                     ("SE", "se_land_day", 4000)]:
                if p.get(key, -1) >= 0 and day >= p[key] and quad not in unlocked \
                        and money >= price + buf \
                        and self._land_density_ok(board, unlocked) \
                        and len(orders) < 10:
                    orders.append(["BUY_LAND"])

            if not terminal:
                # seed rebuys
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

                # herd toward ramp targets
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
                        orders.append(["BUY_ANIMAL", atype, min(2, eff - have)])

                # v3: opportunistic expansion — only if the expected net value
                # of an extra animal (or extra hands) is clearly positive.
                if plan.get("consider_animal") and len(orders) < 10 \
                        and p.get("expansion_enabled", False):
                    pick = self._decide_expansion(day, money)
                    if pick == "hands":
                        for _ in range(2):
                            if len(orders) < 10:
                                orders.append(["HIRE"])
                    elif pick in ANIMALS:
                        orders.append(["BUY_ANIMAL", pick, 1])

            # wheat top-up
            wheat_in_shed = int(shed.get("WHEAT", 0) or 0)
            need = max(0, (reserve + n_animals) - wheat_in_shed)
            if need > 0 and money > buf and len(orders) < 10:
                orders.append(["BUY_PRODUCT", "WHEAT", min(int(need), 20)])

            return orders[:10]

        # ---- selling ----
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

    # ------------------------------------------------------------ lookahead
    def _avg_sell_price(self, product, obs, units):
        """Average price we'd get selling `units` of `product` one at a time
        into the CURRENT market, using the engine's exact price function.
        This is the price-elasticity term: each unit we dump moves the price
        down (premiums crash hard), so the marginal animal's produce is worth
        far less than the current sticker price once we're producing at scale."""
        from kaggle_environments.envs.kaggriculture import kaggriculture as K
        market = obs["market"]
        inv = int(market["inventory"].get(product, 10000))
        params = market.get("params")
        if units <= 0:
            return 0.0
        total = 0.0
        for _ in range(int(units)):
            total += K.market_price(product, inv, params)
            inv += 1
        return total / int(units)

    def _animal_net_value(self, animal, obs):
        """Marginal value of buying one more `animal` right now.

        Prices future yields/fertilizer at the price we'd actually receive
        AFTER dumping our whole herd's remaining production into the market
        (exact price function), and charges feed at the current wheat price.

        Reads the LIVE market so it adapts per match — the "knows if adding
        an animal pays" answer with price elasticity included.
        """
        a = ANIMALS[animal]
        day = int(obs.get("day", 0) or 0)
        prices = obs["market"]["prices"]

        n_new = 0
        t = day + a["first"]
        while t < 30:
            n_new += 1
            t += a["interval"]
        remaining_days = 30 - day

        # count the existing herd's remaining production of the same product
        board = self._scan_board(
            obs["farms"][obs["player"]]["tiles"],
            set(obs["farms"][obs["player"]].get("unlocked_quadrants", []) or []))
        existing = 0
        for an in board["animals"]:
            if ANIMALS.get(an.get("animal"), {}).get("product") == a["product"]:
                tt = day + ANIMALS[an["animal"]]["first"]
                while tt < 30:
                    existing += 1
                    tt += ANIMALS[an["animal"]]["interval"]

        product_price = self._avg_sell_price(a["product"], obs, n_new + existing)
        revenue = n_new * product_price

        # fertilizer: 1/animal/day; price also gluts
        n_fert_animals = len(board["animals"]) + 1
        fert_units = n_fert_animals * remaining_days
        fert_price = self._avg_sell_price("FERTILIZER", obs, fert_units)
        fert = remaining_days * fert_price

        wheat_price = float(prices.get("WHEAT", BASE_PRICE["WHEAT"]))
        feed = remaining_days * wheat_price

        return revenue + fert - feed - a["cost"]

    def _decide_expansion(self, day, money):
        """Choose whether (and what) to add today, by expected net value."""
        p = self.params
        obs = getattr(self, "_obs", None)
        if obs is None:
            return None
        if p.get("decision_mode", "direct") == "whatif":
            return self._lookahead_expand(day, money)

        margin = p.get("animal_min_net", 150)
        best, best_v = None, margin
        for animal in ("SHEEP", "COW", "GOOSE"):
            v = self._animal_net_value(animal, obs)
            if v > best_v:
                best_v, best = v, animal
        if best and p.get("debug_plan"):
            print(f"[v3 day {day}] direct: best={best} net=${best_v:,.0f}")
        return best

    def _reflex_agent(self):
        # The rollout policy is the plain v2 reactive economy (no recursive
        # lookahead). Use the live agent's own v2-level params so the rollout
        # matches how we actually play apart from the decision under test.
        r = DecisionAgent(dict(self.params), seat=0)
        return lambda obs: r.act(obs)

    def _lookahead_expand(self, day, money):
        p = self.params
        if not HAVE_SIM or not p.get("lookahead_enabled", True):
            return None
        if money < p.get("lookahead_min_money", 900):
            return None
        if day - self._last_lookahead_day < p.get("lookahead_every", 2):
            return None
        obs = getattr(self, "_obs", None)
        if obs is None:
            return None
        try:
            self._last_lookahead_day = day
            sim = GameSim.from_obs(obs, seed=12345)
            # Simulate to the END of the game so an animal's full payoff
            # (milk/wool/eggs) is captured, not just its purchase cost.
            horizon = 30 - day
            reflex = self._reflex_agent()

            options = []
            on_board = {"SHEEP": 0, "COW": 0, "GOOSE": 0}
            for a in self._scan_board(
                    obs["farms"][obs["player"]]["tiles"],
                    set(obs["farms"][obs["player"]].get("unlocked_quadrants", []) or []))["animals"]:
                t = a.get("animal")
                if t in on_board:
                    on_board[t] += 1
            shed_animals = sum(int((obs.get("private") or {}).get("shed", {}).get(a, 0) or 0)
                               for a in ANIMAL_ORDER)
            cap = p.get("final_sheep", 4) + p.get("final_cow", 10) + \
                  p.get("final_goose", 0) + p.get("animal_headroom", 2)
            if sum(on_board.values()) + shed_animals < cap:
                options.append(("cow", _planner.option_buy_animal("COW", 1, day=day)))
                options.append(("sheep", _planner.option_buy_animal("SHEEP", 1, day=day)))
                options.append(("goose", _planner.option_buy_animal("GOOSE", 1, day=day)))
            options.append(("hands", _planner.option_extra_hires(2, days=(day,))))

            results = _planner.what_if(sim, horizon, options, agent0=reflex,
                                       verbose=False, terminal_value=False,
                                       opp_pass=True)
            base = results[0][1]
            best, best_d = None, 0
            for label, val, delta in results[1:]:
                if delta > best_d and delta > 0:
                    best_d, best = delta, label
            if p.get("debug_plan") and best:
                print(f"[v3 lookahead day {day}] best={best} (+{best_d:,.0f})")
            return best
        except Exception:
            return None

    # ------------------------------------------------------------ worker
    def _decide_worker(self, pos, inv, board, shed, seeds, day, hour, claims):
        # Identical priority chain to v2 — critical work first, flexible work
        # after. The capacity layer only adjusts HIRING and BUYING; the chain
        # itself already degrades gracefully when a day is overloaded.
        # 0. carrying an animal -> place it
        for atype in ANIMAL_ORDER:
            if int(inv.get(atype, 0) or 0) > 0:
                return self._act_place_animal(pos, atype, board, claims)
        # 1. emergency feed
        a = self._act_feed(pos, inv, board, shed, claims, True)
        if a: return a
        # 2. emergency water
        a = self._act_water(pos, board, claims, True)
        if a: return a
        # 3. herd progress
        a = self._act_start_herd(pos, inv, board, shed, day, claims)
        if a: return a
        # 4. feed
        a = self._act_feed(pos, inv, board, shed, claims, False)
        if a: return a
        # 5. water
        a = self._act_water(pos, board, claims, False)
        if a: return a
        # 6. harvest
        a = self._act_harvest(pos, board, day, claims)
        if a: return a
        # 7. plant
        a = self._act_plant(pos, board, seeds, day, hour, claims)
        if a: return a
        # 8. collect fertilizer
        a = self._act_collect(pos, board, claims)
        if a: return a
        # 9. care
        a = self._act_care(pos, board, claims)
        if a: return a
        # 10. dig weeds
        a = self._act_dig(pos, board, claims)
        if a: return a
        return ["PASS"]


# ----------------------------------------------------------------------------
# Kaggle entry point (same interface as v1/v2).
# ----------------------------------------------------------------------------
_params = None
_agents = {}


def agent(obs, configuration=None):
    global _params, _agents
    if _params is None:
        _params = dict(V3_DEFAULT_PARAMS)
    seat = int(obs.get("player", 0) or 0)
    if seat not in _agents:
        _agents[seat] = AdaptiveAgent(_params, seat)
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
    print(f"Decision Agent v3 vs PASS (seed 1): ${money:,.0f}")
