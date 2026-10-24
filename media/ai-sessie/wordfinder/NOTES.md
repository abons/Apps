# Word Swipe - gameplay (telefoon, debug-build, 540x1200, ~60 s)
Commit 941fc1d (wordfinder-src), com.hrbons.wordfinder.debug, Motorola edge 30 neo via USB, 2026-10-24. Daglevel 24 okt, NL, letters G E W A A G D.

Wat je ziet (ongeveer; GEWAAD was al gevonden voor de opname begon):
- WAAG swipen en accepteren, bord vult kruiswoord (Woorden 2/9).
- WAD en DAG (3 letters): toast 'Minimaal 4 letters', geen woord.
- Hint-knop (8), Shuffle (wiel herschikt).
- Statistieken-dialoog: reeks, levels, munten, campagne, bonuswoorden, hints, Woordenschrift, Spelregels, Voortgang bewaren, knoppen-zijde, thema.

Opvallend:
- Statistiekendialoog is lang en rommelig (8+ regels/rijen, links naar instellingen verstopt in 'Statistieken').
- Alleen woorden vanaf 4 letters tellen: WAD/DAG worden stil geweigerd met een toast.

## Sleutelbeelden (voor een AI-sessie: lees deze, niet de mp4)
`01-start.jpg` leeg level · `02-gewaad.jpg` eerste woord gevonden · `03-waag.jpg` tweede woord + 'Minimaal 4 letters' · `04-statistieken.jpg` stats-dialoog.

## Animaties (filmstrips: 8 frames, links→rechts, boven→onder)
Code: `Juice.kt` (bump, shake, flyCoins, flyLetters, confetti), `PuzzleGridView` (fill/pulse/glow/ants/pop), `WheelView` (glide/glim/outcome/guide). Aan/uit via animatorschaal.
- `anim-01-swipe.jpg` (2.88-3.63 s): swipe door het wiel (selectie en letter-pop; 'WAAG' lichtoranje in het raster).
- `anim-02-woord-geaccepteerd.jpg` (3.83-4.78 s, 0,95 s): woord vult het raster, oranje→wit fade, toast 'WAAG ✓'.
- `anim-03-fout-woord-en-hint.jpg` (12.56-14.23 s): toast 'Minimaal 4 letters'; daarna Hint: letter D onthuld, muntteller telt 57→55→50→49 in stapjes, cel oranje→wit.
- `anim-04-shuffle.jpg` (18.36 s, 0,4 s): wiel schuift de letters om.
