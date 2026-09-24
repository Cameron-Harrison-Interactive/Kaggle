# SESSION 112 — "Something You're Doing Is Wrong" — The Data Answer

**Time:** 2026-09-06 ~20:20 UTC · User: "You keep saying they are capped but other people are
winning top 10 with them. So something you're doing is wrong."

---

## You were right. Here's exactly where.

**1. The top-10 run OUR build.** Fresh census of the 09-04 daily #1 and current top-10:

| Player | rating | herd | crops | differentiator |
|---|---|---|---|---|
| Jesse Bullard (09-04 #1) | ~2900s | 9C+5S | 23 WHEAT + 38 STRB + 6 TOMATO | milk premium $181/u |
| keiz (#4 now) | 2857 | 11C+11S+1G | 18 WHEAT + 32 STRB + **30 TOMATO** | wheat 1,495u @$40-44 |
| Mater Welon | top-10 | 8C+9S | 24 WHEAT + 33 STRB | milk 226u @$202 windows |

That is the same family as our tetsu/v4b class (we run 9C/8S/24W/33S/12M). **The class is
not trash and not capped by nature.** What they have that the compiled blob lacks:

- **Sell-hour discipline:** elite wheat sells h1-h2 (night band); premium milk h14/h18/h22/h0.
  Our blob: wheat h19/h22, milk h7/h8 — the crowded windows (verified in live replays tonight).
- **A niche anchor:** keiz's 30 tomato tiles, winners' carrot $3.8-4.8k. We run 12 melon (contested).
- Their engines are **their own readable code** — they tuned the windows in. Ours is a compiled
  blob: every one of the 5 overlay mechanisms we tried to move sell hours / portfolio was
  falsified (v12 adds, v13 herd, v14 delays, v15 buys, melon-timing) — the schedule is baked.

**2. The part that IS my fault — slot management.** v4b's 2526 came from an undisturbed ~20h
convergence run. Since then we benched our winners mid-climb to chase other people's
notebooks: harvest 1330, route 1220, hamburger 824-capped — **every one finished below what
our own winner already had.** Reading v4b-FIXED's 2086@13h as "capped" was premature — the
2526 run was at a similar point at 13h. That's the error. No more of it.

## Midnight plan (00:00 UTC, ~3.6h) — BOTH slots to our winners

1. **v4b-FIXED** (submission_MIDNIGHT_v4b.tar.gz — verbatim 2526-class, last callable
   `submission_agent` ✓) → displaces the stalled 2900-verbatim.
2. **v11** (submission_MIDNIGHT_v11.tar.gz — the file as-is; last callable `_V6_AGENT` =
   base+cleanup+peak-join = **the exact agent that scored 2322.5 live**, verified: 23 fert
   buys in its live replay, fert-blocker never ran) → displaces hamburger.
3. **Commitment: no displacement for 48h.** Both converge fully. Team score = better of the
   two. 3 slots held in reserve.

## The real "fix it" (starts tomorrow)

Own readable engine, elite recipe: wheat-fert loop base + night-band wheat sells + premium
milk windows + tomato/carrot niche anchor. The from-scratch line died on labor planning —
fix: graft a proven 720-step labor route (hamburger's readable route) and write only the
market layer ourselves. That is "our main winner, fixed" at the level that actually plays
the top-10's game.
