# Il repository — come è fatto e come si pubblica

Aggiornato il 23 settembre 2026.

## Struttura

```
book/       un file Markdown per capitolo (NN-slug.md), figure in book/figures/, STYLE.md per chi scrive
slides/     un deck HTML5 per lezione (reveal.js da CDN), tema condiviso in slides/assets/
code/       il codice mostrato in ciascun capitolo, una cartella per capitolo, tutto eseguibile
exam/       regole d'esame e testi delle due prove (italiano)
docs/       questi documenti del docente (italiano); docs/archivio/ i testi d'esame 2025
tools/      build.py e il foglio di stile del libro; nient'altro
site/       generato da tools/build.py, non versionato
```

Il libro **non è più la sorgente delle slide**. I capitoli sono prosa da leggere; i deck sono
scritti a mano, slide per slide, e stanno in `slides/`. Il codice sta in `code/` e ogni
capitolo cita solo frammenti presi da lì: se un frammento serve nel testo, prima si mette nel
file e si esegue.

`python3 tools/build.py` costruisce `site/`: un HTML per capitolo, l'indice, l'esame, copia
delle slide e del codice. `--pdf` aggiunge il libro intero in un PDF. `--serve` lo serve in
locale. Serve `pandoc`; per il PDF anche `xelatex` e i font IBM Plex.

## Rami

- `main` — quello che gli studenti vedono. GitHub Pages lo pubblica su
  <https://vincenzoml.github.io/PLDW/> a ogni push (workflow in `.github/workflows/pages.yml`;
  va abilitato una volta nelle impostazioni del repository, *Pages → Source: GitHub Actions*).
- `draft-2026` — tutto il materiale rivisto, anche le lezioni non ancora tenute. **Non è
  pubblico finché non viene fuso in `main`.**
- `edizione-2025` — il corso com'era: PDF generati dai README, vecchio `build.py`.

## Pubblicare una lezione

Le lezioni si pubblicano una alla volta, quando vengono tenute. Per la lezione N, dal ramo
`main`:

```bash
git checkout main
git checkout draft-2026 -- book/NN-slug.md book/figures/NN-slug slides/NN-slug.html code/NN-slug
git commit -m "Lezione N: <titolo>"
git push
```

`tools/build.py` elenca solo i capitoli presenti in `book/`: l'indice del sito si aggiorna da
solo. Se si è corretto un capitolo già pubblicato lavorando su `draft-2026`, lo stesso comando
lo porta su `main`.

## Vincolo di riservatezza

Il repository è pubblico. Il materiale dell'esperimento in corso su VoxLogicA è inedito e non
entra in nessuna forma: né numeri, né figure, né testo, né registri di sviluppo. Il capitolo
11 ne racconta solo il metodo di lavoro. Chi tocca i capitoli 0 e 11 rilegge questo paragrafo.
