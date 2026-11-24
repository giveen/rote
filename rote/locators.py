"""How the recorder names a control.

The implementation lives in `rote/scriptenv.py`, the same code that is embedded into every
generated automation, so the recorder and the replay cannot drift apart.
"""
from __future__ import annotations

from .scriptenv import button, field, perform, select_options  # noqa: F401
