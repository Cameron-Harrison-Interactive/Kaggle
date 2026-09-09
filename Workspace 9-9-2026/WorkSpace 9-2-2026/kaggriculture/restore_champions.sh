#!/bin/bash
# Restore topbots goose champions from root masters (stale-wipe gremlin recovery)
cd "$(dirname "$0")"
for v in v3_76 v4 v5 v6; do
  f="CHAMPION_goosebot_${v}.py"
  [ -f "$f" ] && cp "$f" "topbots/goosebot_${v}.py"
done
[ -f CHAMPION_goosebot_v4.py ] && cp CHAMPION_goosebot_v4.py topbots/goosebot_v4_final.py
[ -f CHAMPION_goosebot_v6.py ] && cp CHAMPION_goosebot_v6.py topbots/goosebot_v6b.py
[ -f CHAMPION_goosebot_v5.py ] && cp CHAMPION_goosebot_v5.py topbots/goosebot_v5.py
echo "restored:"; ls topbots/ | grep -i "goosebot_v[3-6]"
# v7 backups (goose solo-ladder champions; H2H gate vs v11 still unbeaten)
for v in v7b v7e; do
  [ -f CHAMPION_goosebot_$v.py ] && cp CHAMPION_goosebot_$v.py topbots/goosebot_$v.py
done
[ -f CHAMPION_goosebot_v7e.py ] && cp CHAMPION_goosebot_v7e.py topbots/goosebot_v7.py
