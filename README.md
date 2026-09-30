# Apps

Showcase van mijn apps en games: een pagina met kaartjes, elk met een korte demo-video van de gameplay of het gebruik.

## Bekijken

Open `index.html` in je browser, of zet GitHub Pages aan (Settings → Pages → branch `main`, map `/ (root)`).
De pagina is dan te zien op `https://abons.github.io/Apps/`.

## Een app toevoegen

1. Zet een korte demo-video (10–20 sec, `.mp4` of `.webm`) in `media/<app-id>/`, bijvoorbeeld `media/mijn-game/demo.mp4`.
   Voeg eventueel een stilstaand beeld toe (`poster.jpg`) dat getoond wordt voordat de video speelt.
2. Voeg in `apps.js` een item toe aan de lijst `window.APPS` (de velden staan bovenaan dat bestand uitgelegd).
   Voor een langere video kun je in plaats van `video` een YouTube-id invullen bij `youtube`.

Op een computer speelt de demo (zonder geluid) zodra je over het kaartje beweegt; op een telefoon zodra het kaartje in beeld is.
Klik op de video om hem groot en met geluid af te spelen.

Tip: houd video's klein (enkele MB's), bijvoorbeeld met
`ffmpeg -i opname.mov -vf scale=1280:-2 -an -c:v libx264 -crf 28 -movflags +faststart demo.mp4`.
