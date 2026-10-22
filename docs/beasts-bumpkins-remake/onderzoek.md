# Onderzoeksrapporten (niet geverifieerd)
Ruwe uitkomsten van 4 onderzoeksagents, 21 oktober 2026. De factcheckstap is niet uitgevoerd. Rapporten in het Engels.

## Graphics en animatie

### Bevindingen
- **[high] Midjourney has no official public API, and its terms ban automated access. Leave it out of any agent pipeline.**  
  The Midjourney Terms of Service say users may not use automated tools to access, interact with, or generate Assets through the Services. The Community Guidelines say Midjourney does not provide an API, and that automating the service can get the account blocked. In July 2025 Midjourney said it was 'starting to investigate' an Enterprise API and opened an application form. Sources from mid-2026 (third-party, so less reliable) still report no public API as of August 2026. The 'Midjourney APIs' sold by APIFrame, PiAPI and others are unofficial wrappers and risk violating the ToS. At most a human can use Midjourney by hand for mood boards.  
  Bron: https://docs.midjourney.com/hc/en-us/articles/32083055291277-Terms-of-Service
- **[medium] Midjourney Community Guidelines: 'does not provide an API'. The Enterprise API is still only being explored.**  
  Community Guidelines: https://docs.midjourney.com/hc/en-us/articles/32013696484109-Community-Guidelines . Enterprise API announcement on X (16 July 2025): https://x.com/midjourney/status/1945563447309341140 . Survey page: https://updates.midjourney.com/enterprise-api-survey/ . I found no launch announcement up to 2026-10-21.  
  Bron: https://docs.midjourney.com/hc/en-us/articles/32013696484109-Community-Guidelines
- **[high] ComfyUI runs locally on Windows and has an HTTP/WebSocket API plus an official agent-oriented CLI, so an agent can drive it fully.**  
  Local server on 127.0.0.1:8188. POST /prompt queues a workflow JSON and returns a prompt_id. The /ws WebSocket reports progress, GET /history/{prompt_id} returns results, and /view serves output files. The official comfy-cli adds `comfy install`, `comfy launch --background`, `comfy node install <id>`, `comfy model download --url`, and `comfy --json run --workflow wf.json --wait`, with `comfy workflow set-slot` for changing inputs. There is also a local Comfy MCP server with run_workflow, fetch_outputs and validate_workflow tools. One caveat: Comfy's own design notes say the local routes exist to serve the web UI and are not a promised stable contract. Windows options: Desktop app (Windows 10+), Portable build (NVIDIA or CPU), or manual install. AMD on Windows and Intel Arc are also supported.  
  Bron: https://docs.comfy.org/development/comfyui-server/comms_routes
- **[high] comfy-cli 'comfy run' and the local Comfy MCP server are documented for agent use.**  
  From the docs: `comfy --json run --workflow my_workflow.json`, then `comfy jobs watch` or `comfy download`. `comfy validate` checks a workflow before submitting. The MCP route needs comfy-cli>=1.14.0. Related pages: https://docs.comfy.org/comfy-cli/getting-started and https://docs.comfy.org/agent-tools/local  
  Bron: https://docs.comfy.org/agent-tools/cli
- **[high] Model licences: FLUX.2 [klein] 4B and Qwen-Image are Apache 2.0. FLUX.2 [dev], FLUX.2 klein 9B and FLUX.1 [dev] are non-commercial or ambiguous, so avoid them for a product.**  
  The FLUX.2 repo lists klein 4B and klein 4B Base as Apache 2.0, with klein 4B fitting in about 8GB VRAM. klein 9B and FLUX.2 [dev] (32B) fall under the FLUX Non-Commercial License. Whether FLUX.1 [dev] outputs may be used commercially is disputed in the HF threads. Qwen-Image (20B MMDiT) is Apache 2.0 and natively supported in ComfyUI; I could not confirm the licence for Qwen-Image-Edit separately. SDXL uses CreativeML OpenRAIL++-M, which allows commercial use with use-based restrictions (secondary sources only). For a safe commercial base: FLUX.2 klein 4B (Base for LoRA training) or Qwen-Image.  
  Bron: https://github.com/black-forest-labs/flux2
- **[high] Qwen-Image is Apache 2.0 and supported in ComfyUI. Offloading via DiffSynth gets it running on low VRAM.**  
  The README states 'Qwen-Image is licensed under Apache 2.0'. Native ComfyUI support was announced on 2025-08-05. DiffSynth-Studio reports inference within 4GB VRAM using layer offloading, which is slow.  
  Bron: https://github.com/QwenLM/Qwen-Image
- **[high] Style LoRA training can be scripted on Windows. ostris ai-toolkit (MIT) runs from a YAML config, and kohya_ss (Apache 2.0) supports Windows.**  
  ai-toolkit command: `python run.py config/x.yml`. It ships run_windows.bat, needs an NVIDIA GPU, and lists FLUX.1, FLUX.2, Qwen-Image, SDXL and Wan 2.1/2.2. kohya_ss supports SD1.5/2.x, SDXL, SD3 and Flux.1 and has Windows installers. It is GUI-first, but the GUI generates sd-scripts CLI commands. BFL's official klein training docs give the floor for klein 4B base LoRA training as 12GB VRAM (RTX 3060 12GB) plus 32GB system RAM, with roughly 1-3 hours per LoRA. The kohya sd-scripts docs say SDXL LoRA works on 8GB, with 10GB recommended. Sources: https://github.com/bmaltais/kohya_ss, https://docs.bfl.ai/flux_2/flux2_klein_training, https://github.com/kohya-ss/sd-scripts/blob/main/docs/train_SDXL-en.md  
  Bron: https://github.com/ostris/ai-toolkit
- **[high] Blender headless rendering (blender -b file.blend -P script.py) can be fully scripted, and renders are the user's own property. This is the most consistent way to produce 8-direction isometric sprite sheets.**  
  From the manual: -b runs without the UI, -P runs a Python script, and -a / -f render the animation or a single frame. -f or -a must come last because arguments are processed in order, and --enable-autoexec is needed if the .blend relies on drivers. Blender's licence page says artwork you create (images, .blend files) is free to use as you like, because the GPL covers only the application. Add-ons that `import bpy` are GPL, which only matters if you distribute the add-on. Pipeline: an agent-written bpy script imports a GLB/FBX, sets an orthographic camera at an isometric/dimetric angle, rotates the model or camera in 8 steps of 45 degrees, renders each action's frames with a transparent background and a fixed toon/flat shader, and a Pillow script packs the frames into atlases. Because the same geometry and lighting are used for every frame, consistency between directions and frames is guaranteed. Pure 2D AI generation cannot guarantee that. CLI docs: https://docs.blender.org/manual/en/latest/advanced/command_line/render.html  
  Bron: https://docs.blender.org/manual/en/latest/advanced/command_line/arguments.html
- **[high] Blender output licence: the GPL does not apply to renders or .blend data.**  
  The licence page: 'all your artwork ... is free for you to use as you like'. Only Blender code embedded in a shipped executable is a GPL concern.  
  Bron: https://www.blender.org/about/license/
- **[medium] Tripo has an official REST API (v3) for image/text-to-3D, auto-rigging for many creature types including quadrupeds, and preset animation retargeting. This matters because B&B has cows, sheep and chickens.**  
  Base URL https://openapi.tripo3d.ai/v3 with a Bearer API key. Calls are async, with polling or a webhook. rig-check is free, auto-rig costs 25 credits, and each retarget animation costs 10 credits. Rig types: biped, quadruped, hexapod, octopod, avian, serpentine, aquatic, and others (others needs rig v3.0). There are 90+ biped presets, while quadruped has only preset:quadruped:walk. Pricing is $0.01 per credit, with a $1 minimum top-up. Text-to-3D costs 10-20 credits and image-to-3D 20-30 credits. Tripo's announcement says new API keys get 2,000 free credits. The parallel limit for rigging/animation is given as 3 on one page and 10 on another. Tripo also ships ComfyUI nodes. Commercial rights for API output are only claimed in a Tripo blog post; I did not find them in the ToS text. Related: https://developers.tripo3d.ai/en/pricing, https://developers.tripo3d.ai/en/docs/animations-rig, https://www.tripo3d.ai/blog/announcement-tripo-openapi-platform-payment-system  
  Bron: https://developers.tripo3d.ai/en/docs/animations-retarget
- **[medium] Meshy has an official API for text/image-to-3D, rigging and preset animations. Rigging works reliably only for humanoid bipeds, and API access requires a paid plan.**  
  Endpoints: POST /openapi/v1/rigging (input_task_id or model_url). GET /openapi/v1/animations/library is free. POST /openapi/v1/animations takes a rig_task_id and action_id. The API pricing page lists rigging at 5 credits and animation at 3 credits per action, up to 10 per request; the web-app pricing page shows 0, so the figures conflict. The docs say programmatic rigging 'currently only works well with standard bipedal assets', so animals would need another route. A Text-to-Motion API page exists in the docs (I saw only its title). Plans: Pro is $20/month with 1,000 credits and includes API access, the Free plan has no API, Premium is $40 and Ultra $100. Paid-plan outputs carry full commercial rights and ownership; Free-plan outputs are CC BY 4.0. Related: https://docs.meshy.ai/en/api/pricing, https://www.meshy.ai/pricing, https://help.meshy.ai/en/articles/9992001-can-i-use-meshy-assets-commercially-license-copyright-explained  
  Bron: https://docs.meshy.ai/en/api/rigging
- **[medium] Mixamo still works (free, royalty-free for games) but has no official API, so it cannot be cleanly automated. Treat it as a manual, human-in-the-loop step.**  
  Adobe's FAQ: characters and animations are royalty-free for personal, commercial and non-profit projects, including video games, and the service is free with an Adobe account. You may not redistribute the raw character or animation files, for example as asset packs. I found no Adobe developer API. A 2026 third-party guide says it still works in September 2026 but is in maintenance mode, had a multi-day outage in June 2025, and has no announced shutdown date. Driving the website with scripts is not an official interface, so avoid it under the ToS. Third-party status source: https://app.cinevva.com/guides/free-character-animations-rigging  
  Bron: https://helpx.adobe.com/creative-cloud/faq/mixamo-faq.html
- **[high] Hunyuan3D 2.1 (built into ComfyUI) may NOT be used in the EU, UK or South Korea. A user in the Netherlands is excluded by its licence.**  
  Tencent Hunyuan 3D 2.1 Community License, section 1.l: Territory is 'the worldwide territory, excluding the territory of the European Union, United Kingdom and South Korea'. Above 1M MAU a separate licence is required. VRAM is about 10GB for shape, 21GB for texture, and 29GB for both. Even though ComfyUI ships nodes for it, it is not a legal option for a Dutch user.  
  Bron: https://github.com/Tencent-Hunyuan/Hunyuan3D-2.1/blob/main/LICENSE
- **[high] The legal local image-to-3D alternative is Microsoft TRELLIS / TRELLIS.2 (MIT), but both are officially Linux-only and need 16GB (TRELLIS) or 24GB (TRELLIS.2) of VRAM on NVIDIA.**  
  TRELLIS: MIT (some submodules have other licences), needs at least 16GB, 'tested only on Linux', exports GLB. TRELLIS.2 (4B): MIT, nvdiffrast/nvdiffrec under NVIDIA licences, at least 24GB, Linux only, PBR GLB output. On Windows that means WSL2 or fragile forks, so the cloud APIs (Tripo/Meshy) are the more practical route on Windows. TRELLIS v1: https://github.com/microsoft/TRELLIS  
  Bron: https://github.com/microsoft/TRELLIS.2
- **[medium] UniRig (MIT) can auto-rig locally with 8GB VRAM, but setup is Unix-oriented and the public checkpoint is limited.**  
  Inputs: obj/fbx/glb/vrm. Output: FBX skeleton and skin, merged into GLB. Needs CUDA with at least 8GB. Only the Articulation-XL2.0 checkpoint is released. Missing bones such as tails or wings hurt the skinning, and Windows is not stated. A possible free fallback to Tripo rigging for animals, but expect manual fixes.  
  Bron: https://github.com/VAST-AI-Research/UniRig
- **[high] Wan 2.2 (Apache 2.0) can turn images into video for 2D animation, but frame-to-frame consistency is weaker than with 3D rendering, and it needs 24GB.**  
  TI2V-5B runs on at least 24GB (RTX 4090) with offload flags, while the A14B models need 80GB. Integrated in ComfyUI since July 2025, and the README does not mention Windows. Useful at most for VFX or idle loops. Video models do not give clean 8-direction sprite consistency.  
  Bron: https://github.com/Wan-Video/Wan2.2
- **[high] Real-ESRGAN ncnn-vulkan is a portable Windows CLI (BSD-3) that batch-upscales on Intel, AMD or NVIDIA through Vulkan, with no CUDA or PyTorch needed.**  
  `realesrgan-ncnn-vulkan.exe -i in_dir -o out_dir -n realesrgan-x4plus-anime -s 4 -f png`. Includes models such as realesrgan-x4plus-anime and realesr-animevideov3. Tiling can produce small block inconsistencies. Upscayl (AGPL-3.0) is a GUI on the same NCNN backend with a CLI ('upscayl-ncnn') and needs a Vulkan GPU, as most iGPUs do not work: https://github.com/upscayl/upscayl . chaiNNer (GPL-3.0) does batch work through Load Images. Its README mentions 'CLI usage' in the wiki, but I could not confirm a headless run of a saved chain: https://github.com/chaiNNer-org/chaiNNer . The licences of third-party models such as Remacri and UltraSharp are not stated on these pages.  
  Bron: https://github.com/xinntao/Real-ESRGAN
- **[medium] PixelLab has an official REST API, Python/JS SDKs and an MCP server for pixel-art characters in 8 directions plus animation. The resolution is small, at 128px or below for the rotate tool.**  
  The SDK (pip install pixellab) covers Pixflux and Bitforge generation, skeleton animation, text animation, inpainting and rotation. The v2 API lists endpoints including /v2/create-character-with-8-directions, /v2/generate-8-rotations-v3, /v2/animate-character and /v2/create-isometric-tile; exact paths conflict between pages, so check https://api.pixellab.ai/v2/docs. The Rotate tool's documented canvases are 16, 32, 64 and 128px, with an option for 'high top-down' view. The ToS allow commercial use, but the outputs may not be used to train other models. Subscription prices from third parties range from $9 to $50/month (not verified). It fits a pixel-art remake, but is less suited to 'upscaled' hi-res graphics. Related: https://www.pixellab.ai/termsofservice, https://www.pixellab.ai/docs/tools/rotate  
  Bron: https://github.com/pixellab-code/pixellab-python
- **[medium] Scenario has an official API that includes custom style, character and subject model training. API access starts at the Pro plan, and paid plans include a commercial licence.**  
  Generation via https://api.cloud.scenario.com/v1/generate/custom/{modelId} (async job polling) with Basic Auth (key and secret). Training can be automated through the API, at about 100-500 CU per training and 2-15 CU per image. `dryRun=true` returns the cost without charging. Plans: Starter $15 (1,500 CU), Pro $45 (5,000 CU), Max $75, with API access from Pro and CU shared with the web app. The Terms assign the user 'all right, title, and interest' in Generated Assets. Scenario says it has a commercial licence for Flux. It is a cloud alternative to local ComfyUI plus LoRA, for when there is no suitable GPU. Related: https://help.scenario.com/en/articles/api-usage-and-credits-creative-units/, https://www.scenario.com/terms-and-conditions  
  Bron: https://help.scenario.com/en/articles/generating-from-your-custom-trained-models-via-api
- **[medium] Ludo.ai has a REST API and an MCP server, but both are in beta, need Pro or Studio, and allow 1 concurrent request per endpoint.**  
  REST base https://api.ludo.ai/api/ and MCP at https://mcp.ludo.ai/mcp, with an ApiKey header (the header name differs between pages). The trial has no API, and generation calls cost credits. The Sprite Generator combines image and video animation into sprite sheets. Pro is about $50/month according to Ludo's own pages. I found no detailed endpoint reference for sprites.  
  Bron: https://ludo.ai/docs/api-mcp
- **[medium] GPU guidance: Comfy's own docs say 8-24GB is enough for images and 24GB+ is advised for video. Training and local 3D push the minimum to 12-16GB, and NVIDIA is effectively required.**  
  Comfy MCP page: below 8GB use the cloud, 8-24GB is fine for images, 24GB+ for most tasks including video. FLUX.2 klein 4B inference fits about 8GB, while klein 4B LoRA training has an official floor of 12GB plus 32GB RAM. SDXL LoRA runs on 8-10GB. TRELLIS needs 16GB, TRELLIS.2 24GB, and Wan 2.2 5B 24GB. ai-toolkit, TRELLIS and UniRig all require NVIDIA CUDA. ComfyUI itself also supports AMD and Intel. Blender rendering of low-poly sprites is light work for any modern GPU.  
  Bron: https://docs.comfy.org/agent-tools/mcp#local-comfy-mcp-connection
- **[low] IP caveat: Beasts and Bumpkins (1997) is Worldweaver/EA property. I could not establish the current rights holder.**  
  Using the original sprites as img2img/LoRA training data or upscaling them creates a derivative work of copyrighted assets. The name and characters may also be protected. This is a legal judgement for a human, not something the agent can resolve.  
  Bron: https://en.wikipedia.org/wiki/Beasts_and_Bumpkins

### Conclusie

Most automatable pipeline for consistent isometric sprites and animations, every step callable from PowerShell or Python:
(1) Style: ComfyUI run locally through comfy-cli (`comfy run --workflow ... --wait`) or the HTTP /prompt API, using commercially safe Apache 2.0 base models (FLUX.2 klein 4B, or Qwen-Image). A style LoRA is trained with ostris ai-toolkit from a YAML config (`python run.py config.yml`). This produces concept art and reference images for each unit, animal and building. Cloud alternative without a GPU: the Scenario API (Pro, $45/mo) with custom style training.
(2) 3D: reference image to GLB through the Tripo API (official v3 REST, about $0.20-0.30 per model, rigging for biped, quadruped and avian, preset retargeting). Meshy API (Pro, $20/mo) is a second option for humans; its rigging is reliable only for bipeds. Do not use Hunyuan3D 2.1: its licence excludes the EU. TRELLIS (MIT) is legal but officially Linux-only and needs 16-24GB.
(3) Animation: presets from Tripo or Meshy. Game-specific actions (milking, chopping wood, building) are keyframed by the agent through bpy scripts in Blender, or rigged and fixed with UniRig. Mixamo has no API, so it is only a manual, human step.
(4) Sprites: Blender headless (`blender -b scene.blend -P render_iso.py -- args`) with an orthographic isometric camera, 8 rotations of 45 degrees, a fixed toon shader and a transparent background. A Pillow script then packs the atlases. This 3D-to-2D route is the only way to guarantee consistency across directions and frames; pure 2D generators (PixelLab, Ludo, Midjourney) cannot.
(5) Finishing: Real-ESRGAN ncnn-vulkan CLI (BSD-3) for batch upscaling UI and 2D assets. An optional low-denoise ComfyUI style pass on frames risks flicker.
PixelLab is a good API-driven option only if the remake should look like pixel art (128px or smaller). Midjourney is excluded: it has no API and its ToS ban automation.
Minimum GPU: an NVIDIA RTX card with 12GB VRAM (e.g. RTX 3060 12GB) and 32GB system RAM, the official floor for FLUX.2 klein 4B LoRA training plus SDXL/klein inference, with 3D generation done in the cloud through Tripo or Meshy. Recommended is 16GB (4060 Ti / 5060 Ti 16GB). 24GB (3090/4090/5090) is needed only to run image-to-3D (TRELLIS) or video models (Wan 2.2) locally.

### Wat de mens moet doen
- Create accounts, generate API keys and pay: Tripo (top-up credits), Meshy (Pro $20/mo for API), Scenario (Pro $45/mo for API), PixelLab and Ludo (Pro/Studio) subscriptions, an Adobe account for Mixamo.
- Mixamo downloads, because it has no official API and scripted use of the website is not an official interface.
- Taste: choose the art direction, curate the 15-50 images in the LoRA training set, and approve style samples.
- Visual QA of each unit and building: silhouette readability at game zoom, correct facing per direction, animation timing, and fixing rigging errors (especially animals and tails).
- Legal: decide whether original Beasts and Bumpkins sprites or audio may be used as input or training data, and whether the name and characters may be used (the EA/Worldweaver rights holder is unknown).
- Check and accept licences: Tripo API ToS on commercial rights, Meshy API terms, and Hugging Face licence clicks for any gated models.
- Choose and buy the GPU (minimum 12GB NVIDIA).

### Open vragen
- Do Tripo's official ToS or API agreement confirm commercial rights for API output? So far that comes only from a Tripo blog post.
- Tripo rigging/animation concurrency: 3 or 10 parallel tasks? Their own pages conflict.
- Meshy animation pricing: 3 credits per action (API page) versus 0 (web-app page). Which applies to the API?
- What exactly do Meshy's Text-to-Motion API endpoint and its pricing look like? I saw only the page title.
- Does chaiNNer have a working headless CLI for running saved chains? The README points to the wiki, which I did not verify.
- Exact PixelLab API endpoint paths, maximum canvas size for v3 character creation, and current prices: the sources conflict and the official pages could not be fetched from this environment.
- Does Midjourney launch an Enterprise API between August and October 2026? I found no evidence, and the official pages could not be fetched directly here (DNS blocked), so the result rests on search snippets.
- Does Blender EEVEE run reliably headless in background mode on Windows? The manual shows it is possible in principle, but I did not test it on Windows.

## Audio

### Bevindingen
- **[high] ElevenLabs has an official Sound Effects API that an agent can drive end to end: POST /v1/sound-generation, model eleven_text_to_sound_v2, duration_seconds 0.5-30, a loop flag for seamless loops, and prompt_influence (default 0.3).**  
  The loop parameter only works on eleven_text_to_sound_v2 and makes the end blend into the start, which suits ambience such as wind, fields, a crowd hum or a forge. The docs list the cost as 40 credits per second when a duration is set. The general pricing page estimates about 200 credits per generation. An older API pricing page says $0.12 per minute. These figures conflict, so check the live pricing before budgeting. Official Python and JS SDKs exist, plus an official CLI (@elevenlabs/cli, installable on Windows with npm or Scoop) that takes the ELEVENLABS_API_KEY environment variable. The old local MCP server is archived; ElevenLabs points to a hosted MCP at api.elevenlabs.io/v1/mcp.  
  Bron: https://elevenlabs.io/docs/api-reference/text-to-sound-effects/convert
- **[medium] On a paid ElevenLabs plan, sound effects can be used commercially inside games. They may not be sold or licensed on their own or packaged as a sound library. The free plan is non-commercial and requires attribution.**  
  Exhibit 4 of the ElevenCreative Terms allows Sound Effects output in films, ads and games when combined with other material, and bars standalone resale or library packaging. Community Sharing must stay off, or ElevenLabs may offer your outputs to other users. The help center says all paid plans include a commercial licence except for Beta services, while the free plan cannot be used commercially and must credit elevenlabs.io. Not settled: whether loose WAV files in the game folder count as 'isolated files'. Packing them into a game archive lowers that risk.  
  Bron: https://elevenlabs.io/creative-terms
- **[high] The Eleven Music API is official and scriptable (POST /v1/music, music_length_ms 3,000-600,000, composition plans at /v1/music/plan, inpainting). Self-serve plans exclude 'Studio Games', though 'Indie Games' are allowed.**  
  The Music Terms define an Indie Game as a game that has made less than $500,000 since release, from a developer whose games earned less than $1,000,000 in its last financial year. Any other monetised public game is a Studio Game and needs Enterprise. If a game stops qualifying, you have 60 days to upgrade or stop using the music. The free tier requires attribution, and streaming rights start at Pro. The API page cites $0.15 per minute, which may be out of date. A commercial remake starts as an Indie Game, but someone has to keep checking its revenue.  
  Bron: https://elevenlabs.io/music-terms
- **[high] ElevenLabs Voice Design (POST /v1/text-to-voice/design) creates new synthetic voices from a text description, so villager voices need no cloning of a real person.**  
  The description must be 20-1000 characters. The call returns preview mp3s with generated_voice_id values, and you save one through text_to_voice.create. The models are eleven_multilingual_ttv_v2 and eleven_ttv_v3. The old create-previews endpoint was deprecated on 2026-05-13. TTS with eleven_v3 supports bracket audio tags such as [laughs], [sighs], [whispers] and [clears throat], which fits mumbles, grunts and gibberish lines. The current docs reportedly recommend Eleven v4, but I did not confirm that model ID.  
  Bron: https://elevenlabs.io/docs/api-reference/text-to-voice/design
- **[high] Voice cloning is restricted. ElevenLabs only allows a Professional Voice Clone of your own voice, after verification. Cloning any living person without explicit consent is prohibited, and celebrity voices are blocked.**  
  The PVC FAQ says you cannot clone someone else's voice even with their consent, and verification requires the owner to record lines live, which only a human can do. Instant clones require you to confirm you have consent. The Prohibited Use Policy bans cloning or impersonating anyone without explicit, informed consent and bans evading verification. In practice the original game's voice actors or audio must never be used as cloning input. Use designed voices, or the user's own voice with consent.  
  Bron: https://elevenlabs.io/use-policy
- **[medium] As of 2026-10-21, Suno has no public self-serve API. Access is partner-only, and the unofficial wrappers break Suno's terms.**  
  Music Business Worldwide reported in July 2026 that Suno is exploring a developer API, starting with a curated group of partners selected through an intake form. platform.suno.com shows only a sign-in page for API accounts, with no public docs, pricing or signup that I could find. The unofficial wrappers (for example gcui-art/suno-api) replay browser cookies, and Suno's Terms of Service prohibit 'data mining, robots, scraping'. Rights: free (Basic) songs are owned by Suno and non-commercial. Pro and Premier songs are owned by the user and commercially usable. Since 3 September 2026 downloads are capped at 7 lifetime trial downloads (no commercial use) for Free, 20 per month for Pro and 60 per month for Premier. Suno can therefore only be used by a human in the web UI, not by an agent.  
  Bron: https://www.musicbusinessworldwide.com/suno-explores-developer-api-seeking-apps-that-unlock-experiences-generative-music-makes-possible-for-the-first-time/
- **[high] Suno's commercial rights depend on the plan at the time each song is made, and upgrading does not retroactively cover songs made on the free plan.**  
  This comes from the help center articles on rights and ownership and on the free plan. Suno also warns that its output may not be eligible for copyright protection.  
  Bron: https://help.suno.com/en/articles/9601601
- **[high] Udio cannot be used: audio, video and stem downloads have been disabled since its partnership with Universal Music Group on 29 October 2025, and I found no official API.**  
  Udio's help center says downloads are disabled, and the platform is still under its transition Terms of Service. Third-party reviews say downloads were still off in September 2026.  
  Bron: https://help.udio.com/en/articles/12683565-changes-associated-with-the-universal-music-group-umg-partnership
- **[medium] Stable Audio 3.0 (released 2026-05-20) has open weights for Small-SFX, Small and Medium and was trained on licensed data. The 2.7B Large model is only available through the API or enterprise licensing.**  
  Per the official GitHub: Small-SFX has 433M parameters, runs on CPU only and is limited to 120 seconds. Medium has 1.4B parameters, makes up to about 380 seconds, needs CUDA plus Flash Attention 2, and peaked at roughly 5.1-6.5 GB VRAM (measured on an H200). The models generate 44.1 kHz stereo without vocals, which is fine for village and ambient music. An official tflite build runs natively on Windows x64 (Python 3.10-3.13, install.bat, sa3.bat). Flash-attn has no official Windows wheels, so Medium on Windows needs community wheels or WSL2. One community fork reports that a 12 GB card is tight when all three models are loaded.  
  Bron: https://github.com/Stability-AI/stable-audio-3
- **[high] Stability AI's Community License allows free commercial use of the outputs for individuals and organisations under $1M annual revenue, with registration. Above $1M an Enterprise licence is required.**  
  You own the outputs, to the extent the law allows. Commercial users must register with Stability, and the licence ends once you or your affiliates pass $1M in annual revenue. The Hugging Face repo for Stable Audio 3 Small-SFX is gated, so a human must accept the terms and create an HF token. It also bundles a T5Gemma encoder under the Gemma Terms of Use. The Stability Terms forbid removing AI watermarks or content credentials and forbid passing outputs off as human-made.  
  Bron: https://stability.ai/license
- **[low] The hosted Stability API sells audio generation for credits (1 credit = $0.01).**  
  The pricing page lists Stable Audio 2.5 at 8 credits per generation (up to 3 minutes). The listing for Stable Audio 3.0 shows 5 in one place and 8 in another. New accounts get 25 free credits. I could not confirm the price or endpoint path for the Large model.  
  Bron: https://platform.stability.ai/pricing
- **[high] Meta AudioCraft (MusicGen, AudioGen, MultiBand Diffusion) is not safe for commercial use: the code is MIT but the pretrained weights are CC-BY-NC 4.0.**  
  The weights are under the non-commercial licence in LICENSE_weights, so they are fine for prototyping and not for shipping. Coqui XTTS-v2 is also non-commercial (CPML), and Coqui shut down in January 2024, so no commercial licence can be bought.  
  Bron: https://github.com/facebookresearch/audiocraft/blob/main/model_cards/MUSICGEN_STYLE_MODEL_CARD.md
- **[medium] There are commercially usable local TTS options for villager voices: Kokoro-82M (Apache-2.0 weights) and Resemble AI Chatterbox (MIT, with a PerTh watermark in every output).**  
  Kokoro is small and CPU-friendly. Its phonemizer, espeak-ng, is GPLv3, so it should run as a build tool and not be shipped in the game. Chatterbox embeds an imperceptible watermark and supports zero-shot cloning, which is only acceptable with the voice owner's consent. Both work offline, so there is no per-call cost.  
  Bron: https://huggingface.co/hexgrad/Kokoro-82M
- **[low] ACE-Step 1.5 is a local open-weight music model (vocals included) that claims to run in under 4 GB VRAM, but its licence is unclear.**  
  Hugging Face lists the licence as MIT. One guide says the XL weights use a proprietary StepFun licence. Other sources give 12 GB VRAM. AMD documents ComfyUI support on Windows. Treat it as a candidate to verify, not a default.  
  Bron: https://huggingface.co/ACE-Step/Ace-Step1.5
- **[medium] Google Lyria 3 has an official API on Vertex AI and the Gemini API, with commercial use allowed during the preview, and outputs carry a SynthID watermark.**  
  The pricing table lists Lyria 3 Pro at $0.08 per full song (about 184 seconds), the 30-second Lyria 3 clip model at $0.04, and Lyria 2 at $0.06 per 30 seconds. The model docs say preview customers may use it for production or commercial purposes. Because it is a preview, the terms may change.  
  Bron: https://docs.cloud.google.com/vertex-ai/generative-ai/docs/models/lyria/lyria-3
- **[high] The agent can measure loudness and normalise it with ffmpeg alone: loudnorm in two passes (first pass print_format=json, second pass with the measured values and linear=true) plus ebur128 for integrated LUFS, LRA and true peak.**  
  loudnorm often resamples to 192 kHz, so add aresample=48000 afterwards. ebur128 and loudnorm can report slightly different values. On Windows, install ffmpeg with 'winget install -e --id Gyan.FFmpeg'. For game targets: Sony's ASWG-R001 guidance is about -23 or -24 LUFS integrated (sources disagree) with true peak at or below -1 dBTP, measured over gameplay. That is a whole-mix target, not a per-asset rule.  
  Bron: https://ffmpeg.org/ffmpeg-filters.html
- **[high] Clipping, silence and broken files can be detected automatically, and a spectrogram can be rendered to PNG for the agent to look at.**  
  From the ffmpeg filter docs: astats reports Peak_level, Peak_count, DC offset and Number_of_samples, so a peak near 0 dBFS plus a high Peak_count means clipping. silencedetect (n=-50dB:d=0.3) finds leading and trailing silence, and silenceremove trims it. showspectrumpic=s=1024x512 draws the whole file as one image that Claude can view with its image reader, which reveals empty output, band-limited audio, hum and noise. ffprobe gives duration, sample rate and channels. For loops, compare the RMS and sample values of the last and first few milliseconds and crossfade with acrossfade.  
  Bron: https://ffmpeg.org/ffmpeg-filters.html
- **[medium] Semantic and quality pre-screening can be automated with pyloudnorm (MIT), Meta audiobox-aesthetics (CC-BY 4.0) and LAION-CLAP (code CC0), so the agent can rank N candidates before a human listens.**  
  audiobox-aesthetics (CLI command audio-aes) scores clips without a reference on Production Quality, Production Complexity, Content Enjoyment and Content Usefulness. CLAP gives a text-to-audio similarity score against the prompt. A speech-to-text model can check whether voice lines are intelligible, or that gibberish contains no real words. These tools are only used for QA and are not shipped. The licence for the CLAP weights (CC0 or Apache) is not settled.  
  Bron: https://github.com/facebookresearch/audiobox-aesthetics
- **[high] On Steam, AI-generated audio shipped with the game counts as 'Pre-Generated' AI content and must be disclosed in the Content Survey.**  
  Valve reviews AI output like any other content: it must not be illegal or infringing and must match the marketing. Someone needs to keep a log of which tool and plan produced each asset.  
  Bron: https://partner.steamgames.com/doc/gettingstarted/contentsurvey

### Conclusie

The audio stack that is both the most automatable and safe for commercial use, as of 2026-10-21:

1) SFX. Use the ElevenLabs Sound Effects API (eleven_text_to_sound_v2, with loop=true for ambience) through the official Python SDK or CLI on a paid plan (Starter or higher), with Community Sharing turned off. For bulk or offline variations, use Stable Audio 3 Small-SFX locally; its official tflite build runs on CPU on Windows and is free under the Stability Community License below $1M revenue, after registering.

2) Music. The default is Stable Audio 3 Medium on a local NVIDIA GPU (about 8 GB VRAM or more recommended; it needs CUDA and Flash Attention 2, so WSL2 or community wheels on Windows), or the Large model through the Stability API. This gives no download cap, training on licensed data, and outputs the user owns. The alternative is the Eleven Music API while the game still meets the Indie Game test (under $500k game revenue and under $1M studio games revenue); above that it needs Enterprise. Google Lyria 3 is a third option, but it is still in preview. Do not use Suno in an agent pipeline: it has no public API, and scraping is forbidden. Suno can only be used by a human in the web UI on Pro or Premier, with monthly download caps. Udio is unusable because downloads are disabled. Do not use AudioCraft or MusicGen or XTTS for shipping, since their weights are non-commercial.

3) Villager voices and mumbles. Use ElevenLabs Voice Design for synthetic character voices, plus TTS (eleven_v3) with gibberish scripts and audio tags. Free local alternatives are Kokoro (Apache-2.0) and Chatterbox (MIT, watermarked), or procedural gibberish built from syllable clips with ffmpeg pitch and tempo filters. Never clone the original game's voices or any real person. The only acceptable clone is the user's own verified voice.

4) QA without ears. A fully automatic gate checks ffprobe metadata, astats for clipping and DC offset, silencedetect and silenceremove, loop seams, and spectrogram PNGs that Claude inspects visually. It then normalises with a two-pass loudnorm and ranks candidates with CLAP and audiobox-aesthetics. After that, only the top 2-3 candidates per asset go to a human in a listening sheet. The agent can generate, filter, normalise and catalogue everything, but it cannot judge taste, timbre consistency or fit with the game. The final listening must be done by a human.

Caveat: WebFetch failed with DNS errors throughout this run. All findings come from search-engine summaries of the official pages, not from full page reads, so the price figures in particular need a live check.

### Wat de mens moet doen
- Create the accounts and API keys for ElevenLabs, Stability AI and Hugging Face, and store the keys as environment variables on the Windows PC.
- Pay for and choose plan tiers: ElevenLabs Starter or higher for commercial SFX and voices, a Stability credit top-up for API use, and possibly ElevenLabs Enterprise later for music.
- Accept the gated Hugging Face licence for the Stable Audio 3 models and register with Stability for commercial use under the Community License.
- Keep tracking revenue against the thresholds: ElevenLabs Indie Game ($500k per game, $1M studio) and Stability Community License ($1M organisation revenue).
- Do all final listening and taste decisions: choose between candidates, check villager voice character, judge consistency with the 1997 feel, and balance the in-game mix.
- Approve the designed voice characters. If any voice is cloned, it must be the user's own voice with live verification recordings, which only a human can make.
- If Suno is used at all, a human must use the web UI by hand on Pro or Premier within the download caps. An agent cannot do this legally.
- Legal review of the remake's IP (Electronic Arts / Worldweaver rights to Beasts and Bumpkins). No original game audio may be used as model input. This sits outside the audio area but blocks shipping.
- Fill in the Steam Content Survey AI disclosure, supported by a per-asset provenance log that the agent can generate.

### Open vragen
- Does shipping individual ElevenLabs SFX files as loose WAV or OGG in the game folder count as distributing 'isolated files' under the ElevenCreative Terms, or does packing them into an archive avoid that? Ask ElevenLabs support.
- What are the current ElevenLabs API prices? Sources conflict: $0.12 per minute for SFX and $0.15 per minute for music on an older page, versus about 40 credits per second or 200 credits per generation in newer docs.
- What do Stable Audio 3 calls cost on the Stability API (5 or 8 credits), and what is the exact endpoint path for Large? Neither was confirmed.
- Does Stable Audio 3 Medium run natively on Windows without WSL2, given that flash-attn has no official Windows wheels? And what GPU and VRAM does the user's PC have?
- Would Suno grant partner API access (platform.suno.com) to a hobby or indie game, and on what terms?
- Is ACE-Step 1.5's licence MIT or a proprietary StepFun licence for some checkpoints? Verify before any use.
- Is the Eleven v4 TTS model ID confirmed as the current recommendation over eleven_v3? Only a secondary summary mentioned it.
- Is the remake meant to be commercial (Steam sale) or a free fan project? That changes which plans and licences are needed.
- WebFetch failed with DNS errors during this run, so the full texts of the terms pages (Music Terms, ElevenCreative Terms, Stability licence, Suno ToS) were not read directly. A human or a later agent run should re-read them before purchasing.

## Engine en Windows-toolchain

### Bevindingen
- **[high] Godot 4 installs via winget as GodotEngine.GodotEngine. The latest version in winget-pkgs is 4.7.2 (released 2026-08-18). It is a portable zip that registers two commands, `godot` and `godot_console`.**  
  The manifest is InstallerType zip with NestedInstallerType portable, for x86, x64 and arm64. It registers PortableCommandAlias `godot` (Godot_v4.7.2-stable_win64.exe) and `godot_console` (Godot_v4.7.2-stable_win64_console.exe). No elevation is declared, so it installs without UAC. Export templates are NOT included. The C# build is a separate package, GodotEngine.GodotEngine.Mono (4.7.2 present). Command: `winget install -e --id GodotEngine.GodotEngine --silent --accept-package-agreements --accept-source-agreements --disable-interactivity`.  
  Bron: https://github.com/microsoft/winget-pkgs/blob/master/manifests/g/GodotEngine/GodotEngine/4.7.2/GodotEngine.GodotEngine.installer.yaml
- **[high] The other winget IDs check out against the winget-pkgs manifests: BlenderFoundation.Blender (5.2.2), Python.Python.3.14 (3.14.7) or Python.PythonInstallManager (26.4), Git.Git (2.55.0), Gyan.FFmpeg (9.0.2) or Gyan.FFmpeg.Essentials (9.0.1), and OpenJS.NodeJS.LTS (24.20.0) or OpenJS.NodeJS (current 26.x).**  
  Blender: WiX MSI, Scope machine, ElevationRequirement elevatesSelf, no Commands entry (blender.exe is not put on PATH). Python.Python.3.14: burn installer, user scope uses `InstallAllUsers=0 PrependPath=1`. Git.Git: Inno installer, elevatesSelf, user and machine scope. Gyan.FFmpeg: portable zip exposing ffmpeg, ffprobe and ffplay. Its locale manifest says License GPL-3.0. OpenJS.NodeJS.LTS: MSI machine scope with elevatesSelf, plus a portable zip variant that exposes only `node`. Also available: GitHub.GitLFS (3.8.0 seen) and Anthropic.ClaudeCode. The Blender manifest folder also has an LTS/4 sub-package; I did not confirm its exact ID.  
  Bron: https://github.com/microsoft/winget-pkgs/tree/master/manifests
- **[high] The official Python 3.14 docs now recommend the Python Install Manager over the classic installer. Its documented unattended command is `winget install 9NQ7512CXL7T -e --accept-package-agreements --disable-interactivity`, then `py install --configure -y`.**  
  9NQ7512CXL7T is the Microsoft Store ID. The winget community source also has Python.PythonInstallManager, an MSIX that needs Windows 10 build 19044 or later. Its global aliases live in %LocalAppData%\Python\bin, and adding that to PATH is optional; the docs say to use `py` or venvs. Pitfall from the troubleshooting table: a legacy py launcher or older runtimes with PATH options can shadow it, so `python` and `py` may start different runtimes.  
  Bron: https://github.com/python/cpython/blob/3.14/Doc/using/windows.rst
- **[high] winget can run fully unattended with `-e --id <ID> --silent --accept-package-agreements --accept-source-agreements --disable-interactivity`. Batch installs work with `winget import -i packages.json` or `winget configure -f x.winget --accept-configuration-agreements`. `winget pin add` freezes a version.**  
  From the official winget docs: --silent suppresses installer UI, the two --accept-* flags suppress the EULA and source prompts, and --disable-interactivity disables prompts. A pin can be blocking (`--blocking`) or gating (`--version 4.7.*`). Pinning Godot matters because export templates must match the editor version exactly.  
  Bron: https://github.com/MicrosoftDocs/windows-dev-docs/blob/main/hub/package-manager/winget/install.md
- **[high] Pitfall: --silent does not bypass UAC. Packages marked elevatesSelf or machine scope (Blender MSI, Node LTS MSI, Git) raise a UAC prompt that an unelevated agent cannot answer. User-scope EXE installs may also still ask for UAC.**  
  The winget troubleshooting doc says EXE installer scope is not deterministic and that 'Packages installed in user scope may still require UAC authorization from an administrator'. Practical fix: a human starts ONE elevated PowerShell for the bootstrap script, or the agent prefers user scope or portable variants (`--scope user`, Node portable zip). Blender has only a machine-scope MSI in winget.  
  Bron: https://github.com/MicrosoftDocs/windows-dev-docs/blob/main/hub/package-manager/winget/troubleshooting.md
- **[high] Pitfall: PATH is not refreshed in already running processes. That includes Claude Code and every shell it spawns.**  
  Portable packages get symlinks in %LOCALAPPDATA%\Microsoft\WinGet\Links (machine scope: Program Files\WinGet\Links), and that folder is appended to PATH. PowerShell docs say the Process scope is built from the Machine and User scopes and inherited from the parent. So after an install the agent must re-read PATH in each command, for example `$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine')+';'+[Environment]::GetEnvironmentVariable('Path','User')`, or restart Claude Code. Call Blender by its full path under C:\Program Files\Blender Foundation\ (folder name may include the version).  
  Bron: https://github.com/microsoft/winget-cli/blob/master/doc/specs/%23182%20-%20Support%20for%20installation%20of%20portable%20standalone%20apps.md
- **[high] winget may not be available on a brand-new Windows user profile until App Installer has registered.**  
  WinGet needs Windows 10 1809 or later. It is registered asynchronously by the Store after the first login. The fix is `Add-AppxPackage -RegisterByFamilyName -MainPackage Microsoft.DesktopAppInstaller_8wekyb3d8bbwe`. Windows Sandbox does not include winget.  
  Bron: https://github.com/MicrosoftDocs/windows-dev-docs/blob/main/hub/package-manager/winget/index.md
- **[high] Pitfall: PowerShell execution policy. On Windows clients the effective policy is Restricted when nothing is set, which blocks .ps1 bootstrap scripts. Set it per user with `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`. Downloaded scripts also need `Unblock-File`.**  
  Restricted 'permits individual commands, but doesn't allow scripts', and also blocks profiles. RemoteSigned runs unsigned internet-downloaded scripts only after they are unblocked (Zone.Identifier). The same doc says 'Default' maps to RemoteSigned, so the agent should check `Get-ExecutionPolicy -List` rather than assume. Per-process alternative: `powershell -ExecutionPolicy Bypass -File x.ps1`.  
  Bron: https://github.com/MicrosoftDocs/PowerShell-Docs/blob/main/reference/7.5/Microsoft.PowerShell.Core/About/about_Execution_Policies.md
- **[high] Pitfall: long paths. MAX_PATH is 260 characters unless HKLM\SYSTEM\CurrentControlSet\Control\FileSystem LongPathsEnabled=1 is set (needs admin, may need a reboot) AND the app's manifest declares longPathAware. Git additionally needs `git config --global core.longpaths true`.**  
  Microsoft gives the PowerShell command `New-ItemProperty -Path 'HKLM:\SYSTEM\CurrentControlSet\Control\FileSystem' -Name 'LongPathsEnabled' -Value 1 -PropertyType DWORD -Force`. The value is cached per process. Git for Windows ships with long paths off, and its page explains core.longpaths; I confirmed that page through a search summary, not a direct read. Simple mitigation: keep the project at a short root such as C:\bb\.  
  Bron: https://github.com/MicrosoftDocs/win32/blob/docs/desktop-src/FileIO/maximum-file-path-limitation.md
- **[high] Claude Code runs natively on Windows 10 1809 or later. Install with `irm https://claude.ai/install.ps1 | iex` (no admin needed) or `winget install Anthropic.ClaudeCode`. Git for Windows supplies Git Bash for the Bash tool; without it Claude uses the PowerShell tool. Sandboxing is not supported on native Windows.**  
  Set CLAUDE_CODE_GIT_BASH_PATH if Git Bash isn't found. Needs a Pro, Max, Team, Enterprise or Console account, so login is a human step. The winget install does not auto-update. For unattended runs, permission modes are default, acceptEdits, plan, auto, dontAsk and bypassPermissions. The docs say bypassPermissions is for isolated containers and VMs only. dontAsk plus explicit allow rules suits scripted runs.  
  Bron: https://code.claude.com/docs/en/setup
- **[high] Godot 4 CLI covers what an unattended build needs. `--headless`, `--path <dir>`, `--import` (imports resources, then quits), `--export-release "<preset>" <path>`, `--export-debug`, `--export-pack` (.pck/.zip), `--export-patch`, `-s/--script` (SceneTree/MainLoop scripts), `--check-only` (parse errors only), `--quit`/`--quit-after N`, `--log-file`, `--fixed-fps`, `--time-scale`, `--disable-vsync`, `--resolution WxH`, `--rendering-method`, `--gpu-index`, `--print-fps`.**  
  Export rules: the binary must be an editor build and export templates must be installed. The preset name must match export_presets.cfg (quote names with spaces, e.g. "Windows Desktop"). The target directory must exist. Relative output paths resolve against the folder with project.godot, NOT the current directory. --headless is required without a GPU and otherwise just stops a window from opening. The flags are the same on the 4.7 docs branch.  
  Bron: https://github.com/godotengine/godot-docs/blob/4.7/tutorials/editor/command_line_tutorial.rst
- **[medium] Export templates can be installed without the editor UI. Download Godot_v4.7.2-stable_export_templates.tpz from the GitHub release and unzip its `templates/` folder into %APPDATA%\Godot\export_templates\4.7.2.stable\.**  
  The release asset URL https://github.com/godotengine/godot/releases/download/4.7.2-stable/Godot_v4.7.2-stable_export_templates.tpz resolves (HTTP 302 to the asset). Godot docs say the editor data path on Windows is %APPDATA%\Godot\ and that it 'contains export templates'. The `export_templates/<version>.stable` subfolder name comes from the widely used godot-ci Dockerfile, which uses the Linux path, so for Windows it is an inference. Alternative: self-contained mode (a `_sc_` file next to the editor exe keeps all data in ./editor_data/).  
  Bron: https://github.com/godotengine/godot-docs/blob/4.7/tutorials/io/data_paths.rst
- **[medium] On Windows the agent should call `godot_console` (the _console.exe wrapper), not the GUI exe, to get stdout/stderr and reliable exit codes. Exported games can ship their own console wrapper too.**  
  winget registers `godot_console` for this purpose. In the Windows export preset, `debug/export_console_wrapper` 'exports a console wrapper executable alongside the main executable, which allows running the project with enabled console output'. Code signing is optional and needs SignTool from the Windows SDK plus a certificate. Icon and metadata are set via application/modify_resources. PCK embedding is limited to about 3.89 GB.  
  Bron: https://github.com/godotengine/godot/blob/master/platform/windows/doc_classes/EditorExportPlatformWindows.xml
- **[high] GUT 9.7.1 is the release for Godot 4.7.x and runs from the CLI with an exit code (0 = all pass, 1 = any fail) and JUnit XML output.**  
  Command: `godot_console -d -s --path <proj> addons/gut/gut_cmdln.gd -gdir=res://test -gexit -gjunit_xml_file=res://reports/gut.xml`. A config file at res://.gutconfig.json is read by default. GutInputSender can send InputEvents to objects or to the Input singleton for input-driven tests. On a fresh checkout, run `godot --headless --path <proj> --import` first so the import and class caches exist; this is my recommendation, not a GUT doc quote.  
  Bron: https://github.com/bitwes/Gut/blob/main/documentation/docs/Command-Line.md
- **[high] gdUnit4 supports Godot 4.7 (v6.2.x and master v7.0.0) and has a Windows runner, addons/gdUnit4/runtest.cmd. By default it REFUSES headless mode because InputEvents are not delivered in headless, so UI and scene-input tests need a real (minimized) window.**  
  runtest.cmd takes `--godot_binary <exe>` or the GODOT_BIN env var. It runs `godot --path . -s -d --remote-debug tcp://127.0.0.1:0 res://addons/gdUnit4/bin/GdUnitCmdTool.gd`; the remote-debug setting avoids a hanging 'debug>' prompt. Options: -a <dir|suite>, -i <ignore>, -c (continue after failures), -conf, -rd <report dir> (default res://reports/), -rc, --ignoreHeadlessMode. It writes HTML and JUnit reports. The README lists a SceneRunner that simulates mouse, keyboard, touch and actions and can wait for signals.  
  Bron: https://github.com/godot-gdunit-labs/gdUnit4/blob/master/addons/gdUnit4/src/core/runners/GdUnitTestCIRunner.gd
- **[high] A running game can save its own screenshots for the agent: `await RenderingServer.frame_post_draw` and then `get_viewport().get_texture().get_image().save_png(path)`. DisplayServer.screen_get_image() also works on Windows.**  
  The Viewport docs warn the texture can be black or stale if read too early, hence the await on frame_post_draw. Agent-controlled triggers can be passed after `--` and read with OS.get_cmdline_user_args(), e.g. `godot_console --path . -- --shot-at=300 --shot-dir=C:/bb/shots`. The agent then reads the PNGs (Claude Code can view images). Expect nothing to be rendered under --headless (dummy display server), so capture runs need a window and GPU.  
  Bron: https://github.com/godotengine/godot/blob/master/doc/classes/Viewport.xml
- **[high] Movie Maker mode gives deterministic, non-real-time frame capture from the CLI: `godot --path <proj> --write-movie out.png --fixed-fps 30 --quit-after 600 --resolution 1280x720`.**  
  A .png target writes a lossless PNG sequence plus a matching .wav. A .avi target writes MJPEG plus uncompressed audio. OGV (Theora/Vorbis) works only in editor builds. Use --quit-after so AVI and WAV files are finalized properly. ffmpeg (Gyan.FFmpeg) can encode the sequence or extract contact sheets for review. Good for agent visual regression checks; listening to the WAV still needs a human.  
  Bron: https://github.com/godotengine/godot-docs/blob/4.7/tutorials/animation/creating_movies.rst
- **[high] Bot input and automated playtesting use built-in APIs. `Input.parse_input_event()` triggers _input calls. `Input.action_press()` sets action state only, with no _input. `Viewport.push_input()` replays recorded or synthetic events. Godot has NO built-in replay or bot framework, so one must be written.**  
  A practical pattern: keep the village simulation deterministic and separate from rendering. Drive it from a GDScript bot or autoload that injects InputEvents or calls game commands directly. Run with --fixed-fps plus --time-scale (and --disable-vsync) to accelerate. Assert on game state in GUT or gdUnit4 and dump periodic screenshots. Third-party MCP servers exist, e.g. Coding-Solo/godot-mcp (MIT), which can launch the editor, run projects and capture debug output, but its feature list does not include screenshots; treat these as optional and unofficial.  
  Bron: https://github.com/godotengine/godot/blob/master/doc/classes/Input.xml
- **[high] Isometric maps are first-class in Godot 4: TileSet tile_shape ISOMETRIC (diamond) with diamond layouts, painted on TileMapLayer nodes. The old TileMap node is deprecated.**  
  The TileSet docs say isometric 'works best if all sibling TileMapLayers and their parent inheriting from Node2D have Y-sort enabled'. The Y Sort Origin offset is set per layer and per tile. Rendering Quadrant Size does not apply to Y-sorted layers, since tiles are grouped by Y. TileMap now says 'Use multiple TileMapLayer nodes instead', and the editor can extract them. There is an official 2D isometric demo (Compatibility renderer) with depth sorting and occlusion.  
  Bron: https://github.com/godotengine/godot/blob/master/modules/tilemap/doc_classes/TileSet.xml
- **[medium] Performance with many animated units: Godot batches 2D draws. For tens of thousands of objects processed every frame, the docs recommend the low-level servers (RenderingServer canvas items) or MultiMesh instead of one node each.**  
  The docs name tens of thousands of instances processed every frame as a bottleneck and point to the Bullet Shower demo. MultiMesh is for thousands to millions of instances. A Beasts and Bumpkins-scale village (dozens to a few hundred bumpkins and animals) should be fine with normal AnimatedSprite2D/Node2D units sharing texture atlases. That figure is my estimate and should be benchmarked with --print-fps on the target PC.  
  Bron: https://github.com/godotengine/godot-docs/blob/4.7/tutorials/performance/using_servers.rst
- **[high] The engine's GPU needs are modest; heavy VRAM needs come only from local AI asset generation (another area). Godot's docs recommend the Compatibility renderer for 2D games. On Windows, Forward+ falls back from Vulkan to Direct3D 12, and Compatibility falls back from OpenGL 3.3 to ANGLE over Direct3D 11.**  
  Minimum: integrated GPU with Vulkan 1.0 (Forward+/Mobile) or OpenGL 3.3 (Compatibility). Recommended: dedicated GPU with Vulkan 1.2 and 8 GB RAM for the editor (4 GB minimum). Windows 10 minimum, Windows 11 recommended. The defaults are rendering_device/driver.windows=vulkan with fallback_to_d3d12=true, and gl_compatibility fallback_to_angle=true. GPU driver installs and updates go through vendor tools and may reboot, so plan them as a human step; I did not check whether vendor drivers can be installed via winget.  
  Bron: https://github.com/godotengine/godot-docs/blob/4.7/about/system_requirements.rst
- **[high] GDScript can be checked statically and formatted by the agent with `godot --headless --check-only -s <script>` and gdtoolkit 4.x (`pip install "gdtoolkit==4.*"`, which provides gdlint and gdformat).**  
  Combine these with the GUT or gdUnit4 exit codes for a fully scripted edit, lint, test and export loop in PowerShell.  
  Bron: https://github.com/Scony/godot-gdscript-toolkit/blob/master/README.md
- **[high] Licences: Godot is MIT, and its license text must be shown to players (e.g. in a credits screen). The Gyan FFmpeg 'full' build is GPL-3.0, which is fine as a dev tool but matters if ffmpeg is redistributed with the game.**  
  The Godot 'Complying with licenses' page says the license text must be made available to the user and suggests a credits screen. The engine itself places no restriction on the game. The rights to the original Beasts and Bumpkins name and assets are a separate legal question outside this area.  
  Bron: https://github.com/godotengine/godot-docs/blob/4.7/about/complying_with_licenses.rst

### Conclusie

For the engine and toolchain, nearly everything can run unattended from PowerShell once a short bootstrap is done.

**Steps the agent can run alone:**
- **Installs:** `winget install -e --id <ID> --silent --accept-package-agreements --accept-source-agreements --disable-interactivity`. Godot (GodotEngine.GodotEngine 4.7.2, portable, installs without UAC), FFmpeg (Gyan.FFmpeg) and Python (Python.PythonInstallManager or Python.Python.3.14 at user scope) fit this pattern.
- **Version freeze:** `winget pin add GodotEngine.GodotEngine --version 4.7.*`, so the export templates keep matching.
- **Export templates:** download the matching .tpz and unzip it into %APPDATA%\Godot\export_templates\4.7.2.stable. The folder name is inferred from Linux CI setups, so verify it once.
- **Project work:** write the project and export_presets.cfg as text, run `godot_console --headless --path . --import`, lint with `--check-only` and gdlint, test with GUT (`-gexit`, JUnit output) or gdUnit4 (runtest.cmd, HTML/JUnit), and build with `--export-release "Windows Desktop" C:/bb/build/game.exe` (the folder must exist).
- **Visual checks:** run the game in a real window, not headless. Use `--fixed-fps`/`--time-scale` and scripted bot input (`Input.parse_input_event`, GUT InputSender, gdUnit4 SceneRunner). Capture frames with in-game `save_png` after `frame_post_draw`, or with `--write-movie out.png --quit-after N`, then use ffmpeg for contact sheets the agent can look at.

**Engine fit:** isometric maps are built in (TileMapLayer with an isometric TileSet and Y-sort on all layers). A few hundred animated units is well within ordinary Node2D/AnimatedSprite2D use; servers or MultiMesh are only needed at thousands to tens of thousands.

**Known Windows pitfalls:**
1. **UAC:** Blender, Node LTS and Git (machine scope) install with elevatesSelf. --silent does not get past the UAC prompt, so a human must start one elevated PowerShell or approve the prompts. Prefer user-scope or portable variants where they exist.
2. **PATH:** a running Claude Code session and its child shells do not pick up PATH changes. Re-read Machine+User PATH in each command or restart Claude Code. Blender is never put on PATH; call it by full path.
3. **Execution policy:** use `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` and `Unblock-File` on downloaded scripts.
4. **Long paths:** set LongPathsEnabled in HKLM (admin, possibly a reboot), set `git config --global core.longpaths true`, and keep the project at a short root such as C:\bb.
5. **Console output:** use `godot_console` for stdout and exit codes. The GUI exe gives no usable console output.
6. **Headless limits:** --headless renders nothing and delivers no InputEvents. That is fine for import, export and pure-logic tests, but wrong for screenshots and input tests.
7. **Export paths:** relative export paths resolve against the project folder, not the current directory.
8. **GPU drivers:** Vulkan falls back to D3D12, and OpenGL falls back to ANGLE. Installing or updating drivers is a human step. Choosing the Compatibility renderer for this 2D game reduces driver risk.
9. **New Windows account:** winget may need registering first with `Add-AppxPackage -RegisterByFamilyName ...`.

On "ultracode or maximaal": this area is not the bottleneck. The toolchain is mature and scriptable, and the hard parts of the project lie in asset generation, art direction and audio judgement.

### Wat de mens moet doen
- Start one elevated PowerShell, or click the UAC prompts, for machine-scope installs: Blender MSI, Node.js LTS MSI, Git machine scope.
- Set LongPathsEnabled in HKLM (admin) and reboot if needed.
- Log in to Claude Code (Pro/Max/Team/Enterprise/Console account) and choose its permission mode. auto or dontAsk with allow rules are the sensible choices; bypassPermissions is meant for isolated VMs only.
- Install or update GPU drivers through vendor tools, which may reboot. I did not check whether vendor drivers can be installed via winget.
- On a brand-new Windows profile, log in once so App Installer/winget registers, or run the Add-AppxPackage registration command.
- Judge look and feel: review screenshots and Movie Maker captures for art direction, animation feel and isometric readability, and listen to all audio (the WAV output from Movie Maker).
- Decide on the Godot version (4.7.x pinned vs moving to 4.8 when stable) and GDScript vs C#. C# needs the .NET SDK, which I did not verify here.
- Optional: buy a code-signing certificate and use SignTool if signed Windows builds are wanted (avoids SmartScreen warnings).

### Open vragen
- The exact Windows export-template folder (%APPDATA%\Godot\export_templates\4.7.2.stable\templates layout) is inferred from the Linux CI Dockerfile and the data-paths doc, not from a Windows-specific doc. Verify it with one test export.
- Godot docs say --export-debug and --export-pack imply --import, but are silent for --export-release. Running an explicit --import first is the safe default.
- There are no official performance numbers for N AnimatedSprite2D units with Y-sorted isometric TileMapLayers. This needs a benchmark scene on the user's actual GPU using --print-fps.
- Does gdUnit4's runtest.cmd `if not exist` check accept the winget symlink path for GODOT_BIN? Untested; pointing at the real exe under %LOCALAPPDATA%\Microsoft\WinGet\Packages avoids the question.
- The exact winget ID of the Blender LTS sub-package (manifest folder LTS/4) is unconfirmed.
- Whether the Godot 4.7 Windows editor binary is longPathAware is unverified.
- Third-party Godot MCP servers (e.g. Coding-Solo/godot-mcp) are unofficial; their screenshot support and Godot 4.7 compatibility were not verified.

## Omvang van het originele spel

### Bevindingen
- **[high] Basic facts: a single-player isometric real-time strategy / village sim developed by Worldweaver and published by Electronic Arts for Windows in 1997, mainly in Europe (IMDb lists a UK release on 1 June 1997). The composer is James Hannigan.**  
  Sources disagree on the developer's name: Wikipedia says Worldweaver Ltd, GameFAQs says Worldweaver Productions. Wikipedia calls it a 'standard isometric god style game'. Note: WebFetch could not resolve wikipedia.org, mobygames.com or most other non-GitHub sites from this sandbox (DNS errors). Every non-GitHub claim in this report comes from search-engine extracts of those pages, not from reading the pages directly.  
  Bron: https://en.wikipedia.org/wiki/Beasts_and_Bumpkins
- **[medium] Story: you play Lord Mildew, an exiled member of the royal family. The final enemy is Dark Lord Sabellian, and the game ends with your coronation as King Mildew I. I could not confirm the name 'Lord of the Dead' in any source.**  
  After a few training missions the old King dies and leaves a power vacuum. The main enemy is the Dark Lord Sabellian. An exact-phrase search for 'Beasts and Bumpkins' plus 'Lord of the Dead' found nothing, so the brief's name is probably a paraphrase. The game does have plenty of undead (zombies, zombie tombs, vampires, a dark altar), which may be where the name comes from.  
  Bron: https://collectionchamber.blogspot.com/p/beasts-bumpkins.html
- **[high] The campaign has 30 missions.**  
  The reefbarman patch README says the developer-mode `loadmission` command takes mission numbers 1 to 30. Store and database text says 'over 30 missions' or '30 missions'. Each level has its own goal: collect an item (for example the Holy Grail, which needs a magic key and is booby-trapped), kill a given enemy or village, earn an amount of gold, or survive for a set time. Some levels start with a ready-made village and a fixed number of units and you must hold off waves of enemies. Missions are scripted with commands and conditions; BBTools ships a visual graph editor for these scripts.  
  Bron: https://github.com/reefbarman/beasts-and-bumpkins-patch
- **[medium] Villager life cycle: baby, then child (boy or girl), then working adult, then retired (old man or old woman), then death. An adult lives about 4 to 5 game years, depending on food and water.**  
  Population only grows naturally: a man and a woman go into a hut and a baby comes out, if the wolves don't get it first. Villagers only reproduce when there are enough houses and resources. Huts are where villagers sleep and reproduce. The decompiled action catalog also has 'Meet spouse for reproduction' and 'Attend wedding', and bride and groom are separate unit types, so there is a wedding step. Old people can catch plague and spread it through the village.  
  Bron: https://www.old-games.com/download/5096/beasts-bumpkins
- **[medium] Villager needs, according to the reverse-engineered catalogs: food, water, happiness and fitness, plus sleep at night. There is a day/night cycle and four seasons.**  
  In BBTools' activity_catalog.json, butchering a cow or chicken adds food, water and happiness. The priest's 'bless' restores food, water, happiness and fitness. Sleep is cleared when night ends. Fan sources say wheat is planted in spring and harvested in autumn, and winter snow changes the landscape and kills any remaining crops; the decompiled draw code also has a snow-fence sprite. A thought-cloud shows a villager's state (the RaZLeN patch fixes its position). No source mentions cold as a separate need.  
  Bron: https://raw.githubusercontent.com/JonMagon/BBTools/master/BBScriptEditor/resources/activity_catalog.json
- **[medium] Farming, livestock and division of labour: women do farm work (milking cows, cutting wheat for bread, picking apples for cider). Men build and repair, and only men can train at guilds. The livestock are cows and chickens, with pigs only in a farm animation.**  
  Cows are lured into fenced fields to be milked. They also have calf-birth, butcher and death animations. Chickens lay eggs that hatch into chicks, and villagers butcher them. The farm building has feeding, rooster, cowshed and pig animations (state_catalog.json). The production chains are wheat to bakery to bread, apples to brewery to cider, and milk. The automatic job picker handles wheat, apples and milking (action_catalog.json).  
  Bron: https://raw.githubusercontent.com/JonMagon/BBTools/master/BBScriptEditor/resources/state_catalog.json
- **[medium] Buildings: 21 player-built structures (each has its own construction-site class), plus about 8 to 10 that only appear in specific missions. That fits the roughly 20 buildings a Polish review counts.**  
  From BBTools' class_labels.json and objects_list.txt, the 21 player-built structures are: peasant hut, well, farm, bakery, brewery, town hall, church, builders guild, footmans guild, archers guild, knights guild, wizards guild, minstrels guild, stables, prison, lookout post, stone wall, fence, gate, bolt trap and trebuchet. The mission-only structures are: chapel, barrack, castle, tower, cabin, temple, teleport temple, dark altar, keep or tent, and campfire. Buildings unlock in a fixed order (Wikipedia gives the example that a farm needs a bakery first). Guilds cost gold per trainee, and one source says each guild caps how many units it can train (6 footmen per guild). Wikipedia also mentions a paladins guild, but no paladin class appears in the decompiled lists, so it may be the cavalier trained at the stables (low confidence). I found no evidence that buildings themselves can be upgraded; progress comes from unlock order and from training units.  
  Bron: https://raw.githubusercontent.com/JonMagon/BBTools/master/BBScriptEditor/resources/class_labels.json
- **[high] The decompiled unit list has 33 unit types: 11 villager kinds, 3 religious/magic users, 9 military units and 10 creatures or undead.**  
  From hover_names.json ('sex' field): male/female peasant, builder, taxman, old man, old woman, boy, girl, minstrel, bride, groom; priest, monk, wizard; guard (pikeman), footman, knight, flagman, cavalier, archer, crossbow, bombman, trebuchet; zombie, wolf, dark wolf, wasp, blood wasp, bat, vampire, demon (fiend), giant, ogre. The draw code also has a bush-man, a dwarf-like unit and a villager-eating bush. The animals are cow, calf, chicken and chick. There are 256 object class IDs in total (110 named in objects_list.txt); many are props, projectiles, effects or unused.  
  Bron: https://raw.githubusercontent.com/JonMagon/BBTools/master/BBScriptEditor/resources/hover_names.json
- **[medium] Magic and combat: wizards have 7 spells and priests have 7. There are traps, about 15 magic artefacts and several projectile types. Reviewers describe the combat as light: small skirmishes rather than big battles.**  
  Wizard spells: fireball, lightning, see, teleport, summon zombie, fear, detect traps. Priest spells: mass heal, quench fire, protect, fast food, cause plague, cure plague, bless. Spells are unlocked with scrolls. Traps: spike trap, land mine, flame trap, gas, bolt trap, oil slick. Artefacts: silver and gold goblets, holy sword, helmet of strength, ring of fire protection, shield of the gods, crucifix, magic key, shovel, cloak of invisibility, ring of absolute power, potions, fountain of youth. Priests also heal, preach, bury the dead and collect tithes. The prison is used to arrest villagers.  
  Bron: https://raw.githubusercontent.com/JonMagon/BBTools/master/BBScriptEditor/resources/state_catalog.json
- **[high] Original resolution and requirements: 640x480 (menus, briefings and FMV are fixed at 640x480), DirectDraw / DirectX 3, Windows 95, a Pentium, 16 MB RAM and 2 MB of video RAM.**  
  The 640x480 figure is confirmed by MobyGames, bb-patch, the RaZLeN patch and the reefbarman patch. Colour depth is unclear: one PC Gamer demo listing says '16-bit high colour SVGA, VBE 2.0' and another says '256c SVGA', so I could not settle it. The BBTools MAPViewer draws diamond tiles 78x40 px. PC Review at the time called the graphics 'outdated'.  
  Bron: https://www.mobygames.com/game/3804/beasts-bumpkins/specs/windows/
- **[medium] Sprites face 8 directions. Walk cycles are about 6 frames per direction, attacks 4 to 7, and some units 1 to 2. I counted roughly 220 distinct sprite-sheet names in the decompiled draw code.**  
  In BBTools' decompiled code, direction is calculated as `(gen_period + 16) / 32` with `& 7`, which gives 8 directions. The frame index is the frame number plus N times the direction, with N = 6 for almost every walk cycle (peasants, elders, kids, footman, knight, archer, wizard, zombie, giant, wasp, bat), 7 for cow walk, knight attack and ogre attack, 5 for throws and cavalier attack, 4 for wolf, catapult and archer shot, and 2 for crossbow. I found no mirroring in the BBTools viewer. Character sheets include still, walk, attack, flee and death/corpse variants, plus peasant work cycles: chop, saw, hammer, pick, harvest, milk, carry sack or barrel, throw, butcher chicken, shake, wedding. I only counted sheet names; I did not open or extract any assets.  
  Bron: https://github.com/JonMagon/BBTools/blob/master/additions/Objects__DrawObject.cpp
- **[medium] Music is 7 CD-audio tracks by James Hannigan. Most of the sound comes from what happens on screen, and the villager voices (West Country accents) are the game's signature.**  
  Music sits on CD tracks 2 to 8, and the game plays it through MCI cdaudio (RaZLeN and reefbarman READMEs). Credits found via search: sound designer Adele Kellett, audio producer Chris Nicholls, speech editing Bill Lusty (all EA), and Hannigan also did the FMV music. Reviews describe builders hammering, chickens laying, cows mooing and zombies moaning, comic villager barks (for example 'Fancy a bit of nookie?'), and stereotypical West Country accents. PC Review called the voice acting 'shamefully stereotypical'. No source gives a number of sound effects or voice lines; BBTools still lists 'sound files (ambient and speech)' as unfinished.  
  Bron: https://maybemattis.de/en/review_game-music/beasts-and-bumpkins/
- **[high] bb-patch does not reimplement anything. It is a GPLv3 Go/Fyne patcher for the original BEASTS.EXE.**  
  It fixes the registry entries the game needs, removes the CD check, fixes lag on new PCs, turns on the F11 developer console, and raises the resolution from 640x480 to 1280x720 (the README says some graphics glitch and some icons end up in the wrong place). It bundles DxWrapper and has only been tested against one EXE (MD5 2d2852fcb22e6f65a0cf3415abaf4411).  
  Bron: https://github.com/bb-patch/bb-patch/blob/main/README.md
- **[high] Other existing work: one new decompilation/reimplementation (OpenBumpkins), an active reverse-engineering toolkit (BBTools), two more modern patches, one abandoned remake, and the user's own spiritual successor. None is a remake with new assets.**  
  - MichelPaulissen/openbumpkins (GPLv3, created 16 Oct 2026): a decompilation and C/SDL2 reimplementation. It needs the original game files plus a one-time bundle generated from the user's own EXE. The README says it is playable to at least scenario 8, tested on Linux and macOS, AI-generated, and the code is deliberately left uncleaned. RUNNING.md mentions Windows builds but the README says there is none.
- JonMagon/BBTools (GPLv3, last push 19 Oct 2026): an IDA database, MAP/SAV format docs, a map viewer, a sprite viewer and a Qt6 mission-script editor. It is the best source of game-logic metadata.
- RaZLeN/beasts-and-bumpkins-patch (MIT, July 2026): cnc-ddraw upscaling, OGG music and engine fixes.
- reefbarman/beasts-and-bumpkins-patch (GPLv3, October 2026): up to 1920x1080, WASD scrolling, quicksave.
- Orangeyness/B-B-rebirth (C++/Allegro 5, 2010 to 2013): 'online B&B', on hold indefinitely.
- abons/beasts (the user's own): a Kotlin Android spiritual successor with all art drawn in code, 12 levels, 11 beasts, not released.  
  Bron: https://github.com/MichelPaulissen/openbumpkins

### Conclusie

Rough asset inventory for a full remake with new art and sound. These are estimates built from the reverse-engineered catalogs above; the original assets were not opened.

1. **Missions:** 30 campaign levels with scripted goals. The goal types are collect item, kill enemy or village, earn gold and survive. On top of that come the intro and briefing FMVs; their number is unknown.

2. **Buildings:** about 21 player-built types plus 8 to 10 mission-only ones, so about 30. Each needs:
   - a finished sprite or model,
   - a construction-site or stage view,
   - a damaged or burning state,
   - 0 to 4 animated overlays (doors, smoke, farm animals, bakery and brewery animations).
   That comes to roughly 120 to 180 building images or animations, plus snow-season variants if seasons are kept.

3. **Characters:** 33 unit types plus 4 farm animals and a few extras (bush-man, dwarf, villager-eating bush), about 40 rigs. Animation sets:

   | Group | Animation sets |
   |---|---|
   | Male peasant | about 15 (work cycles, carrying, wedding, fleeing, death) |
   | Female peasant | about 13 |
   | Other human types | 3 to 5 each |
   | Military units | about 4 each |
   | Creatures | 3 to 4 each |
   | **Total** | **about 170 to 200** |

   At 8 directions and 4 to 7 frames, that is about 6,000 to 9,000 sprite frames. Rendering 3D models to 8 directions makes the directions nearly free to produce, so the real cost is the 40 models and roughly 180 animation clips.

4. **Props and effects:** roughly 80 to 120 items:
   - trees, rocks and shrubs (about 15)
   - fences, walls, gates and a bridge
   - wheat and apple growth stages
   - graves and coffins
   - about 15 artefacts and about 6 traps
   - about 12 projectiles
   - 14 spell effects
   - rain and thunder clouds, fire, smoke and explosions

5. **Terrain:** 8 terrain types (grass, light grass, water, mud, rock, sand, forest, green forest) on 2:1 isometric tiles, with transitions and probably a winter set.

6. **Interface:**
   - about 33 unit portraits
   - about 21 build icons and 14 spell icons
   - about 15 artefact icons
   - about 8 command cursors
   - thought-cloud need icons
   - menus and briefing screens

7. **Audio:**
   - 7 music tracks.
   - Sound effects and voices are unconfirmed; estimate 300 to 500 clips. That is about 20 human unit types with 8 to 15 voiced barks each (selected, acknowledge, attack, death, wedding, needs), plus about 100 to 150 sounds for animals, creatures, work, buildings, spells, combat and ambience.

**Simulation systems to rebuild:**
- life cycle and ageing
- marriage and reproduction tied to housing
- food, water, happiness and fitness needs, plus sleep
- day/night and four seasons
- gendered jobs and automatic job picking
- production chains: wheat to bread, apples to cider, milk
- plague
- taxes and tithes for gold
- guild training with caps
- 14 spells, traps and artefacts
- creature and undead AI
- a mission scripting engine

**What this means for the effort question:** this is large, multi-month work. It needs maximum effort and should be split into phases (engine and simulation, content pipeline, then 30 missions), not run as a single pass.

**Can an agent do it on its own?**
- Code, data tables and batch rendering of sprites can be largely automated.
- Art direction, voice and comedic tone, and audio review cannot; a person has to judge them.
- OpenBumpkins and BBTools can serve as a behaviour reference (studying mechanics). Their asset paths depend on the user's own copy of the game, and the remake must not ship or derive from those assets.

### Wat de mens moet doen
- Legal and IP decision: the name 'Beasts and Bumpkins', the characters (Lord Mildew, Sabellian) and the original assets belong to the rights holders (probably EA). A person has to decide whether to use a new name, story and characters (a spiritual successor) and must not ship original sprites, voices, music or FMV. Abandonware status is not a licence.
- Art direction: one person has to set the look (cartoon, painted, pre-rendered 3D) and approve character designs for about 40 rigs and about 30 buildings.
- Voice and humour: someone has to listen to and approve the voice barks (the West Country comedy is the game's signature). Whether the voices are synthetic or recorded is a taste call and possibly a consent or licensing question for real actors.
- Music: someone has to listen to and approve about 7 or more new tracks, and decide whether to commission a composer or use generated or licensed music.
- Game balance across 30 missions (economy pacing, combat difficulty) needs human playtesting for fun, beyond the automated 'can be completed' bot checks.
- If the original game is used as a behaviour reference, the user needs a legitimately owned copy. Whether one can still be bought is unconfirmed.

### Open vragen
- Is 'Lord of the Dead' an actual in-game name? Every source names the antagonist Dark Lord Sabellian.
- Is there a paladin unit or paladins guild? Wikipedia mentions one, but the decompiled lists only have knight and cavalier (stables).
- Original colour depth: 8-bit 256 colours or 16-bit high colour? The two PC Gamer demo listings conflict.
- Exact number of sound effects and voice lines, and of FMV cutscenes. No public source counts them, and BBTools has not documented the sound files yet.
- Whether some of the 8 directions are mirrored in the original sprites. That affects the frame count but not a 3D-render pipeline.
- Do any buildings have real upgrade tiers? I found no evidence, only unlock order and guild training.
- Most non-GitHub pages (Wikipedia, MobyGames, review sites) could not be fetched directly because of sandbox DNS errors. Claims from them rest on search-engine extracts and should be spot-checked in a browser.
- Is the game currently sold anywhere (GOG or EA)? This is unconfirmed, and it matters for how a user could legally get a reference copy.
