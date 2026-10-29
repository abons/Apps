# Beasts & Bumpkins-remake: onderzoek AI-orkestratie

Onderzoek van 21-22 oktober 2026: kan Claude Code een volledige remake (nieuwe/upscaled graphics, animaties, geluid) zelf orkestreren op een Windows-pc?

> **Let op:** de vier onderzoeksrapporten in `onderzoek.md` zijn **niet nagecontroleerd**. De factcheck-agents vielen uit door de sessielimiet. Controleer prijzen, licenties en versies voordat je iets koopt.

## Conclusie

Grotendeels wel, maar niet volledig.

### Wat Claude zelf kan
- Claude Code draait in PowerShell zonder adminrechten (`irm https://claude.ai/install.ps1 | iex` of `winget install Anthropic.ClaudeCode`).
- Chrome bedienen via de extensie "Claude in Chrome" (`claude --chrome`). Gebruikt je bestaande logins. Vereist een Pro-, Max-, Team- of Enterprise-abonnement.
- Software installeren met winget: Godot (`GodotEngine.GodotEngine`), Python, FFmpeg, Blender en Git.
- Godot 4 vanaf de commandline: importeren, testen met GUT of gdUnit4, exporteren, screenshots maken (Movie Maker) en playtests met bot-input.
- Graphics:
  1. Conceptart met ComfyUI lokaal en een eigen stijl-LoRA. Basismodellen FLUX.2 klein 4B of Qwen-Image (Apache 2.0).
  2. 3D-modellen en rigs via de Tripo-API.
  3. Blender headless rendert de figuren in 8 richtingen.
  4. Een Python-script maakt er sprite sheets van.
- Audio: de ElevenLabs-API voor geluidseffecten, nieuw ontworpen stemmen (Voice Design) en muziek, en Stable Audio 3 lokaal. Technische controle gaat met ffmpeg (loudnorm, clipping, spectrogrammen).

### Wat de mens moet doen
- Accounts, API-sleutels en betalingen regelen.
- UAC-prompts goedkeuren (Blender, Git, Node).
- Audio beluisteren. Claude kan geen geluid horen.
- Stijl kiezen, ontwerpen goedkeuren en de missies balanceren door ze te spelen.
- Midjourney, Suno en Mixamo met de hand gebruiken: ze hebben geen officiële API en automatiseren mag niet. Udio valt af, want downloaden is daar uitgeschakeld.
- Rechten: het origineel is van Worldweaver/EA. Gebruik geen originele assets en bij voorkeur een eigen naam.

### Beperkingen
- Geen sandbox op native Windows. Gebruik de permissiemodus `auto`; `bypassPermissions` is alleen voor een geïsoleerde VM. Werk bij voorkeur op een aparte pc of een apart account.
- GPU: NVIDIA met minimaal 12 GB VRAM (16 GB aanbevolen) en 32 GB RAM.
- Niet gebruiken: Hunyuan3D (de licentie sluit de EU uit) en MusicGen/AudioCraft (de modelgewichten zijn niet-commercieel).
- Omvang van het origineel: 30 missies, ongeveer 30 gebouwen, 33 soorten figuren, ongeveer 180 animaties en 6.000 tot 9.000 sprite-frames.

### Ultracode of max effort
- **Ultracode** zet meerdere agents tegelijk in, met onderlinge controle. Gebruik het alleen voor grote, afgebakende fasen: onderzoek, assets in bulk maken, grote reviews. Het verbruikt je limiet snel: in dit onderzoek zat de limiet al na 4 agents vol.
- **Effort**: gebruik dagelijks high of xhigh. Max alleen voor de lastigste onderdelen (simulatie, pathfinding, savegames).

### Aanpak
1. Speel het origineel (via bb-patch) en schrijf een ontwerpdocument. OpenBumpkins/BBTools kan helpen om de spelregels te begrijpen. Gebruik daar geen assets uit.
2. Bouw een vertical slice in Godot: 1 missie, 3 gebouwen en 2 soorten dorpelingen, met tijdelijke art.
3. Leg de stijl vast: werk 1 figuur en 1 gebouw helemaal uit.
4. Maak daarna de assets in bulk, eventueel met ultracode.

### Eerste gebouw: de peasant hut (2026-10-28)
`modellen/peasant_hut.py` bouwt de hut in Blender 5.2 na naar `House.png` (217×147, uit `abons/Unity_bumpkins`), zelfde camera (iso 2:1), render op 4×. 12 Opus-rondes van meten tegen de sprite; Sonnet stopte twee keer na 2–3 rondes. Draaien: `blender -b -P peasant_hut.py -- 4`.
- ⚠️ De vergelijkingsplaat bevat de originele sprite en blijft daarom uit deze publieke repo.
- Les: een Gemini-plaat van de sprite als detailreferentie scheelt rondes raden; volgende gebouw eerst plaat, dan eventueel Tripo, dan Blender.
- Animatieklaar voor realtime 3D (2026-10-29): beide deuren zijn een leeg object op de scharnieras (`deur_voor`, `deur_aanbouw`; planken als kinderen), open naar buiten = negatieve hoek om lokaal Z (Blender), om lokaal Y in glTF/Godot. Achter de deuren een donker interieur (vloer, tafel met kaars, haard), achter het luik een binnenruit voor nachtlicht door de kieren. Ankers als lege objecten in de glb: `rook_bron`, `deur_voor_drempel`, `deur_aanbouw_drempel`, `kaars` (venster).
- De 2D-passes (`-- 4 pass=…` of `all`, uitvoer in `modellen/render/`) bestaan nog in het script maar zijn verlaten: de game wordt echt 3D.

### Real-time asset voor Godot (2026-10-29)
`modellen/peasant_hut_realtime.py` maakt van de Cycles-hut een glTF zonder procedurele nodes en zonder halmen. Eerst `peasant_hut.py` (schrijft `peasant_hut.blend`), dan `blender -b -P peasant_hut_realtime.py -- [res=2048] [vergelijk]`, ~4,5 min op de RTX 2060. Uit: `peasant_hut_rt.glb` (LOD0), `peasant_hut_rt_lod1.glb` (LOD1), texturen ook los in `modellen/rt_textures/`, met `vergelijk` ook `peasant_hut_rt_vergelijk.png` (Cycles | EEVEE LOD0 | EEVEE LOD1).
- Per materiaalgroep een atlas, in Cycles gebakken van de echte objecten: kleur (jpg), normaal (OpenGL, jpg 95), ORM (R AO, G ruwheid). Groepen: `steen` (stenen, kozijnen), `riet` (koepel, aanbouwdak, band), `hout` (hout, specie, gras, deuren), plus `riet_kaart` (alfa) en `lod1`.
- Riet: koepel en aanbouwdak dragen de gebakken halmen; daarop alfakaarten (glTF MASK, tweezijdig) op dezelfde lagen als de halmen (de rnd-volgorde uit `peasant_hut.py` wordt via `ast` nagespeeld), rafelige zoom, kuif als gekruiste kaarten. Kaarttextuur = echte halmen, ortho van boven gerenderd.
- Stenen blijven echte stenen: gedecimeerd (18 %), verborgen vlakken weg, een UV-cel per steen.
- Budget: LOD0 ~112k driehoeken (stenen 68k, riet-kaarten 18k, hout 13k), 4 atlassen van 2k (kleur + normaal) + 3× ORM 1k, glb ~25 MB. LOD1 ~6k driehoeken, een atlas van 1k, glb ~2 MB.
- LOD: Godot 4 kent geen LOD-namen in glTF. Twee glb's naast elkaar, wissel via `visibility_range_end` (LOD0) en `visibility_range_begin` (LOD1) op ~25–30 m. Beide hebben dezelfde scharnieren en ankers; LOD1-meshes heten `*_lod1`.
- Namen in LOD0: `deur_voor` › `voordeur`, `deur_aanbouw` › `aanbouwdeur`, `luik`, `ruit`, `tafelkaars`, `kaarsvlam`, `haardvuur`, ankers als lege nodes. Materialen `ruit`, `kaarsvlam`, `haardvuur` zijn vlak en emissief (ruit overdag 0, 's nachts zet de game hem aan).
- ⚠️ OptiX faalt op deze driver (kernel compile error), het script neemt CUDA.
- ⚠️ Selected-to-active cast per pixel naar elk bronobject apart: 460 stenen = 13 min per 512-bake. Het script voegt de bronnen per groep samen en geeft Object-coördinaten, Generated en Object Info > Random mee als attributen: 2 s.
- Afwijking t.o.v. Cycles: riet iets geler en minder contrast (std 0,11 tegen 0,15), laagranden minder scherp, kuif lichter; achterkant (hoek 350–100°) en aanbouw achter/rechts hebben in de bron geen stenen.

## Stand na sessie 2026-10-29 (volgende stappen)

- **Lokale data (niet in git):** `lokaal/` — originele sprites/frames/portretten (`bb_original/`), concepten en beoordelingspagina (`concept/lijst.html`), `map1/`, `missies/`, `bumpkin/ref/`, `audio_origineel/`. `spel/sync.ps1` leest de kaart hieruit.
- **Speelbaar:** `spel/` (missie 1 Aorta: terrein met rotsplateau, natuur, seizoenen, zes bestuurbare dorpelingen). Starten: `spel/README.md`.
- **Modellen** (scripts in git, glb's lokaal): `modellen/bumpkin/` (6 personages, beoordeling 4,5-6,5), `dieren/koe` (6,5), `natuur/` (29), `gebouwen/` (loods, molen = bakkerij, melkerij, kippenhok; 6-7).
- **Docs:** `gameplay.md` sectie 7 = besluiten gebruiker; `missies.md` (30 missies); `map1.md`; `audio.md` (besluiten onderaan); `concept/lijst.md`.
- **Volgende:**
  1. Spellogica naar `missies.md`/`gameplay.md` sectie 7: economie, werk, bouwen, koe-generator, winst/verlies missie 1.
  2. Gebouwen en koe in het spel zetten (de zes personages staan er sinds 2026-10-29 avond in, de hut ook na een bouw).
  3. Gebouwen: rieten dak opnieuw bakken in melkerij/kippenhok (stralen raken de onderlaag).
  4. Personages boven ~6: andere aanpak nodig (gebeeldhouwde of basismodel-mens), geen extra procedurele rondes.
  5. Conceptronde 3 afmaken (Chrome eerst herstarten): voetsoldatengilde (gedownload naar `lokaal/concept/`, beoordeling open), boogschuttersgilde, stadhuis, brouwerij, draagprops.
