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
