# Word Guesser - gameplay (telefoon, debug-build, 540x1200, ~80 s)
Commit 98adba4 (wordguesser-src), com.hrbons.wordguesser.debug, Motorola edge 30 neo via USB, 2026-10-24. Daily 5 letters NL.

Wat je ziet (ongeveer):
- STORM, WATER, KLEIN geraden (blauw = juiste letter/plek-kleur, rood = andere plek, zwart = niet in woord).
- Statistieken- en instellingen-dialoog open/dicht.
- BOVEN, KAMER, KETEL; spel verloren: 'Not solved - the word was FALIE', Time 1:00, SHARE / CLOSE / LEADERBOARD.

Opvallend:
- Dialoogtekst is Engels terwijl het spel NL is (toestelinstelling Engels).
- '?' (definitie) naast elke geraden rij.
- Opname niet frame voor frame nagekeken: kan een systeemmelding bevatten.

## Sleutelbeelden (voor een AI-sessie: lees deze, niet de mp4)
`01-start.jpg` leeg bord · `02-midgame.jpg` zes rijen deels geraden · `03-statistieken.jpg` stats-dialoog · `04-verloren.jpg` resultaat-dialoog.

## Animaties (filmstrips: 8 frames, links→rechts, boven→onder; uit de mp4 geknipt op echte frametijden)
Code: `Juice.kt` (flipReveal, bump, shake, haptics); aan/uit via animatorschaal.
- `anim-01-flip-reveal.jpg` (18.45-19.11 s, 0,66 s): tegels draaien één voor één om (rand-op), kleur wisselt halverwege de flip; toetsenbordkleuren pas ná de flip. Rij 3 van de video (KLEIN).
- `anim-02-dialog-open.jpg` (21.07 s, 0,29 s): statistieken-dialoog schuift op.
- `anim-03-resultaat-dialog.jpg` (49.82 s, 0,3 s): verliesdialoog onderin.
- Letter-tik (bump) is ~0,18 s per toets; niet apart gestript. shake() (afgekeurd woord) kwam in de opname niet voor: alle woorden werden geaccepteerd.
