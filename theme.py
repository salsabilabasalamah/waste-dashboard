"""Editorial Terroir theme — colours, Plotly template, and global CSS."""
from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio


# ─────────────────── Palette ───────────────────
INK        = "#1A1F1B"   # primary text
INK_SOFT   = "#3D4A3F"
PARCHMENT  = "#FBF8F2"   # background
CREAM      = "#F4EFE3"   # secondary background / cards
BORDER     = "#E2DCC9"
RULE       = "#CFC6AE"

FOREST     = "#2C5530"   # primary brand
FOREST_DK  = "#1A3520"
MOSS       = "#7C9070"

BIOCHAR    = "#C2410C"   # accent
AMBER      = "#E0A458"
CLAY       = "#A0522D"

OK_GREEN   = "#3E7C5C"
WARN_AMBER = "#D97706"
DANGER     = "#A03A3A"

MUTED      = "#6B7B6E"

# Categorical sequence for charts (tuned for cream background)
CATEGORICAL = [
    "#2C5530", "#C2410C", "#7C9070", "#E0A458",
    "#1A3520", "#A0522D", "#3E7C5C", "#D97706",
]
SEQUENTIAL_GREEN = [
    "#F4EFE3", "#D4DDC2", "#A8B8A0", "#7C9070",
    "#557056", "#2C5530", "#1A3520",
]


# ─────────────────── Plotly template ───────────────────
def install_plotly_template() -> None:
    """Register and activate the SB-Geocarbon editorial template."""
    template = go.layout.Template()
    template.layout = go.Layout(
        font=dict(family="DM Sans, system-ui, sans-serif",
                  color=INK, size=13),
        title=dict(font=dict(family="Fraunces, Georgia, serif",
                             size=18, color=INK),
                   x=0.0, xanchor="left", pad=dict(t=8, l=0)),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        colorway=CATEGORICAL,
        margin=dict(l=12, r=12, t=44, b=12),
        xaxis=dict(
            showgrid=False, showline=True, linecolor=BORDER,
            ticks="outside", tickcolor=BORDER, ticklen=4,
            tickfont=dict(size=11, color=INK_SOFT),
            title=dict(font=dict(size=12, color=INK_SOFT)),
        ),
        yaxis=dict(
            showgrid=True, gridcolor=BORDER, gridwidth=1,
            zeroline=False, showline=False,
            tickfont=dict(size=11, color=INK_SOFT),
            title=dict(font=dict(size=12, color=INK_SOFT)),
        ),
        legend=dict(
            bgcolor="rgba(255,255,255,0.6)", bordercolor=BORDER,
            borderwidth=1, font=dict(size=11, color=INK_SOFT),
            orientation="h", yanchor="bottom", y=1.02, x=0,
        ),
        hoverlabel=dict(
            bgcolor=INK, font=dict(color=PARCHMENT,
                                   family="DM Sans, sans-serif", size=12),
            bordercolor=INK,
        ),
    )
    pio.templates["SB-Geocarbon"] = template
    pio.templates.default = "SB-Geocarbon"


# ─────────────────── Global CSS ───────────────────
GLOBAL_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,300;9..144,400;9..144,500;9..144,600;9..144,700&family=DM+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

:root {
    --ink:        #1A1F1B;
    --ink-soft:   #3D4A3F;
    --parchment:  #FBF8F2;
    --cream:      #F4EFE3;
    --border:     #E2DCC9;
    --rule:       #CFC6AE;
    --forest:     #2C5530;
    --forest-dk:  #1A3520;
    --moss:       #7C9070;
    --biochar:    #C2410C;
    --amber:      #E0A458;
    --ok:         #3E7C5C;
    --warn:       #D97706;
    --danger:     #A03A3A;
    --muted:      #6B7B6E;
}

html, body, [class*="css"] {
    font-family: 'DM Sans', system-ui, sans-serif !important;
    color: var(--ink);
}
.stApp { background: var(--parchment); }

/* ─── Header band ─── */
.brand-band {
    margin: -2.0rem -2rem 1.4rem -2rem;
    padding: 1.6rem 2.2rem 1.4rem 2.2rem;
    background: linear-gradient(135deg, #1A3520 0%, #2C5530 55%, #3a6b3d 100%);
    color: #F4EFE3;
    border-bottom: 4px solid var(--biochar);
    position: relative;
    overflow: hidden;
}
.brand-band::after {
    content: "";
    position: absolute; inset: 0;
    background:
      radial-gradient(circle at 88% -10%, rgba(224,164,88,0.28), transparent 45%),
      radial-gradient(circle at -5% 110%, rgba(124,144,112,0.25), transparent 50%);
    pointer-events: none;
}
.brand-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem; letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--amber);
    margin-bottom: 0.35rem;
    position: relative; z-index: 1;
}
.brand-title {
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 500; font-size: 2.4rem; line-height: 1.05;
    letter-spacing: -0.02em;
    margin: 0; color: #FBF8F2;
    position: relative; z-index: 1;
}
.brand-title em {
    font-style: italic; font-weight: 400; color: var(--amber);
}
.brand-sub {
    font-size: 0.95rem; color: rgba(244,239,227,0.78);
    margin-top: 0.5rem; max-width: 64ch;
    position: relative; z-index: 1;
}
.brand-meta {
    display: flex; gap: 1.5rem; flex-wrap: wrap;
    margin-top: 0.95rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem; letter-spacing: 0.08em;
    color: rgba(244,239,227,0.72);
    position: relative; z-index: 1;
}
.brand-meta b { color: var(--amber); font-weight: 500; }
.brand-meta .dot {
    display: inline-block; width: 6px; height: 6px;
    border-radius: 50%; background: var(--amber);
    margin-right: 0.45rem; vertical-align: middle;
    box-shadow: 0 0 0 3px rgba(224,164,88,0.18);
}

/* ─── Section heading ─── */
.section-h {
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 500; font-size: 1.55rem;
    color: var(--ink); letter-spacing: -0.01em;
    margin: 1.4rem 0 0.2rem 0;
}
.section-h em { font-style: italic; color: var(--forest); font-weight: 400; }
.section-rule {
    height: 1px; background: var(--rule);
    margin: 0.5rem 0 1.1rem 0;
    background-image: linear-gradient(90deg, var(--rule) 0%, var(--rule) 70%, transparent 100%);
}
.section-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; letter-spacing: 0.22em;
    text-transform: uppercase;
    color: var(--biochar);
    margin-bottom: 0.2rem;
}

/* ─── KPI cards ─── */
.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 0.85rem;
    margin: 0.4rem 0 1.4rem 0;
}
.kpi {
    background: #FFFCF5;
    border: 1px solid var(--border);
    border-left: 3px solid var(--forest);
    padding: 1rem 1.15rem 0.95rem 1.15rem;
    position: relative;
    transition: transform 0.18s ease, box-shadow 0.18s ease;
}
.kpi:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 18px -10px rgba(26,53,32,0.25);
}
.kpi.accent      { border-left-color: var(--biochar); }
.kpi.amber       { border-left-color: var(--amber); }
.kpi.moss        { border-left-color: var(--moss); }
.kpi.danger      { border-left-color: var(--danger); }
.kpi-label {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.66rem; letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--muted);
    margin-bottom: 0.4rem;
}
.kpi-value {
    font-family: 'Fraunces', Georgia, serif;
    font-weight: 500;
    font-size: 1.85rem; line-height: 1.05;
    color: var(--ink); letter-spacing: -0.01em;
}
.kpi-value .unit {
    font-family: 'DM Sans', sans-serif;
    font-weight: 400; font-size: 0.85rem;
    color: var(--muted); margin-left: 0.25rem;
    letter-spacing: 0;
}
.kpi-foot {
    font-size: 0.76rem; color: var(--ink-soft);
    margin-top: 0.4rem;
}
.kpi-foot.ok      { color: var(--ok); }
.kpi-foot.warn    { color: var(--warn); }
.kpi-foot.danger  { color: var(--danger); }

/* ─── Insight callout ─── */
.callout {
    background: #FFFCF5;
    border: 1px solid var(--border);
    border-left: 3px solid var(--biochar);
    padding: 1rem 1.2rem;
    font-family: 'Fraunces', Georgia, serif;
    font-style: italic; font-size: 1.02rem; font-weight: 400;
    color: var(--ink); line-height: 1.55;
    margin: 0.4rem 0 1.4rem 0;
}
.callout::before {
    content: "—"; color: var(--biochar);
    margin-right: 0.6rem; font-style: normal;
}

/* ─── Severity pills ─── */
.pill {
    display: inline-block;
    padding: 0.18rem 0.65rem;
    border-radius: 999px;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.66rem; letter-spacing: 0.12em;
    font-weight: 500;
    border: 1px solid;
}
.pill.high   { color: var(--danger); border-color: var(--danger);
               background: rgba(160,58,58,0.08); }
.pill.medium { color: var(--warn); border-color: var(--warn);
               background: rgba(217,119,6,0.08); }
.pill.low    { color: var(--ok); border-color: var(--ok);
               background: rgba(62,124,92,0.08); }

/* ─── Sidebar ─── */
section[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #1A3520 0%, #2C5530 100%);
    border-right: 1px solid #0e2a17;
}
section[data-testid="stSidebar"] {
    color: #F4EFE3;
    font-family: 'DM Sans', sans-serif;
}
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div,
section[data-testid="stSidebar"] li,
section[data-testid="stSidebar"] small,
section[data-testid="stSidebar"] hr {
    color: #F4EFE3;
}
section[data-testid="stSidebar"] hr {
    border-color: rgba(244,239,227,0.18) !important;
}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3 {
    font-family: 'Fraunces', Georgia, serif !important;
    color: #FBF8F2 !important; font-weight: 500;
}
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] label p {
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important; letter-spacing: 0.16em !important;
    text-transform: uppercase !important;
    color: var(--amber) !important;
}

/* ─── Sidebar inputs (text / date / multiselect / select) ─── */
section[data-testid="stSidebar"] input,
section[data-testid="stSidebar"] textarea {
    color: #FBF8F2 !important;
    background-color: rgba(0,0,0,0.22) !important;
    border-color: rgba(224,164,88,0.35) !important;
    caret-color: var(--amber) !important;
}
section[data-testid="stSidebar"] input::placeholder {
    color: rgba(244,239,227,0.45) !important;
}

/* baseweb input/select wrappers */
section[data-testid="stSidebar"] [data-baseweb="input"],
section[data-testid="stSidebar"] [data-baseweb="select"] > div,
section[data-testid="stSidebar"] [data-baseweb="select"] [data-baseweb="select-control"] {
    background-color: rgba(0,0,0,0.22) !important;
    border-color: rgba(224,164,88,0.35) !important;
    color: #FBF8F2 !important;
}
section[data-testid="stSidebar"] [data-baseweb="select"] *,
section[data-testid="stSidebar"] [data-baseweb="input"] * {
    color: #FBF8F2 !important;
}

/* multiselect tags */
section[data-testid="stSidebar"] [data-baseweb="tag"] {
    background-color: rgba(224,164,88,0.22) !important;
    border: 1px solid rgba(224,164,88,0.55) !important;
}
section[data-testid="stSidebar"] [data-baseweb="tag"] span,
section[data-testid="stSidebar"] [data-baseweb="tag"] div {
    color: #FBF8F2 !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 0.78rem !important;
    letter-spacing: 0 !important;
    text-transform: none !important;
}
section[data-testid="stSidebar"] [data-baseweb="tag"] svg {
    fill: #FBF8F2 !important;
    color: #FBF8F2 !important;
}

/* date input cells */
section[data-testid="stSidebar"] [data-testid="stDateInput"] input {
    color: #FBF8F2 !important;
    background-color: rgba(0,0,0,0.22) !important;
}

/* sidebar buttons override (less stark contrast) */
section[data-testid="stSidebar"] .stButton > button {
    background: rgba(224,164,88,0.14) !important;
    color: #FBF8F2 !important;
    border: 1px solid rgba(224,164,88,0.55) !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: var(--amber) !important;
    color: var(--forest-dk) !important;
    border-color: var(--amber) !important;
}

/* tooltip "?" icon */
section[data-testid="stSidebar"] [data-testid="stTooltipIcon"] svg {
    fill: rgba(244,239,227,0.55) !important;
}

section[data-testid="stSidebar"] [data-testid="stSidebarNav"] { display:none; }

/* ─── Tabs ─── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.4rem; border-bottom: 1px solid var(--rule);
}
.stTabs [data-baseweb="tab"] {
    background: transparent !important;
    color: var(--muted) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.78rem !important; letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    padding: 0.7rem 0.2rem !important; margin-right: 1.2rem !important;
    border-bottom: 2px solid transparent !important;
}
.stTabs [aria-selected="true"] {
    color: var(--forest) !important;
    border-bottom-color: var(--biochar) !important;
}

/* ─── Dataframe / tables ─── */
.stDataFrame, .stTable { font-family: 'DM Sans', sans-serif !important; }
.stDataFrame thead tr th {
    background: var(--cream) !important;
    color: var(--ink) !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.7rem !important;
    letter-spacing: 0.12em !important;
    text-transform: uppercase !important;
    border-bottom: 1px solid var(--rule) !important;
}

/* ─── Buttons ─── */
.stButton > button, .stDownloadButton > button {
    background: #FFFCF5 !important;
    color: var(--forest-dk) !important;
    border: 1px solid var(--rule) !important;
    border-radius: 2px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.74rem !important; letter-spacing: 0.14em !important;
    text-transform: uppercase !important;
    padding: 0.5rem 1rem !important;
    transition: all 0.18s ease;
}
.stButton > button:hover, .stDownloadButton > button:hover {
    background: var(--forest) !important; color: #F4EFE3 !important;
    border-color: var(--forest) !important;
}

/* ─── Footer ─── */
footer { visibility: hidden; }
.app-foot {
    margin-top: 2.4rem; padding-top: 1rem;
    border-top: 1px solid var(--rule);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem; letter-spacing: 0.12em;
    color: var(--muted); text-transform: uppercase;
    display: flex; justify-content: space-between; flex-wrap: wrap; gap: 0.6rem;
}

/* ─── Scrollbar ─── */
::-webkit-scrollbar { width: 8px; height: 8px; }
::-webkit-scrollbar-track { background: var(--cream); }
::-webkit-scrollbar-thumb {
    background: var(--moss); border-radius: 4px;
}
::-webkit-scrollbar-thumb:hover { background: var(--forest); }

/* ─── Hide Streamlit chrome ─── */
#MainMenu, header [data-testid="stToolbar"] { visibility: hidden; height: 0; }
.stDeployButton { display: none; }
</style>
"""
