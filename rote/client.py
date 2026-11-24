"""Muse Ember client: every call measured, every token accounted, $10 enforced in code.

The ledger it writes is not a debug log. The hackathon submission requires a prompt and
token trace with the amount spent, and a budget that is only *watched* is a budget that
gets exceeded.
"""
from __future__ import annotations

import json
import os
import threading
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import httpx

BASE = "https://api.meta.ai/v1"
MODEL = "muse-ember-1.0"

PRICE_IN = 0.10 / 1e6
PRICE_CACHED = 0.004 / 1e6
PRICE_OUT = 0.50 / 1e6
PRICE_IN_LONG, PRICE_CACHED_LONG, PRICE_OUT_LONG = 0.30 / 1e6, 0.012 / 1e6, 1.50 / 1e6
LONG_CONTEXT = 200_000


class BudgetExceeded(RuntimeError):
    pass


def api_key() -> str:
    if key := os.environ.get("MODEL_API_KEY"):
        return key
    cfg = Path.home() / ".config" / "muse" / "auth.json"
    return json.loads(cfg.read_text())["providers"]["meta"]["api_key"]


def cost_of(usage: dict | None) -> float:
    if not usage:
        return 0.0
    i = usage.get("input_tokens") or 0
    c = (usage.get("input_tokens_details") or {}).get("cached_tokens") or 0
    o = usage.get("output_tokens") or 0
    if i > LONG_CONTEXT:
        return (i - c) * PRICE_IN_LONG + c * PRICE_CACHED_LONG + o * PRICE_OUT_LONG
    return (i - c) * PRICE_IN + c * PRICE_CACHED + o * PRICE_OUT


@dataclass
class Call:
    unit: str            # what part of the pipeline spent this
    purpose: str
    effort: str
    input_tokens: int
    cached_tokens: int
    output_tokens: int
    reasoning_tokens: int
    cost: float
    seconds: float
    ok: bool
    note: str = ""


@dataclass
class Ledger:
    budget: float = 10.0
    path: Path | None = None
    calls: list[Call] = field(default_factory=list)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    @property
    def spent(self) -> float:
        return sum(c.cost for c in self.calls)

    @property
    def left(self) -> float:
        return self.budget - self.spent

    def record(self, call: Call) -> None:
        with self._lock:
            self.calls.append(call)
            if self.path:
                self.path.parent.mkdir(parents=True, exist_ok=True)
                with self.path.open("a") as f:
                    f.write(json.dumps(asdict(call)) + "\n")

    def guard(self, estimate: float = 0.05) -> None:
        if self.left < estimate:
            raise BudgetExceeded(
                f"stopping: ${self.left:.4f} left of ${self.budget:.2f}. "
                "rote refuses to spend past its budget.")

    def summary(self) -> dict[str, Any]:
        c = self.calls
        i = sum(x.input_tokens for x in c)
        cached = sum(x.cached_tokens for x in c)
        return {
            "calls": len(c),
            "spent_usd": round(sum(x.cost for x in c), 6),
            "input_tokens": i,
            "cached_tokens": cached,
            "output_tokens": sum(x.output_tokens for x in c),
            "reasoning_tokens": sum(x.reasoning_tokens for x in c),
            "cache_hit_pct": round(100 * cached / i, 1) if i else 0.0,
        }


def text_of(data: dict) -> str:
    return "".join(c.get("text", "")
                   for item in data.get("output", []) if item.get("type") == "message"
                   for c in item.get("content", []) if c.get("type") == "output_text")


def create(*, unit: str, purpose: str, input_: Any, ledger: Ledger,
           instructions: str | None = None, effort: str = "max",
           schema: dict | None = None, schema_name: str = "plan",
           cache_key: str | None = None, max_output_tokens: int | None = None,
           timeout: float = 900.0, retries: int = 2, note: str = "") -> str:
    ledger.guard()
    body: dict[str, Any] = {"model": MODEL, "input": input_, "reasoning": {"effort": effort}}
    if instructions:
        body["instructions"] = instructions
    if schema:
        body["text"] = {"format": {"type": "json_schema", "name": schema_name,
                                   "schema": schema, "strict": True}}
    if cache_key:
        body["prompt_cache_key"] = cache_key
    if max_output_tokens:
        body["max_output_tokens"] = max_output_tokens

    err = None
    for attempt in range(retries + 1):
        t0 = time.time()
        try:
            r = httpx.post(f"{BASE}/responses",
                           headers={"Authorization": f"Bearer {api_key()}",
                                    "Content-Type": "application/json"},
                           json=body, timeout=timeout)
            dt = time.time() - t0
            if r.status_code != 200:
                err = f"HTTP {r.status_code}: {r.text[:300]}"
                if r.status_code in (429, 500, 502, 503, 504):
                    time.sleep(1.5 * (attempt + 1))
                    continue
                break
            d = r.json()
            u = d.get("usage") or {}
            ledger.record(Call(
                unit=unit, purpose=purpose, effort=effort,
                input_tokens=u.get("input_tokens") or 0,
                cached_tokens=(u.get("input_tokens_details") or {}).get("cached_tokens") or 0,
                output_tokens=u.get("output_tokens") or 0,
                reasoning_tokens=(u.get("output_tokens_details") or {}).get("reasoning_tokens") or 0,
                cost=cost_of(u), seconds=round(dt, 2), ok=d.get("status") != "failed",
                note=note))
            return text_of(d)
        except Exception as e:
            err = f"{type(e).__name__}: {e}"
            time.sleep(1.5 * (attempt + 1))
    ledger.record(Call(unit, purpose, effort, 0, 0, 0, 0, 0.0, 0.0, False, err or ""))
    raise RuntimeError(f"{unit}/{purpose} failed: {err}")


def count_tokens(input_: Any, *, instructions: str | None = None) -> int:
    """Exact input-token count without generating anything (not billed as generation)."""
    body: dict[str, Any] = {"model": MODEL, "input": input_}
    if instructions:
        body["instructions"] = instructions
    r = httpx.post(f"{BASE}/responses/input_tokens",
                   headers={"Authorization": f"Bearer {api_key()}"},
                   json=body, timeout=300)
    r.raise_for_status()
    return r.json()["input_tokens"]


def upload(path: Path, *, purpose: str = "user_data", timeout: float = 900.0) -> str:
    """Put a file on the API once, then reference it by id."""
    with path.open("rb") as f:
        r = httpx.post(f"{BASE}/files",
                       headers={"Authorization": f"Bearer {api_key()}"},
                       data={"purpose": purpose},
                       files={"file": (path.name, f, "video/mp4")}, timeout=timeout)
    r.raise_for_status()
    d = r.json()
    return d.get("id") or d["file"]["id"]
