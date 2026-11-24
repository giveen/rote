"""The plan: what Ember says happened in a recording, and how we judge that answer.

A plan is deliberately small. It names intents and visible labels, never pixels or
coordinates, which is what lets a cheap model produce it and what lets the generated
automation stay readable years later.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

# The whole contract with the model. Sent as a strict json_schema, so a malformed plan
# is rejected by the API rather than discovered halfway through a replay.
PLAN_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "app": {"type": "string"},
        "goal": {"type": "string"},
        "fields": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "label": {"type": "string"},
                    "control": {"type": "string",
                                "enum": ["text", "number", "select", "checkbox", "file"]},
                    "example": {"type": "string"},
                },
                "required": ["label", "control", "example"],
                "additionalProperties": False,
            },
        },
        "steps": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "action": {"type": "string",
                               "enum": ["type", "select", "click", "submit",
                                        "navigate", "read", "check", "uncheck"]},
                    "target": {"type": "string"},
                    "value": {"type": ["string", "null"]},
                    "note": {"type": "string"},
                    "scope": {"type": "string", "enum": ["each_row", "once"]},
                },
                "required": ["action", "target", "value", "note", "scope"],
                "additionalProperties": False,
            },
        },
        # Strict schemas cannot describe a free-form object, so a row is a list of
        # explicit field/value cells. It also reads better in the report.
        "rows": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "cells": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "field": {"type": "string"},
                                "value": {"type": "string"},
                            },
                            "required": ["field", "value"],
                            "additionalProperties": False,
                        },
                    },
                },
                "required": ["cells"],
                "additionalProperties": False,
            },
        },
        # Which steps repeat for each row of data. One pair of numbers instead of a scope
        # label on every step: a model that has to get N judgements right will flip one of
        # them, and one flip reorders the whole script.
        "repeat": {
            "type": "object",
            "properties": {"first": {"type": "integer"}, "last": {"type": "integer"}},
            "required": ["first", "last"],
            "additionalProperties": False,
        },
        "expected_effect": {"type": "string"},
    },
    "required": ["app", "goal", "fields", "steps", "rows", "repeat", "expected_effect"],
    "additionalProperties": False,
}


@dataclass
class Step:
    action: str
    target: str
    value: str | None = None
    note: str = ""
    scope: str = "each_row"      # each_row repeats per data row; once happens at the end

    def matches(self, other: "Step") -> bool:
        """Same intent, allowing for whitespace and case drift in labels."""
        return (self.action == other.action
                and _norm(self.target) == _norm(other.target)
                and _norm(self.value or "") == _norm(other.value or ""))


@dataclass
class Plan:
    app: str
    goal: str
    steps: list[Step] = field(default_factory=list)
    rows: list[dict[str, str]] = field(default_factory=list)
    fields: list[dict[str, str]] = field(default_factory=list)
    expected_effect: str = ""
    repeat: tuple[int, int] | None = None   # 1-based, inclusive
    cost: float = 0.0
    seconds: float = 0.0

    @classmethod
    def from_dict(cls, d: dict) -> "Plan":
        return cls(
            app=d.get("app", ""),
            goal=d.get("goal", ""),
            steps=[Step(s["action"], s["target"], s.get("value"), s.get("note", ""),
                        s.get("scope", "each_row"))
                   for s in d.get("steps", [])],
            rows=[{c["field"]: c["value"] for c in row.get("cells", [])}
                  for row in d.get("rows", [])],
            fields=d.get("fields", []),
            expected_effect=d.get("expected_effect", ""),
            repeat=(int(d["repeat"]["first"]), int(d["repeat"]["last"]))
            if isinstance(d.get("repeat"), dict) else None,
        )

    @classmethod
    def from_json(cls, text: str) -> "Plan":
        return cls.from_dict(json.loads(text))

    def to_dict(self) -> dict:
        return {"app": self.app, "goal": self.goal,
                "fields": self.fields,
                "rows": [{"cells": [{"field": k, "value": v} for k, v in row.items()]}
                         for row in self.rows],
                "steps": [{"action": s.action, "target": s.target,
                           "value": s.value, "note": s.note, "scope": s.scope}
                          for s in self.steps],
                "repeat": ({"first": self.repeat[0], "last": self.repeat[1]}
                           if self.repeat else None),
                "expected_effect": self.expected_effect}

    @property
    def targets(self) -> set[str]:
        return {_norm(s.target) for s in self.steps}


def _norm(s: str) -> str:
    return " ".join(str(s).split()).strip().lower()


def coverage(plan: Plan, expected_steps: list[Step]) -> dict[str, Any]:
    """How much of a known-correct sequence the plan recovered.

    Used for scoring Ember against a hand-labelled recording; this is the only place a
    human-written answer is allowed to judge a model answer.
    """
    hits, missed = 0, []
    for want in expected_steps:
        if any(want.matches(got) for got in plan.steps):
            hits += 1
        else:
            missed.append(want)
    total = len(expected_steps) or 1
    return {"matched": hits, "total": len(expected_steps),
            "recall": round(hits / total, 3),
            "missed": [f"{s.action} {s.target} {s.value or ''}".strip() for s in missed]}
