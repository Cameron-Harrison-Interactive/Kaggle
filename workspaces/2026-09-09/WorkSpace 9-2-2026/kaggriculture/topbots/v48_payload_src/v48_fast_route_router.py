"""Sparse current-meta routing over real fast-climber trajectories.

The default remains the validated v43/v44 backbone.  Only public shop events
with a measured held-out advantage select a different continuation:

* first shop YARN_STORE -> Kaileh57 train-only YARN continuation at step 88;
* first shop FARMERS_MARKET -> taiseiu train-only continuation at step 120;
* later YARN branches retain the validated v44 continuations.

Exactly one child policy is evaluated per turn.  This is both cheaper and
safer than advancing every expert, which can breach the one-second hosted
action budget when each child has its own closed-loop controller.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scripts.v19_terminal import terminal_market
from v23.planner import PlannerConfig, build_sparse_planner
from v23.state_encoder import get
from v44.gold_floor import (
    CloneSellPreemption,
    GoldFloorConfig,
    bakery_capital_candidate,
)


ROUTES = (
    "default",
    "yarn_fast",
    "farm_fast",
    "yarn_second",
    "yarn_third",
    "bakery_capital",
)


@dataclass(frozen=True)
class FastRouteConfig:
    yarn_first_start: int = 88
    farm_first_start: int = 120
    yarn_second_start: int = 153
    yarn_third_start: int = 216
    yarn_third_prefixes: tuple[tuple[str, str], ...] = (
        ("BRUNCH_SPOT", "PET_CAFE"),
        ("PET_CAFE", "FARMERS_MARKET"),
    )
    terminal_rule: str = "collision"


def _shops(obs: Any) -> list[str]:
    town = get(obs, "town", {}) or {}
    return [str(value) for value in (get(town, "unlocked_shops", []) or [])]


def route_event(obs: Any, config: FastRouteConfig) -> str | None:
    """Return a newly visible continuation event, or ``None``."""
    step = int(get(obs, "step", 0) or 0)
    shops = _shops(obs)
    if (
        shops
        and shops[0] == "YARN_STORE"
        and step >= int(config.yarn_first_start)
    ):
        return "yarn_fast"
    if (
        shops
        and shops[0] == "FARMERS_MARKET"
        and step >= int(config.farm_first_start)
    ):
        return "farm_fast"
    if (
        len(shops) >= 2
        and shops[0] not in {"YARN_STORE", "FARMERS_MARKET"}
        and shops[1] == "YARN_STORE"
        and step >= int(config.yarn_second_start)
    ):
        return "yarn_second"
    allowed = {
        (str(first), str(second))
        for first, second in config.yarn_third_prefixes
    }
    if (
        len(shops) >= 3
        and shops[0] not in {"YARN_STORE", "FARMERS_MARKET"}
        and shops[1] != "YARN_STORE"
        and shops[2] == "YARN_STORE"
        and (not allowed or (shops[0], shops[1]) in allowed)
        and step >= int(config.yarn_third_start)
    ):
        return "yarn_third"
    return None


def build_fast_route_router(
    routes: dict[str, list[dict]],
    config: FastRouteConfig = FastRouteConfig(),
    gold_config: GoldFloorConfig = GoldFloorConfig(
        clone_preempt_horizon=2,
        clone_streak_required=24,
        clone_distance_threshold=2.0,
        clone_detection_start=48,
        clone_maximum_batch=10,
        clone_active_start=160,
        terminal_rule="collision",
    ),
):
    expected = set(ROUTES)
    if set(routes) != expected:
        raise ValueError(
            f"expected routes {sorted(expected)}, received {sorted(routes)}"
        )
    if any(len(routes[name]) != 719 for name in expected):
        raise ValueError("every route must contain exactly 719 actions")

    children = {
        name: build_sparse_planner(routes[name], PlannerConfig())
        for name in ROUTES
    }
    preemption = CloneSellPreemption(routes, gold_config)
    selected = {0: "default", 1: "default"}
    last_step = {0: -1, 1: -1}
    telemetry = {
        "calls": 0,
        "selected": {name: 0 for name in ROUTES},
        "route_events": {name: 0 for name in ROUTES if name != "default"},
        "child_calls": 0,
    }

    def agent(obs: Any, configuration: Any = None) -> dict:
        seat = 1 if int(get(obs, "player", 0) or 0) == 1 else 0
        step = int(get(obs, "step", 0) or 0)
        if step == 0 or step < last_step[seat]:
            selected[seat] = "default"
        last_step[seat] = step

        if selected[seat] == "default":
            event = route_event(obs, config)
            if event is None and bakery_capital_candidate(obs, gold_config):
                event = "bakery_capital"
            if event is not None:
                selected[seat] = event
                telemetry["route_events"][event] += 1
        route_name = selected[seat]

        # Only the selected expert runs.  The weed controller explicitly
        # supports a first call at a late continuation decision point.
        result = children[route_name](obs, configuration)
        telemetry["child_calls"] += 1
        result = preemption.apply(
            obs, result, route_name, configuration
        )
        if step == 718 and str(config.terminal_rule) != "none":
            result = terminal_market(
                obs,
                result,
                rule=str(config.terminal_rule),
                replace=True,
            )

        telemetry["calls"] += 1
        telemetry["selected"][route_name] += 1
        return result

    agent.children = children
    agent.preemption = preemption
    agent.selected = selected
    agent.telemetry = telemetry
    agent.fast_route_config = config
    agent.gold_floor_config = gold_config
    return agent
