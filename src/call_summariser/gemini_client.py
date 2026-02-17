from __future__ import annotations

import os
from dataclasses import dataclass

from google import genai


@dataclass(frozen=True)
class GeminiLLM:
    model: str = "gemini-3-flash-preview"

    def __post_init__(self) -> None:
        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError("GEMINI_API_KEY is not set (use env var or .env).")

    def generate(self, prompt: str) -> str:
        client = genai.Client()
        resp = client.models.generate_content(model=self.model, contents=prompt)
        text = getattr(resp, "text", None)
        if not text:
            raise RuntimeError("Gemini returned no text.")
        return text
