# Analyse Qwen 3.6-35b-a3b Fouten

## Overzicht

Qwen 3.6-35b-a3b behaalde **81.6-90.8%** op het VWO natuurkunde examen (vw-1023-a-26-1-o), afhankelijk van de judge. Dit model toont sterke reasoning-capaciteiten maar maakt enkele conceptuele fouten.

## Cross-validatie Scores

| Judge | Score | Max | % |
|-------|-------|-----|---|
| google/gemma-3-27b-it | 66 | 76 | 86.8% |
| google/gemma-4-26b-a4b | 69 | 76 | 90.8% |
| google/gemma-4-31b | 67 | 76 | 88.2% |
| qwen/qwen3.6-27b | 68 | 76 | 89.5% |
| qwen/qwen3.6-35b-a3b (self) | 62 | 76 | 81.6% |

**Opvallend**: De self-judge is significant strenger dan andere judges (-7 tot -9 punten verschil).

## Verloren Punten per Vraag

| Vraag | Consensus Score | Self Score | Probleem |
|-------|-----------------|------------|----------|
| Q04 | 0/2 | 0/2 | Snelheid vs positie verwarring |
| Q13 | 3/4 | 0/4 | Grafiek aflezing net buiten marge |
| Q18 | 1/3 | 1/3 | Verkeerde diffractie-orde (n=2 i.p.v. n=1) |
| Q21 | 2/3 | 1/3 | Tekst i.p.v. tekening, rechte lijn na veld ontbreekt |

---

## Q04: Botsproef - Aya's Conclusie (0/2)

### Opgave
"Leg met behulp van figuur 3 uit of Aya gelijk heeft."

Aya beweert dat de beweging van S ten opzichte van M stopt na t = 0,34 s.

### CV Criteria
1. Inzicht dat de **snelheden** van M en S op t=0,34s vergeleken moeten worden (1 pt)
2. Consequente conclusie (1 pt)

### CV Antwoord
Uit de onderlinge afstand tussen meetpunten in figuur 3 volgt dat de snelheid van S rond t=0,34s **groter is** dan de snelheid van M. Dus S beweegt nog steeds t.o.v. M. **Aya heeft ongelijk.**

### Model Antwoord
Het model concludeerde dat Aya **gelijk** heeft, gebaseerd op het feit dat marker S terugkeert naar positie x=0 bij beeldje 17.

### Analyse
**Fundamentele fysica-fout**: Het model verwarde positie met snelheid. De vraag gaat over relatieve beweging, wat bepaald wordt door snelheidsverschil, niet door positie. Dat S terugkeert naar x=0 betekent niet dat de relatieve beweging gestopt is.

### Beoordeling
**0/2 - Alle judges correct**

---

## Q13: Cepheïden - Bepaal a en C (3/4 vs 0/4)

### Opgave
1. Bepaal de grootte van a (uit helling trendlijn in log-log diagram)
2. Toon aan dat C = 1,5 × 10⁻¹⁴ W m⁻²

### CV Criteria
1. Inzicht dat a = steilheid van de trendlijn (1 pt)
2. Bepaling van a met twee punten, uitkomst 0,81 ± 0,01 (1 pt)
3. Aflezen snijpunt of invullen punt in formule (1 pt)
4. Completeren bepaling van C (1 pt)

### CV Methode
Gebruik punten (0,40; -13,50) en (1,50; -12,61):
```
a = (-12,61 - (-13,50)) / (1,50 - 0,40) = 0,89 / 1,10 = 0,81
```

### Model Antwoord
- Correct inzicht dat a = helling ✓
- Gebruikte punten (0; -13,8) en (1,5; -12,5)
- Berekende a = 1,3 / 1,5 = **0,87** (buiten marge 0,80-0,82)
- Correcte methode voor C: log(C) = -12,5 - 0,87 × 1,5 = -13,8
- Resultaat C = 10⁻¹³·⁸ ≈ 1,6 × 10⁻¹⁴ ✓

### Judge Disagreement
| Judge | Score | Redenering |
|-------|-------|------------|
| gemma-3-27b-it | 4/4 | Methode correct, kleine afwijking acceptabel |
| gemma-4-26b-a4b | 4/4 | Afwijking door grafisch aflezen, methode correct |
| gemma-4-31b | 3/4 | a buiten marge, rest correct |
| qwen/qwen3.6-27b | 3/4 | a buiten marge, C-berekening correct |
| qwen/qwen3.6-35b-a3b | **0/4** | a fout → alles fout |

### Mijn Beoordeling
**3/4 is correct. Self-judge (0/4) is te streng.**

De CV-marge van ±0,01 is extreem strikt voor grafisch aflezen. Het model:
- Toonde correct inzicht (a = helling) ✓
- Gebruikte correcte methode ✓
- Las grafiek net iets verkeerd af (0,87 vs 0,81)
- Voerde C-berekening correct uit met eigen waarden ✓

De self-judge behandelt dit als "alles of niets" terwijl partial credit gepast is.

---

## Q18: Morphodidius - Diffractietralie (1/3)

### Opgave
"Bepaal met behulp van het diagram op de uitwerkbijlage het aantal richels per centimeter op de vleugel."

### CV Criteria
1. Gebruik formule d·sin(α) = n·λ (1 pt)
2. Inzicht dat n=1 en aflezen α₁ tussen 48° en 52° (1 pt)
3. Completeren berekening met juiste significantie (1 pt)

### CV Antwoord
- Eerste-orde maximum bij ~50°
- d·sin(50) = 1·480 nm → d = 627 nm
- Aantal = 1 cm / 627 nm = **1,6 × 10⁴ cm⁻¹**

### Model Antwoord
- Correcte formule d·sin(θ) = m·λ ✓
- Las hoek correct af als 50° ✓
- **Identificeerde dit als m=2 in plaats van m=1** ✗
- Berekende d = 960/sin(50) = 1253 nm (2× te groot)
- Eindantwoord: 8,0 × 10³ cm⁻¹ (2× te klein)

### Analyse
**Conceptuele fout in diffractie-theorie**: Het model dacht dat het tellen van pieken (0, 1, 2) betekent dat de eerste zijpiek n=2 is. In werkelijkheid:
- Centrale piek = n=0 (nulde orde)
- Eerste zijpieken (±50°) = n=1 (eerste orde)
- Tweede zijpieken (indien zichtbaar) = n=2 (tweede orde)

### Beoordeling
**1/3 - Alle judges correct**

---

## Q21: Linac - Elektronenbanen Tekenen (2/3 vs 1/3)

### Opgave
"**Teken** in beide figuren op de uitwerkbijlage de baan die het elektron volgt door het magneetveld heen **en** na het verlaten van het magneetveld."

- Linker figuur: elektron met gemiddelde snelheid, boven in de bundel
- Rechter figuur: elektron met hogere snelheid, midden in de bundel

### CV Criteria
1. Linker figuur: elektron buigt >90° af (1 pt)
2. Rechter figuur: elektron buigt <90° af (1 pt)
3. Buiten veld: elektronen buigen niet verder af (rechte lijn) (1 pt)

### Model Antwoord (tekstueel, geen tekening)

**Linker figuur:**
> "Teken een lijn die begint op de linkerkant van het magneetveld... Laat deze lijn naar beneden en rechts afbuigen in een cirkelboog... Het elektron komt dus uit bij de onderkant van het magneetveld, maar meer naar links dan punt Q."

**Rechter figuur:**
> "Omdat de snelheid v hoger is, wordt de straal r groter... De lijn moet dus 'vlakkere' afbuigen... komt uit bij de rechterkant van het magneetveld."

**Na het veld:** Niet vermeld.

### Judge Disagreement
| Judge | Score | Redenering |
|-------|-------|------------|
| gemma-3-27b-it | 3/3 | Beschrijving volledig en correct |
| gemma-4-26b-a4b | 2/3 | Beide figuren correct, rechte lijn ontbreekt |
| gemma-4-31b | 2/3 | Beide figuren correct, rechte lijn ontbreekt |
| qwen/qwen3.6-27b | 2/3 | Beide figuren correct, rechte lijn ontbreekt |
| qwen/qwen3.6-35b-a3b | **1/3** | Linker figuur verkeerd geïnterpreteerd |

### Analyse
De self-judge interpreteerde "naar beneden en rechts afbuigen" als <90° afbuiging. Echter, de beschrijving "komt uit bij de onderkant... meer naar links dan Q" impliceert duidelijk >90° afbuiging:
- Elektron komt binnen van links bij P
- Elektron verlaat het veld aan de onderkant, links van Q
- Dit vereist een bocht van >90°

### Beoordeling
**2/3 is correct. Self-judge (1/3) te streng.**

Het model gaf een correcte fysische beschrijving van beide banen, maar:
1. Maakte geen daadwerkelijke tekening (LLM-beperking)
2. Vermeldde niet dat elektronen buiten het veld rechtdoor gaan

---

## Conclusies

### Systematische Problemen

1. **Snelheid vs. Positie (Q04)**: Het model verwarde kinematische concepten. Bij relatieve beweging moet snelheid vergeleken worden, niet positie.

2. **Diffractie-orde Identificatie (Q18)**: Conceptuele fout bij het tellen van diffractiemaxima. De eerste piek na het centrale maximum is altijd n=1.

3. **Grafisch Aflezen (Q13)**: Kleine afleesfouten bij het bepalen van punten op een trendlijn. Methodologie was correct.

4. **Tekenopdrachten (Q21)**: LLM-beperking - kan geen visuele output produceren. Tekstuele beschrijvingen waren grotendeels correct.

### Self-Judge Probleem

De self-judge (qwen3.6-35b-a3b) is systematisch **te streng**:
- Q13: 0/4 vs consensus 3/4 (-3 punten)
- Q21: 1/3 vs consensus 2/3 (-1 punt)
- Totaal: ~4-5 punten te streng

Dit suggereert dat dit model als judge te weinig partial credit geeft en te strikt vasthoudt aan exacte antwoorden.

### Vergelijking met Andere Modellen

| Model | Gemiddelde Score | Opmerkingen |
|-------|------------------|-------------|
| google/gemma-4-31b | 89.5% | Beste prestatie |
| qwen/qwen3.6-35b-a3b | 88.2%* | Sterk, enkele conceptuele fouten |
| google/gemma-4-26b-a4b | 82.9% | Goede reasoning |
| google/gemma-3-27b-it | 52-66% | Non-reasoning, significant zwakker |

*Gemiddelde van externe judges, exclusief te strenge self-judge.

### Aanbevelingen voor Verbetering

1. **Kinematica-context**: Verduidelijk bij bewegingsvragen of snelheid of positie relevant is
2. **Diffractie-terminologie**: Expliciet benoemen dat centrale maximum = orde 0
3. **Grafiek-interpretatie**: Meer aandacht voor nauwkeurig aflezen van trendlijnen
4. **Tekenopdrachten**: Erken beperking en geef zo gedetailleerd mogelijke tekstbeschrijving
