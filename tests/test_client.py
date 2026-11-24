"""Tests for the budget ledger: what a call is allowed to cost, and what has been spent.

The ledger is the only thing between "the budget is documented" and "the budget is
enforced", so its reserve arithmetic is pinned rather than trusted.
"""
from __future__ import annotations

import unittest

from rote.client import BudgetExceeded, Call, Ledger


def call(cost: float) -> Call:
    return Call(unit="u", purpose="p", effort="max", input_tokens=100, cached_tokens=0,
                output_tokens=10, reasoning_tokens=0, cost=cost, seconds=1.0, ok=True)


def ledger_with(budget: float, *costs: float) -> Ledger:
    led = Ledger(budget=budget)
    for cost in costs:
        led.record(call(cost))
    return led


class TestGuardReserve(unittest.TestCase):
    def test_fresh_ledger_admits_with_the_floor_reserve(self):
        """No calls seen yet: the reserve falls back to the $0.05 floor and $10 is plenty."""
        ledger_with(10.0).guard()

    def test_reserve_is_twice_the_largest_call_seen(self):
        """A $0.04 call makes the reserve $0.08, so $0.06 left refuses — the old flat
        $0.05 reserve would have admitted this call and let it overrun."""
        with self.assertRaises(BudgetExceeded):
            ledger_with(0.10, 0.04).guard()

    def test_a_small_largest_call_keeps_the_floor(self):
        """When the largest call seen so far is tiny, twice it is below the floor, so the
        reserve stays at $0.05 rather than shrinking toward nothing."""
        ledger_with(0.10, 0.01).guard()

    def test_an_explicit_estimate_still_wins(self):
        """A caller that states its own estimate is honoured as before."""
        ledger_with(0.10, 0.04).guard(estimate=0.01)

    def test_the_refusal_says_what_is_left(self):
        """The message must keep its wording: what remains, and what the cap is."""
        try:
            ledger_with(0.10, 0.04).guard()
        except BudgetExceeded as e:
            message = str(e)
        else:
            self.fail("guard should have refused")
        self.assertIn("$0.0600 left of $0.10", message)
        self.assertIn("rote refuses to spend past its budget", message)


class TestRunningTotal(unittest.TestCase):
    def test_spent_accumulates_as_calls_are_recorded(self):
        ledger = Ledger(budget=10.0)
        self.assertEqual(ledger.spent, 0.0)
        ledger.record(call(0.05))
        ledger.record(call(0.04))
        self.assertAlmostEqual(ledger.spent, 0.09)
        self.assertAlmostEqual(ledger.left, 9.91)

    def test_summary_agrees_with_the_running_total(self):
        """summary() must report the same number spent as the property, after records."""
        ledger = ledger_with(10.0, 0.05, 0.04)
        summary = ledger.summary()
        self.assertEqual(summary["calls"], 2)
        self.assertAlmostEqual(summary["spent_usd"], ledger.spent, places=5)

    def test_guard_and_summary_do_not_move_the_total(self):
        """guard() (pass or refusal) and summary() are reads, never writes."""
        ledger = ledger_with(10.0, 0.05)
        before = ledger.spent
        ledger.guard()
        ledger.summary()
        self.assertEqual(ledger.spent, before)


if __name__ == "__main__":
    unittest.main()
