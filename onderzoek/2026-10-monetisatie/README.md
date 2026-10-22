# Vergelijkbare apps en verdienmodellen (oktober 2026, onvolledig)

Onderzoek naar vergelijkbare apps met meer dan 1.000 downloads en naar de beste manier om met dit soort apps
geld te verdienen. Gestart op 2026-10-21 als workflow met 40 agents, waarvan 24 in de eerste ronde.

**Status: afgebroken.** Alle 24 agents liepen na ongeveer een minuut tegen de sessielimiet aan en schreven geen
rapport. Acht agents haalden vóór die stop nog zoekresultaten binnen; die staan in `ruwe-zoekresultaten/`.
De cijfers hieronder komen uit zoeksamenvattingen en zijn **niet nagecontroleerd**.

## Wat er in deze map staat

- `portfolio.md`: profiel van alle apps dat de agents als briefing kregen.
- `ruwe-zoekresultaten/`: zoekvragen en samenvattingen per onderwerp (M = markt, P = verdienmodel).
- `workflow.js`: het workflowscript (fasen: sweep, strategy, verify). Het pad `R` bovenin wijst naar de
  scratchpad van de oude sessie; pas dat aan voordat je het opnieuw draait. Tip: draai met Sonnet-agents.

## Gedekt en niet gedekt

Wel: Wordle-achtigen (wereldwijd en NL), AI-dungeon-masters, levenssimulaties, advertenties, in-app aankopen,
web/PWA-verdienmodellen, indie-postmortems.

Niet: Wordscapes-achtigen, kruiswoordapps, dorpsbouwers, 4X, kinderapps, laad-/energieapps, sportapps,
stemtools, betaalde apps en Play Pass, abonnementen, donaties, Play-beleid, vindbaarheid (ASO),
Nederlandse belasting, B2B.

## Vergelijkbare apps (voorlopig)

| App | Downloads | Verdienmodel | Betekenis |
|---|---|---|---|
| Wordle! (Lion Studios / AppLovin) | 10M+ op Play | Veel reclame, Remove Ads $5.99, munten $0.99-$9.99 | ±$800K netto geschat (2022); reclame is de grootste klacht |
| Woordle: Dagelijks Woordenspel (appsurd, Venlo) | ±76K, ±27 per dag | Gratis | Directe NL-concurrent; maat voor de NL-niche |
| OCTORDLE (Zooboo) | 10K+ | Reclame | Beoordeling 1,35 en toch 10K |
| Worduel | onbekend | onbekend | Duel in 13 talen; enige die de meertaligheid benadert |
| AI Dungeon (Latitude) | ±1M, 4,0 | Abonnement $14.99-$99.99/mnd | #30 top-grossing Adventure (maart 2026) |
| AI Game Master: Dungeon RPG | 100K+ | Beurtenpakketten (350 beurten $9.99) | Betalen per beurt werkt |
| Friends & Fables | onbekend | $19.95-$39.95/mnd | Gratis met daglimiet |
| BitLife (Candywriter) | 50M+ | Reclame + aankopen (Remove Ads $2.99, Bitizenship $7.99) | $26M omzet 2019, verkocht voor $74M + earn-out |
| The Game of Life 2 (Marmalade) | 500K | $4.99 + aankopen | Betaalde levenssimulatie op Android werkt |
| No Time to Relax | ±2.500 Steam-reviews | $13.99, alleen Steam | Jones-achtig; op Android niets gevonden: niche Fast Lane lijkt leeg |

## Opbrengst-cijfers (voorlopig)

| Bron | Cijfer |
|---|---|
| Woordspel "Letters", alleen IAP | $56.89 bij 1.883 downloads |
| Tinytouchtales, alleen IAP | $8.600 bij 104K downloads (±$80 per 1.000) |
| App met reclame, 10K downloads | ±$35 totaal |
| App met reclame, 10K actieve gebruikers | $400-$900 per maand |
| Woordspel op Flippa (2024, claim verkoper) | ±$60K/jaar: 45% reclame, 45% Play Pass, 10% IAP |
| Retentie mobiele games (mediaan) | D1 22%, D7 4%, D30 0,7%; woordspellen beter |
| Play-commissie | 15% over eerste $1M/jaar, na aanmelding; Google draagt EU-btw af |
| Betalende spelers casual/puzzel | ±2% (AppsFlyer, 2017, gedateerd) |
| Personalized vs. niet-gepersonaliseerde reclame | 1,5 tot 3 keer zoveel opbrengst |
| Webreclame-drempels | Raptive 25K pageviews/mnd (sinds okt 2025), Mediavine Journey 10K sessies |

## Voorlopige conclusies

- **Reclame loont pas bij veel actieve gebruikers.** Onder ±10K actieve spelers levert het tientjes op en kost
  het de belofte "geen reclame, geen trackers".
- **Eenmalige aankopen passen bij de filosofie:** supporterpakket of extra puzzels, gekoppeld aan de bestaande
  munten, met meerdere bedragen naast elkaar. Een losse fooienpot werkt slecht.
- **Play Pass onderzoeken:** in het Flippa-voorbeeld kwam bijna de helft van de omzet daaruit.
- **DnDAI kan niet gratis:** markt hanteert $5-$20/mnd of beurtenpakketten.
- **Webversies zijn een bezit:** Wordle (NYT, "laag zeven cijfers"), Quordle (Merriam-Webster), Puzzmo (Hearst).
  Via een Trusted Web Activity kan een PWA met Play Billing in de Play Store.
- **Ko-fi:** op het gratis plan meestal 0% over fooien, plus Stripe/PayPal-kosten.

## Waarom het onvolledig is

1. Sessielimiet bereikt (reset was 2:30 UTC).
2. Het netwerkbeleid van de cloudomgeving blokkeerde play.google.com, apps.apple.com, f-droid.org,
   appbrain.com, reddit.com en news.ycombinator.com. Downloadaantallen komen daardoor alleen uit
   zoeksamenvattingen. Toestaan via Network access in de omgevingsinstellingen
   (https://code.claude.com/docs/en/cloud-environments#network-access).
