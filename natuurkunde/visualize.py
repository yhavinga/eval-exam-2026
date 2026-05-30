#!/usr/bin/env python3
"""Generate Tufte-style benchmark visualizations for VWO exam evaluation."""

import sqlite3
import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path
import numpy as np

# Tufte style: maximize data-ink ratio, remove chartjunk
mpl.rcParams['font.family'] = 'sans-serif'
mpl.rcParams['font.size'] = 9
mpl.rcParams['axes.spines.top'] = False
mpl.rcParams['axes.spines.right'] = False
mpl.rcParams['axes.spines.left'] = False
mpl.rcParams['axes.linewidth'] = 0.5
mpl.rcParams['xtick.major.width'] = 0.5
mpl.rcParams['ytick.major.width'] = 0.5
mpl.rcParams['figure.facecolor'] = 'white'
mpl.rcParams['axes.facecolor'] = 'white'
mpl.rcParams['savefig.facecolor'] = 'white'

# Colors: minimal, functional
LOCAL_COLOR = '#666666'  # gray for local models
CLOUD_COLOR = '#2563eb'  # blue for cloud models
VLLM_COLOR = '#059669'   # green for vLLM optimized


def save_both(fig: plt.Figure, base_path: Path):
    """Save figure as both SVG and PNG."""
    fig.savefig(str(base_path) + ".svg", bbox_inches='tight', pad_inches=0.1)
    fig.savefig(str(base_path) + ".png", bbox_inches='tight', dpi=150, pad_inches=0.1)
    plt.close(fig)
    print(f"  Saved {base_path.name}.svg and .png")


def plot_model_ranking(db_path: str) -> plt.Figure:
    """Horizontal bar chart of model scores, colored by local/cloud/vllm."""
    conn = sqlite3.connect(db_path)
    # Group by model AND stack to show vLLM separately
    # Use best available judge for each stack
    rows = conn.execute("""
        SELECT a.model,
               ROUND(100.0 * SUM(j.score) / SUM(j.max_score), 1) as pct,
               a.inference_stack
        FROM answers a
        JOIN judgements j ON j.answer_id = a.id
        WHERE j.score IS NOT NULL
          AND ((a.inference_stack != 'vllm-int4' AND j.judge_model = 'google/gemma-4-31b')
               OR (a.inference_stack = 'vllm-int4' AND j.judge_model = 'gemma-4-31b'))
        GROUP BY a.model, a.inference_stack
        ORDER BY pct DESC
    """).fetchall()
    conn.close()

    models = [r[0] for r in rows]
    scores = [r[1] for r in rows]
    stacks = [r[2] for r in rows]

    def get_color(stack):
        if stack == 'openrouter':
            return CLOUD_COLOR
        elif stack == 'vllm-int4':
            return VLLM_COLOR
        return LOCAL_COLOR

    colors = [get_color(s) for s in stacks]

    fig, ax = plt.subplots(figsize=(8, 5))
    y_pos = np.arange(len(models))
    bars = ax.barh(y_pos, scores, color=colors, height=0.7, edgecolor='none')

    # Direct labels on bars
    for i, (bar, score, stack) in enumerate(zip(bars, scores, stacks)):
        label = f"{score}%"
        if stack == 'openrouter':
            label += " (cloud)"
        elif stack == 'vllm-int4':
            label += " (vLLM)"
        ax.text(score + 0.5, i, label, va='center', fontsize=8, color='#333333')

    # Clean model names for y-axis
    clean_names = []
    for m, stack in zip(models, stacks):
        name = m.replace('google/', '').replace('qwen/', '').replace('openai/', '')
        name = name.replace('mistralai/', '').replace('nvidia/', '')
        if stack == 'vllm-int4':
            name += ' (vLLM+MTP)'
        clean_names.append(name)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(clean_names, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlim(0, 105)
    ax.set_xlabel('Score %')
    ax.set_title('VWO Physics Exam: Model Ranking', fontsize=11, fontweight='bold', loc='left')

    # Remove x-axis ticks (bars speak for themselves)
    ax.set_xticks([])
    ax.spines['bottom'].set_visible(False)

    # Subtle reference lines at key thresholds
    for thresh in [50, 80]:
        ax.axvline(thresh, color='#cccccc', linewidth=0.5, linestyle='-', zorder=0)

    # Legend
    from matplotlib.patches import Patch
    legend_elements = [
        Patch(facecolor=VLLM_COLOR, label='vLLM int4-MTP'),
        Patch(facecolor=LOCAL_COLOR, label='LMStudio Q4_K_M'),
        Patch(facecolor=CLOUD_COLOR, label='Cloud (OpenRouter)'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=7, framealpha=0.9)

    fig.tight_layout()
    return fig


def plot_cost_effectiveness() -> plt.Figure:
    """Scatter: cost vs accuracy for cloud models."""
    # Hardcoded pricing data (from OpenRouter)
    data = [
        ('gpt-5-mini', 2.00, 84.2),
        ('gpt-5.1', 10.00, 81.6),
        ('gpt-4o', 10.00, 57.9),
        ('gpt-4o-mini', 0.60, 38.2),
        ('mistral-large', 1.50, 59.2),
    ]

    fig, ax = plt.subplots(figsize=(6, 4))

    for name, price, score in data:
        ax.scatter(price, score, s=60, color=CLOUD_COLOR, edgecolor='white', linewidth=0.5, zorder=3)
        # Position labels to avoid collision
        offset_x = 0.1
        offset_y = 1.5
        if name == 'gpt-5.1':
            offset_x = 0.2
            offset_y = -3
        elif name == 'gpt-4o':
            offset_y = -3
        elif name == 'gpt-4o-mini':
            offset_x = 0.05
        ax.text(price + offset_x, score + offset_y, name, fontsize=8, color='#333333')

    ax.set_xscale('log')
    ax.set_xlabel('Output price ($/M tokens)')
    ax.set_ylabel('Score %')
    ax.set_title('Cloud Model Cost-Effectiveness', fontsize=11, fontweight='bold', loc='left')

    # Minimal grid
    ax.set_xlim(0.4, 15)
    ax.set_ylim(30, 90)
    ax.set_xticks([0.5, 1, 2, 5, 10])
    ax.set_xticklabels(['$0.50', '$1', '$2', '$5', '$10'])

    # Pareto frontier annotation
    ax.annotate('← Better value', xy=(1.5, 87), fontsize=8, color='#666666')

    ax.spines['left'].set_visible(True)
    fig.tight_layout()
    return fig


def plot_speed_accuracy_cloud(db_path: str) -> plt.Figure:
    """Scatter: inference time vs accuracy for OpenRouter models."""
    conn = sqlite3.connect(db_path)
    # Get scores (all answers including errors)
    score_rows = conn.execute("""
        SELECT a.model, ROUND(100.0 * SUM(j.score) / SUM(j.max_score), 1) as pct
        FROM answers a
        JOIN judgements j ON j.answer_id = a.id
        WHERE j.score IS NOT NULL
          AND j.judge_model = 'google/gemma-4-31b'
          AND a.inference_stack = 'openrouter'
        GROUP BY a.model
    """).fetchall()
    scores = {r[0]: r[1] for r in score_rows}

    # Get timing (only successful answers)
    timing_rows = conn.execute("""
        SELECT a.model, AVG(a.duration_ms)/1000.0 as avg_sec
        FROM answers a
        WHERE a.inference_stack = 'openrouter' AND a.error IS NULL
        GROUP BY a.model
    """).fetchall()
    timing = {r[0]: r[1] for r in timing_rows}

    rows = [(m, timing.get(m, 0), scores.get(m, 0)) for m in scores.keys()]
    conn.close()

    fig, ax = plt.subplots(figsize=(6, 4))

    for model, sec, score in rows:
        ax.scatter(sec, score, s=60, color=CLOUD_COLOR, edgecolor='white', linewidth=0.5, zorder=3)
        name = model.replace('openai/', '').replace('mistralai/', '')
        # Position labels
        offset_x = 0.5
        offset_y = 1.5
        if 'gpt-5-mini' in model:
            offset_y = -3
        elif 'gpt-4o-mini' in model:
            offset_y = -3
        ax.text(sec + offset_x, score + offset_y, name, fontsize=8, color='#333333')

    ax.set_xlabel('Avg. seconds per question')
    ax.set_ylabel('Score %')
    ax.set_title('Cloud Models: Speed vs Score', fontsize=11, fontweight='bold', loc='left')

    ax.set_xlim(0, 30)
    ax.set_ylim(30, 90)
    ax.spines['left'].set_visible(True)

    fig.tight_layout()
    return fig


def plot_speed_accuracy_local(db_path: str) -> plt.Figure:
    """Scatter: inference time vs accuracy for local models (LMStudio + vLLM)."""
    conn = sqlite3.connect(db_path)
    # Get scores for LMStudio
    score_rows = conn.execute("""
        SELECT a.model, a.inference_stack,
               ROUND(100.0 * SUM(j.score) / SUM(j.max_score), 1) as pct
        FROM answers a
        JOIN judgements j ON j.answer_id = a.id
        WHERE j.score IS NOT NULL
          AND ((a.inference_stack = 'lmstudio' AND j.judge_model = 'google/gemma-4-31b')
               OR (a.inference_stack = 'vllm-int4' AND j.judge_model = 'gemma-4-31b'))
        GROUP BY a.model, a.inference_stack
    """).fetchall()
    scores = {(r[0], r[1]): r[2] for r in score_rows}

    # Get timing (only successful answers)
    timing_rows = conn.execute("""
        SELECT a.model, a.inference_stack, AVG(a.duration_ms)/1000.0 as avg_sec
        FROM answers a
        WHERE a.inference_stack IN ('lmstudio', 'vllm-int4') AND a.error IS NULL
        GROUP BY a.model, a.inference_stack
    """).fetchall()
    timing = {(r[0], r[1]): r[2] for r in timing_rows}

    rows = [(m, s, timing.get((m, s), 0), scores.get((m, s), 0))
            for (m, s) in scores.keys()]
    conn.close()

    fig, ax = plt.subplots(figsize=(7, 4))

    for model, stack, sec, score in rows:
        color = VLLM_COLOR if stack == 'vllm-int4' else LOCAL_COLOR
        ax.scatter(sec, score, s=60, color=color, edgecolor='white', linewidth=0.5, zorder=3)
        name = model.replace('google/', '').replace('qwen/', '').replace('nvidia/', '')
        name = name.replace('-it-claude-opus-distill', '-distill')
        if stack == 'vllm-int4':
            name += ' (vLLM)'
        # Position labels to minimize collision
        offset_x = 2
        offset_y = 1
        if 'qwen3.6-27b' in model:
            offset_x = -55
            offset_y = 1
        elif 'gemma-4-31b' in name and stack == 'lmstudio':
            offset_y = -2.5
        elif 'gemma-4-31b' in name and stack == 'vllm-int4':
            offset_x = 3
            offset_y = -2.5
        elif 'nemotron' in model:
            offset_x = 3
        ax.text(sec + offset_x, score + offset_y, name, fontsize=7, color='#333333')

    ax.set_xlabel('Avg. seconds per question')
    ax.set_ylabel('Score %')
    ax.set_title('Local Models: Speed vs Score',
                 fontsize=11, fontweight='bold', loc='left')

    ax.set_xlim(0, 220)
    ax.set_ylim(10, 100)
    ax.spines['left'].set_visible(True)

    # Note about timing
    ax.text(110, 15, 'Green = vLLM+MTP optimized\nGray = LMStudio Q4_K_M',
            fontsize=7, color='#666666', style='italic')

    fig.tight_layout()
    return fig


def plot_speed_accuracy_all(db_path: str) -> plt.Figure:
    """Scatter: inference time vs accuracy for ALL models (cloud + local + vLLM)."""
    conn = sqlite3.connect(db_path)

    # Get scores with appropriate judge per stack, grouped by reasoning mode
    # Only include groups with at least 5 answers (filters out outliers like 2 empty reasoning questions)
    score_rows = conn.execute("""
        SELECT a.model, a.inference_stack, NOT a.reasoning_enabled as no_reasoning,
               ROUND(100.0 * SUM(j.score) / SUM(j.max_score), 1) as pct,
               COUNT(*) as cnt
        FROM answers a
        JOIN judgements j ON j.answer_id = a.id
        WHERE j.score IS NOT NULL
          AND ((a.inference_stack != 'vllm-int4' AND j.judge_model = 'google/gemma-4-31b')
               OR (a.inference_stack = 'vllm-int4' AND j.judge_model = 'gemma-4-31b'))
        GROUP BY a.model, a.inference_stack, a.reasoning_enabled
        HAVING COUNT(*) >= 5
    """).fetchall()
    scores = {(r[0], r[1], r[2]): r[3] for r in score_rows}

    # Get timing (only successful answers), grouped by reasoning mode
    timing_rows = conn.execute("""
        SELECT a.model, a.inference_stack, NOT a.reasoning_enabled as no_reasoning,
               AVG(a.duration_ms)/1000.0 as avg_sec,
               COUNT(*) as cnt
        FROM answers a
        WHERE a.error IS NULL
        GROUP BY a.model, a.inference_stack, a.reasoning_enabled
        HAVING COUNT(*) >= 5
    """).fetchall()
    timing = {(r[0], r[1], r[2]): r[3] for r in timing_rows}

    rows = [(m, s, nr, timing.get((m, s, nr), 0), scores.get((m, s, nr), 0))
            for (m, s, nr) in scores.keys() if timing.get((m, s, nr), 0) > 0]
    conn.close()

    fig, ax = plt.subplots(figsize=(10, 5))

    for model, stack, no_reasoning, sec, score in rows:
        # Color by stack type
        if stack == 'openrouter':
            color = CLOUD_COLOR
        elif stack == 'vllm-int4':
            color = VLLM_COLOR
        else:
            color = LOCAL_COLOR

        # Marker: filled circle for reasoning, hollow circle for cloud (unknown), hollow triangle for explicit no-reasoning
        if stack == 'openrouter':
            # Cloud: hollow circle (reasoning unknown)
            ax.scatter(sec, score, s=60, marker='o', facecolors='none',
                       edgecolors=color, linewidth=1.5, zorder=3)
        elif no_reasoning:
            # Explicit no-reasoning: hollow triangle
            ax.scatter(sec, score, s=60, marker='^', facecolors='none',
                       edgecolors=color, linewidth=1.5, zorder=3)
        else:
            # With reasoning: filled circle
            ax.scatter(sec, score, s=60, color=color, edgecolor='white',
                       linewidth=0.5, zorder=3)

        # Clean model name for label
        name = model.replace('google/', '').replace('qwen/', '')
        name = name.replace('openai/', '').replace('mistralai/', '').replace('nvidia/', '')
        name = name.replace('-it-claude-opus-distill', '-distill')
        if stack == 'vllm-int4':
            name += ' (vLLM)'
        if no_reasoning and stack != 'openrouter':
            name += ' no-R'

        # Default: label to the right and slightly above
        offset_x = 2
        offset_y = 1

        # Only fix collisions
        if 'gpt-4o' in model and 'mini' not in model:
            offset_y = 3  # above gpt-4o-mini
        elif 'mistral-large' in model:
            offset_y = -3  # below to avoid gemma-3-27b-it

        ax.text(sec + offset_x, score + offset_y, name, fontsize=7, color='#333333')

    ax.set_xlabel('Avg. seconds per question')
    ax.set_ylabel('Score %')
    ax.set_title('All Models: Speed vs Score', fontsize=11, fontweight='bold', loc='center')

    # Linear axis limits
    ax.set_xlim(0, 220)
    ax.set_ylim(15, 100)
    ax.spines['left'].set_visible(True)

    # Legend with marker shapes
    from matplotlib.patches import Patch
    from matplotlib.lines import Line2D
    legend_elements = [
        Patch(facecolor=CLOUD_COLOR, label='Cloud (OpenRouter)'),
        Patch(facecolor=LOCAL_COLOR, label='LMStudio Q4_K_M'),
        Patch(facecolor=VLLM_COLOR, label='vLLM int4-MTP'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='gray',
               markersize=8, label='With reasoning'),
        Line2D([0], [0], marker='o', color='w', markerfacecolor='none',
               markeredgecolor='gray', markersize=8, label='Reasoning unknown'),
        Line2D([0], [0], marker='^', color='w', markerfacecolor='none',
               markeredgecolor='gray', markersize=8, label='No reasoning'),
    ]
    ax.legend(handles=legend_elements, loc='lower right', fontsize=7, framealpha=0.9)

    fig.tight_layout()
    return fig


def plot_stack_speed_comparison(db_path: str) -> plt.Figure:
    """Bar chart comparing inference speed: LMStudio vs vLLM for gemma-4-31b."""
    conn = sqlite3.connect(db_path)

    # Get per-question timing for both stacks
    rows = conn.execute("""
        SELECT
            q.question_number,
            lm.duration_ms/1000.0 as lm_sec,
            v.duration_ms/1000.0 as vllm_sec
        FROM questions q
        JOIN answers lm ON lm.question_id = q.id
            AND lm.inference_stack = 'lmstudio'
            AND lm.model = 'google/gemma-4-31b'
        JOIN answers v ON v.question_id = q.id
            AND v.inference_stack = 'vllm-int4'
        ORDER BY q.question_number
    """).fetchall()
    conn.close()

    if not rows:
        # Return empty figure if no data
        fig, ax = plt.subplots(figsize=(8, 5))
        ax.text(0.5, 0.5, 'No comparison data available', ha='center', va='center')
        return fig

    questions = [f"Q{r[0]}" for r in rows]
    lm_times = [r[1] for r in rows]
    vllm_times = [r[2] for r in rows]

    x = np.arange(len(questions))
    width = 0.35

    fig, ax = plt.subplots(figsize=(12, 5))

    bars1 = ax.bar(x - width/2, lm_times, width, label='LMStudio Q4_K_M', color='#888888')
    bars2 = ax.bar(x + width/2, vllm_times, width, label='vLLM int4-MTP', color='#2563eb')

    ax.set_ylabel('Seconds per question')
    ax.set_title('Inference Speed: LMStudio vs vLLM (Gemma-4-31B)',
                 fontsize=11, fontweight='bold', loc='left')
    ax.set_xticks(x)
    ax.set_xticklabels(questions, fontsize=8)
    ax.legend(loc='upper right', fontsize=8)

    # Add speedup annotations on top
    for i, (lm, vllm) in enumerate(zip(lm_times, vllm_times)):
        speedup = lm / vllm if vllm > 0 else 0
        if speedup >= 2:
            ax.text(i, max(lm, vllm) + 5, f'{speedup:.1f}×',
                   ha='center', fontsize=7, color='#2563eb')

    # Summary stats
    avg_lm = sum(lm_times) / len(lm_times)
    avg_vllm = sum(vllm_times) / len(vllm_times)
    total_lm = sum(lm_times)
    total_vllm = sum(vllm_times)

    summary = f'Average: {avg_lm:.0f}s → {avg_vllm:.0f}s ({avg_lm/avg_vllm:.1f}× faster)\n'
    summary += f'Total: {total_lm/60:.0f}min → {total_vllm/60:.0f}min'
    ax.text(0.02, 0.98, summary, transform=ax.transAxes, fontsize=8,
            verticalalignment='top', color='#333333',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8))

    ax.spines['left'].set_visible(True)
    ax.set_ylim(0, max(lm_times) * 1.15)

    fig.tight_layout()
    return fig


def plot_question_heatmap(db_path: str) -> plt.Figure:
    """Heatmap: questions × top models showing difficulty patterns."""
    # (model, stack, reasoning_enabled, display_name)
    top_models = [
        ('gemma-4-31b', 'vllm-int4', 1, 'gemma-4-31b (vLLM)'),
        ('gemma-4-31b', 'vllm-int4', 0, 'gemma-4-31b (vLLM, no-R)'),
        ('qwen/qwen3.6-27b', 'lmstudio', 1, 'qwen3.6-27b'),
        ('google/gemma-4-31b', 'lmstudio', 1, 'gemma-4-31b'),
        ('qwen/qwen3.6-35b-a3b', 'lmstudio', 1, 'qwen3.6-35b-a3b'),
        ('openai/gpt-5-mini', 'openrouter', 0, 'gpt-5-mini'),
        ('openai/gpt-5.1', 'openrouter', 0, 'gpt-5.1'),
        ('openai/gpt-4o', 'openrouter', 0, 'gpt-4o'),
        ('openai/gpt-4o-mini', 'openrouter', 0, 'gpt-4o-mini'),
        ('google/gemma-4-26b-a4b', 'lmstudio', 1, 'gemma-4-26b-a4b'),
        ('google/gemma-3-27b-it', 'lmstudio', 0, 'gemma-3-27b-it'),
    ]

    conn = sqlite3.connect(db_path)

    # Get question metadata
    questions = conn.execute("""
        SELECT question_number, question_name, max_punten
        FROM questions ORDER BY question_number
    """).fetchall()

    # Build score matrix and compute totals for sorting
    scores = {}
    totals = {}
    for model, stack, reasoning, display in top_models:
        # Use appropriate judge for each stack
        if stack == 'vllm-int4':
            judge = 'gemma-4-31b'
        else:
            judge = 'google/gemma-4-31b'
        rows = conn.execute("""
            SELECT q.question_number, j.score, j.max_score
            FROM questions q
            JOIN answers a ON a.question_id = q.id
            JOIN judgements j ON j.answer_id = a.id
            WHERE a.model = ? AND a.inference_stack = ? AND a.reasoning_enabled = ? AND j.judge_model = ?
            ORDER BY q.question_number
        """, (model, stack, reasoning, judge)).fetchall()
        scores[display] = {r[0]: (r[1], r[2]) for r in rows}
        total_score = sum(r[1] for r in rows if r[1] is not None)
        total_max = sum(r[2] for r in rows if r[2] is not None)
        totals[display] = total_score / total_max if total_max > 0 else 0
    conn.close()

    # Sort models by total score descending
    display_names = sorted([m[3] for m in top_models], key=lambda d: totals[d], reverse=True)

    # Create matrix
    n_questions = len(questions)
    n_models = len(display_names)
    matrix = np.zeros((n_questions, n_models))

    for j, display in enumerate(display_names):
        for i, (qnum, _, _) in enumerate(questions):
            if qnum in scores[display]:
                score, max_score = scores[display][qnum]
                matrix[i, j] = score / max_score if max_score > 0 else 0

    fig, ax = plt.subplots(figsize=(8, 9))

    # Heatmap with white (100%) to dark gray (0%)
    cmap = plt.cm.RdYlGn  # Red (low) -> Yellow (mid) -> Green (high)
    im = ax.imshow(matrix, aspect='auto', cmap=cmap, vmin=0, vmax=1)

    # Labels
    clean_models = display_names
    ax.set_xticks(np.arange(n_models))
    ax.set_xticklabels(clean_models, rotation=45, ha='right', fontsize=8)

    # Y-axis: Q01 botsproef, etc.
    q_labels = [f"Q{q[0]} {q[1]}" for q in questions]
    ax.set_yticks(np.arange(n_questions))
    ax.set_yticklabels(q_labels, fontsize=7)

    # Add score text in each cell
    for i in range(n_questions):
        for j in range(n_models):
            val = matrix[i, j]
            color = 'white' if val < 0.5 else 'black'
            text = f"{int(val*100)}" if val > 0 else "0"
            ax.text(j, i, text, ha='center', va='center', fontsize=6, color=color)

    ax.set_title('Question Difficulty by Model (% correct)', fontsize=11, fontweight='bold', loc='left')

    # Topic separators (subtle lines between topics)
    # botsproef: Q01-Q07, elektriciteit: Q08-Q10, cepheiden: Q11-Q15, etc.
    topic_breaks = [7, 10, 15, 18]  # After these question indices
    for brk in topic_breaks:
        ax.axhline(brk - 0.5, color='#666666', linewidth=1)

    fig.tight_layout()
    return fig


if __name__ == "__main__":
    DB = "eval.db"
    OUT = Path("images/benchmark")
    OUT.mkdir(parents=True, exist_ok=True)

    print("Generating Tufte-style benchmark visualizations...")

    print("\n1. Model ranking bar chart")
    fig = plot_model_ranking(DB)
    save_both(fig, OUT / "01_ranking")

    print("\n2. Cloud cost-effectiveness scatter")
    fig = plot_cost_effectiveness()
    save_both(fig, OUT / "02_cost")

    print("\n3a. Speed-accuracy: cloud models")
    fig = plot_speed_accuracy_cloud(DB)
    save_both(fig, OUT / "03a_speed_cloud")

    print("\n3b. Speed-accuracy: local models")
    fig = plot_speed_accuracy_local(DB)
    save_both(fig, OUT / "03b_speed_local")

    print("\n3c. Speed-accuracy: all models combined")
    fig = plot_speed_accuracy_all(DB)
    save_both(fig, OUT / "03c_speed_all")

    print("\n4. Question difficulty heatmap")
    fig = plot_question_heatmap(DB)
    save_both(fig, OUT / "04_questions")

    print("\n5. Stack speed comparison (LMStudio vs vLLM)")
    fig = plot_stack_speed_comparison(DB)
    save_both(fig, OUT / "05_speed_comparison")

    print(f"\nDone! Files saved to {OUT}/")
