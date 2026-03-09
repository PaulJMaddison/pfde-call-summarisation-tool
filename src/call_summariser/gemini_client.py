from __future__ import annotations

import os
import random
import re
import time
from dataclasses import dataclass

from google import genai  # type: ignore[import-not-found]


@dataclass(frozen=True)
class GeminiLLM:
    model: str = "gemini-3-flash-preview"
    max_attempts: int = 4
    timeout_s: float = 30.0  # soft timeout per request

    def __post_init__(self) -> None:
        if not os.getenv("GEMINI_API_KEY"):
            raise RuntimeError("GEMINI_API_KEY is not set (use env var or .env).")

    def _debug(self, msg: str) -> None:
        if os.getenv("GEMINI_DEBUG") == "1":
            print(f"[GeminiLLM] {msg}", flush=True)

    def _is_retryable(self, err: BaseException) -> bool:
        s = str(err)
        # Common transient classes/messages:
        # - 429 RESOURCE_EXHAUSTED (rate limit / quota)
        # - 503 Service Unavailable
        # - network-ish timeouts
        if "RESOURCE_EXHAUSTED" in s or "429" in s:
            return True
        if "503" in s or "ServiceUnavailable" in s or "SERVICE_UNAVAILABLE" in s:
            return True
        if "Timeout" in s or "timed out" in s or "timeout" in s:
            return True
        if "Connection" in s or "connection" in s:
            return True
        return False

    def _extract_retry_after_seconds(self, err: BaseException) -> float | None:
        """
        Gemini sometimes returns a JSON-ish blob including:
          'retryDelay': '47s'
        or text like:
          'Please retry in 47.5163s'
        We try to parse that and sleep accordingly.
        """
        s = str(err)

        # 1) Parse "Please retry in 47.516s"
        m = re.search(r"retry in ([0-9]+(?:\.[0-9]+)?)s", s, re.IGNORECASE)
        if m:
            return float(m.group(1))

        # 2) Parse JSON-ish 'retryDelay': '47s'
        m = re.search(r"retryDelay'\s*:\s*'(\d+)s'", s)
        if m:
            return float(m.group(1))

        # 3) Try to parse a JSON dict if present (best-effort)
        # Sometimes string contains "{'error': {...}}" which isn't strict JSON.
        # We'll just attempt very conservatively:
        return None

    def _call_gemini_once(self, prompt: str) -> str:
        # IMPORTANT: do NOT pass unsupported kwargs like request_options here.
        client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
        resp = client.models.generate_content(model=self.model, contents=prompt)

        text = getattr(resp, "text", None)
        if not text:
            raise RuntimeError("Gemini returned no text.")
        return text

    def generate(self, prompt: str) -> str:
        """
        Retries with backoff on transient errors.
        Uses a SOFT timeout: if Gemini hangs, we stop waiting and retry.
        """
        import concurrent.futures

        last_err: BaseException | None = None

        for attempt in range(1, self.max_attempts + 1):
            start = time.time()
            self._debug(f"attempt {attempt}/{self.max_attempts}")

            try:
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as ex:
                    fut = ex.submit(self._call_gemini_once, prompt)
                    text = fut.result(timeout=self.timeout_s)

                elapsed = time.time() - start
                self._debug(f"success (elapsed {elapsed:.2f}s)")
                return text

            except concurrent.futures.TimeoutError:
                last_err = TimeoutError(f"Gemini call timed out after {self.timeout_s}s")
                self._debug(str(last_err))

            except Exception as e:  # noqa: BLE001
                last_err = e
                self._debug(f"error: {type(e).__name__}: {e}")

                if not self._is_retryable(e):
                    raise

            # If we're here, we are retrying
            if attempt < self.max_attempts:
                retry_after = self._extract_retry_after_seconds(last_err) if last_err else None

                # backoff: either respect retry_after, or exponential + jitter
                if retry_after is not None:
                    sleep_s = min(retry_after, 60.0)  # cap
                    # add small jitter so we don't thundering-herd
                    sleep_s += random.uniform(0.0, 0.5)
                else:
                    base = 1.5 ** (attempt - 1)  # 1, 1.5, 2.25, 3.375...
                    sleep_s = min(base + random.uniform(0.0, 0.5), 15.0)

                self._debug(f"sleeping {sleep_s:.2f}s before retry")
                time.sleep(sleep_s)

        assert last_err is not None
        raise last_err
