// Shared reveal.js initialisation for every PLDW deck.
Reveal.initialize({
  hash: true,
  slideNumber: "c/t",
  width: 1280, height: 720, margin: 0.06,
  transition: "none",
  progress: true, controls: false,
  plugins: [RevealHighlight, RevealNotes, RevealMath.KaTeX],
});
