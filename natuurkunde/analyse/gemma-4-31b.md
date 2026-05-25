# Analyse Gemma-4-31b Fouten

## Overzicht

Gemma-4-31b behaalde **89.5%** op het VWO natuurkunde examen (vw-1023-a-26-1-o), het hoogste van alle geteste modellen. Hieronder een analyse van de vragen waar punten verloren gingen.

## Cross-validatie Scores

| Judge | Score | Max | % |
|-------|-------|-----|---|
| Gemma-4-31b | 68 | 76 | 89.5% |
| Qwen 3.6-35b | 68 | 76 | 89.5% |

## Verloren Punten

| Vraag | Score | Probleem |
|-------|-------|----------|
| Q21 | 0/3 | Tekst in plaats van tekening |
| Q02 | 0/2 | Methode niet gevolgd |
| Q22 | 1/3 | Verkeerde B-richting |
| Q04 | 1/2 | Onbekend |
| Q18 | 1-2/3 | Onbekend |

---

## Q21: Elektronenbanen Tekenen (0/3)

### Opgave
"**Teken** in beide figuren op de uitwerkbijlage de baan die het elektron volgt door het magneetveld heen **en** na het verlaten van het magneetveld."

### CV Criteria
1. Linker figuur: elektron buigt >90° af (1 pt)
2. Rechter figuur: elektron buigt <90° af (1 pt)
3. Buiten veld: elektronen buigen niet verder af (1 pt)

### Gemma-4-31b Antwoord
Het model gaf een uitgebreide **tekstuele uitleg** over hoe de banen getekend moeten worden, inclusief correcte fysica (r = mv/Bq), maar maakte **geen daadwerkelijke tekening**.

### Beoordeling
**0/3 - Correct beoordeeld door beide judges**

Dit is een fundamentele beperking van tekst-gebaseerde LLMs: ze kunnen geen visuele output produceren. Het model begrijpt de fysica volledig maar kan de opdracht niet uitvoeren.

---

## Q02: Meetnauwkeurigheid Bepalen (0/2)

### CV Criteria
1. Schatten van de meetnauwkeurigheid op het beeldje tussen 0,5 en 2 mm (1 pt)
2. Completeren van de bepaling via schaalberekening (1 pt)

### CV Methode
1. Meet de balk op de uitwerkbijlage (bijv. 45 mm)
2. Schat meetnauwkeurigheid op papier (bijv. 1 mm)
3. Bereken: 0,91 × (1/45) = 0,02 m = 2 cm

### Gemma-4-31b Antwoord
Het model gebruikte een **alternatieve visuele methode**: het vergeleek de breedte van de markeringen met de segmenten van de balk en schatte "±2 tot 5 cm".

### Judge Disagreement
- **Gemma-4-31b judge**: 0/2 - methode niet gevolgd
- **Qwen judge**: 2/2 - juist antwoord, valide redenering

### Mijn Beoordeling
**0-1/2 - Gemma-4-31b judge is correcter**

Het CV vraagt expliciet om:
1. Een mm-schatting op het beeldje (niet gedaan)
2. Een schaalberekening (niet gedaan)

Hoewel het eindantwoord (2-5 cm) in de buurt komt, werd de vereiste methode niet gevolgd.

---

## Q22: Magneetveld Richting (1/3)

### CV Criteria
1. Bepalen richting B met richtingregel (1 pt)
2. Inzicht verband tussen r en B (1 pt)
3. Consequente keuze van het plaatje (1 pt)

### CV Antwoord
- Magneetveld komt **uit het papier** (⊙)
- Straal wordt kleiner naar rechtsboven → B daar sterker
- Juiste antwoord: **Plaatje IV**

### Gemma-4-31b Antwoord
- Stelde dat B **het papier in** gaat (×) - **FOUT**
- Gaf correcte uitleg over r-B verband ✓
- Koos **Plaatje II** - **FOUT**

### Fysica-analyse
Voor een elektron (negatieve lading) dat naar rechts beweegt en tegen de klok in afbuigt:
- F = qv × B (met q negatief)
- v wijst naar rechts
- F wijst initieel omhoog
- Dus v × B wijst omlaag, wat betekent B uit het papier (⊙)

Het model maakte een teken-fout in de Lorentzkracht analyse.

### Beoordeling
**1/3 - Correct beoordeeld door beide judges**

---

## Conclusies

### Systematische Problemen

1. **Teken-opdrachten (Q21)**: Fundamentele LLM-beperking - tekst-modellen kunnen geen visuele output produceren. Dit probleem is onoplosbaar zonder multimodale output-capaciteit.

2. **Methode-vereisten (Q02)**: Het model neemt soms shortcuts door visueel te schatten in plaats van de gevraagde berekeningsmethode te volgen. Dit kan leiden tot correcte antwoorden maar geen punten volgens het CV.

3. **Complexe 3D-vectoranalyse (Q22)**: Bij Lorentzkracht-problemen met meerdere richtingen kan het model fouten maken in de tekenconventies.

### Vergelijking met Andere Modellen

| Model | Type | Score |
|-------|------|-------|
| Gemma-4-31b | Reasoning | 89.5% |
| Qwen 3.6-35b | Reasoning | 86.9% |
| Gemma-4-26b | Reasoning | 82.2% |
| Gemma-3-27b | Non-reasoning | 56.6% |

De reasoning-capaciteit blijkt cruciaal voor VWO natuurkunde examens. Het verschil tussen reasoning (80-90%) en non-reasoning (57%) modellen is dramatisch.
