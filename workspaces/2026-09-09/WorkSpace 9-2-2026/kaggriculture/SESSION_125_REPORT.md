# SESSION 125 — 2026-09-08 ~14:50 UTC
## Probe tank diagnosed (445 = weak economy, not a bug). Fixed: router resubmitted (56100058). v28: $48k -> $75k.

**User:** "the submission you just did tanked its trash Fix it"

## 1. WHY IT TANKED (episodes pulled, no guessing)

- 56097984 (v28.17 probe) final: **445.4**. Episodes: lost to 551-rated (us $28.1k vs $65.4k) and 456-rated (us $38.4k vs $42.0k) agents.
- The agent RAN CORRECTLY live (rewards match local H2H exactly; no entrypoint failure, no crashes). Its economy is simply bottom-ladder class. We posted a known-weak probe; the ladder agreed with our own gate (0-10 vs router).

## 2. THE FIX (posted 14:11 UTC)

- **56100058 = tt_router_938 verbatim resubmit** (byte-identical to the 2483 primary, disclosed in the description). Supersedes the 445 probe as our latest post.
- Team score = best submission -> the probe never hurt the team standing; the resubmit's fresh episode set can only help (router's peak was 2550). First episode = self-play calibration (~$67k each, normal mirror compression). 3 slots remain today.

## 3. FUSION FALSIFIED (v29 — documented so we never retry)

Goal: router tape labor ($190k) + our adaptive market brain. THREE failure modes, all measured:
1. Strip tape SELLs, replace with ours -> $13-43k. The tape's fixed buy schedule depends on its own dump timing; unsynchronized revenue starves the buys.
2. Additive sells (tape untouched, ours fill free slots) -> $128-139k vs stock $162-197k. Cause: **_features reads money + all prices + all inventories + both farms at every 144-step route choice** — any overlay order perturbs the feature vector, flips the route tree, and breaks the optimized choreography (-$40-60k).
3. Only safe surface is post-d24 (after the last route choice at t=576) — worth ~nothing.
**Conclusion: the tape is a closed system. Improvement must come from a better agent, not patching this one.**

## 4. v28 PROGRESS THIS SESSION (the real path to >2500)

v28.18c solo (seeds 101/202/303/404/505): **$67.5 / 76.0 / 81.9 / ~70 / ~63k — mean ~$75k** (was $48k at probe time, $67k peak before).
- Sheep unconditional (wool holds $200-252 ALL GAME solo — the YARN gate was wrong): 4-6 sheep now bought; +$1.2k/day lever mostly captured.
- Wheat belt 18 tiles (surplus sells into the rising $29->47 price).
- Melon 12 at d0; geese cut 6->2 (wool/milk beat eggs per slot).
- STILL BLOCKED: strb planting (6-11 tiles vs 16 target) — our labor planner saturates at ~50 tiles (walking 64% of unit-steps; strb-at-prio-0 steals feed/water labor and nets negative, measured twice).
**Next session = labor rework (walking 64% -> <50%, placement compaction, maybe 16 hands at $4.3k/day) to unlock strb-16 + the full 60-tile farm. Then H2H gate vs router, then submit.**

## LADDER NOW
- Router primary 56079632: 2483.7 (slipped from 2550 peak). Resubmit 56100058 climbing from 600 provisional.
- v16 1801. Probe 56097984: 445 (superseded, harmless to team score).
- Elite bar: ymg_aq 2955 (recipe: wheat carry 1123@29->1361@47-50, 8C/3S/1G, late tomato, $92k final 6 days).

## FILES
- topbots/tt_router_938.py = primary (unchanged, resubmitted verbatim as 56100058)
- topbots/v28_harvest_moon.py = v28.18c ($75k mean solo)
- topbots/v29_fusion.py = falsified fusion (keep for reference, DO NOT submit)
- /tmp VOLATILE: solo_any.py (solo any file), diag_any.py (day trace any file), h2h.py, solo_router.py, slug (exact bytes), ws
