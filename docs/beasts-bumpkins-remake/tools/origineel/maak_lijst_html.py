# ---- markdown (hoort bij het html-deel: maak_lijst.py = head -n 187 v1 + dit bestand)
def mdtable(rows, n0):
    o = ["| Nr | Naam | Origineel | Sprites (U/ B/ A/ T/ = Unity-project, `bb_original/` = lokale uitpak) | Portret | Richt./staten | Prio | Batch | Opmerking |", "| --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    n = n0
    for x in rows:
        sp = ", ".join("`%s`" % s.replace("Units/", "U/").replace("Buildings/", "B/").replace("Animals/", "A/").replace("Terrain/", "T/") for s in x["spr"]) or "geen"
        pt = "`scratchpad/bumpkin/ref/avatar_man.png`" if x["port"] == AV else ("`%s`" % x["port"] if x["port"] != N else "geen")
        o.append("| %d | %s | %s | %s | %s | %s | %s | %s | %s |" % (n, x["naam"], x["orig"], sp, pt, x["rs"], x["prio"], x["batch"], x["opm"]))
        n += 1
    return "\n".join(o), n

out = []
out.append("""# Conceptart-inventaris Beasts & Bumpkins-remake

Doel: per model eerst Gemini-conceptart, door de gebruiker beoordeeld, pas daarna modelleren. Dit is alleen de lijst (geen beelden, alleen paden en tekst). Stand 2026-10-29.

Bronnen: `../onderzoek.md` (aantallen, gilden, 33 units uit BBTools-catalogi), de **originele game-uitpak** (`bb_original/`, 625 PNG's uit de MFB-bestanden) en het Unity-project (`Unity_bumpkins/Bumpkins/Assets/Resources/Sprites/` en `Sprites-HD/`, exact 2x).

⚠️ **`bb_original/<naam>.png` is een lokale map (scratchpad), niet in git**: persoonlijk gebruik, nooit committen. Per sprite staat ook een sheet met alle frames in `bb_original/sheets/<naam>.png` (zie hieronder); de MFB's en `mfb.py` staan in `bb_original/mfb/`.

## Wat de bronnen wel en niet hebben
- **De 625 uitgepakte PNG's zijn alleen het eerste frame** van elke MFB (`mfb.py` bewaart `entries[0]`). Alle frames zijn wel te exporteren: `bb_original/mfb/sheets.py` zet ze in een horizontale sheet per sprite (`bb_original/sheets/`, 603 stuks, `_info.txt` = frames en afmeting). Lopen/aanval is **8 richtingen x 6 frames** (48 totaal), een gewone plaat is 1 richting; spiegelen gaat in code.
- Het origineel heeft **sprites voor vrijwel alles**: alle gilde-eenheden, vampier, demon, struikman, reus, ogre, bijna alle gebouwen, vallen, artefacten en spreukpictogrammen. Het Unity-project had maar ~10 figuren en 9 gebouwen. Pad-afkortingen: U/ = `Units/`, B/ = `Buildings/`, A/ = `Animals/`, T/ = `Terrain/` (Unity), `bb_original/` = origineel.
- Naamregels: `d_*` = doodsprite, `mn_*` = minikaart-pictogram, `ni_*` = nacht-overlay (verlichte ramen), `*over`/`*door` = dak- of deur-overlay, `l_*` = licht-overlay, `m_*`/`f_*` = man/vrouw-acties, `v*` = variant met een dorpeling.
- **Portretten bestaan wel**: `statbust` bevat 18 portretten van 102x102 (uitgesneden naar `bb_original/portret/bustNN.png`). Toewijzing is op het oog; zie open vragen.

## Hergebruik
- Elk eenheidsconcept is een **keerplaat** (voor, zij, achter). Hergebruik van de man betekent: zijn plaat als stijlreferentie meegeven, niet de plaat overslaan; een keerplaat per gilde blijft nodig.
- Mens-eenheden delen basislichaam (man 26 px hoog in het origineel = 1,37 m, kind 0,81x, oudere 0,96x) met eigen outfit en gereedschap.
- Samen op een plaat (telt als 1 beeld): kippen-sheet, dorpsprops, bomen, rots+heuvel, hek/muur/poort, wesp+bloedwesp, wolf+donkere wolf, bruidspaar, missiegebouwen per drie, vallen, artefacten.
""")
n = 1
for g, rows in G:
    out.append("## %s — %d rijen\n" % (g, len(rows)))
    if g.startswith("Klaar"):
        t, _ = mdtable(rows, 0); t = "\n".join(l if i < 2 else l.replace("| 0 |", "| - |", 1).replace("| 1 |", "| - |", 1) for i, l in enumerate(t.split("\n")))
        out.append(t + "\n")
    else:
        t, n = mdtable(rows, n); out.append(t + "\n")
nbb = sum(1 for g, rows in G if not g.startswith("Klaar") for x in rows if any(s.startswith("bb_original/") for s in x["spr"]))
out.append("## Tellingen\n- Rijen (onderwerpen): " + ", ".join("%s %d" % (g.split('. ', 1)[-1].split(' (')[0], len(rows)) for g, rows in G if not g.startswith('Klaar')) + " = **%d** rijen, plus 2 klaar. Alle %d hebben nu minstens een sprite; %d hebben een sprite uit het origineel (`bb_original/`), de rest alleen uit het Unity-project (batch 1 is bewust ongewijzigd gelaten).\n" % (nrows, gespr, nbb))
out.append("- Nieuw ten opzichte van de vorige stand: Beul + hakblok, Nar / jongleur, Herberg (pub), Graanschuur, Appelboom + appelpluk, Zombiegraf, Spookboom + wortelaltaar, Straatlamp en toorts, Meubilair. Vervallen: Dwerg (`dw_*` is een zwarte wolf). Kruisboogschutter is nu Kruisboog (wielgeschut); Struikman staat apart (geen dwerg erbij).\n")
out.append("## Batches (ongeveer 14 beelden per dag, prio 1 eerst)\n\n| Batch | Beelden | Inhoud |\n| --- | --- | --- |")
for b in sorted(tel):
    namen = []
    for g, rows in G:
        for x in rows:
            if x["batch"] == b: namen.append(x["naam"].split(" (")[0])
    out.append("| %d | %d | %s |" % (b, tel[b], "; ".join(namen)))
out.append("\nTotaal **%d beelden in %d batches**. Batch 1 is het speelbare dorp (vrouw, kinderen, ouderen, bouwer, koe, kippen, eerste vijanden, vier gebouwen) en is ongewijzigd; batch 2 de eerste gilden en basisgebouwen.\n" % (sum(tel.values()), len(tel)))
out.append("""## Beantwoord uit de sprites
- **Paladijn**: bestaat niet. Geen sprite, niet in `objects_list.txt`; de zwaarst bepantserde eenheid is de ridder (`kn_*`) en te paard de cavalerist (`cavalier`, ruiter en paard in een model).
- **`vsaw` / `vpick`**: dezelfde animatie als `saw` / `pick`, maar met een dorpeling (bruin haar, grijs hemd, paarse broek) in plaats van de bouwer (blauw, gele muts). `v` = villager. Het laatste frame van `saw`/`pick` is de afgewerkte tegel.
- **Reus**: 36 px hoog tegen 26 px voor de man, dus ~1,35x (ca. 1,9 m). Niet 1,5 tot 2x.
- **Ogre**: 47 px incl. hoge staf met bol (~1,8x); zonder staf ~35 px, ca. 1,35x. Dik en breed (37 px), groen, met rond houtschild.
- **Dwerg**: bestaat niet; `dw_still`/`dw_walk`/`dw_attak` zijn een **zwarte wolf** (35x30). Dat is de "donkere wolf" van de wolf-plaat. **Struikman** (`bushman`) is een dennenboom met ogen.
- **Kruisboogschutter**: `crossbow` is een kruisboog op wielen (belegeringswapen), geen schutter; `catapult` is de trebuchet. Bommenwerper (`bombman`) is een klein zwart figuur.
- **Wachter/piekenier**: wel, `pk_still`/`pikewalk`/`pikeatta`; vlagdrager (`flagwalk`, `fg_still`) ook.
- **Demon**: `fiend` is een gevleugelde duivel van 88x71 px, 64 frames; **vampier** heeft stil, vleermuisvorm en doodsprite.
- **Bruid en bruidegom**: `d_bride`, `d_groom`, `f_weddin`, `m_weddin`: bestaan wel.
- **Portretten**: er zijn er 18 in `statbust`. Gok-toewijzing: 1 minstreel, 2 jongen (rood haar), 3 bouwer (kaal, blauw), 4 voetsoldaat, 5 vlagdrager, 6 cavalerist (knots), 7 meisje, 8 nar, 9 ridder, 10 boogschutter, 11 tovenaar, 12 man (avatar), 13 vrouw, 14 wachter (bijl), 15 priester, 16 belastinginner, 0 en 17 oudere vrouwen. Voor batch 1 (vrouw, jongen, meisje, bouwer) zijn er dus portretten.
""")
out.append("""## Open vragen
1. **Gildegebouwen**: voetsoldaten (`fguild`) en boogschutters (`fletcher`) zijn zeker (deur-sprites `footdoor`, `archdoor`). Tovenaars waarschijnlijk `treehous`. Ridders (`barrack` of `keep`), minstrels (`pub`?) en bouwers (alleen deur `workover`) onzeker; `uguild` is een menu-pictogram. Controle in een screenshot van het origineel.
2. **Stadhuis**: welke sprite? `th_nodo` (strodak met klok) of `th_over` (steen met bruin dak, lijkt op `granover`). `mn_tax` (belastingkantoor) is geel strodak.
3. Is de gereedschapsloods (`Toolshed`, nachtversie `ni_tools`) het bouwersgilde-gebouw, of is dat `mn_work`?
4. `Dairy` heet in de code melkerij; research noemt "farm" met koestal; origineel `farm`. Welke naam?
5. Kuiken heeft geen sprite (ei `chickegg` wel); `bushk_fl/ml/pr/rp` zijn vier kleine figuurtjes (vrouw, man, priester, bouwer; 4 frames) van onbekend gebruik, waarschijnlijk liggend/schuilend; `soldier` is een paarse gebogen figuur (48 frames) van onbekend gebruik.
6. Portret-toewijzing (hierboven) klopt op het oog; controleren in het spel (`mn_*`/portretvenster).
7. Spreukeffecten: slechts 9 `s_*`-sprites tegen 14 spreuken (7 + 7); de rest is zelf te ontwerpen.
""")
open(MD, "w", encoding="utf-8", newline="\n").write("\n".join(out))


# ---- html: per ronde beoordelen (lokaal, niet in git)
import re
from struct import unpack
os.makedirs(SC + "concept/img", exist_ok=True)

def slug(s):
    s = s.lower().split(" (")[0]
    return re.sub(r"[^a-z0-9]+", "_", s).strip("_")

INFO = {}
try:
    for l in open(SC + "bb_original/sheets/_info.txt"):
        p = l.split(); INFO[p[0]] = int(p[1].split("=")[1])
except Exception:
    pass

def sprite_cells(x):
    cells = ""
    for s in x["spr"]:
        p, _ = hd(s)
        d = open(p, "rb").read(32); w, h = unpack(">II", d[16:24])
        nm = os.path.basename(s)[:-4]
        if s.startswith("bb_original/"):
            k = INFO.get(nm, 1)
            sc = 2 if w * 2 <= 1000 else 1   # volledige sheet, alle frames
            cells += '<div class="t sh"><img src="%s" width="%d" height="%d"><br>%s%s</div>' % (b64(p), w * sc, h * sc, nm, " (%d fr)" % k if k > 1 else "")
        else:
            cells += '<div class="t"><img src="%s" width="%d" height="%d"><br>%s</div>' % (b64(p), w * 3, h * 3, nm)
    return cells or "<i>geen sprite</i>"

# rijen per ronde; 'samen'-rijen delen het beeld van de rij erboven
rondes, klaar = {}, []
vorige = None
for g, rows in G:
    for x in rows:
        if g.startswith("Klaar"):
            klaar.append(x); continue
        x["id"] = slug(x["naam"]) if not x["samen"] or vorige is None else vorige["id"]
        x["groep"] = g.split(". ", 1)[-1].split(" (")[0]
        rondes.setdefault(x["batch"], []).append(x)
        vorige = x

CSS = """
:root{--bg:#fafafa;--fg:#222;--kaart:#fff;--rand:#ccc;--goed:#2e7d32;--weer:#c62828}
@media(prefers-color-scheme:dark){:root{--bg:#1b1b1b;--fg:#ddd;--kaart:#262626;--rand:#444}}
body{font:14px system-ui,sans-serif;margin:0;background:var(--bg);color:var(--fg)}
header{position:sticky;top:0;z-index:5;background:#345;color:#fff;padding:8px 16px;display:flex;gap:6px;flex-wrap:wrap;align-items:center}
header b{margin-right:10px}header button{border:0;border-radius:4px;padding:6px 10px;cursor:pointer;background:#567;color:#fff}
header button.aan{background:#fff;color:#234;font-weight:600}
main{padding:12px 16px}.ronde{display:none}.ronde.aan{display:block}
.kaart{background:var(--kaart);border:1px solid var(--rand);border-radius:6px;padding:10px;margin:0 0 12px;display:grid;grid-template-columns:minmax(0,1.3fr) minmax(0,1fr) minmax(160px,.6fr);gap:12px}
@media(max-width:800px){.kaart{grid-template-columns:1fr}}
.kaart h3{margin:0 0 4px;font-size:15px}.meta{font-size:12px;opacity:.75;margin-bottom:6px}
.t{display:inline-block;background:#8a8f88;padding:3px;margin:2px;text-align:center;font-size:10px;color:#000;vertical-align:bottom}
.t img{image-rendering:pixelated;display:block;margin:0 auto}.av img{image-rendering:auto}
.kaart>div{min-width:0}.t.sh{display:block;overflow-x:auto;max-width:100%}.concept img{max-width:100%;border-radius:4px;cursor:zoom-in}.leeg{border:2px dashed var(--rand);border-radius:4px;padding:30px;text-align:center;opacity:.6}
.oordeel button{border:1px solid var(--rand);background:transparent;color:var(--fg);border-radius:4px;padding:6px 10px;margin:0 4px 6px 0;cursor:pointer}
.oordeel button.goed.aan{background:var(--goed);color:#fff}.oordeel button.weer.aan{background:var(--weer);color:#fff}
textarea{width:100%;box-sizing:border-box;min-height:70px;background:transparent;color:var(--fg);border:1px solid var(--rand);border-radius:4px;font:inherit}
.voet{margin:8px 0 24px}.voet button{padding:8px 14px;border-radius:4px;border:0;background:#345;color:#fff;cursor:pointer}
#groot{position:fixed;inset:0;background:#000d;display:none;z-index:9;align-items:center;justify-content:center}#groot img{max-width:96vw;max-height:96vh}
"""

JS = r"""
const K='bb-concept-oordeel';let O={};try{O=JSON.parse(localStorage.getItem(K)||'{}')}catch(e){}
const bewaar=()=>{try{localStorage.setItem(K,JSON.stringify(O))}catch(e){}};
function toon(r){document.querySelectorAll('.ronde').forEach(s=>s.classList.toggle('aan',s.id=='r'+r));
 document.querySelectorAll('header button').forEach(b=>b.classList.toggle('aan',b.dataset.r==r));try{localStorage.setItem(K+'-r',r)}catch(e){}}
document.querySelectorAll('header button').forEach(b=>b.onclick=()=>toon(b.dataset.r));
let start='1';try{start=localStorage.getItem(K+'-r')||'1'}catch(e){};toon(start);
document.querySelectorAll('.kaart[data-id]').forEach(k=>{const id=k.dataset.id,o=O[id]||{},g=k.querySelector('.goed'),w=k.querySelector('.weer'),t=k.querySelector('textarea');
 const zet=()=>{g.classList.toggle('aan',o.s=='goed');w.classList.toggle('aan',o.s=='opnieuw')};t.value=o.c||'';zet();
 g.onclick=()=>{o.s=o.s=='goed'?'':'goed';O[id]=o;zet();bewaar()};w.onclick=()=>{o.s=o.s=='opnieuw'?'':'opnieuw';O[id]=o;zet();bewaar()};
 t.oninput=()=>{o.c=t.value;O[id]=o;bewaar()}});
document.querySelectorAll('.kopieer').forEach(b=>b.onclick=async()=>{const r=b.dataset.r,regels=['Oordeel ronde '+r+':'];
 document.querySelectorAll('#r'+r+' .kaart[data-id]').forEach(k=>{const o=O[k.dataset.id]||{};regels.push('- '+k.dataset.naam+' ['+k.dataset.id+']: '+(o.s||'geen oordeel')+(o.c?' - '+o.c.replace(/\n/g,' '):''))});
 const txt=regels.join('\n');let ok=true;try{await navigator.clipboard.writeText(txt)}catch(e){ok=false}
 b.nextElementSibling.textContent=ok?'gekopieerd, plak het in de chat':'kopieren mislukt, selecteer de tekst hieronder';
 if(!ok){const p=document.createElement('pre');p.textContent=txt;b.parentNode.appendChild(p)}});
const gr=document.getElementById('groot');document.addEventListener('click',e=>{if(e.target.matches('.concept img')){gr.querySelector('img').src=e.target.src;gr.style.display='flex'}else if(e.target.closest('#groot'))gr.style.display='none'});
"""

H = ['<!doctype html><html lang="nl"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
     '<title>Concept-rondes B&amp;B</title><style>' + CSS + '</style><header><b>Concept-rondes</b>']
for b in sorted(rondes):
    H.append('<button data-r="%s">Ronde %s (%d)</button>' % (b, b, tel.get(b, 0)))
H.append('<button data-r="klaar">Klaar</button></header><main>')

KAART = '''<div class="kaart" data-id="{id}" data-naam="{naam}">
<div><h3>{naam}</h3><div class="meta">{groep} · {orig} · prio {prio} · {rs}</div><div class="meta">{opm}</div>{spr}{pt}</div>
<div class="concept"><img src="img/{id}.jpg" onerror="this.outerHTML='&lt;div class=leeg&gt;nog geen concept&lt;br&gt;img/{id}.jpg&lt;/div&gt;'">{ged}</div>
<div class="oordeel"><button class="goed">Goed</button><button class="weer">Opnieuw</button><textarea placeholder="Opmerking"></textarea></div></div>'''

for b in sorted(rondes):
    H.append('<section class="ronde" id="r%s"><p>Ronde %s: %d beelden. Concepten komen in <code>scratchpad/concept/img/&lt;id&gt;.jpg</code>; zolang er geen is staat er een leeg vak. Je oordeel blijft in deze browser bewaard.</p>' % (b, b, tel.get(b, 0)))
    for x in rondes[b]:
        pf = SC + "concept/portret/%s.png" % x["id"]
        pt = ('<div class="t av"><img src="%s" width="120"><br>portret</div>' % b64(pf)) if os.path.exists(pf) else ('<div class="t av"><img src="%s" width="96"><br>avatar</div>' % b64(SC + AV) if x["port"] == AV else "")
        if not pt and x["port"] != N and os.path.exists(SC + x["port"]):
            pt = '<div class="t av"><img src="%s" width="96"><br>origineel portret (gok)</div>' % b64(SC + x["port"])
        ged = ' <span class="meta">(zelfde plaat als de vorige)</span>' if x["samen"] else ""
        H.append(KAART.format(id=x["id"], naam=html.escape(x["naam"]), groep=html.escape(x["groep"]), orig=html.escape(x["orig"]),
                              prio=x["prio"], rs=html.escape(x["rs"]), opm=html.escape(x["opm"].replace("`", "")),
                              spr=sprite_cells(x), pt=pt, ged=ged))
    H.append('<div class="voet"><button class="kopieer" data-r="%s">Kopieer oordeel ronde %s</button> <span class="ok"></span></div></section>' % (b, b))

H.append('<section class="ronde" id="rklaar">')
for x in klaar:
    H.append('<div class="kaart"><div><h3>%s</h3><div class="meta">%s</div>%s</div><div class="meta">%s</div><div></div></div>' % (
        html.escape(x["naam"]), html.escape(x["orig"]), sprite_cells(x), html.escape(x["opm"].replace("`", ""))))
H.append('</section></main><div id="groot"><img></div><script>' + JS + '</script>')
open(HTML, "w", encoding="utf-8").write("\n".join(H))
print(os.path.getsize(HTML), [x["id"] for x in rondes[1]])
