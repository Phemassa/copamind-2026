"""CSS global injetado no Streamlit para corresponder ao estilo CopaMind."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');

/* ── root ───────────────────────────────────────────────────────── */
:root {
  --bg:#07100f; --panel:#101a1a; --panel-2:#172525;
  --line:#29403f; --text:#f2faf8; --muted:#9eb5b1;
  --accent:#52e3b5; --accent-2:#8df0d1;
  --gold:#f6c453; --silver:#c7d4d2; --bronze:#d89567;
  --blue:#4895ff; --red:#ff8c72; --purple:#8e7cff;
}

html,body,[data-testid="stApp"] {
  background: radial-gradient(circle at 10% -8%,rgba(82,227,181,.18),transparent 32rem),
              radial-gradient(circle at 98% 6%,rgba(72,149,255,.12),transparent 36rem),
              linear-gradient(180deg,#06100f 0%,#07100f 100%) !important;
  font-family: Inter, system-ui, sans-serif;
  color: var(--text) !important;
}

/* sidebar */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg,#0c1a19,#091413) !important;
  border-right: 1px solid var(--line) !important;
}
[data-testid="stSidebar"] [data-testid="stRadio"] label {
  color: var(--muted) !important;
  font-size: 13px;
}
[data-testid="stSidebar"] [data-testid="stRadio"] input:checked + div span {
  color: var(--accent) !important;
}

/* metrics */
[data-testid="stMetric"] {
  background: rgba(16,26,26,.82);
  border: 1px solid var(--line);
  border-radius: 12px;
  padding: 14px !important;
}
[data-testid="stMetricValue"] { color: var(--text) !important; font-weight:700; }
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size:11px; }

/* dataframes */
[data-testid="stDataFrame"] { border: 1px solid var(--line) !important; border-radius:12px; }

/* buttons */
[data-testid="stButton"] > button {
  background: linear-gradient(135deg,var(--accent),#29b892) !important;
  color: #061110 !important; font-weight:800; border:none !important;
  border-radius:10px !important;
}
[data-testid="stButton"] > button:hover {
  opacity:.88; transform:translateY(-1px);
}

/* expanders */
[data-testid="stExpander"] {
  border: 1px solid var(--line) !important;
  border-radius:12px !important; background: rgba(16,26,26,.7) !important;
}

/* text inputs */
[data-testid="stTextInput"] input, [data-testid="stNumberInput"] input {
  background: var(--panel-2) !important; color: var(--text) !important;
  border: 1px solid var(--line) !important; border-radius:8px !important;
}

/* tabs */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
  background: transparent !important;
  border-bottom: 1px solid var(--line) !important;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
  color: var(--muted) !important; font-weight:600;
}
[data-testid="stTabs"] [aria-selected="true"] {
  color: var(--accent) !important;
  border-bottom: 2px solid var(--accent) !important;
}

/* divider */
hr { border-color: var(--line) !important; }

/* image */
img { border-radius:8px; }

/* eyebrow helper */
.eyebrow {
  font-size:11px; font-weight:900; letter-spacing:.2em;
  text-transform:uppercase; color:var(--accent); margin-bottom:6px;
}
</style>
"""


def inject_css() -> None:
    import streamlit as st
    st.markdown(CSS, unsafe_allow_html=True)
