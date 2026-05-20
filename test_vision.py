#!/usr/bin/env python3
"""LMStudio vision API for VWO exam questions - multi-turn for multiple images."""

import base64
from pathlib import Path
from openai import OpenAI

client = OpenAI(
    base_url="http://192.168.2.97:1234/v1",
    api_key="not-needed"
)

def load_image_as_base64(path: Path) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

def solve_single_image(image_path: Path, question: str = "Los dit op") -> str:
    """Solve question with single image."""
    image_data = load_image_as_base64(image_path)
    content = [
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_data}"}},
        {"type": "text", "text": question}
    ]
    response = client.chat.completions.create(
        model="qwen3.5-27b",
        messages=[{"role": "user", "content": content}],
        max_tokens=16384
    )
    return response.choices[0].message.content

def solve_with_uitwerkbijlage(opgave_path: Path, bijlage_path: Path, question: str = "Los dit op") -> str:
    """Solve question using multi-turn: opgave first, then uitwerkbijlage."""
    opgave_data = load_image_as_base64(opgave_path)
    bijlage_data = load_image_as_base64(bijlage_path)

    messages = [
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{opgave_data}"}},
            {"type": "text", "text": "Dit is de opgave."}
        ]},
        {"role": "assistant", "content": "Begrepen, ik zie de opgave. Ik heb de uitwerkbijlage nodig om de vraag te beantwoorden."},
        {"role": "user", "content": [
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{bijlage_data}"}},
            {"type": "text", "text": f"Hier is de uitwerkbijlage. {question}"}
        ]}
    ]

    response = client.chat.completions.create(
        model="qwen3.5-27b",
        messages=messages,
        max_tokens=16384
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    base = Path("images/2026-05/vw-1023-a-26-1-o")

    print("=== Vraag 01: Botsproef ===\n")
    print(solve_single_image(base / "01_botsproef.png"))

    print("\n" + "="*60 + "\n")

    print("=== Vraag 02: Botsproef Film Analyse ===\n")
    print(solve_with_uitwerkbijlage(
        base / "02_botsproef_opgave.png",
        base / "02_botsproef_uitwerkbijlage.png"
    ))
