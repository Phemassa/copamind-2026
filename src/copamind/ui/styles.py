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
  background: linear-gradient(180deg,#06100f 0%,#07100f 44%,#091312 100%) !important;
  font-family: Inter, system-ui, sans-serif;
  color: var(--text) !important;
}

[data-testid="stAppViewContainer"] > .main .block-container {
  max-width: 1320px;
  padding-top: 2.25rem;
}

/* sidebar */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg,#0b1716,#091312) !important;
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
  border-radius: 8px;
  padding: 14px !important;
}
[data-testid="stMetricValue"] { color: var(--text) !important; font-weight:700; }
[data-testid="stMetricLabel"] { color: var(--muted) !important; font-size:11px; }

/* dataframes */
[data-testid="stDataFrame"] { border: 1px solid var(--line) !important; border-radius:8px; }

/* buttons */
[data-testid="stButton"] > button {
  background: linear-gradient(135deg,var(--accent),#29b892) !important;
  color: #061110 !important; font-weight:800; border:none !important;
  border-radius:8px !important;
}
[data-testid="stButton"] > button:hover {
  opacity:.88; transform:translateY(-1px);
}

/* expanders */
[data-testid="stExpander"] {
  border: 1px solid var(--line) !important;
  border-radius:8px !important; background: rgba(16,26,26,.7) !important;
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

.cm-hero {
  border: 1px solid rgba(82,227,181,.22);
  border-top: 3px solid var(--accent);
  border-radius: 8px;
  background: linear-gradient(135deg,rgba(12,25,24,.94),rgba(10,17,23,.9));
  padding: 22px 24px;
  margin: 0 0 18px;
}
.cm-hero h1 {
  color: var(--text);
  font-size: 34px;
  line-height: 1.12;
  margin: 0 0 8px;
  letter-spacing: 0;
}
.cm-hero p {
  color: var(--muted);
  font-size: 15px;
  max-width: 760px;
  margin: 0;
}
.cm-kicker {
  color: var(--accent);
  font-size: 11px;
  font-weight: 900;
  letter-spacing: .16em;
  margin-bottom: 8px;
  text-transform: uppercase;
}
.cm-stat {
  min-height: 112px;
  background: rgba(16,26,26,.88);
  border: 1px solid var(--line);
  border-top: 3px solid var(--accent);
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 12px;
}
.cm-stat span,
.cm-stat small {
  display: block;
  color: var(--muted);
  font-size: 12px;
}
.cm-stat strong {
  display: block;
  color: var(--text);
  font-size: 30px;
  line-height: 1.15;
  margin: 8px 0 4px;
}
.cm-panel,
.cm-row,
.cm-rank {
  background: rgba(16,26,26,.82);
  border: 1px solid var(--line);
  border-radius: 8px;
}
.cm-row,
.cm-rank {
  display: grid;
  gap: 10px;
  align-items: center;
  margin-bottom: 8px;
  padding: 11px 12px;
}
.cm-row {
  grid-template-columns: minmax(90px,.42fr) 1fr;
}
.cm-row b,
.cm-rank b {
  color: var(--accent);
}
.cm-row span,
.cm-rank span {
  color: var(--text);
  min-width: 0;
}
.cm-rank {
  grid-template-columns: 46px 1fr auto;
}
.cm-rank strong {
  color: var(--gold);
  white-space: nowrap;
}
.cm-flow {
  display: grid;
  grid-template-columns: repeat(2,minmax(0,1fr));
  gap: 10px;
  padding: 12px;
}
.cm-flow div {
  background: rgba(255,255,255,.035);
  border-radius: 8px;
  padding: 12px;
}
.cm-flow b,
.cm-flow span {
  display: block;
}
.cm-flow b {
  color: var(--text);
  margin-bottom: 4px;
}
.cm-flow span {
  color: var(--muted);
  font-size: 12px;
}
.cm-podium {
  min-height: 168px;
  background: rgba(16,26,26,.9);
  border: 1px solid var(--line);
  border-top: 4px solid var(--accent);
  border-radius: 8px;
  padding: 18px;
  margin-bottom: 12px;
  text-align: center;
}
.cm-podium span,
.cm-podium small {
  color: var(--muted);
  display: block;
}
.cm-podium b {
  color: var(--text);
  display: block;
  font-size: 13px;
  margin: 8px 0;
  min-height: 34px;
}
.cm-podium strong {
  color: var(--gold);
  display: block;
  font-size: 42px;
  line-height: 1;
}
.cm-versus {
  align-items: center;
  background: rgba(255,255,255,.035);
  border: 1px solid var(--line);
  border-radius: 8px;
  color: var(--muted);
  display: grid;
  gap: 4px;
  justify-items: center;
  min-height: 104px;
  padding: 12px;
  text-align: center;
}
.cm-versus b {
  color: var(--text);
  display: block;
  font-size: 13px;
}
.cm-versus span {
  color: var(--accent);
  font-size: 18px;
  font-weight: 900;
  text-transform: uppercase;
}

@media (max-width: 760px) {
  [data-testid="stAppViewContainer"] > .main .block-container {
    padding: 1rem;
  }
  .cm-hero {
    padding: 18px;
  }
  .cm-hero h1 {
    font-size: 28px;
  }
  .cm-row,
  .cm-rank,
  .cm-flow {
    grid-template-columns: 1fr;
  }
}
</style>
"""


def inject_css() -> None:
    import streamlit as st

    st.markdown(CSS, unsafe_allow_html=True)
