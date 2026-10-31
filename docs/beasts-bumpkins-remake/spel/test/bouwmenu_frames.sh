#!/bin/bash
# frames bouwmenu variant A (view/bouwmenu.gd) naar ../lokaal/concept/img/r5/bouwmenu_*.png; draai vanuit spel/: bash test/bouwmenu_frames.sh
G="$LOCALAPPDATA/Microsoft/WinGet/Packages/GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe/Godot_v4.7.2-stable_win64_console.exe"
U=../lokaal/concept/img/r5
r="$G --path . --fixed-fps 10 -- --missie=1 --scenario=minikaart --opname_frame=40"
$r --venster=1920x1080 --proef=paneel --proef_tab=voedsel --proef_kas=400 --opname=$U/bouwmenu_pc_rij.png 2>&1 | grep scherm
$r --venster=1920x1080 --proef=paneel --proef_tab=wonen --proef_kas=250 --opname=$U/bouwmenu_pc_te_duur.png 2>&1 | grep scherm
$r --venster=1920x1080 --proef=bouw --opname=$U/bouwmenu_pc_ghost.png 2>&1 | grep scherm
$r --venster=1920x1080 --proef=rij --opname=$U/bouwmenu_pc_weg.png 2>&1 | grep scherm
t="$r --touch --venster=1080x2400"
$t --opname=$U/bouwmenu_tel_rust.png 2>&1 | grep scherm
$t --proef=paneel --proef_tab=voedsel --proef_kas=400 --opname=$U/bouwmenu_tel_paneel.png 2>&1 | grep scherm
$t --proef=paneel --proef_tab=wonen --proef_kas=250 --opname=$U/bouwmenu_tel_te_duur.png 2>&1 | grep scherm
$t --proef=bouw --opname=$U/bouwmenu_tel_ghost.png 2>&1 | grep scherm
$t --proef=rij --opname=$U/bouwmenu_tel_weg.png 2>&1 | grep scherm
