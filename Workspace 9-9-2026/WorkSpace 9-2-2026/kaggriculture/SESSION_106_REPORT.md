# SESSION 106 — The Mirror Wall, and the Two-Horse Play (Executed)

**Time:** 2026-09-06 ~00:40 UTC · Session 42 continuing · Mission: 3000 / #1

---

## TL;DR

**I pulled v11's live loss replays via the Kaggle API and found out exactly why we're at 2322 and not 2500+: the live pool is a WALL OF MIRRORS — forks of the same public tetsu kernel we built on — and v11 was losing the coin-flips. I then submitted BOTH new actives:**

| Submission | Ref | Time (UTC) | Status |
|---|---|---|---|
| **v4b terminal-overlay resubmit** (live-proven 2526.5) | 56043483 | 00:30 | **COMPLETE — converging (600 → ~2500 expected over ~2 days)** |
| **harvest public champion** (slot B) | 56043540 | 00:36 | PENDING → live |

Active pair = **v4b + harvest** (v11 2322.5 and v6 1998.5 displaced). Team score = max of the two (staff rule). 3 submissions remain today.

---

## 1. The Mirror Wall (why v11 loses)

v11's last 12 live games: **3W-9L**. The margins are the story:

| Episode | Opponent | Us | Them | Margin |
|---|---|---|---|---|
| 105937730 | Roshan Roy | $134,322 | $134,599 | **−$277** |
| 105934868 | goh | $93,981 | $94,690 | −$709 |
| 105947095 | Moshel | $84,066 | $84,946 | −$880 |
| 105944899 | Andrej Carpenter | $61,156 | $63,240 | −$2,084 |
| 105948761 | masspeaks | $72,576 | $77,904 | −$5,328 |
| 105954391 | Cabbage Corp | $47,594 | $49,738 | −$2,144 |
| 105955040 | Rister | $42,938 | $47,474 | −$4,536 |
| 105947681 | atl132 | $71,837 | $93,465 | −$21,628 |
| 105937597 | Joseph Adamski | $89,267 | $104,553 | −$15,286 |

**Autopsy bombshell:** Roshan Roy's revenue mix is *byte-identical* to ours — WHEAT $12,478 vs $12,478, MELON $912 vs $912. goh and Moshel: same. **These opponents run our own lineage.** The public "tetsutani shape-the-shop r5" kernel seeded a whole population of forks; v11 vs forks = coin-flips decided by fork deltas, and we're 3-9 on the flips.

The thin-margin losers dump **FERT and MILK more often and earlier** (h1-h3/h6 vs our h3/h7) — first-mover on town-drain windows.

## 2. The wool gap (the big-margin losses)

atl132 (+$21.6k) and JAdamski (+$15.3k) beat us with one asymmetry: **they sell 118-133 WOOL at ~$242/unit vs our 96** (yarn demand 450/game keeps wool scarce), while **MILK is worthless live** — the cow-saturated pool dumps it to the floor ($4/u; $488-771 total per game, vs $38k solo). Our build's biggest solo revenue stream is dead weight in the live meta.

Engine facts: `BUY_ANIMAL` is a market order `["BUY_ANIMAL", item, count]`; SHEEP $500 → wool every 3d from d6 ≈ 8 yields ≈ $1,936/sheep at live prices.

## 3. Falsified today (do not retry)

- **v12 cadence overlay** (v11 + hourly FERT/MILK/WOOL liquidation): first tape sample scored **−$4.3k vs v11**. Naive dumping ≠ the mirrors' demand-window timing. DEAD as built.
- **v13 wool-flock** (v4b + BUY_ANIMAL COW→SHEEP swap): **0-10 vs v4b, $437k vs $1.5M.** The frozen native policy's choreography is cow-coupled; herd surgery via market orders breaks placement/collection catastrophically. **Herd surgery on the frozen policy is DEAD** — the sheep-heavy design belongs in the from-scratch goose line.
- **Replay-gate control divergence:** re-running a recorded episode locally (v11 + opponent tape + exact seed) does NOT reproduce the live game ($143k local vs $94k live) — local engine/context ≠ live replay context. Tape A/B is still valid for relative comparisons, not absolute reproduction.

## 4. The harvest validation (why slot B went in today)

Ran harvest against the **tapes of the opponents that beat v11** (exact seeds):

| Tape opponent | v11 result | harvest result |
|---|---|---|
| atl132 (beat us +$21.6k) | loss $71,837 | **WIN $86,519 − $64,903** |
| Joseph Adamski (beat us +$15.3k) | loss $89,267 | **WIN $108,943 − $94,853** |
| Rister (beat us +$4.5k) | loss $42,938 | **WIN $89,693 − $68,694** |

3/3, avg margin +$19k, **and it suppresses their scores** ($64.9k/94.9k/68.7k vs what they scored against v11). Combined with 10-0 H2H vs k2900/v27/hamburger → harvest is a different archetype that contains the mirror class.

*(Loader note for future gates: poolsrc agents are single-arg `def agent(obs)` — wrap as `lambda obs, config=None: a(obs)`, NOT `a(obs, config)`; the two-arg call silently TypeErrors into a $3,000 fallback.)*

## 5. Why this exact pair (decision log)

- v4b: highest live-proven rating we've ever had (2526.5). v11 = v4b + peak-join + fert-blocker; both overlays tested +locally, **both negative live** (−528, then +327 partial recovery). Local H2H (v11 10-0 v4b) is the same trap that shipped v11 over v4b — live evidence outranks.
- harvest: upside bet in the free second slot; displaces a *declining* v11 (2456→2322 over one day).
- Kept 3 submissions in reserve for emergencies/rollback.

## 6. Next steps

1. **Watch convergence** (~2 days): v4b trajectory vs its 2526.5 prior; harvest's initial games (is it winning the mirror matchups live?).
2. **Diagnose the strb-collapse mode** — our $43-72k games (Rister, Cabbage Corp, masspeaks): strb revenue collapses to $92-739 vs $1.1-2.3k for opponents. If fixable → the biggest single lever for the tetsu line.
3. **Wool-flock design → goose line** (from scratch, not frozen-policy surgery): sheep-heavy herd + differentiated sell mix (yarn-scarce economics).
4. **Exact LB rank** (leaderboard pagination still pending).
5. Elite autopsy of kwa/keiz games via the 09-05 daily dataset (664 episodes, top avg 3027) for the 2950+ recipe.

## Artifacts

- `analysis/loss_tapes/` — 8 loss episodes (seed + opponent tape + rewards) for future gates
- `topbots/tetsu_r5_v4b_terminal.py` — reconstructed v4b (= v11 minus last two overlays, byte-truncated)
- `topbots/tetsu_r5_v12_cadence.py`, `topbots/tetsu_r5_v13_woolflock.py` — falsified, kept for the record
- `submission_v4b_resubmit.tar.gz` (root) — what went live as 56043483
- Live refs: **56043483 v4b**, **56043540 harvest**

---

## ADDENDUM (~06:00 UTC): the entrypoint law — root cause found, fix live

User check at +5h: v4b-resubmit 161.8, harvest 1330.9. Diagnosis:

**KAGGLE ENTRYPOINT LAW (critical, permanent):** the live runner resolves a file agent via
`kaggle_environments.agent.get_last_callable` = **the LAST callable in the module dict by
insertion order** — NOT the function named `agent`. Rebinding `agent` later does NOT move it to
the end (dict key keeps its first-insertion position).

What this means (all three confirmed empirically):
- **v4b-resubmit (161.8):** my truncation left `_pk_amp` (defined at line 525) as the last
  callable → Kaggle called `_pk_amp(obs, config)` as the agent → invalid actions → **$3,000
  forfeit every game** (5/5 episodes exactly $3,000). My bug, found and fixed.
- **Live "v11" (2317.3) was never v11:** its last callable = `_V6_AGENT` (binding at line 618)
  = v4b+peak-join. The fert-blocker overlay NEVER ran live. So live evidence is really:
  v4b 2526.5 > v4b+pk 2317 — the fert-blocker remains untested live.
- **Live harvest (1330.9) runs the E283 stack** (`kaggressu…_e283_agent`), not the base
  V17 `agent` I tape-validated. On the 3 loss tapes all variants (V17 / E279 / E283) play
  identically (the MoE switch never fired), so live 1330.9 ≈ V17's own level so far;
  recent live games: 1W-3L-1T incl. an exact $89,013 tie vs Astraeus (same lineage mirror).

**Fix shipped (56047687, ~05:52 UTC):** `tetsu_r5_v4b_fixed.py` = truncation + final line
`submission_agent = agent` (a fresh binding = guaranteed last callable). Verified before
upload: tar main.py sha == source, last callable == `submission_agent`.

**Live confirmation (~05:55):** first two public games:
- 106028387 vs Chase Martyn: **$175,932 vs $77,474 WIN**
- 106029374 vs Aayush Sigdel: **$166,853 vs $30,747 WIN**

**Active pair now: v4b-fixed (56047687, converging toward ~2526) + harvest E283 (56043540,
1330.9).** 2 submissions left today, held in reserve.

**New standing rule for every future submission:** before upload, `exec` the exact tar
main.py and assert the last callable in module-dict insertion order is the intended agent
(checked for 56047687 ✓).
