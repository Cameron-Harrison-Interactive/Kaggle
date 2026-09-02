"""
router.py — S63 route planner: committed multi-stop plans for animal chores.

WHY: the hourly greedy assigner re-matches every unit every hour, producing
measured churn (4,501 moves/game vs top bots' 3,625) and shed ping-pong
(313 PICKUP + 135 DROP). The daily animal workload (feed + care + collect +
harvest for ~15 animals = ~50 visits) is perfectly predictable and clusters
geographically (NW/NE pasture rows, NW/NE coop rows) — ideal for explicit
routes: one shed pickup amortized over a whole cluster, feeds swept in
nearest-neighbor order, products dropped ONCE at the end.

Design:
  Route = ordered stops; each hour the executor emits the next primitive
  action for the unit's current stop, then advances when the stop's work is
  done. Stop completion is read from TILE STATE (fed_today / cared_today /
  fertilizer_available / yield_units), so routes are self-invalidating —
  no stale state if an animal escapes or another unit rescues a feed.

Scheduling safety (the compound-task lesson: -$25k when per-animal bundles
serialized and starved the herd):
  - All FEEDs of a cluster run FIRST (starvation = 2 consecutive unfed
    DAYS; intra-day order only needs to finish before end of day).
  - Routed units are excluded from the emergency FEED pool only; urgent
    feed tasks remain available to all free units.
  - At most (units - 3) units get routes: 3+ always stay on the reactive
    task system for field work (water/plant/harvest) and emergencies.

Products are DROPPED at the route's end (~mid-day) — same-day sales keep
the H2H sell race (the nodrop-v1 lesson: -$7.4k when products waited for
end-of-day).
"""

from .board import SHED_TILES, SHED_SET
from .pathing import step_toward, nearest, manhattan

# module state (rebuilt daily; keyed by unit index, valid within the day)
_ROUTES = {}
_ROUTES_DAY = -1
MAX_CLUSTER = 5
MIN_FREE_UNITS = 3          # units kept off routes for field work + rescue
MIN_UNITS_FOR_ROUTING = 6   # below this, plain task system is fine

FEED, COLLECT, CARE, HARVEST = "FEED", "COLLECT_FERTILIZER", "CARE", "HARVEST"


def _cluster_animals(animals, max_size=MAX_CLUSTER):
    """Geographic clusters via nearest-neighbor chaining on sorted tiles."""
    if not animals:
        return []
    pts = sorted(animals)  # (x, y) sort groups rows naturally
    clusters = [[pts[0]]]
    for p in pts[1:]:
        # distance to the last member of the newest cluster
        last = clusters[-1][-1]
        if len(clusters[-1]) < max_size and manhattan(p, last) <= 2:
            clusters[-1].append(p)
        else:
            clusters.append([p])
    return clusters


def _route_stops(cluster):
    """Stop list for one cluster: pickup -> feeds -> collects -> cares ->
    harvests -> drop. Feeds first (life), then fert (money, zero preconditions
    from H0), then cares (bonus banking), then product harvest, one drop."""
    order = sorted(cluster)  # stable NN-ish sweep order (row-major)
    stops = [("PICKUP_WHEAT", None, len(order))]
    for pos in order:
        stops.append((FEED, pos, 1))
    for pos in order:
        stops.append((COLLECT, pos, 1))
    for pos in order:
        stops.append((CARE, pos, 1))
    for pos in order:
        stops.append((HARVEST, pos, 1))
    stops.append(("DROP", None, 1))
    return stops


def maybe_build_routes(board):
    """(Re)build daily routes once hands exist. Idempotent within a day."""
    global _ROUTES, _ROUTES_DAY
    day = board.day
    n_units = len(board.units)
    if day == _ROUTES_DAY and _ROUTES:
        return _ROUTES
    if n_units < MIN_UNITS_FOR_ROUTING:
        _ROUTES = {}
        return _ROUTES

    animals = []
    for (x, y) in board.animals():
        animals.append((x, y))
    if len(animals) < 4:
        _ROUTES = {}
        return _ROUTES

    clusters = _cluster_animals(animals)
    max_routed = n_units - MIN_FREE_UNITS
    if len(clusters) > max_routed:
        # merge smallest clusters together until within budget
        while len(clusters) > max_routed and len(clusters) > 1:
            clusters.sort(key=len)
            a = clusters.pop(0)
            clusters[0] = sorted(clusters[0] + a)
            clusters[0] = _split_if_huge(clusters[0])
            # re-cluster merged blob properly
            clusters = _cluster_animals(
                [p for c in clusters for p in c],
                max_size=max(MAX_CLUSTER, len(animals) // max(1, max_routed)))

    # Prefer units already positioned near each cluster (hands home near
    # shed/NW; farmer idx 0 is exempt from routing so it stays reactive).
    free_units = list(range(1, n_units))
    routes = {}
    for cluster in sorted(clusters, key=lambda c: -len(c)):
        if not free_units:
            break
        cx = sum(p[0] for p in cluster) / len(cluster)
        cy = sum(p[1] for p in cluster) / len(cluster)
        best_u = min(free_units,
                     key=lambda u: manhattan(board.units[u], (cx, cy)))
        free_units.remove(best_u)
        routes[best_u] = {"stops": _route_stops(cluster), "i": 0}
    _ROUTES = routes
    _ROUTES_DAY = day
    return _ROUTES


def _split_if_huge(cluster):
    return cluster if len(cluster) <= 2 * MAX_CLUSTER else cluster[:MAX_CLUSTER]


def active_route(unit_idx):
    r = _ROUTES.get(unit_idx)
    if r and r["i"] >= len(r["stops"]):
        return None
    return r


def routed_units():
    return [u for u, r in _ROUTES.items() if r["i"] < len(r["stops"])]


def route_action(unit_idx, pos, board):
    """Next primitive action for a routed unit, or None if route finished."""
    r = _ROUTES.get(unit_idx)
    if r is None or r["i"] >= len(r["stops"]):
        _ROUTES.pop(unit_idx, None)
        return None
    inv = board.unit_inv(unit_idx)

    while r["i"] < len(r["stops"]):
        kind, target, n = r["stops"][r["i"]]

        if kind == "PICKUP_WHEAT":
            # need = remaining FEED stops for animals still unfed
            need = sum(1 for k, t, _ in r["stops"][r["i"]:]
                       if k == FEED and _tile_needs(board, t, "fed"))
            if need <= 0 or board.shed.get("WHEAT", 0) <= 0:
                r["i"] += 1
                continue
            if inv.get("WHEAT", 0) >= need:
                r["i"] += 1
                continue
            if tuple(pos) in SHED_SET:
                take = min(max(need, 3), board.shed.get("WHEAT", 0))
                return ["PICKUP", "WHEAT", take]
            shed, _ = nearest(pos, SHED_TILES)
            d = step_toward(pos, shed)
            if d:
                return [d]
            r["i"] += 1
            continue

        if kind == "DROP":
            # only useful if carrying anything
            if not any(v > 0 for v in inv.values()):
                r["i"] += 1
                continue
            if tuple(pos) in SHED_SET:
                r["i"] += 1
                return ["DROP"]
            shed, _ = nearest(pos, SHED_TILES)
            d = step_toward(pos, shed)
            if d:
                return [d]
            r["i"] += 1
            continue

        # chore stop: must still be pending, else skip
        t = board.tile(target[0], target[1])
        if not (isinstance(t, dict) and t.get("animal")):
            r["i"] += 1
            continue
        if kind == FEED and t.get("fed_today"):
            r["i"] += 1
            continue
        if kind == COLLECT and not t.get("fertilizer_available"):
            r["i"] += 1
            continue
        if kind == CARE and t.get("cared_today"):
            r["i"] += 1
            continue
        if kind == HARVEST and t.get("yield_units", 0) <= 0:
            r["i"] += 1
            continue
        if kind == FEED and inv.get("WHEAT", 0) <= 0:
            # out of wheat mid-sweep: try shed only if it has stock and the
            # detour is short; else leave the rest to free-unit rescue
            if board.shed.get("WHEAT", 0) > 0:
                shed, ds = nearest(pos, SHED_TILES)
                if ds <= 3:
                    d = step_toward(pos, shed)
                    if d:
                        return [d]
            r["i"] += 1
            continue

        if tuple(pos) == tuple(target):
            r["i"] += 1
            return [kind]
        d = step_toward(pos, target)
        if d:
            return [d]
        r["i"] += 1
        continue

    _ROUTES.pop(unit_idx, None)
    return None


def _tile_needs(board, target, what):
    t = board.tile(target[0], target[1])
    if not (isinstance(t, dict) and t.get("animal")):
        return False
    if what == "fed":
        return not t.get("fed_today")
    return True
