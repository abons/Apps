// Lijst met apps die op de showcase-pagina getoond worden.
// Voeg een app toe door hieronder een object te kopiëren en aan te passen.
//
// Velden:
//   id          unieke korte naam (ook gebruikt als map in media/)
//   name        naam van de app
//   type        "game" of "app" (gebruikt voor de filterknoppen)
//   tagline     één korte zin
//   description paar zinnen uitleg
//   tags        lijst met trefwoorden
//   video       pad naar een korte demo-video (mp4/webm), bv. "media/mijn-app/demo.mp4"
//   youtube     alternatief voor video: YouTube-video-id, bv. "dQw4w9WgXcQ"
//   poster      stilstaand beeld dat getoond wordt voordat de video speelt
//   color       accentkleur voor de placeholder als er (nog) geen media is
//   links       knoppen onder het kaartje: { label, url }

window.APPS = [
  {
    id: "voorbeeld-game",
    name: "Voorbeeld Game",
    type: "game",
    tagline: "Een snelle arcade-game voor tussendoor.",
    description:
      "Vervang deze tekst door een korte beschrijving van je game. Zet een demo-video in media/voorbeeld-game/ en vul hieronder het pad in.",
    tags: ["Arcade", "Web"],
    video: "", // bv. "media/voorbeeld-game/demo.mp4"
    poster: "",
    color: "#e4572e",
    links: [
      { label: "Speel", url: "#" },
      { label: "Code", url: "https://github.com/abons/Apps" },
    ],
  },
  {
    id: "voorbeeld-app",
    name: "Voorbeeld App",
    type: "app",
    tagline: "Handige tool voor dagelijks gebruik.",
    description:
      "Laat in een korte opname zien hoe de app gebruikt wordt: een schermopname van 10–20 seconden werkt het best.",
    tags: ["Productiviteit", "iOS", "Android"],
    video: "",
    poster: "",
    color: "#2e86ab",
    links: [{ label: "Open app", url: "#" }],
  },
  {
    id: "voorbeeld-youtube",
    name: "Voorbeeld met YouTube",
    type: "game",
    tagline: "Demo die vanaf YouTube wordt afgespeeld.",
    description:
      "Heb je een langere video? Zet dan het YouTube-id in het veld youtube in plaats van een lokaal videobestand.",
    tags: ["Puzzel"],
    youtube: "", // bv. "dQw4w9WgXcQ"
    color: "#76b041",
    links: [],
  },
];
