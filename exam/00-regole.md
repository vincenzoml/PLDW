# Regole d'esame

Valido **dalla coorte che inizia il 14 settembre 2026**. Chi ha già sostenuto lo scritto
sostiene l'esame del vecchio programma; la transizione è chiusa.

Il voto del laboratorio è **autonomo** e concorre per **un terzo** al voto finale
dell'insegnamento, per peso in crediti. Non si negozia con nessuno: lo assegna il docente
del laboratorio.

## 1. Perché il progetto attuale non regge più

Il testo dell'edizione 2025 (in `docs/archivio/`) chiedeva di progettare e implementare un DSL con
espressioni, `let`, funzioni, condizionale e ciclo, e valuta *il manufatto*: correttezza,
originalità delle primitive, visualizzazione, qualità degli esempi.

Il problema non è che gli studenti barino. È che **il manufatto ha smesso di essere un
segnale.** Dando a un modello l'interprete di riferimento del corso, quel progetto si
completa in un paio d'ore, e il risultato è indistinguibile — anzi, spesso migliore — da
quello di chi ha lavorato tre mesi. Ogni criterio che guarda il codice consegnato valuta
qualcosa che non discrimina più.

Il resto dei difetti discende da lì:

- **Il midterm è facoltativo e vagamente pesato** ("terrà conto della qualità del progetto
  midterm, se svolto"): non c'è un punto di controllo reale a metà corso.
- **L'orale è concepito come verifica difensiva** ("serve a verificare che il progetto sia
  stato svolto personalmente"): è un controllo di autenticità, non una valutazione di
  competenza.
- **Non si valuta mai la capacità di esporre.** Che è invece, oggi, una delle poche cose che
  non si delegano.

## 2. Il principio

Non si certifica il codice prodotto. Si certifica la **padronanza del sistema costruito**.

L'AI è ammessa e presupposta: aiuta a scrivere il DSL, l'interfaccia e gli esempi. Ciò che
resta interamente a carico dello studente — e che è esattamente ciò che si valuta — è:

- conoscere **ogni** primitiva del proprio linguaggio e saperla usare;
- saper **lanciare e spiegare** ogni esempio consegnato;
- saper dire **cosa il proprio DSL fa bene e cosa fa male** su problemi concreti del dominio
  scelto.

Un linguaggio che lo studente non sa spiegare non è il suo linguaggio, chiunque l'abbia
scritto.

## 3. Struttura

I testi delle due prove sono in [01-consegna-intermedia](01-consegna-intermedia.html) e
[02-prova-finale](02-prova-finale.html).

### 3.1 Consegna intermedia — **obbligatoria e votata**

A metà corso. Contiene:

1. **La scelta del dominio applicativo**, con l'analisi: quali sono le entità del dominio,
   quali le operazioni caratteristiche, cosa si vuole poter esprimere.
2. **La selezione delle primitive**, giustificata: perché queste e non altre.
3. **Il primo interprete**, funzionante allo stato di *smoke test*: gira, valuta espressioni
   e `let` nel dominio, produce un risultato osservabile. Non deve avere ancora funzioni,
   condizionale, ciclo.

Chi non consegna non è ammesso alla prova finale.

### 3.2 Prova finale — presentazione pubblica

**Formato:** slide e demo dal vivo, in aula, davanti agli altri studenti, in **date dedicate
fissate fuori dall'orario delle lezioni**. Con 15–20 consegne previste, tutte le
presentazioni stanno in due o tre pomeriggi.

**Durata indicativa:** 15 minuti di esposizione, 10 di domande. Il tetto è rigido.

**Contenuto obbligatorio della presentazione:**

- il dominio e perché merita un linguaggio;
- le primitive e le decisioni di semantica prese, con le alternative scartate;
- **demo dal vivo** degli esempi, lanciati dallo studente;
- la visualizzazione dei risultati;
- **virtù e difetti** del proprio DSL rispetto a problemi concreti del dominio: cosa
  risolve bene, cosa non sa esprimere, cosa costerebbe troppo aggiungere.

**Domande:** su codice e su teoria. Sul codice: cosa fa questa primitiva, perché qui c'è un
ambiente, cosa succede se cambio questo. Sulla teoria: i concetti del programma d'esame
(i capitoli 1–8 del libro del corso).

L'ultima voce — dichiarare i difetti — è la più informativa: chi ha solo fatto generare non
conosce i limiti del proprio sistema, e lo si vede senza bisogno di accusare nessuno.

## 4. Pesi

| Prova | Peso sul voto di laboratorio |
|---|---|
| Consegna intermedia | 1/3 |
| Presentazione finale (esposizione + demo + domande) | 2/3 |

Il voto di laboratorio pesa a sua volta **1/3** sul voto finale dell'insegnamento.

## 5. Griglia di valutazione

Le voci corrispondono uno a uno agli obiettivi di uscita del modulo.

**Consegna intermedia (1/3)**

| Voce | Cosa si guarda |
|---|---|
| Scelta e analisi del dominio | Il dominio ha operazioni proprie e non è un pretesto per fare aritmetica con un altro nome. |
| Adeguatezza delle primitive | Le primitive vengono dal dominio, sono giustificate, e la selezione è motivata anche per esclusione. |
| Interprete allo smoke test | Gira, valuta, produce un risultato osservabile. |

**Presentazione finale (2/3)**

| Voce | Cosa si guarda |
|---|---|
| Decisioni di semantica | Sa dire cosa ha scelto, quali erano le alternative, cosa ci ha guadagnato e cosa perso. |
| Padronanza delle primitive | Risponde su qualunque parte del proprio linguaggio, senza consultare. |
| Casi d'uso | Gli esempi mostrano che il linguaggio serve nel dominio; non sono esercizi travestiti. |
| Visualizzazione | Il risultato di un programma è qualcosa che una persona può guardare e giudicare. |
| Esposizione e limiti | Espone in modo chiaro nel tempo dato, e sa dire cosa il proprio DSL non sa fare. |
| Teoria | Risponde sui concetti del programma d'esame. |

## 6. Regole di consegna

- Progetti **individuali o in coppia**. In coppia, entrambi rispondono su tutto: la
  presentazione è congiunta e le domande vanno a entrambi.
- **Linguaggio:** Python 3.12+ raccomandato. Alternative accettate (F#, Haskell, JavaScript,
  TypeScript); per altri, accordarsi prima.
- **Librerie di dominio incoraggiate** (imaging, audio, grafi, geometria) per i calcoli nel
  dominio semantico.
- **L'uso di assistenti AI è ammesso e atteso.** Non va nascosto e non va dichiarato come
  colpa. Non riduce ciò che viene chiesto in sede di presentazione.
- **Scadenza consegna finale:** di regola 15 giorni prima della data di presentazione.
- Contatto: vincenzo.ciancia@isti.cnr.it — repository: https://github.com/vincenzoml/PLDW
