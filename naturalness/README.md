# Arabic Translation Naturalness

A small dataset and benchmark for one question:

> **Can a model tell a literal Arabic translation from natural Arabic, and fix it?**

Machine and human translations into Arabic are often grammatical but read as translated: «قام المستخدم بتحديث الإعدادات» instead of «حدّث المستخدم الإعدادات». This project collects such pairs from app interfaces, labels the pattern behind each one, and measures how well different models detect and repair them.

## Status

**Work in progress.** 24 seed pairs (48 sentences) to build and test the pipeline. They were drafted to start the project and are being reviewed; the target is 500+ reviewed pairs from real app strings.

## Data

[`data/pairs.csv`](data/pairs.csv), one row per pair:

| Column | Description |
|---|---|
| `pair_id` | Stable id |
| `source_en` | English UI string |
| `literal_ar` | Grammatical but literal Arabic translation |
| `natural_ar` | Natural Arabic with the same meaning |
| `issue` | Pattern behind the literal version (see [guidelines](GUIDELINES.md)) |
| `status` | `seed` or `reviewed` |

For classification, each pair becomes two sentences (`literal` = 1, `natural` = 0). Folds are **grouped by pair**, so both sides of a pair are always in the same fold and a model is never tested on a sentence whose counterpart it trained on.

## Tasks

1. **Detection**: classify a sentence as literal or natural.
2. **Repair** (planned): given `source_en` and `literal_ar`, produce natural Arabic; judged against `natural_ar` and by human review.

## Results

See [`results/baseline.md`](results/baseline.md). Current models:

| Model | How to run |
|---|---|
| Rules (known literal patterns) | `python baseline.py` |
| TF-IDF character n-grams + logistic regression | `python baseline.py` |
| AraBERT fine-tuned | [`notebooks/arabert_finetune.ipynb`](notebooks/arabert_finetune.ipynb) in Google Colab [![Open in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ShahadA-lmutairi/LinguAlyzer/blob/main/naturalness/notebooks/arabert_finetune.ipynb) |
| Large language models (planned) | Zero-shot and few-shot prompting, detection and repair |

The rules were written from the same patterns as the seed data, so they are expected to score well on it; the real test is new pairs from real apps.

## Run

```bash
cd naturalness
pip install -r requirements.txt
python validate.py
python baseline.py
```

## Roadmap

- [ ] Review the 24 seed pairs
- [ ] 200 reviewed pairs from real app strings, then 500+
- [ ] Inter-annotator agreement on a sample
- [ ] AraBERT and CAMeLBERT results with error analysis
- [ ] LLM evaluation: detection and repair, zero-shot vs few-shot
- [ ] Publish the dataset on Hugging Face with a dataset card
- [ ] Short write-up of findings

## License

Not chosen yet. Suggested before publishing: MIT for the code, CC BY 4.0 for the data.
