(function () {
  const apps = window.APPS || [];
  const grid = document.getElementById("grid");
  const empty = document.getElementById("empty");
  const player = document.getElementById("player");
  const playerMedia = document.getElementById("player-media");
  const playerPrev = document.getElementById("player-prev");
  const playerNext = document.getElementById("player-next");
  const playerCount = document.getElementById("player-count");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const canHover = window.matchMedia("(hover: hover)").matches;
  const SLIDE_MS = 1800;

  function el(tag, props, children) {
    const node = document.createElement(tag);
    Object.assign(node, props || {});
    (children || []).forEach((c) => c && node.append(c));
    return node;
  }

  function initials(name) {
    return name
      .split(/\s+/)
      .map((w) => w[0])
      .join("")
      .slice(0, 2)
      .toUpperCase();
  }

  function videoEl(sources, props) {
    const v = el("video", props);
    [].concat(sources).forEach((src) => {
      const ext = src.split(".").pop().toLowerCase();
      v.append(el("source", { src, type: ext === "webm" ? "video/webm" : "video/mp4" }));
    });
    return v;
  }

  // Alles wat in de grote speler getoond kan worden: eerst de video, dan de screenshots.
  function galleryItems(app) {
    const items = [];
    if (app.video) items.push({ kind: "video", src: app.video, poster: app.poster });
    else if (app.youtube) items.push({ kind: "youtube", id: app.youtube });
    (app.screenshots || []).forEach((src) => items.push({ kind: "image", src }));
    return items;
  }

  // Een preview heeft start() en stop(): speelt de video of wisselt de screenshots.
  function buildMedia(app) {
    const button = el("button", { type: "button", className: "media" });
    button.style.setProperty("--card-color", app.color || "#555");
    const frame = el("div", { className: "frame" });
    const shots = app.screenshots || [];
    let preview = null;

    if (app.video) {
      const video = videoEl(app.video, { muted: true, loop: true, playsInline: true, preload: "none" });
      if (app.poster) video.poster = app.poster;
      video.setAttribute("aria-hidden", "true");
      frame.append(video);
      button.append(frame, el("span", { className: "badge", textContent: "▶ Demo" }));
      preview = {
        start: () => video.play().catch(() => {}),
        stop: () => video.pause(),
      };
    } else if (app.youtube) {
      frame.classList.add("wide");
      frame.append(el("img", { src: app.poster || `https://i.ytimg.com/vi/${encodeURIComponent(app.youtube)}/hqdefault.jpg`, alt: "", loading: "lazy" }));
      button.append(frame, el("span", { className: "badge", textContent: "▶ Video" }));
    } else if (shots.length) {
      const imgs = shots.map((src, i) => el("img", { src, alt: "", loading: "lazy", className: i === 0 ? "active" : "" }));
      frame.append(...imgs);
      const dots = shots.length > 1 ? el("span", { className: "dots" }, shots.map((_, i) => el("i", { className: i === 0 ? "on" : "" }))) : null;
      button.append(frame, dots, el("span", { className: "badge", textContent: `📷 ${shots.length}` }));
      let index = 0;
      let timer = null;
      const show = (i) => {
        imgs[index].classList.remove("active");
        if (dots) dots.children[index].classList.remove("on");
        index = i;
        imgs[index].classList.add("active");
        if (dots) dots.children[index].classList.add("on");
      };
      if (shots.length > 1) {
        preview = {
          start: () => {
            if (!timer) timer = setInterval(() => show((index + 1) % imgs.length), SLIDE_MS);
          },
          stop: () => {
            clearInterval(timer);
            timer = null;
          },
        };
      }
    } else {
      button.append(el("div", { className: "placeholder" }, [initials(app.name), el("small", { textContent: "Demo volgt" })]));
      button.disabled = true;
    }

    if (!button.disabled) {
      button.setAttribute("aria-label", `Demo van ${app.name} bekijken`);
      button.addEventListener("click", () => openPlayer(app));
    }
    return { button, preview };
  }

  // Op touch-apparaten start de preview zodra het kaartje grotendeels in beeld is.
  const previews = new WeakMap();
  const allPreviews = [];
  const inView = new Set();
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        const p = previews.get(e.target);
        if (!p) return;
        if (e.isIntersecting) inView.add(p);
        else inView.delete(p);
        if (player.open) return;
        e.isIntersecting ? p.start() : p.stop();
      });
    },
    { threshold: 0.6 }
  );

  function buildCard(app) {
    const { button, preview } = buildMedia(app);

    const links = el(
      "div",
      { className: "links" },
      (app.links || []).map((l) => {
        const a = el("a", { href: l.url, textContent: l.label });
        if (/^https?:/.test(l.url)) {
          a.target = "_blank";
          a.rel = "noopener";
        }
        return a;
      })
    );

    const body = el("div", { className: "card-body" }, [
      el("div", { className: "card-title" }, [
        el("h2", { textContent: app.name }),
        el("span", { className: "type", textContent: app.type === "game" ? "Game" : "App" }),
      ]),
      app.status ? el("p", { className: "status", textContent: app.status }) : null,
      app.tagline ? el("p", { className: "tagline", textContent: app.tagline }) : null,
      app.description ? el("p", { className: "description", textContent: app.description }) : null,
      el("ul", { className: "tags" }, (app.tags || []).map((t) => el("li", { textContent: t }))),
      links,
    ]);

    const card = el("li", { className: "card" }, [button, body]);
    card.dataset.type = app.type;

    if (preview && !reduceMotion) {
      allPreviews.push(preview);
      button.addEventListener("focus", preview.start);
      button.addEventListener("blur", preview.stop);
      if (canHover) {
        card.addEventListener("mouseenter", preview.start);
        card.addEventListener("mouseleave", preview.stop);
      } else {
        previews.set(button, preview);
        observer.observe(button);
      }
    }
    return card;
  }

  // Grote speler: video en/of screenshots, met vorige/volgende.
  let current = { app: null, items: [], index: 0 };

  function renderItem() {
    const { app, items, index } = current;
    const item = items[index];
    if (playerMedia.contains(document.activeElement)) player.focus();
    playerMedia.replaceChildren();
    playerMedia.className = "player-media " + (item.kind === "youtube" ? "wide" : "tall");
    if (item.kind === "video") {
      const v = videoEl(item.src, { controls: true, autoplay: true, loop: true, playsInline: true });
      v.setAttribute("aria-label", `Demo van ${app.name}`);
      if (item.poster) v.poster = item.poster;
      playerMedia.append(v);
    } else if (item.kind === "youtube") {
      playerMedia.append(
        el("iframe", {
          src: `https://www.youtube-nocookie.com/embed/${encodeURIComponent(item.id)}?autoplay=1&rel=0`,
          title: `Demo van ${app.name}`,
          allow: "autoplay; encrypted-media; picture-in-picture; fullscreen",
          allowFullscreen: true,
        })
      );
    } else {
      playerMedia.append(el("img", { src: item.src, alt: `${app.name}, afbeelding ${index + 1}` }));
    }
    const multi = items.length > 1;
    playerPrev.hidden = playerNext.hidden = playerCount.hidden = !multi;
    playerCount.textContent = `${index + 1} / ${items.length}`;
  }

  function step(delta) {
    const n = current.items.length;
    if (n < 2) return;
    current.index = (current.index + delta + n) % n;
    renderItem();
  }

  function openPlayer(app) {
    current = { app, items: galleryItems(app), index: 0 };
    if (!current.items.length) return;
    player.setAttribute("aria-label", `Demo van ${app.name}`);
    allPreviews.forEach((p) => p.stop());
    renderItem();
    player.showModal();
  }

  player.addEventListener("close", () => {
    playerMedia.replaceChildren();
    inView.forEach((p) => p.start());
  });
  player.addEventListener("click", (e) => {
    if (e.target === player) player.close();
  });
  document.addEventListener("keydown", (e) => {
    if (!player.open || e.target instanceof HTMLVideoElement) return;
    if (e.key === "ArrowLeft") step(-1);
    if (e.key === "ArrowRight") step(1);
  });
  playerPrev.addEventListener("click", () => step(-1));
  playerNext.addEventListener("click", () => step(1));
  document.getElementById("player-close").addEventListener("click", () => player.close());

  // Filters
  const chips = document.querySelectorAll(".chip");
  chips.forEach((chip) =>
    chip.addEventListener("click", () => {
      const filter = chip.dataset.filter;
      chips.forEach((c) => c.setAttribute("aria-pressed", String(c === chip)));
      let visible = 0;
      grid.querySelectorAll(".card").forEach((card) => {
        const show = filter === "all" || card.dataset.type === filter;
        card.hidden = !show;
        if (show) visible++;
      });
      empty.hidden = visible > 0;
    })
  );

  apps.forEach((app) => grid.append(buildCard(app)));
  empty.hidden = apps.length > 0;
})();
