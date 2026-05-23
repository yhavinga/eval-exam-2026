# Analyse Qwen 3.6-27b Fouten

## Overzicht

Qwen 3.6-27b behaalde **93.4%** op het VWO natuurkunde examen (vw-1023-a-26-1-o) volgens gemma-4-31b - de **hoogste score** van alle geteste modellen. Slechts 5 punten verloren op 3 vragen.

## Cross-validatie Scores

| Judge | Score | Max | % |
|-------|-------|-----|---|
| google/gemma-4-31b | 71 | 76 | **93.4%** |
| qwen/qwen3.6-27b (self) | 66 | 76 | 86.8% |

## Verloren Punten

| Vraag | Score | Verloren | Probleem |
|-------|-------|----------|----------|
| Q04 | 0/2 | 2 | Snelheid vs positie (zelfde fout als alle modellen) |
| Q05 | 1/3 | 2 | Verkeerd startpunt tijdsinterval |
| Q24 | 1/2 | 1 | Beer-Lambert i.p.v. halveringsdikte |

**Totaal verloren: 5 punten**

---

## Q04: Botsproef - Aya's Conclusie (0/2)

### CV Vereiste
Vergelijk **snelheden** van M en S op t=0,34s → Aya heeft **ongelijk**

### Model Antwoord
Concludeerde Aya heeft **gelijk** op basis van positie x terugkerend naar 0.

### Analyse
Zelfde fundamentele fout als **alle andere modellen**. Dit is blijkbaar een systematisch probleem: LLMs verwarren positie met snelheid bij relatieve bewegingsvragen.

### Beoordeling
**0/2 - Judge correct**

---

## Q05: Botsproef - Gemiddelde Vertraging (1/3)

### CV Vereiste
- Formule a = Δv/Δt ✓
- Tijdsduur van **t=0,04s tot t=0,12s** (Δt = 0,08s)
- Antwoord: **50 m/s²** (±6)

### Model Antwoord
- Correcte formule ✓
- Maar begon bij **t=0** i.p.v. t=0,04s
- Δt = 0,13s (te groot)
- Antwoord: **31 m/s²** (buiten marge)

### Analyse
Het model las niet correct dat de vertraging pas begint bij t≈0,04s waar de snelheid begint te dalen vanaf het plateau. Dit is dezelfde fout als gemma-4-26b-a4b maakte.

### Beoordeling
**1/3 - Judge correct**

---

## Q24: Linac - Filterdikte (1/2)

### CV Vereiste
- Gebruik halveringsdikte-formule: I = I₀ × (½)^(d/d½)
- Opzoeken d½ = 2,1 cm uit Binas
- Antwoord: **2,9 cm**

### Model Antwoord
- Gebruikte Beer-Lambert: I = I₀ × e^(-μx)
- Berekende μ uit massa-absorptiecoëfficiënt (externe bron)
- Antwoord: **2,1 cm** (fout)

### Analyse
De methode is fysisch equivalent maar het model gebruikte verkeerde waarden voor μ (niet uit Binas). Dit is dezelfde fout als gemma-4-26b-a4b.

### Beoordeling
**1/2 - Judge correct** (punt voor correcte formule-opzet)

---

## Vergelijking met Andere Modellen

| Vraag | qwen3.6-27b | qwen3.6-35b | gemma-4-31b | gemma-4-26b |
|-------|-------------|-------------|-------------|-------------|
| Q04 (v vs x) | 0/2 | 0/2 | 0/2* | 0/2 |
| Q05 (interval) | 1/3 | 3/3 | 3/3 | 1/3 |
| Q24 (Binas) | 1/2 | 2/2 | 2/2 | 0-1/2 |

*gemma-4-31b werd niet beoordeeld op Q04 door zichzelf

### Opvallend
- **Q04**: Alle modellen maken dezelfde fout - dit lijkt een fundamentele LLM-beperking
- **Q05 & Q24**: qwen3.6-27b maakt dezelfde fouten als gemma-4-26b-a4b

---

## Conclusies

### Sterke Punten qwen3.6-27b
1. **Hoogste totaalscore** (93.4%)
2. **Slechts 3 fouten** op 25 vragen
3. **Perfecte scores** op alle complexe vragen (Q13, Q15, Q16, Q17, Q21, Q22)
4. Uitstekende reasoning en grafiek-interpretatie

### Systematische Problemen (gedeeld met andere modellen)
1. **Q04 (snelheid vs positie)**: Alle LLMs falen hierop - fundamentele conceptuele verwarring
2. **Grafiek-intervalherkenning**: Moeite met identificeren waar een fase precies begint
3. **Binas-gebruik**: Prefereert algemene fysica-methodes boven examspecifieke tabellen

### Model Ranking (na alle analyses)

| Rank | Model | Score (gemma-4-31b judge) |
|------|-------|---------------------------|
| 🥇 | **qwen/qwen3.6-27b** | **93.4%** |
| 🥈 | google/gemma-4-31b | 89.5% |
| 🥉 | qwen/qwen3.6-35b-a3b | 88.2% |
| 4 | google/gemma-4-26b-a4b | 82.9% |
| 5 | google/gemma-3-27b-it | 52.6% |

### Aanbeveling
**qwen3.6-27b** is het beste model voor VWO natuurkunde examens, met **gemma-4-31b** als beste judge.
