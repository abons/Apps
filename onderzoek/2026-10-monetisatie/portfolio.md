# Portfolio-profiel: apps van abons / hrbons (Nederland)

Alle apps delen dezelfde filosofie: **klein (±100-210 KB APK), snel, offline, geen reclame, geen trackers, geen accounts,
geen runtime-dependencies** (pure Kotlin op het Android-framework; web-apps als PWA zonder build-stap of framework).
Huidige inkomsten: alleen een Ko-fi-link (ko-fi.com/hrbons). Geen ads, geen IAP, geen abonnement.
Distributie: web (GitHub Pages, abons.github.io) en Android. APK-downloads zijn op 2026-08-16 van GitHub gehaald;
F-Droid is op 2026-08-07 afgevallen; **Google Play wordt het enige Android-kanaal** (listings nog niet live).
Showcase: https://abons.github.io/Apps/

## Games

1. **Word Guesser** (web + Android). Wordle-achtig: raad het woord in 6 pogingen, groen/geel/grijs.
   16 talen (woordlijsten online gedownload, offline gecached), woordlengte 4-8, strict mode, hard mode,
   dagpuzzel per taal/lengte met publiek leaderboard (Firebase Realtime DB), streaks, statistieken,
   timed mode (5-min sprint, weekbord), duels (vs computer / vs speler via roomcode), NL/EN definities ("?"-hint).
   Heeft al een **munten-systeem**: 1 munt per opgeloste dagpuzzel, munt uitgeven om streak te redden;
   in de web-versie zit code voor "purchase record carries coins" (Ko-fi-aankoop → munten claimen).
   Web: https://abons.github.io/wordguesser/
2. **Woord Swiper / Word Swipe** (web + Android, NL). Wordscapes-achtig: swipe letters op een wiel, vul de
   kruiswoordpuzzel; alle woorden uit één basiswoord; bonuswoorden leveren munten op voor hints; dagelijks level + campagne.
   Web: https://abons.github.io/wordfinder/
3. **Woord Puzzel / Word Cross** (web + Android, NL). Zweedse kruiswoordpuzzels, gegenereerd, elke aanwijzing is een echte
   woordenboekdefinitie met het antwoord weggelaten; één dagpuzzel voor iedereen met scorebord; vrij spelen in drie formaten.
   Web: https://abons.github.io/wordpuzzle/
4. **Beasts** (Android, in ontwikkeling). Isometrisch dorpsbouwspel in de geest van Beasts and Bumpkins (1997):
   akkers, kuddes, oogst, winkels, huizen, 12 levels, realtime.
5. **Kwelder** (Android, in ontwikkeling). Beurtgebaseerde 4X in de geest van The Battle of Polytopia: twee stammen op
   een archipel uit één seed, mist, steden veroveren, land inpolderen.
6. **DnDAI** (Android, in ontwikkeling). D&D-verhaalspel met een AI (LLM) als dungeon master: verhaal, regels,
   karakterblad; dobbelstenen rol je zelf. Let op: LLM-gebruik kost geld per beurt.
7. **Fast Lane** (Android, "binnenkort op Google Play"). Levenssimulatie in de geest van Jones in the Fast Lane:
   gegenereerde stad, weken, rijkdom/opleiding/geluk/carrière, vs AI-rivaal, hotseat of online duel. Tweetalig, ±210 KB.

## Apps

8. **Kinderwoordjes** (PWA, NL). Eerste Nederlandse woordjes voor peuters: categorie kiezen, groot plaatje, voorlezen (TTS),
   installeerbaar, offline. https://abons.github.io/Kinderwoordjes/
9. **e-charge** (PWA, NL). Rekenhulp van één scherm: laadtijd Nissan Leaf aan het stopcontact, klaar-tijd, km, kosten
   met dynamische stroomprijs per kwartier (EnergyZero-API). https://abons.github.io/e-charge/
10. **Volleybal** (PWA, NL). Nevobo-team zoeken, programma/uitslagen/stand, wedstrijden in agenda, aanwezigheid doorgeven
    en delen via groep met code; geen account, offline. https://abons.github.io/Volleybal/
11. **Vocal** (zelf te draaien, desktop). Stem klonen uit korte opname, opnames omzetten naar jouw stem, TTS, liedjes
    maken met jouw zang; alles lokaal op open-source modellen; repo privé.

## Eerder onderzoek (30-09-2026, "Klein, snel, reclamevrij")
Vergeleek 9 open-source Android-spellen (billthefarmer/crossword, ReGeX, Lexica, robocrosswords, minesweeper, wordle-kt,
Dooz, sgtpuzzles, Shattered Pixel Dungeon, Unciv). Conclusie: "geen runtime-dependencies + ±100 KB" is een echt
onderscheid. Ideeën voor nieuwe apps: Woordraster (Boggle-achtig), Kruiswoordhulp, Stroomplanner, dagelijkse
logicapuzzel (nonogram), Kindertellen.

## Wat de eigenaar wil weten
1. Welke **vergelijkbare apps met meer dan 1.000 downloads** bestaan er (per app/categorie), wat doen ze, hoe verdienen ze?
2. **Hoe valt er het best geld te verdienen** met dit soort apps, gegeven de filosofie (klein, reclamevrij, privacyvriendelijk)?
   Wees eerlijk over wat realistisch is voor een solo-ontwikkelaar in Nederland.
