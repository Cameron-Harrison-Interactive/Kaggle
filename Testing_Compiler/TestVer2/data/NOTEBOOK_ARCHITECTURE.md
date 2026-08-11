# Notebook Architecture (why water overlays failed)

Sources read 2026-08-10:
1. [Kaito — 15/16 Strict-Future v25 Meta Reset](https://www.kaggle.com/code/kaitofukami/15-16-strict-future-v25-meta-reset) (LB ~3013)
2. [Rayk — Findings from Zero to Top Meta](https://www.kaggle.com/code/raykkretzschmar/kaggriculture-findings-from-zero-to-top-meta) (LB ~2955)
3. [Tetsu — Adaptive Farming Strategy](https://www.kaggle.com/code/tetsutani/adaptive-farming-strategy-for-kaggriculture)

## The consensus architecture (all three)

```
fit-only complete 719-step route backbone
        ↓
observed WEED only → actor-local DIG + replay
        ↓
2+ route-existing SELLs → rank by price-impact + Town demand
        ↓
otherwise → exact route action
```

### Production invariants (Kaito §5)
- ordinary turns create/delete/resize **no SELL**
- SELLs only **permuted** inside existing slots
- BUY/HIRE/land/seed/animal stay in original slots
- farmer/hands follow **one complete route** except observed WEED
- no opponent identity fields at runtime

### Tetsu thesis
> Use the route for economics; use live state only where execution or queue order can drift.
> Quantity discipline: ordinary runtime does not create, delete, or resize planned SELL volume.

### Kaito closed-loop warning
- Freezing Seb's adaptive **trace** scored **0/50** — a top replay is one path, not a portable policy
- Family router after open: **no margin gain** vs fixed route → removed
- v24 market-maker: live fell to 9/20 → removed
- **More state ≠ alpha**

## Why our water “fixes” failed

We tried to **add** coverage at runtime (PASS/MOVE→WATER on dry tiles). That violates “exact route action.”

| Overlay | Result |
|---------|--------|
| MOVE→WATER on dry | −30k..−85k desync |
| PASS→WATER on dry | −33k; later tape WATER misses |
| water_optimizer (v15 CU==1) | kept for a while; notebook agents **have zero water_optimizer** |

Kaito/Tetsu/Rayk: **WATER count in source = 0**. Coverage is **baked into the route**, not repaired live.

Roman/tong00 beat us with 55–59 WATER/day because **their route visits every crop** — not because they have a smarter runtime water steal.

## What we ship: v17 NotebookStrict

| Layer | Source | Role |
|-------|--------|------|
| Dual-seat tapes | Our Yubo/Gbining (proven keep-gate) | Labor + coverage + economy |
| WEED repair | Notebook standard | DIG + replay |
| Tomato hedge | Crop-type only | Adaptive **crops** (not path) |
| SELL rank | Kaito/Tetsu sparse controller | Adaptive **timing** of existing sells |
| Terminal sweep | Ours | End cash-out |
| Memory/classifier | Sensors only | Future crop/market gates |
| ~~water_optimizer~~ | **REMOVED** | Desyncs route |
| ~~plant-on-empty~~ | **REMOVED** | Breaks meta |
| ~~path rewrites~~ | **REMOVED** | Chat-Log-5 + notebooks |

### Keep-gate (local)
| Matchup | Result |
|---------|--------|
| vs 14.5 seeds 1–5 | **5/5 WIN**, max d=−283 |
| vs HS | **+1.8k** mean vs v15 |
| vs Kaito v25 | **WIN** all 3 seeds tested |

## Coverage still lacking vs Roman

Notebook-strict does not magically add visits. To match Roman’s 100% coverage we must **replace the backbone route** (offline fit from a coverage-winning public replay / compiler), then keep this same thin runtime.

Next step if ladder still loses on coverage: fit a new dual-seat route from a top coverage winner (THUNDER / Roman-class), validate 5-seed keep-gate, swap tapes only — **do not** add water overlays.

## Adaptive scope (locked)
**MAY change:** crop type on planned PLANTs, seed buys, sell **order** (not qty), tomato hedge, future family-gated market holds  
**MUST NOT change:** walk paths, water visits, land timing, plant positions, animal placement paths
