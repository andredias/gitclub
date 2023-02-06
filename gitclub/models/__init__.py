from pathlib import Path
from secrets import randbelow
from typing import Any

from pydantic import BaseModel
from sqlalchemy import MetaData

metadata = MetaData()

# metadata.tables is only populated after all models are imported.
# see alembic/env.py for an example.
modules = Path(__file__).parent.glob('*.py')
__all__ = [p.stem for p in modules if p.is_file() and p.stem != '__init__']

MAX_ID = 2**31


def random_id() -> int:
    """
    Return a random integer to be used as ID.

    Auto-incremented IDs are not particularly good for users as primary keys.
    1. Sequential IDs are guessable.
       One might guess that admin is always user with ID 1, for example.
    2. Tests end up using fixed ID values such as 1 or 2 instead of real values.
       This leads to poor test designs that should be avoided.
    """
    return randbelow(MAX_ID)


def diff_models(from_: BaseModel, to_: BaseModel) -> dict[str, Any]:
    """
    Return a dict with differences of the second in relation to the first model.
    Useful for getting only the fields that have changed before an update,
    for example.
    """
    from_dict = from_.dict()
    to_dict = to_.dict(exclude_unset=True)
    return {k: v for k, v in to_dict.items() if from_dict.get(k) != v}
