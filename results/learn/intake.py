"""Automation for Stockroom, written by rote from intake.mp4.

Procedure: Log goods received against a purchase order on the Parts intake page by entering one or more part lines and submitting the intake.
What success looks like: Each entered line appears as a row in the table below the form (SKU, Description, QTY, Unit cost, Supplier, Location) and the form resets to its placeholders; after submitting, a confirmation toast appears at the bottom right stating 'Intake submitted — 1 line recorded.'

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
    _field(page, "SKU").fill(row[_key(row, "sku")])
    _field(page, "Description").fill(row[_key(row, "description")])
    _field(page, "Quantity").fill(row[_key(row, "quantity")])
    _field(page, "Unit cost").fill(row[_key(row, "unit_cost")])
    _select(page, "Supplier", row[_key(row, "supplier")])
    _select(page, "Location", row[_key(row, "location")])
    _button(page, "Add line").click()


def run(page: Page, rows: list[dict[str, str]]) -> None:
    """Perform the task once for every row."""
    for row in rows:
        _one(page, row)
    _button(page, "Submit intake").click()
