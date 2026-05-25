# Analyse OpenAI GPT-5-mini

## Overzicht

GPT-5-mini via OpenRouter behaalde **84.2%** op het VWO natuurkunde examen - een drastische verbetering ten opzichte van gpt-4o-mini (38.2%). Het model is nu competitief met de beste lokale 27B+ modellen.

## Score

| Model | Score | Max | % |
|-------|-------|-----|---|
| openai/gpt-5-mini | 64 | 76 | **84.2%** |
| openai/gpt-4o-mini | 29 | 76 | 38.2% |

**Verbetering: +35 punten (+46 procentpunt)**

## Prijsvergelijking

| Model | Input | Output | Relatieve kosten |
|-------|-------|--------|------------------|
| gpt-4o-mini | $0.15/M | $0.60/M | 1x (baseline) |
| gpt-5-mini | $0.25/M | $2.00/M | ~2.5x duurder |

De 2.5x hogere kosten resulteren in 2.2x betere score (84% vs 38%).

## Configuratie

- **Provider**: OpenRouter
- **Temperature**: 1.0 (default)
- **Max tokens**: 32768
- **Gemiddelde solve tijd**: ~25s per vraag

## Vraag-voor-vraag Vergelijking

| Vraag | gpt-5-mini | gpt-4o-mini | Verschil |
|-------|------------|-------------|----------|
| Q01 | 3/3 | 3/3 | = |
| Q02 | 2/2 | 0/2 | **+2** |
| Q03 | 2/2 | 2/2 | = |
| Q04 | 0/2 | 0/2 | = |
| Q05 | 1/3 | 1/3 | = |
| Q06 | 4/4 | 4/4 | = |
| Q07 | 2/3 | 0/3 | **+2** |
| Q08 | 4/4 | 0/4 | **+4** |
| Q09 | 3/3 | 0/3 | **+3** |
| Q10 | 3/3 | 1/3 | **+2** |
| Q11 | 3/3 | 1/3 | **+2** |
| Q12 | 2/3 | 1/3 | +1 |
| Q13 | 3/4 | 1/4 | **+2** |
| Q14 | 2/2 | 1/2 | +1 |
| Q15 | 3/4 | 0/4 | **+3** |
| Q16 | 4/4 | 1/4 | **+3** |
| Q17 | 5/5 | 2/5 | **+3** |
| Q18 | 2/3 | 0/3 | **+2** |
| Q19 | 2/2 | 2/2 | = |
| Q20 | 3/3 | 3/3 | = |
| Q21 | 2/3 | 3/3 | -1 |
| Q22 | 1/3 | 0/3 | +1 |
| Q23 | 3/3 | 3/3 | = |
| Q24 | 2/2 | 0/2 | **+2** |
| Q25 | 3/3 | 0/3 | **+3** |

**gpt-5-mini wint op 17 vragen, verliest op 1 (Q21), gelijk op 7.**

---

## Kritieke Verbeteringen t.o.v. gpt-4o-mini

### 1. Geen "Vraag niet zichtbaar" Fouten
gpt-4o-mini claimde bij Q07 en Q25 dat de vraag niet zichtbaar was. gpt-5-mini heeft dit probleem niet - alle vragen correct gelezen.

### 2. Elektriciteitspracticum: 10/10 vs 1/10
| Vraag | gpt-5-mini | gpt-4o-mini |
|-------|------------|-------------|
| Q08 | 4/4 | 0/4 |
| Q09 | 3/3 | 0/3 |
| Q10 | 3/3 | 1/3 |

gpt-5-mini interpreteert schakelschema's correct, waar gpt-4o-mini volledig faalde.

### 3. Cepheiden: 13/16 vs 3/16
Significante verbetering op astronomievragen die grafiekinterpretatie vereisen.

---

## Resterende Fouten gpt-5-mini

### Q04 (botsproef): 0/2 - Conceptuele fout
**Vraag**: Controleer of Aya's bewering klopt (relatieve beweging duurt 0,34s)

**Vereist**: Vergelijk snelheden van M en S op t=0,34s om te concluderen dat S nog steeds sneller beweegt.

**gpt-5-mini fout**: Interpreteerde "relatieve beweging" als "verschil in positie" in plaats van "verschil in snelheid". Concludeerde ten onrechte dat beweging stopt als posities gelijk zijn.

*Opmerking: gpt-4o-mini maakte dezelfde fout.*

### Q05 (botsproef): 1/3 - Verkeerd tijdsinterval
**Vraag**: Bepaal gemiddelde horizontale vertraging uit grafiek.

**Vereist**: Δt van t=0,040s tot t=0,120s (vertraging van 4 m/s naar 0 m/s)

**gpt-5-mini fout**: Startte bij t=0,00s in plaats van t=0,040s.

### Q22 (linac): 1/3 - Lorentzkracht richting
**Vraag**: Bepaal richting magneetveld en verband met straal.

**gpt-5-mini fout**: Verkeerde richting magneetveld bepaald met rechterhandregel voor elektronen.

*Opmerking: gpt-4o-mini maakte grotere fout (noemde elektron "positief geladen").*

---

## Vergelijking met Alle Modellen

| Model | Score | Opmerking |
|-------|-------|-----------|
| qwen/qwen3.6-27b | 93.4% | Best presterende |
| google/gemma-4-31b | 89.5% | Beste judge |
| qwen/qwen3.6-35b-a3b | 88.2% | |
| **openai/gpt-5-mini** | **84.2%** | Cloud model |
| google/gemma-4-26b-a4b | 82.9% | |
| gemma-4-31b-opus-distill | 56.6% | |
| google/gemma-3-27b-it | 52.6% | |
| google/gemma-4-e4b | 40.8% | |
| openai/gpt-4o-mini | 38.2% | |
| nvidia/nemotron-3-nano-omni | 20.0% | |

---

## Conclusie

**gpt-5-mini is een valide optie voor VWO natuurkunde examens.**

Sterke punten:
1. **Betrouwbare vision** - geen "vraag niet zichtbaar" fouten
2. **Schakelschema's** - correct geïnterpreteerd (10/10 elektriciteitspracticum)
3. **Grafiekanalyse** - significant beter dan gpt-4o-mini
4. **Algemene nauwkeurigheid** - 84.2% is competitief met lokale 27B+ modellen

Zwakke punten:
1. **Conceptuele fysica** - sommige subtiele fouten (Q04 relatieve beweging)
2. **Lorentzkracht** - rechterhandregel voor negatieve ladingen lastig
3. **Kosten** - 2.5x duurder dan gpt-4o-mini

### Aanbeveling

Voor cloud-gebaseerde evaluatie is gpt-5-mini de beste OpenAI optie. De hogere kosten zijn gerechtvaardigd door de 2.2x betere score. Voor maximale nauwkeurigheid blijven lokale modellen (qwen3.6-27b, gemma-4-31b) superieur én gratis na hardware-investering.
