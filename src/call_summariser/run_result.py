from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RunResult:
    summary: str
    attempts_used: int
