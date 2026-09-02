"""
Decision Agent v5 — "Coverage" — EXPERIMENTAL full-board router (opt-in).

IMPORTANT: by default this agent is EXACTLY decision_agent_v2 (the proven
$68.5k economy). The board-coverage sweep is an experiment behind
`coverage=True` that is NOT yet better than v2 — the reactive worker pool is
at a local optimum, and filling 60+ tiles needs a deterministic per-worker
route compiler (the next milestone, building on Aster's ledger design).

What the experimental sweep adds when `coverage=True`:
  * every worker shares the animal chores (feed / collect / harvest), then
    sweeps its own quadrant for water / harvest / plant / dig, choosing the
    NEAREST task in that quadrant (short walks, no cross-board thrash);
  * emergency feed/water overrides fire first (never-miss);
  * fresh plantings are watered the same day;
  * quadrant assignment / sweep direction rotate per match (anti-mirror).

Why it's not shipped: keeping 14 animals serviced AND watering 60 crops from
one reactive pool currently leaves too little time for both (measured: the
crops go unwatered and the herd income falls). That tension is exactly what a
deterministic route compiler resolves, and that is the next build.

Use it:
    v5.set_params({**v5.V5_DEFAULT_PARAMS, "coverage": True})
"""

from decision_agent_v2 import (
    DecisionAgent, DEFAULT_PARAMS, ANIMALS, ANIMAL_ORDER, manhattan,
)

QUAD_LIST = ["NW", "NE", "SW", "SE"]


def _build_orders():
    orders = {}
    for q in QUAD_LIST:
        y0 = 0 if q[0] == "N" else 5
        x0 = 0 if q[1] == "W" else 5
        o = []
        for r in range(5):
            row = [(x, y0 + r) for x in range(x0, x0 + 5)]
            if r % 2 == 1:
                row = row[::-1]
            o += row
        orders[q] = o
    return orders


QUAD_ORDERS = _build_orders()

V5_DEFAULT_PARAMS = dict(DEFAULT_PARAMS)
V5_DEFAULT_PARAMS.update({
    "coverage": False,       # master switch for the experimental sweep
    "target_plants": 60,     # crop fill target when coverage is on
})


class CoverageAgent(DecisionAgent):
    def __init__(self, params=None, seat=0):
        super().__init__(params, seat)
        self._worker_idx = 0
        self._quad_rot = 0
        self._snake_rev = 0
        self._sig = None

    # ------------------------------------------------------------------ act
    def act(self, obs, configuration=None):
        if not self.params.get("coverage", False):
            return super().act(obs, configuration)

        day = int(obs.get("day", 0) or 0)
        hour = int(obs.get("hour", 0) or 0)
        player = int(obs.get("player", 0) or 0)
        if hour == 0 and self._sig is None:
            self._sig = self._signature(obs)
            self._quad_rot = self._sig % 4
            self._snake_rev = (self._sig // 4) % 2

        farm = obs["farms"][player]
        tiles = farm["tiles"]
        money = float(farm.get("money", 0) or 0)
        unlocked = set(farm.get("unlocked_quadrants", []) or [])
        private = obs.get("private") or {}
        shed = private.get("shed") or {}
        seeds = private.get("seeds") or {}
        inventories = private.get("inventories") or [{}]

        board = self._scan_board(tiles, unlocked)
        board["weedset"] = set(board["weeds"])
        board["empty_set"] = set(board["empty"])
        board["unlocked_quads"] = unlocked

        market = super()._decide_market(day, hour, money, shed, seeds, board, unlocked)

        claims = set()
        farmer_pos = tuple(farm.get("farmer", [4, 4]))
        farmer_inv = inventories[0] if len(inventories) > 0 else {}
        self._worker_idx = 0
        farmer_action = self._decide_worker(farmer_pos, farmer_inv, board,
                                            shed, seeds, day, hour, claims)
        hand_actions = []
        for i, hp in enumerate(farm.get("hands", []) or []):
            self._worker_idx = i + 1
            inv = inventories[i + 1] if i + 1 < len(inventories) else {}
            hand_actions.append(self._decide_worker(tuple(hp), inv, board,
                                                    shed, seeds, day, hour, claims))
        return {"farmer": farmer_action, "hands": hand_actions,
                "market": market[:10]}

    @staticmethod
    def _signature(obs):
        seat = int(obs.get("player", 0) or 0)
        opp = obs["farms"][1 - seat]
        n_an = sum(1 for row in opp["tiles"] for t in row
                   if isinstance(t, dict) and t.get("animal"))
        prices = (obs.get("market") or {}).get("prices") or {}
        return (seat + n_an * 31 + int(sum(prices.values())) * 7) % 1000003

    # --------------------------------------------------------------- worker
    def _decide_worker(self, pos, inv, board, shed, seeds, day, hour, claims):
        if not self.params.get("coverage", False):
            return super()._decide_worker(pos, inv, board, shed, seeds, day,
                                          hour, claims)
        # shared animal chores, then the localized crop sweep
        for atype in ANIMAL_ORDER:
            if int(inv.get(atype, 0) or 0) > 0:
                return self._act_place_animal(pos, atype, board, claims)
        a = self._act_feed(pos, inv, board, shed, claims, True)
        if a: return a
        a = self._act_water(pos, board, claims, True)
        if a: return a
        a = self._act_start_herd(pos, inv, board, shed, day, claims)
        if a: return a
        a = self._act_feed(pos, inv, board, shed, claims, False)
        if a: return a
        a = self._act_collect(pos, board, claims)
        if a: return a
        a = self._act_harvest_animals(pos, board, claims)
        if a: return a
        a = self._crop_sweep(pos, inv, board, shed, seeds, day, hour, claims)
        if a: return a
        a = self._act_care(pos, board, claims)
        if a: return a
        a = self._act_dig(pos, board, claims)
        if a: return a
        return ["PASS"]

    def _act_harvest_animals(self, pos, board, claims):
        p = self.params
        cands = []
        for a in board["animals"]:
            if a["yield_units"] >= p.get("harvest_animal_min", 2):
                cands.append((manhattan(pos, (a["x"], a["y"])), (a["x"], a["y"])))
        cands.sort()
        for _, t in cands:
            if ("harvest", t[0], t[1]) in claims:
                continue
            claims.add(("harvest", t[0], t[1]))
            return self._move_or_act(pos, t, ["HARVEST"])
        return None

    def _crop_sweep(self, pos, inv, board, shed, seeds, day, hour, claims):
        here = board["grid"].get(pos)
        if here and here.get("kind") == "PLANT" and not here.get("watered_today"):
            k = ("water", pos[0], pos[1])
            if k not in claims:
                claims.add(k)
                return ["WATER"]

        j = self._worker_idx
        unlocked_q = sorted(board["unlocked_quads"])
        q = unlocked_q[(j + self._quad_rot) % len(unlocked_q)]
        best = None
        for t in QUAD_ORDERS[q]:
            if ("busy", t[0], t[1]) in claims:
                continue
            act = self._tile_action(t, board, seeds, day, hour, claims)
            if act is None:
                continue
            d = manhattan(pos, t)
            if best is None or d < best[0]:
                best = (d, t, act)
        if best is None:
            return ["PASS"]
        _, tile, act = best
        claims.add(("busy", tile[0], tile[1]))
        return self._move_or_act(pos, tile, act)

    def _tile_action(self, t, board, seeds, day, hour, claims):
        if ("busy", t[0], t[1]) in claims:
            return None
        if t in board["weedset"]:
            return ["DIG"]
        d = board["grid"].get(t)
        if d is None:
            if t in board["empty_set"] \
                    and hour < self.params.get("plant_cutoff", 12) \
                    and len(board["plants"]) < self._target(day, board):
                crop = self._pick_crop(seeds, day)
                if crop:
                    return ["PLANT", crop]
            return None
        if d.get("kind") == "PLANT":
            if not d.get("watered_today"):
                return ["WATER"]
            if self._harvestable_plant(d, day):
                return ["HARVEST"]
        return None

    def _target(self, day, board):
        p = self.params
        capacity = 25 * len(board["unlocked_quads"])
        cap = min(p.get("target_plants", 60), capacity)
        return min(cap, 6 + (cap - 6) * day // 12)

    def _pick_crop(self, seeds, day):
        for c in self._plant_priority(day):
            if int(seeds.get(c, 0) or 0) <= 0:
                continue
            cd = self._crop_data(c)
            need = cd["first"] if cd["ongoing"] else cd["max_day"]
            if day + need <= 29:
                return c
        return None

    @staticmethod
    def _crop_data(crop):
        from decision_agent_v2 import CROPS
        return CROPS[crop]


# ----------------------------------------------------------------------------
_params = None
_agents = {}


def agent(obs, configuration=None):
    global _params, _agents
    if _params is None:
        _params = dict(V5_DEFAULT_PARAMS)
    seat = int(obs.get("player", 0) or 0)
    if seat not in _agents:
        _agents[seat] = CoverageAgent(_params, seat)
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
    print(f"Decision Agent v5 vs PASS (seed 1): ${money:,.0f}")
