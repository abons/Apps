#!/bin/bash
# Bouwt de rig/glb en rendert de contactbladen. Gebruik: bash run.sh [animatie ...]
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
cd "$(dirname "$0")"
"$B" -b -P bumpkin_rig.py 2>&1 | grep -E "KLAAR|Error|Traceback|line " | cut -c1-120
"$B" -b -P bumpkin_preview.py -- "$@" 2>&1 | grep -E "^blad|Error|Trace|line "
