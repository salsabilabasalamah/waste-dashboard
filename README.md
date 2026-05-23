# SB-Geocarbon · Operations Dashboard

Polished Streamlit dashboard for the SB-Geocarbon biochar pipeline. Reads four
operational sheets directly from a public Google Spreadsheet, runs the
ten-anomaly validator, and surfaces KPIs / trends / a triage queue across
four tabs.

> **Aesthetic:** *Editorial Terroir* — earth tones, Fraunces serif display,
> DM Sans body, JetBrains Mono accents, deep-forest sidebar.

```
dashboard/
├── dashboard.py          # entry point (Streamlit app)
├── data.py               # Google Sheets loader + 10-anomaly validator
├── theme.py              # Plotly template + global CSS
├── requirements.txt      # pinned deps for Streamlit Cloud
├── .streamlit/config.toml
└── README.md
```

## What's in it

| Tab | Contents |
|---|---|
| **Overview** | Headline KPIs (biochar produced, CO₂e, yield, bags), editorial callout with the leading/lagging feedstock, daily + cumulative production trend, donut of feedstock mix. |
| **Production** | Bag-sum yield by feedstock, output by operator, full production-batch table. |
| **Application** | Application KPIs (batches, bags, applied kg, charged), type mix, geographic map (lat/lng auto-parsed), application-batch table. |
| **Data Quality** | Quality score, severity breakdown, anomaly distribution by type, sheet × severity heatmap, top affected records, **filterable validation queue with CSV export**. |

Filters in the sidebar (date range, feedstock type, operator) propagate
through all tabs.

## Run locally

```bash
cd dashboard
pip install -r requirements.txt
streamlit run dashboard.py
# → http://localhost:8501
```

## Deploy to Streamlit Community Cloud

1. **Push this folder to a GitHub repo** (just the `dashboard/` directory
   is enough — no other project files required).
2. Go to <https://share.streamlit.io> → **New app**.
3. Select the repo, branch, and set:
   * **Main file path:** `dashboard.py` (or `dashboard/dashboard.py` if
     deploying the whole project).
   * **Python version:** 3.11 or 3.12.
4. Click **Deploy**. Streamlit Cloud reads `requirements.txt` and
   `.streamlit/config.toml` automatically.

No secrets, no service accounts, no API keys — the Google Sheet is
accessed via its public CSV-export endpoint, so it just works as long as
the spreadsheet is shared as **Anyone with the link → Viewer**.

### Changing the data source

The default Google Sheet URL is hard-coded in `data.py::DEFAULT_SHEET_URL`
but can be **overridden at runtime** from the sidebar input box without
restarting the app. Cache TTL is 5 minutes; the **Refresh data** button
clears it on demand.

## How the validator works

`data.py` ports the same 10 anomaly checks that the production pipeline
runs (TYPES 1–10):

| # | Type | Action |
|---|---|---|
| 1 | Comma decimal (`"18,15"`) | **Auto-fixed** → `18.15`, recorded with `AUTO_FIXED` status. |
| 2 | Negative value in non-negative field | Flagged HIGH. |
| 3 | Missing critical field (weight, biochar_amount_kg, carbon%) | Flagged HIGH. |
| 4 | Duplicate `bag_id` | Flagged HIGH. |
| 5 | Future / implausible timestamp | Flagged MEDIUM. Also triggers when timestamp drifts >30 days from the YYMMDD encoded in `activity_id`. |
| 6 | Invalid `application_type` | Flagged HIGH. |
| 7 | Orphan bag (in `bag_application` but not in `bag_production`) | Flagged HIGH. |
| 8 | App-vs-prod weight discrepancy >5 % | Flagged MEDIUM. |
| 9 | Σ(bag weights) vs `biochar_amount_kg` mismatch | Flagged MEDIUM. |
| 10 | `bag_id` re-used across multiple application batches | Flagged HIGH. |

The CLEANED frames keep all rows (no row dropping), so KPIs are computed
over the full operational dataset.

## Troubleshooting

* **"Could not fetch data"** — verify the sheet's sharing setting
  (Anyone with the link → Viewer) and that the four sheet tabs are named
  exactly: `biochar_production`, `bag_production`,
  `biochar_application`, `bag_application`.
* **Map tab shows "no coordinates"** — `lat_lng` must be a string of the
  form `"-7.123, 110.456"`. Comma-separated, latitude first.
* **Empty charts** — check the sidebar filters. Try resetting the date
  range or clearing the multiselects.
