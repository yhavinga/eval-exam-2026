# Analyse Google Gemma-4-e4b Fouten

## Overzicht

Google Gemma-4-e4b (efficient variant met 4B actieve parameters) behaalde **40.8%** op het VWO natuurkunde examen. Ondanks goede tekstuele reasoning heeft het model significante problemen met het interpreteren van diagrammen, grafieken en fysica-notatie in afbeeldingen.

## Score

| Judge | Score | Max | % |
|-------|-------|-----|---|
| google/gemma-4-31b | 31 | 76 | **40.8%** |

## Vergelijking met Andere Modellen

| Model | Score |
|-------|-------|
| qwen/qwen3.6-27b | 93.4% |
| google/gemma-4-31b | 89.5% |
| qwen/qwen3.6-35b-a3b | 88.2% |
| google/gemma-4-26b-a4b | 82.9% |
| gemma-4-31b-opus-distill | 56.6% |
| google/gemma-3-27b-it | 52.6% |
| **google/gemma-4-e4b** | **40.8%** |
| nvidia/nemotron-3-nano-omni | 20.0% |

## Verloren Punten Overzicht

| Vraag | Score | Verloren | Probleem |
|-------|-------|----------|----------|
| Q15 | 0/4 | 4 | Periode verkeerd afgelezen uit grafiek |
| Q16 | 0/4 | 4 | Claimde data ontbrak (vision) |
| Q17 | 1/5 | 4 | Onvolledige interferentie-analyse |
| Q09 | 0/3 | 3 | Schakelschema verkeerd geïnterpreteerd |
| Q12 | 0/3 | 3 | Grafiek-interpretatie fout |
| Q13 | 1/4 | 3 | Onvolledig |
| Q18 | 0/3 | 3 | Richels verkeerd geteld |
| Q21 | 0/3 | 3 | Lorentzkracht-richting fout |
| Q22 | 0/3 | 3 | Magneetveld-symbolen niet begrepen |
| + 6 meer | | 12 | Diverse kleine fouten |

**Totaal verloren: 45 punten**

---

## Kritieke Fouten

### Q09: Schakelschema Verkeerd Gelezen (0/3)

**Opgave**: Leid af dat U_R3 = 2·U_R1

**Model Fout**:
> "De leerling stelt dat alle drie de weerstanden in serie zijn geschakeld, terwijl uit de tekening duidelijk blijkt dat R₁ en R₂ parallel staan."

Het model concludeerde zelfs dat er een "typefout" in de opgave zat, terwijl de stelling correct was.

**Analyse**: Het model kan het schakelschema niet correct interpreteren. Dit is een fundamenteel vision-probleem bij het herkennen van serie vs parallel schakelingen.

---

### Q15: Grafiek Verkeerd Afgelezen (0/4)

**Opgave**: Bepaal periode T en bereken afstand

**CV Vereiste**: T = 5,2-5,6 dagen (uit grafiek)

**Model Antwoord**: T ≈ 8 dagen

**Judge**: "Uit de grafiek is duidelijk te zien dat de pieken elkaar ongeveer elke 5,4 dag opvolgen."

**Analyse**: Het model las de x-as van de intensiteitsgrafiek verkeerd af, waardoor de vervolgberekening ook fout ging.

---

### Q16: Data "Ontbreekt" (0/4)

**Opgave**: Bereken minimale energie voor elektron-overgang (particle-in-a-box)

**Model Antwoord**:
> "U heeft echter alle [gegevens niet gegeven]... de vraag en de benodigde gegevens ontbreken"

**Judge**: "De leerling stelt dat de vraag en de benodigde gegevens ontbreken, terwijl deze wel duidelijk in de afbeelding staan."

**Analyse**: Vergelijkbaar met nemotron's "Not answerable" probleem - het model kan bepaalde tekst in afbeeldingen niet lezen.

---

### Q22: Magneetveld-Symbolen Niet Begrepen (0/3)

**Opgave**: Bepaal richting magneetveld en verband met straal

**Model Antwoord**: Koos "Figuur 5 IV" op basis van visuele patronen

**Judge**: "De leerling interpreteert de kruisjes en stippen als 'patronen' of 'texturen' in plaats van vectoren."

**Analyse**: Het model herkent de standaard fysica-notatie niet:
- ⊗ (kruis) = vector het papier in
- ⊙ (stip) = vector uit het papier

Dit is een fundamentele kennislacune over fysica-diagramconventies.

---

## Sterke Punten

Het model scoorde **perfect** op 6 vragen:

| Vraag | Score | Topic |
|-------|-------|-------|
| Q01 | 3/3 | Energiebehoud berekening |
| Q03 | 2/2 | Frame-telling uitleg |
| Q06 | 4/4 | Kinematica formule-afleiding |
| Q11 | 3/3 | Cepheïden-historische context |
| Q19 | 2/2 | Tumorbestraling voorwaarde |
| Q20 | 3/3 | Linac formule |
| Q23 | 3/3 | Energie-berekening |

**Patroon**: Het model presteert goed op:
- Zuivere berekeningen zonder complexe diagrammen
- Conceptuele uitlegvragen
- Vragen waar de opgave duidelijk in tekst staat

---

## Systematische Problemen

### 1. Diagram-Interpretatie (KRITIEK)
- Schakelschema's: serie vs parallel niet herkend (Q09)
- Magneetveld-notatie: ⊗ en ⊙ niet begrepen (Q22)
- Stroomrichtingen en polariteit

### 2. Grafiek-Aflezen
- Periode uit intensiteitsgrafiek: factor 1.5 fout (Q15)
- Nauwkeurigheid bij het bepalen van specifieke waarden

### 3. Partiële Vision-Blindheid
- Soms claimt het model dat gegevens ontbreken (Q16, Q02)
- Minder ernstig dan nemotron, maar wel aanwezig

### 4. Fysica-Conventies
- Standaard notaties in diagrammen niet herkend
- Rechterhandregel niet correct toegepast

---

## Vergelijking met Grotere Modellen

| Aspect | gemma-4-e4b | gemma-4-26b-a4b | gemma-4-31b |
|--------|-------------|-----------------|-------------|
| Score | 40.8% | 82.9% | 89.5% |
| Diagram-interpretatie | ❌ Slecht | ⚠️ Matig | ✅ Goed |
| Grafiek-aflezen | ❌ Fouten | ⚠️ Soms fout | ✅ Goed |
| Tekstbegrip | ✅ Goed | ✅ Goed | ✅ Goed |

De "efficient" variant (e4b) verliest significant aan vision-capabilities vergeleken met de grotere modellen.

---

## Solve Timing

Gemiddelde solve-tijd: **~20 seconden per vraag** (snelste van alle modellen)

| Vraag | Tijd |
|-------|------|
| Snelste (Q16) | 10.7s |
| Langste (Q17) | 37.6s |
| Gemiddeld | ~20s |

De snelheid is indrukwekkend, maar ten koste van nauwkeurigheid.

---

## Conclusie

**Niet aanbevolen voor VWO natuurkunde examens.**

Gemma-4-e4b is een snelle, efficiënte variant maar mist cruciale vision-capabilities voor examenvragen:

1. **Diagram-interpretatie** faalt consistent
2. **Grafiek-aflezen** is onnauwkeurig
3. **Fysica-notatie** (⊗, ⊙) wordt niet herkend
4. **Soms claimt data ontbreekt** terwijl het in de afbeelding staat

### Wanneer Bruikbaar
- Snelle conceptuele vragen zonder complexe diagrammen
- Tekstuele reasoning-taken
- Situaties waar snelheid belangrijker is dan nauwkeurigheid

### Aanbeveling
Gebruik **gemma-4-26b-a4b** of **gemma-4-31b** voor betere vision-capabilities. De extra inferentietijd weegt op tegen de significante verbetering in nauwkeurigheid.
