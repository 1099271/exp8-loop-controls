"""Reproduction shim: the author's vendored IFEval checkers were not published; this maps them to Google's official
instruction_following_eval (code/instruction_following_eval, google-research commit 0eebfd40, unmodified)."""
import sys
from instruction_following_eval import instructions_registry  # noqa: F401  (sets the attribute evaluate.py imports)
import instruction_following_eval as _m
sys.modules[__name__] = _m
