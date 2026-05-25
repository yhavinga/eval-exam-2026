# Analyse Gemma-4-31B vLLM MTP

## Overzicht

Deze analyse vergelijkt dezelfde Gemma-4-31B op twee inference stacks:
- **LMStudio** met Q4_K_M GGUF quantisatie
- **vLLM** met Intel int4-AutoRound quantisatie + Multi-Token Prediction (MTP)

## Hardware & Software Stack

### Hardware
| Component | Specificatie |
|-----------|--------------|
| GPUs | 2× NVIDIA RTX 3090 (24GB elk, PCIe, geen NVLink) |
| Platform | Ubuntu 22.04 LTS |
| Driver | NVIDIA 595+ (CUDA 13.2) |
| Stroomverbruik | ~500W tijdens inferentie |

### Model Configuratie

| Component | Model | Grootte |
|-----------|-------|---------|
| Target | Intel/gemma-4-31B-it-int4-AutoRound | ~21 GB |
| Draft (MTP) | google/gemma-4-31B-it-assistant | ~0.5B / 927 MB BF16 |

### vLLM Configuratie

```bash
vllm serve Intel/gemma-4-31B-it-int4-AutoRound \
  --tensor-parallel-size 2 \
  --dtype bfloat16 \
  --gpu-memory-utilization 0.92 \
  --max-model-len 32768 \
  --max-num-seqs 4 \
  --disable-custom-all-reduce \
  --speculative-config '{"model": "google/gemma-4-31B-it-assistant", "num_speculative_tokens": 4}' \
  --reasoning-parser gemma4
```

**RTX 3090-specifieke settings:**
- `--disable-custom-all-reduce`: Vereist voor CUDA graphs zonder NVLink
- `NCCL_P2P_DISABLE=1`: PCIe communicatie i.p.v. NVLink
- `NCCL_CUMEM_ENABLE=0`: Memory allocatie compatibiliteit

**MTP Performance:**
- Generation: ~57+ tok/s
- MTP acceptance rate: 80-100%
- VRAM per GPU: ~21.5 GB

---

## Inference Snelheid Vergelijking

### Per Examen (25 vragen)

| Stack | Gem. tijd/vraag | Totale tijd | Speedup |
|-------|-----------------|-------------|---------|
| LMStudio Q4_K_M | 87.2s | 36.3 min | 1.0× |
| **vLLM int4-MTP** | **28.6s** | **11.9 min** | **3.0×** |

### Per Vraag Detail

| Vraag | LMStudio | vLLM | Speedup |
|-------|----------|------|---------|
| Q01 | 48.6s | 10.0s | 4.9× |
| Q08 | 161.7s | 21.7s | **7.4×** |
| Q11 | 128.0s | 22.3s | 5.7× |
| Q21 | 68.7s | 67.3s | 1.0× |
| Q13 | 103.4s | 72.5s | 1.4× |

**Observaties:**
- Speedup varieert van 1.0× tot 7.4× afhankelijk van de vraag
- Kortere antwoorden profiteren meer van MTP (hogere acceptance rate)
- Lange reasoning chains (Q21, Q13) hebben lagere speedup

---

## Judge Resultaten

### Score Vergelijking

| Answer Stack | Judge Stack | Score | Percentage |
|--------------|-------------|-------|------------|
| LMStudio | LMStudio (gemma-4-31b) | 68/76 | 89.5% |
| vLLM-int4 | vLLM-int4 (gemma-4-31b) | 73/76 | **96.1%** |

**Analyse van het verschil (6.6 procentpunt):**

| Vraag | LM score | vLLM score | Verklaring |
|-------|----------|------------|------------|
| Q21 | 0/3 | 3/3 | **Judge-inconsistentie**: LMStudio judge gaf zichzelf 0/3, maar andere modellen 3/3 voor identieke tekstbeschrijvingen |
| Q18 | 2/3 | 3/3 | **Beter antwoord**: vLLM las grafiek nauwkeuriger (50° vs 53°) |
| Q25 | 3/3 | 2/3 | **Striktere judge**: vLLM judge correcter volgens CV |

**Gecorrigeerde schatting:** Als de LMStudio judge consistent was geweest op Q21 (+3 punten), zou de score **93.4%** zijn (71/76) - vergelijkbaar met vLLM (96.1% - 1 op Q25 = 94.7%).

### Steekproef Analyse

#### Q18 (Morphodidius - diffractierooster): Antwoord verschil
| Aspect | LMStudio | vLLM |
|--------|----------|------|
| Afgelezen hoek | 53° (buiten range) | 50° (correct) |
| Score | 2/3 | 3/3 |
| Reden | Grafiek minder nauwkeurig afgelezen | Grafiek correct afgelezen |

**Conclusie:** vLLM int4 quantisatie presteert minstens zo goed als Q4_K_M op vision-taken.

#### Q21 (Linac - tekenvraag): Judge inconsistentie
| Model beoordeeld | LMStudio judge | Score |
|------------------|----------------|-------|
| qwen/qwen3.6-27b | Tekstbeschrijving geaccepteerd | 3/3 |
| google/gemma-4-26b-a4b | Tekstbeschrijving geaccepteerd | 3/3 |
| mistral-large-2512 | Tekstbeschrijving geaccepteerd | 3/3 |
| **google/gemma-4-31b (zichzelf)** | "Moet tekening zijn" | **0/3** |

De LMStudio judge was **inconsistent**: gaf andere modellen 3/3 voor vergelijkbare tekstbeschrijvingen, maar zichzelf 0/3. De vLLM judge (3/3) was juist consistent met hoe de LMStudio judge andere modellen beoordeelde.

**Conclusie:** Geen judge-soepelheid verschil, maar LMStudio judge-inconsistentie op eigen antwoord.

#### Q25 (Flattening filter): Judge verschil
| Aspect | LMStudio judge | vLLM judge |
|--------|----------------|------------|
| Punt 3 (randen tegengesteld) | "Convex impliceert dit" → 3/3 | "Niet expliciet benoemd" → 2/3 |

**Conclusie:** vLLM judge is hier juist strikter en correcter volgens CV.

---

## Reasoning Output

vLLM vereist specifieke configuratie voor Gemma-4 reasoning:

```python
extra_body = {
    "chat_template_kwargs": {"enable_thinking": True},
    "skip_special_tokens": False
}
```

De reasoning wordt correct geparsed uit het `reasoning` veld (vs `reasoning_content` bij LMStudio).

| Stack | Reasoning veld | Gem. reasoning lengte |
|-------|----------------|----------------------|
| LMStudio | `reasoning_content` | ~5000 chars |
| vLLM | `reasoning` | ~6000 chars |

---

## Kosten Analyse

| Stack | Tijd/examen | Stroomverbruik | Kosten/examen* |
|-------|-------------|----------------|----------------|
| LMStudio | 36.3 min | ~500W | ~€0.21 |
| **vLLM MTP** | **11.9 min** | ~500W | **~€0.07** |

*Gebaseerd op €0.35/kWh

---

## Conclusies

### vLLM + MTP voordelen
1. **3× sneller** dan LMStudio op dezelfde hardware
2. **Zelfde of betere kwaliteit** - int4-AutoRound ≥ Q4_K_M
3. **Betere vision-interpretatie** op sommige vragen (Q18)
4. **70% lagere stroomkosten** per examen

### Aandachtspunten
1. **Judge inconsistentie** - LMStudio judge beoordeelde eigen model strenger dan andere modellen (Q21: 0/3 vs 3/3 voor vergelijkbare antwoorden)
2. **MTP speedup varieert** - 1.0× tot 7.4× afhankelijk van antwoordlengte
3. **Setup complexer** - vereist specifieke NCCL en CUDA graph configuratie
4. **Max context 32K** - vs 128K+ mogelijk met LMStudio (afhankelijk van VRAM)

### Aanbeveling

Voor productie-gebruik met Gemma-4-31B:
- **vLLM + int4-AutoRound + MTP** is de beste keuze
- 3× sneller, vergelijkbare kwaliteit, lagere kosten
- LMStudio alleen voor prototyping of als vLLM setup te complex is
