# PROGETTO INTERMEDIO: Implementazione di un Linguaggio Specifico di Dominio

**Scadenza:** 28 Aprile 2025

## Panoramica del Progetto

In questo progetto intermedio è richiesto di progettare e implementare un Linguaggio Specifico di Dominio (Domain-Specific Language o DSL) e in particolare, nel midterm, costituito da espressioni e let binding, focalizzato su un dominio applicativo a scelta. Il compito si basa sui concetti trattati nelle prime cinque lezioni, tra cui:

- Principi fondamentali della progettazione di linguaggi di programmazione
- Tipi e pattern matching strutturale
- Interpreti e alberi sintattici astratti
- Domini semantici e interpretazione basata su ambienti
- Binding di nomi
- Linguaggio delle espressioni e sua valutazione ricorsiva

## Implementazione

### 1. Selezione di un Dominio Applicativo

Scegliere un dominio applicativo, ad esempio uno dei seguenti. È possibile contattare il docente per consigli nel caso si intenda sviluppare un tema diverso:

- **Elaborazione di Immagini**: Creare un linguaggio per manipolare immagini, dove le costanti sono nomi di file e le operazioni trasformano una o più immagini (es. somma di immagini, applicazione di maschere). Le variabili rappresentano immagini, e la semantica produce immagini risultanti.

- **Forme Geometriche**: Sviluppare un linguaggio per operazioni su forme geometriche (es. cerchi, poligoni, forme irregolari), supportando operazioni come unione, intersezione, complemento, o altre ritenute interessanti. Ogni forma è descritta da punti e misure appropriate. Il risultato della valutazione semantica è una rappresentazione astratta delle figure risultanti (es: una lista di polilinee).

- **Operazioni su Grafi**: Implementare un linguaggio per grafi non diretti definiti come insiemi di coppie, supportando intersezione, unione e altre operazioni sui grafi. Le variabili possono denotare nodi o insiemi di nodi, e ci possono essere operazioni di "incollaggio" fra grafi diversi identificando nodi che devono essere identificati. Il risultato della valutazione è un grafo.

- **Composizione Musicale**: Creare un linguaggio per composizione musicale con note come costanti, e operazioni come concatenazione di battute, armonia (diverse note suonate contemporaneamente), creazione di accordi e trasposizione. Il risultato della valutazione è una sequenza di insiemi di note indiciata dal tempo.

- **Elaborazione di segnali audio**: Creare un linguaggio per manipolare file audio e applicare effetti, usando una libreria esistente, ad esempio delay, riverbero, ecc. In questo caso è interessante avere come valori nel dominio semantico le funzioni del tempo, che possano poi essere applicate ai parametri degli effetti per modularli (ad esempio: cambiare l'ampiezza del segnale in accordo con "sin(1/t)"). 

- **Modellazione 3D**: Progettare un linguaggio per descrivere complessi simpliciali (triangolazioni di poliedri) con trasformazioni come scala, rotazione, deformazione e composizione. Il risultato della valutazione è un complesso simpliciale.

- **Manipolazione di testi**: 
Sviluppare un linguaggio per operazioni su testo che includa concatenazione, sostituzione di stringhe per espressioni, ripetizione k volte e altre operazioni. La valutazione produce il testo finale.

- **Calcolo di processo parallelo**: Sviluppare la semantica di un linguaggio simile a quelli visti a lezione, ma con costrutto di composizione parallela e comunicazione. 

### 2. Requisiti 

L'implementazione del DSL deve includere:

- **Struttura Lessicale e Sintattica**: Definire una sintassi chiara per il DSL
- **Albero Sintattico Astratto (AST)**: Progettare strutture dati per rappresentare programmi nel DSL
- **Domini Semantici**: Creare tipi appropriati per i valori nel dominio
- **Interprete**: Implementare un interprete basato su ambienti che valuti i programmi DSL
- **Programmi di Esempio**: Fornire almeno tre programmi di esempio nel DSL

## Linee Guida per la Consegna

- I progetti possono essere completati individualmente o in coppie
- Il codice deve essere ben documentato con spiegazioni chiare delle decisioni di progettazione, anche se non si richiede di commentare il codice riga per riga (anzi, si sconsiglia di farlo)
- Includere un file README.md che spieghi la progettazione del DSL, l'approccio di implementazione e gli esempi

## Criteri di Valutazione

Il progetto sarà valutato in base a:

- **Progettazione del Linguaggio**: Adeguatezza dei costrutti linguistici per il dominio scelto
- **Qualità dell'Implementazione**: Correttezza, chiarezza e organizzazione del codice
- **Documentazione**: Qualità delle spiegazioni e degli esempi

## Linguaggi e Strumenti

- Python 3.12+ è il linguaggio utilizzato nel corso e raccomandato per il progetto.

- Linguaggi alternativi (F#, Haskell, JavaScript, TypeScript) sono anch'essi accettati; per altri linguaggi discutere prima con il docente.

- È possibile e consigliabile utilizzare librerie standard appropriate al dominio per i calcoli nel dominio semantico (es primitive di imaging), ma l'elaborato deve essere svolto in autonomia.

## Note Importanti

- Questo progetto intermedio è progettato per confluire nel progetto finale, che aggiungerà al linguaggio gli argomenti studiati nella seconda parte del corso.

- E' importante sviluppare la **Visualizzazione del Dominio**: implementazione di funzionalità per visualizzare o renderizzare i risultati dei programmi DSL (es. visualizzare immagini, riprodurre musica, visualizzare grafi, mostrare una rappresentazione astratta della semantica di un linguaggio concorrente... ), e alcuni esempi che mostrino l'utilità di scrivere ad esempio un ciclo while nel dominio applicativo.

- Al progetto (alle sue parti se diviso in midterm e consegna finale) sarà dato un voto .

- L'esame orale serve a verificare che il progetto sia stato svolto personalmente e che la sua struttura sia ben compresa, e a verificare che le competenze descritte nelle note del corso siano state acquisite (File course_book.pdf nel repository del progetto).

- Il repository del progetto con i materiali del corso è disponibile all'indirizzo: https://github.com/vincenzoml/PLDW

- Per qualunque chiarimento contattare il docente all'indirizzo e-mail vincenzo.ciancia@isti.cnr.it

