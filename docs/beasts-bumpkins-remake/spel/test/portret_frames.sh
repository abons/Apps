#!/bin/bash
# frames voor de staand/liggend-indeling (view/scherm.gd) naar out/portret/; draai vanuit spel/: bash test/portret_frames.sh
G="$LOCALAPPDATA/Microsoft/WinGet/Packages/GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe/Godot_v4.7.2-stable_win64_console.exe"
for v in 1080x2400 2400x1080; do
  r="$G --path . --fixed-fps 10 --"
  $r --touch --venster=$v --missie=1 --opname=out/portret/touch_${v}_briefing.png 2>&1 | grep scherm
  $r --touch --venster=$v --scenario=minikaart --opname_frame=30 --opname=out/portret/touch_${v}_hud.png 2>&1 | grep scherm
  $r --touch --venster=$v --scenario=minikaart --proef=bouw --opname_frame=30 --opname=out/portret/touch_${v}_bouw.png 2>&1 | grep scherm
  $r --touch --venster=$v --scenario=minikaart --proef=lade --opname_frame=30 --opname=out/portret/touch_${v}_lade.png 2>&1 | grep scherm
  $r --touch --venster=$v --scenario=minikaart --proef=prijzen --opname_frame=30 --opname=out/portret/touch_${v}_prijzen.png 2>&1 | grep scherm
  $r --venster=$v --scenario=minikaart --proef=bouw --opname_frame=30 --opname=out/portret/pc_${v}_bouw.png 2>&1 | grep scherm
done
# portret met de Gemini-png (view/portret.gd, besluit gebruiker 2026-10-31): man, vrouw, bouwer, voetsoldaat, pc en telefoon
for s in man vrouw bouwer voetsoldaat; do
  $G --path . --fixed-fps 10 -- --venster=1600x900 --scenario=gedachten --stap=$s --opname_frame=30 --opname=out/portret/gemini_pc_$s.png 2>&1 | grep scherm
  $G --path . --fixed-fps 10 -- --touch --venster=1080x2400 --scenario=gedachten --stap=$s --opname_frame=30 --opname=out/portret/gemini_tel_$s.png 2>&1 | grep scherm
done
