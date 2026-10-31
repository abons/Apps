#!/bin/bash
# frames deurweg-ghost (view/bouwmenu.gd _toon_pad: de keienweg doorzichtig in de ghost-tint) naar
# ../lokaal/concept/img/r5/pad_ghost_*.png; draai vanuit spel/: bash test/deurweg_frames.sh
# (de oude pad_*.png zonder ghost_ zijn de stippen van 0d677da, voor de vergelijking in ronde5.html)
G="$LOCALAPPDATA/Microsoft/WinGet/Packages/GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe/Godot_v4.7.2-stable_win64_console.exe"
U=../lokaal/concept/img/r5
r="$G --path . --fixed-fps 10 -- --missie=1 --scenario=minikaart --opname_frame=40 --proef=bouw --proef_pad"
$r --venster=1920x1080 --opname=$U/pad_ghost_pc_hut.png 2>&1 | grep scherm
$r --venster=1920x1080 --proef_draai=1 --opname=$U/pad_ghost_pc_hut_draai.png 2>&1 | grep scherm
$r --venster=1920x1080 --proef_soort=molen --opname=$U/pad_ghost_pc_molen.png 2>&1 | grep scherm
$r --venster=1920x1080 --proef_duur --opname=$U/pad_ghost_pc_duur.png 2>&1 | grep scherm
$r --touch --venster=1080x2400 --opname=$U/pad_ghost_tel_hut.png 2>&1 | grep scherm
