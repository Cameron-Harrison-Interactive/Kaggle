# Session 45 — Ryo Tape Extraction + Adaptive Wrapper Test

## What you asked for

"Build a stronger tape but keep our layers from 35"

## What I did

### Step 1: Extract top-5 bots' actual replays

Used Kaggle API to walk the episode graph and find current submission IDs
for the top 8 teams (Ryo Hasegawa rank 1, Subramanya N rank 2, etc). Pulled
30 recent replays of **Ryo Hasegawa (rank #1, score 3140)** — the actual
top-1 bot on the ladder. Their **farmer + hands actions are visible** in
the replay JSON (unlike the hash-obscured top-10 dataset).

### Ryo's opening (D0)

100% deterministic across all 30 replays:

```
BUILD_PASTURE + 5 HIRES + BUY_ANIMAL SHEEP 3 + BUY_ANIMAL COW 1
+ BUY_SEED MELON 11 + BUY_SEED WHEAT 6 + BUY_PRODUCT WHEAT 4
```

Different from the meta consensus (c2s2 + MELON 12). Ryo goes **c1s3 with
MELON 11**.

### Ryo's tape doesn't replay

Extracted canonical tape (most common action per turn across 30 games)
and tested it on the same seeds Ryo actually played:

- **Seed 1891858796**: canonical tape = **$2,222**, actual Ryo = **$108,361**
- Diff: **−$106,139**

Reason: Ryo's bot is heavily ADAPTIVE from D1 onwards. Only 110/720 turns
have hand actions ≥80% consistent. The tape approach fails when the game
state diverges from what Ryo expected.

Ryo is 20/30 (67% win rate) against top-tier opponents — even they don't
dominate consistently.

### Step 2: Build BT + Session-35 adaptive layers wrapper

Built a hybrid where `breaking_tie` drives all farmer/hands/primary market
actions and adaptive layers ADD to unused slots. Layers wrapped in:

1. **Price momentum dump** (from Session-35): 5-day rolling price history,
   dumps surplus when price drops ≥3% below 5-day max
2. **Fertilizer surplus sell**: unload if shed >25 fert and price ≥$50
3. **Land override**: buy SW quad at D9+ if BT hasn't and we have $3,500+
4. **Opponent classifier**: fingerprint opp D0-D3 (currently logging only)

### Test results — each layer isolated

Against moon + amey + multiroute (24 games total per config):

| config | wins/24 | total | avg |
|--------|:-------:|------:|----:|
| **baseline BT alone** | **19/24** | **+$23,851** | **+$994** ★ |
| momentum layer only | 17/24 | +$20,154 | +$840 |
| fert-surplus only | 19/24 | +$23,851 | +$994 (no-op) |
| land-override only | 19/24 | +$23,851 | +$994 (no-op) |
| all three | 17/24 | +$20,154 | +$840 |

**Momentum layer HURTS** us by $154/game. It fires on false positives (short
price dips that recover). Fert + land are no-ops in these games (BT already
handles them well).

### The honest conclusion

**BT is already so well-tuned that our adaptive additions can only match it
at best, and typically hurt.** The Session-35 layers were designed for a
production bot that under-uses market slots. BT uses market slots
efficiently already, leaving no room for adaptive layers to add value.

## What I shipped

**`main.py` = Session-42 breaking_tie, unchanged.** All experiments reverted.

Verified via smoke test: last callable `_kaggle_submission_entrypoint`,
$167,943 vs PASS seed 1 via kaggle_environments.make.

## Why the top-5 push is hard

I explored three real paths this session:

1. **Extract & replay top-1 (Ryo) tape** — doesn't work (adaptive, state-dependent)
2. **Wrap BT with Session-35 adaptive layers** — layers don't fire or hurt
3. **Rebuild Session-35 with meta production** — architectural incompatibility (documented in Session 44)

**The real path to top-5 is genuine multi-session custom development** where
we write a bot from scratch that:
- Matches BT/moon's mechanical efficiency (max market slots, aggressive land buys)
- Adds true adaptive intelligence (opp modeling → sell timing)
- Tests each subsystem against ADAPTIVE opponents (not static replays)

That's real work over multiple sessions, not one session of tape extraction.

## What we have going forward

Current bot (Session-42 BT):
- 71% head-to-head win rate against 5 other top public bots
- 25/29 wins vs 29 real Kaggle opponent replays  
- Avg margin +$7,954 per game
- ~2800-3000 estimated rating (currently what BT shipped as)

To exceed this we need to write custom code that outperforms every public
notebook. That's not one session of tweaking. That's real ML/game-theory
engineering.

## Backups preserved

- `main.py` (shipped = Session-42 breaking_tie)
- `main.py.bak_session43_selfaware_attempt` (session 43 layers)
- All prior sessions preserved
