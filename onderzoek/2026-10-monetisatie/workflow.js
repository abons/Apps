export const meta = {
  name: 'apps-markt-en-monetisatie',
  description: 'Marktonderzoek naar vergelijkbare apps (>1000 downloads) en verdienmodellen voor de app-portfolio van abons; 40 agents die via een gedeeld prikbord samenwerken',
  phases: [
    { title: 'Markt', detail: 'vergelijkbare apps per categorie, downloads en verdienmodel' },
    { title: 'Monetisatie', detail: 'verdienmodellen, cijfers, beleid, NL-markt' },
    { title: 'Strategie', detail: 'per app-groep, leest alle rapporten en het bord' },
    { title: 'Kritiek', detail: 'red team per strategie' },
    { title: 'Verificatie', detail: 'claims en cijfers nacontroleren' },
    { title: 'Volledigheid', detail: 'wat ontbreekt er nog' },
  ],
}

const R = '/tmp/claude-0/-home-user/1b872e0f-ba89-5b31-84db-ddb6c342f5ce/scratchpad/research'

const ROSTER = `TEAM (40 agents; gebruik deze id's bij VRAAG AAN / ANTWOORD AAN / TIP VOOR):
Markt (vergelijkbare apps): M01 Wordle-achtigen wereldwijd · M02 NL/meertalige Wordle-achtigen · M03 Wordscapes-achtigen (Woord Swiper) · M04 kruiswoord/Zweedse puzzels (Woord Puzzel) · M05 dorpsbouwers (Beasts) · M06 Polytopia/4X (Kwelder) · M07 AI-dungeon-masters (DnDAI) · M08 levenssimulaties (Fast Lane) · M09 peuter-apps (Kinderwoordjes) · M10 EV-laad/energieprijs-apps (e-charge) · M11 sport-/clubapps NL (Volleybal) · M12 AI-stemtools (Vocal)
Monetisatie: P01 advertentie-economie · P02 in-app aankopen · P03 betaald/premium/Play Pass · P04 abonnementen · P05 donaties/fooien · P06 Play/App Store-beleid en kosten · P07 web/PWA-monetisatie en Wordle-exits · P08 indie-postmortems met cijfers · P09 downloads krijgen (ASO/distributie) · P10 Nederlandse markt en belasting · P11 privacyvriendelijk verdienen · P12 B2B/licenties/AI-kosten
Strategie: S01 woordspellen-trio · S02 Beasts+Kwelder · S03 DnDAI · S04 Fast Lane · S05 Kinderwoordjes+e-charge+Volleybal · S06 Vocal + portfolio-niveau
Kritiek: C01..C06 (red team van S01..S06) · Verificatie: V01 app-feiten · V02 cijfers · V03 beleid/juridisch · Q01 volledigheid`

function common(id, role) {
  return `Je bent onderzoeksagent ${id} ("${role}") in een team van 40 agents. Opdrachtgever: een Nederlandse solo-ontwikkelaar (abons / hrbons) met 11 kleine, reclamevrije apps. Het team onderzoekt (1) welke VERGELIJKBARE APPS MET MEER DAN 1.000 DOWNLOADS bestaan en (2) HOE ER MET DIT SOORT APPS HET BEST GELD TE VERDIENEN VALT. Werktaal: Nederlands (bronnen mogen Engels zijn).

${ROSTER}

WERKMAP: ${R}
- ${R}/portfolio.md = profiel van zijn apps. LEES DIT EERST (Bash: cat).
- ${R}/board.md = gedeeld PRIKBORD van alle agents. Lees het aan het begin en NOG EENS halverwege je werk. Andere agents laten er feiten, vragen en tips achter; jij ook. Alleen TOEVOEGEN, nooit herschrijven.
- ${R}/reports/${id}.md = jouw eindrapport (Markdown, Nederlands).

GEREEDSCHAP (lees goed, dit scheelt veel tijd):
- Laad eerst je webtools als ze nog niet in je lijst staan: ToolSearch met query "select:WebSearch,WebFetch".
- WebSearch is je HOOFDBRON. Begin met mode "standard"; gebruik "extended" zodra resultaten mager, gedateerd of niet-specifiek zijn. Doe minimaal 8 en hooguit ~20 zoekopdrachten. Varieer: Engels én Nederlands; "<appnaam>" site:play.google.com; AppBrain, AppMagic, Sensor Tower, data.ai, 42matters-snippets; Reddit r/androiddev r/gamedev r/IndieDev postmortems; Hacker News; Indie Hackers; dev-blogs; officiële documentatie.
- WebFetch WERKT ALLEEN voor github.com en raw.githubusercontent.com. ALLE andere hosts (play.google.com, apps.apple.com, reddit.com, f-droid.org, appbrain.com, nieuws-sites...) zijn door het netwerkbeleid geblokkeerd (403): probeer ze NIET, het mislukt gegarandeerd. Haal Play-gegevens (downloads-tier zoals "1K+", "10K+", "100K+", "1M+"; rating; "Bevat advertenties"; "In-app aankopen"; prijs) uit de zoekresultaten en hun samenvattingen.
- Bij ELK cijfer de bron-URL én (als bekend) het jaar. Verzin niets. Niet gevonden = zeg "niet gevonden". Schattingen markeer je met "(onzeker)". Bronnen ouder dan 2023 markeer je als "gedateerd". Voorkeur voor 2025-2026.
- Bash mag je gebruiken voor cat, grep, ls en heredocs in de werkmap. Niets buiten de werkmap wijzigen.

WERKWIJZE:
1. cat ${R}/portfolio.md ; cat ${R}/board.md
2. Voer je opdracht (hieronder) uit. Halverwege: cat ${R}/board.md opnieuw. Staat er een "VRAAG AAN" die jij kunt beantwoorden (ook als die niet aan jou gericht is), beantwoord die dan in je bordbericht met "ANTWOORD AAN <id>:". Zie je iets dat voor een andere agent nuttig is: "TIP VOOR <id>:".
3. Schrijf je rapport naar ${R}/reports/${id}.md met een Bash-heredoc. Opbouw: # titel · korte samenvatting (5 regels) · bevindingen met cijfers en bronnen · tabel(len) waar dat past · "Wat dit betekent voor de eigenaar" · open vragen · bronnenlijst (volledige URL's). Lengte: 60-200 regels.
4. Zet je bordbericht erop (5-12 regels, belangrijkste feiten MET bron-URL, cijfers, en je VRAAG AAN / ANTWOORD AAN / TIP VOOR-regels), precies zo:
{ echo; echo "## [${id}] <korte titel> · $(date -u +%H:%M)Z"; cat <<'EOF_B'
<je regels>
EOF_B
} >> ${R}/board.md
5. Geef je gestructureerde eindresultaat via het schema. Je eindtekst is data voor het script, geen bericht aan een mens.
`
}

const MARKET_SCHEMA = {
  type: 'object',
  properties: {
    agent_id: { type: 'string' },
    comparable_apps: { type: 'array', items: { type: 'object', properties: {
      name: { type: 'string' }, developer: { type: 'string' }, platform: { type: 'string' },
      store_or_site_url: { type: 'string' },
      downloads: { type: 'string', description: 'bv "1K+", "10K+", "1M+" of "onbekend"' },
      rating: { type: 'string' }, monetization: { type: 'string' }, price_points: { type: 'string' },
      open_source: { type: 'boolean' }, notable: { type: 'string' },
      source_urls: { type: 'array', items: { type: 'string' } },
    }, required: ['name', 'downloads', 'monetization', 'source_urls'] } },
    key_insights: { type: 'array', items: { type: 'string' } },
    implications_for_owner: { type: 'array', items: { type: 'string' } },
    questions_for_others: { type: 'array', items: { type: 'string' } },
    report_path: { type: 'string' },
  },
  required: ['agent_id', 'comparable_apps', 'key_insights', 'implications_for_owner', 'report_path'],
}

const MONEY_SCHEMA = {
  type: 'object',
  properties: {
    agent_id: { type: 'string' },
    findings: { type: 'array', items: { type: 'object', properties: {
      claim: { type: 'string' }, evidence: { type: 'string' }, source_url: { type: 'string' },
      year: { type: 'string' }, confidence: { type: 'string', enum: ['hoog', 'middel', 'laag'] },
    }, required: ['claim', 'source_url', 'confidence'] } },
    numbers: { type: 'array', items: { type: 'object', properties: {
      metric: { type: 'string' }, value: { type: 'string' }, context: { type: 'string' }, source_url: { type: 'string' },
    }, required: ['metric', 'value', 'source_url'] } },
    recommendations_for_owner: { type: 'array', items: { type: 'string' } },
    questions_for_others: { type: 'array', items: { type: 'string' } },
    report_path: { type: 'string' },
  },
  required: ['agent_id', 'findings', 'numbers', 'recommendations_for_owner', 'report_path'],
}

const STRATEGY_SCHEMA = {
  type: 'object',
  properties: {
    agent_id: { type: 'string' }, group: { type: 'string' },
    recommended_models: { type: 'array', items: { type: 'object', properties: {
      model: { type: 'string' }, why: { type: 'string' }, expected_revenue_range: { type: 'string' },
      evidence_sources: { type: 'array', items: { type: 'string' } },
    }, required: ['model', 'why', 'expected_revenue_range', 'evidence_sources'] } },
    do_not_do: { type: 'array', items: { type: 'string' } },
    implementation_steps: { type: 'array', items: { type: 'string' } },
    risks: { type: 'array', items: { type: 'string' } },
    key_claims: { type: 'array', items: { type: 'object', properties: {
      claim: { type: 'string' }, source_url: { type: 'string' } }, required: ['claim', 'source_url'] } },
    report_path: { type: 'string' },
  },
  required: ['agent_id', 'group', 'recommended_models', 'do_not_do', 'implementation_steps', 'risks', 'key_claims', 'report_path'],
}

const CRITIQUE_SCHEMA = {
  type: 'object',
  properties: {
    agent_id: { type: 'string' }, target: { type: 'string' },
    verdict: { type: 'string', enum: ['houdbaar', 'deels houdbaar', 'niet houdbaar'] },
    strongest_objections: { type: 'array', items: { type: 'string' } },
    unsupported_claims: { type: 'array', items: { type: 'object', properties: {
      claim: { type: 'string' }, why: { type: 'string' } }, required: ['claim', 'why'] } },
    missed_opportunities: { type: 'array', items: { type: 'string' } },
    revised_recommendation: { type: 'string' },
    answered_board_questions: { type: 'array', items: { type: 'string' } },
    report_path: { type: 'string' },
  },
  required: ['agent_id', 'target', 'verdict', 'strongest_objections', 'unsupported_claims', 'missed_opportunities', 'revised_recommendation', 'report_path'],
}

const VERIFY_SCHEMA = {
  type: 'object',
  properties: {
    agent_id: { type: 'string' }, lens: { type: 'string' },
    checked: { type: 'array', items: { type: 'object', properties: {
      claim: { type: 'string' }, origin_agent: { type: 'string' },
      status: { type: 'string', enum: ['bevestigd', 'weerlegd', 'genuanceerd', 'niet te verifiëren'] },
      evidence_url: { type: 'string' }, note: { type: 'string' },
    }, required: ['claim', 'origin_agent', 'status', 'note'] } },
    report_path: { type: 'string' },
  },
  required: ['agent_id', 'lens', 'checked', 'report_path'],
}

const GAPS_SCHEMA = {
  type: 'object',
  properties: {
    agent_id: { type: 'string' },
    missing: { type: 'array', items: { type: 'string' } },
    contradictions: { type: 'array', items: { type: 'string' } },
    weakest_evidence: { type: 'array', items: { type: 'string' } },
    top_conclusions: { type: 'array', items: { type: 'string' } },
    report_path: { type: 'string' },
  },
  required: ['agent_id', 'missing', 'contradictions', 'weakest_evidence', 'top_conclusions', 'report_path'],
}

const MARKET = {
  M01: { role: 'Wordle-achtigen wereldwijd', task: 'Breng Wordle-achtige apps op Google Play (en kort de App Store) in kaart met minstens 1K+ downloads: MINSTENS 12 apps, van groot (NYT Games/Wordle, "Wordle!" van Lion Studios, Word Guess, Wordly, Quordle, Octordle, Wordhurdle, Wordus, Lingo-achtigen) tot klein/indie en open source. Per app: downloads-tier, rating, verdienmodel (ads / IAP / abonnement / betaald / gratis zonder iets), prijzen, reclamevrij ja/nee, open source ja/nee. Zoek specifiek ook: hoeveel downloads halen Wordle-klonen van solo-devs (Reddit/HN "I made a Wordle clone" met Play-cijfers)? Welke features zie je bij de succesvolle (dagpuzzel, streaks, deel-raster, meerdere talen, leaderboard, onbeperkt spelen)? Hoe onderscheidt Word Guesser (16 talen, 4-8 letters, duels, timed, 100 KB, reclamevrij) zich?' },
  M02: { role: 'Nederlandstalige en meertalige Wordle-achtigen', task: 'Nederlandse Wordle-varianten: Woordle (woordle.nl), "Woord van de dag", Lingo-apps (Lingo is een NL tv-format), "Woorden raden", RTL/NOS/krant-varianten, Vlaamse varianten; meertalige Wordle-apps (16 talen is de USP van Word Guesser: welke apps bieden ook veel talen, en hoeveel downloads halen ze?); open-source Wordle-apps op Play/F-Droid/GitHub met bekende downloads (bv. opatry/wordle-kt, "Wordle" Flutter-klonen, Nerdle, Worldle). Ook: hoe groot is de NL/BE markt voor woordspellen op mobiel (Denksport-apps, Puzzelen.nl, Woordzoeker-apps, "Lingo"-apps: downloads-tiers en verdienmodel)? Per app: downloads-tier, rating, verdienmodel, prijzen, bron.' },
  M03: { role: 'Wordscapes-achtigen (Woord Swiper)', task: 'Swipe-woordspellen: Wordscapes (PeopleFun), Word Cookies, Word Connect, Words of Wonders (Fugo), Word Trip, Wordscapes Uncrossed, Word Collect, Word Crossy, Word Link, plus NEDERLANDSTALIGE varianten ("Woord Puzzel", "Woorden van Wonders", "Word Connect Nederlands", "WOW Nederlands", "Woordzoeker Pro", Kruiswoord-swipe-apps in het Nederlands). Per app: downloads-tier, rating, verdienmodel (ads + IAP-munten; prijzen van muntenpakketten en "remove ads"), geschatte omzet (Sensor Tower/AppMagic-snippets, met datum), en kleinere indie-varianten met 1K-100K downloads: hoe verdienen die? Hoe is de hint-/munteneconomie van Wordscapes opgebouwd (munten per level, prijs hint, prijs pakket)? Minstens 10 apps.' },
  M04: { role: 'Kruiswoord- en Zweedse-puzzel-apps (Woord Puzzel)', task: 'Kruiswoord-apps: NYT Crossword, Daily Themed Crossword (PlaySimple), Crossword Jam, Redstone Crossword, Crossword Puzzle Free, "Crosswords With Friends"; NEDERLANDS: Denksport-app (Keesing), Sanders Puzzels, "Zweedse puzzel"-apps, "Kruiswoordpuzzel Nederlands", "Puzzelboeken", Puzzelen.nl; DUITS: Schwedenrätsel-apps (zelfde genre, grote markt); open-source: Shortyz/Forkyz, billthefarmer/crossword. Per app: downloads-tier, rating, verdienmodel (let op abonnementen bij uitgevers: prijzen per maand/jaar), gegenereerd vs handgemaakt, echte definities ja/nee. Minstens 10 apps. Wat betekent "gegenereerde Zweedse puzzels met echte woordenboekdefinities" als positionering tegenover deze markt?' },
  M05: { role: 'Dorpsbouwers in de geest van Beasts and Bumpkins', task: 'Isometrische dorps-/stadsbouwers en settlers-achtigen op Android: Townsmen en Townsmen VR/Premium (HandyGames), Pocket City en Pocket City 2 (premium), Kingdom Two Crowns, Settlement Survival, Banished-achtigen, Farm/Village-builders, "Medieval"-builders, Forager, Stardew Valley (premium, als referentie), kleine indie premium builders met 1K-100K downloads. Per app: downloads-tier, rating, premium vs F2P, prijs, verdienmodel, omvang. Specifiek: hoe verkopen KLEINE premium builders op Play (cijfers/postmortems, bv. Pocket City $4.99; "Townsmen Premium" vs gratis versie)? Minstens 10 apps.' },
  M06: { role: 'Polytopia-achtigen en 4X (Kwelder)', task: 'The Battle of Polytopia (gratis + stammen-IAP: hoe werkt het, welke prijzen, welke omzet/downloads meldt Midjiwan?), Unciv (open source, gratis: downloads op Play), Hexonia, Civilization VI mobiel, Rising Empires, Age of Strategy / Age of Civilizations II (betaald), Uciana, Island Empire, Pocket Empires, Hex Commander, "Civ-achtige" indie 4X-spellen op Play met 1K-100K downloads. Per app: downloads-tier, rating, verdienmodel, prijzen, sessielengte/positionering ("in minuten op de telefoon"). Minstens 10 apps. Wat is het verdienmodel dat in dit genre bewezen werkt zonder ads?' },
  M07: { role: 'AI-dungeon-master-apps (DnDAI)', task: 'AI Dungeon (Latitude): abonnementen/credits, prijzen, downloads; Friends & Fables; Hidden Door; "AI Game Master"; "DnD AI"; "RPG AI Dungeon Master"; Talefy; Infinite Worlds; NovelAI (tekst); Character.AI-achtige rollenspel-apps; kleinere Play-apps met LLM-dungeon-masters en 1K-100K downloads. Per app: downloads-tier, rating, verdienmodel (abonnement vs credits vs "eigen API-sleutel" vs gratis met limiet), prijzen, welk model/LLM, en welke klachten gebruikers hebben (kosten, limieten, geheugen). Minstens 8 apps. Leid af: welke LLM-kosten per beurt impliceert dit en welke prijs is gangbaar? (TIP VOOR P12 als je kostencijfers vindt.)' },
  M08: { role: 'Levenssimulaties (Fast Lane)', task: 'BitLife (Candywriter): downloads, Bitizenship-prijs, ads, omzet; InstLife; "Life Simulator"-apps; "Mini Life"; "Alter Ego"; "Jones in the Fast Lane"-remakes/hommages (ook op itch.io/Steam); "Tiny Life"; "Youtubers Life"; "The Game of Life" (Marmalade, premium); "Idle Life Sim"; hotseat-/online-duel-partijspellen; kleine indie life-sims op Play met 1K-100K downloads. Per app: downloads-tier, rating, verdienmodel, prijzen, multiplayer ja/nee. Minstens 10 apps. Wat is de positionering van een "Jones in the Fast Lane"-achtige op Android (de niche lijkt leeg: klopt dat?).' },
  M09: { role: 'Peuter-/eerste-woordjes-apps (Kinderwoordjes)', task: 'Eerste-woordjes- en peuter-leerapps, NL en internationaal: "Eerste woordjes", "Baby Flash Cards", "First Words" (verschillende devs), Lingokids, Khan Academy Kids (gratis), Sago Mini, Toca Boca, Juf Jannie-apps, Nijntje-apps, Woezel en Pip, Squla, Pepi Play, "Peuterspelletjes", "Kleuter"-apps, Duolingo ABC. Per app: downloads-tier, rating, verdienmodel (abonnement, betaald, "ouderpoort", geen ads vanwege Families-beleid), prijzen, taalondersteuning. Minstens 10 apps. Wat betalen Nederlandse ouders voor zulke apps en welke kanalen gebruiken ze (Play, App Store, Squla-achtige abonnementen)? Welke eisen stelt Google Play Families aan reclame en betalingen in kinderapps (VRAAG AAN P06 als je het niet rond krijgt)?' },
  M10: { role: 'EV-laad- en dynamische-energieprijs-apps NL (e-charge)', task: 'Dynamische-energieprijs-apps in Nederland: ANWB Energie, Frank Energie, Zonneplan, Tibber, NextEnergy, "Energieprijzen", "Stroomprijs", "Dynamische Energieprijzen", "EnergyZero", "Jedlix" (slim laden), "Stekker.app"; EV-laadcalculators en laad-apps: "EV Charging Calculator", LeafSpy, ABRP (A Better Routeplanner), Chargemap, PlugShare, Shell Recharge, "Laadpaal"-apps, "EV Charge Time". Per app: downloads-tier, rating, verdienmodel (door leverancier gefinancierd, abonnement zoals ABRP Premium, affiliate/referral-bonussen, betaald), prijzen. Minstens 10 apps. Wat is realistisch voor een onafhankelijke rekenhulp van één scherm (NL-niche: Nissan Leaf aan stopcontact)?' },
  M11: { role: 'Sport-/club-/teamapps NL (Volleybal)', task: 'Nevobo-app (officieel, Nevobo = volleybalbond), Volleybal.nl, Sportlink / Sportlink Club, Spond, Teamers, KNVB Wedstrijdzaken, Voetbal.nl, "Mijn Team", TeamSnap, Heja, Teamstuff, Kampioenen-apps, ClubCollect, AllUnited, "Teamleider", "Volleybal Stand"-apps. Per app: downloads-tier, rating, verdienmodel (B2B-abonnement per club/lid, gratis bond-app, sponsors, premium-functies), prijzen per club of lid. Minstens 8 apps. Specifiek: heeft een onafhankelijke Nevobo-programma-app (zonder account, offline, aanwezigheid delen via code) bestaansrecht? Zijn er voorwaarden van Nevobo op het gebruik van hun data/API (zoek "Nevobo API", "Nevobo open data", voorwaarden)?' },
  M12: { role: 'AI-stem-/zangtools (Vocal)', task: 'Lokale en open-source stemkloon-/stemconversietools (RVC, Applio, so-vits-svc, Coqui TTS, XTTS, OpenVoice, "Voice Changer"-desktop) en commerciële apps/diensten (Voice.ai, Voicemod, Kits.ai, ElevenLabs, Suno, Udio, Covers.ai, Jammable/Voicify, "AI Cover"-apps op Play). Per tool/app: gebruikers/downloads/sterren, verdienmodel (abonnement/credits, OSS-donaties/Patreon/GitHub Sponsors, "zelf-gehost = gratis"), prijzen. Minstens 8. Ook: juridische en beleidsgrenzen (stemrechten, Play-beleid over deepfake-audio, EU AI Act-transparantie) en of een zelf-gehoste desktop-tool überhaupt te monetiseren is (voorbeelden: Applio Patreon, Pinokio, LM Studio).' },
}

const MONEY = {
  P01: { role: 'Advertentie-economie voor casual woord-/puzzelgames', task: 'AdMob en andere netwerken (AppLovin, Unity Ads, ironSource) voor casual woord-/puzzelgames 2025-2026: eCPM per formaat (banner, interstitial, rewarded video, app open) in Nederland/EU versus VS; ARPDAU-benchmarks voor word games; wat 1K, 10K, 100K en 1M downloads realistisch per maand opleveren (geef uitgewerkte rekenvoorbeelden met aannames en bronnen: retentie, sessies/dag, impressies/sessie); invloed van GDPR-consent (Google UMP) en Apple ATT op eCPM; niet-gepersonaliseerde ads (NPA) en contextuele netwerken zonder tracking (EthicalAds, Carbon Ads, Google NPA): eCPM-verschil met gepersonaliseerd. Eerlijke conclusie: is ads toevoegen de moeite waard onder 10K downloads, en wat kost het aan "geen trackers"-belofte?' },
  P02: { role: 'In-app aankopen in casual word games', task: 'IAP-modellen: "remove ads" eenmalig, hint-/muntpakketten, thema\'s/cosmetica, "unlock all levels", tip-jar-IAP ("buy me a coffee" als IAP), "pay what you want". Benchmarks 2024-2026: conversie naar betalende spelers in het puzzle-genre, ARPPU, prijsankers ($0.99-$4.99-$9.99), Play-servicefee 15% onder $1M (Small Business) en Google als Merchant of Record voor btw. Voorbeelden van kleine word games die ALLEEN via IAP (zonder ads) verdienen, met cijfers. Hoe benut je het bestaande muntensysteem (Word Guesser: 1 munt per dagpuzzel, munt redt streak; Woord Swiper: bonuswoorden = munten voor hints; de web-versie heeft al "Ko-fi-aankoop -> munten claimen") zonder pay-to-win en zonder de reclamevrije positionering te beschadigen?' },
  P03: { role: 'Betaald vooraf, Pro-versies en Play Pass', task: 'Betaalde apps op Google Play 2025-2026: werkt het nog? Voorbeelden van betaalde puzzel-/strategie-apps met downloads/omzet (Pocket City, Mindustry (betaald op Play, gratis elders), Hexologic, Slay the Spire, Terraria, Stardew Valley, Age of Civilizations II, Simon Tatham\'s Puzzles (gratis)); "gratis lite + betaalde Pro"-model (Nova Launcher Prime, Tasker, Fossify/Simple Mobile Tools Pro-versies, Sleep as Android): cijfers; prijs-elasticiteit ($0.99 vs $2.99 vs $4.99); piraterij/APK-mirrors; Google Play Pass: voorwaarden voor deelname, hoe devs betaald worden (engagement-based), wat kleine devs ermee verdienen (postmortems). Conclusie: welk betaald model past bij apps van 100 KB zonder ads?' },
  P04: { role: 'Abonnementen', task: 'Abonnementen voor puzzelgames en kleine apps: NYT Games (prijs, aantal abonnees), Puzzmo, Denksport/Keesing-apps, Lumosity, Sudoku.com, Crossword Jam, Wordscapes-abonnement ("Wordscapes+"?), RevenueCat "State of Subscription Apps" 2025/2026 benchmarks (trial-conversie, churn maand 1, retentie jaar 1, mediaan omzet per app), Play-fee 15% voor abonnementen, realistische omzet voor een solo-dev met <50K gebruikers; wat moet je bieden om een abonnement te rechtvaardigen (dagelijkse content, archief, sync, duels); "lifetime"-aankoop als alternatief; abonnementsmoeheid in NL. Conclusie met cijfers: wanneer wel/niet.' },
  P05: { role: 'Donaties en fooien', task: 'Ko-fi, Buy Me a Coffee, GitHub Sponsors, Liberapay, Patreon, OpenCollective, tip-jar als IAP, Tikkie/iDEAL-betaallink. Concrete cijfers uit postmortems van open-source/indie-devs (F-Droid-devs, "Ask HN: how much do you make from donations", r/fossdroid, r/androiddev, blogposts 2023-2026): typische opbrengst per 1.000 actieve gebruikers, conversie, wat de conversie verhoogt (in-app vragen na een "moment van vreugde" zoals een gewonnen dagpuzzel; Shattered Pixel Dungeon\'s donatie-IAP; "supporter badge"). Regels en fees van Ko-fi (0% op donaties? Stripe/PayPal-kosten). Google Play-beleid: mag een Play-app naar Ko-fi/externe donatiepagina linken, of moet een donatie via Play Billing (zoek het Payments-beleid 2025-2026 letterlijk op)? Apple idem kort.' },
  P06: { role: 'Google Play- en App Store-beleid, kosten en regels 2026', task: 'Alles met datum en OFFICIËLE bron (support.google.com/googleplay/android-developer, developer.android.com, developer.apple.com): Play developer-account ($25 eenmalig), eis van 12 testers / 14 dagen closed testing voor nieuwe persoonlijke accounts (actuele regels), identiteits-/D-U-N-S-verificatie, servicefee 15% tot $1M (hoe aanmelden), abonnementen 15%, Families-beleid en reclame/betalingen in apps voor kinderen (Kinderwoordjes!), Data safety-sectie bij "geen tracking", Play Billing verplicht voor digitale goederen (en uitzonderingen: donaties? fysieke goederen?), EU DMA/alternatieve betalingen en externe links in de EU (2025-2026 stand), Play Pass-voorwaarden, target-SDK-eisen, "reclamevrij" als claim in de listing. Apple kort: $99/jaar, Small Business Program 15%, PWA naar App Store (Capacitor/PWABuilder) en of een web-wrapper geaccepteerd wordt.' },
  P07: { role: 'Web/PWA-monetisatie en Wordle-achtige exits', task: 'Hoe verdienen browser-/PWA-woordspellen zonder store: Wordle -> NYT (bedrag, 2022), Quordle -> Merriam-Webster, Heardle -> Spotify, Worldle, Nerdle, Framed, Connections-klonen, Puzzmo (Hearst), "Contexto", "Semantle": omzet, verkeer, exits; web-ads (Google AdSense, Ezoic, Mediavine, Raptive: RPM voor puzzle-/game-sites 2025, drempels zoals 50K sessies); betaallinks (Ko-fi, Stripe Payment Links, Paddle/Lemon Squeezy als Merchant of Record voor EU-btw); sponsoring; "Web Monetization"-standaard (status 2026). Benchmarks: puzzle-website-verkeer en omzet (Indie Hackers, r/juststart). Wat kan een PWA met 16 talen realistisch verdienen? Ook: Trusted Web Activity (TWA)/PWABuilder om een PWA op Play te zetten met Play Billing (Digital Goods API): werkt dat in 2026?' },
  P08: { role: 'Indie-postmortems met echte cijfers', task: 'Vind MINSTENS 10 postmortems (2023-2026) van solo- of kleine devs met woord-/puzzelgames, kleine strategiespellen of kleine nuts-apps op Google Play, met concrete downloads ÉN omzet (Reddit r/androiddev, r/gamedev, r/IndieDev, r/incremental_games, r/SoloDevelopment, Hacker News, Indie Hackers, Medium, dev-blogs, YouTube-transcripts, Twitter/X-threads). Per case: naam, genre, downloads, verdienmodel, omzet per maand, tijd geïnvesteerd, marketing, wat werkte en wat niet. Leid af: mediaan omzet per 1.000 downloads per model (ads / IAP / betaald / donaties) en de spreiding. Wees eerlijk over "survivorship bias" en over de vele apps die bijna niets verdienen.' },
  P09: { role: 'Downloads krijgen: ASO en distributie', task: 'Hoe halen kleine apps 1K -> 10K -> 100K downloads zonder budget: ASO (titel/keywords/screenshots/lokalisatie: 16 talen = 16 markten, met cijfers over lokalisatie-effect), Play "new personal developer"-drempels, organische kanalen (Reddit, Product Hunt, Hacker News "Show HN", nieuwsbrieven, TikTok/Shorts), de kracht van dagelijkse puzzels en deel-rasters (Wordle-groei: cijfers), cross-promotie binnen een portfolio (de showcase-pagina abons.github.io/Apps), PWA-SEO (Google indexeert PWA\'s; zoekvolume "woordle", "wordle nederlands", "zweedse puzzel"), F-Droid als gratis distributie (afgevallen: wat kost dat aan bereik? F-Droid-gebruikersaantallen), itch.io, Samsung Galaxy Store/Huawei AppGallery als extra kanalen. Eerlijk over wat solo-devs rapporteren over organische downloads zonder marketing.' },
  P10: { role: 'Nederlandse markt, belasting en betalen', task: 'Omvang NL/BE-markt voor mobiele puzzel-/woordspellen (Denksport/Keesing-cijfers, Puzzelen.nl, de "Woordle"-hype in NL 2022, Lingo), NL bereidheid om voor apps te betalen (app-uitgaven per capita, Android- vs iOS-marktaandeel in NL 2025-2026, iDEAL), kids-apps NL (Squla-prijzen, Juf Jannie), en de FISCALE kant voor een solo-dev in loondienst met app-inkomsten: "resultaat uit overige werkzaamheden" vs ondernemer (Belastingdienst-criteria), KvK-inschrijving nodig?, btw en de kleineondernemersregeling (KOR, grens €20.000), Google Play als Merchant of Record (btw door Google), Ko-fi-/donatie-inkomsten aangeven, hobby-vrijstelling. OFFICIËLE bronnen (belastingdienst.nl, kvk.nl) met datum.' },
  P11: { role: 'Privacyvriendelijk verdienen zonder trackers', task: 'Hoe verdienen apps die "geen ads, geen trackers" als USP hebben: Shattered Pixel Dungeon (donatie-IAP in een gratis OSS-game: Evan Debenham heeft cijfers gepubliceerd), Mindustry (betaald op Play, gratis elders), Unciv, Simon Tatham, Fossify/Simple Mobile Tools (verkoop aan ZipoApps 2023: les), Nova Launcher (verkoop aan Branch: les), Tasker, Aegis, AdGuard, Proton, Olauncher, Feeel, "Catima", F-Droid-devs met Pro-versies op Play. Welke modellen werken (donatie-IAP, betaald op Play + gratis elders, Pro-upgrade, "supporter badge", lifetime), welke cijfers rapporteren ze; GDPR/"geen toestemmingsbanner" als voordeel in store-tekst; contextuele ads zonder tracking als compromis (eCPM); open source als marketing versus risico van herpublicatie (APK-klonen op Play).' },
  P12: { role: 'B2B, licenties, affiliates en AI-kosten', task: '(a) Kinderwoordjes: licenties aan scholen/kinderopvang/logopedisten, NL edu-markt (Basispoort, Squla B2B, "Bereslim", "Gynzy"): prijzen per leerling/instelling. (b) Volleybal: clubsponsoring, Nevobo-partnerschap, white-label voor verenigingen, prijsmodellen van Spond/Sportlink per lid. (c) e-charge: affiliate/referral van energieleveranciers (Tibber, Frank Energie, Zonneplan, ANWB: bedrag per aanmelding, 2025-2026), laadpas-affiliates. (d) Woordspellen: licentie van puzzelgenerator/woordlijsten/dagpuzzel-widget aan uitgevers, kranten of websites (Keesing, Denksport, regionale kranten, Puzzelen.nl): bestaat die markt, prijzen? (e) DnDAI: LLM-kosten per speelbeurt bij Claude Haiku/Sonnet, GPT-4o-mini, Gemini Flash (prijzen per miljoen tokens 2026, ~2-4K tokens per beurt, 20-40 beurten per sessie): kosten per sessie en per maandelijkse speler; daardoor is "gratis" onhoudbaar: vergelijk credits vs abonnement vs "eigen API-sleutel" vs on-device model (Gemini Nano/klein open model); welke prijs dekt de kosten met marge?' },
}

const GROUPS = {
  S01: { role: 'Strategie woordspellen-trio', apps: 'Word Guesser, Woord Swiper en Woord Puzzel (web/PWA + Android via Play)', market: ['M01', 'M02', 'M03', 'M04'] },
  S02: { role: 'Strategie Beasts en Kwelder', apps: 'Beasts (dorpsbouwer) en Kwelder (4X), beide Android, nog in ontwikkeling', market: ['M05', 'M06'] },
  S03: { role: 'Strategie DnDAI', apps: 'DnDAI (AI-dungeon-master, Android, in ontwikkeling; LLM-kosten per beurt)', market: ['M07'] },
  S04: { role: 'Strategie Fast Lane', apps: 'Fast Lane (levenssimulatie, Android, binnenkort op Play, ±210 KB, tweetalig, multiplayer)', market: ['M08'] },
  S05: { role: 'Strategie nuts-apps', apps: 'Kinderwoordjes (peuter-PWA), e-charge (EV-laadcalculator PWA) en Volleybal (Nevobo-team-PWA)', market: ['M09', 'M10', 'M11'] },
  S06: { role: 'Strategie Vocal en portfolio-niveau', apps: 'Vocal (zelf-gehoste AI-stemtool) EN het portfolio als geheel: merk, cross-promotie, Play-account, prioritering van tijd versus verwachte opbrengst over alle 11 apps', market: ['M12'] },
}

function strategistTask(sid) {
  const g = GROUPS[sid]
  return `
JOUW OPDRACHT (fase Strategie): schrijf het monetisatie-advies voor: ${g.apps}.
Lees EERST volledig: cat ${R}/portfolio.md ; cat ${R}/board.md ; daarna de marktrapporten van jouw apps volledig (${g.market.map(m => R + '/reports/' + m + '.md').join(' ; ')}), ALLE twaalf monetisatie-rapporten volledig (ls ${R}/reports/P*.md), en van de overige marktrapporten de samenvatting (head -40). Dit is de kennis van 24 collega's: gebruik hun cijfers en citeer hun bron-URL's (niet "volgens M03" maar de echte bron). Doe daarna zelf 4-10 gerichte zoekopdrachten om gaten te vullen of twijfels te checken.
Eisen aan het advies:
- Blijf binnen de filosofie van de eigenaar (klein, snel, offline, geen reclame, geen trackers, geen accounts, geen runtime-dependencies). Als je daar toch van wilt afwijken (bijv. niet-gepersonaliseerde ads), zeg expliciet wat het kost aan positionering en waarom het de moeite zou zijn.
- Per aanbevolen model: waarom, VERWACHTE OPBRENGST ALS RANGE met de aannames (downloads, conversie, prijs) en bronnen, en wat er concreet gebouwd/ingesteld moet worden (zo klein mogelijk).
- Een eerlijke "verwacht niet"-paragraaf: wat is realistisch voor een solo-dev in NL met deze apps op 1K / 10K / 100K downloads.
- "Niet doen"-lijst met reden.
- Volgorde van stappen (eerst downloads, dan geld? of andersom?), inclusief wat al bestaat (munten, Ko-fi, leaderboard, dagpuzzels, 16 talen).
- Risico's (beleid, juridisch, reputatie, tijd).
Zet op het bord: je 3 belangrijkste conclusies met bron, plus "VRAAG AAN C${sid.slice(1)}: val dit vooral aan op ..." (wat jij zelf je zwakste punt vindt).
Rapport: ${R}/reports/${sid}.md (120-250 regels).`
}

function criticTask(sid, cid, strat) {
  const g = GROUPS[sid]
  const claims = strat && strat.key_claims ? JSON.stringify(strat.key_claims, null, 1) : '(geen gestructureerd resultaat ontvangen; haal de claims uit het rapport)'
  const models = strat && strat.recommended_models ? JSON.stringify(strat.recommended_models.map(m => ({ model: m.model, range: m.expected_revenue_range })), null, 1) : '(zie rapport)'
  return `
JOUW OPDRACHT (fase Kritiek, red team): probeer het strategie-advies van ${sid} (${g.apps}) ONDERUIT TE HALEN. Standaardhouding: sceptisch. Lees: cat ${R}/reports/${sid}.md ; cat ${R}/board.md ; de rapporten die ${sid} aanhaalt (M- en P-rapporten in ${R}/reports/). Doe daarna 5-12 eigen zoekopdrachten om de belangrijkste cijfers en aannames te controleren (zoek de ORIGINELE bron op en kijk of die echt zegt wat beweerd wordt, en of hij actueel is).
Aanbevolen modellen van ${sid}: ${models}
Belangrijkste claims van ${sid}: ${claims}
Lever:
- Verdict: houdbaar / deels houdbaar / niet houdbaar, met de 3-5 sterkste bezwaren.
- Lijst van claims zonder of met zwak bewijs (en wat de bron werkelijk zegt).
- Gemiste kansen of modellen die ${sid} niet overwoog, met bewijs.
- Jouw HERZIENE advies in 10-20 regels: wat zou jij de eigenaar nu zeggen te doen, in welke volgorde, met realistische range.
- Beantwoord bovendien de "VRAAG AAN ${cid}" van ${sid} op het bord, en ELKE andere open "VRAAG AAN" op het bord die nog geen "ANTWOORD AAN" heeft en die jij kunt beantwoorden (noteer welke je beantwoordde).
Zet op het bord: "ANTWOORD AAN ${sid}: ..." met je verdict en de 3 grootste bezwaren, plus de antwoorden op andere open vragen.
Rapport: ${R}/reports/${cid}.md (80-200 regels).`
}

const VERIFY = {
  V01: { role: 'Verificatie van app-feiten', task: `
JOUW OPDRACHT (fase Verificatie, lens: APP-FEITEN): lees cat ${R}/board.md en de S- en C-rapporten (ls ${R}/reports/S*.md ${R}/reports/C*.md), en de M-rapporten waar nodig. Kies de 15-20 vergelijkbare apps die het ZWAARST wegen in de strategieën en kritieken (vaak genoemd of dragend voor een conclusie). Verifieer per app met NIEUWE zoekopdrachten: bestaat de app nog, developer, downloads-tier op Play (1K+/10K+/...), rating, verdienmodel (ads/IAP/betaald/abonnement), prijzen. Status per claim: bevestigd / weerlegd / genuanceerd / niet te verifiëren, met bron-URL en datum. Zet de weerlegde en genuanceerde claims op het bord als "CORRECTIE: ...". Rapport: ${R}/reports/V01.md.` },
  V02: { role: 'Verificatie van cijfers', task: `
JOUW OPDRACHT (fase Verificatie, lens: CIJFERS): lees cat ${R}/board.md en de S-, C- en P-rapporten (ls ${R}/reports/). Verzamel de 15-20 kwantitatieve claims die de conclusies DRAGEN: eCPM's, ARPDAU, conversiepercentages (IAP, abonnement, donaties), omzet per 1.000 downloads, prijzen, Play-fees, LLM-tokenprijzen, exit-bedragen (Wordle), postmortem-omzetten. Verifieer elk met NIEUWE zoekopdrachten tegen de originele bron: klopt het getal, is het actueel (2025-2026 of gedateerd), wordt het uit zijn context gehaald, is er een betere bron? Status per claim: bevestigd / weerlegd / genuanceerd / niet te verifiëren, met bron-URL. Zet weerlegde/genuanceerde cijfers op het bord als "CORRECTIE: ...". Rapport: ${R}/reports/V02.md.` },
  V03: { role: 'Verificatie van beleid en juridische claims', task: `
JOUW OPDRACHT (fase Verificatie, lens: BELEID/JURIDISCH): lees cat ${R}/board.md en de S-, C-, P06-, P05-, P10-rapporten (ls ${R}/reports/). Verzamel alle beleids-, kosten- en juridische claims die de conclusies dragen: Play-fees (15%/30%), testers-eis voor nieuwe accounts, Families-beleid en reclame in kinderapps, Play Billing-verplichting en donaties/externe links, EU DMA-uitzonderingen, Apple Small Business Program, Play Pass-voorwaarden, NL belasting (KOR-grens, resultaat uit overige werkzaamheden, KvK), Ko-fi-fees, Nevobo-datavoorwaarden, AI-stemrecht/EU AI Act, GPL-risico's. Verifieer elk tegen de OFFICIËLE bron (support.google.com, developer.apple.com, belastingdienst.nl, kvk.nl, ko-fi.com, eur-lex) met NIEUWE zoekopdrachten en datum. Status per claim: bevestigd / weerlegd / genuanceerd / niet te verifiëren. Zet correcties op het bord als "CORRECTIE: ...". Rapport: ${R}/reports/V03.md.` },
}

const QTASK = `
JOUW OPDRACHT (fase Volledigheid): jij bent de laatste van de 40. Lees cat ${R}/board.md volledig, alle S-, C- en V-rapporten volledig, en de M-/P-rapporten diagonaal (ls ${R}/reports/). Beantwoord: (1) Wat ONTBREEKT nog om de twee hoofdvragen van de eigenaar te beantwoorden (vergelijkbare apps >1.000 downloads per app; beste manier om geld te verdienen)? Welke app-categorie is onderbelicht, welke claim is nooit geverifieerd, welke bron nooit gelezen, welk verdienmodel nooit overwogen? (2) Welke TEGENSTRIJDIGHEDEN tussen agents zijn niet opgelost (noem agent-id's en wat ieder beweert, en welke kant het bewijs op wijst)? (3) Welke conclusies rusten op het ZWAKSTE bewijs? (4) Geef een gerangschikte lijst van de 10 best onderbouwde conclusies voor de eigenaar, elk met de sterkste bron-URL. Doe zelf 5-10 zoekopdrachten om de grootste gaten alvast te dichten. Rapport: ${R}/reports/Q01.md. Zet op het bord een slotbericht met de 5 grootste open punten.`

const phase = args && args.phase
if (phase === 'sweep') {
  const ids = args.ids
  log('Sweep gestart: ' + ids.join(', '))
  const results = await parallel(ids.map(id => () => {
    const a = MARKET[id] || MONEY[id]
    const isMarket = !!MARKET[id]
    return agent(common(id, a.role) + '\nJOUW OPDRACHT (fase ' + (isMarket ? 'Markt' : 'Monetisatie') + '): ' + a.task + '\n\nRapport: ' + R + '/reports/' + id + '.md', {
      label: id + ' · ' + a.role,
      phase: isMarket ? 'Markt' : 'Monetisatie',
      schema: isMarket ? MARKET_SCHEMA : MONEY_SCHEMA,
    })
  }))
  const missing = ids.filter((id, i) => !results[i])
  if (missing.length) log('Geen resultaat van: ' + missing.join(', '))
  return results
}
if (phase === 'strategy') {
  const groups = args.groups
  log('Strategie + kritiek voor: ' + groups.join(', '))
  const out = await pipeline(groups,
    sid => agent(common(sid, GROUPS[sid].role) + strategistTask(sid), { label: sid + ' · ' + GROUPS[sid].role, phase: 'Strategie', schema: STRATEGY_SCHEMA }),
    (strat, sid) => {
      const cid = 'C' + sid.slice(1)
      return agent(common(cid, 'Red team van ' + sid) + criticTask(sid, cid, strat), { label: cid + ' · red team ' + sid, phase: 'Kritiek', schema: CRITIQUE_SCHEMA })
        .then(c => ({ group: sid, strategy: strat, critique: c }))
    }
  )
  return out
}
if (phase === 'verify') {
  log('Verificatie door V01-V03')
  const vs = await parallel(['V01', 'V02', 'V03'].map(v => () => agent(common(v, VERIFY[v].role) + VERIFY[v].task, { label: v + ' · ' + VERIFY[v].role, phase: 'Verificatie', schema: VERIFY_SCHEMA })))
  log('Volledigheidscheck door Q01')
  const q = await agent(common('Q01', 'Volledigheidscriticus') + QTASK, { label: 'Q01 · volledigheid', phase: 'Volledigheid', schema: GAPS_SCHEMA })
  return { verifications: vs.filter(Boolean), gaps: q }
}
throw new Error('Onbekende fase: ' + phase)