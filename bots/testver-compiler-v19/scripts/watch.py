"""watch.py — watch our bot play, visually.

Default: OUR BOT vs OUR BOT (self-play) so you can compare different starts:
    python scripts/watch.py             # self-play, seed 1
    python scripts/watch.py 7           # self-play, seed 7
    python scripts/watch.py 7 starter   # or any opponent: starter/random/pass/<path>

Kaggle episodes:
    python scripts/watch.py --latest              # our newest live match
    python scripts/watch.py --episode 91134600    # any episode id

Outputs data/watch/match.html (visual replay, auto-opens in your browser)
plus a per-day stats table in the console.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
AGENT = os.path.join(ROOT, "agent", "main.py")
WATCH_DIR = os.path.join(ROOT, "data", "watch")
os.makedirs(WATCH_DIR, exist_ok=True)


def _kaggle_token_env():
    env = dict(os.environ)
    if "KAGGLE_API_TOKEN" not in env:
        tok = os.path.expanduser("~/.kaggle/access_token")
        if os.path.exists(tok):
            with open(tok) as f:
                env["KAGGLE_API_TOKEN"] = f.read().strip()
    return env


def fetch_episode(episode_id):
    out = os.path.join(WATCH_DIR, f"episode-{episode_id}-replay.json")
    if not os.path.exists(out):
        print(f"[watch] downloading episode {episode_id} ...")
        subprocess.run(["kaggle", "competitions", "replay", str(episode_id),
                        "-p", WATCH_DIR], check=True, env=_kaggle_token_env())
    return out


def _table_rows(stdout):
    rows = []
    for l in stdout.splitlines():
        parts = l.split()
        if parts and parts[0].isdigit() and len(parts) >= 3:
            rows.append(parts)
    return rows


def latest_episode():
    res = subprocess.run(["kaggle", "competitions", "submissions", "kaggriculture"],
                         capture_output=True, text=True, env=_kaggle_token_env())
    subs = _table_rows(res.stdout)
    if not subs:
        raise SystemExit("no submissions found")
    sub_id = subs[0][0]
    print(f"[watch] latest submission: {sub_id} ({subs[0][1]})")
    res = subprocess.run(["kaggle", "competitions", "episodes", sub_id],
                         capture_output=True, text=True, env=_kaggle_token_env())
    eps = _table_rows(res.stdout)
    if not eps:
        raise SystemExit("no episodes yet for that submission")
    ep = eps[0][0]
    print(f"[watch] newest episode: {ep}")
    return ep


def summarize_replay(path):
    with open(path) as f:
        rp = json.load(f)
    steps = rp["steps"]
    names = rp.get("info", {}).get("TeamNames", ["p0", "p1"])
    rewards = [s.get("reward", 0) for s in steps[-1]]
    print(f"\n{'='*72}")
    print(f" {os.path.basename(path)}")
    print(f" {names[0]} ${rewards[0]:,.0f}   vs   {names[1]} ${rewards[1]:,.0f}")
    print(f"{'='*72}")
    hdr = f"{'day':>3}"
    for pi in (0, 1):
        hdr += f" | {'$':>7} {'an':>2} {'cr':>2} {'wd':>2}  hires"
    print(hdr + "   (left=%s right=%s)" % (names[0][:10], names[1][:10]))

    series = [{}, {}]
    sells = [{}, {}]
    buys_wheat = [0, 0]
    sold_wheat = [0, 0]
    for si, step in enumerate(steps):
        day = si // 24
        for pi in (0, 1):
            obs = step[pi].get("observation") or {}
            farm = (obs.get("farms") or [None, None])[pi] if obs.get("farms") else None
            if farm:
                an = cr = wd = 0
                for row in farm.get("tiles", []):
                    for t in row:
                        if isinstance(t, dict):
                            if t.get("animal"):
                                an += 1
                            elif t.get("kind") == "PLANT":
                                cr += 1
                            elif t.get("kind") == "WEED":
                                wd += 1
                series[pi][day] = (farm.get("money", 0), an, cr, wd,
                                   farm.get("hires_today", 0))
            act = step[pi].get("action") or {}
            if isinstance(act, dict):
                for o in act.get("market", []) or []:
                    if not o:
                        continue
                    if o[0] == "SELL":
                        sells[pi][o[1]] = sells[pi].get(o[1], 0) + o[2]
                        if o[1] == "WHEAT":
                            sold_wheat[pi] += o[2]
                    elif o[0] == "BUY_PRODUCT" and o[1] == "WHEAT":
                        buys_wheat[pi] += o[2]

    days = sorted(set(series[0]) | set(series[1]))
    for d in days:
        line = f"{d:>3}"
        for pi in (0, 1):
            m, an, cr, wd, h = series[pi].get(d, (0, 0, 0, 0, 0))
            line += f" | {m:>7,.0f} {an:>2} {cr:>2} {wd:>2} {h:>6}"
        print(line)

    for pi in (0, 1):
        print(f"\n-- {names[pi]}: wheat bought={buys_wheat[pi]} sold={sold_wheat[pi]}"
              f" (net {sold_wheat[pi]-buys_wheat[pi]:+d})")
        print("   sold:", ", ".join(f"{k}:{v}" for k, v in sorted(sells[pi].items())))


def local_match(opponent, seed):
    from kaggle_environments import make
    who = "OUR BOT vs OUR BOT (self-play)" if opponent == "agent/main.py" else f"agent/main.py vs {opponent}"
    print(f"[watch] simulating: {who} (seed {seed}) ...")
    env = make("kaggriculture", configuration={"episodeSteps": 720, "seed": seed})
    env.run([AGENT, opponent])
    p0 = env.steps[-1][0].reward or 0
    p1 = env.steps[-1][1].reward or 0
    print(f"[watch]   US ${p0:,.0f}   OPP ${p1:,.0f}   "
          f"{'WIN' if p0 > p1 else 'LOSS' if p0 < p1 else 'TIE'}")

    replay = env.toJSON()
    rpath = os.path.join(WATCH_DIR, "match_replay.json")
    with open(rpath, "w") as f:
        json.dump(replay, f)

    print("[watch] rendering HTML replay ...")
    try:
        html = env.render(mode="html")
        hpath = os.path.join(WATCH_DIR, "match.html")
        with open(hpath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[watch] saved {hpath}")
        import webbrowser
        url = "file://" + os.path.abspath(hpath)
        print(f"[watch] opening {url} in your browser ...")
        try:
            webbrowser.open(url)
        except Exception:
            print("[watch] (could not auto-open — open the file manually)")
    except Exception as e:
        print(f"[watch] HTML render skipped: {e}")

    summarize_replay(rpath)


def render_kaggle_replay(path):
    """Render a downloaded Kaggle replay JSON into the visual HTML player."""
    try:
        from kaggle_environments import make

        class StepObj(dict):
            """dict that also supports attribute access (the renderer reads
            .reward/.status but json.dumps needs a real dict)."""
            __getattr__ = dict.get

        with open(path) as f:
            replay = json.load(f)
        env = make("kaggriculture", configuration={"episodeSteps": 720})
        wrapped = []
        for step in replay["steps"]:
            row = []
            for st in step:
                o = StepObj(st)
                o.setdefault("reward", 0)
                o.setdefault("status", "DONE")
                row.append(o)
            wrapped.append(row)
        env.steps = wrapped
        env.state = env.steps[-1]
        html = env.render(mode="html", playing=True, controls=True)
        hpath = os.path.join(WATCH_DIR, "match.html")
        with open(hpath, "w", encoding="utf-8") as f:
            f.write(html)
        print(f"[watch] saved visual replay -> {hpath}")
        import webbrowser
        url = "file://" + os.path.abspath(hpath)
        print(f"[watch] opening {url} in your browser ...")
        try:
            webbrowser.open(url)
        except Exception:
            print("[watch] (could not auto-open — open the file manually)")
    except Exception as e:
        print(f"[watch] visual render of Kaggle replay skipped: {e}")
        print("[watch] (stats above are complete; visual viewer works for local matches)")


def main():
    args = sys.argv[1:]
    if args and args[0] == "--episode":
        path = fetch_episode(int(args[1]))
        summarize_replay(path)
        render_kaggle_replay(path)
    elif args and args[0] == "--latest":
        path = fetch_episode(int(latest_episode()))
        summarize_replay(path)
        render_kaggle_replay(path)
    else:
        # default: SELF-PLAY (our bot vs our bot) — compare starts by seed
        seed = 1
        opponent = os.path.join(ROOT, "agent", "main_v14_5.py")  # v15 AdaptivePortfolio vs 14.5
        for a in args:
            if a.isdigit():
                seed = int(a)
            else:
                opponent = a
        local_match(opponent, seed)


if __name__ == "__main__":
    main()
