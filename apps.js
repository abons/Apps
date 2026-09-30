// Lijst met apps die op de showcase-pagina getoond worden.
// Voeg een app toe door hieronder een object te kopiëren en aan te passen.
//
// Velden:
//   id          unieke korte naam (ook de map in media/)
//   name        naam van de app
//   type        "game" of "app" (gebruikt voor de filterknoppen)
//   status      korte statusregel, bv. "Speel in je browser" of "In ontwikkeling"
//   tagline     één korte zin
//   description paar zinnen uitleg
//   tags        lijst met trefwoorden
//   video       pad naar een korte demo-video, of een lijst met dezelfde video in meerdere
//               formaten (mp4 eerst, webm als terugval), bv. ["media/x/demo.mp4", "media/x/demo.webm"]
//   youtube     alternatief voor video: YouTube-video-id
//   poster      stilstaand beeld dat getoond wordt voordat de video speelt
//   screenshots lijst met afbeeldingen; zonder video worden ze als slideshow getoond
//   color       achtergrondkleur achter de telefoonbeelden
//   links       knoppen onder het kaartje: { label, url }

window.APPS = [
  {
    id: "wordguesser",
    name: "Word Guesser",
    type: "game",
    status: "Speel in je browser",
    tagline: "Raad het verborgen woord in zes pogingen.",
    description:
      "Groen, geel en grijs vertellen hoe dichtbij je zit. Dagelijkse puzzel met scorebord, vrij spelen, op tijd en duels, in veel talen en met woordlengtes van 4 tot 8.",
    tags: ["Woordspel", "Web", "Android"],
    video: ["media/wordguesser/demo.mp4", "media/wordguesser/demo.webm"],
    poster: "media/wordguesser/poster.jpg",
    screenshots: ["media/wordguesser/screenshot.webp"],
    color: "#3f7d3a",
    links: [
      { label: "Speel", url: "https://abons.github.io/wordguesser/" },
      { label: "GitHub", url: "https://github.com/abons/wordguesser" },
    ],
  },
  {
    id: "wordfinder",
    name: "Woord Swiper",
    type: "game",
    status: "Speel in je browser",
    tagline: "Swipe letters op het wiel en vul de kruiswoordpuzzel.",
    description:
      "Alle woorden van een level komen uit één basiswoord. Geldige woorden die niet in het rooster staan zijn bonuswoorden en leveren munten op voor hints. Dagelijks level en een campagne.",
    tags: ["Woordspel", "Nederlands", "Web", "Android"],
    video: ["media/wordfinder/demo.mp4", "media/wordfinder/demo.webm"],
    poster: "media/wordfinder/poster.jpg",
    screenshots: ["media/wordfinder/swipe.webp", "media/wordfinder/campaign.webp"],
    color: "#4a8fc4",
    links: [
      { label: "Speel", url: "https://abons.github.io/wordfinder/" },
      { label: "GitHub", url: "https://github.com/abons/wordfinder" },
    ],
  },
  {
    id: "wordpuzzle",
    name: "Woord Puzzel",
    type: "game",
    status: "Speel in je browser",
    tagline: "Zweedse kruiswoordpuzzels met echte woordenboekdefinities.",
    description:
      "Elke puzzel wordt gegenereerd, elke aanwijzing is een echte definitie met het antwoord weggelaten. Eén dagpuzzel voor iedereen met een scorebord, plus vrij spelen in drie formaten.",
    tags: ["Kruiswoord", "Nederlands", "Web", "Android"],
    video: ["media/wordpuzzle/demo.mp4", "media/wordpuzzle/demo.webm"],
    poster: "media/wordpuzzle/poster.jpg",
    screenshots: ["media/wordpuzzle/puzzle.webp", "media/wordpuzzle/clues.webp"],
    color: "#5b6fb5",
    links: [
      { label: "Speel", url: "https://abons.github.io/wordpuzzle/" },
      { label: "GitHub", url: "https://github.com/abons/wordpuzzle" },
    ],
  },
  {
    id: "kinderwoordjes",
    name: "Kinderwoordjes",
    type: "app",
    status: "Gebruik in je browser",
    tagline: "Eerste Nederlandse woordjes voor peuters.",
    description:
      "Kies een categorie en zie een groot plaatje met het woord eronder. De eerste tik leest het woord voor, de tweede gaat naar het volgende. Installeerbaar en werkt offline.",
    tags: ["Kinderen", "Leren", "PWA"],
    video: ["media/kinderwoordjes/demo.mp4", "media/kinderwoordjes/demo.webm"],
    poster: "media/kinderwoordjes/poster.jpg",
    color: "#f2b441",
    links: [
      { label: "Open app", url: "https://abons.github.io/Kinderwoordjes/" },
      { label: "GitHub", url: "https://github.com/abons/Kinderwoordjes" },
    ],
  },
  {
    id: "e-charge",
    name: "e-charge",
    type: "app",
    status: "Gebruik in je browser",
    tagline: "Hoe lang laadt de Nissan Leaf aan het stopcontact?",
    description:
      "Rekenhulp van één scherm: laadtijd van je huidige naar je gewenste percentage, hoe laat hij klaar is, hoeveel kilometer erin zit en wat het kost met de stroomprijs per kwartier.",
    tags: ["Elektrisch rijden", "Rekenhulp", "PWA"],
    video: ["media/e-charge/demo.mp4", "media/e-charge/demo.webm"],
    poster: "media/e-charge/poster.jpg",
    color: "#2f6f5e",
    links: [
      { label: "Open app", url: "https://abons.github.io/e-charge/" },
      { label: "GitHub", url: "https://github.com/abons/e-charge" },
    ],
  },
  {
    id: "beasts",
    name: "Beasts",
    type: "game",
    status: "In ontwikkeling · Android",
    tagline: "Isometrisch dorpsspel in de geest van Beasts and Bumpkins.",
    description:
      "Bouw en onderhoud een dorp dat zich voedt met eigen akkers en kuddes. Oogst, verkoop in de winkels, bouw meer huizen en groei tot je het doel van het level haalt. Twaalf levels.",
    tags: ["Strategie", "Realtime", "Android"],
    screenshots: [
      "media/beasts/level-zes.webp",
      "media/beasts/groei-in-het-dorp.webp",
      "media/beasts/bouwplaats-vier-bouwers.webp",
      "media/beasts/vee-in-het-dorp.webp",
      "media/beasts/beginscherm.webp",
    ],
    color: "#7a9a3a",
    links: [{ label: "GitHub", url: "https://github.com/abons/beasts" }],
  },
  {
    id: "kwelder",
    name: "Kwelder",
    type: "game",
    status: "In ontwikkeling · Android",
    tagline: "Beurtgebaseerde 4X-strategie in de geest van Polytopia.",
    description:
      "Twee stammen op een archipel die uit één seed wordt gegenereerd. Verken in de mist, verover steden en win land terug op de zee: de kwelder waar het spel naar vernoemd is.",
    tags: ["Strategie", "4X", "Android"],
    screenshots: [
      "media/kwelder/eiland.webp",
      "media/kwelder/mist.webp",
      "media/kwelder/kwelder-voor.webp",
      "media/kwelder/kwelder-na.webp",
      "media/kwelder/stad-veroverd.webp",
    ],
    color: "#3d7ea6",
    links: [{ label: "GitHub", url: "https://github.com/abons/kwelder" }],
  },
  {
    id: "dndai",
    name: "DnDAI",
    type: "game",
    status: "In ontwikkeling · Android",
    tagline: "Een D&D-verhaalspel met een AI als dungeon master.",
    description:
      "Kies een verhaal en een personage en speel aan een virtuele tafel. De AI vertelt, handhaaft de regels en houdt je karakterblad bij; de dobbelstenen rol je zelf in de app.",
    tags: ["RPG", "AI", "Android"],
    screenshots: [
      "media/dndai/tafel.webp",
      "media/dndai/dobbelsteen.webp",
      "media/dndai/suggesties.webp",
      "media/dndai/aanval.webp",
      "media/dndai/levelup.webp",
    ],
    color: "#7b4b94",
    links: [{ label: "GitHub", url: "https://github.com/abons/dndai" }],
  },
  {
    id: "fastlane",
    name: "Fast Lane",
    type: "game",
    status: "Binnenkort op Google Play",
    tagline: "Levenssimulatie in de geest van Jones in the Fast Lane.",
    description:
      "Loop door een gegenereerde stad en bouw in een beperkt aantal weken rijkdom, opleiding, geluk en carrière op. Speel tegen een AI-rivaal, samen op één telefoon of online tegen een ander.",
    tags: ["Simulatie", "Multiplayer", "Android"],
    screenshots: ["media/fastlane/map.webp", "media/fastlane/duel.webp"],
    color: "#c2603a",
    links: [{ label: "GitHub", url: "https://github.com/abons/fastlane" }],
  },
];
