# VWO Examen Evaluatie 2026

LLM benchmark op Nederlandse VWO eindexamens - zero data contamination, multimodale evaluatie.

## Vakken

| Vak | Status | Beste Model | Score |
|-----|--------|-------------|-------|
| [**Natuurkunde**](natuurkunde/README.md) | ✅ Compleet | gemma-4-31b (vLLM) | 96.1% |

## Overzicht

Dit project evalueert hoe goed large language models presteren op officiële Nederlandse VWO eindexamens uit 2026. Omdat deze examens niet in de trainingsdata van de modellen kunnen zitten, meten we echte generalisatie - niet memorisatie.

**Belangrijkste bevinding:** Lokale modellen op consumentenhardware (31B parameters, €0.07/examen) presteren beter dan alle cloud APIs inclusief Claude Opus en GPT-5.

## Structuur

```
eval-exam-2026/
├── natuurkunde/          # VWO Natuurkunde 2026
│   ├── images/           # Examenafbeeldingen + CV
│   ├── analyse/          # Model-specifieke analyses
│   ├── eval.db           # Alle antwoorden en beoordelingen
│   └── README.md         # Volledige benchmark resultaten
└── README.md             # Dit bestand
```

## Meer vakken toevoegen

Elk vak krijgt een eigen directory met dezelfde structuur:

```bash
mkdir wiskunde
cd wiskunde
# Screenshots van PDF naar images/{jaar}/{examencode}/
# python eval.py scan images/{jaar}/{examencode}
# python eval.py sync images/{jaar}/{examencode}
# python eval.py solve --model "..."
# python eval.py judge --judge-model "..."
```

## Licentie

De examenafbeeldingen zijn eigendom van het College voor Toetsen en Examens (CvTE). Dit project is voor educatieve en onderzoeksdoeleinden.
