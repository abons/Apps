# Word Puzzle - gameplay (telefoon, debug-build, 540x1200, ~60 s)
Commit c284009 (wordpuzzle-src), com.hrbons.wordpuzzle.debug, Motorola edge 30 neo via USB, 2026-10-24. Dagpuzzel 24 okt, NL.

Wat je ziet (ongeveer):
- Statistieken-dialoog open/dicht (alles 0, 'Steun de maker', Wissen, Wiktionary-bron).
- 2 horizontaal ingevuld (MINIBAR), Controleer - gratis (groen = goed).
- Doorklikken met de clue-pijlen, Hint-dialoog (letter 1 munt / woord 3 munten, Annuleren).
- Dagpuzzel-dialoog (vandaag niet opgelost, reeks, Ranglijst).

Opvallend:
- Het bord verspringt ~20 px als de clue-balk van 3 regels naar 1 regel wisselt.
- Na force-stop/herstart (am start -S) was MINIBAR weg: voortgang niet bewaard bij kill (niet bevestigd bij normaal sluiten).
- Back-toets sloot eerder de app in plaats van een dialoog (emulatorpoging).
- Munten 0.

## Sleutelbeelden (voor een AI-sessie: lees deze, niet de mp4)
`01-start.jpg` dagpuzzel leeg · `02-ingevuld.jpg` MINIBAR ingevuld · `03-statistieken.jpg` stats-dialoog · `04-dagpuzzel.jpg` dagpuzzel-dialoog.

## Animaties (filmstrips: 8 frames, links→rechts, boven→onder)
Code: geen Animator/animate()-aanroepen gevonden in de app-bronnen; het meeste is dus direct tekenen zonder tween. Verbeterkans.
- `anim-01-dialog-open.jpg` (1.93 s, 0,29 s): statistieken-dialoog.
- `anim-02-check-toast.jpg` (13.88 s, 0,4 s): Controleer op onvolledige puzzel: knop-indruk, toets-rij dimt, toast 'Nog niet af - vul de rest in' over het toetsenbord.
- `anim-03-hint-dialog.jpg` (23.48 s, 0,34 s): Hint-dialoog.
