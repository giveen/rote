"""Automation for Stockroom, written by rote from intake.mp4.

Procedure: Log goods received against a purchase order by adding parts intake lines and submitting the intake.
What success looks like: Both entered lines appear in the intake table below the form with SKU, description, quantity, unit cost, supplier and location; the entry form is cleared to its placeholders and a confirmation toast appears at the bottom right saying Intake submitted.

Data comes in through `rows`: one dict per repetition, keyed by `sku`, `description`, `quantity`, `unit_cost`, `supplier`, `location`.
No model is involved in running this file.
"""
from __future__ import annotations

from playwright.sync_api import Page


def _field(page: Page, label: str):
    """A control by its visible label, falling back to placeholder or name."""
    for locator in (page.get_by_label(label, exact=False),
                    page.get_by_placeholder(label, exact=False),
                    page.locator(f"[name='{label}']")):
        if locator.count() > 0:
            return locator.first
    raise LookupError(f"no form control labelled {label!r} on {page.url}")


def _button(page: Page, name: str):
    """A button by its accessible name, falling back to visible text."""
    for locator in (page.get_by_role("button", name=name, exact=False),
                    page.get_by_text(name, exact=False)):
        if locator.count() > 0:
            return locator.first
    raise LookupError(f"no button named {name!r} on {page.url}")


def _truthy(value) -> bool:
    return str(value).strip().lower() in ("1", "true", "yes", "y", "on", "checked")


def _tick(page: Page, label: str, want: bool, action: str) -> None:
    control = _field(page, label)
    (control.check if want else control.uncheck)()


DATE_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%d %b %Y", "%d %B %Y", "%b %d, %Y", "%B %d, %Y")


def _to_iso_date(value: str) -> str | None:
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


def _fill(page: Page, label: str, value: str) -> None:
    """Fill a control, giving a date input the form it actually accepts."""
    control = _field(page, label)
    kind = (control.get_attribute("type") or "text").lower()
    text = "" if value is None else str(value)
    if kind == "date":
        iso = _to_iso_date(text)
        if not iso:
            raise ValueError(f"{label!r} is a date field; {text!r} is not an "
                             f"unambiguous date. Give it YYYY-MM-DD.")
        control.fill(iso)
        if not control.input_value():
            raise ValueError(f"the date field {label!r} rejected {iso!r}")
        return
    control.fill(text)


def _select(page: Page, label: str, value: str) -> None:
    """Choose an option, and say which ones exist when the value is not among them."""
    control = _field(page, label)
    options = [t.strip() for t in control.locator("option").all_inner_texts()]
    if value not in options:
        raise LookupError(f"{label!r} has no option {value!r}. "
                          f"Available: {options}")
    control.select_option(label=value)



def _key(row: dict, key: str) -> str:
    """Accept the row key in any casing, and the visible label as a fallback."""
    if key in row:
        return key
    for candidate in (key.lower(), key.upper(), key.title(), key.replace("_", " ")):
        if candidate in row:
            return candidate
    raise KeyError(f"row has no value for {key!r}: {sorted(row)}")


def _one(page: Page, row: dict[str, str]) -> None:
    """One repetition of the task."""
    _fill(page, "SKU", row[_key(row, "sku")])
    _fill(page, "Description", row[_key(row, "description")])
    _fill(page, "Quantity", row[_key(row, "quantity")])
    _fill(page, "Unit cost", row[_key(row, "unit_cost")])
    _select(page, "Supplier", row[_key(row, "supplier")])
    _select(page, "Location", row[_key(row, "location")])
    _button(page, "Add line").click()


def run(page: Page, rows: list[dict[str, str]]) -> None:
    """Perform the task once for every row."""
    for row in rows:
        _one(page, row)
    _button(page, "Submit intake").click()
