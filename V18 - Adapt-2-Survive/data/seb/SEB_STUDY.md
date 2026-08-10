# Seb (allegedly) (#2, teamId 16630516) — study from top-5 wins

Pulled 2026-08-09. Subs: 55299100 (3195.4 peak), 55323652 (2596.2).

## Top-5 wins
| episode  | seat | Seb $  | opp $  | opponent |
|----------|------|--------|--------|----------|
| 90442423 | 1    | 183082 | 28916  | Shijian Wen |
| 90699383 | 0    | 165822 | 85577  | Quyền Thịnh |
| 90701764 | 0    | 160874 | 133700 | Jeff Horon |
| 90700185 | 0    | 159789 | 82278  | ` |
| 90698587 | 1    | 159170 | 31587  | Kendamarron |

## Fingerprint / build (4-quad animal-heavy)
- **Open t1:** HIRE×6–7, BUY_SEED MELON 3 + WHEAT 12, BUY_ANIMAL COW 2 (+ SHEEP 2 same hour or t2)
- **Wheat product drip** almost every other hour day 0
- **Land:** NE **d4**, SW **d6**, SE **d10** (full 4-quad)
- **Animals end:** 16–21 (cow 7–11 + sheep 5–14); hires ~304–310
- **Crops:** strawberry heavy (plants 41–45, sells **289–323**), melon 16–27 planted / 92–162 sold
- **Wheat:** net BUYER (buys product 292–403, sells only 77–105)
- **Fertilizer sold:** 263–320; milk 191–271; wool 132–263
- No tomato

## Local tape regression vs v15
Seb 4-quad choreography is fragile under local weed RNG (tape vs starter only ~$4.7k; live peaks $160–183k). Still a valid fingerprint/regression opponent.

| seed | v15 vs Seb | Seb vs v15 | v15 margin |
|------|------------|------------|------------|
| 1 | 153505–1196 | 8914–141100 | +152k / +132k |
| 2 | 113105–1306 | 9208–106915 | +112k / +98k |
| 3 | 146528–1221 | 4450–124920 | +145k / +120k |
| 4 | 164715–1314 | 7207–143676 | +163k / +136k |
| 5 | 80519–1112 | 8777–78784 | +79k / +70k |

**v15 wins 10/10** seat matchups. No counter-tape swap warranted until a candidate beats v15 vs 14.5.

## Artifacts
- `seb_seat0_tape.json` / `seb_seat1_tape.json`, `*.b85`
- `scripts/opp_seb.py`
- `analysis.json`, `meta.json`

## v16 AdaptiveMemory note
Seb is cleanly classified (`family=seb` by day1 via wheat-heavy open + later SE).
Sell top-up counter is coded path but **disabled** until it passes keep-gate
(previous mild milk/wool top-up cost ~$4k vs v15). Memory still tags Seb every match.
