# Analyse Gemma-3-27b-it Fouten (Non-Reasoning Model)

## Overzicht

Gemma-3-27b-it behaalde slechts **40.8-65.8%** op het VWO natuurkunde examen (vw-1023-a-26-1-o). Dit is een **non-reasoning model** en presteert dramatisch slechter dan reasoning modellen (80-90%).

## Cross-validatie Scores

| Judge | Score | Max | % |
|-------|-------|-----|---|
| google/gemma-3-27b-it (self) | 50 | 76 | 65.8% |
| google/gemma-4-31b | 40 | 76 | 52.6% |
| qwen/qwen3.6-35b-a3b | 39 | 76 | 51.3% |
| qwen/qwen3.6-27b | 31 | 76 | 40.8% |

**WAARSCHUWING**: De self-judge is niet alleen mild (+14-25 punten), maar ook **feitelijk onjuist** in sommige beoordelingen (zie Q22).

## Verschil Reasoning vs Non-Reasoning

| Model Type | Model | Score |
|------------|-------|-------|
| Reasoning | gemma-4-31b | 89.5% |
| Reasoning | qwen3.6-35b-a3b | 87.4% |
| Reasoning | gemma-4-26b-a4b | 82.9% |
| **Non-reasoning** | **gemma-3-27b-it** | **51.3%** |

Verschil: **~35 procentpunten** - reasoning is cruciaal voor VWO natuurkunde.

---

## Q09: Circuit-Analyse (0/3) - VOLLEDIGE MISLUKKING

### Opgave
"Leid af dat U_R3 = 2·U_R1" voor schakeling in figuur 2 met R₁ = R₂ = R₃.

### Circuit Topologie (uit figuur 2)
```
    ┌──R₁──┐
────┤      ├──R₃──
    └──R₂──┘
```
R₁ en R₂ staan **parallel**, deze combinatie staat in **serie** met R₃.

### CV Methode
- R_parallel = R/2
- Spanning verdeelt als R_parallel : R₃ = 1:2
- Dus U_R3 = 2 × U_R1 ✓

### Model Antwoord
Het model identificeerde de topologie **volledig verkeerd**:
> "Aangezien R₂ en R₃ in serie geschakeld zijn..."

Vervolgens maakte het contradictoire berekeningen en concludeerde:
> "U₃ = (2/3)UR₁" - **het omgekeerde van het juiste antwoord!**

### Judge Verificatie
Alle judges gaven 0/3 met dezelfde reden:
> "De leerling heeft de schakeling fundamenteel verkeerd geïnterpreteerd... R₁ en R₂ staan parallel, niet R₂ en R₃ in serie."

### Beoordeling
**0/3 - Judges correct**

---

## Q15: Cepheïden - Periode en Afstand (0-1/4)

### Opgave
1. Bepaal periode T van Delta Cephei uit lichtkromme (figuur 3)
2. Bepaal afstand tot de KMW

### Figuur 3 Analyse (Intensiteitsverloop)
De grafiek toont intensiteitspieken bij t ≈ 3, 8, 14, 19 dagen.
- Periode = tijd tussen pieken = **~5 dagen**
- CV accepteert: 5,2 - 5,6 dagen

### Model Antwoord
> "we kunnen zien dat de intensiteit zich herhaalt na ongeveer **20 dagen**. Dus T ≈ 20 dagen."

Het model verwarde de **totale grafiekbreedte** (20 dagen) met de **periode** (5 dagen)!

Vervolgens berekende het:
> "afstand tussen de aarde en KMW = **5,3 × 10¹⁸ m**"

Dit is ~200× te klein (CV: 1,1 × 10²¹ m) en fysisch onzinnig (zou KMW dichterbij plaatsen dan Delta Cephei).

### Beoordeling
**0-1/4 - Judges correct**

---

## Q16: Kwantummechanica - Pauli Principe (1-2/4)

### Opgave
"Toon met een berekening aan dat de kleinst mogelijke energieopname vanuit de grondtoestand van dit molecuul overeenkomt met de absorptie-energie van een blauw pigment."

Context: 8 elektronen in potentiaalput van 1,27 nm, absorptie-energie = 2,1 eV

### CV Methode
Met **Pauli uitsluitingsprincipe** (2 elektronen per niveau):
- 8 elektronen vullen n = 1, 2, 3, 4
- Kleinste transitie: n=4 → n=5
- ΔE = (5² - 4²) × h²/(8mL²) = 9 × 0,37 eV = **2,1 eV** ✓

### Model Antwoord
Het model negeerde Pauli volledig:
> "De kleinste mogelijke energieopname vindt plaats van de grondtoestand naar het eerstvolgende hoger gelegen energieniveau, n=2"

Berekende E₂ - E₁ = **1,0 eV** en concludeerde:
> "Dit komt niet overeen met de absorptie-energie van het blauwe pigment (2,1 eV)."

### Analyse
Het model:
1. Kent de formule voor energieniveaus ✓
2. Begrijpt niet dat 8 elektronen de eerste 4 niveaus vullen ✗
3. Begrijpt niet dat "grondtoestand van het systeem" ≠ n=1 ✗

### Beoordeling
**1-2/4 - Judges correct** (punt voor formule-gebruik)

---

## Q22: Lorentzkracht - SELF-JUDGE FEITELIJK ONJUIST (0/3)

### Opgave
"Leg uit welk magneetveld in figuur 5 geschikt is om de elektronen de banen van figuur 4 te laten volgen."

### Figuur 4 Analyse
- Elektronen komen van links binnen bij P
- Ze buigen **OMHOOG** (tegen de klok in)
- Snelle elektronen: grotere straal
- Langzame elektronen: kleinere straal

### Fysica-Analyse (Lorentzkracht)
Voor elektron (q < 0) met v naar rechts, F omhoog:
- F = qv × B (met q negatief)
- v × B moet omlaag wijzen (want q negatief keert richting om)
- v naar rechts, v × B omlaag → **B moet UIT het papier komen (⊙)**

Figuur 5 opties:
- I, II: B in het papier (×) → VERKEERD
- III, IV: B uit het papier (⊙) → CORRECT

Omdat straal varieert (kleiner naar rechtsboven), moet B sterker zijn naar rechtsboven.
→ **Plaatje IV is correct**

### Model Antwoord
> "**magneetveld II** het meest geschikt"
> "III & IV: De richting van het magnetisch veld (uit het papier) zal een omgekeerde kromming veroorzaken"

Dit is **fysisch volkomen onjuist**. Het model paste de rechterhandregel verkeerd toe.

### KRITIEK: Self-Judge Failure
De self-judge (gemma-3-27b-it) gaf **3/3** met motivatie:
> "De keuze voor magneetveld II is ook correct beargumenteerd"

Dit is **feitelijk onjuist**! De externe judges gaven allen 0/3:
> "De leerling bepaalt de richting onjuist... het veld moet uit het papier komen (⊙), niet erin."

### Beoordeling
**0/3 - Externe judges correct, self-judge feitelijk fout**

---

## Systematische Problemen

### 1. Geen Multi-Step Reasoning
Circuit-analyse (Q09) vereist:
1. Topologie identificeren
2. Equivalente weerstand berekenen
3. Stroomverdeling bepalen
4. Spanningen berekenen

Het model faalde op stap 1 en merkte dit niet op in latere stappen.

### 2. Begripsverwarring
- Q15: "Periode" verward met "grafiekbreedte"
- Q16: "Grondtoestand systeem" verward met "n=1"
- Q22: Lorentzkracht-richting omgekeerd

### 3. Geen Zelf-Verificatie
- Q15: Antwoord plaatst KMW dichterbij dan Delta Cephei - fysisch absurd
- Q09: Eindantwoord is exact omgekeerd - niet opgemerkt
- Q16: Concludeert "komt niet overeen" zonder te begrijpen waarom

### 4. Self-Judge Onbetrouwbaar
De self-judge is niet alleen te mild, maar ook **feitelijk incorrect**:
- Q22: Gaf 3/3 voor een antwoord met verkeerde Lorentzkracht-richting

---

## Vergelijking: Reasoning vs Non-Reasoning

### Q09 (Circuit)

**Reasoning (qwen3.6-35b-a3b)**:
Identificeert correct R₁||R₂ in serie met R₃, berekent stapsgewijs → **3/3**

**Non-reasoning (gemma-3-27b-it)**:
Verkeerde topologie, contradictoire berekeningen, omgekeerd antwoord → **0/3**

### Q22 (Lorentzkracht)

**Reasoning (gemma-4-31b)**:
Correcte rechterhandregel, B uit papier, kiest IV → **2-3/3**

**Non-reasoning (gemma-3-27b-it)**:
Verkeerde richting, kiest II → **0/3**

---

## Conclusies

### Waarom Non-Reasoning Faalt

1. **Formules ≠ Begrip**: Kent E_n formule, begrijpt Pauli niet
2. **Geen ketening**: Kan geen logische stappen volgen die op elkaar bouwen
3. **Geen verificatie**: Merkt fysisch onzinnige antwoorden niet op
4. **Grafiek-interpretatie**: Begrijpt niet wat gevraagd wordt

### Self-Judge Probleem

Dit model als judge gebruiken is **onbetrouwbaar**:
- Te mild (+14-25 punten)
- Soms feitelijk incorrect (Q22)

### Implicaties

| Toepassing | Non-Reasoning | Reasoning |
|------------|---------------|-----------|
| VWO Natuurkunde | ❌ Ongeschikt | ✓ Geschikt |
| Als Judge | ❌ Onbetrouwbaar | ✓ Betrouwbaar |
| Score | ~50% | ~85% |
