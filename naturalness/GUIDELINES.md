# Annotation guidelines

Each row in `data/pairs.csv` is a **pair**: an English UI string, a literal Arabic translation of it, and a natural Arabic rewrite.

## Columns

| Column | What to write |
|---|---|
| `pair_id` | `p001`, `p002`, … Never reuse an id. |
| `source_en` | The English string, as it appears in the app. |
| `literal_ar` | An Arabic translation that is grammatical but reads as translated. |
| `natural_ar` | The same meaning, written the way a native Arabic writer would. |
| `issue` | The main reason `literal_ar` is literal (one value from the table below). |
| `status` | `seed` (drafted, not checked yet) or `reviewed` (checked by an annotator). |

Save as UTF-8. Wrap a cell in double quotes if it contains a Latin comma `,`.

## Issue types

| `issue` | Pattern | Example (literal → natural) |
|---|---|---|
| `qam_bi` | «قام بـ / قم بـ» + masdar | قام المستخدم بتحديث ← حدّث المستخدم |
| `passive_tam_yatim` | «تم / يتم» + masdar | يتم تحميل الملفات ← جارٍ تحميل الملفات |
| `biwasita` | «بواسطة» for the agent | أُرسلت بواسطة التطبيق ← أرسلها التطبيق |
| `khas_bi` | «الخاص بك» | كلمة المرور الخاصة بك ← كلمة مرورك |
| `redundant_pronoun` | extra pronoun or copula | أنت لديك ← لديك |
| `purpose_clause` | «لكي / من أجل» | لكي تستمر ← للمتابعة |
| `bishakl` | «بشكل» + adjective | بشكل ناجح ← بنجاح |
| `calque` | English idiom or structure | دعنا نبدأ ← لنبدأ |

If a sentence has two issues, pick the one that a reviewer would fix first. If a new pattern keeps coming up, add a new issue type here and in `common.py`.

## Rules

1. **Naturalness only.** Spelling, glossary and punctuation are out of scope; the app checks those separately.
2. **Same meaning.** `natural_ar` must say what `source_en` says, nothing added or dropped.
3. **Modern Standard Arabic, UI register**: buttons, alerts, settings, onboarding, errors.
4. **Real sources first.** Strings from real apps (screenshots, open-source `.strings` / `.xliff` files) are worth more than invented ones. Note where they came from in your own log, not in the dataset.
5. **When unsure, leave it out.**
6. **Spread the issue types.** Avoid more than about a quarter of the data in one type.

## Quality

- Review every `seed` row; fix or delete it, then mark it `reviewed`.
- For a report, have a second annotator label a random 10–20% and compute agreement (Cohen's kappa). Disagreements usually point to an unclear guideline.

## Checklist before committing

```bash
python validate.py   # schema, duplicates, issue types
python baseline.py   # re-runs the baselines and updates results/baseline.md
```
