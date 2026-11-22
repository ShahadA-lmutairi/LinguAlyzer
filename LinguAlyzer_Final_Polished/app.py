
import re
import pandas as pd
import streamlit as st
from sentence_transformers import SentenceTransformer, util

import xliff
from checks import (arabic_ratio, extract_numbers, extract_placeholders,
                    length_ratio, strip_tags)

st.set_page_config(
    page_title="LinguAlyzer",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #f7f8f8 0%, #f2f5f4 100%);
    }
    [data-testid="stSidebar"] {
        background: #0f2f2b;
    }
    [data-testid="stSidebar"] * {
        color: #ffffff !important;
    }
    .block-container {
        padding-top: 1.4rem;
        max-width: 1450px;
    }
    .hero {
        background: rgba(255,255,255,0.92);
        border: 1px solid #e7ecea;
        border-radius: 24px;
        padding: 28px 30px;
        box-shadow: 0 12px 35px rgba(20, 49, 44, 0.08);
        margin-bottom: 18px;
    }
    .eyebrow {
        font-size: 0.82rem;
        letter-spacing: .12em;
        font-weight: 700;
        color: #0c7a68;
        text-transform: uppercase;
        margin-bottom: 8px;
    }
    .hero h1 {
        font-size: 2.4rem;
        line-height: 1.08;
        margin: 0 0 8px 0;
        color: #0e2233;
    }
    .hero p {
        color: #60706d;
        font-size: 1.02rem;
        margin: 0;
    }
    .soft-card {
        background: white;
        border: 1px solid #e5ebe8;
        border-radius: 20px;
        padding: 18px;
        box-shadow: 0 8px 24px rgba(20, 49, 44, 0.06);
    }
    .metric-card {
        background: #ffffff;
        border: 1px solid #e7ecea;
        border-radius: 18px;
        padding: 18px 16px;
        box-shadow: 0 8px 20px rgba(20, 49, 44, 0.05);
        min-height: 120px;
    }
    .metric-title {
        color: #6a7774;
        font-size: 0.82rem;
        margin-bottom: 8px;
    }
    .metric-value {
        color: #0f2f2b;
        font-size: 1.65rem;
        font-weight: 800;
    }
    .status-good {
        color: #0c7a68;
        font-weight: 700;
    }
    .small-note {
        color: #74817e;
        font-size: 0.84rem;
    }
    .stTextArea textarea {
        border-radius: 16px !important;
        border: 1px solid #dfe7e3 !important;
        background: #ffffff !important;
        color: #102232 !important;
        caret-color: #102232 !important;
        font-weight: 500 !important;
    }
    .stTextArea textarea::placeholder {
        color: #7a878f !important;
        opacity: 1 !important;
    }
    .stTextArea label, .stTextArea p, [data-testid="stTextArea"] label {
        color: #102232 !important;
    }
    .stMarkdown, .stMarkdown p, .stMarkdown span, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #102232;
    }
    div[data-baseweb="tab"] {
        color: #263947 !important;
    }
    div[data-baseweb="tab"][aria-selected="true"] {
        color: #0f7a68 !important;
        font-weight: 700 !important;
    }
    .stButton > button {
        border-radius: 14px !important;
        border: 0 !important;
        font-weight: 700 !important;
        min-height: 46px;
    }
    .stButton > button[kind="primary"] {
        background: linear-gradient(90deg, #0b6458 0%, #0f8574 100%) !important;
        color: white !important;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 12px 12px 0 0;
        padding: 10px 16px;
    }
    div[data-testid="stMetric"] {
        background: white;
        border: 1px solid #e7ecea;
        border-radius: 16px;
        padding: 14px;
        box-shadow: 0 6px 18px rgba(20,49,44,.04);
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def load_model():
    return SentenceTransformer("sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2")

model = load_model()

DEFAULT_GLOSSARY = {
    "settings": "الإعدادات",
    "privacy": "الخصوصية",
    "account": "الحساب",
    "continue": "متابعة",
    "cancel": "إلغاء",
    "download": "تنزيل",
    "save": "حفظ",
}

def semantic_similarity(source: str, target: str) -> float:
    emb = model.encode([strip_tags(source), strip_tags(target)], convert_to_tensor=True, normalize_embeddings=True)
    score = util.cos_sim(emb[0], emb[1]).item()
    return max(0.0, min(1.0, score))

def terminology_score(source: str, target: str, glossary: dict):
    matched, missed = [], []
    s = source.lower()
    for en, ar in glossary.items():
        if en.lower() in s:
            (matched if ar in target else missed).append((en, ar))
    total = len(matched) + len(missed)
    return (1.0 if total == 0 else len(matched) / total), matched, missed

def consistency_score(source, target, extractor):
    return 1.0 if extractor(source) == extractor(target) else 0.0

def score_total(semantic, terminology, arabic, length, placeholders, numbers):
    length_component = 1.0 if 0.55 <= length <= 1.8 else 0.6
    return round(100 * (
        semantic * .50 +
        terminology * .18 +
        arabic * .10 +
        length_component * .07 +
        placeholders * .08 +
        numbers * .07
    ))

def parse_glossary(text):
    g = {}
    for line in text.splitlines():
        if "=" in line:
            a,b = line.split("=",1)
            if a.strip() and b.strip():
                g[a.strip()] = b.strip()
    return g

def analyze(source, target, glossary):
    sem = semantic_similarity(source, target)
    term, matched, missed = terminology_score(source, target, glossary)
    arab = arabic_ratio(target)
    lr = length_ratio(source, target)
    ph = consistency_score(source, target, extract_placeholders)
    num = consistency_score(source, target, extract_numbers)
    total = score_total(sem, term, arab, lr, ph, num)

    issues = []
    if sem < .60: issues.append(("Meaning", "Semantic alignment may need review."))
    if missed: issues.append(("Terminology", "Some glossary terms are inconsistent."))
    if arab < .85: issues.append(("Script", "Target contains noticeable non-Arabic text."))
    if not (.55 <= lr <= 1.8): issues.append(("Length", "Target/source length ratio is unusual."))
    if not ph: issues.append(("Placeholders", "Placeholder tokens are not preserved."))
    if not num: issues.append(("Numbers", "Numeric values differ between source and target."))

    return dict(overall=total, semantic=sem, terminology=term, arabic_ratio=arab,
                length_ratio=lr, placeholders=ph, numbers=num, issues=issues, missed_terms=missed)

with st.sidebar:
    st.markdown("## 🌿 LinguAlyzer")
    st.caption("Language AI • Localization • NLP")
    st.markdown("---")
    st.markdown("### Workspace")
    st.write("📝 Text Analysis")
    st.write("📚 Batch Analysis")
    st.write("🧩 Terminology")
    st.write("📈 Evaluation")
    st.markdown("---")
    st.caption("Arabic Localization Quality Analyzer")

st.markdown("""
<div class="hero">
  <div class="eyebrow">AI-powered • Human-centered</div>
  <h1>Arabic Localization Quality Analyzer</h1>
  <p>Evaluate English → Arabic localization with multilingual NLP and practical linguistic quality checks.</p>
  <div style="margin-top:12px;color:#667681;font-size:.86rem;">Developed by <b style="color:#0b1f33;">Shahad Almutairi</b> · Applied Linguistics • Localization • NLP</div>
</div>
""", unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["Text Analysis", "Batch Evaluation", "About"])

with tab1:
    left, right = st.columns(2, gap="large")
    with left:
        st.markdown("<div style=\"color:#0b1f33;font-size:1.15rem;font-weight:800;margin-bottom:8px;\">English Source</div>", unsafe_allow_html=True)
        source = st.text_area(
            "Source",
            value="Go to Settings to update your privacy preferences, then select Continue.",
            height=170,
            label_visibility="collapsed"
        )
    with right:
        st.markdown("<div style=\"color:#0b1f33;font-size:1.15rem;font-weight:800;margin-bottom:8px;\">Arabic Localized Text</div>", unsafe_allow_html=True)
        target = st.text_area(
            "Target",
            value="انتقل إلى الإعدادات لتحديث تفضيلات الخصوصية، ثم اختر متابعة.",
            height=170,
            label_visibility="collapsed"
        )

    with st.expander("Terminology glossary"):
        glossary_text = st.text_area(
            "Glossary",
            value="\n".join(f"{k} = {v}" for k,v in DEFAULT_GLOSSARY.items()),
            height=140,
            label_visibility="collapsed"
        )

    c1, c2, c3 = st.columns([1,1,2])
    with c1:
        if st.button("Clear"):
            st.rerun()
    with c2:
        st.button("Swap")
    with c3:
        analyze_clicked = st.button("Analyze Translation →", type="primary", use_container_width=True)

    if analyze_clicked:
        result = analyze(source, target, parse_glossary(glossary_text))
        st.markdown("## Results")

        m1,m2,m3,m4 = st.columns(4)
        with m1:
            st.markdown(f"""<div class="metric-card"><div class="metric-title">Overall Quality</div><div class="metric-value">{result['overall']}/100</div><div class="status-good">AI-assisted score</div></div>""", unsafe_allow_html=True)
        with m2:
            st.markdown(f"""<div class="metric-card"><div class="metric-title">Semantic Similarity</div><div class="metric-value">{result['semantic']*100:.1f}%</div><div class="small-note">Meaning alignment</div></div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div class="metric-card"><div class="metric-title">Terminology</div><div class="metric-value">{result['terminology']*100:.1f}%</div><div class="small-note">Glossary consistency</div></div>""", unsafe_allow_html=True)
        with m4:
            st.markdown(f"""<div class="metric-card"><div class="metric-title">Arabic Script</div><div class="metric-value">{result['arabic_ratio']*100:.1f}%</div><div class="small-note">Target-language signal</div></div>""", unsafe_allow_html=True)

        st.markdown("### Quality Findings")
        if not result["issues"]:
            st.success("No major automatic flags detected. Human linguistic review is still recommended.")
        else:
            for cat, msg in result["issues"]:
                st.warning(f"**{cat}:** {msg}")

        s1,s2,s3 = st.columns(3)
        s1.metric("Length Ratio", f"{result['length_ratio']:.2f}")
        s2.metric("Placeholders", "Pass" if result["placeholders"] else "Review")
        s3.metric("Numbers", "Pass" if result["numbers"] else "Review")

with tab2:
    st.markdown("### Batch Evaluation")
    st.caption("Upload a CSV with `source` and `target` columns, or a translation file: "
               "XLIFF 1.2 / 2.0 (`.xlf`, `.xliff`) or SDL Trados (`.sdlxliff`).")
    uploaded = st.file_uploader("Upload file", type=["csv", "xlf", "xliff", "sdlxliff"])
    if uploaded:
        name = uploaded.name.lower()
        pairs = None
        if name.endswith(".csv"):
            df = pd.read_csv(uploaded)
            if {"source", "target"}.issubset(df.columns):
                pairs = pd.DataFrame({
                    "id": df["id"] if "id" in df.columns else range(1, len(df) + 1),
                    "source": df["source"].astype(str),
                    "target": df["target"].fillna("").astype(str),
                })
            else:
                st.error("CSV must contain `source` and `target` columns.")
        else:
            try:
                units = xliff.parse(uploaded.getvalue())
            except xliff.XliffError as exc:
                st.error(str(exc))
            else:
                if units:
                    pairs = pd.DataFrame([vars(u) for u in units])
                else:
                    st.warning("No translation units found in this file.")

        if pairs is not None and len(pairs):
            translated = pairs[pairs["target"].str.strip() != ""]
            skipped = len(pairs) - len(translated)
            k1, k2, k3 = st.columns(3)
            k1.metric("Segments", len(pairs))
            k2.metric("Analyzed", len(translated))
            k3.metric("Untranslated (skipped)", skipped)

            rows = []
            progress = st.progress(0.0, text="Analyzing segments…")
            for i, (_, row) in enumerate(translated.iterrows(), 1):
                r = analyze(row["source"], row["target"], DEFAULT_GLOSSARY)
                rows.append({
                    "id": row["id"],
                    "source": row["source"],
                    "target": row["target"],
                    "state": row.get("state", ""),
                    "overall_score": r["overall"],
                    "semantic_similarity": round(r["semantic"], 3),
                    "terminology_score": round(r["terminology"], 3),
                    "issue_count": len(r["issues"]),
                    "issues": "; ".join(f"{c}: {m}" for c, m in r["issues"]),
                })
                progress.progress(i / len(translated), text=f"Analyzing segments… {i}/{len(translated)}")
            progress.empty()

            if rows:
                out = pd.DataFrame(rows).sort_values(["issue_count", "overall_score"], ascending=[False, True])
                out = out[["id", "issue_count", "issues", "overall_score", "source", "target", "state",
                           "semantic_similarity", "terminology_score"]]
                flagged = int((out["issue_count"] > 0).sum())
                st.markdown(f"**{flagged} of {len(out)} segments have at least one flag.** Most flagged first.")
                st.dataframe(out, use_container_width=True, hide_index=True)
                st.download_button("Download Results (CSV)", out.to_csv(index=False).encode("utf-8-sig"),
                                   "localization_results.csv", "text/csv")

with tab3:
    st.markdown("""
    ### Project Concept
    LinguAlyzer is a portfolio NLP prototype designed to support English-to-Arabic localization review.

    **Checks included**
    - Multilingual semantic similarity
    - Terminology consistency
    - Placeholder preservation
    - Numeric consistency
    - Arabic-script ratio
    - Length-ratio heuristic

    **Files**
    - CSV, XLIFF 1.2 / 2.0 and SDL Trados `.sdlxliff`

    **Positioning**
    Human-in-the-loop language quality support — not a replacement for professional linguists.
    """)
