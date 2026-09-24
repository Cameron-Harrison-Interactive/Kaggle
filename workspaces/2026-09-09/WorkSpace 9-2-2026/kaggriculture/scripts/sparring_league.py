"""Sparring league: test candidate bots against EXACT live opponents.

Method (validated 2026-09-04, episode 105328506):
  1. A live replay contains info.seed — the game's exact seed.
  2. Opponent action streams (steps[s+1][ag]['action'], s=0..718) replayed
     in GameSim(seed) with our candidate reproduce the LIVE game to the coin
     when our candidate is the same bot (exact match on all 12 tested).
  3. => recorded opponent streams are valid sparring partners (field tapes
     are state-independent enough); swap our seat to test any candidate.

Usage:
  python3 scripts/sparring_league.py replay_dir candidate1.py:agent candidate2.py:kaggle_agent_v58 ...
Replays: `kaggle competitions replay <episode_id>` per episode of interest
(episode list via `kaggle competitions episodes <submission_id>`).
"""
import glob, importlib.util, json, os, sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from sim import GameSim


def load_agent(path, attr):
    spec = importlib.util.spec_from_file_location("cand_" + os.path.basename(path), path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    obj = getattr(m, attr) if attr else None
    if obj is None:
        for name in ("agent", "kaggle_submission_entrypoint", "main"):
            if hasattr(m, name):
                obj = getattr(m, name); break
    return obj


def call(fn, obs):
    try:
        return fn(obs, None)
    except TypeError:
        return fn(obs)


def build_league(replay_dir):
    league = []
    for f in sorted(glob.glob(os.path.join(replay_dir, "episode-*-replay.json"))):
        d = json.load(open(f))
        names = d["info"]["TeamNames"]; seed = d["info"]["seed"]
        if len(names) != 2:
            continue
        # opponent = the seat that is NOT us; works for any team name filter
        me_idx = 0 if "Harrison" in names[0] else 1
        opp = 1 - me_idx
        stream = [(d["steps"][s + 1][opp].get("action") if s + 1 < len(d["steps"]) else None) or {}
                  for s in range(719)]
        rw = [s.get("reward") for s in d["steps"][-1]]
        league.append(dict(opp=names[opp], seed=seed, opp_seat=opp,
                           stream=stream, live_margin=rw[me_idx] - rw[opp]))
    return league


def test_candidate(agent, league):
    res = []
    for g in league:
        sim = GameSim(seed=g["seed"])
        for s in range(719):
            o0, o1 = sim.obs(0), sim.obs(1)
            if g["opp_seat"] == 0:
                sim.step(g["stream"][s], call(agent, o1))
            else:
                sim.step(call(agent, o0), g["stream"][s])
        res.append((g["opp"], sim.money(1 - g["opp_seat"]) - sim.money(g["opp_seat"]),
                    g["live_margin"]))
    return res


if __name__ == "__main__":
    replay_dir = sys.argv[1]
    league = build_league(replay_dir)
    print(f"league: {len(league)} games")
    for spec_arg in sys.argv[2:]:
        path, _, attr = spec_arg.partition(":")
        agent = load_agent(path, attr or None)
        res = test_candidate(agent, league)
        w = sum(1 for _, m, _ in res if m > 0)
        print(f"\n{path}: {w}W-{len(res)-w}L")
        for o, m, lm in res:
            print(f"  {o[:24]:24s} local {m:+9,.0f} (live {lm:+9,.0f})")
