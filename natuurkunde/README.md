# VWO Natuurkunde Examen 2026 - LLM Benchmark

**Lokale modellen op consumentenhardware overtreffen commerciële SOTA van een jaar geleden.**

![Model Ranking](images/benchmark/01_ranking.png)

## Waarom Deze Benchmark?

### Zero Data Contamination

Dit is het VWO natuurkunde examen van **mei 2026**. Geen enkel model kan hierop getraind zijn - de data bestond simpelweg nog niet tijdens training. Dit maakt het een van de weinige benchmarks waar we zeker weten dat we *generalisatie* meten, niet *memorisatie*.

### Historisch Perspectief

- **Maart 2023**: GPT-4 release - eerste "frontier" multimodal model
- **Mei 2024**: GPT-4o was state-of-the-art, de standaard voor complexe taken
- **Mei 2026**: Lokale 27B modellen op een enkele GPU scoren **93.4%**, terwijl GPT-4o blijft steken op **57.9%**

In drie jaar tijd is wat ooit cloud-only frontier capability was, nu beschikbaar op consumentenhardware - en het presteert *beter*.

### Wat Meet Deze Benchmark?

| Capability | Hoe Getest |
|------------|------------|
| **Vision + Text → Text** | Alle vragen staan in afbeeldingen, niet als tekst |
| **Multi-image reasoning** | Tot 14 afbeeldingen per topic in context |
| **Instructie-opvolging uit images** | Model moet opdrachten in plaatjes lezen en uitvoeren |
| **Nederlands** | Vraag en antwoord volledig in het Nederlands |
| **Lange context coherentie** | Vragen bouwen voort op eerdere antwoorden binnen topic |
| **Domeinkennis (natuurkunde)** | Formules, concepten, Binas-tabellen |
| **Wetenschappelijke diagrammen** | Grafieken, schakelschema's, vectordiagrammen |
| **Multi-step redenering** | Gegeven → formule → berekening → conclusie |
| **Nauwkeurigheid** | Eenheden, significante cijfers, foutmarges |

### Mogen We Het Intelligentie Noemen?

De resultaten zijn opmerkelijk. Per vraag krijgt het model **one-shot** de relevante afbeeldingen - geen voorbeelden, geen tools, geen calculator. Bij opeenvolgende vragen binnen een topic (opgave) krijgt het model wel de conversatiehistorie: eerdere vragen, antwoorden, en alle bijbehorende afbeeldingen als context. Een lokaal model behaalt zo 93.4% op een VWO eindexamen. Het:

- Leest complexe natuurkundige vraagstukken uit afbeeldingen
- Past correcte formules toe op nieuwe situaties
- Redeneert over concepten (snelheid vs positie, Lorentzkracht)
- Produceert antwoorden in correct Nederlands
- Volgt de gevraagde methode, niet alleen het eindantwoord

Of dit "intelligentie" is, is filosofisch. Maar het is onmiskenbaar *indrukwekkend* - en praktisch bruikbaar voor educatie.

---

## Resultaten

### Overall Ranking

| Rank | Model | Score | Type | Opmerking |
|------|-------|-------|------|-----------|
| 🥇 | qwen/qwen3.6-27b | **93.4%** | Lokaal | Best presterend |
| 🥈 | google/gemma-4-31b | **89.5%** | Lokaal | Beste judge |
| 🥉 | qwen/qwen3.6-35b-a3b | **88.2%** | Lokaal | MoE variant |
| 4 | openai/gpt-5-mini | **84.2%** | Cloud | Beste cloud model |
| 5 | google/gemma-4-26b-a4b | **82.9%** | Lokaal | |
| 6 | openai/gpt-5.1 | **81.6%** | Cloud | Snelste (~5s/vraag) |
| 7 | mistralai/mistral-large-2512 | 59.2%* | Cloud | *8-image limit |
| 8 | openai/gpt-4o | **57.9%** | Cloud | Vision failures |
| 9 | openai/gpt-4o-mini | 38.2% | Cloud | Vision failures |
| 10 | nvidia/nemotron-3-nano-omni | 20.0% | Lokaal | |

*Judge: google/gemma-4-31b*

### Cloud Model Kosten vs Prestatie

![Cost Effectiveness](images/benchmark/02_cost.png)

**gpt-5-mini** domineert: hoogste score (84.2%) bij laagste prijs ($2/M output tokens).

### Vraag Moeilijkheid

![Question Heatmap](images/benchmark/04_questions.png)

**Opvallend:**
- **Q04** (relatieve beweging): Bijna alle modellen falen - conceptuele verwarring tussen snelheid en positie
- **Q22** (Lorentzkracht): Lastig maar niet onmogelijk - qwen3.6-27b scoort 100%
- **Elektriciteitspracticum** (Q08-Q10): Reasoning models scoren hier 100%

---

## Methodologie

### Evaluatie Pipeline

```
1. SCAN    Exam images → metadata.jsonl
2. SYNC    metadata.jsonl → SQLite database
3. SOLVE   Model genereert antwoorden (vision API)
4. JUDGE   Judge model vergelijkt met correctievoorschrift
```

### Judge Verificatie

Alle scores zijn beoordeeld door **google/gemma-4-31b** tegen de officiële correctievoorschriften (CV). Steekproeven zijn handmatig geverifieerd - de judge is accuraat, inclusief het toekennen van deelpunten. Cross-validatie met qwen-judges toont dat gemma genuanceerder beoordeelt waar qwen strenger is.

### Hardware

Lokale modellen gedraaid via LMStudio op een enkele consumer GPU (niet geoptimaliseerd voor snelheid). Cloud modellen via OpenRouter API.

---

## Gebruik

```bash
cd natuurkunde

# Activeer venv
source ../venv/bin/activate

# Genereer antwoorden
python eval.py solve --model "qwen/qwen3.6-27b" \
  --temperature 1.0 --max-tokens 32768

# Beoordeel antwoorden
python eval.py judge --judge-model "google/gemma-4-31b" \
  --temperature 1.0

# Genereer visualisaties
python visualize.py
```

### OpenRouter (cloud modellen)

```bash
# Zet API key in .env
echo "OPENROUTER_API_KEY=sk-..." > ../.env

# Solve via OpenRouter
python eval.py solve --model "openai/gpt-5-mini" \
  --base-url "https://openrouter.ai/api/v1"
```

---

## Structuur

```
natuurkunde/
├── images/
│   ├── 2026-05/vw-1023-a-26-1-o/   # 53 exam + CV images
│   └── benchmark/                   # Visualisaties
├── analyse/                         # 14 model-specifieke analyses
├── eval.db                          # Alle antwoorden en beoordelingen
├── eval.py                          # Hoofdscript
├── visualize.py                     # Tufte-style grafieken
└── schema.sql                       # Database schema
```

---

## Model-Specifieke Analyses

Gedetailleerde foutanalyses per model in [`analyse/`](analyse/):

- [qwen3.6-27b](analyse/qwen3.6-27b.md) - Hoogste score, 3 fouten
- [gemma-4-31b](analyse/gemma-4-31b.md) - Beste judge
- [gpt-5-mini](analyse/gpt-5-mini.md) - Beste cloud, geen vision failures
- [gpt-5.1](analyse/gpt-5.1.md) - Snelste, maar slechter dan gpt-5-mini
- [gpt-4o](analyse/gpt-4o.md) - Vision failures op Q07/Q25
- [mistral-large-2512](analyse/mistral-large-2512.md) - 8-image context limit

---

## Conclusie

**De democratisering van AI is meetbaar.**

Lokale modellen op consumentenhardware presteren nu beter dan wat een jaar geleden state-of-the-art cloud AI was - op een examen dat niet in hun trainingsdata kan zitten.

Voor VWO natuurkunde examenvoorbereiding:
- **Beste keuze:** qwen3.6-27b lokaal (93.4%, gratis na hardware)
- **Cloud alternatief:** gpt-5-mini (84.2%, $2/M tokens)
- **Vermijd:** gpt-4o en ouder (vision failures, lage scores)
