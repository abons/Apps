# Beasts & Bumpkins-remake op mobiel: PWA of APK?

Onderzoek 2026-10-30, daarna dezelfde dag de APK-proef (zie "Stand APK"). Waar Godot-gedrag uit kennis komt en niet uit een proef, staat "(onbevestigd)".

## Stand APK (2026-10-30, emulator `beasts`)

- Gedaan: export templates 4.7.2, editor_settings (SDK `D:/emulator`, JDK 17), `export_presets.cfg` (Android, arm64-v8a + x86_64, debug-keystore uit editor_settings, geen pad of wachtwoord in het bestand), `project.godot`: `rendering_method.mobile="mobile"`, schaduw `.mobile` 2048, `import_etc2_astc=true`. Touch in `rts_camera.gd` (1 vinger pannen, 2 vingers pan/knijp-zoom/draai, randpannen uit op mobiel) en `view/bestuur.gd` (gesleepte vinger = geen kader/klik). Geluid laadde al via `load()` (geïmporteerd).
- Export: `"$G" --headless --path . --export-debug "Android" out/android/beasts.apk`, ~1 min, **818 MB** APK. Install op de emulator 25 s, start ~45 s tot het eiland.
- **Mobile/Vulkan op de emulator: zwart beeld, 3 pogingen.** (1) SwiftShader: "no Vulkan surface". (2) `-gpu host -memory 4096`: Vulkan 1.3 op de RTX 2060, sim start (`[spel] missie 1 ...`), maar `Couldn't present to Vulkan queue (VkResult error 5)`, screencap en emulator-screenshot zwart. Met de standaard 1536 MB RAM bleef System UI hangen (ANR). (3) Compatibility-rooktest (`command_line/extra_args="--rendering-method gl_compatibility --rendering-driver opengl3"` tijdelijk in het preset, niet gecommit; `am start --esa command_line_params` werkt niet): **HUD en briefing goed, 3D zwart** door de mist (`android_compat_mist_zwart.jpg`), met `-- --mist=uit` erbij **het hele spel** (`android_compat_start.jpg`): terrein, bomen, bumpkins, vlag, vuur, minikaart, schaduw.
- Touch op de emulator (adb `input`): tik sluit briefing en hint, tik op bouwknop zet bouwmodus aan, **een vinger slepen pant** (`android_compat_pan.jpg`, de grond volgt de vinger). Twee vingers kan adb niet; op de telefoon testen. Logcat: alleen de SSAO-waarschuwing onder Mobile (verwacht), geen scriptfouten.
- Pc ongewijzigd: alle 11 tests ALLES OK; `--scenario=overzicht`-frame tegen `out/voor_overzicht` (voor de mobiel-wijzigingen): 3D pixelgelijk, verschil alleen in de HUD (prijzen/geluk van een ander onderwerp).
- ✅ **Motorola (2026-10-30, draadloos adb, serial `adb-ZY22GD8FG4-…_adb-tls-connect._tcp`; `device-lock.ps1` kent alleen `ZY22GD8FG4` en ziet hem dan als ABSENT, dus claimen op de lange naam): Mobile/Vulkan geeft beeld** (Adreno, `vulkan.adreno.so`), mist werkt, briefing, HUD, minikaart, bumpkins, vuur, pad, vijver (`out/android/shots/moto_start.png`, `moto_spel.png`). Install 1,5 min (842 MB), start ~60 s. PSS 646 MB, graphics 150 MB. Geen scriptfouten in logcat. Nog: fps in het spel meten (gfxinfo telt het Godot-oppervlak niet goed), touch/twee vingers door de gebruiker, sneltoetsuitleg onderin is op mobiel zinloos.
- **Voor de Motorola** (vooraf): claimen (`device-lock.ps1 acquire -Serial ZY22GD8FG4`), `adb install -r out/android/beasts.apk` (arm64), kijken of Mobile/Vulkan daar wel beeld geeft (verwacht: ja, Adreno 619 met echte Vulkan; de emulator-fout is een present-probleem van de emulator), dan fps, RAM (`dumpsys meminfo`, 818 MB assets), twee-vinger-zoom/draai. Lukt Vulkan niet: Compatibility + mist/water-z-fix (`d*2-1`, zie Web hieronder). Geen app-icoon gezet (exportwaarschuwing).

## Wat het project nu gebruikt

- Renderer: **Forward+** (`project.godot`, `config/features` "Forward Plus"), MSAA 3D x2, directional shadow 4096, soft-shadow quality 3, SSAO quality 2.
- `view/licht.gd`: ACES tonemap, **SSAO aan**, **glow aan**, exponentiele fog (geen volumetrische), zon + maan met schaduw. Geen SDFGI, geen volumetrische mist.
- Lichten: OmniLight3D zonder schaduw (kampvuur in `props.gd`, nachtlicht per bumpkin in `bumpkin.gd`, `props.gd:298`). GPUParticles3D (vuur, rook, regen).
- Shaders (`shaders/`): twee lezen `hint_depth_texture`:
  - `mist.gdshader`: schermvullende quad, `texture(diepte, SCREEN_UV)`, `INV_PROJECTION_MATRIX`, `texelFetch` op R8-raster, `d <= 0` = lucht (omgekeerde z van Forward+/Mobile).
  - `water.gdshader`: `textureLod(depth_tex, ...)`, `ndc = vec3(uv*2-1, d)`, `depth_draw_always`.
  - `terrein`, `weg`, `natuur_wind`, `natuur_steen`, `minikaart`: gewone spatial/canvas, geen schermtextuur. `terrein` gebruikt NORMAL_MAP_DEPTH (gewoon).
- Threads: alleen `ResourceLoader.load_threaded_request` in `view/bouwmenu.gd:447`. Geen Thread/WorkerThreadPool in het project.
- Audio: 62 mp3, 62 ogg, 7 wav (3 MB). `view/geluid.gd:102` laadt mp3 met `AudioStreamMP3.load_from_file(ProjectSettings.globalize_path(...))`: **werkt niet op web/Android**, `res://` zit daar in de pck en globalize_path geeft geen echt pad. Moet `load()` worden (of ogg).
- Assets (`assets/`, niet in git): **745 MB**, waarvan 63 glb = 393 MB, 125 png = 226 MB, 241 jpg = 123 MB. `data/origineel/` = 1,6 MB originele kaarten (persoonlijk gebruik).
- Invoer: muis; touch via `emulate_mouse_from_touch` (standaard aan) in `bouwmenu.gd` en `minikaart.gd`. Geen multitouch (pinch, twee-vinger-pan), geen rechtermuisknop-draai voor de camera (`rts_camera.gd` gebruikt `window_is_focused` voor randpannen, op touch zinloos), sneltoetsen in het bouwmenu (`OS.get_keycode_string`) werken niet zonder toetsenbord.

## Wat er op deze pc staat

| onderdeel | stand |
| --- | --- |
| Godot 4.7.2 stable | ja, `...WinGet\Packages\GodotEngine.GodotEngine_...\Godot_v4.7.2-stable_win64.exe` (172 MB) |
| **Export templates 4.7.2** | ja, `%APPDATA%\Godot\export_templates\4.7.2.stable\` (2026-10-30) |
| `export_presets.cfg` | ja, Android-preset, zonder keystorepad of wachtwoord (gecommit) |
| JDK 17 | ja, `E:\werk\tools\jdk-17.0.20+8` (staat al in Godot editor_settings; `java` op PATH is nog de te oude 1.8) |
| Android SDK | **ja, op `D:\emulator`** (correctie 2026-10-30): build-tools 36.0.0, platforms 34/35/36, platform-tools, cmdline-tools, emulator + AVD `beasts_api34`. Alleen het SDK-pad in Godots editor_settings omzetten (wijst nu naar het niet-bestaande `%LOCALAPPDATA%\Android\Sdk`) |
| Debug keystore | ja, `%APPDATA%\Godot\keystores\debug.keystore` (buiten het repo, nooit committen) |
| Emulator | `beasts` is poort 5564 in `emulator.ps1` (`beasts_api34`); AVD op schijf niet gecontroleerd |
| Telefoon | Motorola `ZY22GD8FG4`, eerst claimen met `device-lock.ps1 acquire`, na afloop `release` (niet aangeraakt) |

Dus proefexport (web of apk) kan pas na toestemming voor de download.

## Web / PWA (Godot 4.7)

- **Alleen Compatibility (WebGL2)**. Forward+ en Mobile draaien niet in de browser (WebGPU-export bestaat niet als stabiele route, onbevestigd voor 4.7).
- Wat in Compatibility **niet** bestaat of anders is (onbevestigd, geen proef):
  - **SSAO, SDFGI, volumetrische fog, SSR, SSIL, DoF-kwaliteit**: weg. SSAO uit `licht.gd` valt stil weg, het beeld wordt vlakker. Glow werkt sinds 4.3, ACES-tonemap werkt. Exponentiele fog werkt.
  - **Dieptetextuur** (`hint_depth_texture`) werkt in Compatibility, maar met **niet-omgekeerde z**: 1.0 = ver weg, NDC-z = `d*2.0-1.0`. Concreet:
    - `mist.gdshader`: `if (d <= 0.0)` (lucht) wordt `d >= 1.0`, en `vec4(uv*2-1, d, 1)` wordt `vec4(uv*2-1, d*2.0-1.0, 1)`.
    - `water.gdshader:31`: `ndc = vec3(uv*2-1, d*2.0-1.0)`.
    - Beide shaders moeten per renderer verschillen (shader-`#ifdef` bestaat niet; oplossing: uniform `plat_z` die `main.gd` zet via `RenderingServer.get_current_rendering_method()`), anders is mist en waterdiepte fout.
  - Een transparante pass die de diepte leest en zelf `depth_draw_always` schrijft (water) werkt in Compatibility via een diepte-kopie; mist met `depth_test_disabled` ook. Risico: extra kopie per frame op mobiele GPU.
  - Lichten: Compatibility telt per mesh max 8 omni + 8 spot (instelbaar `max_lights_per_object`), schaduw voor omni/spot kan, maar bumpkin-nachtlichten staan al zonder schaduw. Veel bumpkins met elk een OmniLight3D (nacht) = trager dan in Forward+ (per object-rendering in plaats van geclusterd). Beperk tot de dichtstbijzijnde N.
  - Schaduwen: 4096 directional is te zwaar voor een telefoon; 2048 of 1024 en minder splits.
  - MSAA 3D werkt in WebGL2 maar kost op mobiel veel; liever uit of x2 laten schatten op echte telefoon.
  - GPUParticles3D werkt in Compatibility (vanaf 4.3 transform-feedback); controleren.
  - Texturen: browsers lezen S3TC niet overal; Godot importeert voor web ETC2/ASTC mee als `rendering/textures/vram_compression/import_etc2_astc=true` staat (nu waarschijnlijk niet; reimport van 350 MB textuur).
- **Threads**: sinds 4.3 exporteert Godot zonder threads (default), dan zijn geen COOP/COEP-headers nodig en werkt het ook op een gewone `tailscale serve`. `load_threaded_request` blijft werken maar draait op de hoofdthread; het laden van een glb kan dan een paar frames haperen. Mogelijke oplossing: glb's bij start voorladen achter een laadscherm. Met threads aan zijn `Cross-Origin-Opener-Policy: same-origin` en `Cross-Origin-Embedder-Policy: require-corp` nodig (python `http.server` met eigen handler), en iOS/Safari is daar kieskeurig. Aanbeveling: zonder threads.
- **PWA-optie** in de web-exportdialoog ("Progressive Web App": manifest, service worker, offline, icoon, orientation). Vereist **HTTPS** voor installeren op de telefoon: `tailscale serve --https=<poort>` (zoals voor de andere tools), **nooit `funnel`**, zolang er originele data in zit. Exclusiefilter in het preset: `data/origineel/*` weglaten (1,6 MB), controleer ook of er originele sprites/geluiden in `assets/` zitten voordat iets buiten het tailnet gaat.
- **Geheugen/laadtijd**: de pck zou ~745 MB zijn (glb's niet gecomprimeerd door Godot, textures wel VRAM-gecomprimeerd en dan kleiner, schatting 250-450 MB). Web wasm heeft 32-bit adresruimte (max 4 GB, in de praktijk crasht een tabblad op een telefoon rond 1-2 GB) en de hele pck gaat eerst door het netwerk (tailnet-snelheid) en dan in het RAM. Mobiele Safari/Chrome is dan de grens. Serieus risico; assets moeten fors kleiner (glb's decimeren, textures 1024 max, wereld streamen) voor web.
- Offline-cache van een PWA van 300+ MB: browsers (iOS vooral) gooien dat weg.

## Android APK

- Renderer: **Mobile** (Vulkan op de telefoon) is de beste match met het huidige project: omgekeerde z blijft, **mist- en waterdiepte werken zonder aanpassing**, geclusterde lichten, MSAA/schaduwen werken. Wat Mobile niet kent: **SDFGI** (niet gebruikt), **volumetrische fog** (niet gebruikt), SSAO beperkt (Mobile heeft SSAO sinds 4.x niet, onbevestigd: in 4.x staat SSAO alleen in Forward+; dan valt `licht.gd` SSAO stil weg). Glow en tonemap werken.
- De motorola edge 30 neo heeft Vulkan 1.1 (Adreno 619 / Snapdragon 695); fine voor Mobile, op deze gpu zijn 4096-schaduw en MSAA x2 zwaar, dus 2048 en test.
- Compatibility (OpenGL ES 3) kan ook op Android, maar dan gelden dezelfde z-aanpassingen als bij web; alleen nodig voor oudere telefoons.
- Threads zijn op Android gewoon beschikbaar: `load_threaded_request` werkt ongewijzigd.
- **Geluid**: `load_from_file(globalize_path(...))` moet `load()` worden, anders is er geen mp3.
- **Grootte**: APK < 4 GB, maar Google Play en installatie willen liever < 200 MB base; voor sideload (debug-APK of `adb install`) maakt het niet uit. 745 MB assets in een APK installeren op een telefoon kan wel, maar het schrijft 1x en pakt niet uit; laadtijd van pck ok. Textures: ETC2/ASTC-import aanzetten, anders valt het terug op niet-gecomprimeerd en is het geheugen veel hoger. Op een telefoon van 6-8 GB RAM is het eindige geheugen met 393 MB glb-geometrie en alle textures nog de vraag; meten.
- **Invoer**: touch = muis via emulate; alles wat rechtsklik of toetsenbord nodig heeft (camera draaien, sneltoetsen, randpannen) moet een touch-variant krijgen: twee-vinger-pan/pinch/draai in `rts_camera.gd`, bouwmenu-knoppen groter, minikaart (werkt al via muis-emulatie).
- Export: `export_presets.cfg` met Android-preset (package `nl.axelbons.beasts_remake` o.i.d., Mobile renderer, arm64-v8a, Gradle-build niet nodig), debug keystore is er al (pad staat in editor_settings), JDK 17 staat erin, Android SDK staat op `D:\emulator`.

## Vergelijking

| | PWA (web) | APK (Android) |
| --- | --- | --- |
| Renderer | Compatibility (WebGL2), versimpeld beeld, SSAO weg | Mobile (Vulkan), bijna gelijk aan pc |
| Shaders | mist + water z-conventie aanpassen (twee plekken) | niet nodig (bij Mobile) |
| Threaded laden | geen threads (of COOP/COEP), haperingen | werkt |
| Geluid | `load_from_file` vervangen | idem |
| Grootte/geheugen | 745 MB pck door het netwerk, tabblad-RAM-limiet: groot risico | sideload ok, meten op telefoon |
| Installeren | via tailscale https, geen store | `adb install`, geen store |
| Inspanning | groot (assets verkleinen, shaders, tests per browser) | klein-middel (templates, touch-camera) |
| Risico | hoog | laag |

## Aanbeveling

**APK met de Mobile-renderer** eerst: bijna geen codewijziging aan de shaders, threads en dieptebuffer werken als op pc; de rest is touchbediening (camera), `Geluid.load_from_file` en ETC2/ASTC-import. PWA pas daarna, en alleen als de assets omlaag gaan; het is meer werk en de limieten (geheugen, geen SSAO, z-conventie, geen threads) zijn harder. Een snelle web-proef kan de aanname "werkt het eigenlijk?" snel testen zodra de templates er zijn.

## Wat de gebruiker moet beslissen of leveren

1. Toestemming om de **export templates 4.7.2** te downloaden (~1 GB .tpz, in te pakken naar `%APPDATA%\Godot\export_templates\4.7.2.stable\`), anders geen proefexport.
2. ~~Android SDK installeren~~: niet nodig, staat op `D:\emulator`.
3. Keuze APK eerst of PWA eerst, en of de aanpassingen (touchcamera, Geluid, ETC2) erin mogen.
4. Bevestiging dat de telefoon geclaimd mag worden voor een installatie (`device-lock.ps1 acquire`, daarna `release`), of dat de emulator `beasts` (5564, AVD `beasts_api34` zo nodig kopieren van een sibling) volstaat. Op de emulator is Vulkan/softwarerender traag: voor prestaties is de echte telefoon nodig.
5. Publiek zetten blijft uitgesloten zolang `data/origineel/` en eventuele originele assets meekomen.
