from pathlib import Path
import html
import pandas as pd
import numpy as np
import streamlit as st
from master_compare_v3 import (
    CompareConfig,
    TECH_PARAMS,
    compare_master,
    list_companies,
    list_models,
    load_master_dataset,
)

st.set_page_config(
    page_title="Linearführungs-Vergleichstool",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
 
<style> 
.spinning-gear {
    position: fixed;
    bottom: 20px;
    right: 20px;
    font-size: 40px;
    z-index: 9999;
    animation: spin 5s linear infinite;
}

@keyframes spin {
    from { transform: rotate(0deg); }
    to   { transform: rotate(360deg); }
}
.hero {
    position: relative;
    overflow: hidden;

    background: linear-gradient(135deg, var(--navy-950), var(--navy-800));
    border: 1px solid rgba(255,255,255,.12);
    border-radius: 30px;
    padding: 34px 38px;
    margin-bottom: 24px;
    color: white;
    box-shadow: 0 24px 60px rgba(7,35,55,.22);
}

.hero::before {
    content: "";
    position: absolute;
    top: 0;
    left: -150%;
    width: 80%;
    height: 100%;

    background: linear-gradient(
        120deg,
        transparent,
        rgba(255,255,255,0.15),
        transparent
    );

    animation: shine 6s infinite;
}

@keyframes shine {
    0% {
        left: -150%;
    }

    100% {
        left: 200%;
    }
}
:root {
    --navy-950: #061826;
    --navy-900: #08243A;
    --navy-800: #0B3554;
    --navy-700: #0D4B73;
    --blue-500: #168AD5;
    --blue-400: #3EA6E8;
    --ice-100: #EAF5FC;
    --surface: rgba(255, 255, 255, 0.96);
    --surface-soft: #F5F9FC;
    --text: #102A3A;
    --muted: #5F7280;
    --line: rgba(16, 42, 58, 0.11);
}
.stApp {
    background:
        radial-gradient(circle at 82% 4%, rgba(62,166,232,.17), transparent 28rem),
        linear-gradient(145deg, #F7FAFC 0%, #EAF3F8 100%);
    color: var(--text);
}
.block-container { max-width: 1460px; padding-top: 1.8rem; padding-bottom: 4rem; }
.hero {
    background: linear-gradient(135deg, var(--navy-950), var(--navy-800));
    border: 1px solid rgba(255,255,255,.12); border-radius: 30px; padding: 34px 38px;
    margin-bottom: 24px; color: white; box-shadow: 0 24px 60px rgba(7,35,55,.22);
}
.hero-eyebrow { color: #8ED2F6; font-size:.78rem; font-weight:700; letter-spacing:.14em; text-transform:uppercase; margin-bottom:10px; }
.hero h1 { color:white!important; font-size:clamp(2rem,4vw,3.25rem); line-height:1.02; letter-spacing:-.045em; margin:0 0 12px 0; }
.hero p { color:rgba(255,255,255,.76); max-width:780px; font-size:1.04rem; line-height:1.55; margin:0; }
div[data-testid="stVerticalBlockBorderWrapper"] { background:var(--surface); border:1px solid var(--line); border-radius:24px; box-shadow:0 12px 38px rgba(22,55,75,.08); }
[data-testid="stSidebar"] { background:linear-gradient(180deg,var(--navy-950),var(--navy-900)); border-right:1px solid rgba(255,255,255,.08); }
[data-testid="stSidebar"] * { color:#F4FAFD; }
[data-testid="stSidebar"] [data-baseweb="select"] *, [data-testid="stSidebar"] [data-baseweb="input"] *, [data-testid="stSidebar"] input { color:#102A3A!important; }
[data-testid="stSidebar"] hr { border-color:rgba(255,255,255,.12); }
.stButton > button { background:linear-gradient(135deg,var(--navy-800),var(--blue-500)); color:white; border:0; border-radius:16px; min-height:3.1rem; font-weight:700; box-shadow:0 10px 24px rgba(13,75,115,.24); transition:transform .15s ease,box-shadow .15s ease; }
.stButton > button:hover { color:white; transform:translateY(-1px); box-shadow:0 14px 30px rgba(13,75,115,.30); }
[data-testid="stMetric"] { background:var(--surface); border:1px solid var(--line); border-radius:22px; padding:16px 18px; box-shadow:0 10px 28px rgba(22,55,75,.08); }
[data-testid="stMetricLabel"] { color:var(--muted); }
[data-testid="stMetricValue"] { color:var(--navy-900); letter-spacing:-.03em; }
.stTabs [data-baseweb="tab-list"] { gap:8px; background:rgba(255,255,255,.72); padding:6px; border-radius:16px; border:1px solid var(--line); }
.stTabs [data-baseweb="tab"] { border-radius:12px; padding:9px 18px; }
.stTabs [aria-selected="true"] { background:var(--navy-800); color:white!important; }
.result-card { border:1px solid rgba(22,138,213,.18); background:linear-gradient(135deg,rgba(255,255,255,.98),rgba(234,245,252,.93)); padding:18px 22px; border-radius:22px; margin:10px 0 18px 0; box-shadow:0 12px 32px rgba(22,55,75,.08); }
.definition-card { background:white; border:1px solid var(--line); border-radius:22px; padding:22px 24px; height:100%; box-shadow:0 12px 32px rgba(22,55,75,.07); }
.definition-number { display:inline-flex; align-items:center; justify-content:center; width:34px; height:34px; border-radius:11px; background:var(--ice-100); color:var(--navy-700); font-weight:800; margin-bottom:12px; }
.definition-title { color:var(--navy-900); font-size:1.05rem; font-weight:800; margin-bottom:7px; }
.definition-text { color:var(--muted); line-height:1.58; font-size:.95rem; }
.callout { background:linear-gradient(135deg,var(--navy-950),var(--navy-800)); color:white; border-radius:24px; padding:22px 25px; margin:18px 0; box-shadow:0 16px 38px rgba(7,35,55,.18); }
.callout strong { color:#8ED2F6; }
.relaxed-box { background:linear-gradient(135deg,#061826,#0B3554)!important; border-left:4px solid #3EA6E8!important; color:#FFFFFF!important; border-radius:0 16px 16px 0; padding:16px 20px; margin:10px 0 18px 18px; line-height:1.65; box-shadow:0 12px 28px rgba(7,35,55,.18); }
.relaxed-box strong { color:#8ED2F6!important; }
.strict-box { background:linear-gradient(135deg,#061826,#0B3554)!important; border-left:4px solid #3EA6E8!important; border-radius:0 16px 16px 0; padding:16px 20px; margin:10px 0 18px 18px; color:#FFFFFF!important; line-height:1.65; box-shadow:0 12px 28px rgba(7,35,55,.18); }
.strict-box,.strict-box * { color:#FFFFFF!important; }
.strict-box strong { color:#8ED2F6!important; }
.section-title { color:var(--navy-900); font-size:1.45rem; font-weight:800; letter-spacing:-.025em; margin:10px 0 6px; }
.section-subtitle { color:var(--muted); margin-bottom:18px; }
.small-note { color:var(--muted); font-size:.91rem; line-height:1.55; }
[data-baseweb="select"]>div,[data-baseweb="input"]>div,.stNumberInput>div>div,.stTextInput>div>div { border-radius:14px!important; }
.compact-table-wrap { width:100%; overflow-x:auto; margin:10px 0 14px 0; border-radius:16px; border:1px solid rgba(16,42,58,.13); box-shadow:0 8px 24px rgba(22,55,75,.07); background:white; }
.compact-table { width:100%; border-collapse:collapse; table-layout:auto; font-size:.88rem; line-height:1.2; }
.compact-table th { background:#08243A; color:#FFFFFF; text-align:center!important; vertical-align:middle; font-weight:700; padding:10px 9px; white-space:nowrap; border-right:1px solid rgba(255,255,255,.13); }
.compact-table td { color:#183548; text-align:center!important; vertical-align:middle; padding:8px 9px; white-space:nowrap; border-right:1px solid rgba(16,42,58,.08); border-bottom:1px solid rgba(16,42,58,.08); }
.compact-table tbody tr:nth-child(even) { background:#F5F9FC; }
.compact-table tbody tr:hover { background:#EAF5FC; }
.compact-table th:last-child,.compact-table td:last-child { border-right:0; }
.compact-table tbody tr:last-child td { border-bottom:0; }
.reference-pill { display:inline-flex; align-items:center; gap:8px; background:linear-gradient(135deg,#0B3554,#168AD5); color:#FFFFFF; border-radius:999px; padding:8px 14px; margin:2px 0 9px 0; font-size:.82rem; font-weight:700; box-shadow:0 8px 20px rgba(13,75,115,.20); }
.reference-pill-number { display:inline-flex; align-items:center; justify-content:center; width:22px; height:22px; border-radius:50%; background:rgba(255,255,255,.20); color:#FFFFFF; font-size:.75rem; font-weight:800; }
.definition-heading { display:flex; align-items:center; gap:11px; margin-bottom:12px; }
.definition-heading .definition-number { margin-bottom:0; flex:0 0 auto; }
.definition-heading .definition-title { margin-bottom:0; }
.definition-formula { background:linear-gradient(135deg,#071F33,#0B3554); color:#FFFFFF; border-radius:14px; padding:11px 13px; margin-top:14px; text-align:center; font-size:.94rem; line-height:1.45; font-weight:700; box-shadow:inset 0 1px 0 rgba(255,255,255,.08); }
.definition-formula-label { display:block; color:#8ED2F6; font-size:.68rem; letter-spacing:.08em; text-transform:uppercase; margin-bottom:4px; }
.check-panel,.missing-panel { background:rgba(255,255,255,.72); border:1px solid rgba(16,42,58,.09); border-radius:22px; padding:10px; margin:8px 0 22px 0; box-shadow:0 12px 30px rgba(22,55,75,.06); }
.check-list,.missing-list { list-style:none; margin:0; padding:0; display:flex; flex-direction:column; gap:7px; }
.check-item,.missing-item { display:grid; grid-template-columns:42px 14px minmax(0,1fr); align-items:center; column-gap:11px; min-height:46px; padding:7px 14px 7px 8px; background:#FFFFFF; border:1px solid rgba(16,42,58,.08); border-radius:15px; color:#183548; box-shadow:0 3px 10px rgba(22,55,75,.04); }
.check-item:hover,.missing-item:hover { transform:translateY(-1px); box-shadow:0 8px 18px rgba(22,55,75,.08); transition:.15s ease; }
.check-key,.missing-key { display:inline-flex; align-items:center; justify-content:center; min-width:36px; height:30px; padding:0 6px; background:#08243A; color:#FFFFFF; border-radius:10px; font-size:.77rem; font-weight:800; letter-spacing:.02em; }
.status-dot { width:10px; height:10px; border-radius:50%; box-shadow:0 0 0 4px rgba(22,138,213,.10); }
.status-pass .status-dot { background:#15956B; box-shadow:0 0 0 4px rgba(21,149,107,.11); }
.status-pass { border-left:3px solid #15956B; }
.status-notchecked .status-dot { background:#D89B28; box-shadow:0 0 0 4px rgba(216,155,40,.13); }
.status-notchecked { border-left:3px solid #D89B28; }
.status-fail .status-dot { background:#C95050; box-shadow:0 0 0 4px rgba(201,80,80,.11); }
.status-fail { border-left:3px solid #C95050; }
.status-neutral .status-dot,.missing-item .status-dot { background:#168AD5; }
.check-text,.missing-text { min-width:0; color:#405A69; line-height:1.42; font-size:.92rem; }
.check-text strong { color:#102A3A; font-weight:750; }
.missing-item { border-left:3px solid #168AD5; }
.empty-comparison { padding:15px 17px; color:#426172; background:#F4F9FC; border-radius:14px; border:1px dashed rgba(22,138,213,.30); text-align:center; }
.math-intro { background:linear-gradient(135deg,rgba(255,255,255,.98),rgba(234,245,252,.95)); border:1px solid var(--line); border-radius:24px; padding:22px 24px; margin-bottom:18px; box-shadow:0 12px 30px rgba(22,55,75,.07); color:var(--text); line-height:1.6; }
.math-bubble { background:rgba(255,255,255,.98); border:1px solid rgba(16,42,58,.10); border-radius:26px; padding:22px; min-height:220px; box-shadow:0 14px 34px rgba(22,55,75,.08); margin-bottom:14px; }
.math-chip { display:inline-block; color:#0D4B73; background:#EAF5FC; border-radius:999px; padding:6px 11px; font-size:.75rem; font-weight:800; letter-spacing:.06em; text-transform:uppercase; margin-bottom:13px; }
.math-formula { background:#071F33; color:#FFFFFF; border-radius:16px; padding:13px 14px; text-align:center; font-size:1.02rem; font-weight:700; margin:12px 0; overflow-x:auto; }
.math-title { color:#08243A; font-size:1.08rem; font-weight:800; margin-bottom:6px; }
.math-text { color:#5F7280; line-height:1.55; font-size:.93rem; }
.math-example { color:#0D4B73; font-size:.88rem; margin-top:10px; font-weight:650; }
@media (max-width:800px) { .hero { padding:28px 24px; border-radius:24px; } .block-container { padding-left:1rem; padding-right:1rem; } }
</style>
""", unsafe_allow_html=True)
st.markdown(
    '<div class="spinning-gear">⚙️</div>',
    unsafe_allow_html=True
)
# st.markdown(
#     '<div class="flying-gear">⚙️</div>',
#     unsafe_allow_html=True
# )

APP_DIR = Path(__file__).resolve().parent
MASTER_PATH = APP_DIR / "Master_Linear_Guides2.xlsx"

@st.cache_data(show_spinner=False)
def load_data(path_string: str):
    return load_master_dataset(path_string)


def compact_table(df: pd.DataFrame) -> str:
    headers = "".join(f"<th>{html.escape(str(col))}</th>" for col in df.columns)
    rows = []
    for _, row in df.iterrows():
        cells = "".join(
            f"<td>{html.escape('—' if pd.isna(value) else str(value))}</td>"
            for value in row.tolist()
        )
        rows.append(f"<tr>{cells}</tr>")
    return (
        '<div class="compact-table-wrap"><table class="compact-table">'
        f'<thead><tr>{headers}</tr></thead><tbody>{"".join(rows)}</tbody></table></div>'
    )


def vertical_checks(value) -> str:
    raw = "" if value is None or pd.isna(value) else str(value)
    entries = [part.strip() for part in raw.split("|") if part.strip()]
    if not entries:
        entries = ["Prüfung: Keine Details zu Pflichtprüfungen verfügbar."]
    items = []
    for entry in entries:
        if ":" in entry:
            key, description = entry.split(":", 1)
        else:
            key, description = "Prüfung", entry
        description = description.strip()
        upper = description.upper()
        if upper.startswith("PASS"):
            status_class, status_word, display_word = "status-pass", "PASS", "BESTANDEN"
        elif upper.startswith("FAIL"):
            status_class, status_word, display_word = "status-fail", "FAIL", "NICHT BESTANDEN"
        elif upper.startswith("NOT CHECKED"):
            status_class, status_word, display_word = "status-notchecked", "NOT CHECKED", "NICHT GEPRÜFT"
        else:
            status_class, status_word, display_word = "status-neutral", "INFO", "INFO"
        if description.upper().startswith(status_word):
            remainder = description[len(status_word):].lstrip(": ")
            display_text = f"<strong>{html.escape(display_word)}</strong>"
            if remainder:
                display_text += f" · {html.escape(remainder)}"
        else:
            display_text = html.escape(description)
        items.append(
            f'<li class="check-item {status_class}">'
            f'<span class="check-key">{html.escape(key.strip())}</span>'
            f'<span class="status-dot"></span>'
            f'<span class="check-text">{display_text}</span></li>'
        )
    return f'<div class="check-panel"><ul class="check-list">{"".join(items)}</ul></div>'


def vertical_missing(value) -> str:
    raw = "" if value is None or pd.isna(value) else str(value).strip()
    if not raw or raw.lower() == "none":
        return (
            '<div class="missing-panel">'
            '<div class="empty-comparison">Alle ausgewählten Parameter konnten direkt verglichen werden.</div>'
            '</div>'
        )
    entries = [part.strip() for part in raw.split(",") if part.strip()]
    items = []
    for index, entry in enumerate(entries, start=1):
        items.append(
            f'<li class="missing-item"><span class="missing-key">{index:02d}</span>'
            f'<span class="status-dot"></span>'
            f'<span class="missing-text">{html.escape(entry)}</span></li>'
        )
    return f'<div class="missing-panel"><ul class="missing-list">{"".join(items)}</ul></div>'


# Hero
st.markdown("""
<div class="hero">
  <div class="hero-eyebrow">Umschlüsselungstool – Bosch Rexroth AG</div>
  <h1>Linearführungswagen-Umschlüsselungstool</h1>
  <p>Wählen Sie ein Referenzprodukt und identifizieren Sie technisch ähnliche Alternativen mithilfe transparenter Filter, vergleichbarer Parameter und einer nachvollziehbaren Rangfolge.</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("Vergleichseinstellungen")
    workbook = st.text_input(
        "Hauptdatei (Excel)",
        str(MASTER_PATH),
        help="Excel-Datei mit dem normalisierten Hauptdatensatz.",
    )
    st.divider()
    st.subheader("Tragfähigkeitsanforderung")
    mode_label = st.radio(
        "Minimale Tragfähigkeitsstufe wählen",
        [
            "Entspannt — mindestens 80 % des Referenzwerts",
            "Streng — mindestens 100 % des Referenzwerts",
        ],
        help="Dies ist ein Pflichtfilter und vom endgültigen Ähnlichkeitswert getrennt.",
    )
    mode = "relaxed_80" if mode_label.startswith("Entspannt") else "strict"

    if mode == "relaxed_80":
        st.markdown("""
            <div class="relaxed-box">
              <strong>Entspannter Modus</strong><br>
              Ein Kandidat bleibt auswählbar, wenn jede geforderte Tragfähigkeit mindestens
              <strong>80 %</strong> des Referenzprodukts erreicht. Diese Einstellung erweitert die Suche,
              ein positives Ergebnis ist jedoch keine automatische Bestätigung der vollständigen Austauschbarkeit.
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown("""
            <div class="strict-box">
              <strong>Strenger Modus</strong><br>
              Ein Kandidat bleibt auswählbar, wenn jede geforderte Tragfähigkeit den Referenzwert
              zu <strong>100 %</strong> erreicht oder übertrifft.
            </div>""", unsafe_allow_html=True)

    st.divider()
    top_n = st.slider(
        "Maximale Anzahl von Ergebnissen", 1, 20, 5,
        help="Das System bewertet zunächst alle Kandidaten und zeigt dann bis zu dieser Anzahl der bestbewerteten Ergebnisse an.",
    )
    min_coverage = st.slider(
        "Minimale Datenabdeckung", 0.30, 1.00, 0.60, 0.05,
        help="Bei 60 % müssen mindestens 60 % der ausgewählten Parameter für beide Produkte verfügbar sein.",
    )
    st.divider()
    st.subheader("Maßliche Grenzen")

    b_rule_label = st.radio(
        "Vergleichsregel für B",
        [
            "Altsystemkompatibel — Kandidat B ≤ Referenz B + Toleranz",
            "Symmetrisch — absoluter B-Unterschied ≤ Toleranz",
        ],
        help=(
            "Die altsystemkompatible Regel reproduziert die nachvollziehbare Ball-Rail-Bedingung "
            "aus der geprüften ASP-Anwendung. Die symmetrische Regel ist eine optionale Prototypeinstellung."
        ),
    )
    b_rule = "legacy_max_plus" if b_rule_label.startswith("Altsystemkompatibel") else "symmetric"

    if b_rule == "legacy_max_plus":
        b_tol = st.number_input(
            "Maximale zusätzliche B-Länge (mm)", min_value=0.0, value=5.0, step=0.5,
            help="Der Kandidat darf kürzer sein, darf jedoch den Referenzwert um nicht mehr als den gewählten Wert überschreiten.",
        )
        st.caption("Angewandte Regel: Kandidat B ≤ Referenz B + Toleranz")
    else:
        b_tol = st.number_input(
            "Maximale absolute B-Differenz (mm)", min_value=0.0, value=15.0, step=0.5,
            help="Der Kandidat darf in beide Richtungen von der Referenz abweichen, innerhalb der gewählten Toleranz.",
        )
        st.caption("Angewandte Regel: |Kandidat B − Referenz B| ≤ Toleranz")

    h2_tol = st.number_input(
        "Maximale absolute H2-Differenz (mm)", min_value=0.0, value=5.0, step=0.5,
        help="Angewandte Regel: |Kandidat H2 − Referenz H2| ≤ Toleranz.",
    )

# Data loading
try:
    df = load_data(workbook)
except Exception as exc:
    st.error(f"Die Hauptdatei konnte nicht geladen werden: {exc}")
    st.stop()

companies = list_companies(df)
if not companies:
    st.error("In der Datei wurden keine Hersteller gefunden.")
    st.stop()

# Product selection
with st.container(border=True):
    st.markdown('<div class="section-title">Vergleich auswählen</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-subtitle">Wählen Sie das Referenzprodukt und den Herstellerbereich für die Suche.</div>', unsafe_allow_html=True)
    left, middle, right = st.columns([1, 1.35, 1])
    with left:
        st.markdown('<div class="reference-pill"><span class="reference-pill-number">1</span>Referenzhersteller</div>', unsafe_allow_html=True)
        default_source = next((i for i, c in enumerate(companies) if "BOSCH" in c.upper() or "REXROTH" in c.upper()), 0)
        source_company = st.selectbox("Referenzhersteller", companies, index=default_source, label_visibility="collapsed")
    with middle:
        st.markdown('<div class="reference-pill"><span class="reference-pill-number">2</span>Referenzprodukt</div>', unsafe_allow_html=True)
        models = list_models(df, source_company)
        source_model = st.selectbox("Referenzprodukt", models, label_visibility="collapsed")
    with right:
        st.markdown('<div class="reference-pill"><span class="reference-pill-number">3</span>Suchbereich</div>', unsafe_allow_html=True)
        targets = [c for c in companies if c != source_company]
        target_choice = st.selectbox("Suchbereich", ["Alle anderen Hersteller"] + targets, label_visibility="collapsed")

compare_all = target_choice == "Alle anderen Hersteller"
target_company = None if compare_all else target_choice

cfg = CompareConfig(
    mode=mode, top_n=top_n, compare_all=compare_all,
    b_rule=b_rule, b_tolerance_mm=float(b_tol),
    h2_tolerance_mm=float(h2_tol), min_coverage=float(min_coverage),
)

if st.button("Vergleichbare Produkte finden", type="primary", use_container_width=True):
    try:
        st.session_state["results"] = compare_master(df, source_company, source_model, target_company, cfg)
        st.session_state["source_label"] = f"{source_company} — {source_model}"
    except Exception as exc:
        st.error(str(exc))

# Results
results = st.session_state.get("results")
if results is not None:
    if results.empty:
        st.warning("Kein Produkt hat die Pflichtprüfungen und die Mindestanforderung an die Datenabdeckung erfüllt. Bitte passen Sie die Vergleichseinstellungen an und versuchen Sie es erneut.")
        st.warning("Hinweis: Die Pflichtprüfungen befinden sich in der 'Maßliche Grenzen'-Sektion. Die Datenabdeckung wird in der Seitenleiste unter 'Tragfähigkeitsanforderung' eingestellt.")
    else:
        st.markdown(
            f'<div class="result-card"><span class="small-note">Referenzprodukt</span><br><b>{st.session_state.get("source_label", "")}</b></div>',
            unsafe_allow_html=True,
        )
        best = results.iloc[0]
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Bestbewerteter Kandidat", str(best["Target_Model"]))
        m2.metric("Hersteller", str(best["Target_Company"]))
        m3.metric("Ähnlichkeit", f'{best["Similarity_Score"]*100:.1f}%')
        m4.metric("Datenabdeckung", f'{best["Data_Coverage"]*100:.1f}%')

        tab1, tab2, tab3, tab4 = st.tabs([
            "Rangliste der Ergebnisse",
            "Parametervergleich",
            "Ergebnisse verstehen",
            "Mathematische Zusammenhänge",
        ])

        with tab1:
            st.markdown('<div class="section-title">Rangliste der Kandidatenprodukte</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-subtitle">Kandidaten werden nach Ähnlichkeit geordnet, nachdem die obligatorischen technischen Prüfungen angewendet wurden.</div>', unsafe_allow_html=True)
            b_rule_summary = (
                f"B ≤ Referenz B + {b_tol:.1f} mm" if b_rule == "legacy_max_plus"
                else f"|B Kandidat − B Referenz| ≤ {b_tol:.1f} mm"
            )
            st.caption(f"Angewandte Einstellungen: {b_rule_summary}; |H2 Kandidat − H2 Referenz| ≤ {h2_tol:.1f} mm; Mindestdatenabdeckung {min_coverage * 100:.0f} %.")
            shown = results.copy()
            shown.insert(0, "Rang", range(1, len(shown) + 1))
            for col in ["Similarity_Score", "Data_Coverage", "C_Ratio", "C0_Ratio", "Dimensions_Score", "Capacity_Score"]:
                if col in shown:
                    shown[col] = shown[col].map(lambda x: "—" if pd.isna(x) else f"{x*100:.1f}%")
            ranked_view = shown[["Rang", "Target_Company", "Target_Model", "Similarity_Score", "Data_Coverage", "C_Ratio", "C0_Ratio"]].rename(columns={
                "Target_Company": "Hersteller", "Target_Model": "Kandidatenprodukt",
                "Similarity_Score": "Ähnlichkeit", "Data_Coverage": "Datenabdeckung",
                "C_Ratio": "C-Verhältnis", "C0_Ratio": "C0-Verhältnis",
            })
            st.markdown(compact_table(ranked_view), unsafe_allow_html=True)
            st.caption(f"Die Anwendung bewertet alle infrage kommenden Kandidaten und zeigt bis zu {top_n} Produkte mit den höchsten Ähnlichkeitswerten an.")

        with tab2:
            st.markdown('<div class="section-title">Technischer Parametervergleich</div>', unsafe_allow_html=True)
            # st.image(
            #     APP_DIR / "boschsymbol.png",
            #     caption="Parameterbezeichnungen gemäß Bosch Rexroth AG",
            #     width= 550
            # )
            # st.markdown('</div>', unsafe_allow_html=True)
            # col1, col2, col3 = st.columns([1,2,1])

            # with col2:
            #     st.image(
            #         APP_DIR / "boschsymbol.png",
            #         caption="Parameterbezeichnungen gemäß Bosch Rexroth AG",
            #         width=550
            #     )
            col1, col2 = st.columns([1.2, 1])

            with col1:
                st.image(
                    APP_DIR / "boschsymbol.png",
                    caption="Parameterbezeichnungen gemäß Bosch Rexroth AG",
                    width=650
                )

            with col2:
                st.markdown("""

                | Parameter | Beschreibung |
                |-----------|-------------|
                | A | Wagenbreite |
                | A2 | Schienenbreite |
                | B | Gesamtlänge des Führungswagens |
                | H | Gesamthöhe des Führungswagens |
                | H2 | Schienenhöhe |
                | E1 | Mittenabstand der Befestigungsbohrungen (quer) |
                | E2 | Mittenabstand der Befestigungsbohrungen (längs) |
                | C | Dynamische Tragzahl (N) |
                | C0 | Statische Tragzahl (N) |
                | Mt | Dynamische Torsionstragmoment (Nm) |
                | Mt0 | Statische Torsionstragmoment (Nm) |
                | ML | Dynamische Längstragmoment (Nm) |
                | ML0 | Statische Längstragmoment (Nm) |
                            
                """)
            st.markdown("<br>", unsafe_allow_html=True) 
            st.markdown('<div class="section-subtitle">Überprüfen Sie Referenz- und Kandidatenwerte direkt. Differenzen werden als Kandidatenwert minus Referenzwert berechnet.</div>', unsafe_allow_html=True)
            labels = [f'#{i+1} — {r.Target_Company} — {r.Target_Model}' for i, r in results.iterrows()]
            chosen_index = st.selectbox("Zu prüfender Kandidat", range(len(labels)), format_func=lambda i: labels[i])
            row = results.iloc[chosen_index]
            reference_header = f"{source_company} — {source_model}"
            candidate_header = f"{row.get('Target_Company')} — {row.get('Target_Model')}"
            detail = []
            for p in TECH_PARAMS:
                src_val = row.get(f"Source_{p}")
                tgt_val = row.get(f"Target_{p}")
                delta = tgt_val - src_val if pd.notna(src_val) and pd.notna(tgt_val) else np.nan
                detail.append({"Parameter": p, reference_header: src_val, candidate_header: tgt_val, "Differenz": delta})
            st.markdown(compact_table(pd.DataFrame(detail)), unsafe_allow_html=True)
            st.markdown("#### Obligatorische technische Prüfungen")
            st.markdown(vertical_checks(row.get("Mandatory_Checks", "Keine Details verfügbar")), unsafe_allow_html=True)
            st.markdown("#### Parameter ohne direkten Vergleich")
            st.markdown(vertical_missing(row.get("Missing_Comparisons", "None")), unsafe_allow_html=True)

        with tab3:
            st.markdown('<div class="section-title">Ergebnisse verstehen</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-subtitle">Die folgenden Kennzahlen beschreiben verschiedene Aspekte des Vergleichs. Sie sollten gemeinsam betrachtet werden.</div>', unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("""
                <div class="definition-card">
                  <div class="definition-heading"><div class="definition-number">01</div><div class="definition-title">Ähnlichkeitswert</div></div>
                  <div class="definition-text">Der Ähnlichkeitswert zeigt, <strong>wie genau die verfügbaren technischen Werte eines Kandidaten mit dem Referenzprodukt übereinstimmen</strong>. Er kombiniert die verfügbaren Maß- und Tragfähigkeitsvergleiche zu einem einzigen Rankingwert.</div>
                  <div class="definition-formula"><span class="definition-formula-label">Formel</span>Ähnlichkeit = 0,55 × Maßwert + 0,45 × Tragfähigkeitswert</div>
                </div>""", unsafe_allow_html=True)
            with c2:
                st.markdown("""
                <div class="definition-card">
                  <div class="definition-heading"><div class="definition-number">02</div><div class="definition-title">Datenabdeckung</div></div>
                  <div class="definition-text">Die Datenabdeckung zeigt, <strong>wie viele Informationen für den Vergleich tatsächlich verfügbar waren</strong>. Es handelt sich um den Anteil der Parameter, für die bei beiden Produkten Werte vorliegen.</div>
                  <div class="definition-formula"><span class="definition-formula-label">Formel</span>Abdeckung = Vergleichbare Parameter ÷ Ausgewählte Parameter × 100 %</div>
                </div>""", unsafe_allow_html=True)
            st.markdown("""
            <div class="callout"><strong>Warum beide Werte wichtig sind</strong><br><br>
              Ein Kandidat kann einen hohen Ähnlichkeitswert, aber eine geringe Datenabdeckung aufweisen.
              Ein gut abgesichertes Ergebnis kombiniert daher <strong>hohe Ähnlichkeit</strong> mit <strong>hoher Datenabdeckung</strong>.
            </div>""", unsafe_allow_html=True)
            c3, c4 = st.columns(2)
            with c3:
                st.markdown("""
                <div class="definition-card">
                  <div class="definition-heading"><div class="definition-number">03</div><div class="definition-title">Tragfähigkeitsverhältnis</div></div>
                  <div class="definition-text">Das Tragfähigkeitsverhältnis vergleicht den Kandidatenwert mit dem Referenzwert. 100 % = gleiche Tragfähigkeit, 90 % = Kandidat erreicht 90 % des Referenzwerts, 110 % = Kandidat übertrifft Referenz um 10 %.</div>
                  <div class="definition-formula"><span class="definition-formula-label">Formel</span>Verhältnis = Kandidatentragfähigkeit ÷ Referenztragfähigkeit × 100 %</div>
                </div>""", unsafe_allow_html=True)
            with c4:
                st.markdown("""
                <div class="definition-card">
                  <div class="definition-heading"><div class="definition-number">04</div><div class="definition-title">Top-Ergebnisse</div></div>
                  <div class="definition-text">Die Einstellung steuert ausschließlich die Anzahl der angezeigten Kandidaten. Alle infrage kommenden Kandidaten werden zunächst bewertet und anschließend nach Ähnlichkeit sortiert.</div>
                  <div class="definition-formula"><span class="definition-formula-label">Beziehung</span>Angezeigte Ergebnisse = Erste N Kandidaten nach Sortierung</div>
                </div>""", unsafe_allow_html=True)
            st.markdown("### Tragfähigkeitsmodi")
            st.markdown("""
            <div class="relaxed-box"><strong>Entspannter Modus — Mindestverhältnis 80 %</strong><br><br>
              Ein Kandidat besteht den Filter, wenn jede Tragfähigkeit mindestens 80 % des Referenzwerts erreicht. Verhältnis 90 % → besteht; 70 % → besteht nicht.
            </div>
            <div class="strict-box"><strong>Strenger Modus — Mindestverhältnis 100 %</strong><br><br>
              Ein Kandidat besteht den Filter nur, wenn jede Tragfähigkeit den Referenzwert erreicht oder übertrifft. Verhältnis 110 % → besteht; 90 % → besteht nicht.
            </div>""", unsafe_allow_html=True)
            st.markdown("### Praxisbeispiel zur Ergebnisinterpretation")
            st.markdown("""
| Angezeigtes Ergebnis | Fachliche Interpretation |
|---|---|
| **Ähnlichkeit: 89 %** | Die verfügbaren Werte stimmen nach der gewählten Berechnungsmethode eng mit dem Referenzprodukt überein. |
| **Datenabdeckung: 85 %** | 85 % der Vergleichsparameter lagen für beide Produkte vor. |
| **C-Verhältnis: 105 %** | Die dynamische Tragzahl des Kandidaten liegt 5 % über dem Referenzwert. |
| **C0-Verhältnis: 92 %** | Die statische Tragzahl des Kandidaten erreicht 92 % des Referenzwerts. |
| **Rang 1** | Dieser Kandidat erhielt den höchsten Ähnlichkeitswert unter allen Produkten, die die Pflichtprüfungen bestanden haben. |
""")
            st.warning("Die Rangliste ist ein Entscheidungsunterstützungsergebnis auf Basis der ausgewählten Daten und Regeln. Ein hoher Wert bestätigt allein keine vollständige physische Austauschbarkeit oder Eignung für eine bestimmte Anwendung.")

        with tab4:
            st.markdown('<div class="section-title">Mathematische Zusammenhänge im Vergleich</div>', unsafe_allow_html=True)
            st.markdown('<div class="section-subtitle">Jeder Zusammenhang beantwortet eine andere Frage. Die Formeln werden mit einer verständlichen Erklärung und einem kurzen Beispiel gezeigt.</div>', unsafe_allow_html=True)
            st.markdown("""
            <div class="math-intro">
              Die Berechnung erfolgt in zwei Stufen. Zunächst entscheiden Pflichtanforderungen, ob ein Kandidat zugelassen wird.
              Anschließend erhalten die zugelassenen Kandidaten Ähnlichkeitswerte und werden eingestuft.
              Fehlende Werte werden nicht als perfekte Übereinstimmung behandelt; die Datenabdeckung wird gesondert ausgewiesen.
            </div>""", unsafe_allow_html=True)
            if b_rule == "legacy_max_plus":
                b_formula = "B Kandidat ≤ B Referenz + Toleranz"
                b_description = "Altsystemkompatible einseitige Regel: Ein Kandidat darf kürzer sein, darf jedoch die Referenzlänge nur um die gewählte Toleranz überschreiten."
            else:
                b_formula = "|B Kandidat − B Referenz| ≤ Toleranz"
                b_description = "Symmetrische Prototypregel: Ein Kandidat darf in beide Richtungen innerhalb der gewählten Toleranz von der Referenz abweichen."
            st.markdown(f"""
                <div class="math-bubble">
                  <div class="math-chip">Pflicht-B-Regel</div>
                  <div class="math-title">Angewandte Prüfung der Laufwagenlänge</div>
                  <div class="math-text">{html.escape(b_description)}</div>
                  <div class="math-formula">{html.escape(b_formula)}</div>
                  <div class="math-example">Aktuelle Toleranz: {b_tol:.1f} mm</div>
                </div>""", unsafe_allow_html=True)
            a, b = st.columns(2)
            with a:
                st.markdown("""<div class="math-bubble"><div class="math-chip">Zusammenhang 01</div><div class="math-title">Absoluter Unterschied</div><div class="math-text">Misst den numerischen Abstand zwischen Kandidaten- und Referenzwert. Das Vorzeichen wird ignoriert.</div><div class="math-formula">| Kandidat − Referenz |</div><div class="math-example">Beispiel: |72 mm − 70 mm| = 2 mm</div></div>""", unsafe_allow_html=True)
            with b:
                st.markdown("""<div class="math-bubble"><div class="math-chip">Zusammenhang 02</div><div class="math-title">Prozentualer Unterschied</div><div class="math-text">Drückt den Unterschied relativ zum Referenzwert aus, um Werte unterschiedlicher Größenordnung vergleichbar zu machen.</div><div class="math-formula">((Kandidat − Referenz) ÷ Referenz) × 100 %</div><div class="math-example">Beispiel: ((72 − 70) ÷ 70) × 100 % = +2,86 %</div></div>""", unsafe_allow_html=True)
            c, d = st.columns(2)
            with c:
                st.markdown("""<div class="math-bubble"><div class="math-chip">Zusammenhang 03</div><div class="math-title">Tragfähigkeitsverhältnis</div><div class="math-text">Zeigt, welcher Anteil der Referenztragfähigkeit vom Kandidaten bereitgestellt wird. Wird auch von den 80-%- und 100-%-Pflichtfiltern verwendet.</div><div class="math-formula">Kandidatentragfähigkeit ÷ Referenztragfähigkeit</div><div class="math-example">Beispiel: 18.000 N ÷ 20.000 N = 0,90 = 90 %</div></div>""", unsafe_allow_html=True)
            with d:
                st.markdown("""<div class="math-bubble"><div class="math-chip">Zusammenhang 04</div><div class="math-title">Maßähnlichkeit</div><div class="math-text">Weist Maßen, die nah beieinanderliegen, einen hohen Wert zu. Der Wert nimmt gemäß konfigurierbarer Prototypskalierung gleichmäßig ab.</div><div class="math-formula">e^(− |Kandidat − Referenz| ÷ Toleranzskalierung)</div><div class="math-example">Gleiche Werte ergeben 100 %; größere Unterschiede ergeben niedrigere Werte.</div></div>""", unsafe_allow_html=True)
            e1, f = st.columns(2)
            with e1:
                st.markdown("""<div class="math-bubble"><div class="math-chip">Zusammenhang 05</div><div class="math-title">Tragfähigkeitsähnlichkeit</div><div class="math-text">Belohnt einen Kandidaten, der die Referenztragfähigkeit erreicht. Gleiche oder höhere Tragfähigkeit erhält den Maximalwert 100 %.</div><div class="math-formula">min(100 %, Kandidat ÷ Referenz)</div><div class="math-example">90 % ergibt 90 %; 120 % wird auf 100 % begrenzt.</div></div>""", unsafe_allow_html=True)
            with f:
                st.markdown("""<div class="math-bubble"><div class="math-chip">Zusammenhang 06</div><div class="math-title">Gruppendurchschnitt</div><div class="math-text">Kombiniert die gültigen Parameterwerte innerhalb einer Gruppe, z. B. Maße oder Tragfähigkeiten.</div><div class="math-formula">Summe der gültigen Werte ÷ Anzahl der gültigen Werte</div><div class="math-example">Beispiel: (90 % + 80 % + 70 %) ÷ 3 = 80 %</div></div>""", unsafe_allow_html=True)
            g, h = st.columns(2)
            with g:
                st.markdown("""<div class="math-bubble"><div class="math-chip">Zusammenhang 07</div><div class="math-title">Gewichtete Ähnlichkeit</div><div class="math-text">Kombiniert Maß- und Tragfähigkeitsgruppen. Die 55/45-Gewichtung ist eine konfigurierbare Prototypeinstellung und wurde nicht aus dem alten ASP-Tool übernommen.</div><div class="math-formula">0,55 × Maße + 0,45 × Tragfähigkeiten</div><div class="math-example">Beispiel: 0,55 × 90 % + 0,45 × 80 % = 85,5 %</div></div>""", unsafe_allow_html=True)
            with h:
                st.markdown("""<div class="math-bubble"><div class="math-chip">Zusammenhang 08</div><div class="math-title">Datenabdeckung</div><div class="math-text">Zeigt den Anteil der Parameter, für die bei beiden Produkten Werte vorliegen. Abdeckung beschreibt Vollständigkeit, nicht Nähe.</div><div class="math-formula">Vergleichbare Parameter ÷ Ausgewählte Parameter</div><div class="math-example">Beispiel: 8 vergleichbare Felder ÷ 13 ausgewählte Felder = 61,5 %</div></div>""", unsafe_allow_html=True)
            st.markdown("""
            <div class="callout"><strong>Empfohlene Interpretation</strong><br><br>
              Verwenden Sie die Pflichtprüfungen zur Beurteilung der Zulässigkeit, den Ähnlichkeitswert zur Beurteilung der Nähe
              und die Datenabdeckung zur Beurteilung, wie gut der Vergleich durch verfügbare Informationen gestützt wird.
            </div>""", unsafe_allow_html=True)
