"""Baselines for detecting literal Arabic translations.

1. Rules: flag a sentence if it contains a known literal pattern.
2. TF-IDF character n-grams + logistic regression.

Both are evaluated with grouped k-fold cross-validation: the literal and
natural sides of a pair are always in the same fold, so the model never
sees the answer to a test pair during training.
"""
import re
from pathlib import Path

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.model_selection import GroupKFold
from sklearn.pipeline import make_pipeline

from common import load_pairs, to_rows

RULES = [r"\bقا?م\s?ب", r"\bقم ب", r"\bيتم\b", r"\bتم\b", r"بواسطة", r"الخاصة? ب",
         r"\bلكي\b", r"من أجل", r"بشكل", r"في الواقع", r"\bأنت لديك", r"\bهو\b", r"\bهي\b",
         r"دعنا", r"سوف يقوم", r"لم يتم"]


def rule_predict(texts):
    return np.array([int(any(re.search(p, t) for p in RULES)) for t in texts])


def main():
    rows = to_rows(load_pairs())
    X, y, groups = rows["text"].to_numpy(), rows["label"].to_numpy(), rows["group"].to_numpy()
    k = min(5, len(set(groups)))
    folds = list(GroupKFold(n_splits=k).split(X, y, groups))

    results = {}
    for name, predict in {
        "Rules": lambda tr, te: rule_predict(X[te]),
        "TF-IDF char n-grams + LogReg": lambda tr, te: make_pipeline(
            TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 5), sublinear_tf=True),
            LogisticRegression(max_iter=1000, C=4.0),
        ).fit(X[tr], y[tr]).predict(X[te]),
    }.items():
        acc, f1 = [], []
        for tr, te in folds:
            pred = predict(tr, te)
            acc.append(accuracy_score(y[te], pred))
            f1.append(f1_score(y[te], pred, average="macro", zero_division=0))
        results[name] = (np.mean(acc), np.std(acc), np.mean(f1), np.std(f1))

    lines = [
        "# Baseline results",
        "",
        f"Data: {len(rows)} sentences from {len(set(groups))} pairs, {k}-fold grouped cross-validation.",
        "",
        "| Model | Accuracy | Macro-F1 |",
        "|---|---|---|",
    ]
    for name, (a, sa, f, sf) in results.items():
        lines.append(f"| {name} | {a:.1%} ± {sa:.1%} | {f:.1%} ± {sf:.1%} |")
    lines += ["", "With this little data the numbers have wide error bars; treat them as a pipeline check, not a result."]
    report = "\n".join(lines)
    print(report)
    out = Path(__file__).parent / "results" / "baseline.md"
    out.write_text(report + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
