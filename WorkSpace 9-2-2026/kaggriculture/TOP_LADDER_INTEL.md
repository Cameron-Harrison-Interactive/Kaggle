# Top-of-Ladder Intel — know everyone, drop them first

Generated 2026-08-28 01:14. Source: their own public episodes (top 60 teams, 6 games each, harvested 2026-08-28), our 278-opponent ladder library, live leaderboard.
Re-run: _ref/harvest_top.py, _ref/harvest_top_replays.py, _ref/build_intel2.py.

## THE META (why we were losing)

- **55/60 top teams are COW_HEAVY.** Dominant herd: **11c/4s (24 teams)**, then 9c/4s (9).
- Their cows: first yield D8, MILK every 2 days, season-long. Ours: first cows bought D6 (first yield D14). That is the 835-vs-333 milk gap in every cow-heavy loss.
- **They sell at NIGHT (H22/H23/H00/H02 — 43/40/38/23 votes), not H1.** Our tape sells at H01 (the old meta). Same shared market, they ride the scarcity price curve one night earlier.
- Only 9/60 are strictly cow-FIRST on D0; the rest load cows D1-D4. Counter window: buy cows D1-D3.

## Counter (v11.14 — pure tape, two edits)

1. **Herd**: D1 cow injection + existing D4/D6/D7 cow buys -> 9-11c/3-4s final (matches the 11c/4s block).
2. **Sell band**: move race-item SELL orders (MILK/WOOL/STRAW/MELON/FERT) from H01 into H22-H00 — sell into the same night band, one hour ahead of the H23/H00 wave.
Bench gate: ghost A/B vs meryol/cheezyp/Triston/Lucien/Yohanes/Shinichiro (the 6 cow-heavy losses) must flip to wins; 80-game matrix must not regress.

## The top 60 (from their own games)

| # | team | score | their W-L | archetype | last-game herd | sell hours | h1% | hands | fert | money D5/D10/D20/fin |
|--:|---|---:|---|---|---|---|---:|---:|---:|---|
| 1 | Subramanya N | 2968.7 | ? | COW_HEAVY | 13c/10s/0g | H01,H23,H11 | 57.7 | 12 | 352 | 366/3361/53490/99853 |
| 2 | Ryo Hasegawa | 2967.4 | ? | COW_HEAVY | 7c/9s/0g | H01,H18,H10 | 42.7 | 12 | 277 | 282/15016/51044/93052 |
| 3 | tetsuya | 2898.1 | 126W-54L of 180 | C_BIG_CREW_NO_FERT | 7c/8s/0g | H01,H00,H21 | 35.3 | 12 | 272 | 438/1816/47014/84596 |
| 4 | Naru041104 | 2883.2 | 69W-20L of 89 | COW_HEAVY | 5c/9s/0g | H02,H23,H22 | 1.3 | 15 | 418 | 184/8578/47773/95051 |
| 5 | William Diment | 2861.5 | 63W-19L of 82 | COW_HEAVY | 10c/4s/0g | H22,H02,H23 | 0.7 | 15 | 473 | 123/7815/47015/88401 |
| 6 | Blu3s | 2861.0 | 95W-32L of 127 | COW_HEAVY | 5c/9s/0g | H02,H00,H19 | 1.8 | 15 | 397 | 176/7936/45830/89421 |
| 7 | Michael Timbs | 2845.3 | 103W-19L of 122 | COW_HEAVY | 7c/4s/0g | H03,H13,H06 | 6.0 | 12 | 791 | 467/15743/58519/109955 |
| 8 | Shuwen(Shawn) Ge | 2818.4 | 64W-17L of 81 | COW_HEAVY | 8c/4s/0g | H03,H02,H13 | 7.7 | 12 | 665 | 441/15142/51301/86615 |
| 9 | antadam127 | 2806.3 | 76W-25L of 101 | C_BIG_CREW_NO_FERT | 9c/4s/0g | H23,H02,H00 | 2.4 | 15 | 437 | 182/8640/46473/81581 |
| 10 | NIklitaCheporev | 2786.5 | 51W-5L of 56 | COW_HEAVY | 8c/4s/0g | H02,H03,H13 | 5.3 | 12 | 636 | 548/16392/56549/94933 |
| 11 | Rister | 2785.2 | 67W-10L of 77 | COW_HEAVY | 6c/10s/0g | H02,H00,H14 | 1.8 | 15 | 397 | 166/9188/50639/97571 |
| 12 | Kaileh57 | 2783.0 | 68W-27L of 95 | COW_HEAVY | 9c/4s/0g | H23,H22,H00 | 1.3 | 15 | 397 | 170/7261/44208/83058 |
| 13 | aashka | 2777.7 | 56W-21L of 77 | COW_HEAVY | 6c/10s/0g | H02,H00,H23 | 1.7 | 15 | 397 | 164/8638/41571/64116 |
| 14 | Erfan Eshratifar | 2774.4 | 91W-42L of 133 | COW_HEAVY | 8c/2s/0g | H01,H00,H22 | 44.9 | 14 | 241 | 549/4858/45927/95321 |
| 15 | QQ Farming | 2772.7 | 104W-46L of 150 | COW_HEAVY | 5c/8s/0g | H02,H23,H00 | 1.5 | 15 | 400 | 181/7448/40836/75375 |
| 16 | Mingkang YAN | 2765.3 | 83W-43L of 126 | COW_HEAVY | 11c/4s/0g | H22,H00,H23 | 1.8 | 15 | 397 | 161/7380/40986/62438 |
| 17 | redblackbst | 2734.9 | 75W-25L of 100 | COW_HEAVY | 6c/10s/0g | H02,H00,H23 | 1.5 | 15 | 397 | 138/8234/49484/88697 |
| 18 | Kronki | 2731.4 | 97W-67L of 164 | COW_HEAVY | 9c/4s/0g | H23,H22,H00 | 1.7 | 15 | 400 | 173/7235/49277/103160 |
| 19 | SCNU | 2730.8 | 63W-19L of 82 | COW_HEAVY | 10c/4s/0g | H22,H00,H23 | 1.8 | 15 | 397 | 197/7856/43779/78937 |
| 20 | yy | 2730.5 | 66W-16L of 82 | COW_HEAVY | 9c/5s/0g | H19,H18,H03 | 8.8 | 12 | 326 | 212/16800/51266/82117 |
| 21 | Carson Zhang | 2728.2 | 71W-32L of 103 | COW_HEAVY | 6c/10s/0g | H02,H00,H23 | 1.7 | 15 | 397 | 170/8659/49661/91965 |
| 22 | SJY321 | 2725.6 | 76W-28L of 104 | B_FERT_FACTORY | 11c/4s/0g | H23,H00,H02 | 0.2 | 15 | 1396 | 183/7037/43296/85438 |
| 23 | Debmalya | 2716.3 | 60W-17L of 77 | COW_HEAVY | 9c/4s/0g | H23,H02,H14 | 1.4 | 15 | 277 | 162/7072/40298/74114 |
| 24 | tyz123456 | 2711.6 | 79W-65L of 144 | COW_HEAVY | 3c/10s/0g | H22,H18,H14 | 0.5 | 15 | 448 | 150/7862/44319/82299 |
| 25 | ebisu_ya | 2708.7 | 85W-57L of 142 | COW_HEAVY | 11c/4s/0g | H00,H02,H22 | 1.8 | 15 | 311 | 178/7438/41680/86230 |
| 26 | lucaskna | 2707.2 | 75W-6L of 81 | COW_HEAVY | 9c/4s/1g | H22,H18,H14 | 0.7 | 15 | 397 | 112/8595/53516/103006 |
| 27 | Janus | 2679.6 | 61W-20L of 81 | COW_HEAVY | 11c/4s/0g | H22,H00,H23 | 1.9 | 15 | 400 | 176/7922/42497/70127 |
| 28 | prvsiyan | 2677.6 | 64W-15L of 79 | COW_HEAVY | 11c/4s/0g | H23,H00,H22 | 1.6 | 15 | 397 | 139/7932/48148/84308 |
| 29 | peikopon | 2658.0 | 58W-24L of 82 | COW_HEAVY | 11c/4s/0g | H23,H22,H00 | 1.1 | 15 | 500 | 184/6994/44268/91179 |
| 30 | Georgy Mamarin | 2651.3 | 72W-13L of 85 | COW_HEAVY | 7c/4s/0g | H03,H13,H06 | 6.4 | 12 | 609 | 486/14470/55186/92396 |
| 31 | Mforg | 2627.0 | 103W-67L of 170 | COW_HEAVY | 9c/4s/0g | H00,H22,H23 | 1.5 | 15 | 400 | 182/7435/42601/77793 |
| 32 | Omer Faruk Merey | 2626.0 | 74W-40L of 114 | COW_HEAVY | 11c/4s/0g | H22,H23,H00 | 1.7 | 15 | 400 | 184/7525/50064/93790 |
| 33 | nao.kwmr | 2624.4 | 102W-74L of 176 | C_BIG_CREW_NO_FERT | 6c/10s/0g | H02,H23,H00 | 2.6 | 15 | 400 | 168/9692/51594/86642 |
| 34 | Joseph Adamski | 2622.1 | 63W-16L of 79 | COW_HEAVY | 11c/4s/0g | H23,H00,H22 | 1.6 | 15 | 397 | 173/7094/47657/85059 |
| 35 | Ueddy | 2603.9 | 110W-51L of 161 | COW_HEAVY | 9c/4s/0g | H23,H00,H22 | 1.8 | 15 | 397 | 184/7590/48510/82901 |
| 36 | Zyy7390 | 2599.3 | 68W-48L of 116 | COW_HEAVY | 11c/4s/0g | H23,H00,H22 | 1.6 | 15 | 397 | 154/7668/46029/93819 |
| 37 | YJR | 2598.3 | 60W-36L of 96 | COW_HEAVY | 11c/4s/0g | H22,H23,H02 | 1.9 | 15 | 397 | 186/7012/47365/92151 |
| 38 | Arda Ceylan | 2589.7 | 64W-16L of 80 | COW_HEAVY | 9c/4s/0g | H22,H23,H00 | 1.8 | 15 | 402 | 186/7983/42722/84070 |
| 39 | senkin13 | 2588.1 | 67W-31L of 98 | COW_HEAVY | 11c/4s/0g | H22,H00,H23 | 1.4 | 15 | 482 | 288/7446/50472/92030 |
| 40 | G!vIOne | 2583.8 | 67W-12L of 79 | COW_HEAVY | 11c/4s/0g | H22,H00,H23 | 1.9 | 15 | 400 | 107/8337/50186/98027 |
| 41 | PrasadChopade213 | 2582.3 | 60W-29L of 89 | COW_HEAVY | 11c/4s/0g | H23,H00,H22 | 1.9 | 15 | 400 | 174/7816/53648/100712 |
| 42 | datatuu | 2577.8 | 59W-20L of 79 | COW_HEAVY | 11c/4s/0g | H22,H18,H14 | 0.8 | 15 | 419 | 188/7089/38746/69750 |
| 43 | CREART | 2577.3 | 53W-31L of 84 | COW_HEAVY | 9c/7s/0g | H02,H00,H23 | 1.6 | 15 | 397 | 188/6987/49722/83400 |
| 44 | CroDoc | 2574.0 | 56W-23L of 79 | COW_HEAVY | 11c/4s/0g | H23,H22,H00 | 1.4 | 15 | 400 | 188/7059/51825/91919 |
| 45 | Stephen Schott | 2572.6 | 131W-75L of 206 | COW_HEAVY | 8c/4s/1g | H02,H22,H23 | 2.9 | 13 | 238 | 141/7762/40614/70581 |
| 46 | Yizuki | 2570.8 | 70W-8L of 78 | COW_HEAVY | 11c/4s/0g | H23,H22,H00 | 1.5 | 15 | 397 | 152/7922/43051/85499 |
| 47 | Izzoudine Mohamed KANTA | 2570.5 | 62W-32L of 94 | COW_HEAVY | 10c/4s/0g | H22,H23,H00 | 1.9 | 15 | 397 | 170/8161/45653/80012 |
| 48 | theredbluepill | 2568.6 | 129W-110L of 239 | COW_HEAVY | 8c/9s/1g | H01,H17,H23 | 48.0 | 12 | 313 | 794/12086/53596/95967 |
| 49 | Dude and Destroy | 2563.6 | 87W-26L of 113 | COW_HEAVY | 11c/4s/0g | H22,H23,H18 | 1.4 | 15 | 400 | 167/7024/42370/86401 |
| 50 | DeeperNet | 2558.7 | 79W-31L of 110 | COW_HEAVY | 11c/4s/0g | H22,H00,H23 | 1.9 | 15 | 401 | 182/8684/43790/83118 |
| 51 | Aurora | 2552.9 | 111W-80L of 191 | COW_HEAVY | 9c/4s/0g | H23,H02,H18 | 2.0 | 15 | 299 | 164/7528/44640/80404 |
| 52 | Iulian Curte | 2547.8 | 89W-54L of 143 | COW_HEAVY | 9c/4s/0g | H23,H00,H22 | 1.6 | 15 | 397 | 180/7424/40376/75180 |
| 53 | Terry Luo | 2547.7 | 69W-72L of 141 | COW_HEAVY | 11c/4s/0g | H23,H22,H00 | 1.7 | 15 | 397 | 186/6936/44280/78648 |
| 54 | Lenin Goud | 2541.9 | 81W-82L of 163 | COW_HEAVY | 11c/4s/0g | H23,H00,H22 | 1.7 | 15 | 397 | 166/8390/40576/71568 |
| 55 | Timbydude | 2538.7 | 77W-7L of 84 | COW_HEAVY | 11c/4s/0g | H23,H22,H00 | 1.5 | 15 | 397 | 139/7283/40241/71591 |
| 56 | yuxuan | 2536.7 | 77W-73L of 150 | COW_HEAVY | 6c/9s/0g | H02,H00,H19 | 1.9 | 15 | 397 | 187/8836/43842/73494 |
| 57 | masayoshi | 2536.0 | 148W-41L of 189 | COW_HEAVY | 6c/10s/0g | H02,H22,H19 | 1.5 | 15 | 400 | 187/7174/44960/81601 |
| 58 | GIN | 2531.4 | 72W-18L of 90 | COW_HEAVY | 11c/4s/0g | H02,H00,H22 | 1.6 | 15 | 397 | 106/6954/45006/88849 |
| 59 | iwance | 2529.0 | 124W-45L of 169 | C_BIG_CREW_NO_FERT | 11c/4s/0g | H22,H00,H23 | 2.3 | 15 | 400 | 213/8734/48819/89893 |
| 60 | Will | 2527.4 | 81W-57L of 138 | COW_HEAVY | 11c/4s/0g | H22,H23,H02 | 1.9 | 15 | 397 | 183/7590/50370/93189 |

## Known W-L vs us (from our own games, 278-opponent library)

| team | rank now | our W-L | note |
|---|---:|---|---|
| Blu3s | 6 | 2W-0L | C_BIG_CREW_NO_FERT, sell H01,H18,H23 |
| Kaileh57 | 12 | 0W-1L | C_BIG_CREW_NO_FERT, sell H22,H00,H23 |
| Erfan Eshratifar | 14 | 1W-0L | C_BIG_CREW_NO_FERT, sell H01,H00,H22 |
| Carson Zhang | 21 | 0W-1L | B_FERT_FACTORY, sell H01,H23,H22 |
| Arda Ceylan | 38 | 0W-1L | B_FERT_FACTORY, sell H01,H19,H21 |
| CroDoc | 44 | 0W-1L | C_BIG_CREW_NO_FERT, sell H02,H00,H19 |
| Dude and Destroy | 49 | 0W-2L | C_BIG_CREW_NO_FERT, sell H22,H23,H18 |
| yuxuan | 56 | 1W-0L | B_FERT_FACTORY, sell H01,H22,H20 |
| Kaggs | 66 | 2W-0L | B_FERT_FACTORY, sell H01,H22,H20 |
| Homii_N | 70 | 0W-1L | C_BIG_CREW_NO_FERT, sell H22,H00,H23 |
| WENJIE_Wang | 73 | 1W-0L | B_FERT_FACTORY, sell H01,H20,H21 |
| MD. Nazmus Sakib Anik | 84 | 1W-0L | C_BIG_CREW_NO_FERT, sell H01,H22,H18 |
| Emre Cirak | 104 | 1W-0L | B_FERT_FACTORY, sell H01,H22,H18 |
| zjukop1 | 112 | 0W-1L | B_FERT_FACTORY, sell H01,H22,H20 |
| 李BCDEFGA | 118 | 1W-1L | B_FERT_FACTORY, sell H01,H00,H20 |
| TheMightiestMan | 123 | 0W-1L | C_BIG_CREW_NO_FERT, sell H22,H00,H23 |
| alessandrozonta | 137 | 0W-1L | C_BIG_CREW_NO_FERT, sell H02,H19,H23 |
| Chanhyuk Han | 139 | 1W-0L | B_FERT_FACTORY, sell H01,H00,H22 |
| Forrest | 148 | 0W-1L | B_FERT_FACTORY, sell H01,H00,H23 |
| Harris Bashir | 159 | 0W-1L | B_FERT_FACTORY, sell H01,H20,H18 |
| Vextrovis | 164 | 0W-1L | C_BIG_CREW_NO_FERT, sell H00,H22,H23 |
| JALKARNA GAUTAM | 171 | 1W-0L | B_FERT_FACTORY, sell H01,H20,H22 |
| T0m0t0m0 W | 178 | 1W-1L | B_FERT_FACTORY, sell H01,H22,H18 |
| Tien N. | 196 | 0W-1L | B_FERT_FACTORY, sell H01,H22,H20 |
| Orig_lab | 207 | 0W-1L | B_FERT_FACTORY, sell H01,H22,H20 |
| CrazyDave111 | 218 | 1W-1L | B_FERT_FACTORY, sell H01,H22,H20 |
| Riva Kajangu | 222 | 1W-0L | B_FERT_FACTORY, sell H01,H22,H19 |
| c0nrad | 224 | 0W-1L | C_BIG_CREW_NO_FERT, sell H01,H23,H22 |
| One-For-All | 226 | 1W-0L | C_BIG_CREW_NO_FERT, sell H01,H23,H02 |
| Dr Chandrasen Pandey | 243 | 0W-1L | C_BIG_CREW_NO_FERT, sell H22,H00,H23 |
| Raul Tinajero | 245 | 0W-2L | B_FERT_FACTORY, sell H01,H22,H20 |
| Khanh | 247 | 0W-1L | C_BIG_CREW_NO_FERT, sell H02,H19,H00 |
| Auto Fermers | 265 | 1W-0L | B_FERT_FACTORY, sell H01,H20,H18 |
| Aurora wy | 276 | 0W-1L | C_BIG_CREW_NO_FERT, sell H02,H19,H00 |
| taiseiu | 282 | 0W-1L | B_FERT_FACTORY, sell H01,H20,H18 |
| Phi | 293 | 1W-0L | B_FERT_FACTORY, sell H01,H22,H20 |
| Jin Niu | 295 | 0W-2L | B_FERT_FACTORY, sell H01,H20,H22 |
| Jince | 296 | 1W-0L | B_FERT_FACTORY, sell H01,H00,H18 |