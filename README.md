# LinguAlyzer

**Language. Culture. Intelligence.**

Arabic Localization Quality Analyzer using NLP and multilingual sentence embeddings. It helps a reviewer check an English to Arabic translation.

## Try it

**Live app (Streamlit):** https://lingualyzer-j46qnmpej563zcfh79exbv.streamlit.app

## Code

The app is in the [`LinguAlyzer_Final_Polished`](./LinguAlyzer_Final_Polished) folder:

- `app.py`: the Streamlit app
- `requirements.txt`: Python packages
- `fancy_preview.html`: a visual preview of the interface

To run it locally:


## Research: Arabic translation naturalness

The [`naturalness`](./naturalness) folder holds a dataset and benchmark for detecting and repairing literal Arabic translations («قام المستخدم بتحديث» → «حدّث المستخدم»): annotation guidelines, baselines (rules, TF-IDF + logistic regression), and an AraBERT fine-tuning notebook for Google Colab.
