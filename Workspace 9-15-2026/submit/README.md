# Kaggressure — submission folder

## LIVE (on the ladder)
- `v29_champion.py` — ref 56243015 (v28 + final liquidation: last-2-day shed-reservation zeroing; solo/panels identical, ladder leftover fix — 09-15 ladder replay autopsy)
- `v28_champion.py` — ref 56232075 (v27 + endgame carrot rotation, price-gated 2x wheat d23+)
- `v27_champion.py` — ref 56230288 (quota: 5/5 used 09-12; submit at UTC rollover or via the web page) = live20_8: carrots-out wheat-in; solo 97.7k BEST, tetsu -92,680 BEST, v21 -3,942 BEST
- `v26_champion.py` — ref 56177992 (v25 + floor power-check: hold only while market drains; pipeline pocket cap 4/crop)
- `v25_champion.py` — ref 56177266, v24 + sell floor: quantity restriction ~40% base px, hold-for-recovery, denial carve-out, d28+ liquidation (tetsu -99,824 best ever)
- `v24_champion.py` — ref 56177082, submitted 09-12 03:01 UTC (v23 + market control: floor-price animal triage, first-seller melon exit; tetsu +3.7k, solo identical)
- `v23_champion.py` — ref 56176714, submitted 09-12 02:34 UTC (= live20_3: v22 + 4 tape fixes - endgame seed discipline, d28-29 no-weed, late strb window; byte-identical locally, activates on ladder endgame shapes)
- `v22_champion.py` — ref 56176013, submitted 09-12 01:39 UTC
  (= war/astra_live20_1.py [78bdd357], the R34 opening redesign: d4 NE-first
  + steady herd 1-2/day + mix-first NE + late strb factory 38 + SE 3rd worker;
  econ log stripped, kaggle_entry_agent tail)
  Card: solo 6-seed 96.8k (42: 91,727 / 5: 97,830 / 101: 101,250 / 202:
  99,507 / 303: 108,582 / 777: 81,961); v21 panel -4,806 median (best ever);
  tetsu -104,059; live18 9-2 (+6,568); v58 7-4 (+3,865); self-play clean.
- `v21_champion.py` — ref 56153311, submitted 09-10 23:27 UTC (571.0)
  (v20 line + land discipline: same-turn quad fill, solvency-gated buys, SE herd gate)
  Solo gates: $99,618 / $102,735 / $109,169 (seeds 42/101/202)

## Submitting (5/day limit; latest 2 are scored)
```
KAGGLE_API_TOKEN=$(cat kaggle_kgat.txt) python3 -m kaggle competitions submit \
  -c kaggriculture -f submit/v22_champion.py -m "<message>"
```
Verify the ref in the submissions list, never the CLI message:
```
KAGGLE_API_TOKEN=$(cat kaggle_kgat.txt) python3 -m kaggle competitions submissions -c kaggriculture
```

## History
| file | ref | note |
|---|---|---|
| submit/old/v21_champion.py | 56153311 | land discipline (571.0) — now fallback |
| submit/old/v20_champion.py | 56149948 | war mode + coverage (582.4) |
| submit/old/v19_champion.py | 56148276 | planned dispatch (566.4 → 552.9) |
| submit/old/v58_champion.py | — | emergency fallback only |

Dev line: `war/astra_live20_1.py` = v22 chassis (LINE BEST),
`war/astra_live20_2.py` = R35 d0-NE experiment (REJECTED, record only),
`war/astra_live20.py` = R33 chassis (v22's direct parent).
Token: `kaggle_kgat.txt` (root). Playbook: `KAGGRESSURE_PLAYBOOK.md` (root).
Watch matches: `python watch.py` (root; `--lite` for in-app preview).
