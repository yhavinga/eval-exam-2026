# Analyse Gemma-4-26b-a4b Fouten

## Overzicht

Gemma-4-26b-a4b behaalde **77.6-85.5%** op het VWO natuurkunde examen (vw-1023-a-26-1-o). Dit is een reasoning model dat consistent presteert maar enkele karakteristieke fouten maakt bij grafiekinterpretatie en formulekeuze.

## Cross-validatie Scores

| Judge | Score | Max | % |
|-------|-------|-----|---|
| google/gemma-3-27b-it | 65 | 76 | 85.5% |
| google/gemma-4-26b-a4b (self) | 63 | 76 | 82.9% |
| google/gemma-4-31b | 63 | 76 | 82.9% |
| qwen/qwen3.6-35b-a3b | 59 | 76 | 77.6% |

**Opmerking**: qwen3.6-35b-a3b is opnieuw de strengste judge (-6 punten t.o.v. gemiddelde).

## Verloren Punten per Vraag

| Vraag | Consensus Score | Probleem |
|-------|-----------------|----------|
| Q04 | 0/2 | Snelheid vs positie verwarring (zelfde als andere modellen) |
| Q05 | 1/3 | Verkeerd tijdsinterval voor vertraging |
| Q15 | 2-3/4 | Periode net buiten marge (5.0 vs 5.4 dagen) |
| Q22 | 1/3 | r-B relatie niet besproken, geen specifieke plaatje-keuze |
| Q24 | 0-1/2 | Verkeerde formule (Beer-Lambert i.p.v. halveringsdikte) |

---

## Q04: Botsproef - Aya's Conclusie (0/2)

### Opgave
"Leg met behulp van figuur 3 uit of Aya gelijk heeft." (Aya beweert dat relatieve beweging stopt na t = 0,34 s)

### CV Criteria
1. Inzicht dat **snelheden** van M en S vergeleken moeten worden (1 pt)
2. Consequente conclusie (1 pt)

### Model Antwoord
Het model telde frames in figuur 3 en concludeerde dat Aya **gelijk** heeft omdat marker S na 17 frames terugkeert naar x=0.

### Analyse
**Zelfde fundamentele fout als qwen3.6-35b-a3b**: Het model verwarde positie met snelheid. Relatieve beweging stopt wanneer v_S = v_M, niet wanneer x_S = 0. Op t=0,34s is v_S nog steeds groter dan v_M, dus S beweegt nog steeds t.o.v. M.

**Aya heeft ongelijk.**

### Beoordeling
**0/2 - Alle judges correct**

---

## Q05: Botsproef - Gemiddelde Vertraging (1/3)

### Opgave
"Bereken de gemiddelde horizontale vertraging van S tijdens het deel van de beweging waarin S vertraagt tot aan het moment dat de bewegingsrichting omkeert."

### CV Criteria
1. Gebruik formule a_gem = Δv/Δt (1 pt)
2. Bepalen tijdsduur van begin vertraging tot omkeerpunt (1 pt)
3. Completeren berekening met juiste significantie (1 pt)

### CV Methode
- Vertraging begint bij t = 0,040 s (waar v begint te dalen vanaf 4,0 m/s)
- Omkeerpunt bij t = 0,120 s (waar v = 0)
- Δt = 0,080 s
- a = (0 - 4,0) / 0,080 = **-50 m/s²**

### Model Antwoord
- Gebruikte correcte formule a = Δv/Δt ✓
- Maar koos verkeerd interval: t = 0 tot t = 0,2 s
- Las af: v(0) = 4 m/s, v(0,2) = -1 m/s
- Berekende: a = (-1 - 4) / 0,2 = **-25 m/s²**

### Analyse
Het model maakte twee fouten bij het aflezen van de grafiek:
1. **Startpunt verkeerd**: De vertraging begint niet bij t=0 maar bij t≈0,04s waar de snelheid begint te dalen
2. **Eindpunt verkeerd**: Het omkeerpunt (v=0) ligt bij t≈0,12s, niet bij t=0,2s

Hierdoor is het tijdsinterval 2,5× te groot en de berekende vertraging 2× te klein.

### Beoordeling
**1/3 - Alle judges correct**

---

## Q15: Cepheïden - Afstand tot KMW (2-3/4)

### Opgave
1. Bepaal de periode T van Delta Cephei uit de grafiek
2. Bepaal de afstand tot de KMW

### CV Criteria
1. Bepalen T tussen 5,2 en 5,6 dagen (1 pt)
2. Consequent bepalen van I_max in de KMW (1 pt)
3. Gebruik van de kwadratenwet (1 pt)
4. Completeren bepaling met juiste significantie (1 pt)

### CV Antwoord
- T = 5,4 dagen
- d = 1,1 × 10²¹ m (marge 0,1 × 10²¹)

### Model Antwoord
- Bepaalde T = **5,0 dagen** (buiten marge 5,2-5,6)
- Las I_max af bij log(T) = log(5) ≈ 0,7 i.p.v. log(5,4) ≈ 0,73
- Gebruikte kwadratenwet correct ✓
- Einantwoord: 1,4 × 10²¹ m (buiten marge)

### Judge Scores
| Judge | Score | Redenering |
|-------|-------|------------|
| gemma-3-27b-it | 2/4 | T en eindantwoord buiten marge |
| gemma-4-26b-a4b | 2/4 | T buiten marge, methode correct |
| gemma-4-31b | 3/4 | Methode grotendeels correct |
| qwen/qwen3.6-35b-a3b | 1/4 | Streng op alle criteria |

### Analyse
De kern van de fout zit in het aflezen van de periode. Het model las de pieken af bij t ≈ 4, 9, 14, 19 dagen en berekende T = 5 dagen. Een nauwkeuriger aflezing zou T ≈ 5,4 dagen geven.

### Beoordeling
**2/4 is fair** - Methode correct, maar periode-aflezing net buiten marge waardoor eindantwoord ook afwijkt.

---

## Q22: Linac - Magneetveld Richting (1/3)

### Opgave
"Leg uit welk plaatje in figuur 5 een geschikt magneetveld weergeeft."

### CV Criteria
1. Bepalen richting B met richtingregel (1 pt)
2. Inzicht in verband tussen r en B (1 pt)
3. Consequente keuze van het plaatje (1 pt)

### CV Antwoord
- B komt uit het papier (⊙)
- Straal wordt kleiner naar rechtsboven → B is daar sterker
- Juiste antwoord: **Plaatje IV**

### Model Antwoord
- Correct bepaald dat B uit het papier komt ✓
- Analyseerde dat figuren III en IV beide ⊙ hebben
- Concludeerde: "figuur III en IV zijn geschikt"
- **Miste**: r-B relatie (kleinere straal = sterker veld)
- **Miste**: Specifieke keuze voor plaatje IV

### Analyse
Het model deed de Lorentzkracht-analyse correct maar stopte te vroeg:
1. Richting B correct (uit papier) ✓
2. Vergat te analyseren waarom de straal verandert langs de baan
3. Koos daarom niet specifiek tussen III en IV

De vraag vereist ook inzicht dat r = mv/Bq, dus kleinere r betekent groter B. In figuur 4 wordt de straal kleiner naar rechtsboven, dus B moet daar sterker zijn. Alleen plaatje IV toont een veld dat sterker wordt naar rechtsboven.

### Beoordeling
**1/3 - Judges correct**

---

## Q24: Linac - Filterdikte (0-1/2)

### Opgave
"Bereken hoe dik het filter in het midden moet zijn."
(Filter moet intensiteit reduceren van 100% naar 38%)

### CV Criteria
1. Gebruik formule I = I₀ × (½)^(d/d½) met opzoeken d½ (1 pt)
2. Completeren berekening (1 pt)

### CV Methode
- Opzoeken in Binas: d½ = 2,1 cm voor ijzer bij 2,0 MeV
- Oplossen: 0,38 = (½)^(d/2,1)
- d = 2,1 × log(0,38)/log(0,5) = **2,9 cm**

### Model Antwoord
- Gebruikte **Beer-Lambert wet**: I = I₀ × e^(-μx)
- Zocht niet d½ op in Binas
- Raadde μ ≈ 0,34 cm⁻¹
- Kreeg x ≈ 2,84 cm (toevallig dicht bij juiste antwoord)

### Analyse
Het model koos de verkeerde fysische benadering:
- **CV verwacht**: Halveringsdikte-formule met Binas-tabel
- **Model gebruikte**: Beer-Lambert met geschatte μ

Hoewel beide formules wiskundig equivalent zijn (μ = ln(2)/d½), vraagt het examen expliciet om de halveringsdikte-methode met Binas-opzoekwerk. Het model kon μ niet opzoeken en moest raden.

### Judge Scores
| Judge | Score |
|-------|-------|
| gemma-3-27b-it | 1/2 |
| gemma-4-26b-a4b | 1/2 |
| gemma-4-31b | 0/2 |
| qwen/qwen3.6-35b-a3b | 0/2 |

### Beoordeling
**0-1/2** - Verkeerde methode, geen Binas-gebruik. Sommige judges geven partial credit voor correcte wiskundige aanpak.

---

## Conclusies

### Systematische Problemen

1. **Snelheid vs. Positie (Q04)**: Zelfde fout als andere modellen - fundamenteel fysica-concept niet correct toegepast.

2. **Grafiek-intervalherkenning (Q05, Q15)**: Het model heeft moeite met het identificeren van de juiste intervallen op grafieken:
   - Q05: Verkeerde start- en eindpunten voor vertraging
   - Q15: Periode net buiten acceptabele marge

3. **Onvolledige analyse (Q22)**: Het model stopt soms te vroeg in de redenering en mist secundaire inzichten (r-B relatie).

4. **Formulekeuze (Q24)**: Bij stralingsabsorptie koos het model Beer-Lambert i.p.v. de verwachte halveringsdikte-methode met Binas.

### Vergelijking met Andere Modellen

| Fout | gemma-4-26b-a4b | qwen3.6-35b-a3b | gemma-4-31b |
|------|-----------------|-----------------|-------------|
| Q04 (v vs x) | ✗ | ✗ | ✗* |
| Q05 (interval) | ✗ | ✓ | ✓ |
| Q13 (grafiek a) | ✓ | ✗ | ✓ |
| Q18 (diffractie n) | ✓ | ✗ | ✓ |
| Q22 (r-B relatie) | ✗ | ✗ | ✗ |

*gemma-4-31b niet getest op Q04

### Sterke Punten

- Correcte toepassing van Lorentzkracht-richtingregel
- Goede beheersing van kwadratenwet voor intensiteit
- Correcte wiskundige bewerkingen (logaritmen, exponenten)

### Aanbevelingen

1. **Grafiekinterpretatie**: Meer aandacht voor het identificeren van relevante intervallen
2. **Volledigheid**: Doordenken of alle aspecten van een vraag beantwoord zijn
3. **Binas-gebruik**: Bij stralingsvragen de halveringsdikte-methode prefereren
