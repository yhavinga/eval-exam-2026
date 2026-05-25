# Analyse OpenAI GPT-4o-mini

## Overzicht

GPT-4o-mini via OpenRouter behaalde **38.2%** op het VWO natuurkunde examen. Dit is lager dan verwacht voor een OpenAI model en plaatst het onderaan de ranking, zelfs onder de kleinste lokale modellen.

## Score

| Model | Score | Max | % |
|-------|-------|-----|---|
| openai/gpt-4o-mini | 29 | 76 | **38.2%** |

## Configuratie

- **Provider**: OpenRouter
- **Temperature**: 0.2 (recommended for accuracy)
- **Max tokens**: 4096
- **Gemiddelde solve tijd**: ~20s per vraag
- **Totale solve tijd**: ~8 minuten (25 vragen)

## Resultaten per Vraag

| Vraag | Score | Topic | Opmerking |
|-------|-------|-------|-----------|
| Q01 | 3/3 ✓ | botsproef | |
| Q02 | 0/2 ✗ | botsproef | |
| Q03 | 2/2 ✓ | botsproef | |
| Q04 | 0/2 ✗ | botsproef | |
| Q05 | 1/3 | botsproef | |
| Q06 | 4/4 ✓ | botsproef | |
| Q07 | 0/3 ✗ | botsproef | **"Vraag niet zichtbaar"** |
| Q08 | 0/4 ✗ | elektriciteitspracticum | |
| Q09 | 0/3 ✗ | elektriciteitspracticum | Schakelschema fout |
| Q10 | 1/3 | elektriciteitspracticum | |
| Q11 | 1/3 | cepheiden | |
| Q12 | 1/3 | cepheiden | |
| Q13 | 1/4 | cepheiden | |
| Q14 | 1/2 | cepheiden | |
| Q15 | 0/4 ✗ | cepheiden | |
| Q16 | 1/4 | morphodidius | |
| Q17 | 2/5 | morphodidius | |
| Q18 | 0/3 ✗ | morphodidius | |
| Q19 | 2/2 ✓ | linac | |
| Q20 | 3/3 ✓ | linac | |
| Q21 | 3/3 ✓ | linac | |
| Q22 | 0/3 ✗ | linac | |
| Q23 | 3/3 ✓ | linac | |
| Q24 | 0/2 ✗ | linac | |
| Q25 | 0/3 ✗ | linac | **"Vraag niet zichtbaar"** |

**Verdeling**: 7 perfect, 8 partieel, 10 nul

---

## Kritieke Problemen

### 1. Vision Failures - "Vraag niet zichtbaar"

Bij Q07 en Q25 claimde het model dat de vraag niet zichtbaar was:

**Q07 antwoord:**
> "Het lijkt erop dat je vraag 07 niet is weergegeven. Zou je de details of context van vraag 07 kunnen delen, zodat ik je kan helpen?"

**Q25 antwoord:**
> "Het lijkt erop dat je vraag 25 niet zichtbaar is. Zou je de inhoud van vraag 25 kunnen delen, zodat ik je kan helpen?"

Dit is een fundamenteel vision-probleem vergelijkbaar met nvidia/nemotron-3-nano-omni, maar minder ernstig (2 vs 25 vragen).

### 2. Hoog Aantal Zero Scores

10 van 25 vragen (40%) kregen 0 punten. Dit is veel hoger dan de beste modellen:
- qwen/qwen3.6-27b: ~2-3 zeros
- gpt-4o-mini: 10 zeros

### 3. Elektriciteitspracticum Compleet Gefaald

Alle 3 vragen over schakelschema's scoorden slecht:
- Q08: 0/4
- Q09: 0/3
- Q10: 1/3

Het model heeft moeite met het interpreteren van elektrische schakelingen in afbeeldingen.

---

## Vergelijking met Andere Modellen

| Model | Score | Opmerking |
|-------|-------|-----------|
| qwen/qwen3.6-27b | 93.4% | Best presterende |
| google/gemma-4-31b | 89.5% | Beste judge |
| qwen/qwen3.6-35b-a3b | 88.2% | |
| google/gemma-4-26b-a4b | 82.9% | |
| gemma-4-31b-opus-distill | 56.6% | |
| google/gemma-3-27b-it | 52.6% | |
| google/gemma-4-e4b | 40.8% | |
| **openai/gpt-4o-mini** | **38.2%** | |
| nvidia/nemotron-3-nano-omni | 20.0% | |

GPT-4o-mini presteert slechter dan alle lokale modellen behalve nemotron.

---

## Sterke Punten

Het model scoorde perfect op 7 vragen:
- Q01, Q03, Q06 (botsproef)
- Q19, Q20, Q21, Q23 (linac)

De linac-vragen gingen relatief goed (11/16 = 69%).

---

## Kosten vs Prestaties

- **Solve kosten**: ~$0.02 voor 25 vragen (geschat)
- **Snelheid**: ~20s per vraag via OpenRouter

Vergeleken met lokale inferentie:
- Lokale modellen zijn gratis na hardware-investering
- Lokale 27B modellen scoren 2.5x beter (93% vs 38%)

---

## Conclusie

**Niet aanbevolen voor VWO natuurkunde examens.**

GPT-4o-mini heeft significante problemen met:
1. **Vision reliability** - soms claimt het dat vragen niet zichtbaar zijn
2. **Schakelschema interpretatie** - elektriciteitsvragen falen consistent
3. **Overall accuracy** - 38% is onvoldoende voor examendoeleinden

### Mogelijke Oorzaken

1. **Model size**: gpt-4o-mini is geoptimaliseerd voor snelheid/kosten, niet accuracy
2. **Vision training**: mogelijk minder getraind op technische diagrammen
3. **Nederlandse taal**: mogelijk minder sterk in Nederlands dan Engels

### Aanbeveling

Gebruik lokale modellen (qwen3.6-27b, gemma-4-31b) voor VWO examens. Deze zijn:
- Gratis na hardware
- 2-3x nauwkeuriger
- Betrouwbaarder voor vision-taken
