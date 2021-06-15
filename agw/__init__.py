import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from application import AGW  # noqa


_app: AGW = None


def get_app():
    global _app
    if _app is None:
        _app = AGW().app
    return _app
