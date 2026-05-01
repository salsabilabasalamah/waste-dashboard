"""
WasteX Operations Dashboard
───────────────────────────
A polished Streamlit application for the WasteX biochar pipeline:

* Reads four operational sheets from a public Google Spreadsheet.
* Runs the same 10-anomaly validation that the production pipeline uses.
* Surfaces KPIs, trends, and a triage queue across four tabs.

Designed to be deployed to Streamlit Community Cloud as-is — no API
credentials required, since the spreadsheet is public.

Theme: Editorial Terroir — earth tones, serif display + mono accents.
"""
from __future__ import annotations

from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data import (
    DEFAULT_SHEET_URL,
    ANOMALY_NAMES,
    DataBundle,
    clear_cache,
    load_bundle,
)
from theme import (
    AMBER, BIOCHAR, CATEGORICAL, FOREST, FOREST_DK, GLOBAL_CSS, MOSS,
    SEQUENTIAL_GREEN, install_plotly_template,
)

# ─────────────────────────────────────────────────────────────────────── #
# Page config + theme                                                     #
# ─────────────────────────────────────────────────────────────────────── #

st.set_page_config(
    page_title="WasteX | Operations Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "Get help": None,
        "Report a bug": None,
        "About": "WasteX Operations Dashboard — built for the Data Analyst skills test.",
    },
)
install_plotly_template()
st.markdown(GLOBAL_CSS, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────── #
# Helpers                                                                 #
# ─────────────────────────────────────────────────────────────────────── #

def fmt_num(v: float, decimals: int = 0) -> str:
    if pd.isna(v):
        return "—"
    return f"{v:,.{decimals}f}"


def kpi_card(label: str, value: str, *, unit: str = "",
             tone: str = "", foot: str = "", foot_class: str = "") -> str:
    cls = f"kpi {tone}".strip()
    unit_html = f"<span class='unit'>{unit}</span>" if unit else ""
    foot_html = (f"<div class='kpi-foot {foot_class}'>{foot}</div>"
                 if foot else "")
    return (
        f"<div class='{cls}'>"
        f"<div class='kpi-label'>{label}</div>"
        f"<div class='kpi-value'>{value}{unit_html}</div>"
        f"{foot_html}"
        f"</div>"
    )


def kpi_row(cards: list[str]) -> None:
    st.markdown(
        "<div class='kpi-grid'>" + "".join(cards) + "</div>",
        unsafe_allow_html=True,
    )


def section(eyebrow: str, title_html: str) -> None:
    st.markdown(
        f"<div class='section-eyebrow'>{eyebrow}</div>"
        f"<div class='section-h'>{title_html}</div>"
        f"<div class='section-rule'></div>",
        unsafe_allow_html=True,
    )


def severity_pill(sev: str) -> str:
    return f"<span class='pill {sev.lower()}'>{sev}</span>"


# ─────────────────────────────────────────────────────────────────────── #
# Sidebar                                                                 #
# ─────────────────────────────────────────────────────────────────────── #

with st.sidebar:
    st.markdown(
        "<div style='padding:0.4rem 0 0.6rem 0;'>"
        "<div style='font-family:Fraunces,serif;font-size:1.55rem;"
        "font-weight:500;color:#FBF8F2;letter-spacing:-0.01em;'>"
        "WasteX <em style='color:#E0A458;font-style:italic;'>Ops</em></div>"
        "<div style='font-family:JetBrains Mono,monospace;font-size:0.66rem;"
        "letter-spacing:0.18em;color:rgba(244,239,227,0.65);"
        "text-transform:uppercase;margin-top:0.15rem;'>"
        "Biochar Operations Dashboard</div>"
        "</div>",
        unsafe_allow_html=True,
    )
    st.markdown("---")

    sheet_url = st.text_input(
        "Google Sheet URL or ID",
        value=DEFAULT_SHEET_URL,
        help="Must be shared as 'Anyone with the link → Viewer'.",
    )

    refresh = st.button("Refresh data", use_container_width=True)
    if refresh:
        clear_cache()
        st.toast("Cache cleared — fetching fresh data…", icon="🌿")

# ── Load data ───────────────────────────────────────────────────────── #
with st.spinner("Pulling sheets from Google Sheets …"):
    try:
        bundle: DataBundle = load_bundle(sheet_url)
    except Exception as exc:
        st.error(
            f"**Could not fetch data from Google Sheets.**\n\n"
            f"`{exc}`\n\n"
            f"Verify the URL is correct and the sheet is shared as "
            f"*Anyone with the link → Viewer*."
        )
        st.stop()

prod = bundle.prod
bag_prod = bundle.bag_prod
app = bundle.app
bag_app = bundle.bag_app
queue = bundle.queue


# ── Sidebar filters (require the data to be loaded first) ───────────── #
with st.sidebar:
    st.markdown("### Filters")

    if "_date" in prod.columns and prod["_date"].notna().any():
        min_d = pd.to_datetime(prod["_date"].min())
        max_d = pd.to_datetime(prod["_date"].max())
        # Pad by 1 day so sliders can show single-day ranges.
        if min_d == max_d:
            max_d = max_d + pd.Timedelta(days=1)
        date_range = st.date_input(
            "Production date",
            value=(min_d.date(), max_d.date()),
            min_value=min_d.date(),
            max_value=max_d.date(),
        )
        if isinstance(date_range, tuple) and len(date_range) == 2:
            d_lo, d_hi = date_range
        else:
            d_lo, d_hi = min_d.date(), max_d.date()
    else:
        d_lo, d_hi = None, None

    feed_options = sorted(
        v for v in prod.get("feedstock_type", pd.Series(dtype=str))
        .dropna().unique()
    )
    selected_feed = st.multiselect(
        "Feedstock type",
        options=feed_options, default=feed_options,
    )

    op_options = sorted(
        v for v in prod.get("username", pd.Series(dtype=str))
        .dropna().unique()
    )
    selected_op = st.multiselect(
        "Operator",
        options=op_options, default=op_options,
    )

    st.markdown("---")
    st.markdown(
        f"<div style='font-family:JetBrains Mono,monospace;font-size:0.66rem;"
        f"letter-spacing:0.16em;color:rgba(244,239,227,0.6);"
        f"text-transform:uppercase;line-height:1.7;'>"
        f"Cache TTL · 5 min<br/>"
        f"Fetched · {bundle.fetched_at.strftime('%H:%M:%S')}<br/>"
        f"Raw rows · {sum(bundle.raw_sizes.values())}"
        f"</div>",
        unsafe_allow_html=True,
    )


# ── Apply filters ──────────────────────────────────────────────────── #
def apply_prod_filter(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    if d_lo is not None and "_date" in out.columns:
        out = out[(out["_date"] >= d_lo) & (out["_date"] <= d_hi)]
    if selected_feed and "feedstock_type" in out.columns:
        out = out[out["feedstock_type"].isin(selected_feed)]
    if selected_op and "username" in out.columns:
        out = out[out["username"].isin(selected_op)]
    return out


prod_f = apply_prod_filter(prod)
prod_ids = set(prod_f["activity_id"]) if "activity_id" in prod_f.columns else set()
bag_prod_f = bag_prod[bag_prod["production_id"].isin(prod_ids)] \
    if "production_id" in bag_prod.columns else bag_prod
applied_bag_ids = set(bag_prod_f["bag_id"]) if "bag_id" in bag_prod_f.columns else set()
bag_app_f = bag_app[bag_app["bag_id"].isin(applied_bag_ids)] \
    if "bag_id" in bag_app.columns else bag_app
app_ids = set(bag_app_f["application_id"]) \
    if "application_id" in bag_app_f.columns else set()
app_f = app[app["activity_id"].isin(app_ids)] \
    if "activity_id" in app.columns else app


# ─────────────────────────────────────────────────────────────────────── #
# Header band                                                             #
# ─────────────────────────────────────────────────────────────────────── #

n_anom = len(queue)
n_review = int((queue["status"] == "REVIEW_REQUIRED").sum()) if not queue.empty else 0

st.markdown(
    f"""
    <div class='brand-band'>
        <div class='brand-eyebrow'>Operations Intelligence · 2024 Q4</div>
        <h1 class='brand-title'>WasteX <em>Biochar</em> Operations</h1>
        <div class='brand-sub'>
            A live snapshot of the biochar production and field-application
            pipeline — pulled directly from the operational Google Sheet,
            cleaned through the ten-anomaly validator, and reconciled
            bag-by-bag.
        </div>
        <div class='brand-meta'>
            <span><span class='dot'></span>LIVE · {bundle.fetched_at.strftime("%d %b %Y · %H:%M")}</span>
            <span>RAW ROWS · <b>{sum(bundle.raw_sizes.values())}</b></span>
            <span>ANOMALIES · <b>{n_anom}</b> ({n_review} need review)</span>
            <span>AUTO-FIXED · <b>{bundle.autofix_count}</b></span>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────── #
# Tabs                                                                    #
# ─────────────────────────────────────────────────────────────────────── #

tab_overview, tab_prod, tab_app, tab_dq = st.tabs(
    ["Overview", "Production", "Application", "Data Quality"]
)


# ════════════════════════════════════════════════════════════════════════
# TAB · OVERVIEW
# ════════════════════════════════════════════════════════════════════════
with tab_overview:
    section("Headline metrics", "The <em>state</em> of operations")

    total_biochar = prod_f["biochar_amount_kg"].sum() if "biochar_amount_kg" in prod_f.columns else 0
    total_co2e = prod_f["co2e_persistent"].sum() if "co2e_persistent" in prod_f.columns else 0
    feed_total = prod_f["feedstock_amount"].sum() if "feedstock_amount" in prod_f.columns else 0
    yield_pct = (total_biochar / feed_total * 100) if feed_total else 0
    n_batches = len(prod_f)
    n_bags_prod = len(bag_prod_f)
    n_bags_app = len(bag_app_f)
    applied_kg = bag_app_f["bag_weight"].sum() if "bag_weight" in bag_app_f.columns else 0

    raw_total_rows = sum(bundle.raw_sizes.values())
    dq_score = (1 - n_review / raw_total_rows) * 100 if raw_total_rows else 100

    kpi_row([
        kpi_card("Biochar produced", fmt_num(total_biochar, 1),
                 unit="kg", tone="",
                 foot=f"across {n_batches} production batches"),
        kpi_card("CO₂e sequestered", fmt_num(total_co2e, 1),
                 unit="kg", tone="moss",
                 foot="persistent — 1 000-yr horizon"),
        kpi_card("Conversion yield", fmt_num(yield_pct, 1),
                 unit="%", tone="amber",
                 foot=f"{fmt_num(feed_total,0)} kg feedstock processed"),
        kpi_card("Bags in field", fmt_num(n_bags_app, 0),
                 tone="accent",
                 foot=f"{fmt_num(applied_kg,1)} kg applied · {len(app_f)} batches"),
    ])

    # ─── Editorial callout (computed insight) ─────────────────────── #
    if not prod_f.empty and "_bag_yield_pct" in prod_f.columns:
        by_feed = (prod_f.groupby("feedstock_type")["_bag_yield_pct"]
                   .mean().sort_values(ascending=False).round(1))
        if len(by_feed) >= 2:
            lead, lag = by_feed.index[0], by_feed.index[-1]
            spread = by_feed.iloc[0] - by_feed.iloc[-1]
            if spread > 1:
                st.markdown(
                    f"<div class='callout'>"
                    f"<b>{lead}</b> currently leads on bag-derived yield at "
                    f"<b>{by_feed.iloc[0]}%</b>, while <b>{lag}</b> trails at "
                    f"<b>{by_feed.iloc[-1]}%</b> — a spread of "
                    f"<b>{spread:.1f}</b> percentage points. With most "
                    f"feedstocks represented by a single batch, this gap "
                    f"warrants more replicates before changing the mix."
                    f"</div>",
                    unsafe_allow_html=True,
                )

    # ─── Two-up: production trend + feedstock mix ─────────────────── #
    c1, c2 = st.columns([7, 5], gap="large")

    with c1:
        section("Cadence", "Production <em>over time</em>")
        if not prod_f.empty and "_date" in prod_f.columns:
            trend = (prod_f.dropna(subset=["_date"])
                     .groupby("_date", as_index=False)
                     .agg(biochar_kg=("biochar_amount_kg", "sum"),
                          batches=("activity_id", "count")))
            trend["cum_kg"] = trend["biochar_kg"].cumsum()

            fig = go.Figure()
            fig.add_bar(
                x=trend["_date"], y=trend["biochar_kg"],
                name="Daily output (kg)", marker_color=FOREST,
                hovertemplate="<b>%{x}</b><br>%{y:,.1f} kg<extra></extra>",
            )
            fig.add_scatter(
                x=trend["_date"], y=trend["cum_kg"],
                name="Cumulative (kg)", mode="lines+markers",
                line=dict(color=BIOCHAR, width=2.5),
                marker=dict(size=6, color=BIOCHAR),
                yaxis="y2",
                hovertemplate="<b>%{x}</b><br>cum %{y:,.1f} kg<extra></extra>",
            )
            fig.update_layout(
                height=360,
                yaxis=dict(title="Daily (kg)"),
                yaxis2=dict(title="Cumulative (kg)", overlaying="y",
                            side="right", showgrid=False),
                margin=dict(l=8, r=8, t=10, b=8),
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No production records in the current filter.")

    with c2:
        section("Mix", "Feedstock <em>composition</em>")
        if not prod_f.empty and "feedstock_type" in prod_f.columns:
            mix = (prod_f.groupby("feedstock_type", as_index=False)
                   .agg(kg=("biochar_amount_kg", "sum")))
            fig = go.Figure(go.Pie(
                labels=mix["feedstock_type"], values=mix["kg"],
                hole=0.62,
                marker=dict(colors=CATEGORICAL[:len(mix)],
                            line=dict(color="#FBF8F2", width=2)),
                textinfo="label+percent",
                textfont=dict(family="DM Sans", size=12),
                hovertemplate="<b>%{label}</b><br>%{value:,.1f} kg "
                              "(%{percent})<extra></extra>",
            ))
            fig.update_layout(
                height=360, showlegend=False,
                margin=dict(l=8, r=8, t=10, b=8),
                annotations=[dict(
                    text=f"<b style='font-family:Fraunces,serif;font-size:1.5rem;'>"
                         f"{fmt_num(mix['kg'].sum(),0)}</b><br>"
                         f"<span style='font-family:JetBrains Mono,monospace;"
                         f"font-size:0.7rem;letter-spacing:0.16em;'>KG TOTAL</span>",
                    x=0.5, y=0.5, showarrow=False,
                )],
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No feedstock data to show.")


# ════════════════════════════════════════════════════════════════════════
# TAB · PRODUCTION
# ════════════════════════════════════════════════════════════════════════
with tab_prod:
    section("Carbonisation floor", "Production <em>performance</em>")

    if prod_f.empty:
        st.info("No production batches match the current filter.")
    else:
        c1, c2 = st.columns(2, gap="large")

        with c1:
            section("Yield", "By <em>feedstock</em>")
            yld = (prod_f.dropna(subset=["_bag_yield_pct"])
                   if "_bag_yield_pct" in prod_f.columns else prod_f)
            yld_g = (yld.groupby("feedstock_type", as_index=False)
                     .agg(mean_yield=("_bag_yield_pct", "mean"),
                          n=("activity_id", "count"))
                     .sort_values("mean_yield", ascending=True))
            fig = px.bar(
                yld_g, y="feedstock_type", x="mean_yield",
                orientation="h",
                color="mean_yield",
                color_continuous_scale=SEQUENTIAL_GREEN,
                text=yld_g["mean_yield"].map(lambda v: f"{v:.1f}%"),
                labels={"feedstock_type": "", "mean_yield": "Bag-sum yield (%)"},
            )
            fig.update_traces(textposition="outside",
                              textfont=dict(family="DM Sans", size=11))
            fig.update_layout(height=320, coloraxis_showscale=False,
                              xaxis=dict(ticksuffix="%"))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            section("Operators", "Output by <em>username</em>")
            if "username" in prod_f.columns:
                op = (prod_f.groupby("username", as_index=False)
                      .agg(kg=("biochar_amount_kg", "sum"),
                           batches=("activity_id", "count"))
                      .sort_values("kg", ascending=True))
                fig = px.bar(
                    op, y="username", x="kg", orientation="h",
                    text=op["kg"].map(lambda v: f"{v:,.0f}"),
                    color_discrete_sequence=[FOREST],
                    labels={"username": "", "kg": "Biochar produced (kg)"},
                )
                fig.update_traces(textposition="outside",
                                  textfont=dict(family="DM Sans", size=11))
                fig.update_layout(height=320)
                st.plotly_chart(fig, use_container_width=True)

        section("Inventory", "Production <em>batches</em>")
        cols = [c for c in [
            "activity_id", "Timestamp", "username", "feedstock_type",
            "feedstock_amount", "biochar_amount_kg", "_bag_sum_kg",
            "_bag_yield_pct", "number_of_bags", "co2e_persistent",
        ] if c in prod_f.columns]
        df = prod_f[cols].copy()
        rename = {
            "activity_id": "Batch", "Timestamp": "Timestamp",
            "username": "Operator", "feedstock_type": "Feedstock",
            "feedstock_amount": "Feedstock (kg)",
            "biochar_amount_kg": "Reported (kg)",
            "_bag_sum_kg": "Bag sum (kg)",
            "_bag_yield_pct": "Yield (%)",
            "number_of_bags": "# bags",
            "co2e_persistent": "CO₂e (kg)",
        }
        df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
        st.dataframe(df, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════
# TAB · APPLICATION
# ════════════════════════════════════════════════════════════════════════
with tab_app:
    section("In the field", "Application <em>activity</em>")

    if app_f.empty and bag_app_f.empty:
        st.info("No application records match the current filter.")
    else:
        n_app = len(app_f)
        applied_kg = bag_app_f["bag_weight"].sum() if "bag_weight" in bag_app_f.columns else 0
        n_bags = len(bag_app_f)
        if "application_type" in app_f.columns:
            charged = int(app_f["application_type"]
                          .str.contains("Charged", case=False, na=False).sum())
            sales = int(app_f["application_type"]
                        .str.contains("Sale", case=False, na=False).sum())
        else:
            charged = sales = 0

        kpi_row([
            kpi_card("Application batches", fmt_num(n_app, 0)),
            kpi_card("Bags applied", fmt_num(n_bags, 0), tone="moss"),
            kpi_card("Total applied", fmt_num(applied_kg, 1), unit="kg",
                     tone="amber"),
            kpi_card("Charged biochar", fmt_num(charged, 0), tone="accent",
                     foot=f"{sales} sales · {max(n_app - charged - sales, 0)} pure"),
        ])

        c1, c2 = st.columns([5, 7], gap="large")

        with c1:
            section("Type mix", "Application <em>categories</em>")
            if "application_type" in app_f.columns:
                mix = (app_f.groupby("application_type", as_index=False)
                       .agg(n=("activity_id", "count"))
                       .sort_values("n", ascending=True))
                fig = px.bar(
                    mix, y="application_type", x="n", orientation="h",
                    text="n",
                    color_discrete_sequence=[BIOCHAR],
                    labels={"application_type": "", "n": "Batches"},
                )
                fig.update_traces(textposition="outside",
                                  textfont=dict(family="DM Sans", size=11))
                fig.update_layout(height=320)
                st.plotly_chart(fig, use_container_width=True)

        with c2:
            section("Geography", "Application <em>locations</em>")
            if "location" in app_f.columns:
                coords = app_f["location"].dropna().astype(str).str.split(",", expand=True)
                if coords.shape[1] >= 2:
                    try:
                        map_df = pd.DataFrame({
                            "lat": pd.to_numeric(coords[0], errors="coerce"),
                            "lon": pd.to_numeric(coords[1], errors="coerce"),
                            "label": app_f["activity_id"],
                            "type": app_f.get("application_type", ""),
                            "weight": app_f.get("total_weight", 0),
                        }).dropna(subset=["lat", "lon"])
                        if not map_df.empty:
                            fig = px.scatter_map(
                                map_df, lat="lat", lon="lon",
                                size="weight", hover_name="label",
                                hover_data={
                                    "lat": False, "lon": False,
                                    "type": True, "weight": ":,.1f",
                                },
                                color_discrete_sequence=[BIOCHAR],
                                zoom=8, height=320,
                            )
                            fig.update_layout(
                                map_style="open-street-map",
                                margin=dict(l=0, r=0, t=10, b=0),
                            )
                            st.plotly_chart(fig, use_container_width=True)
                        else:
                            st.info("No valid coordinates in the current filter.")
                    except Exception as exc:
                        st.warning(f"Could not render map: {exc}")
                else:
                    st.info("Location column does not contain parseable coordinates.")
            else:
                st.info("No location column available.")

        section("Inventory", "Application <em>batches</em>")
        if not app_f.empty:
            cols = [c for c in [
                "activity_id", "Timestamp", "username", "application_type",
                "total_weight", "purpose", "charging_material",
                "location",
            ] if c in app_f.columns]
            df = app_f[cols].copy()
            rename = {
                "activity_id": "Batch", "Timestamp": "Timestamp",
                "username": "Operator", "application_type": "Type",
                "total_weight": "Weight (kg)", "purpose": "Purpose",
                "charging_material": "Charging material",
                "location": "Location",
            }
            df = df.rename(columns={k: v for k, v in rename.items()
                                    if k in df.columns})
            st.dataframe(df, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════════════
# TAB · DATA QUALITY
# ════════════════════════════════════════════════════════════════════════
with tab_dq:
    section("Trust the data", "Validation <em>queue</em>")

    if queue.empty:
        st.success("No anomalies detected. Pipeline is squeaky clean. 🌿")
    else:
        n_total = len(queue)
        n_review = int((queue["status"] == "REVIEW_REQUIRED").sum())
        n_auto = int((queue["status"] == "AUTO_FIXED").sum())
        n_high = int((queue["severity"] == "HIGH").sum())
        n_med = int((queue["severity"] == "MEDIUM").sum())
        n_low = int((queue["severity"] == "LOW").sum())

        raw_total = sum(bundle.raw_sizes.values())
        dq_score = (1 - n_review / raw_total) * 100 if raw_total else 100
        score_class = "ok" if dq_score >= 90 else ("warn" if dq_score >= 75 else "danger")

        kpi_row([
            kpi_card("Quality score", f"{dq_score:.1f}",
                     unit="%", tone="moss" if dq_score >= 90 else "danger",
                     foot=f"{n_review} of {raw_total} rows need review",
                     foot_class=score_class),
            kpi_card("Total findings", fmt_num(n_total, 0),
                     foot=f"{n_auto} auto-fixed · {n_review} need review"),
            kpi_card("High severity", fmt_num(n_high, 0), tone="danger",
                     foot=f"{n_med} medium · {n_low} low"),
            kpi_card("Anomaly types hit", f"{queue['anomaly_type'].nunique()} / 10",
                     tone="amber",
                     foot="of 10 defined checks"),
        ])

        c1, c2 = st.columns(2, gap="large")

        with c1:
            section("Distribution", "Anomalies by <em>type</em>")
            cnt = (queue.groupby(["anomaly_type", "anomaly_name"])
                   .size().reset_index(name="n")
                   .sort_values("n", ascending=True))
            cnt["label"] = (cnt["anomaly_type"].astype(str) + " — "
                            + cnt["anomaly_name"])
            fig = px.bar(
                cnt, y="label", x="n", orientation="h", text="n",
                color_discrete_sequence=[BIOCHAR],
                labels={"label": "", "n": "Count"},
            )
            fig.update_traces(textposition="outside",
                              textfont=dict(family="DM Sans", size=11))
            fig.update_layout(height=380)
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            section("Heatmap", "Sheet × <em>severity</em>")
            heat = (queue.groupby(["sheet", "severity"])
                    .size().reset_index(name="n"))
            pv = heat.pivot(index="sheet", columns="severity",
                            values="n").fillna(0)
            for s in ("HIGH", "MEDIUM", "LOW"):
                if s not in pv.columns:
                    pv[s] = 0
            pv = pv[["HIGH", "MEDIUM", "LOW"]]
            fig = px.imshow(
                pv.values, x=pv.columns, y=pv.index,
                color_continuous_scale=SEQUENTIAL_GREEN,
                text_auto=True, aspect="auto",
            )
            fig.update_xaxes(side="top")
            fig.update_layout(
                height=380, coloraxis_showscale=False,
                xaxis=dict(title="", tickfont=dict(family="JetBrains Mono",
                                                   size=10)),
                yaxis=dict(title=""),
            )
            st.plotly_chart(fig, use_container_width=True)

        # ─── Top affected records ──────────────────────────────────── #
        section("Hot spots", "Records with <em>most</em> findings")
        top = (queue.groupby(["sheet", "record_id"])
               .agg(n=("anomaly_type", "count"),
                    types=("anomaly_type",
                           lambda s: ", ".join(f"#{t}" for t in
                                               sorted(set(s)))))
               .sort_values("n", ascending=False).head(8)
               .reset_index())
        st.dataframe(
            top.rename(columns={"sheet": "Sheet", "record_id": "Record",
                                "n": "Anomalies", "types": "Types"}),
            use_container_width=True, hide_index=True,
        )

        # ─── Filterable queue ─────────────────────────────────────── #
        section("Triage", "Validation <em>queue</em>")

        f1, f2, f3 = st.columns(3)
        sev_pick = f1.multiselect(
            "Severity",
            options=sorted(queue["severity"].unique()),
            default=sorted(queue["severity"].unique()),
        )
        sheet_pick = f2.multiselect(
            "Sheet",
            options=sorted(queue["sheet"].unique()),
            default=sorted(queue["sheet"].unique()),
        )
        type_pick = f3.multiselect(
            "Anomaly type",
            options=sorted(queue["anomaly_type"].unique()),
            default=sorted(queue["anomaly_type"].unique()),
            format_func=lambda t: f"#{t} {ANOMALY_NAMES.get(t,'')}",
        )

        q = queue[
            queue["severity"].isin(sev_pick) &
            queue["sheet"].isin(sheet_pick) &
            queue["anomaly_type"].isin(type_pick)
        ]

        st.markdown(
            f"<div style='font-family:JetBrains Mono,monospace;"
            f"font-size:0.72rem;color:#6B7B6E;letter-spacing:0.12em;"
            f"text-transform:uppercase;margin:0.4rem 0;'>"
            f"Showing {len(q)} of {len(queue)} findings"
            f"</div>",
            unsafe_allow_html=True,
        )

        show_cols = [c for c in [
            "severity", "sheet", "anomaly_type", "anomaly_name",
            "record_id", "field", "original_value", "description",
            "suggested_action", "status",
        ] if c in q.columns]
        q_view = q[show_cols].copy()
        if "original_value" in q_view.columns:
            q_view["original_value"] = q_view["original_value"].astype(str)
        st.dataframe(
            q_view.rename(columns={
                "anomaly_type": "type",
                "anomaly_name": "name",
            }),
            use_container_width=True, hide_index=True, height=420,
        )

        st.download_button(
            "Download VALIDATION_QUEUE as CSV",
            data=q.to_csv(index=False).encode("utf-8"),
            file_name=f"validation_queue_{datetime.now():%Y%m%d_%H%M}.csv",
            mime="text/csv",
            use_container_width=False,
        )


# ─────────────────────────────────────────────────────────────────────── #
# Footer                                                                  #
# ─────────────────────────────────────────────────────────────────────── #

st.markdown(
    f"""
    <div class='app-foot'>
        <span>WasteX · Operations Dashboard</span>
        <span>Built with Streamlit · Plotly · Editorial Terroir theme</span>
        <span>Data refreshed {bundle.fetched_at:%Y-%m-%d %H:%M}</span>
    </div>
    """,
    unsafe_allow_html=True,
)
