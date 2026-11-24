"""How an action names a control.

Everything in rote goes through these three helpers: the recorder uses them to act like a
person, the generated automation uses them to act like a person, and the replay proves it.
Keeping one strategy is what lets a plan that only names *visible labels* be executable.

Deliberately not CSS selectors and not coordinates: those break the moment a layout
changes, and they are unreadable in a generated script.
"""
from __future__ import annotations

from playwright.sync_api import Page


def field(page: Page, label: str):
    """A form control by its visible label, as a human reads it."""
    by_label = page.get_by_label(label, exact=False)
    if by_label.count() > 0:
        return by_label.first
    # some apps put the label above without wiring it: fall back to placeholder text
    by_placeholder = page.get_by_placeholder(label, exact=False)
    if by_placeholder.count() > 0:
        return by_placeholder.first
    return page.locator(f"[name='{label}']").first


def button(page: Page, name: str):
    """A button by its accessible name."""
    by_role = page.get_by_role("button", name=name, exact=False)
    if by_role.count() > 0:
        return by_role.first
    return page.get_by_text(name, exact=False).first


def select_options(page: Page, label: str) -> list[str]:
    """The choices a dropdown actually offers, which the plan may not have seen."""
    loc = field(page, label)
    try:
        return [t.strip() for t in loc.locator("option").all_inner_texts() if t.strip()]
    except Exception:
        return []


def perform(page: Page, action: str, target: str, value: str | None) -> None:
    """One action from a plan, exactly as a person would do it."""
    if action == "type":
        field(page, target).fill(value or "")
    elif action == "select":
        loc = field(page, target)
        try:
            loc.select_option(label=value or "")
        except Exception:
            loc.select_option(value or "")
    elif action in ("click", "submit"):
        button(page, target).click()
    elif action in ("check", "uncheck"):
        loc = field(page, target)
        (loc.check if action == "check" else loc.uncheck)()
    elif action == "read":
        pass
    else:
        raise ValueError(f"unknown action {action!r}")
