#!/usr/bin/env python3
"""Android-build met VRAM-gecomprimeerde texturen, zonder het pc-project te veranderen.

Godot kent geen importinstelling per platform. Daarom spiegelt dit script het project naar een
eigen map buiten spel/ (standaard ../lokaal/android_project, gitignored), zet daar in elke
textuur-.import uit assets/ compress/mode=2 (VRAM Compressed: ETC2 op Android; normal maps als
RG), laat de spiegel zijn eigen .godot-cache houden (volgende keer alleen gewijzigde bestanden) en
exporteert de APK. De .import-bestanden van spel/ zelf blijven onaangeroerd, dus de pc blijft lossless.

    python tools/android_build.py                 # spiegelen + importeren + export-debug
    python tools/android_build.py --alleen-spiegel
    python tools/android_build.py --apk out/android/beasts.apk --spiegel D:/elders

Uitzondering: terrein_*.jpg blijft lossless (terrein_view.gd leest die via get_image() in een
Texture2DArray; decomprimeren van ETC2 op de CPU kost meer dan het oplevert).
"""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import time

SPEL = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STANDAARD_SPIEGEL = os.path.normpath(os.path.join(SPEL, "..", "lokaal", "android_project"))
GODOT = os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Packages",
                     "GodotEngine.GodotEngine_Microsoft.Winget.Source_8wekyb3d8bbwe",
                     "Godot_v4.7.2-stable_win64_console.exe")

# niet meespiegelen (bovenste niveau van spel/)
OVERSLAAN = {".godot", "out", "screenshots", "test", "tools", ".claude-index", ".git"}
STAAT = ".android_build_staat.json"   # in de spiegel: hash van wat wij laatst schreven
NORMAAL = re.compile(r"(normaal|_nor_gl|_nor_dx|_normal|_nrm)", re.I)
LOSSLESS = re.compile(r"^assets/terrein_")


def zet(tekst, sleutel, waarde):
    pat = re.compile(r"^" + re.escape(sleutel) + r"=.*$", re.M)
    if pat.search(tekst):
        return pat.sub(lambda m: f"{sleutel}={waarde}", tekst)
    return tekst.replace("[params]\n", f"[params]\n\n{sleutel}={waarde}\n", 1)


def omzetten(rel, data):
    """Geeft de spiegelversie van een bestand terug, of None als het ongewijzigd mee kan."""
    if rel == "project.godot":
        t = data.decode("utf-8")
        # de spiegel bouwt alleen voor Android: geen S3TC/BPTC importeren (halveert de importtijd)
        t = t.replace("textures/vram_compression/import_etc2_astc=true",
                      "textures/vram_compression/import_etc2_astc=true\n"
                      "textures/vram_compression/import_s3tc_bptc=false")
        return t.encode("utf-8")
    if rel.startswith("assets/") and rel.endswith(".import") and not LOSSLESS.match(rel):
        t = data.decode("utf-8")
        if 'importer="texture"' not in t:
            return None
        t = zet(t, "compress/mode", "2")
        t = zet(t, "mipmaps/generate", "true")
        t = zet(t, "compress/normal_map", "1" if NORMAAL.search(rel) else "2")
        return t.encode("utf-8")
    return None


def bronbestanden():
    for wortel, mappen, bestanden in os.walk(SPEL):
        rel_w = os.path.relpath(wortel, SPEL).replace("\\", "/")
        if rel_w == ".":
            mappen[:] = [m for m in mappen if m not in OVERSLAAN]
            bestanden = [b for b in bestanden if b not in OVERSLAAN]
            rel_w = ""
        for b in bestanden:
            yield (rel_w + "/" + b) if rel_w else b


def spiegel(doel):
    os.makedirs(doel, exist_ok=True)
    staat_pad = os.path.join(doel, STAAT)
    try:
        with open(staat_pad, encoding="utf-8") as f:
            staat = json.load(f)
    except (OSError, ValueError):
        staat = {}
    nieuw_staat, gezien = {}, set()
    gekopieerd = omgezet = 0
    for rel in bronbestanden():
        gezien.add(rel)
        bron = os.path.join(SPEL, rel)
        dst = os.path.join(doel, rel)
        if rel.endswith(".import") or rel == "project.godot":
            with open(bron, "rb") as f:
                data = f.read()
            uit = omzetten(rel, data)
            if uit is not None:
                h = hashlib.md5(uit).hexdigest()
                nieuw_staat[rel] = h
                # Godot herschrijft de .import na het importeren; alleen opnieuw schrijven als
                # onze versie veranderde, anders volgt bij elke run een volledige herimport.
                if staat.get(rel) != h or not os.path.exists(dst):
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    with open(dst, "wb") as f:
                        f.write(uit)
                    omgezet += 1
                continue
            # Godot zet de mtime van .import-bestanden na het importeren: op inhoud vergelijken
            try:
                with open(dst, "rb") as f:
                    if f.read() == data:
                        continue
            except OSError:
                pass
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            with open(dst, "wb") as f:
                f.write(data)
            gekopieerd += 1
            continue
        st = os.stat(bron)
        try:
            dt = os.stat(dst)
            gelijk = dt.st_size == st.st_size and int(dt.st_mtime) == int(st.st_mtime)
        except OSError:
            gelijk = False
        if not gelijk:
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(bron, dst)
            gekopieerd += 1
    # wat in spel/ verdween, ook uit de spiegel
    weg = 0
    for wortel, mappen, bestanden in os.walk(doel):
        rel_w = os.path.relpath(wortel, doel).replace("\\", "/")
        if rel_w == ".":
            mappen[:] = [m for m in mappen if m not in OVERSLAAN]
            rel_w = ""
        for b in bestanden:
            rel = (rel_w + "/" + b) if rel_w else b
            if rel == STAAT or rel in gezien:
                continue
            os.remove(os.path.join(wortel, b))
            weg += 1
    with open(staat_pad, "w", encoding="utf-8") as f:
        json.dump(nieuw_staat, f, indent=0, sort_keys=True)
    print(f"[android_build] spiegel {doel}: {gekopieerd} gekopieerd, {omgezet} omgezet, {weg} weg")


def draai(args, log):
    print("[android_build]", " ".join(args[1:]))
    t0 = time.time()
    with open(log, "w", encoding="utf-8", errors="replace") as f:
        r = subprocess.run(args, stdout=f, stderr=subprocess.STDOUT)
    print(f"[android_build]   {time.time() - t0:.0f} s, exit {r.returncode}, log {log}")
    return r.returncode


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--spiegel", default=STANDAARD_SPIEGEL)
    p.add_argument("--apk", default=os.path.join(SPEL, "out", "android", "beasts.apk"))
    p.add_argument("--godot", default=GODOT)
    p.add_argument("--alleen-spiegel", action="store_true")
    a = p.parse_args()
    doel = os.path.abspath(a.spiegel)
    if os.path.commonpath([doel, SPEL]) == SPEL:
        sys.exit("spiegel mag niet in spel/ liggen (Godot zou hem meescannen)")
    spiegel(doel)
    if a.alleen_spiegel:
        return
    apk = os.path.abspath(a.apk)
    os.makedirs(os.path.dirname(apk), exist_ok=True)
    logs = os.path.dirname(apk)
    if draai([a.godot, "--headless", "--path", doel, "--import"], os.path.join(logs, "vram_import.log")):
        sys.exit("import mislukt")
    if draai([a.godot, "--headless", "--path", doel, "--export-debug", "Android", apk],
             os.path.join(logs, "vram_export.log")):
        sys.exit("export mislukt")
    print(f"[android_build] {apk}: {os.path.getsize(apk) / 1e6:.0f} MB")


if __name__ == "__main__":
    main()
