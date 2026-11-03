"""shim: weightenv.lmo.tasks.mathqa is code/mathqa.py (the published module), the same module object."""
import sys

import mathqa as _m  # noqa: E402  (code/ is on sys.path: evaluate.py puts it there)

sys.modules[__name__] = _m
