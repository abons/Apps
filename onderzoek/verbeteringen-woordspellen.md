# Verbeteringen voor de drie woordspellen (2026-10-24)

Onderzoek, geen implementatie. Niets gebouwd of gedraaid; alleen code, docs en opnames gelezen.

## Opzet en grenzen

- Apps: Word Guesser (`wordguesser-src`), Word Cross / Woordpuzzel (`wordpuzzle-src`), Word Swipe / Woord Swiper (`wordfinder-src`).
- `main` staat in alle drie nog op de opgenomen commits: 98adba4, c284009, 941fc1d. Beelden en code komen dus overeen.
- Bronnen intern: `Apps/media/ai-sessie/*/NOTES.md`, sleutelbeelden, CLAUDE.md, todo.md, docs/besluiten, gerichte stukken code.
- Er is geen `.claude-index` in deze checkouts (gitignored), dus gezocht via `docs/map.md` en grep.
- Bronnen extern: 3 Sonnet-agents, elk ≤8 zoekopdrachten en ≤5 vergelijkingsapps.
- ⚠️ Play Store, App Store, Reddit en Wikipedia waren niet bereikbaar. Alles extern komt uit zoeksamenvattingen van 2026-10-24.
- ⚠️ Geen enkele concurrent is zelf gespeeld: onboarding en foutfeedback van de leiders zijn **niet geverifieerd**.
- Bouwt voort op `onderzoek/2026-10-monetisatie/`: dat liet kruiswoord- en Wordscapes-achtigen open; die zijn hier gedekt.
- Vaste regels gerespecteerd: geen libraries, ads, tracking of cross-promotie; één vrijwillige Ko-fi-link; Word Guesser-UI blijft Engels.
- Kolom **Toestel** = alleen op een toestel te controleren (ja/nee). Omvang S = uren, M = een dag, L = meerdere dagen.

## Correcties op de bekende bevindingen

- Word Cross, sprong van het bord: clue-balk heeft `minLines = 2` en geen maximum (`wordpuzzle MainActivity.kt:534`). De sprong is dus 3↔2 regels, niet 3↔1.
- Word Cross, letters weg na force-stop: verklaard. `saveSnapshot()` loopt alleen in `onPause` en bij moduswissel (`MainActivity.kt:296-300`); `am start -S` slaat `onPause` over. Normaal sluiten bewaart wel (volgens code, niet op toestel herhaald).
- Word Cross, Back sluit app: in code niet te verklaren. Er is geen Back-handler, dialogen zijn standaard annuleerbaar. Waarschijnlijk een emulator-artefact.
- Word Cross, munten 0: geen bug. Nieuwe install krijgt 5 (`Economy.kt:40`); 0 is eerder uitgegeven saldo.
- Word Swipe, 3 letters: **niet stil**. Pil 'Minimaal 4 letters' + haptische tik (`wordfinder MainActivity.kt:1331-1334`).
- Word Swipe, waarom 4: de grens is van de data, niet van het ontwerp. `nl.txt` en `nl-accept.txt` bevatten niets onder 4 (`docs/besluiten/waarom-de-ondergrens-4-letters-is.md`). Een 3-letterwoord telt ook niet als bonus (`:1372`).
- Word Guesser, schudden nooit gezien: verklaard. In de daily wordt **geen woordcontrole** gedaan (`wordguesser MainActivity.kt:2916`: `!dailyMode && strictMode && …`) en strict staat standaard uit (`:450`).
- Word Guesser, Engelse dialogen: bewust (`docs/besluiten/de-ui-blijft-engels-en-de-winkeltekst-mag-dat-zeggen.md`). Geen verbeterpunt binnen de regels.

## Onderling: wie doet wat beter

| Onderwerp | Beste | Achterblijver | Overnemen |
|---|---|---|---|
| Animatie | WS: `Juice.kt` 462 r. (flyLetters, flyCoins, confetti) | WC: 0 animator-aanroepen | WC port Juice + `Juice.enabled`-schakelaar voor shots |
| Haptiek | WG/WS: tick/success/reject zonder VIBRATE-recht | WC: geen | WC (S) |
| Delen | WG: spoilervrije, geteste `Share.kt`; WS: silhouet + `?s=`-link | WC: geen ACTION_SEND | WC (todo.md:513) |
| Foutmelding | WS: pil in plaats van Toast, reden in tekst | WG: pil ver van de rij; WC: toast over toetsenbord (anim-02) | WG reden bij de rij |
| Dialogen/thema | WC: alles via `SkinDialog.kt`, CONTRAST-skin met kleurenblind-simulatie (`ThemeTest`) | WS: overvolle stats-dialoog (beeld 04) | WS/WG: één dialoogbouwer, contrasttoets |
| Munten | WC: nooit vast (Controleer gratis op 0); WS: stempelkaart, 25 bonuswoorden = hint | WG: munt alleen voor streakredding | WG: kleine verdiende hint |
| Eerste minuut | WS: geleide eerste veeg (todo.md:14-72); WG adopteert toesteltaal | WC: geen uitleg van munten/Controleer | WC tooltip |
| Dagelijkse terugkeer | WG/WC: daily + ranglijst + reeks | alle drie: geen icoon-snelkoppeling (todo.md wf:512) | `shortcuts.xml` in alle drie (S) |
| Bewaren | WC: snapshot per modus met fingerprint (`SavedGame.kt`) | WC zelf: alleen op `onPause` | zie WC #1 |

WG = Word Guesser, WC = Word Cross, WS = Word Swipe.

## Word Guesser: top 5 (effect gedeeld door werk)

| # | Wat | Waarom (bewijs) | Omvang | Toestel |
|---|---|---|---|---|
| 1 | Woordcontrole ook in de daily (en strict standaard aan, of alleen voor de daily) | `MainActivity.kt:2916` slaat de controle over in de daily; "ZZZZZ" kost een beurt en geeft gratis letterinfo, wat de ranglijst oneerlijk maakt. De reden staat nergens in docs; eerst `git log -S'!dailyMode && strictMode'` lezen. Wordle weigert niet-woorden zonder beurt (TechRadar/Tom's Guide via zoeksamenvatting, 2026-10-24, indirect) | S + besluit | nee (JVM-test) |
| 2 | Knop "Meaning" op de eind-sheet | `04-verloren.jpg`: "the word was FALIE" zonder uitleg; de definitie-opzoeking (`?` per rij) bestaat al. Dat onderscheidt hem van elke kloon | S | ja (layout) |
| 3 | Winst krijgt beweging: `bump`-golf over de winnende rij, sheet pas daarna | Na winst nu alleen `hapticSuccess` en direct de sheet (`MainActivity.kt` ~2971); `Juice.bump` bestaat (`Juice.kt:55`) | S | ja |
| 4 | Eind-sheet niet doodlopend: aftelling naar volgende daily + "Next word" | `04-verloren.jpg`: alleen SHARE / CLOSE / LEADERBOARD. NYT-app toont reeks en statistieken na afloop (Play-listing via zoeksamenvatting, 2026-10-24) | M | nee |
| 5 | Afwijzing bij de rij tonen en `?`-knop naar 48 dp raakvlak | Pil "Not in word list" staat boven het toetsenbord, het schudden ver erboven (`:2910/2917`, `Juice.kt:70`); `?` is klein en grijs (`02-midgame.jpg`, todo.md ~450) | S | ja |

Verder: streakmijlpalen 7/30/100 ontgrendelen een scène of skin (M); één hint voor één verdiende munt, niet te koop (M); één icoonstijl in de kop (S, todo.md ~423).
Nakijken: todo zegt dat toetsen tijdens de flip kleuren, NOTES ziet ze pas ná de flip (`anim-01`) — alleen op toestel te beslechten.
Niet doen zonder besluit: lokale herinnering (vraagt POST_NOTIFICATIONS, raakt de "twee permissies"-lijn in `docs/security.md`).

## Word Cross: top 5

| # | Wat | Waarom (bewijs) | Omvang | Toestel |
|---|---|---|---|---|
| 1 | Snapshot ook bij woord af, hint en Controleer (eventueel gedebounced na typen) | Nu alleen `onPause` + moduswissel (`MainActivity.kt:284-300`); het commentaar daar erkent "a crash still loses the board"; NOTES: MINIBAR weg na kill | S | nee (JVM-test op SavedGame) |
| 2 | Clue-balk vaste hoogte: `lines = 3` + ellipsize; tikken opent al de volledige lijst | `minLines = 2` zonder max (`MainActivity.kt:530-536`); bord verspringt ~20 px (NOTES) | S | ja (pixelcheck) |
| 3 | Haptiek: tik per letter, reject bij fout, success bij woord/oplossen | Nul `performHapticFeedback` in de app; kan zonder VIBRATE-recht, zoals in WG `Juice.kt:35-55` | S | ja |
| 4 | Deelknop na de dagpuzzel (tijd, reeks, spoilervrij) | Geen ACTION_SEND; staat open op todo.md:513; `DailyScore.kt`/`Stats.kt` hebben de gegevens; vorm van WG `Share.kt` | S-M | nee |
| 5 | Juice-port: fade/scale op `skinDialog`, bump bij invullen, golf bij goed woord, confetti bij oplossen | 0 animator-aanroepen (grep); `anim-01/02/03` tonen dialogen en toast die direct verschijnen; todo.md:626-634 stelt de port zelf voor. Kleuren via `Skin.p` | M | ja |

Verder: eenmalige uitleg "Controleer is gratis bij 0 munten, hint kost 1/3" (S; geen onboarding in code); kleine muntbonus bij reeks 3/7 naast herstel voor 10 munten (`Economy.kt:54/70`, S); genummerde puzzelreeksen voor voortgang buiten de daily (todo.md:601, L).
Genre: hints met verdiende munten zijn standaard. CodyCross: munten via mijlpalen en dagelijkse login, plus reclame en abonnement (Common Sense Media + Fanatee-helpcentrum). Teazel Crossword: loginbonus die groeit met de reeks. Daily Themed: VIP met 15 munten per dag. Bronnen: zoeksamenvattingen, 2026-10-24.

## Word Swipe: top 5

| # | Wat | Waarom (bewijs) | Omvang | Toestel |
|---|---|---|---|---|
| 1 | Instellingen uit 'Statistieken': twee kopjes (Spel / Instellingen) of één rij naar een eigen blad, geen zesde icoon | `04-statistieken.jpg`: vijf instellingenrijen onder de cijfers; `showStats` `MainActivity.kt:2426-2515`; het besluit over vaste chroom blijft heel | S | ja (shot 'stats') |
| 2 | Reeksmijlpaal (dag 7, 30) betaalt een gratis hint-token | Reeks kost nu alleen (redden, `Economy.kt` STREAK_SAVE_*); tokens bestaan (`MainActivity.kt:1451`). Wordscapes geeft extra beloning bij aaneengesloten dagpuzzels (theriagames.com, mrt-apr 2025, derde partij) | S | nee |
| 3 | Snelkoppeling 'Dagpuzzel' op het icoon (`res/xml/shortcuts.xml`, nl + en) | Dagelijkse terugkeer met één tik; todo.md:512 zegt "geen van de drie woordspellen heeft er een" — daarna kopiëren naar WG en WC | S | ja |
| 4 | Melding bij te kort woord noemt woord en reden: "WAD — woorden hier hebben 4+ letters" | Pil 'Minimaal 4 letters' (`03-waag.jpg`, values-nl strings:53) leest als afwijzing van een goed woord; Wordscapes speelt 3-7 letters (zoeksamenvatting, 2026), spelers verwachten 3 | S | nee |
| 5 | Letters los aantikken als tweede invoer naast vegen | `WheelView` is alleen met een veeg te bedienen en dus niet speelbaar met TalkBack (CLAUDE.md, todo.md:419-428) | M | ja |

Verder: multi-hint als derde muntbestemming (eerste letter van elk open woord), want de muntlus dooft rond level 13-23 uit (todo.md:651; Word Connect noemt hint/target/multi-hint, App Store via zoeksamenvatting, 2026-10-24) (M); `assetlinks.json` zodat de `?s=`-link in de app opent (S, andere repo, todo.md:26); teller 'Woorden 2/9' laten ogen als knop (S, todo.md:497).
Niet doen zonder besluit: 3-letterwoorden (raakt de gedeelde lijst in wordguesser, cache-bump en drempels; L); geluid (raakt het besluit 'geen geluid', todo.md:813).
Genre: Wordscapes (PeopleFun/AppLovin) dagpuzzel met reeks en bonuswoorden voor munten, ~55% omzet uit reclame (schatting, felixbraberg.substack, 2026). Words of Wonders (Fugo): bonuswoorden vullen een icoon dat edelstenen uitkeert (Arkadium-help, ongedateerd). Geen NL-letterwielapp gevonden: mogelijk een zoekgat, geen bewijs van een lege niche.

## Vergelijkingsapps (zoeksamenvattingen 2026-10-24, niet zelf bekeken)

- **Woord raden:** NYT Wordle (lampje-hint, stats, archief voor abonnees). Wordle! van Lion Studios (boosters, Remove Ads $5.99, 4,6★ bij 819K iOS volgens appfollow 2026). Quordle van Merriam-Webster (oefenstand die stats niet raakt). Lingo-app (status onbekend). Woordje (3-8 letters).
- **Kruiswoord:** NYT Mini (sinds sept 2025 achter abonnement, Insider Gaming), CodyCross (Fanatee), Daily Themed Crossword (PlaySimple), Teazel Crossword. Denksport (Keesing) en Puzzelfit (DPG) zijn betaald.
- **Letterwiel:** Wordscapes, Wordscapes Uncrossed (Piggy Bank, Crate of Hints), Words of Wonders (Fugo), Word Connect.
- **Patroon bij de leiders:** hints kosten verdiende munten, reeksen worden beloond, verlies kost weinig. Geld komt uit reclame + Remove Ads of een abonnement; beide vallen buiten onze regels.
- **Wat binnen onze regels past:** verdiende beloningen (reeks → hint), betere winmomenten en delen. Sluit aan op de conclusie in `2026-10-monetisatie/README.md` (eenmalige aankopen of supporterpakket in plaats van reclame).

## Vervolgopdrachten

**Word Guesser**
1. Besluit en bouw "woordcontrole in de daily": git-historie van `:2916` lezen, besluit vastleggen, JVM-test op onEnter-pad, ranglijst-eerlijkheid meewegen.
2. Eind-sheet: knop "Meaning", `bump`-golf vóór de sheet, aftelling naar volgende daily. Toestelronde met nieuwe filmstrip.
3. Toestelronde zonder code: afgekeurd woord (schudden + pil) opnemen, toetskleur tijdens flip bepalen, `?`-raakvlak meten (`uiautomator dump`).

**Word Cross**
1. Bewaren bij woord af/hint/Controleer + clue-balk vaste hoogte, met JVM-test op `SavedGame` en pixelcheck van het bord op het toestel.
2. Juice-port in stappen: eerst haptiek, dan dialoogfade en bump, dan confetti; `Juice.enabled` meenemen zodat shots stil blijven.
3. Deelknop (vorm van WG `Share.kt`) plus eenmalige uitleg van munten en Controleer in de eerste minuut.

**Word Swipe**
1. Statistieken en instellingen splitsen; shot 'stats' en `docs/screenshots.md` bijwerken.
2. Economie-besluit: hint-token bij reeks 7/30 en multi-hint als derde muntbestemming; doorrekenen tegen todo.md:651.
3. Tik-invoer naast vegen in `WheelView`, daarna een TalkBack-ronde op het toestel; snelkoppeling 'Dagpuzzel' meenemen en naar WG/WC kopiëren.

## Wat ontbreekt

- Geen concurrent zelf gespeeld; onboarding, eerste minuut, foutanimatie en meldingen van de leiders zijn niet geverifieerd.
- Downloads, ratings en prijzen alleen uit zoeksamenvattingen; voor echte cijfers moet play.google.com in het netwerkbeleid open.
- Niet bekeken: filmstrips van WG en WS, beelden van WC (code was beslissend); `gameplay.mp4` bewust niet.
- Alles met "Toestel: ja" is alleen uit code en notities beoordeeld en moet op de Motorola of een AVD worden bevestigd.
