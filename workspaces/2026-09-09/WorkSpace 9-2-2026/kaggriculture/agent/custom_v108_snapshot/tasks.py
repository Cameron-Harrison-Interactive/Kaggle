"""
tasks.py — the STATE-DRIVEN task scheduler that replaces precompiled routes.

Every turn:
  1) read Board
  2) compute the *set of tasks worth doing right now* (from state, not tapes)
  3) assign each unit (farmer + hands) to a task using distance + priority
  4) each unit emits ONE primitive engine action toward its assigned task

Tasks are cheap objects — no persistent state between turns; recompute fresh
every step. That's the point: the router is reactive, so no two games route
the same way, and no one can copy the pattern.

A Task exposes:
    - required_items: dict of items the unit must be CARRYING to execute
        (e.g. WATER task requires nothing; FEED requires WHEAT; PLANT requires
        nothing because seeds are drawn from private["seeds"], not carried)
    - target: (x, y) on which the terminal action is executed
    - terminal_action(unit_idx, board) -> list  (the engine action verb+args)
    - priority: higher = do sooner (used to break ties in assignment)
    - completes_after: True if task is one-shot (removed after execution)
"""

from .board import BOARD_SIZE, CROPS, ANIMALS, SHED_TILES, SHED_SET
from .pathing import manhattan


class Task:
    kind = "TASK"
    priority = 0
    required_items = {}   # {item: n_needed_in_hand}
    target = None

    def __init__(self, target, **kw):
        self.target = tuple(target)
        for k, v in kw.items():
            setattr(self, k, v)

    def terminal_action(self, unit_idx, board):
        raise NotImplementedError

    def __repr__(self):
        return f"<{self.kind}@{self.target} pri={self.priority}>"


class WaterTask(Task):
    kind = "WATER"
    priority = 60      # keeping plants alive is urgent
    required_items = {}
    def terminal_action(self, u, b): return ["WATER"]


class HarvestTask(Task):
    kind = "HARVEST"
    priority = 70      # harvest before decay
    required_items = {}
    def terminal_action(self, u, b): return ["HARVEST"]


class PlantTask(Task):
    kind = "PLANT"
    priority = 40
    required_items = {}
    def __init__(self, target, crop, priority=40):
        super().__init__(target)
        self.crop = crop
        self.priority = priority
    def terminal_action(self, u, b): return ["PLANT", self.crop]


class FeedTask(Task):
    kind = "FEED"
    priority = 90      # animals starve after 2 unfed days — top priority
    required_items = {"WHEAT": 1}
    def terminal_action(self, u, b): return ["FEED"]


class CareTask(Task):
    kind = "CARE"
    priority = 65       # care+feed same day = +1 unit banked to production
    required_items = {}
    def terminal_action(self, u, b): return ["CARE"]


class CollectFertTask(Task):
    kind = "COLLECT_FERTILIZER"
    priority = 55      # free money, snag it
    required_items = {}
    def terminal_action(self, u, b): return ["COLLECT_FERTILIZER"]


class HarvestAnimalTask(Task):
    kind = "HARVEST_ANIMAL"
    priority = 65
    required_items = {}
    def terminal_action(self, u, b): return ["HARVEST"]


class PlaceAnimalTask(Task):
    kind = "PLACE"
    priority = 75       # above HARVEST (70) but below WATER (82) — animals
                        # get placed before wheat market pressure explodes
    def __init__(self, target, animal):
        super().__init__(target)
        self.animal = animal
        # Animal lives in shed after BUY_ANIMAL; must be picked up first.
        self.required_items = {animal: 1}
    def terminal_action(self, u, b): return ["PLACE", self.animal]


class BuildTask(Task):
    kind = "BUILD"
    priority = 45       # default; BUILD-early tested at pri 74 -> crashed one seed
    required_items = {}
    def __init__(self, target, structure):
        super().__init__(target)
        self.structure = structure  # "COOP" or "PASTURE"
    def terminal_action(self, u, b):
        return ["BUILD_COOP"] if self.structure == "COOP" else ["BUILD_PASTURE"]


class FertilizeTask(Task):
    kind = "FERTILIZE"
    priority = 85      # very high — must happen BEFORE that day's end-of-day
                       # production computes doubling
    required_items = {"FERTILIZER": 1}
    def terminal_action(self, u, b): return ["FERTILIZE"]


class DigTask(Task):
    kind = "DIG"
    priority = 50   # above PLANT (40) — clear weeds before planting into them
    required_items = {}
    def terminal_action(self, u, b): return ["DIG"]


class DropTask(Task):
    """Drop everything the unit is carrying at the shed."""
    kind = "DROP"
    priority = 20      # do when idle or over-full
    required_items = {}
    def terminal_action(self, u, b): return ["DROP"]


class PreCarryWheatTask(Task):
    """Idle hand grabs wheat from shed so it can FEED immediately next turn.

    Fired only when: hand carries nothing, shed has surplus wheat above
    the reserve, and there are hungry animals somewhere.
    Priority 15 — only fires when NOTHING else to do."""
    kind = "PRE_CARRY_WHEAT"
    priority = 15
    required_items = {}  # we'll go pick up ourselves
    def terminal_action(self, u, b):
        # Only executed when unit stands on shed tile — grab a small bundle.
        have = b.shed.get("WHEAT", 0)
        take = min(4, have)
        return ["PICKUP", "WHEAT", take] if take > 0 else ["PASS"]


# ------------------------------------------------------------------
# Task GENERATION — the actual "what should we do this turn" logic
# ------------------------------------------------------------------

def generate_tasks(board):
    """Return a fresh list of Task objects worth executing this turn.

    Order in list doesn't matter — assignment sorts by priority + distance.
    We intentionally return more tasks than units; the assigner takes the
    top-priority reachable set.
    """
    tasks = []
    day = board.day
    hour = board.hour

    # ---------- animals (feed, harvest, collect_fert, care) ----------
    for (x, y) in board.animals():
        t = board.tile(x, y)
        animal = t["animal"]
        a = ANIMALS[animal]
        placed_day = t["placed_day"]

        # FEED: highest priority — starving loses the animal
        if not t["fed_today"]:
            # extra urgency if already 1 day unfed
            pri = 95 if t["consecutive_unfed"] >= 1 else 90
            tasks.append(FeedTask((x, y), priority=pri))

        # HARVEST animal product if any
        if t["yield_units"] > 0:
            tasks.append(HarvestAnimalTask((x, y)))

        # COLLECT free fertilizer
        if t["fertilizer_available"]:
            tasks.append(CollectFertTask((x, y)))

        # CARE: banks a bonus consumed on the NEXT production day IF fed.
        # We fire CARE whenever animal isn't cared yet — the FEED task will
        # come around too, and if both land the same day the bonus applies.
        # No harm in caring a not-yet-fed animal (bonus just wasted).
        if not t["cared_today"]:
            tasks.append(CareTask((x, y)))

    # ---------- plants (water, harvest, fertilize) ----------
    for (x, y) in board.plants():
        t = board.tile(x, y)
        crop = t["crop"]
        cd = CROPS[crop]
        age = day - t["planted_day"]
        planted_day = t["planted_day"]

        # FERTILIZE strawberry / tomato right before each production day so
        # `fertilized_until_day >= production_day`. Fertilizer is active for
        # day F, F+1, F+2. We fertilize on production_day-1 so it covers.
        # Also generate if a hand is already CARRYING fert (so mid-walk hands
        # aren't stranded when shed empties out at their pickup turn).
        _any_fert_carried = any(
            board.unit_holding(i, "FERTILIZER") > 0
            for i in range(len(board.units))
        )
        if crop in ("STRAWBERRY", "TOMATO") and (
                board.shed.get("FERTILIZER", 0) > 0 or _any_fert_carried):
            # productions occur on planted_day + first + k*interval for k in 0..max_yield-1
            future_prods = []
            for k in range(cd["max_yield"]):
                pd = planted_day + cd["first"] + k * cd["interval"]
                if pd >= day:  # not yet
                    future_prods.append(pd)
            # find next production day; fertilize if today == pd-1 and not
            # already covered
            fert_until = t.get("fertilized_until_day", -1)
            for pd in future_prods:
                if fert_until >= pd:
                    continue
                # apply if today is pd-1 (or pd itself, still doubles that day)
                if day == pd - 1 or day == pd:
                    tasks.append(FertilizeTask((x, y)))
                    break  # one per plant per turn

        # (MELON fertilize tried but net-negative: fert $100 sell > 2-day
        # earlier harvest doesn't add enough cycles. rules.py confirms.)

        # WATER: if not watered today, it'll go 2 consecutive_unwatered and die.
        # Also: watering inside the bonus window is where yield actually comes from.
        if not t["watered_today"]:
            in_window = False
            if not cd["ongoing"]:
                ws = (cd["max_day"] + 1) // 2
                in_window = ws <= age <= cd["max_day"]
            else:
                in_window = True
            urgent = t["consecutive_unwatered"] >= 1
            if urgent:
                pri = 85
            elif in_window:
                pri = 80
            else:
                pri = 40
            tasks.append(WaterTask((x, y), priority=pri))

        # HARVEST when ripe. For one-time crops WAIT for yield to fill (target =
        # what's actually attainable given fert history). Harvesting at yield=1
        # throws away all remaining watering bonuses.
        if t["yield_units"] > 0:
            if not cd["ongoing"]:
                yu = t["yield_units"]
                max_y = cd["max_yield"]
                ws = (cd["max_day"] + 1) // 2
                # Attainable yield without fert = min(max_yield, 1 + window_len).
                # (WHEAT/CARROT get all yield from window; MELON's window > cap.)
                plain_max = min(max_y, 1 + (cd["max_day"] - ws + 1))
                fert_active_ever = t.get("fertilized_until_day", -1) >= 0
                target = max_y if fert_active_ever else plain_max
                last_water_day = cd["max_day"]
                if age >= cd["first"]:
                    if yu >= target or age >= last_water_day:
                        pri = 78 if age >= last_water_day and yu < target else 70
                        tasks.append(HarvestTask((x, y), priority=pri))
            else:
                # ongoing (strawberry, tomato): harvest EVERY time yield > 0
                # so we can sell into a rising market and re-plant space if
                # productions are done.
                if age >= cd["first"] and t["yield_units"] > 0:
                    tasks.append(HarvestTask((x, y), priority=68))

    # ---------- weeds (dig) ----------
    for (x, y) in board.weeds():
        tasks.append(DigTask((x, y)))

    # (PRE_CARRY_WHEAT experiment: -$0 avg but 1-2 animals died from wheat
    # hoarding out of shed. Removed. Alternative idle strategy needed.)

    return tasks


def generate_build_and_place_tasks(board, herd_targets=None):
    """From layout plan: build structures on empty CROP/PASTURE/COOP tiles as
    the plan dictates, and place animals into empty structures.

    herd_targets: {'SHEEP': N, 'COW': N, 'GOOSE': N} — must match the economy's
    herd targets, else the buyer purchases animals the placer refuses to place.
    """
    from .plan import full_layout, desired_animal_for
    tasks = []
    layout = full_layout()

    counts = {"SHEEP": 0, "COW": 0, "GOOSE": 0}
    for (x, y) in board.animals():
        a = board.tile(x, y).get("animal")
        if a in counts:
            counts[a] += 1

    for (x, y), role in layout.items():
        if role not in ("PASTURE", "COOP"):
            continue
        if board.is_locked(x, y):
            continue
        t = board.tile(x, y)
        if t is None:
            tasks.append(BuildTask((x, y), role))
            continue
        if board.is_structure_empty(x, y, role):
            want = desired_animal_for(x, y, counts, herd_targets)
            if want is None:
                continue
            have_shed = board.shed.get(want, 0)
            have_carry = any(board.unit_holding(i, want) > 0 for i in range(len(board.units)))
            if have_shed > 0 or have_carry:
                tasks.append(PlaceAnimalTask((x, y), want))
                counts[want] += 1
            else:
                # Preferred animal not available. Try any OTHER animal we
                # have that fits this structure. This unlocks early-game
                # placements where we might have COW in shed but role
                # wants SHEEP first — placing SOMETHING beats sitting empty.
                if role == "PASTURE":
                    for alt in ("COW", "SHEEP"):
                        if alt == want:
                            continue
                        _have = board.shed.get(alt, 0)
                        _carry = any(board.unit_holding(i, alt) > 0
                                    for i in range(len(board.units)))
                        _cap = (herd_targets or {}).get(alt, 0)
                        if (_have > 0 or _carry) and counts.get(alt, 0) < _cap:
                            tasks.append(PlaceAnimalTask((x, y), alt))
                            counts[alt] += 1
                            break
                elif role == "COOP":
                    # only geese in coops; already tried want above
                    pass
    return tasks


def generate_planting_tasks(board):
    """Plant `desired_crop_for(x,y)` on each empty CROP/STRAW-role tile,
    respecting the seed count we own.

    STRAWBERRY tiles get a HIGH plant priority so we secure them early —
    late-planted strawberry misses productions (first_yield_day=10, harvest
    every 2 days for 4 productions = D10, D12, D14, D16 for a D0 plant;
    plant on D14 you only get 2 harvests)."""
    from .plan import full_layout, desired_crop_for
    tasks = []
    layout = full_layout()
    day = board.day

    per_crop = {}
    for (x, y), role in layout.items():
        if role not in ("CROP", "STRAW", "MELON", "CARROT"):
            continue
        if board.is_locked(x, y):
            continue
        if board.tile(x, y) is None:
            crop = desired_crop_for(x, y)
            per_crop.setdefault(crop, []).append((x, y))

    for crop, tiles in per_crop.items():
        tiles.sort(key=lambda p: (p[1], p[0]))
        have = board.seeds.get(crop, 0)
        if crop == "STRAWBERRY":
            pri = 78
        elif crop == "MELON":
            pri = 72
        elif crop == "CARROT":
            pri = 55  # decent — fast cycle, cash injection
        else:
            pri = 40   # WHEAT
        for i, tile in enumerate(tiles):
            if i >= have:
                break
            tasks.append(PlantTask(tile, crop, priority=pri))
    return tasks
