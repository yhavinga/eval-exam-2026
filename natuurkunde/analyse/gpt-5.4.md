# Analyse OpenAI GPT-5.4

## Overzicht

GPT-5.4 via OpenRouter behaalde **89.5%** op het VWO natuurkunde examen - het beste resultaat van alle cloud modellen en gelijk aan gemma-4-31b (LMStudio). Dit is een significante verbetering ten opzichte van gpt-5-mini (+5.3%) en gpt-5.1 (+7.9%).

## Score

| Model | Score | Max | % |
|-------|-------|-----|---|
| openai/gpt-5.4 | 68 | 76 | **89.5%** |

## Prijsvergelijking OpenAI Modellen

| Model | Score | Input | Output | Opmerkingen |
|-------|-------|-------|--------|-------------|
| **gpt-5.4** | **89.5%** | $1.50 | $10.00 | Beste cloud model |
| gpt-5-mini | 84.2% | $0.25 | $2.00 | Beste prijs/prestatie |
| gpt-5.1 | 81.6% | $1.25 | $10.00 | Snelste |
| gpt-4o | 57.9% | $2.50 | $10.00 | Vision fails Q07/Q25 |
| gpt-4o-mini | 38.2% | $0.15 | $0.60 | Vision fails Q07/Q25 |

## Configuratie

- **Provider**: OpenRouter
- **Temperature**: 1.0
- **Max tokens**: 16384
- **Gemiddelde solve tijd**: ~7s per vraag

## Resultaten per Vraag

| Vraag | Score | gpt-5-mini | gpt-5.1 | gpt-4o | Opmerking |
|-------|-------|------------|---------|--------|-----------|
| Q01 | 3/3 ✓ | 3/3 | 3/3 | 3/3 | |
| Q02 | 2/2 ✓ | 2/2 | 2/2 | 1/2 | |
| Q03 | 2/2 ✓ | 2/2 | 2/2 | 2/2 | |
| Q04 | **2/2** ✓ | 0/2 | 1/2 | 0/2 | **Perfect op lastige vraag!** |
| Q05 | 2/3 | 1/3 | 1/3 | 1/3 | Beter dan anderen |
| Q06 | **0/4** ✗ | 4/4 | 4/4 | 0/4 | Afleiding niet begrepen |
| Q07 | 3/3 ✓ | 2/3 | 3/3 | 0/3 | Geen vision fail |
| Q08 | 4/4 ✓ | 4/4 | 4/4 | 4/4 | |
| Q09 | 3/3 ✓ | 3/3 | 3/3 | 3/3 | |
| Q10 | 3/3 ✓ | 3/3 | 3/3 | 2/3 | |
| Q11 | 3/3 ✓ | 3/3 | 3/3 | 2/3 | |
| Q12 | 3/3 ✓ | 2/3 | 3/3 | 1/3 | Beter dan gpt-5-mini |
| Q13 | **4/4** ✓ | 3/4 | 2/4 | 3/4 | **Perfect!** |
| Q14 | 2/2 ✓ | 2/2 | 2/2 | 2/2 | |
| Q15 | **4/4** ✓ | 3/4 | 3/4 | 1/4 | **Perfect!** |
| Q16 | 4/4 ✓ | 4/4 | 4/4 | 3/4 | |
| Q17 | **5/5** ✓ | 5/5 | 3/5 | 4/5 | **Perfect!** |
| Q18 | **3/3** ✓ | 2/3 | 2/3 | 2/3 | **Perfect!** |
| Q19 | 2/2 ✓ | 2/2 | 2/2 | 2/2 | |
| Q20 | 3/3 ✓ | 3/3 | 3/3 | 3/3 | |
| Q21 | **3/3** ✓ | 2/3 | 1/3 | 2/3 | **Perfect!** |
| Q22 | 1/3 | 1/3 | 0/3 | 0/3 | Lorentzkracht lastig |
| Q23 | 3/3 ✓ | 3/3 | 3/3 | 3/3 | |
| Q24 | 1/2 | 2/2 | 2/2 | 0/2 | Verkeerde constante |
| Q25 | 3/3 ✓ | 3/3 | 3/3 | 0/3 | Geen vision fail |

**Perfect scores**: 17/25 (68%)

---

## Belangrijke Bevindingen

### 1. Q04 Perfect - Uniek onder Cloud Modellen

gpt-5.4 is het enige cloud model dat Q04 volledig correct beantwoordt. Deze vraag over relatieve beweging (snelheid vs positie) leidde bij alle andere modellen tot conceptuele fouten.

### 2. Q06 Complete Mislukking - "Afleiding" niet begrepen

De vraag was: "Leid formule (1) af" voor $a_x = \frac{v_b^2}{2s}$

**gpt-5.4 antwoord:**
> Gebruik de bewegingsvergelijking: $v^2 = v_0^2 + 2as$
> Invullen geeft: $a_x = \frac{v_b^2}{2s}$

**Probleem:** Het model gebruikte een reeds afgeleide formule ($v^2 = v_0^2 + 2as$) die algebraïsch equivalent is aan wat gevraagd wordt. Het correctievoorschrift vereist een afleiding vanuit:
- **Methode 1**: Energiebehoud ($W = \Delta E_k$)
- **Methode 2**: Kinematica met $v_{gem} = \frac{v_{begin} + v_{eind}}{2}$

Dit is een fundamenteel begrip-probleem: het model snapt niet wat "afleiden" betekent in natuurkunde-context.

### 3. Q22 Lorentzkracht - Verkeerde Observatie

**gpt-5.4 antwoord:**
> Het elektron komt bij P van links naar rechts binnen en buigt daarna **omlaag**.

**Probleem:** In figuur 4 buigt de elektronenbaan duidelijk naar **boven**, niet naar beneden. Deze observatiefout leidt tot de verkeerde keuze (II i.p.v. IV).

Dit is dezelfde fout die gpt-5.1 maakte - een vision/interpretatie probleem bij Lorentzkracht-diagrammen.

### 4. Q05 Grafiekaflezing - Zelfde Fout als Gemma-4 (no-R)

**gpt-5.4 antwoord:**
> begin van dit deel: t=0,00 s, $v_x \approx 4,0$ m/s
> omkeerpunt: $v_x=0$ bij ongeveer t ≈ 0,12 s
> $a_x = \frac{0-4,0}{0,12} \approx -33$ m/s²

**Probleem:** De vertraging begint pas bij t=0,04s (daarvoor is de snelheid constant). De correcte berekening is:
- $\Delta t = 0,12 - 0,04 = 0,08$ s
- $a_x = \frac{4,0}{0,08} = 50$ m/s²

Interessant: dit is exact dezelfde fout die gemma-4-31b maakt wanneer reasoning uitgeschakeld is. Met reasoning ziet gemma het subtiele detail dat de snelheid pas later begint te dalen.

### 5. Q24 Verkeerde Constante

**gpt-5.4 antwoord:**
> Voor ijzer bij 2,0 MeV: $\mu \approx 0,45$ cm⁻¹

**Probleem:** De correcte halveringsdikte is 2,1 cm, wat overeenkomt met $\mu \approx 0,33$ cm⁻¹. Het model lijkt een waarde uit het geheugen te gebruiken i.p.v. de gegeven data.

---

## Waar gpt-5.4 Wint van Andere OpenAI Modellen

| Vraag | gpt-5.4 | gpt-5-mini | gpt-5.1 | Verschil |
|-------|---------|------------|---------|----------|
| Q04 | **2/2** | 0/2 | 1/2 | +2/+1 |
| Q13 | **4/4** | 3/4 | 2/4 | +1/+2 |
| Q15 | **4/4** | 3/4 | 3/4 | +1/+1 |
| Q18 | **3/3** | 2/3 | 2/3 | +1/+1 |
| Q21 | **3/3** | 2/3 | 1/3 | +1/+2 |

Totaal: +6 punten vs gpt-5-mini, +7 punten vs gpt-5.1

## Waar gpt-5.4 Verliest

| Vraag | gpt-5.4 | gpt-5-mini | gpt-5.1 | Verschil |
|-------|---------|------------|---------|----------|
| Q06 | **0/4** | 4/4 | 4/4 | -4/-4 |
| Q24 | 1/2 | 2/2 | 2/2 | -1/-1 |

Totaal: -5 punten vs beiden

**Netto**: +1 punt vs gpt-5-mini, +2 punten vs gpt-5.1

---

## Vergelijking met Alle Modellen

| Model | Score | Type |
|-------|-------|------|
| gemma-4-31b (vLLM) | 94.7% | Lokaal |
| qwen/qwen3.6-27b | 93.4% | Lokaal |
| google/gemma-4-31b | 89.5% | Lokaal |
| **openai/gpt-5.4** | **89.5%** | **Cloud** |
| qwen/qwen3.6-35b-a3b | 88.2% | Lokaal |
| openai/gpt-5-mini | 84.2% | Cloud |
| google/gemma-4-26b-a4b | 82.9% | Lokaal |
| openai/gpt-5.1 | 81.6% | Cloud |
| openai/gpt-4o | 57.9% | Cloud |

---

## Conclusie

**gpt-5.4 is het beste cloud model voor VWO examens.**

Sterke punten:
1. **Hoogste cloud score** - 89.5%, gelijk aan gemma-4-31b (LMStudio)
2. **Q04 perfect** - als enige cloud model geen conceptuele fout
3. **Betrouwbare vision** - geen "vraag niet zichtbaar" fouten
4. **Consistente kwaliteit** - 68% perfecte scores

Zwakke punten:
1. **Q06 afleiding niet begrepen** - gebruikt afgeleide formule i.p.v. af te leiden
2. **Q22 observatiefout** - ziet elektronenbaan verkeerd buigen
3. **Q05 grafiekdetail gemist** - zelfde fout als reasoning-loze modellen
4. **Duurder** - hogere kosten dan gpt-5-mini

### Aanbeveling

Voor maximale score: gebruik **gpt-5.4** (89.5%)
Voor beste prijs/prestatie: gebruik **gpt-5-mini** (84.2% voor 1/5e van de prijs)
Voor lokaal/privacy: gebruik **qwen3.6-27b** of **gemma-4-31b** (93%+)
