# Analyse Mistral Large 2512

## Overzicht

Mistral Large 2512 via OpenRouter behaalde **59.2%** op het VWO natuurkunde examen. Het model heeft een fundamentele beperking: maximaal 8 afbeeldingen per context, waardoor 4 vragen geforceerd 0 punten kregen.

## Score

| Metric | Score |
|--------|-------|
| Totaal | 45/76 = **59.2%** |
| Excl. image-limit errors | 45/64 = **70.3%** |

## Prijzen

| | Prijs |
|---|-------|
| Input | $0.50/M tokens |
| Output | $1.50/M tokens |

Goedkoper dan alle OpenAI modellen behalve gpt-4o-mini.

## Configuratie

- **Provider**: OpenRouter
- **Temperature**: 0.15 (recommended)
- **Max tokens**: 16384
- **Gemiddelde solve tijd**: ~15s per vraag

## Image Limit Probleem

Mistral Large heeft een **hard limit van 8 afbeeldingen** per API call. De eval-architectuur bouwt conversatie-context op per topic:

```
Topic: botsproef (7 vragen)
  Q01: 1 image  → ctx=2 msgs (1 img)
  Q02: 2 images → ctx=4 msgs (3 imgs)
  ...
  Q07: 1 image  → ctx=14 msgs (9+ imgs) → ERROR
```

**Gefaalde vragen door image limit:**
- Q07 (botsproef) - 7e vraag in topic
- Q15 (cepheiden) - 5e vraag in topic
- Q24, Q25 (linac) - 6e en 7e vraag in topic

**Verloren punten**: 12 (3+4+2+3)

## Resultaten per Vraag

| Vraag | Score | Opmerking |
|-------|-------|-----------|
| Q01 | 3/3 ✓ | |
| Q02 | 1/2 | |
| Q03 | 2/2 ✓ | |
| Q04 | 0/2 ✗ | Conceptueel (alle modellen) |
| Q05 | 0/3 ✗ | |
| Q06 | 4/4 ✓ | |
| Q07 | 0/3 ✗ | **IMAGE LIMIT ERROR** |
| Q08 | 4/4 ✓ | |
| Q09 | 0/3 ✗ | |
| Q10 | 1/3 | |
| Q11 | 3/3 ✓ | |
| Q12 | 3/3 ✓ | |
| Q13 | 4/4 ✓ | |
| Q14 | 2/2 ✓ | |
| Q15 | 0/4 ✗ | **IMAGE LIMIT ERROR** |
| Q16 | 1/4 | |
| Q17 | 4/5 | |
| Q18 | 2/3 | |
| Q19 | 2/2 ✓ | |
| Q20 | 3/3 ✓ | |
| Q21 | 3/3 ✓ | |
| Q22 | 0/3 ✗ | Lorentzkracht |
| Q23 | 3/3 ✓ | |
| Q24 | 0/2 ✗ | **IMAGE LIMIT ERROR** |
| Q25 | 0/3 ✗ | **IMAGE LIMIT ERROR** |

**Perfect scores**: 11 (excl. errors)
**Zero scores**: 8 (waarvan 4 door image limit)

---

## Vergelijking met Andere Cloud Modellen

| Model | Score | Input | Output |
|-------|-------|-------|--------|
| gpt-5-mini | 84.2% | $0.25 | $2.00 |
| gpt-5.1 | 81.6% | $1.25 | $10.00 |
| **mistral-large-2512** | **59.2%*** | **$0.50** | **$1.50** |
| gpt-4o | 57.9% | $2.50 | $10.00 |
| gpt-4o-mini | 38.2% | $0.15 | $0.60 |

*70.3% op beantwoorde vragen

---

## Wanneer Mistral Gebruiken

**Geschikt voor:**
- Topics met ≤4-5 vragen
- Taken zonder context-accumulatie
- Budget-gevoelige toepassingen

**Niet geschikt voor:**
- Lange exam topics (>5 vragen met afbeeldingen)
- Evaluatie-systemen met conversatie-context

---

## Mogelijke Oplossing

De eval.py zou aangepast kunnen worden om vragen onafhankelijk te beantwoorden (zonder context-accumulatie). Dit zou de image-limit omzeilen maar ten koste van context-voordelen.

```python
# Huidige aanpak (context per topic):
messages.append({"role": "user", "content": [images + prompt]})
messages.append({"role": "assistant", "content": response})

# Alternatief (per vraag reset):
messages = [{"role": "user", "content": [images + prompt]}]
```

---

## Conclusie

**Mistral Large is niet geschikt voor de huidige eval-architectuur.**

De 8-image limit is een fundamentele API-beperking die 16% van de punten kost. Op beantwoorde vragen scoort het model 70.3%, wat competitief zou zijn met gpt-4o maar nog steeds achter gpt-5-mini.

### Aanbeveling

Gebruik gpt-5-mini ($0.25/$2.00) - het kost iets meer maar heeft geen image-limit en scoort 84.2%.
