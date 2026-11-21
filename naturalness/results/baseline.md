# Baseline results

Data: 48 sentences from 24 pairs, 5-fold grouped cross-validation.

| Model | Accuracy | Macro-F1 |
|---|---|---|
| Rules | 85.5% ± 10.0% | 84.7% ± 11.1% |
| TF-IDF char n-grams + LogReg | 72.5% ± 11.2% | 71.8% ± 11.5% |

With this little data the numbers have wide error bars; treat them as a pipeline check, not a result.
