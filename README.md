# Apps

Showcase van mijn apps en games: een pagina met kaartjes, elk met een korte demo-video van de gameplay of het gebruik.

Live: **https://abons.github.io/Apps/**

## Een app toevoegen

1. Zet een korte demo-video (10–20 sec) in `media/<app-id>/`, bij voorkeur als `demo.mp4` én `demo.webm`,
   plus een stilstaand beeld (`poster.jpg`) dat getoond wordt voordat de video speelt.
   Heb je (nog) geen video, dan kun je screenshots opgeven; die worden als slideshow getoond.
2. Voeg in `apps.js` een item toe aan de lijst `window.APPS` (de velden staan bovenaan dat bestand uitgelegd).
   Voor een langere video kun je in plaats van `video` een YouTube-id invullen bij `youtube`.

Op een computer speelt de demo zodra je over het kaartje beweegt; op een telefoon zodra het kaartje in beeld is.
Klik of tik op de video om hem groot af te spelen, samen met de screenshots van die app.

Wat er nog op je pc moet gebeuren (o.a. video's van de Android-games) staat in [TODO.md](TODO.md).

Tip: houd video's klein (enkele MB's), bijvoorbeeld met
`ffmpeg -i opname.mov -vf scale=1280:-2 -an -c:v libx264 -crf 28 -movflags +faststart demo.mp4`.
