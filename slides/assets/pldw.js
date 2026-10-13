// Shared reveal.js initialisation for every PLDW deck.
//
// Before reveal starts, three things are added to the markup, so that the decks
// themselves stay plain HTML:
//   - every section.part gets a dark background and a running number (01, 02, ...);
//   - every ordinary slide gets a running head naming the part it belongs to.

(function decorate() {
  const INK = "#111318";
  const sections = [...document.querySelectorAll(".reveal .slides > section")];
  let current = "", part = 0;

  for (const s of sections) {
    if (s.classList.contains("title")) {
      current = (s.querySelector("h1") || {}).textContent || "";
      part = 0;
      continue;
    }
    if (s.classList.contains("part")) {
      part += 1;
      current = (s.querySelector("h2") || {}).textContent || current;
      if (!s.hasAttribute("data-background-color")) s.setAttribute("data-background-color", INK);
      if (!s.querySelector(".num"))
        s.insertAdjacentHTML("afterbegin", `<p class="num">${String(part).padStart(2, "0")}</p>`);
      continue;
    }
    if (!s.querySelector(".runhead") && current)
      s.insertAdjacentHTML("afterbegin", `<p class="runhead"><span>${escape(current)}</span></p>`);
  }

  function escape(t) {
    return t.replace(/[&<>]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
  }

})();

// Safety net: a slide whose content does not fit is scaled down just enough, and a
// listing wider than its box gets a smaller font. Slides that fit are untouched.
// It is a rescue, not a layout tool: a slide that needs it should be split by hand.
function fit(slide) {
  if (!slide || slide.classList.contains("part") || slide.classList.contains("title")) return;
  // only the flow content counts: the running head, popups and overlays sit on top of it
  const kids = [...slide.children].filter(k => !["absolute", "fixed"].includes(getComputedStyle(k).position));
  kids.forEach(k => (k.style.zoom = ""));
  slide.querySelectorAll("pre").forEach(p => (p.style.fontSize = ""));
  slide.querySelectorAll("pre code").forEach(c => {
    if (c.scrollWidth > c.clientWidth + 1) {
      const pre = c.parentElement, fs = parseFloat(getComputedStyle(pre).fontSize);
      pre.style.fontSize = (fs * c.clientWidth / c.scrollWidth - 0.3) + "px";
    }
  });
  const box = slide.getBoundingClientRect(), scale = box.width / slide.offsetWidth;
  let top = Infinity, bottom = 0;
  kids.forEach(k => {
    const r = k.getBoundingClientRect();
    if (r.height) { top = Math.min(top, r.top); bottom = Math.max(bottom, r.bottom); }
  });
  if (!isFinite(top)) return;
  const used = (bottom - top) / scale, room = 690 - (top - box.top) / scale;
  if (used > room) kids.forEach(k => (k.style.zoom = String(Math.max(0.6, room / used))));
}

// Carousel: a row of cards; each hidden .carousel-step fragment brings the next card to the
// centre, enlarged, with the others pushed aside and dimmed.
function carousel(slide) {
  if (!slide) return;
  slide.querySelectorAll(".carousel").forEach(c => {
    const cards = [...c.children].filter(k => k.classList.contains("card"));
    const k = slide.querySelectorAll(".carousel-step.visible").length - 1;   // -1: none yet
    const n = cards.length;
    cards.forEach((card, i) => {
      const at = k < 0;
      card.style.setProperty("--d", at ? String(i - (n - 1) / 2) : String((i - k) * 1.25));
      card.style.setProperty("--s", at ? "1" : i === k ? "1.4" : "0.8");
      card.style.setProperty("--o", at || i === k ? "1" : "0.3");
      card.classList.toggle("on", !at && i === k);
    });
  });
}
// A popup with data-node="..." points at the element of a figure carrying the same
// data-node: the popup moves to the side away from it, and a ring and a leader line,
// drawn on top of the blur, connect the two.
function pin(slide) {
  if (!slide) return;
  let layer = slide.querySelector(":scope > .pin-layer");
  const pop = slide.querySelector(":scope > .popup.current-fragment[data-node]");
  if (!pop) { if (layer) layer.innerHTML = ""; return; }
  const node = slide.querySelector(`svg [data-node="${pop.dataset.node}"]`);
  if (!node) return;
  if (!layer) {
    layer = document.createElementNS("http://www.w3.org/2000/svg", "svg");
    layer.setAttribute("class", "pin-layer");
    layer.setAttribute("viewBox", "0 0 1280 720");
    slide.appendChild(layer);
  }
  const sb = slide.getBoundingClientRect(), k = sb.width / slide.offsetWidth;
  const nb = node.getBoundingClientRect();
  const nx = (nb.left + nb.width / 2 - sb.left) / k, ny = (nb.top + nb.height / 2 - sb.top) / k;
  pop.style.left = nx < 640 ? "70%" : "30%";
  pop.style.top = "56%";
  const pb = pop.getBoundingClientRect();
  const px0 = (pb.left - sb.left) / k, px1 = (pb.right - sb.left) / k;
  const py0 = (pb.top - sb.top) / k, py1 = (pb.bottom - sb.top) / k;
  const ex = nx < 640 ? px0 : px1, ey = Math.min(Math.max(ny, py0 + 30), py1 - 30);
  layer.innerHTML =
    `<circle class="halo" cx="${nx}" cy="${ny}" r="22"/>` +
    `<circle class="ring" cx="${nx}" cy="${ny}" r="13"/>` +
    `<path class="lead" d="M ${nx + (ex > nx ? 13 : -13)} ${ny} L ${ex} ${ey}"/>` +
    `<circle cx="${ex}" cy="${ey}" r="4" style="fill:var(--warm)"/>`;
}
Reveal.on("fragmentshown", e => pin(Reveal.getCurrentSlide()));
Reveal.on("fragmenthidden", e => pin(Reveal.getCurrentSlide()));
Reveal.on("slidechanged", e => pin(e.currentSlide));

Reveal.on("fragmentshown", e => carousel(Reveal.getCurrentSlide()));
Reveal.on("fragmenthidden", e => carousel(Reveal.getCurrentSlide()));
Reveal.on("slidechanged", e => carousel(e.currentSlide));
Reveal.on("ready", e => carousel(e.currentSlide));

Reveal.on("ready", e => fit(e.currentSlide));
Reveal.on("slidechanged", e => fit(e.currentSlide));

Reveal.initialize({
  hash: true,
  slideNumber: "c/t",
  width: 1280, height: 720, margin: 0.04,
  center: false,
  transition: "none", backgroundTransition: "none",
  progress: true, controls: false,
  plugins: [RevealHighlight, RevealNotes, RevealMath.KaTeX],
});

// Navigation bar: hover the bottom edge of the screen to show it. A button back to the
// start, one per deck opening (in a joined lesson: part A, part B), and a slider that
// jumps to any slide while showing its title.
Reveal.on("ready", () => {
  const titleOf = s => ((s.querySelector("h1, h2") || {}).textContent || "").trim();
  const slides = Reveal.getSlides();
  const openings = slides.map((s, i) => [s, i]).filter(([s]) => s.classList.contains("title"));

  const bar = document.createElement("div");
  bar.className = "pldw-nav";
  bar.innerHTML =
    `<button data-go="0" title="Back to the first slide">↺ start</button>` +
    (openings.length > 1
      ? openings.map(([s, i], k) =>
          `<button data-go="${i}" title="${titleOf(s)}">${String.fromCharCode(65 + k)}</button>`).join("")
      : "") +
    `<input type="range" min="1" max="${slides.length}" step="1" aria-label="Go to slide">` +
    `<span class="where"></span>`;
  document.body.appendChild(bar);

  const range = bar.querySelector("input"), where = bar.querySelector(".where");
  const show = i => (where.textContent = `${i + 1} / ${slides.length} · ${titleOf(slides[i])}`);
  const sync = () => { const i = slides.indexOf(Reveal.getCurrentSlide()); range.value = i + 1; show(i); };

  bar.addEventListener("click", e => {
    const b = e.target.closest("button[data-go]");
    if (b) Reveal.slide(+b.dataset.go);
  });
  range.addEventListener("input", () => { show(range.value - 1); Reveal.slide(range.value - 1); });
  range.addEventListener("keydown", e => e.stopPropagation());
  Reveal.on("slidechanged", sync);
  sync();
});
