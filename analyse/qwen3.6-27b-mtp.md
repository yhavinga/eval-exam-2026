# Analyse Qwen 3.6-27b MTP (Multi-Token Prediction)

## Overzicht

Qwen 3.6-27b-mtp is een Multi-Token Prediction variant van het beste model (qwen/qwen3.6-27b). MTP is een speculative decoding techniek die normaal inferentie versnelt. **Voor reasoning models blijkt MTP echter zowel langzamer als slechter te presteren.**

## Score

| Model | Score | Max | % |
|-------|-------|-----|---|
| qwen/qwen3.6-27b (origineel) | 34 | 38 | **89.5%** |
| qwen3.6-27b-mtp | 21 | 38 | **55.3%** |

*Gebaseerd op 14 vragen (Q01-Q14) - run voortijdig gestopt wegens slechte prestaties*

## Snelheidsvergelijking

| Vraag | MTP | Orig | Verschil |
|-------|-----|------|----------|
| Q01 | 97s | 57s | +69% |
| Q02 | 358s | 326s | +10% |
| Q03 | 416s | 242s | +72% |
| Q04 | 405s | 226s | +79% |
| Q05 | 480s | 232s | +107% |
| Q06 | 708s | 69s | **+926%** |
| Q07 | 322s | 307s | +5% |
| Q08 | 363s | 118s | +208% |
| Q09 | 713s | 61s | **+1072%** |
| Q10 | 209s | 62s | +240% |
| Q11 | 85s | 226s | **-62%** ✓ |
| Q12 | 253s | 110s | +131% |
| **Totaal** | **4408s** | **2035s** | **+117%** |

**MTP is gemiddeld 2x langzamer** - slechts 1 van 12 vragen was sneller.

## Scorevergelijking per Vraag

| Vraag | MTP | Orig | Verschil |
|-------|-----|------|----------|
| Q01 | 3/3 | 3/3 | = |
| Q02 | 0/2 | 2/2 | **-2** |
| Q03 | 0/2 | 2/2 | **-2** |
| Q04 | 1/2 | 0/2 | +1 |
| Q05 | 0/3 | 1/3 | -1 |
| Q06 | 0/4 | 4/4 | **-4** |
| Q07 | 3/3 | 3/3 | = |
| Q08 | 4/4 | 4/4 | = |
| Q09 | None | 3/3 | ? |
| Q10 | 3/3 | 3/3 | = |
| Q11 | 3/3 | 3/3 | = |
| Q12 | 1/3 | 3/3 | **-2** |
| Q13 | 1/4 | 4/4 | **-3** |
| Q14 | 2/2 | 2/2 | = |

**Verloren punten: 13** (van 38 mogelijk op vergelijkbare vragen)

---

## Kritieke Problemen

### 1. Gelekte Interne Reasoning (Q06)

**MTP Response bevat:**
```
...horizontal direction? No wait... Let me re-read carefully again:
"de lengte van the remweg in horizontale richting"). This means
displacement during this interval is constant acceleration phase.

### Derivation Strategy
```

Het model's interne denkproces lekt door naar het uiteindelijke antwoord. Dit is een ernstig kwaliteitsprobleem dat niet voorkomt bij de standaard versie.

### 2. Incomplete Antwoorden

Meerdere vragen die de originele versie perfect beantwoordde, krijgen nu 0 punten:
- **Q02**: Geen concrete mm-schatting gegeven
- **Q03**: Berekening niet voltooid
- **Q05**: Verkeerd tijdsinterval
- **Q06**: Afleiding niet correct afgerond door gelekte reasoning

### 3. None/None Judgement (Q09)

Q09 kon niet beoordeeld worden - waarschijnlijk een onbruikbaar antwoord.

---

## Waarom MTP Faalt voor Reasoning Models

### Speculative Decoding Overhead
MTP voorspelt meerdere tokens tegelijk en verifieert deze achteraf. Bij lange, complexe reasoning chains:
1. Voorspellingen zijn vaak incorrect → veel verwerpingen
2. Overhead van verificatie weegt niet op tegen winst
3. Resulteert in **langzamere** inferentie

### Token-Niveau Interferentie
De multi-token voorspelling lijkt te interfereren met het reasoning-proces:
1. Interne gedachten lekken naar output
2. Reasoning chains worden onderbroken
3. Conclusies worden niet bereikt

### Optimaal Gebruik van MTP
MTP werkt beter voor:
- Korte, voorspelbare outputs
- Non-reasoning taken (vertaling, samenvattingen)
- Outputs met repetitieve patronen

---

## Vergelijking met Andere Modellen

| Model | Score | Opmerking |
|-------|-------|-----------|
| qwen/qwen3.6-27b | 93.4% | Best presterende model |
| google/gemma-4-31b | 89.5% | Beste judge |
| qwen/qwen3.6-35b-a3b | 88.2% | |
| google/gemma-4-26b-a4b | 82.9% | |
| gemma-4-31b-opus-distill | 56.6% | |
| **qwen3.6-27b-mtp** | **55.3%*** | MTP variant |
| google/gemma-3-27b-it | 52.6% | |
| google/gemma-4-e4b | 40.8% | |
| nvidia/nemotron-3-nano-omni | 20.0% | |

*Op 14 van 25 vragen

---

## Conclusie

**MTP is niet geschikt voor reasoning models.**

De qwen3.6-27b-mtp variant presteert:
- **2x langzamer** dan het origineel
- **34 procentpunt slechter** (55% vs 89%)
- Met **kwaliteitsproblemen** (gelekte reasoning)

### Aanbeveling
Gebruik altijd de **standaard qwen/qwen3.6-27b** voor VWO examens. MTP optimaliseert voor snelheid bij simpele taken, maar degradeert zowel snelheid als kwaliteit bij complexe reasoning.

### Technische Notitie
De test is voortijdig gestopt na Q14 vanwege de duidelijke negatieve resultaten. Verdere testing zou waarschijnlijk vergelijkbare of slechtere resultaten opleveren.
