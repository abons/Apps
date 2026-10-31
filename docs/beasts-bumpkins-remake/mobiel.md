# Beasts & Bumpkins-remake op mobiel: PWA of APK?

Onderzoek 2026-10-30, daarna dezelfde dag de APK-proef (zie "Stand APK"). Waar Godot-gedrag uit kennis komt en niet uit een proef, staat "(onbevestigd)".

## Stand APK (2026-10-30, emulator `beasts`)

- Gedaan: export templates 4.7.2, editor_settings (SDK `D:/emulator`, JDK 17), `export_presets.cfg` (Android, arm64-v8a + x86_64, debug-keystore uit editor_settings, geen pad of wachtwoord in het bestand), `project.godot`: `rendering_method.mobile="mobile"`, schaduw `.mobile` 2048, `import_etc2_astc=true`. Touch in `rts_camera.gd` (1 vinger pannen, 2 vingers pan/knijp-zoom/draai, randpannen uit op mobiel) en `view/bestuur.gd` (gesleepte vinger = geen kader/klik). Geluid laadde al via `load()` (geïmporteerd).
- Export: `"$G" --headless --path . --export-debug "Android" out/android/beasts.apk`, ~1 min, **818 MB** APK. Install op de emulator 25 s, start ~45 s tot het eiland.
- **Mobile/Vulkan op de emulator: zwart beeld, 3 pogingen.** (1) SwiftShader: "no Vulkan surface". (2) `-gpu host -memory 4096`: Vulkan 1.3 op de RTX 2060, sim start (`[spel] missie 1 ...`), maar `Couldn't present to Vulkan queue (VkResult error 5)`, screencap en emulator-screenshot zwart. Met de standaard 1536 MB RAM bleef System UI hangen (ANR). (3) Compatibility-rooktest (`command_line/extra_args="--rendering-method gl_compatibility --rendering-driver opengl3"` tijdelijk in het preset, niet gecommit; `am start --esa command_line_params` werkt niet): **HUD en briefing goed, 3D zwart** door de mist (`android_compat_mist_zwart.jpg`), met `-- --mist=uit` erbij **het hele spel** (`android_compat_start.jpg`): terrein, bomen, bumpkins, vlag, vuur, minikaart, schaduw.
- Touch op de emulator (adb `input`): tik sluit briefing en hint, tik op bouwknop zet bouwmodus aan, **een vinger slepen pant** (`android_compat_pan.jpg`, de grond volgt de vinger). Twee vingers kan adb niet; op de telefoon testen. Logcat: alleen de SSAO-waarschuwing onder Mobile (verwacht), geen scriptfouten.
- Pc ongewijzigd: alle 11 tests ALLES OK; `--scenario=overzicht`-frame tegen `out/voor_overzicht` (voor de mobiel-wijzigingen): 3D pixelgelijk, verschil alleen in de HUD (prijzen/geluk van een ander onderwerp).
- ✅ **Motorola (2026-10-30, draadloos adb, serial `adb-ZY22GD8FG4-…_adb-tls-connect._tcp`; `device-lock.ps1` kent alleen `ZY22GD8FG4` en ziet hem dan als ABSENT, dus claimen op de lange naam): Mobile/Vulkan geeft beeld** (Adreno, `vulkan.adreno.so`), mist werkt, briefing, HUD, minikaart, bumpkins, vuur, pad, vijver (`out/android/shots/moto_start.png`, `moto_spel.png`). Install 1,5 min (842 MB), start ~60 s. PSS 646 MB, graphics 150 MB. Geen scriptfouten in logcat. Nog: fps in het spel meten (gfxinfo telt het Godot-oppervlak niet goed), touch/twee vingers door de gebruiker, sneltoetsuitleg onderin is op mobiel zinloos.
- **Touch na de Motorola-proef (2026-10-30, gebruiker):** twee-vingerdraai stond andersom, nu draait de kaart met de vingers mee (`rts_camera.gd`, teken omgedraaid; pan en knijpen waren goed). Bouwen op touch plaatste bij loslaten en kon niet draaien: nu ghost slepen + **Bouwen**/Draai/Annuleer onderin (`Bouwmenu.touch`, zie `spel/README.md` Besturing), sneltoetsuitleg weg op touch. Pc ongewijzigd; 11 tests + `test/touch_bouw_test.gd` (12e) ALLES OK. Nog op de telefoon: draairichting, ghost slepen, knopmaat/plek, rij leggen.
- **Staand en liggend (2026-10-30)**: `orientation=6` (sensor), indeling bij elke `size_changed` (`view/scherm.gd`, zie `spel/README.md` "Staand en liggend"); touch-HUD zonder tekstregels, icoon + getal op >= 16 dp (gebruiker: tekst te klein). Pc-proef `-- --venster=1080x2400`, frames `test/portret_frames.sh` naar `out/portret/`, test `test/indeling_test.gd`. Nog op de telefoon: draaien tijdens het spel, lade Gebouwen, leesbaarheid, beeldhoek staand.
- ✅ **Gecomprimeerde APK op de Motorola (2026-10-31, via usb; wifi-adb valt steeds weg bij 700 MB, usb-push 52 MB/s):** start tot `main _ready klaar` **5,3 s** (was 9,0), vram **483 MB** (was 1196), fps **11,8** (was 10,8), gpu 83 ms, 577k prims, 533 calls, portret, afstand 8. Live los getest (elk apart t.o.v. basis 11,8): schaal 0,5 **20,6**; schaduw uit 13,8; zacht 0 12,8; lucht uit 12,8; mist uit 12,6; fog uit 12,3; terrein uit 12,3; ssao/decoratie/bomen/water ~0. Samen ssao+schaduw+lucht+fog uit 17,1; schaal 0,5 + schaduw uit **24,4**; alles uit 46,5. Conclusie: pixelgebonden, geen enkele dader; 30 fps vraagt schaal ~0,5 plus schaduw uit (of een lichtere materiaal-/belichtingsroute). `git bash`: `MSYS_NO_PATHCONV=1` bij adb-paden.
- **Prestaties Motorola (2026-10-30, `view/prestatie.gd`, alleen mobiel of `-- --prestatie`):** fps-regel linksboven (fps, frame-ms, gpu-ms, script-ms, draw calls, schaal), elke s `[prestatie]` in logcat (tag `godot`), `[start]`-merken per opbouwfase. Instellingen live te proberen zonder export: `user://prestatie.cfg` sectie `[beeld]` (sleutels in `Prestatie.STANDAARD`), `adb exec-in run-as nl.abons.beasts_remake sh -c 'cat > files/prestatie.cfg' < x.cfg`, wordt elke 2 s herlezen.
  - Begin: **7,5 fps** (133 ms) op elke instelling, ook schaduw uit of MSAA uit. Oorzaak: **terreinshader** (5 lagen x 4 samples, 13 ruis): op 50% schaal kaal 85 ms, zonder terrein 25 ms. Nu `shaders/terrein_mobiel.gdshader` (alleen kleur, 5 samples, 2 ruis), pc houdt `terrein.gdshader`; op de pc te zien met `-- --mobiel_beeld`.
  - Met mobiele terreinshader, stapsgewijs: basis 7,5 → schaal 0,75 10,1 → MSAA uit 12,7 → 2 splits 13,1 (prims 1127k → 640k) → glow uit **13,5 fps**. Daarna los (vanaf 13,5): bomen uit 14,6, decoratie uit 14,8, mist uit 14,0, water uit 13,5; terrein uit 10,3 (water vult dan het beeld). Geen enkele post weegt nog zwaar: alles samen ~72 ms gpu op 0,75.
  - Zwaar vermoeden voor de rest: **alle 385 texturen in `assets/` zijn Lossless (`compress/mode=0`, `vram_texture=false`)**, want `detect_3d` slaat alleen aan in de editor, en die is nooit geopend. Dus ongecomprimeerd RGBA8 in VRAM (Godot meldt 1,1-1,2 GB) en CPU-decodering bij elke start. Naar VRAM Compressed (mode 2) zou start en fps flink helpen, maar het pc-beeld verandert dan iets (BC-artefacten): **beslissing gebruiker**.
  - Mobiele standaard (in `Prestatie.STANDAARD`): schaal 0,75, MSAA uit, 2 splits, glow uit. Niet gemeten na de laatste build (telefoon op slot): sky-radiance (`lucht=false`, `lucht_proces=3`), schaal 0,5, `zacht=0`, in- en uitgezoomd.
  - **Start** (ms sinds engine-start tot `main _ready klaar`): 25,7 s → **21,3 s** met `view/voorladen.gd` (27 glb's tegelijk via `load_threaded_request`, alleen mobiel). Engine + main.tscn 2,6 s, terrein-mesh 1,5 s, het wachten op de glb's 14,7 s, dorpelingen 1,1 s. Op de pc 12,0 → 7,1 s (alleen met `-- --voorladen`). Daarna gebouwd, op de telefoon nog niet gemeten: laadscherm met de briefing (binnen ~3 s in beeld) en `worker_pool/low_priority_thread_ratio.mobile=0.9`.
  - ✅ **Texturen VRAM-gecomprimeerd, alleen op Android (2026-10-31, besluit gebruiker: pc blijft lossless).** Build: `python tools/android_build.py` (vanuit `spel/`): spiegelt het project naar `../lokaal/android_project` (gitignored, buiten `spel/` zodat Godot hem niet meescant), zet daar in 370 textuur-`.import`s `compress/mode=2` (normal maps `normal_map=1`, RG), `terrein_*` blijft lossless (`get_image()` in `terrein_view.gd`), en exporteert naar `out/android/beasts.apk`. Eigen `.godot` in de spiegel: eerste keer import 71 s + export 55 s, daarna alleen wat veranderde. De `.import`s van `spel/` blijven onaangeroerd. **APK 852 → 704 MB.** Pc-proxy (spiegel op de pc = S3TC, `-- --voorladen --prestatie`): vram 1164 → ~510 MB, start (warm) 7,2 → 5,6 s. Telefoon vóór (oude build, warme start): `main _ready klaar` 9,0 s, 10,8 fps (briefing open), vram 1196 MB, PSS 774 MB. **Telefoon ná: nog te meten** (telefoon viel van wifi-adb, emulator start niet: D: vol); fps aflezen in de overlay linksboven. `adb install` van een nieuwe build over wifi brak af: `adb push` naar `/data/local/tmp` + `adb shell pm install -r` werkt stapsgewijs.
  - Godot-export zette de adb-daemon uit (de wifi-telefoon viel dan weg): `export/android/shutdown_adb_on_exit = false` in `editor_settings-4.7.tres`.
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
