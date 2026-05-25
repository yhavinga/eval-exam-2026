# Analyse OpenAI GPT-5.1

## Overzicht

GPT-5.1 via OpenRouter behaalde **81.6%** op het VWO natuurkunde examen. Het is OpenAI's nieuwste flagship model en presteert significant beter dan gpt-4o, maar iets slechter dan gpt-5-mini bij hogere kosten.

## Score

| Model | Score | Max | % |
|-------|-------|-----|---|
| openai/gpt-5.1 | 62 | 76 | **81.6%** |

## Prijsvergelijking OpenAI Modellen

| Model | Score | Input | Output | Opmerkingen |
|-------|-------|-------|--------|-------------|
| gpt-5-mini | **84.2%** | $0.25 | $2.00 | Beste prijs/prestatie |
| **gpt-5.1** | **81.6%** | $1.25 | $10.00 | Geen vision fails |
| gpt-4o | 57.9% | $2.50 | $10.00 | Vision fails Q07/Q25 |
| gpt-4o-mini | 38.2% | $0.15 | $0.60 | Vision fails Q07/Q25 |

## Configuratie

- **Provider**: OpenRouter
- **Temperature**: 1.0 (default, niet gespecificeerd)
- **Max tokens**: 32768
- **Gemiddelde solve tijd**: ~4-5s per vraag (zeer snel)

## Resultaten per Vraag

| Vraag | Score | gpt-5-mini | gpt-4o | Opmerking |
|-------|-------|------------|--------|-----------|
| Q01 | 3/3 ✓ | 3/3 | 3/3 | |
| Q02 | 2/2 ✓ | 2/2 | 1/2 | |
| Q03 | 2/2 ✓ | 2/2 | 2/2 | |
| Q04 | 1/2 | 0/2 | 0/2 | Beter dan anderen |
| Q05 | 1/3 | 1/3 | 1/3 | |
| Q06 | 4/4 ✓ | 4/4 | 0/4 | gpt-4o faalde hier |
| Q07 | 3/3 ✓ | 2/3 | 0/3 | **Geen vision fail!** |
| Q08 | 4/4 ✓ | 4/4 | 4/4 | |
| Q09 | 3/3 ✓ | 3/3 | 3/3 | |
| Q10 | 3/3 ✓ | 3/3 | 2/3 | |
| Q11 | 3/3 ✓ | 3/3 | 2/3 | |
| Q12 | 3/3 ✓ | 2/3 | 1/3 | Beter dan gpt-5-mini |
| Q13 | 2/4 | 3/4 | 3/4 | |
| Q14 | 2/2 ✓ | 2/2 | 2/2 | |
| Q15 | 3/4 | 3/4 | 1/4 | |
| Q16 | 4/4 ✓ | 4/4 | 3/4 | |
| Q17 | 3/5 | 5/5 | 4/5 | gpt-5-mini perfect |
| Q18 | 2/3 | 2/3 | 2/3 | |
| Q19 | 2/2 ✓ | 2/2 | 2/2 | |
| Q20 | 3/3 ✓ | 3/3 | 3/3 | |
| Q21 | 1/3 | 2/3 | 2/3 | |
| Q22 | 0/3 ✗ | 1/3 | 0/3 | Lorentzkracht lastig |
| Q23 | 3/3 ✓ | 3/3 | 3/3 | |
| Q24 | 2/2 ✓ | 2/2 | 0/2 | |
| Q25 | 3/3 ✓ | 3/3 | 0/3 | **Geen vision fail!** |

**Perfect scores**: 15/25 (60%)

---

## Belangrijke Bevindingen

### 1. Geen Vision Failures

In tegenstelling tot gpt-4o en gpt-4o-mini heeft gpt-5.1 geen problemen met het lezen van vraag-afbeeldingen:

| Vraag | gpt-5.1 | gpt-4o | gpt-4o-mini |
|-------|---------|--------|-------------|
| Q07 | 3/3 ✓ | 0/3 "niet zichtbaar" | 0/3 "niet zichtbaar" |
| Q25 | 3/3 ✓ | 0/3 "niet gezien" | 0/3 "niet zichtbaar" |

Dit suggereert verbeterde vision-architectuur in de gpt-5 generatie.

### 2. Zeer Snelle Inferentie

Gemiddeld ~4-5 seconden per vraag - significant sneller dan:
- gpt-5-mini: ~25s
- gpt-4o: ~12s
- Lokale modellen: ~60-120s

### 3. Q04 Verbetering

Als enige OpenAI model scoorde gpt-5.1 punten op Q04 (1/2), waar alle andere modellen 0/2 scoorden vanwege een conceptuele fout over "relatieve beweging".

---

## Waar gpt-5.1 Verliest van gpt-5-mini

| Vraag | gpt-5.1 | gpt-5-mini | Verschil |
|-------|---------|------------|----------|
| Q17 | 3/5 | 5/5 | -2 |
| Q13 | 2/4 | 3/4 | -1 |
| Q21 | 1/3 | 2/3 | -1 |
| Q22 | 0/3 | 1/3 | -1 |

Totaal: -5 punten (maar +3 op andere vragen, netto -2).

### Analyse van de fouten (geverifieerd tegen CV)

**Q17 (interferentie)**: gpt-5.1 miste dat licht in de lamel een kortere
golflengte heeft (λ_lamel = λ/n = 320 nm). Gebruikte alleen λ_lucht = 480 nm.

**Q22 (Lorentzkracht)**: gpt-5.1 las de elektronenbaan in figuur 4 verkeerd -
zag de elektronen naar beneden buigen terwijl ze naar boven buigen. Koos
daardoor plaatje II in plaats van het correcte plaatje IV.

**Q13 (grafiek)**: Afleesfouten - berekende a=0.89 terwijl 0.81±0.01 vereist was.

**Q21 (banen tekenen)**: Zei "kwart cirkel" (90°) voor beide figuren, terwijl
links >90° en rechts <90° moet zijn.

**Patroon**: Q13 en Q22 zijn vision/aflees-fouten, Q17 en Q21 zijn fysica-fouten.
Dit is onverwacht - gpt-5.1 zou als groter model beter moeten presteren, maar
gpt-5-mini is nauwkeuriger op zowel vision als fysica-concepten.

---

## Vergelijking met Alle Modellen

| Model | Score | Type |
|-------|-------|------|
| qwen/qwen3.6-27b | 93.4% | Lokaal |
| google/gemma-4-31b | 89.5% | Lokaal |
| qwen/qwen3.6-35b-a3b | 88.2% | Lokaal |
| openai/gpt-5-mini | 84.2% | Cloud |
| google/gemma-4-26b-a4b | 82.9% | Lokaal |
| **openai/gpt-5.1** | **81.6%** | Cloud |
| mistralai/mistral-large-2512 | 59.2%* | Cloud |
| openai/gpt-4o | 57.9% | Cloud |

---

## Conclusie

**gpt-5.1 is een solide keuze voor VWO examens, maar gpt-5-mini is beter.**

Sterke punten:
1. **Betrouwbare vision** - geen "vraag niet zichtbaar" fouten
2. **Zeer snel** - ~4-5s per vraag
3. **Consistente kwaliteit** - 60% perfecte scores
4. **Q04 verbetering** - als enige model punten op moeilijke conceptvraag

Zwakke punten:
1. **Duurder dan gpt-5-mini** - 5x input, 5x output kosten
2. **Iets lagere score** - 81.6% vs 84.2%
3. **Q22 Lorentzkracht** - blijft lastig voor alle modellen

### Aanbeveling

Gebruik **gpt-5-mini** voor de beste prijs/prestatie verhouding:
- 2.6% hogere score (84.2% vs 81.6%)
- 5x goedkoper ($0.25/$2 vs $1.25/$10)

Gebruik **gpt-5.1** alleen als snelheid kritiek is (~5x sneller dan gpt-5-mini).
