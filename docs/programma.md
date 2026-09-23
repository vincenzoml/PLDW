# Programma — Laboratorio di Linguaggi di Programmazione (LPL)

**Modulo:** laboratorio, 3 CFU, una lezione a settimana.
**Inizio:** 14 settembre 2026.
**Docente:** Vincenzo Ciancia.

## 0. Statuto del modulo

Il laboratorio è un **modulo autonomo** (decisione del 4 settembre 2026). È collegato al
modulo di teoria (6 CFU, Fabio Gadducci) come *conseguenza*, non come sua implementazione:
non ne segue l'ordine, non ne è la parte pratica. La valutazione è autonoma e pesata sui
crediti: il laboratorio vale **un terzo del voto finale**. Questa decisione non si riapre.

Il nuovo programma vale dalla coorte che inizia il 14 settembre 2026. Chi ha già sostenuto
lo scritto sostiene l'esame del vecchio programma. La transizione è chiusa, non ci sono casi
particolari da gestire.

## 1. La diagnosi: perché si cambia

Il programma tecnico dell'edizione precedente non era sbagliato. Erano sbagliate due cose
attorno:

1. **Il corso annoiava.** Otto lezioni di costruzione incrementale dello stesso interprete,
   senza che si vedesse mai perché valesse la pena costruirlo.
2. **L'AI ha svuotato il compito.** Il progetto d'esame — progettare e implementare un DSL
   con espressioni, binding, funzioni, condizionale e ciclo — si esegue oggi in due ore
   dando in pasto a un modello l'interprete di riferimento del corso. Il manufatto non
   distingue più chi ha capito da chi ha copiato.

La risposta **non** è irrigidire il divieto, né cambiare i contenuti tecnici. È spostare ciò
che viene certificato: dal *codice prodotto* alla *padronanza del sistema costruito*.

## 2. La cornice: DSL come strato di controllo umano

La tesi che tiene insieme il modulo:

- **DSL come augmented AI.** Un linguaggio di dominio è il modo in cui una persona conserva
  il controllo su un sistema automatico: ristretto, leggibile, ispezionabile, ri-eseguibile.
- **AI + DSL come human-centric autonomous computing.** L'automazione utile non è quella che
  produce codice arbitrario, ma quella che opera dentro un vocabolario che un umano ha
  progettato, sa leggere e sa difendere.

Questa è la **motivazione** del modulo, non un requisito di implementazione: non si chiede
allo studente di mettere un modello dentro il proprio DSL.

**Dove sta l'AI, operativamente:** nella toolchain. L'AI aiuta a scrivere il DSL,
l'interfaccia e gli esempi. Non è vietata, è presupposta. Ciò che resta interamente a carico
dello studente è conoscere ogni primitiva del proprio linguaggio, saperla usare, saper
lanciare e spiegare ogni esempio, e saper esporre virtù e difetti del proprio DSL rispetto a
problemi concreti del dominio scelto.

## 3. Obiettivi di uscita

Uno studente che ha superato il laboratorio sa fare queste cose, che prima non sapeva fare:

1. **Decidere la semantica.** Scegliere fra alternative reali di progetto (cosa è
   denotabile, come si valuta, cosa è espressione e cosa comando, quale disciplina di
   scoping) e dire cosa si guadagna e cosa si perde con ciascuna.
2. **Scegliere e analizzare un dominio applicativo.** Individuare un dominio, capirne le
   operazioni caratteristiche, e derivarne un insieme di primitive che sia adeguato — non
   arbitrario.
3. **Fornire casi d'uso credibili.** Costruire esempi che mostrino che il linguaggio serve a
   qualcosa nel dominio, non esempi-giocattolo che dimostrano solo che l'interprete gira.
4. **Visualizzare i risultati.** Rendere osservabile il dominio semantico: l'esito di un
   programma dev'essere qualcosa che una persona può guardare e giudicare.
5. **Presentare e spiegare il sistema.** Esporre il proprio linguaggio, giustificarne le
   scelte, rispondere su qualunque primitiva, e dichiararne i limiti.

## 4. Il filo delle lezioni

Impianto: **nove lezioni da 90 minuti**, più una lezione di chiusura (la lezione 11) su
VoxLogicA. Il programma tecnico resta quello dell'edizione precedente. Si aggiungono tre
parti che **non fanno parte del programma d'esame**: la motivazione, che apre il corso, una
lezione sul metodo di lavoro, e il caso completo di VoxLogicA, promesso nella lezione 1.

| # | Tema | In esame |
|---|------|----------|
| 1 | Due parti, due deck, due capitoli. **Parte A — Perché costruire un linguaggio** (`book/00-why-a-language.md`, `slides/00-why-a-language.html`): i linguaggi formali prima dei computer (Chomsky, linguistica computazionale, IA simbolica, in breve), semantica dei programmi, il caso dei tumori cerebrali con VoxLogicA senza entrare nella tecnica, la promessa della lezione finale. Il corso non è un corso di IA: è complementare. **Parte B — Cos'è fatto un linguaggio** (`book/01-introduction.md`, `slides/01-introduction.html`): sintassi e semantica in quaranta righe di Python, come funziona il corso e l'esame. | A no, B sì |
| 2 | Tipi e pattern matching strutturale in Python | sì |
| 3 | **AI-assisted coding e GitHub.** Come si lavora davvero: repository, cronologia, revisione del generato, specifica prima del codice. Serve a mettere gli studenti in condizione di costruire; non si valuta. | no |
| 4 | Implementazione: un mini-interprete (parsing, AST, valutazione) | sì |
| 5 | Domini semantici e interpreti basati su ambienti | sì |
| 6 | Binding e scoping | sì |
| 7 | Stato e comandi | sì |
| 8 | Controllo di flusso | sì |
| 9 | Funzioni e closure | sì |
| 11 | **Un linguaggio vero: logica spaziale e VoxLogicA.** Spazi di chiusura come dominio semantico, la logica SLCS, il model checker come interprete (memoizzazione, condivisione massimale, parallelismo), l'imaging medico, la critica alle metriche, VoxLogicA 2 e l'IA ibrida, un metodo di lavoro iterativo. Dalle dispense 2024 per il corso di Gadducci e dai talk pubblici 2025–2026. Scritta: `book/11-spatial-logic-and-voxlogica.md`. | no |

### Note sulla collocazione

- La lezione 1 **apre con la motivazione**: è la risposta alla domanda "perché mi
  interessa", che nell'edizione precedente non veniva mai data. Parte A e parte B hanno
  capitoli e deck separati, così i concetti non si mescolano.
- I numeri dei capitoli del libro seguono gli argomenti (0–8, più 11), quelli delle lezioni
  il calendario: la lezione 3 (AI-assisted coding) non ha capitolo nel libro, per cui dalla
  lezione 4 in poi il capitolo è la lezione meno uno.
- Il libro è stato riscritto a settembre 2026 come testo aperto sulla scrittura di interpreti
  (`book/STYLE.md` dice come): prosa, motivazioni prima del come, decisioni e alternative,
  codice che gira. Le slide sono scritte a parte, in HTML5, una lezione alla volta. La
  struttura del repository e il modo di pubblicare sono in `docs/repository.md`.
- La lezione 3 (AI-assisted coding e GitHub) è collocata **presto** di proposito: gli
  studenti devono poter cominciare a costruire il proprio DSL con gli strumenti giusti,
  e la consegna intermedia arriva a metà corso.

## 5. Vincolo di riservatezza sulle lezioni 1 e 11

Il materiale dell'esperimento in corso è non pubblicato e sta in un repository privato.
Il repository PLDW è **pubblico**.

**Decisione (7 settembre 2026): nel repository pubblico non entra nulla del manoscritto.**
I capitoli `book/00-why-a-language.md` e `book/11-spatial-logic-and-voxlogica.md` sono scritti
rispettando questo vincolo: si appoggiano solo a lavoro pubblicato, e dell'esperimento in
corso la lezione 11 racconta il metodo, mai i risultati.
Non numeri, non figure, non registri di sviluppo, non testo. La lezione 11 si tiene con un
**deck di slide scritto apposta**, indipendente dal manoscritto: racconta il metodo — un
ciclo di lavoro iterativo: prima la specifica in prosa, poi la misura, poi il codice — e perché il linguaggio di dominio è la parte che rende il ciclo
possibile. Nessun risultato non pubblicato viene mostrato.
