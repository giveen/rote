"""Automation for HelpDesk, written by rote from triage.mp4.

Procedure: Search for ticket T-1042, open it, set Status to Resolved, Priority to Low, and Assignee to Jeremy, add a resolution note, and save the ticket.
What success looks like: The Open tickets list shows T-1042 with Priority Low and Status Resolved, the right panel returns to Nothing open, and a T-1042 saved confirmation appears at the bottom right.

Data comes in through `rows`: one dict per repetition, keyed by `ticket_id`, `status`, `priority`, `assignee`, `resolution_note`, `ticket`, `note`.
No model is involved in running this file.
"""

from __future__ import annotations

DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y")


EVENTS: list = []


def _mark(page, label: str) -> None:
    """Record where an iteration ended, so "it looped three times" is observable rather than
    assumed. An app that exposes no state still tells you which page it is on."""
    try:
        EVENTS.append((label, page.url))
    except Exception:
        pass


def _first_present(candidates, timeout_ms: int = 4000):
    """The first candidate that actually shows up.

    Counting matches answers about this instant, which is wrong on any app that navigates:
    the control arrives a moment later. timeout_ms is the whole budget for the lookup,
    shared across candidates, so a failing step waits at most timeout_ms instead of one
    timeout per candidate; the happy path still returns on the first candidate immediately.
    """
    cands = list(candidates)
    per = max(600, timeout_ms // max(len(cands), 1)) if cands else timeout_ms
    for loc in cands:
        try:
            loc.first.wait_for(state="visible", timeout=per)
            return loc.first
        except Exception:
            continue
    raise LookupError(f"none of these appeared within {timeout_ms}ms: {candidates}")


def _field(page, label: str):
    """A form control by the label a person reads, falling back to placeholder or name."""
    return _first_present([
        page.get_by_label(label, exact=False),
        page.get_by_placeholder(label, exact=False),
        page.locator(f"[name='{label}']"),
    ])


def _button(page, name: str):
    """Something clickable, by the name a person reads on it.

    Plenty of apps use a link or a styled div where a person sees a button, so the role is a
    hint rather than a requirement.
    """
    return _first_present([
        page.get_by_role("button", name=name, exact=False),
        page.get_by_role("link", name=name, exact=False),
        page.get_by_role("menuitem", name=name, exact=False),
        page.get_by_role("tab", name=name, exact=False),
        page.get_by_text(name, exact=False),
    ])


def _truthy(value) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "y", "on", "checked")


def _to_iso_date(value: str):
    """Only formats with no ambiguity. 03/01/2026 is refused on purpose: it is either
    March 1st or January 3rd, and silently picking one corrupts the user's data."""
    from datetime import datetime
    text = str(value).strip()
    for fmt in DATE_FORMATS:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return None


def _fill(page, label: str, value: str) -> None:
    """Fill a control, giving a date input the form it actually accepts."""
    control = _field(page, label)
    kind = (control.get_attribute("type") or "text").lower()
    text = "" if value is None else str(value)
    if kind == "date":
        iso = _to_iso_date(text)
        if not iso:
            raise ValueError(f"{label!r} is a date field; {text!r} is not an unambiguous "
                             f"date. Give it YYYY-MM-DD.")
        control.fill(iso)
        if not control.input_value():
            raise ValueError(f"the date field {label!r} rejected {iso!r}")
        return
    control.fill(text)


def select_options(page, label: str):
    """The choices a dropdown actually offers."""
    try:
        control = _field(page, label)
        return [t.strip() for t in control.locator("option").all_inner_texts() if t.strip()]
    except Exception:
        return []


def _select(page, label: str, value: str) -> None:
    """Choose an option, and say which ones exist when the value is not among them."""
    control = _field(page, label)
    options = [t.strip() for t in control.locator("option").all_inner_texts()]
    if value not in options:
        raise LookupError(f"{label!r} has no option {value!r}. Available: {options}")
    control.select_option(label=value)


def _tick(page, label: str, want: bool, action: str = "") -> None:
    (control := _field(page, label))
    (control.check if want else control.uncheck)()


def _key(row: dict, key: str) -> str:
    """Accept the row key in any casing, and the visible label as a fallback.

    `unit_cost` has to find `Unit Cost`, which is what a form label actually reads, so the
    spaced form is tried in Title Case as well as lowercase.
    """
    if key in row:
        return key
    spaced = key.replace("_", " ")
    variants = (key.lower(), key.upper(), key.title(),
                spaced, spaced.lower(), spaced.upper(), spaced.title(),
                key.replace(" ", "_"))
    for candidate in variants:
        if candidate in row:
            return candidate
    raise KeyError(f"row has no value for {key!r}: {sorted(row)}")


def _one(page: Page, row: dict[str, str]) -> None:
    """One repetition of the task."""
    _fill(page, "Search tickets", row[_key(row, "ticket")])
    _button(page, "Open").click()
    _select(page, "Status", row[_key(row, "status")])
    _select(page, "Priority", row[_key(row, "priority")])
    _select(page, "Assignee", row[_key(row, "assignee")])
    _fill(page, "Resolution note", row[_key(row, "note")])
    _button(page, "Save ticket").click()
    _mark(page, "iteration")


def run(page: Page, rows: list[dict[str, str]]) -> None:
    """Set the task up once, perform it for every row, then finish once."""
    row = rows[0] if rows else {}
    pass
    for row in rows:
        _one(page, row)
    pass
