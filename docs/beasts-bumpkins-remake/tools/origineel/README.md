# Lezers voor de originele spelbestanden

Kopieën van de scripts waarmee de originele data is uitgelezen (stand 2026-10-29). Alleen code: de originele
bestanden en alles wat eruit komt (sprites, kaarten, audio) blijven lokaal en gaan nooit in git.

| script | doet |
| --- | --- |
| `box.py`, `mapread.py` | `.BOX`-archieven en kaarten (port van BBTools `MAPFile.cs`) |
| `mfb.py`, `sheets.py` | MFB-sprites naar PNG, alle frames als strook |
| `mis.py`, `export.py`, `gen_md.py`, `summ.py`, `tl.py` | missies M1-M30 decoderen, JSON + layout, `missies.md` |
| `maak_lijst_v1.py` + `maak_lijst_html.py` | conceptinventaris: `concept/lijst.md` + lokale beoordelingspagina |

⚠️ De paden staan hard op de scratchpad van sessie 16e99493 en op `\axel-laptop\Users\axelb\beasts\`; pas ze aan voor
een nieuwe run. Bron van de originele bestanden: zie de geheugennotitie `bb-original-assets`.
