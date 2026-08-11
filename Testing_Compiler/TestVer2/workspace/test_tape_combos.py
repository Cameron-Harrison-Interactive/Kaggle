import importlib.util, json, base64, zlib, sys

DATA = '/home/user/kaggriculture/V18 - Adapt-2-Survive/data'

def load_tape(seed, seat):
    """Load a tape for a specific seed and seat."""
    if seat == 0:
        fn = f'{DATA}/route_v18_opt_seat0_s{seed}.json'
    else:
        # seat 1 tapes might have different naming
        fn = f'{DATA}/route_v18_opt_seat1_s{seed}.json'
        # Try alternate naming
        try:
            with open(fn) as f:
                return json.load(f)
        except:
            pass
        # Some seat1 tapes might be named differently
        for name in [f'seed{seed}', f's{seed}', f'seed{seed}_seat1']:
            fn = f'{DATA}/{name}.json'
            try:
                with open(fn) as f:
                    return json.load(f)
            except:
                pass
    try:
        with open(fn) as f:
            return json.load(f)
    except FileNotFoundError:
        return None

def make_agent(seat0_tape, seat1_tape):
    """Create an agent function with specific tapes."""
    _SEAT0 = seat0_tape
    _SEAT1 = seat1_tape
    
    def agent(obs, configuration=None):
        # Copy from submit/main.py but use custom tapes
        import copy, math
        
        def _get(value, key, default=None):
            if isinstance(value, dict):
                return value.get(key, default)
            getter = getattr(value, "get", None)
            if callable(getter):
                return getter(key, default)
            return getattr(value, key, default)
        
        def _seat(obs):
            return 1 if int(_get(obs, "player", 0) or 0) == 1 else 0
        
        def _farm(obs, seat):
            farms = list(_get(obs, "farms", []) or [])
            return farms[seat] if seat < len(farms) else {}
        
        def _copy_action(action):
            if action is None:
                farm = _farm(obs, _seat(obs))
                return {
                    "farmer": ["PASS"],
                    "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])],
                    "market": [],
                }
            action = copy.deepcopy(action or {})
            return {
                "farmer": list(action.get("farmer") or ["PASS"]),
                "hands": [list(order or ["PASS"]) for order in (action.get("hands") or [])],
                "market": [list(order) for order in (action.get("market") or [])],
            }
        
        def _align_hands(action, obs):
            action = _copy_action(action)
            expected = len(_get(_farm(obs, _seat(obs)), "hands", []) or [])
            hands = list(action.get("hands") or [])
            if len(hands) < expected:
                hands.extend([["PASS"]] for _ in range(expected - len(hands)))
            action["hands"] = [list(order or ["PASS"]) for order in hands[:expected]]
            return action
        
        def _shape(name, value):
            value = max(0.0, float(value))
            if name == "linear": return value
            if name == "sq": return value * value
            if name == "sqrt": return math.sqrt(value)
            if name == "log": return math.log1p(value)
            raise ValueError(name)
        
        _MARKET_PARAMS = {
            "WHEAT": (25, 10000, 400, "sqrt", 0.8, "log", 0.2),
            "CARROT": (35, 10000, 450, "log", 0.2, "sqrt", 0.7),
            "TOMATO": (60, 10000, 200, "linear", 0.4, "sqrt", 0.6),
            "STRAWBERRY": (120, 10000, 100, "sqrt", 0.7, "linear", 1.6),
            "MELON": (250, 10000, 300, "log", 0.2, "sq", 3.6),
            "EGG": (50, 10000, 332, "linear", 0.4, "log", 0.2),
            "MILK": (160, 10000, 122, "sqrt", 0.6, "linear", 1.6),
            "WOOL": (200, 10000, 105, "log", 0.2, "sq", 3.2),
            "FERTILIZER": (100, 10000, 200, "linear", 0.4, "linear", 0.4),
        }
        
        def _market_price(item, inventory):
            base, equilibrium, scale, below_func, below_target, above_func, above_target = _MARKET_PARAMS[item]
            if inventory < equilibrium:
                amplitude = below_target * base / _shape(below_func, scale)
                price = base + amplitude * _shape(below_func, equilibrium - inventory)
            else:
                amplitude = above_target * base / _shape(above_func, scale)
                price = base - amplitude * _shape(above_func, inventory - equilibrium)
            return max(1, int(round(price)))
        
        def _is_sell(order):
            return (isinstance(order, (list, tuple)) and len(order) >= 3 
                    and order[0] == "SELL" and order[1] in _MARKET_PARAMS)
        
        def _impact_score(obs, order):
            if not _is_sell(order): return float("-inf")
            item = str(order[1])
            try: quantity = max(0, int(order[2]))
            except: return 0.0
            market = _get(obs, "market", {}) or {}
            inventory = _get(market, "inventory", {}) or {}
            prices = _get(market, "prices", {}) or {}
            current_inventory = int(_get(inventory, item, 10000) or 0)
            current_quote = float(_get(prices, item, _market_price(item, current_inventory)) or 0)
            later_quote = float(_market_price(item, current_inventory + quantity))
            return float(quantity) * max(0.0, current_quote - later_quote)
        
        def _demand_per_day(obs, configuration, item):
            return 1.0
        
        def _order_score(obs, configuration, order):
            score = _impact_score(obs, order)
            if score <= 0 or not _is_sell(order): return score
            item = str(order[1])
            quantity = max(0, int(order[2]))
            market = _get(obs, "market", {}) or {}
            inventory = _get(market, "inventory", {}) or {}
            current_inventory = int(_get(inventory, item, 10000) or 0)
            demand = max(0.25, _demand_per_day(obs, configuration, item))
            excess = max(0.0, current_inventory + quantity - 10000)
            urgency = min(1.0, (excess / demand) / 10.0)
            return score * (1.0 + 0.25 * urgency)
        
        def _rank_sell_slots(obs, action, configuration):
            action = _copy_action(action)
            market = list(action.get("market") or [])
            rows = [(_order_score(obs, configuration, order), -i, list(order))
                    for i, order in enumerate(market) if _is_sell(order)]
            if len(rows) < 2: return action
            rows.sort(reverse=True)
            ranked = iter(row[2] for row in rows)
            action["market"] = [next(ranked) if _is_sell(order) else order for order in market]
            return action
        
        # Weeds
        _WEED_STATE = {0: {}, 1: {}}
        _WEED_REPLAY_STEPS = 8
        
        def _tile_at(farm, position):
            try:
                x, y = int(position[0]), int(position[1])
                return (_get(farm, "tiles", []) or [])[y][x]
            except:
                return "LOCKED"
        
        def _trace_actor_action(actions, step, actor):
            trace = actions[min(max(int(step), 0), len(actions) - 1)] or {}
            if actor == "farmer":
                return list(trace.get("farmer") or ["PASS"])
            hands = trace.get("hands", []) or []
            return list(hands[actor] if actor < len(hands) else ["PASS"])
        
        def _weed_repair_action(obs, action, actions, step):
            action = _align_hands(action, obs)
            seat = _seat(obs)
            game = _WEED_STATE[seat]
            if step == 0 or step < game.get("last_step", -1):
                game = {"last_step": step, "active": {}}
                _WEED_STATE[seat] = game
            game["last_step"] = step
            farm = _farm(obs, seat)
            positions = [_get(farm, "farmer"), *list(_get(farm, "hands", []) or [])]
            unit_actions = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]
            active = game["active"]
            for actor, transaction in list(active.items()):
                index = 0 if actor == "farmer" else int(actor) + 1
                if index >= len(unit_actions):
                    active.pop(actor, None)
                    continue
                age = step - transaction["start"]
                if age == 1:
                    unit_actions[index] = list(transaction["intended"])
                elif 2 <= age <= 1 + _WEED_REPLAY_STEPS:
                    unit_actions[index] = _trace_actor_action(actions, step - 1, actor)
                else:
                    active.pop(actor, None)
            for index, (position, intended) in enumerate(zip(positions, unit_actions)):
                actor = "farmer" if index == 0 else index - 1
                if actor in active or not isinstance(intended, list) or not intended:
                    continue
                if intended[0] not in ("BUILD_PASTURE", "PLANT"): continue
                tile = _tile_at(farm, position)
                if not isinstance(tile, dict) or tile.get("kind") != "WEED": continue
                active[actor] = {"start": step, "intended": list(intended)}
                unit_actions[index] = ["DIG"]
            action["farmer"] = unit_actions[0] if unit_actions else ["PASS"]
            action["hands"] = unit_actions[1:]
            return _align_hands(action, obs)
        
        _MEM = {0: None, 1: None}
        
        def _new_mem():
            return {"family": "unknown", "locked": False, "price_hist": {},
                    "last_step": -1, "seb_score": 0, "builda_score": 0, "straw_score": 0,
                    "opp_has_se": False, "opp_anim_peak": 0, "opp_straw_peak": 0, 
                    "opp_melon_peak": 0, "behind": False, "mode": "default"}
        
        def _mem_for(obs):
            seat = _seat(obs)
            step = int(_get(obs, "step", 0) or 0)
            m = _MEM.get(seat)
            if m is None or step == 0 or step < int(m.get("last_step", -1) or -1):
                m = _new_mem()
                _MEM[seat] = m
            m["last_step"] = step
            return m
        
        def _count_crop(farm, crop):
            n = 0
            for row in (farm.get("tiles") or []):
                for t in row:
                    if isinstance(t, dict) and t.get("kind") == "PLANT" and t.get("crop") == crop:
                        n += 1
            return n
        
        def _count_animal(farm, kind=None):
            n = 0
            for row in (farm.get("tiles") or []):
                for t in row:
                    if isinstance(t, dict) and t.get("animal"):
                        if kind is None or t.get("animal") == kind: n += 1
            return n
        
        def _opp_farm(obs):
            seat = _seat(obs)
            farms = obs.get("farms") or []
            opp = 1 - seat
            return farms[opp] if opp < len(farms) else {}
        
        def _update_memory(obs):
            m = _mem_for(obs)
            try:
                day = int(obs.get("day", int(obs.get("step", 0) or 0) // 24) or 0)
                market = obs.get("market") or {}
                prices = market.get("prices") or {}
                inv = market.get("inventory") or {}
                ph = m["price_hist"]
                for item, p in prices.items():
                    h = ph.setdefault(str(item), [])
                    h.append(float(p or 0))
                    if len(h) > 48: ph[str(item)] = h[-48:]
                own = _farm(obs, _seat(obs))
                opp = _opp_farm(obs)
                o_sheep = _count_animal(opp, "SHEEP")
                o_cow = _count_animal(opp, "COW")
                o_anim = o_sheep + o_cow
                o_straw = _count_crop(opp, "STRAWBERRY")
                o_melon = _count_crop(opp, "MELON")
                o_wheat = _count_crop(opp, "WHEAT")
                o_quads = list(opp.get("unlocked_quadrants") or [])
                if not m.get("locked"):
                    seb = int(m.get("seb_score") or 0)
                    ba = int(m.get("builda_score") or 0)
                    st = int(m.get("straw_score") or 0)
                    if day <= 2 and o_melon >= 10 and o_cow >= 2 and o_sheep <= 3: ba += 4
                    if day <= 3 and o_melon >= 8 and o_cow >= 2: ba += 2
                    if 6 <= day <= 8 and "NE" in o_quads and "SW" not in o_quads and o_melon >= 8: ba += 1
                    if 10 <= day <= 12 and "SW" in o_quads and o_anim >= 12 and o_melon >= 8: ba += 2
                    if day <= 5 and "NE" in o_quads: seb += 2
                    if day <= 7 and "SW" in o_quads: seb += 2
                    if day <= 12 and "SE" in o_quads: seb += 4
                    if day <= 6 and o_wheat >= 10: seb += 2
                    if day <= 15 and o_anim >= 16: seb += 2
                    if day <= 12 and o_straw >= 15: st += 3
                    if day <= 15 and o_straw >= 25: st += 3
                    if inv.get("STRAWBERRY", 10000) > 10040 or prices.get("STRAWBERRY", 120) < 100: st += 2
                    if day >= 10 and o_straw >= 30: st += 2
                    m["seb_score"] = seb
                    m["builda_score"] = ba
                    m["straw_score"] = st
                    scores = {"seb": seb, "buildA": ba, "straw_flood": st}
                    best = max(scores, key=scores.get)
                    if scores[best] >= 4: m["family"] = best
                    if day >= 6 and scores[best] >= 4: m["locked"] = True
                    if scores[best] >= 6: m["locked"] = True
                    if day >= 8 and m.get("family") == "unknown":
                        m["family"] = "mirror"
                        m["locked"] = True
                fam = m.get("family") or "unknown"
                straw_inv = int(inv.get("STRAWBERRY", 10000) or 10000)
                straw_px = float(prices.get("STRAWBERRY", 120) or 120)
                glut = straw_inv > 10045 or straw_px < 105
                if fam == "straw_flood" and glut: m["mode"] = "anti_straw"
                elif glut and int(m.get("opp_straw_peak") or 0) >= 28 and straw_px < 100: m["mode"] = "anti_straw"
                elif fam == "buildA": m["mode"] = "anti_buildA"
                elif fam == "seb": m["mode"] = "anti_seb"
                else: m["mode"] = "default"
                om = float(own.get("money") or 0)
                xm = float(opp.get("money") or 0)
                if day >= 18 and xm > om * 1.12 and (xm - om) > 4000: m["behind"] = True
                else: m["behind"] = False
            except: pass
            return m
        
        def _adapt_crops(obs, action):
            try:
                m = _update_memory(obs)
                day = int(obs.get("day", int(obs.get("step", 0) or 0) // 24) or 0)
                mode = m.get("mode") or "default"
                market = obs.get("market") or {}
                inv = market.get("inventory") or {}
                prices = market.get("prices") or {}
                straw_inv = int(inv.get("STRAWBERRY", 10000) or 10000)
                straw_px = float(prices.get("STRAWBERRY", 120) or 120)
                private = obs.get("private") or {}
                seeds = dict(private.get("seeds") or {})
                farm = _farm(obs, _seat(obs))
                money = float(farm.get("money") or 0)
                lo, hi = 7, 13
                if mode == "anti_straw": lo, hi = 6, 14
                if not (lo <= day <= hi): return action
                surge = straw_inv > 10050 or straw_px < 100
                if mode == "anti_straw" and (straw_inv > 10040 or straw_px < 108): surge = True
                if not surge: return action
                mo = list(action.get("market") or [])
                if int(seeds.get("TOMATO", 0) or 0) == 0 and money > 200 and len(mo) < 10:
                    if not any(x and x[0] == "BUY_SEED" and len(x) > 1 and x[1] == "TOMATO" for x in mo):
                        mo.append(["BUY_SEED", "TOMATO", 5])
                        action["market"] = mo[:10]
                seeds = dict((obs.get("private") or {}).get("seeds") or seeds)
                if int(seeds.get("TOMATO", 0) or 0) > 0:
                    max_conv = 3 if (straw_px < 90 or straw_inv > 10070) else 2
                    hands = list(action.get("hands") or [])
                    conv = 0
                    for i, h in enumerate(hands):
                        if h and h[0] == "PLANT" and len(h) > 1 and h[1] == "STRAWBERRY" and conv < max_conv:
                            hands[i] = ["PLANT", "TOMATO"]
                            conv += 1
                    action["hands"] = hands
                    fr = action.get("farmer")
                    if fr and fr[0] == "PLANT" and len(fr) > 1 and fr[1] == "STRAWBERRY" and conv < max_conv:
                        action["farmer"] = ["PLANT", "TOMATO"]
            except: pass
            return action
        
        def _adapt_animals(obs, action):
            try:
                m = _mem_for(obs)
                day = int(obs.get("day", int(obs.get("step", 0) or 0) // 24) or 0)
                farm = _farm(obs, _seat(obs))
                our_anim = _count_animal(farm)
                if m.get("mode") == "anti_buildA" and m.get("locked") and day >= 14 and our_anim >= 13:
                    mo = [o for o in (action.get("market") or []) if not (o and o[0] == "BUY_ANIMAL")]
                    action["market"] = mo[:10]
            except: pass
            return action
        
        def _shed_access_tiles(board_size):
            half = board_size // 2
            return [(half - 1, half - 1), (half, half - 1), (half - 1, half), (half, half)]
        
        def _is_shed_adjacent(pos, board_size):
            try: return tuple(int(x) for x in pos) in set(_shed_access_tiles(board_size))
            except: return False
        
        def _v26_terminal_sweep(obs, action, configuration):
            action = _align_hands(_copy_action(action), obs)
            seat = _seat(obs)
            farm = _farm(obs, seat)
            private = _get(obs, "private", {}) or {}
            shed = dict(_get(private, "shed", {}) or {})
            inventories = list(_get(private, "inventories", []) or [])
            tiles = list(_get(farm, "tiles", []) or [])
            board_size = len(tiles) or 10
            capacity = int(_get(configuration, "shedCapacity", 100) or 100)
            room = max(0, capacity - sum(int(v or 0) for v in shed.values()))
            positions = [_get(farm, "farmer", []), *list(_get(farm, "hands", []) or [])]
            unit_actions = [action.get("farmer", ["PASS"]), *list(action.get("hands") or [])]
            prices = _get(_get(obs, "market", {}) or {}, "prices", {}) or {}
            item_prices = sorted([(float(_get(prices, item, 0) or 0), item) for item in _MARKET_PARAMS], reverse=True)
            for index, position in enumerate(positions):
                if index >= len(unit_actions) or index >= len(inventories) or room <= 0: continue
                if not _is_shed_adjacent(position, board_size): continue
                carried = inventories[index] or {}
                choices = []
                for price, item in item_prices:
                    quantity = max(0, int(_get(carried, item, 0) or 0))
                    if quantity <= 0: continue
                    choices.append((price, quantity, item))
                if not choices: continue
                _, quantity, item = max(choices)
                quantity = min(quantity, room)
                if quantity <= 0: continue
                unit_actions[index] = ["PLACE", item, quantity]
                shed[item] = int(shed.get(item, 0) or 0) + quantity
                room -= quantity
            action["farmer"] = unit_actions[0] if unit_actions else ["PASS"]
            action["hands"] = unit_actions[1:]
            action["market"] = [["SELL", item, int(shed.get(item, 0) or 0)]
                                for item in _MARKET_PARAMS if int(shed.get(item, 0) or 0) > 0][:10]
            return _rank_sell_slots(obs, action, configuration)
        
        def _base_agent(obs, configuration=None):
            try:
                actions = _SEAT1 if _seat(obs) == 1 else _SEAT0
                step = min(max(0, int(_get(obs, "step", 0) or 0)), len(actions) - 1)
                action = _copy_action(actions[step])
                action = _rank_sell_slots(obs, action, configuration)
                return _align_hands(action, obs)
            except:
                farm = _farm(obs, _seat(obs))
                return {"farmer": ["PASS"], "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])], "market": []}
        
        def agent_fn(obs, configuration=None):
            step = int(_get(obs, "step", 0) or 0)
            # Weeds
            try:
                actions = _SEAT1 if _seat(obs) == 1 else _SEAT0
                step_idx = min(max(0, int(_get(obs, "step", 0) or 0)), len(actions) - 1)
                action = _copy_action(actions[step_idx])
                action = _weed_repair_action(obs, action, actions, step)
            except:
                farm = _farm(obs, _seat(obs))
                action = {"farmer": ["PASS"], "hands": [["PASS"] for _ in (_get(farm, "hands", []) or [])], "market": []}
            # Adapt crops
            action = _adapt_crops(obs, action)
            # Adapt animals
            action = _adapt_animals(obs, action)
            # Terminal sweep
            if step == 718:
                try:
                    return _v26_terminal_sweep(obs, action, configuration)
                except: pass
            return action
        
        return agent_fn
    
    return make_agent

# Load tapes
print("Loading tapes...", flush=True)
tapes_seat0 = {}
tapes_seat1 = {}
for seed in range(1, 21):
    t = load_tape(seed, 0)
    if t:
        tapes_seat0[seed] = t
    t1 = load_tape(seed, 1)
    if t1:
        tapes_seat1[seed] = t1

print(f"Loaded {len(tapes_seat0)} seat0 tapes, {len(tapes_seat1)} seat1 tapes", flush=True)

# Test combinations on seeds 1-3
from kaggle_environments import make

test_seeds = [1, 2, 3]
best_combo = None
best_score = 0

# Test seat0 tapes with current seat1 (seed 5)
print("\nTesting different seat0 tapes with seat1=seed5...", flush=True)
for s0 in [1, 15, 16, 13]:
    if s0 not in tapes_seat0: continue
    s1 = 5  # current
    if s1 not in tapes_seat1: continue
    
    agent_fn = make_agent(tapes_seat0[s0], tapes_seat1[s1])()
    
    total = 0
    for ts in test_seeds:
        env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": ts})
        steps = env.reset()
        env.run([agent_fn, agent_fn])
        score = env.steps[-1][0].reward + env.steps[-1][1].reward
        total += score
    
    print(f"  seat0=s{s0}, seat1=s{s1}: ${total:,.0f}", flush=True)
    if total > best_score:
        best_score = total
        best_combo = (s0, s1)

print(f"\nBest: seat0=s{best_combo[0]}, seat1=s{best_combo[1]}: ${best_score:,.0f}", flush=True)
