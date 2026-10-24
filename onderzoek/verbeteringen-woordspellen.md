# Verbeteringen voor de drie woordspellen (2026-10-24, na debunkronde)

Onderzoek, geen implementatie. Niets gebouwd of gedraaid; alleen code, docs, git en opnames gelezen.

## Opzet en grenzen

- Apps: Word Guesser (WG, `wordguesser-src`), Word Cross / Woordpuzzel (WC, `wordpuzzle-src`), Word Swipe / Woord Swiper (WS, `wordfinder-src`).
- `main` staat in alle drie op de opgenomen commits (98adba4, c284009, 941fc1d): beelden en code komen overeen.
- Ronde 1: 3 Sonnet-agents, één per app (≤8 zoekopdrachten, ≤5 vergelijkingsapps). Ronde 2: 3 debunk-agents toetsten elk punt aan code, todo.md, besluiten en git; steekproeven bevestigden hun kernclaims.
- ⚠️ Play Store, App Store, Reddit en Wikipedia waren niet bereikbaar. Alles extern komt uit zoeksamenvattingen van 2026-10-24; geen concurrent zelf gespeeld.
- Bouwt voort op `onderzoek/2026-10-monetisatie/`: kruiswoord- en letterwielapps, daar open gelaten, zijn hier gedekt.
- Vaste regels gerespecteerd (geen libraries, ads, tracking, cross-promotie; WG-UI Engels). **Toestel** = alleen op toestel te controleren; S = uren, M = een dag, L = meer.

## Vooraf, voor alle drie: spelers zien het werk nog niet

- WS: `main` loopt 56 commits vóór de live v1.3 (`wordfinder todo.md:9-12`, 2026-10-03).
- WG: live is v2.6 van 2026-08-07; `main` is "far ahead" (`wordguesser docs/stand.md:13-18`). Sindsdien ≥30 commits in `app/src/main` (ondiepe clone, ondergrens).
- WC: live is 1.6 van 2026-08-16 (`wordpuzzle todo.md:6`). Sindsdien ≥11 commits in `app/src/main` (ondergrens). ⚠️ Daar geldt "niets gaat uit tot alles Play-ready is" (gebruikersbesluit 2026-08-17), dus voor WC géén release-advies.
- **Hoogste effect gedeeld door werk van dit hele rapport: een release voor WS en WG** (M, toestel ja: koude eerste start verplicht, `wordfinder CLAUDE.md`).
- Snelkoppeling "Daily" voor WG (`todo.md:862`, label Engels) en WC: S, toestel ja. WS opent al de daily (`MainActivity.kt:217-218`).

## Correcties op de bekende bevindingen

- WC, letters weg na force-stop: testartefact. `am start -S` slaat `onPause` over; alleen een crash of voorgrond-kill verliest het bord.
- WC bewaart bij `onPause` en bij elke wissel (modus, taal, thema, nieuw spel; `MainActivity.kt:284, 1062, 1074, 1417, 1450`), bewust: `docs/besluiten/het-bord-bewaren-vier-keuzes-2026-07-29.md:26-28`.
- WC, de sprong van het bord is 3↔2 regels, niet 3↔1. De clue-balk heeft `minLines = 2` zonder maximum (`:534`), en het bord staat gecentreerd in een gewogen ScrollView (`:520-526`).
- WC, Back sluit de app: niet uit de code te verklaren (geen Back-handler), waarschijnlijk emulator. Munten 0: geen bug, nieuwe install krijgt 5 (`Economy.kt:40`).
- WS, 3 letters: niet stil. De speler ziet de pil 'Minimaal 4 letters' en voelt een lichte tik (`MainActivity.kt:1331-1334`, bewust gekozen in besluitenset 4).
- WS, waarom 4: de grens komt uit de data (`docs/besluiten/waarom-de-ondergrens-4-letters-is.md`). Een woord van 3 letters telt ook niet als bonus (`:1374`).
- WG, schudden nooit gezien: de daily controleert geen woorden (`MainActivity.kt:2916`) en strict staat standaard uit (`:450`). Bewust: gelijke daily voor iedereen (`web/src/main.ts:424-425`, 4dbc951).
- WG, Engelse dialogen: bewust (`docs/besluiten/de-ui-blijft-engels-en-de-winkeltekst-mag-dat-zeggen.md`).

## Onderling: wie doet wat beter

| Onderwerp | Beste | Achterblijver | Overnemen |
|---|---|---|---|
| Animatie | WS: `Juice.kt` 462 r. (flyLetters, flyCoins, confetti), `WinPanel.kt` | WC: nul animator-aanroepen | WC, gepland in todo.md:626-640 |
| Haptiek | WG/WS: tick/success/reject zonder VIBRATE-recht (WG `Juice.kt:35-55`) | WC: nul | WC (S) |
| Delen | WG: spoilervrije, geteste `Share.kt`; WS: silhouet + `?s=`-link | WC: geen ACTION_SEND | WC (todo.md:513) |
| Foutmelding | WS: eigen pil met reden in tekst | WC: echte `Toast` over het toetsenbord (`:2393`, anim-02); WG: pil ver van de rij | WC pil (todo ~633); WG pil bij de rij (todo:449) |
| Dialogen/thema | WC: alles via `SkinDialog.kt`, CONTRAST-skin met kleurenblind-simulatie | WG: HC-palet haalt 1,93:1 (todo ~436) | WG contrast per palet |
| Munten | WS: stempelkaart (25 bonuswoorden = hint, `Economy.kt:25-29`); WC: nooit vast (Controleer gratis op 0) | WG: munt koopt alleen streakredding | WG pas na muntprijsbesluit |
| Eerste minuut | WS: campagne-level 1 met getekende eerste veeg (`:213-217`); WG adopteert toesteltaal | WG: daily verstopt achter getaltegel; WC: geen uitleg | zie top 5 |
| Stats | WS: tegels (besluitenset 3) | WS: instellingen tussen cijfers | WS-indeling |

## Word Guesser: top 5 (effect gedeeld door werk)

| # | Wat | Waarom (bewijs) | Omvang | Toestel |
|---|---|---|---|---|
| 1 | Golf (`bump`) over de winnende rij, sheet pas daarna | Na winst nu alleen `hapticSuccess` (`:2971`) en direct de sheet; `Juice.bump` bestaat (`Juice.kt:60`); al gepland in todo.md:417-421 | S | ja |
| 2 | Daily vindbaar maken: label of chevron op het getaltegeltje, Daily op de New-sheet | De daily zit achter tegel "5" die niet als knop leest, en *New* kent geen Daily (todo.md ~420) | S-M | ja |
| 3 | Knop "Meaning" op de daily-eindsheets | `04-verloren.jpg`: "the word was FALIE" zonder uitleg (`:4033-4040`, `promptSubmit` ~`:4063`). In vrij spel staat al een `?` naast het woord (`:1115-1133`) | S | ja |
| 4 | Afwijzingspil bij de actieve rij; `?`-knop een groter raakvlak via `TouchDelegate` | Pil boven het toetsenbord (todo.md:449); `?` is 20 dp (`:1778/1807`). Echt 48 dp breed raakt de rijbreedte en is dan M | S | ja |
| 5 | Eind-sheet niet doodlopend: aftelling naar de volgende daily | `04-verloren.jpg`: alleen SHARE / CLOSE / LEADERBOARD; geen countdown in de code; zelfde todo-punt als #1 | M | ja |

**Besluiten, niet bouwen:**
- Woordcontrole in de daily (was #1): het gedrag is bewust; een niet-woord kost een rij en de ranglijst telt beurten (`Leaderboard.rank`, `:270`). Afdwingen kan echte woorden weigeren in 17 lijsten en moet mee naar `web/`. Eerst meten wat de accept-lijst mist; dat Wordle niet-woorden weigert, is **niet bevestigd**.
- Contrast HC-palet (1,93:1 en 2,73:1, todo ~436): een toegankelijkheidsbug, maar het vraagt een besluit per palet (M, `SkinTest`).
- Streakmijlpalen die een scène of skin ontgrendelen (todo:466): mijlpalen moeten op stats per taal en instelling, want een reeks die aan de daily hangt werkt niet.
- Hint voor één verdiende munt: raakt het muntprijsbesluit (todo:1276).
- Herinnering (POST_NOTIFICATIONS): raakt de "twee permissies"-lijn (`docs/security.md:170`).

**Nakijken op toestel:** toetsen kleuren tijdens of ná de flip (todo ~447 tegen `anim-01`), en één icoonstijl in de kop (todo ~423).

## Word Cross: top 5

| # | Wat | Waarom (bewijs) | Omvang | Toestel |
|---|---|---|---|---|
| 1 | Haptiek: tik per letter, reject bij fout, success bij woord en oplossen | Nul haptiek in `app/src` (grep); gepland in todo.md:626-631; kan zonder VIBRATE-recht | S | ja |
| 2 | Deelknop na de dagpuzzel (tijd, reeks, spoilervrij, geen andere game noemen) | Geen ACTION_SEND; todo.md:513-517; de vorm moet nog bedacht worden. Of `DailyScore`/`Stats` genoeg leveren, is niet nagelopen | S-M | nee |
| 3 | Sprong weg: bord bovenaan uitlijnen (`gravity` TOP, `:522-524`) of `minLines = 3` | **Niet** `lines = 3` + ellipsize: clues zijn tot 110 tekens plus prefix (`WordData.cleanClue`). In `contracts/puzzle-vectors-v1.json` is 10-20% langer dan drie regels | S | ja |
| 4 | `Toast` vervangen door een pil in de skinkleuren | Een echte `Toast` (`:2393`) valt over het toetsenbord (anim-02) en volgt `Skin.p` niet; todo ~633-635 | S-M | ja |
| 5 | Viering bij oplossen vóór de kale beloningsdialoog, plus dialoogfade en `bump` bij invullen | Enige beloningsmoment (todo ~686-700); patroon in `wordfinder WinPanel.kt` en `Juice.kt`; met `Juice.enabled` zodat shots stil blijven (todo:626-640) | M | ja |

**Verder:** uitleg in de eerste minuut "Controleer gratis bij 0 munten, hint kost 1/3" (S); eigen toetsenbord, "hoogste polish-rendement" (todo ~701, L, zes skins); genummerde reeksen (todo:601, L).

**Besluit, niet bouwen:** een checkpoint bij een afgerond woord stond eerst op 1. Het is gedegradeerd door het bewaarbesluit, en het voordeel geldt alleen bij een crash. Doe het alleen als het besluit wordt bijgewerkt.

**Genre** (zoeksamenvattingen 2026-10-24): CodyCross geeft tokens via streak-mijlpalen (Fanatee-help; loginmunten onbevestigd); Teazel: loginbonus groeit met reeks; Daily Themed: VIP 15 munten/dag; NYT Mini sinds sept 2025 achter abonnement (Insider Gaming, geen NYT-bron).

## Word Swipe: top 5

| # | Wat | Waarom (bewijs) | Omvang | Toestel |
|---|---|---|---|---|
| 1 | Release uitbrengen (zie "Vooraf") | 56 commits vóór live v1.3: gerichte hint, geleide veeg en stempelkaart heeft nog geen speler gezien | M | ja (koude installatie) |
| 2 | Shots opnieuw schieten | De winkelbeelden tonen nog de oude pil en deelknop (todo.md:19, 66) | S | ja |
| 3 | Wiel op een klein scherm (360x640 dp) bekijken | `FitTest` rekent het alleen door (todo.md:30) | S | ja |
| 4 | Dagelijkse beloning, bv. hint-token op reeksdag 7 en 30 | De reeks kost nu alleen; tokens bestaan (`:1448-1456`); "Dagelijkse beloning … nog niet besloten" (todo.md:664) | S bouwen, besluit eerst | nee |
| 5 | Stats-dialoog indelen met kopjes Spel / Instellingen | `04-statistieken.jpg`: tegels zijn al gebouwd, het gaat alleen om de indeling. De thema- en handrij blijven er per besluit staan (`:2426-2515`, "settings row rather than a sixth top-bar icon"); effect klein | S | ja (shot 'stats') |

**Geschrapt na debunk:** snelkoppeling (app opent al de daily); uitgebreidere melding bij te kort woord (noemt het getal al); letters aantikken (staand besluit "swipe-only" met geaccepteerde prijs, `docs/besluiten/staande-richtingsbesluiten.md:63-70`; alleen als besluit te heropenen, L).

**Verder:**
- Multi-hint: een nieuw idee, geen "derde muntbestemming". De stempelkaart is die bestemming al, en todo.md:651 is daarmee verouderd. Het raakt de break-even en `HINT_COST`.
- `assetlinks.json` zodat de `?s=`-link in de app opent (todo.md:26; S, andere repo).
- De teller aantikbaar laten ogen (todo.md:497): S, maar eerst een besluit.

**Niet doen:** 3-letterwoorden (gedeelde lijst, cache-bump; L) en geluid (todo.md:813).

**Genre** (zoeksamenvattingen 2026-10-24): Words of Wonders vult een bonusicoon, wat WS al heeft als stempelkaart (Arkadium-help); Wordscapes ~55% omzet uit reclame is één schatting (felixbraberg.substack, 2026); reeksbeloning Wordscapes en multi-hint Word Connect niet gevonden.

## Vergelijkingsapps (zoeksamenvattingen 2026-10-24, niet zelf bekeken)

- **Woord raden:** NYT Wordle (lampje-hint, archief voor abonnees); Wordle! van Lion Studios (App Store 4,6★ bij ~819K, Remove Ads $5.99); Quordle (oefenstand buiten de stats); Woordje (3-8 letters); Lingo-app (status onbekend).
- **Kruiswoord:** NYT Mini, CodyCross (Fanatee), Daily Themed Crossword (PlaySimple), Teazel Crossword. Denksport (Keesing) en Puzzelfit (DPG) zijn betaald.
- **Letterwiel:** Wordscapes en Wordscapes Uncrossed (PeopleFun), Words of Wonders (Fugo), Word Connect. Geen NL-letterwielapp gevonden; dat kan een zoekgat zijn.
- **Patroon bij de leiders:** hints kosten verdiende munten en reeksen worden beloond. Geld komt uit reclame + Remove Ads of een abonnement; beide vallen buiten onze regels.
- **Wat binnen onze regels past:** verdiende reeksbeloningen, betere winmomenten, delen. Zie ook `2026-10-monetisatie/README.md` (eenmalige aankopen of supporterpakket in plaats van reclame).

## Wat de debunkronde veranderde

- Zes van de vijftien top-punten geschrapt of gedegradeerd. WG #1 (daily-woordcontrole) en WC #1 (vaker bewaren) bleken bestaande besluiten; WS-tikinvoer ook.
- WC `lines = 3` + ellipsize vervangen door bord bovenaan (afkappen beschadigt de clue). WS-snelkoppeling en meldingstekst geschrapt.
- Erbij: release-achterstand van alle drie, WG daily vindbaar, WC pil en viering, WS shots en klein scherm. Wordle- en Word Connect-claims onbevestigd.

## Vervolgopdrachten

De punten die bleven, staan per app in `todo.md` onder *Onderzoek 2026-10-24* (bestaande punten bij hun titel, nieuwe uitgeschreven).

**Word Guesser**
1. Eind-sheet-ronde: `bump`-golf vóór de sheet, "Meaning" op de daily-sheets, aftelling naar de volgende daily. Toestelronde met een nieuwe filmstrip.
2. Daily vindbaar maken plus snelkoppeling "Daily"; daarna release v2.7 met koude installatie.
3. Besluitnotitie "regels in de daily": meten hoeveel echte woorden de accept-lijst mist, en het HC-contrast per palet laten kiezen.

**Word Cross**
1. Haptiek plus een pil in plaats van `Toast` (Juice-basis overnemen met `Juice.enabled`).
2. Sprong wegnemen door het bord bovenaan uit te lijnen, met een pixelcheck op het toestel; deelknop daarna.
3. Viering bij oplossen en dialoogfade; landt op `main`, want er gaat niets uit vóór Play-ready.

**Word Swipe**
1. Release uitbrengen (koude installatie op de Motorola) en de shots opnieuw schieten.
2. Wiel op 360x640 dp bekijken en de stats-dialoog indelen; shot 'stats' bijwerken.
3. Besluit "dagelijkse beloning" (todo.md:664) voorleggen en todo.md:651 bijwerken nu de stempelkaart bestaat.

## Wat ontbreekt

- Geen concurrent zelf gespeeld. Onboarding, eerste minuut, foutanimatie en meldingen van de leiders zijn niet geverifieerd.
- Downloads, ratings en prijzen komen alleen uit zoeksamenvattingen; voor echte cijfers moet play.google.com in het netwerkbeleid open.
- Commits sinds de release voor WG/WC zijn ondergrenzen (ondiepe clones). WS-web live? Tegenstrijdig (todo.md:68 tegen 5bcca25).
- Niet bekeken: filmstrips van WG en WS, beelden van WC, `gameplay.mp4`.
- Alles met "Toestel: ja" moet op de Motorola of een AVD bevestigd worden, inclusief clue-breedte en pixelsprong.
