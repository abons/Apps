(function () {
  const apps = window.APPS || [];
  const grid = document.getElementById("grid");
  const empty = document.getElementById("empty");
  const player = document.getElementById("player");
  const playerMedia = document.getElementById("player-media");
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const canHover = window.matchMedia("(hover: hover)").matches;

  function el(tag, props, children) {
    const node = document.createElement(tag);
    Object.assign(node, props || {});
    (children || []).forEach((c) => node.append(c));
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

  function youtubeThumb(id) {
    return `https://i.ytimg.com/vi/${encodeURIComponent(id)}/hqdefault.jpg`;
  }

  function buildMedia(app) {
    const button = el("button", { type: "button", className: "media" });
    button.style.setProperty("--card-color", app.color || "#555");

    if (app.video) {
      const video = el("video", {
        src: app.video,
        muted: true,
        loop: true,
        playsInline: true,
        preload: "metadata",
      });
      if (app.poster) video.poster = app.poster;
      video.setAttribute("aria-hidden", "true");
      button.append(video, el("span", { className: "play-badge" }));
      button.setAttribute("aria-label", `Demo van ${app.name} afspelen`);
      button.addEventListener("click", () => openPlayer(app));
      button._preview = video;
    } else if (app.youtube) {
      const img = el("img", {
        src: app.poster || youtubeThumb(app.youtube),
        alt: "",
        loading: "lazy",
      });
      button.append(img, el("span", { className: "play-badge" }));
      button.setAttribute("aria-label", `Demo van ${app.name} afspelen`);
      button.addEventListener("click", () => openPlayer(app));
    } else if (app.poster) {
      button.append(el("img", { src: app.poster, alt: "", loading: "lazy" }));
      button.disabled = true;
    } else {
      button.append(
        el("div", { className: "placeholder" }, [
          initials(app.name),
          el("small", { textContent: "Demo volgt" }),
        ])
      );
      button.disabled = true;
    }
    return button;
  }

  function buildCard(app) {
    const media = buildMedia(app);

    const tags = el(
      "ul",
      { className: "tags" },
      (app.tags || []).map((t) => el("li", { textContent: t }))
    );

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
      app.tagline ? el("p", { className: "tagline", textContent: app.tagline }) : "",
      app.description ? el("p", { className: "description", textContent: app.description }) : "",
      tags,
      links,
    ]);

    const card = el("li", { className: "card" }, [media, body]);
    card.dataset.type = app.type;

    const video = media._preview;
    if (video && !reduceMotion) {
      if (canHover) {
        card.addEventListener("mouseenter", () => video.play().catch(() => {}));
        card.addEventListener("mouseleave", () => video.pause());
      } else {
        observer.observe(video);
      }
    }
    return card;
  }

  // Op touch-apparaten speelt de preview zodra het kaartje grotendeels in beeld is.
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (e.isIntersecting) e.target.play().catch(() => {});
        else e.target.pause();
      });
    },
    { threshold: 0.6 }
  );

  function openPlayer(app) {
    playerMedia.replaceChildren();
    if (app.video) {
      const v = el("video", { src: app.video, controls: true, autoplay: true, playsInline: true });
      if (app.poster) v.poster = app.poster;
      playerMedia.append(v);
    } else if (app.youtube) {
      const iframe = el("iframe", {
        src: `https://www.youtube-nocookie.com/embed/${encodeURIComponent(app.youtube)}?autoplay=1&rel=0`,
        title: `Demo van ${app.name}`,
        allow: "autoplay; encrypted-media; picture-in-picture; fullscreen",
        allowFullscreen: true,
      });
      playerMedia.append(iframe);
    }
    player.showModal();
  }

  function closePlayer() {
    player.close();
  }

  player.addEventListener("close", () => playerMedia.replaceChildren());
  player.addEventListener("click", (e) => {
    if (e.target === player) closePlayer();
  });
  document.getElementById("player-close").addEventListener("click", closePlayer);

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
