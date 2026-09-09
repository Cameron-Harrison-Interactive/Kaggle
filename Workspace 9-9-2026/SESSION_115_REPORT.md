# SESSION 115 — The Build Session: 4 Falsifications, 1 New Door, Both Winners Live

**Time:** 2026-09-07 05:20 UTC · User: "Work on that build — we have hours until we can post."

---

## Build attempts tonight (all gated before any submission)

| Build | Idea | Solo result | Mechanism of failure |
|---|---|---|---|
| v18 strb→tomato | swap hamburger's 44 strb plants for tomato (keiz's niche) | **−$53-60k** | Tomato is ANNUAL (one harvest); strb is perennial i2 (repeat harvest). Swapped a repeat-harvester for a one-shot crop: 217u → 16u. |
| v19 melon→tomato | lifecycle-matched swap (both annual) | **−$15-66k** | Ripening timing differs → hand-cycle desyncs → missed harvests cascade: strb volume −43% (216u→123u) even though strb was untouched. |
| v20 keiz tape | replay keiz's (#4, 2857) own 720-step tape — the elite chassis | 56% fidelity, $45k | keiz is ADAPTIVE: blind tape misses cash timing → buys fail → FEED ops miss → **herd starves to 1 cow by d20**. The 30-tomato build never materializes. |
| v21 keiz + premium sells | add our market layer on keiz's tape | ±$0 | Shed is empty at premium hours — the failure is upstream (cash cascade), not sell timing. |

**The complete falsification map (now mechanistic, no mysticism):**
- Compiled tetsu blob: market-ADDITIVE edits only (v16 = the one that works)
- Readable hamburger trace: crop swaps break it two ways — lifecycle class and ripening timing both desync the hand choreography
- Elite tapes: unreplayable (adaptive cash + feeding)

## The new door: PASS-mining

The hamburger trace wastes many hand turns on `['PASS']` — especially late-game — while melon
tiles sit bare after their annual harvest (9-21 tiles by d24). An overlay that REPLACES PASS
ops with useful ops (PLANT WHEAT/TOMATO on bare tiles, then HARVEST) cannot desync the
choreography: the hand spends its turn either way, positions unchanged. Seeds cost ~$50 from
late-game surplus cash (negligible — v15's failure was spending EARLY cash). Estimated
+$3-5k/game of truly additive production. **This is tomorrow's build session.**

## 📢 SUBMITTED at quota reset (05:16 UTC)

1. **56069471 v4b** — control, the 2526-class winner verbatim
2. **56069472 v16** — treatment, same winner + premium-window liquidation
   (milk h1/h14/h18/h22 vs the h7 trough; strb liquidated ≥$180 before the permanent
   $1 floor). Margin-gated +$640/game over v4b on 17 real tapes, zero flips.

Displaced: 2900-verbatim (1208, dead) and hamburger (820, twin-capped — overnight data
confirmed the diagnosis). **Actives = our winner and our winner+fix. 48h undisturbed.**

## Overnight scoreboard (the copy-chase verdict, final)

| Submission | Final-ish | vs our own winner |
|---|---|---|
| v4b-fixed | 2079.1 | — |
| 2900-verbatim | 1207.8 | −871 |
| hamburger | 820.3 | −1259 |

Every public-notebook copy finished far below the class we already owned. Lesson banked.

## Files
- topbots/hamburger_tomato_v18.py, v19 (falsified, kept for record)
- topbots/keiz_tape_v20.py (falsified chassis)
- submission_MIDNIGHT_v4b.tar.gz / submission_MIDNIGHT_v16.tar.gz (live)
