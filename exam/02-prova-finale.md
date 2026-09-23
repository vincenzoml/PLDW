# Prova finale

**Presentazione pubblica con demo dal vivo: vale due terzi del voto di laboratorio.**
Le regole generali sono in [00-regole](00-regole.html).

## Cosa si consegna

Quindici giorni prima della data di presentazione, un repository contenente:

1. **Il linguaggio completo.** Rispetto alla consegna intermedia, l'interprete supporta
   almeno funzioni, condizionale e ciclo (o i costrutti equivalenti che hanno senso nel
   dominio: per esempio una ripetizione sui campioni di un segnale, o una ricorsione su una
   forma). Se un costrutto del corso non ha senso nel tuo dominio, lo dici e lo motivi.
2. **La visualizzazione.** Il risultato di un programma è qualcosa che una persona può
   guardare e giudicare.
3. **Almeno tre programmi di esempio** che mostrano che il linguaggio serve nel dominio: non
   esercizi travestiti, ma casi in cui qualcuno del dominio riconoscerebbe un problema suo.
4. **Le slide** della presentazione, in formato aperto.
5. **`README.md`** aggiornato: dominio, primitive, decisioni di semantica prese e alternative
   scartate, come lanciare gli esempi.

Chi ha fatto la consegna intermedia estende quel progetto. Cambiare dominio è possibile ma
va concordato, e la consegna intermedia resta votata com'era.

## La presentazione

In aula, davanti agli altri studenti, in date fissate fuori dall'orario delle lezioni.
**Quindici minuti di esposizione, dieci di domande.** Il tetto è rigido. In coppia, la
presentazione è congiunta e le domande vanno a entrambi.

Contenuto obbligatorio:

- il dominio e perché merita un linguaggio;
- le primitive e le decisioni di semantica, con le alternative scartate;
- **demo dal vivo** degli esempi, lanciati dallo studente;
- la visualizzazione dei risultati;
- **virtù e difetti** del linguaggio rispetto a problemi concreti del dominio: cosa risolve
  bene, cosa non sa esprimere, cosa costerebbe troppo aggiungere.

L'ultima voce è la più importante. Chi conosce il proprio sistema ne conosce i limiti.

## Le domande

**Sul codice.** Cosa fa questa primitiva. Perché qui c'è un ambiente. Cosa succede se cambio
questo. Fammi vedere dove è definito il significato di questo costrutto.

**Sulla teoria.** I concetti del programma d'esame: sintassi astratta e concreta, domini
semantici, ambienti, binding e scoping, stato e comandi, controllo di flusso, funzioni e
chiusure — cioè i capitoli 1–8 del libro del corso.

## Come si valuta

| Voce | Cosa si guarda |
|---|---|
| Decisioni di semantica | Sa dire cosa ha scelto, quali erano le alternative, cosa ci ha guadagnato e cosa perso. |
| Padronanza delle primitive | Risponde su qualunque parte del proprio linguaggio, senza consultare. |
| Casi d'uso | Gli esempi mostrano che il linguaggio serve nel dominio. |
| Visualizzazione | Il risultato di un programma è qualcosa che una persona può guardare e giudicare. |
| Esposizione e limiti | Espone in modo chiaro nel tempo dato, e sa dire cosa il proprio linguaggio non sa fare. |
| Teoria | Risponde sui concetti del programma d'esame. |
