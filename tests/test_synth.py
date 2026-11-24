"""Tests for the compiler: plan in, runnable automation out.

The compiler is where a wrong plan becomes a wrong script, so its ordering rules are pinned
here: setup before the loop, the repeating block inside it, finishing after it.
"""
from __future__ import annotations

import unittest

from rote.plan import Plan, Step
from rote.synth import compile_plan


def plan_with(repeat: tuple[int, int] | None, steps: list[Step]) -> Plan:
    return Plan(app="Stockroom", goal="log parts", steps=steps, rows=[{"sku": "A"}],
                expected_effect='a toast says "Intake submitted"', repeat=repeat)


STEPS = [
    Step("type", "Username", "standard_user"),
    Step("click", "Login"),
    Step("type", "SKU", "{sku}"),
    Step("click", "Add line"),
    Step("submit", "Submit intake"),
]


class TestOrdering(unittest.TestCase):
    def test_setup_runs_before_the_loop_and_finish_after(self):
        code = compile_plan(plan_with((3, 4), STEPS))
        run_body = code.split("def run(")[1]
        self.assertLess(run_body.index('_fill(page, "Username"'), run_body.index("for row in rows"))
        self.assertGreater(run_body.index("Submit intake"), run_body.index("for row in rows"))

    def test_the_repeating_block_lands_inside_the_loop(self):
        code = compile_plan(plan_with((3, 4), STEPS))
        one = code.split("def _one(")[1].split("def run(")[0]
        self.assertIn('"SKU"', one)
        self.assertIn('"Add line"', one)
        self.assertNotIn('"Username"', one, "setup leaked into the per-row block")

    def test_out_of_range_indices_are_clamped(self):
        code = compile_plan(plan_with((1, 99), STEPS))
        compile(code, "<generated>", "exec")   # must still be valid Python
        code = compile_plan(plan_with((9, 9), STEPS))
        compile(code, "<generated>", "exec")

    def test_no_repeat_range_runs_the_whole_thing_once(self):
        code = compile_plan(plan_with(None, STEPS))
        self.assertIn("for row in rows", code)
        self.assertNotIn('_fill(page, "Username")\n    row', code)


class TestGeneratedCode(unittest.TestCase):
    def test_always_valid_python(self):
        for repeat in (None, (1, 1), (2, 4), (5, 5)):
            compile(compile_plan(plan_with(repeat, STEPS)), "<generated>", "exec")

    def test_navigate_without_a_url_is_not_a_broken_call(self):
        steps = [Step("navigate", "the app"), Step("type", "SKU", "{sku}")]
        code = compile_plan(plan_with((2, 2), steps))
        self.assertNotIn('page.goto("")', code)
        self.assertIn("no URL", code)

    def test_helpers_are_embedded_so_the_script_stands_alone(self):
        code = compile_plan(plan_with((3, 4), STEPS))
        for helper in ("def _field", "def _button", "def _fill", "def _select", "def _key"):
            self.assertIn(helper, code, f"{helper} missing from the generated module")
        self.assertNotIn("import rote", code, "a generated script must not need rote")

    def test_dates_and_checkboxes_use_the_safe_paths(self):
        steps = [Step("type", "Contract start", "{start}"),
                 Step("check", "Send welcome pack", "{welcome}")]
        code = compile_plan(plan_with((1, 2), steps))
        self.assertIn("_fill(page, \"Contract start\"", code)
        self.assertIn("_tick(page, \"Send welcome pack\"", code)

    def test_expected_effect_and_goal_reach_the_docstring(self):
        code = compile_plan(plan_with((3, 4), STEPS), recording="intake.mp4")
        self.assertIn("intake.mp4", code)
        self.assertIn("log parts", code)
        self.assertIn("Intake submitted", code)


if __name__ == "__main__":
    unittest.main()
