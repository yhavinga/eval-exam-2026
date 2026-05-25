# Analyse Nvidia Nemotron-3-Nano-Omni Fouten

## Overzicht

Nvidia Nemotron-3-Nano-Omni behaalde slechts **20.0%** op het VWO natuurkunde examen - de **laagste score** van alle geteste modellen. Het model heeft een fundamenteel **vision-probleem**: het kan tekst in examafbeeldingen niet lezen.

## Score

| Judge | Score | Max | % |
|-------|-------|-----|---|
| google/gemma-4-31b | 13 | 65 | **20.0%** |

*3 vragen (Q05, Q08, Q15) werden niet beoordeeld wegens lege antwoorden*

## Vergelijking met Andere Modellen

| Model | Score |
|-------|-------|
| qwen/qwen3.6-27b | 93.4% |
| google/gemma-4-31b | 89.5% |
| qwen/qwen3.6-35b-a3b | 88.2% |
| google/gemma-4-26b-a4b | 82.9% |
| gemma-4-31b-opus-distill | 56.6% |
| google/gemma-3-27b-it | 52.6% |
| **nvidia/nemotron-3-nano-omni** | **20.0%** |

## Verloren Punten Overzicht

| Type Fout | Vragen | Punten Verloren |
|-----------|--------|-----------------|
| "Not answerable" | Q01, Q02 | 5 |
| Lege antwoorden | Q05, Q08, Q15, Q18 | ~13 |
| Verkeerde vraag beantwoord | Q09-Q13, Q16-Q17, Q20, Q22-Q25 | ~34 |
| **Correct beantwoord** | Q03, Q06, Q14, Q19, Q21 | **13 punten gescoord** |

---

## Kritieke Fouten

### "Not Answerable" Responses (Q01, Q02)

**Symptoom**: Model antwoordt letterlijk "Not answerable"

**Q01 Voorbeeld**:
```
The question is to "Los dit op" which translates from Dutch as "Solve this".
However, the image provided (Figure 1) only contains a diagram...
Since there is no explicit question with specific parameters needed for
calculation visible in the image beyond what's already stated (v=4.0 m/s),
this task as presented is unsolvable...
```

**Realiteit**: De vraag "Bereken op welke hoogte h boven het laagste punt de stoel is losgelaten" staat **duidelijk leesbaar** in de afbeelding.

**Oorzaak**: Het model kan de **tekst in de PNG-afbeelding niet lezen**. Het ziet alleen de grafische elementen (figuur, pijlen, labels) maar niet de vraagstelling eronder.

---

### Lege Antwoorden (Q05, Q08, Q15, Q18)

Het model produceerde geen bruikbaar antwoord voor deze vragen:
- Response veld leeg of None
- Judge kon niet beoordelen (None/None)

Dit zijn waarschijnlijk gevallen waar het model:
1. De vraag niet kon identificeren (vision-probleem)
2. Of vastliep tijdens het genereren

---

### Verkeerde Vraag Beantwoord

Meerdere antwoorden refereren aan verkeerde vraagnummers of contexten:

**Q11 (Cepheiden)**:
```
Based on the text provided in the image under "figuur 1"...
```
De vraag gaat over figuur 3 en de Cepheïden-context, niet figuur 1.

**Q12**:
```
Based on the text below **Figuur 3** in the provided image...
```
Het model leest blijkbaar een andere afbeelding of verwart de context.

---

### Context-Afhankelijke Successen

De **enige correcte antwoorden** waren vragen waar het model profiteerde van context uit eerdere Q&A in hetzelfde topic:

| Vraag | Score | Waarom Correct |
|-------|-------|----------------|
| Q03 | 2/2 | Bouwde voort op Q01/Q02 context over botsproef |
| Q06 | 4/4 | Context accumulation binnen topic |
| Q14 | 2/2 | Eerdere vragen over Cepheïden gaven context |
| Q19 | 2/2 | Eerste vraag linac-topic met heldere afbeelding |
| Q21 | 2/3 | Context van Q19/Q20 hielp |

---

## Fundamenteel Probleem: Vision Capabilities

### Test: Q01 Afbeelding

De afbeelding `01_botsproef.png` bevat duidelijk leesbare tekst:
> "1 Bereken op welke hoogte h boven het laagste punt de stoel is losgelaten. Verwaarsloos daarbij de wrijvingskracht."

**Andere modellen** (gemma-4-31b, qwen3.6-27b, etc.) lezen deze tekst correct en beantwoorden de vraag.

**Nemotron** ziet alleen:
- De figuur met de bobslee
- Labels zoals "v = 4,0 m/s"
- Maar **niet** de vraagstelling

### Implicatie

Het model is niet geschikt voor taken waarbij tekst uit afbeeldingen gelezen moet worden. Dit is een fundamentele beperking van de vision-encoder, niet een probleem met de taalkundige of redeneer-capabilities.

---

## Solve Timing

Opvallend aan de solve-tijden:

| Vraag | Tijd | Opmerking |
|-------|------|-----------|
| Q01 | 2.2s | Supersnel → direct "Not answerable" |
| Q02 | 4.2s | Supersnel → direct "Not answerable" |
| Q05 | 223s | Lang → maar leeg antwoord |
| Q08 | 220s | Lang → maar leeg antwoord |

De snelle tijden voor Q01/Q02 suggereren dat het model direct besloot dat het de vraag niet kon beantwoorden, zonder serieuze poging tot reasoning.

---

## Conclusie

**Niet bruikbaar voor VWO examen evaluatie.**

Nvidia Nemotron-3-Nano-Omni heeft een fundamentele beperking: het kan **tekst in afbeeldingen niet lezen**. Dit maakt het model ongeschikt voor:
- Examenvragen waar de vraagstelling in de afbeelding staat
- Elke taak die OCR-achtige capabilities vereist

### Positieve Punten
- Snelle inferentie-tijden
- Correct output-formaat (reasoning_content gescheiden van content)
- Wanneer context beschikbaar is, kan het model wel redeneren

### Aanbeveling
Gebruik dit model **niet** voor vision-taken met tekst in afbeeldingen. Voor pure tekst-taken of taken met alleen grafische elementen zou het mogelijk wel bruikbaar zijn.
