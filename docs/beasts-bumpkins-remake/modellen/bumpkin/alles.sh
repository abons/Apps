#!/bin/bash
# Bouwt alle personages (of de genoemde) met previews. Gebruik: bash alles.sh [vrouw jongen ...] [-- opties]
B="/c/Program Files/Blender Foundation/Blender 5.2/blender.exe"
cd "$(dirname "$0")"
namen=(); opts=(vergelijk poses)
while [ $# -gt 0 ]; do [ "$1" = "--" ] && { shift; opts=("$@"); break; }; namen+=("$1"); shift; done
[ ${#namen[@]} -eq 0 ] && namen=(vrouw jongen meisje oudere_man oudere_vrouw)
for n in "${namen[@]}"; do
  "$B" -b -P bumpkin_$n.py -- "${opts[@]}" 2>&1 | grep -E "LOD0|tint |export|KLAAR|Error|Traceback|line [0-9]" | cut -c1-200
done
