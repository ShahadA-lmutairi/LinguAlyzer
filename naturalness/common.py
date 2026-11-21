"""Shared helpers for the Arabic translation-naturalness dataset."""
from pathlib import Path

import pandas as pd

DATA = Path(__file__).parent / "data" / "pairs.csv"

ISSUES = {
    "qam_bi": "«قام بـ / قم بـ» + masdar instead of a direct verb",
    "passive_tam_yatim": "«تم / يتم» + masdar for a simple passive or progressive",
    "biwasita": "«بواسطة» to mark the agent",
    "khas_bi": "«الخاص بك» instead of a possessive suffix",
    "redundant_pronoun": "Extra pronoun or copula copied from English (أنت لديك، هو غير)",
    "purpose_clause": "«لكي / من أجل» where «لـ» or a masdar is enough",
    "bishakl": "«بشكل» + adjective instead of an adverb or noun",
    "calque": "English idiom or structure carried over word for word",
}
STATUSES = {"seed", "reviewed"}
COLUMNS = ["pair_id", "source_en", "literal_ar", "natural_ar", "issue", "status"]


def load_pairs(path: Path = DATA) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8", dtype=str).fillna("")


def to_rows(pairs: pd.DataFrame) -> pd.DataFrame:
    """One row per Arabic sentence: label 1 = literal, 0 = natural.
    `group` keeps both sides of a pair together so they never end up
    in different train/test folds (that would leak the answer)."""
    literal = pd.DataFrame({"text": pairs["literal_ar"], "label": 1,
                            "group": pairs["pair_id"], "issue": pairs["issue"]})
    natural = pd.DataFrame({"text": pairs["natural_ar"], "label": 0,
                            "group": pairs["pair_id"], "issue": "none"})
    return pd.concat([literal, natural], ignore_index=True)
