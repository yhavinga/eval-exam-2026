# Analyse OpenAI GPT-4o

## Overzicht

GPT-4o via OpenRouter behaalde **57.9%** op het VWO natuurkunde examen. Dit is onverwacht laag voor OpenAI's flagship model - het scoort significant slechter dan gpt-5-mini (84.2%) en zelfs slechter dan veel kleinere lokale modellen.

## Score

| Model | Score | Max | % |
|-------|-------|-----|---|
| openai/gpt-4o | 44 | 76 | **57.9%** |

## Prijsvergelijking OpenAI Modellen

| Model | Input | Output | Score | Prijs/Punt |
|-------|-------|--------|-------|------------|
| gpt-4o-mini | $0.15/M | $0.60/M | 38.2% | baseline |
| gpt-5-mini | $0.25/M | $2.00/M | 84.2% | beste waarde |
| gpt-4o | $2.50/M | $10.00/M | 57.9% | ~17x duurder, slechter |

**gpt-4o is ~17x duurder dan gpt-4o-mini maar scoort slechts 1.5x beter.**
**gpt-5-mini is ~2.5x duurder dan gpt-4o-mini maar scoort 2.2x beter.**

## Configuratie

- **Provider**: OpenRouter
- **Temperature**: 0.2
- **Max tokens**: 16384
- **Gemiddelde solve tijd**: ~12s per vraag

## Resultaten per Vraag

| Vraag | Score | gpt-5-mini | gpt-4o-mini | Probleem |
|-------|-------|------------|-------------|----------|
| Q01 | 3/3 ✓ | 3/3 | 3/3 | |
| Q02 | 1/2 | 2/2 | 0/2 | |
| Q03 | 2/2 ✓ | 2/2 | 2/2 | |
| Q04 | 0/2 ✗ | 0/2 | 0/2 | Conceptueel (alle modellen) |
| Q05 | 1/3 | 1/3 | 1/3 | Tijdsinterval |
| Q06 | 0/4 ✗ | 4/4 | 4/4 | **Formule niet afgeleid** |
| Q07 | 0/3 ✗ | 2/3 | 0/3 | **"Vraag niet zichtbaar"** |
| Q08 | 4/4 ✓ | 4/4 | 0/4 | |
| Q09 | 3/3 ✓ | 3/3 | 0/3 | |
| Q10 | 2/3 | 3/3 | 1/3 | |
| Q11 | 2/3 | 3/3 | 1/3 | |
| Q12 | 1/3 | 2/3 | 1/3 | |
| Q13 | 3/4 | 3/4 | 1/4 | |
| Q14 | 2/2 ✓ | 2/2 | 1/2 | |
| Q15 | 1/4 | 3/4 | 0/4 | |
| Q16 | 3/4 | 4/4 | 1/4 | |
| Q17 | 4/5 | 5/5 | 2/5 | |
| Q18 | 2/3 | 2/3 | 0/3 | |
| Q19 | 2/2 ✓ | 2/2 | 2/2 | |
| Q20 | 3/3 ✓ | 3/3 | 3/3 | |
| Q21 | 2/3 | 2/3 | 3/3 | |
| Q22 | 0/3 ✗ | 1/3 | 0/3 | Lorentzkracht |
| Q23 | 3/3 ✓ | 3/3 | 3/3 | |
| Q24 | 0/2 ✗ | 2/2 | 0/2 | |
| Q25 | 0/3 ✗ | 3/3 | 0/3 | **"Vraag niet zichtbaar"** |

**Totaal: 8 perfecte scores, 17 met puntenverlies**

---

## Kritieke Problemen

### 1. Vision Failures - "Vraag niet zichtbaar" (Q07, Q25)

Identiek aan gpt-4o-mini claimt gpt-4o dat bepaalde vragen niet zichtbaar zijn:

**Q07:**
> "Natuurlijk, maar ik heb de details van vraag 07 nodig om je te helpen. Kun je die geven?"

**Q25:**
> "Natuurlijk, maar ik heb de vraag niet gezien. Kun je die alsjeblieft geven?"

Dit is verrassend - gpt-5-mini heeft dit probleem niet.

### 2. Q06: Formule Gebruiken vs Afleiden (0/4)

**Vraag**: Leid formule (1) af: $a_x = \frac{v_b^2}{2s}$

**gpt-4o antwoord**: Gebruikte direct de kinematische formule $v^2 = u^2 + 2as$ en loste op.

**Correctievoorschrift vereist**:
- **Methode 1 (Energie)**: W = ΔEk, F·s = ½mv², F = ma → afleiden
- **Methode 2 (Kinematica)**: a = Δv/Δt, s = v_gem·Δt, v_gem = ½vb → afleiden

**Probleem**: gpt-4o citeert een bekende formule in plaats van deze af te leiden uit eerste principes. Dit is een fundamenteel misverstand van wat "afleiden" betekent.

**Opvallend**: gpt-5-mini en gpt-4o-mini scoorden beide 4/4 op deze vraag.

### 3. Linac-vragen: Meerdere Nullen (Q22, Q24, Q25)

De laatste vragen van het linac-topic gingen slecht:
- Q22: 0/3 (Lorentzkracht richting)
- Q24: 0/2
- Q25: 0/3 (vision failure)

---

## Vergelijking OpenAI Modellen

| Aspect | gpt-4o | gpt-5-mini | gpt-4o-mini |
|--------|--------|------------|-------------|
| Score | 57.9% | **84.2%** | 38.2% |
| Vision failures | 2 (Q07, Q25) | 0 | 2 (Q07, Q25) |
| Q06 (afleiden) | 0/4 | 4/4 | 4/4 |
| Elektriciteitspracticum | 9/10 | 10/10 | 1/10 |
| Prijs (input) | $2.50/M | $0.25/M | $0.15/M |
| Prijs (output) | $10.00/M | $2.00/M | $0.60/M |

**Paradox**: Het duurste model (gpt-4o) presteert slechter dan het goedkopere gpt-5-mini.

---

## Vergelijking met Alle Modellen

| Model | Score | Opmerking |
|-------|-------|-----------|
| qwen/qwen3.6-27b | 93.4% | Best presterende |
| google/gemma-4-31b | 89.5% | Beste judge |
| qwen/qwen3.6-35b-a3b | 88.2% | |
| openai/gpt-5-mini | 84.2% | Beste OpenAI |
| google/gemma-4-26b-a4b | 82.9% | |
| **openai/gpt-4o** | **57.9%** | |
| gemma-4-31b-opus-distill | 56.6% | |
| google/gemma-3-27b-it | 52.6% | |
| google/gemma-4-e4b | 40.8% | |
| openai/gpt-4o-mini | 38.2% | |

---

## Conclusie

**gpt-4o is niet aanbevolen voor VWO natuurkunde examens.**

Kritieke problemen:
1. **Vision failures** - zelfde probleem als gpt-4o-mini op Q07 en Q25
2. **Afleidingsvragen** - begrijpt niet wat "afleiden" betekent (Q06)
3. **Slechte prijs/prestatie** - 17x duurder dan gpt-4o-mini, slechts 1.5x beter
4. **Slechter dan gpt-5-mini** - het nieuwere, goedkopere model presteert beter

### Aanbeveling

Gebruik **gpt-5-mini** als cloud-model nodig is:
- 84.2% vs 57.9% score
- ~5x goedkoper ($0.25+$2 vs $2.50+$10)
- Geen vision failures

Voor maximale nauwkeurigheid: lokale modellen (qwen3.6-27b: 93.4%)
