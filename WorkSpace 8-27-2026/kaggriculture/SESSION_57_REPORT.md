# Session 57 — H2H Tuning (Option C) + v10.5 Ship

## Where we are
- Solo: **$80,007 (10 seeds)** — unchanged from S55
- H2H BT: **-$86,953** (was -$86,698 S55; effectively same)
- H2H V41: **-$101,822** (was -$120k in S54 — **-$20k improvement**)
- H2H soil: **-$101,948** (was -$121k in S54 — **-$20k improvement**)
- Ship: `main.py` = v10.5 (candidate concatenated from custom/)
- v10.5 submitted to Kaggle (ID 55748620, 1 submission remaining today)

## Diagnostic finding from BT trace

Ran per-turn trace vs BT seed 1. Key discoveries:
- **D0-D4 WE lead** by $200-680 (custom faster early)
- **D5-D10 BT explodes** to $18k lead. Source: BT dumps 145 fert + 66 melon at D10
- BT has **4 animals by D1** (we have 0-2). Placed sheep+cow from D0 purchase
- BT plants **15 melon + 19 straw** by D10 in NW+NE

BT's trick: buy animals D0 immediately (uses $2500 of $3000 starting cash)
then aggressively BUY_PRODUCT wheat from market to feed them. Builds herd
4-6 by D4 while we're still at 0-1.

## What worked (+$20k on hard opps)

**Price-gated melon selling** — hold melon in shed when price crashes below $100.
- V41: -$120k -> -$102k (+$18k)
- soil: -$121k -> -$102k (+$19k)

**Price-gated strawberry selling** — sell only when price >= $120 base (unless
end-game). Marginal.

## What failed

1. **Buy animals D0 aggressively** (BT-style): solo dropped $80k -> $26k. Emergency wheat buy can't keep up when we blow $2500 on animals D0.
2. **Buy fert cheap for strawberry doubling**: FERT buy pushed our own inventory up, own price down. Hurt.
3. **Staggered melon selling** (max 2/turn): shed fills, blocks other things.
4. **Bumping wheat pri**: kills plants (water starves).
5. **Removing melon**: much worse (melon = our advantage).
6. **Skipping COW row 4 layout swap**: net negative.

## H2H vs all top opps

| opp | S54 | S55 | **S57** | delta |
|---|---:|---:|---:|---:|
| BT | -$89,706 | -$86,698 | -$86,953 | ~= |
| V41 | -$120k | -$120k | **-$101,822** | **+$18k** |
| moon | ~-$90k | -$90k | -$85,547 | +$5k |
| soil | -$120k | -$121k | **-$101,948** | **+$19k** |
| amey | -$90k | -$90k | -$85,547 | +$5k |
| multiroute | -$90k | -$90k | -$85,934 | +$4k |

**Biggest gains vs V41/soil**: our worst matchups improved most because they
dump fert/melon into shared market and our price gate stops us from making
it worse.

## Ship state

| submission | id | notes | public score |
|---|---|---|---:|
| S42 breaking_tie (verified) | 55716221 | | 1862.6 |
| v10 custom (S56 ship) | 55730309 | | 571.6 |
| revert BT (S56) | 55730353 | | 2129.8 |
| BT again (unknown submitter) | 55730825 | | **2192.1** |
| **v10.5 (S57 ship)** | **55748620** | melon price gate | **pending** |

Note: 55730825 is a mystery — public score 2192.1 higher than any of our BT
submissions. Not sure what shipped there. Could be a re-submission from user.

## Progression

| session | solo | H2H BT | ladder |
|---|---:|---:|---:|
| S47 v2 | $22,278 | -$131k | — |
| S48 v3 | $28,962 | -$126k | — |
| S49 v4 | $43,556 | -$121k | — |
| S50 v5 | $56,292 | -$120k | — |
| S51 v6 | $60,890 | -$108k | — |
| S52 v7 | $70,307 | -$100k | — |
| S53 v8 | $77,214 | -$93k | — |
| S54 v9 | $81,696 | -$90k | — |
| S55 v10 | $80,007 | -$87k | 571 (pending ladder time) |
| **S57 v10.5** | $80,007 | -$87k | shipped, awaiting |

## Ideas that failed but noted

- Aggressive D0 animal buy (needs bigger cash reserve engineering)
- BUY fert cheap (creates own glut)
- Stagger melon sells (shed capacity issue)
- Region-specialized hands (multiple failures over sessions)

## Ideas remaining

- Ship v10.5, see ladder score after 24h
- Try shipping alternative bots (v41, moon) to see if any tops BT's 2192
- Study the mystery 55730825 submission for insight

## Files touched
- `economy.py` — MIN_MELON_PRICE=100 gate, straw >=120 gate,
  end-game melon skip if price < 30
- `main.py` = v10.5 (rebuilt from custom/)
- `agent/custom_v10_bak_from56/` — v10 snapshot
- `SESSION_57_REPORT.md`
