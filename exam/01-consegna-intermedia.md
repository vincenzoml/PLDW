# Consegna intermedia

**Obbligatoria e votata: vale un terzo del voto di laboratorio.** Chi non consegna non è
ammesso alla prova finale. Le regole generali sono in [00-regole](00-regole.html).

**Scadenza:** comunicata a lezione, di norma alla sesta settimana di corso.

## Cosa si consegna

Un repository (GitHub o equivalente) contenente:

1. **`README.md` — il dominio.** Quale dominio applicativo hai scelto e perché merita un
   linguaggio. Quali sono le *entità* del dominio (cosa sono i valori) e quali le
   *operazioni caratteristiche* (cosa fa chi lavora in quel dominio). Cosa vuoi poter
   esprimere che oggi, in quel dominio, si fa a mano o con codice ad hoc.
2. **Le primitive, giustificate.** L'elenco delle primitive del tuo linguaggio, ciascuna
   con un esempio d'uso e una riga sul suo significato. Per ogni primitiva, perché è nel
   linguaggio; per almeno due operazioni plausibili del dominio, perché *non* ci sono.
3. **Il primo interprete.** Codice che gira: valuta espressioni e `let` nel dominio scelto,
   e produce un risultato **osservabile** (un'immagine, un suono, un disegno, un file, un
   testo). Non servono ancora funzioni, condizionale, ciclo.
4. **Almeno due programmi di esempio** nel tuo linguaggio, con il risultato che producono
   e un comando per rilanciarli.

Non si chiede una relazione: il `README.md` e il codice bastano.

## Come si valuta

| Voce | Cosa si guarda |
|---|---|
| Scelta e analisi del dominio | Il dominio ha operazioni proprie e non è un pretesto per fare aritmetica con un altro nome. |
| Adeguatezza delle primitive | Le primitive vengono dal dominio, sono giustificate, e la selezione è motivata anche per esclusione. |
| Interprete allo smoke test | Gira, valuta, produce un risultato osservabile. |

## Domini possibili

Un catalogo di partenza. Se vuoi proporne uno tuo, scrivi al docente prima di cominciare.

- **Immagini.** Le costanti sono file; le operazioni trasformano una o più immagini (somma,
  maschere, filtri, soglie). Il risultato è un'immagine.
- **Forme geometriche.** Cerchi, poligoni, curve; unione, intersezione, complemento,
  trasformazioni. Il risultato è un disegno, per esempio un SVG.
- **Grafi.** Grafi definiti da insiemi di archi; unione, intersezione, incollaggio di nodi,
  cammini. Il risultato è un grafo disegnato.
- **Musica.** Note come costanti; concatenazione di battute, accordi, trasposizione,
  ripetizione. Il risultato è una sequenza di eventi nel tempo, esportata in MIDI o audio.
- **Segnali audio.** File audio ed effetti (ritardo, riverbero, filtri) da una libreria
  esistente; interessante avere fra i valori le funzioni del tempo che modulano i parametri.
- **Modelli 3D.** Solidi o mesh; scala, rotazione, deformazione, composizione. Il risultato
  è un file visualizzabile.
- **Testi.** Concatenazione, sostituzione, ripetizione, estrazione. Il risultato è un testo.
- **Processi paralleli.** Un linguaggio come quelli del corso con composizione parallela e
  comunicazione: qui il dominio semantico è la parte interessante.

## Consigli

- Scegli un dominio che conosci o che ti incuriosisce davvero: dovrai parlarne per venti
  minuti alla fine del corso.
- Usa una libreria per il dominio (imaging, audio, grafi, geometria). Il lavoro del corso è
  il linguaggio, non la libreria.
- Gli assistenti AI sono ammessi. Ogni primitiva che consegni deve però essere una che sai
  spiegare, con un esempio in cui serve e uno in cui non basta.
