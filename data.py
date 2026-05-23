"""
SB-Geocarbon dashboard | Data layer.

Reads the four operational sheets from a public Google Spreadsheet 
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd
import requests
import streamlit as st

# ─────────────────────────────────────────────────────────────────────── #
# Configuration                                                           #
# ─────────────────────────────────────────────────────────────────────── #
"""
Catatan : copy google sheet yang diberikan, untuk membantu full akses

Link Google Sheet copy : https://docs.google.com/spreadsheets/d/1sNOPpAa90NfMp14HoW0w7UrdCdEusgUslaZlHKeY7vs/edit?usp=sharing
"""

DEFAULT_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1sNOPpAa90NfMp14HoW0w7UrdCdEusgUslaZlHKeY7vs/edit?usp=sharing"
)

SHEET_NAMES = [
    "biochar_production",
    "bag_production",
    "biochar_application",
    "bag_application",
]

VALID_APPLICATION_TYPES = {
    "Application-Pure Biochar",
    "Application-Charged Biochar",
    "Sale-Pure Biochar",
    "Sale-Charged Biochar",
}

"""
Menambahkan ambang batas (threshold)
WEIGHT_DISCREPANCY_PCT = 0.05 (5%): Batas selisih bag weight. Jika bag weight saat diaplikasikan berbeda lebih dari 5% dibanding saat diproduksi, sistem akan mencatatnya sebagai anomali (Tipe 8).

BATCH_SUM_PCT = 0.02 (2%): Batas toleransi persentase selisih total berat seluruh kantong dalam satu batch dibandingkan dengan total produksi yang diinput (Tipe 9).

BATCH_SUM_KG = 2.0: Batas toleransi absolut (dalam kilogram) untuk selisih total berat batch. Data dianggap anomali hanya jika selisihnya melebihi persentase (2%) dan melebihi 2 kg.

ACTIVITY_ID_LAG_DAYS = 30: Jarak waktu maksimal yang masuk akal (30 hari) antara tanggal yang tertera di activity_id dengan waktu data tersebut diinput ke sistem (Timestamp). Jika lebih dari 30 hari, dianggap mencurigakan (Tipe 5).
"""

WEIGHT_DISCREPANCY_PCT = 0.05
BATCH_SUM_PCT = 0.02
BATCH_SUM_KG = 2.0
ACTIVITY_ID_LAG_DAYS = 30

ANOMALY_NAMES = {
    1:  "Comma decimal separator",
    2:  "Negative value in non-negative field",
    3:  "Missing critical field",
    4:  "Duplicate bag_id (same batch)",
    5:  "Future / implausible timestamp",
    6:  "Invalid application_type",
    7:  "Orphan bag (not in bag_production)",
    8:  "Weight discrepancy (>5% prod vs application)",
    9:  "Batch sum mismatch (bag weights vs biochar_amount_kg)",
    10: "Bag used in multiple application batches",
}


# ─────────────────────────────────────────────────────────────────────── #
# Google Sheets loader                                                    #
# ─────────────────────────────────────────────────────────────────────── #

_SHEET_ID_RE = re.compile(r"/spreadsheets/d/([a-zA-Z0-9-_]+)")


def extract_sheet_id(url_or_id: str) -> str:
    """Accept either a full Google Sheets URL or just the id."""
    m = _SHEET_ID_RE.search(url_or_id)
    return m.group(1) if m else url_or_id.strip()


def csv_export_url(sheet_id: str, sheet_name: str) -> str:
    return (
        f"https://docs.google.com/spreadsheets/d/{sheet_id}"
        f"/gviz/tq?tqx=out:csv&sheet={sheet_name}"
    )


@st.cache_data(ttl=300, show_spinner=False)
def fetch_raw_sheets(sheet_url: str) -> dict[str, pd.DataFrame]:
    """Pull all four sheets via the gviz CSV endpoint. Cached for 5 min."""
    sid = extract_sheet_id(sheet_url)
    out: dict[str, pd.DataFrame] = {}
    for name in SHEET_NAMES:
        url = csv_export_url(sid, name)
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        # `weight` may have comma-decimals — keep as string for TYPE 1
        # detection (handled later in validator).
        df = pd.read_csv(io.StringIO(resp.text), keep_default_na=True)
        out[name] = df
    return out


# ─────────────────────────────────────────────────────────────────────── #
# Helpers                                                                 #
# ─────────────────────────────────────────────────────────────────────── #

_RE_PROD = re.compile(r"^(\d{6})-Y\d{4}-M\d{4}$")
_RE_APP = re.compile(r"^(\d{6})-A\d{4}$")
_RE_BAG = re.compile(r"^(\d{6})-Y\d{4}-M\d{4}-\d+$")


def date_from_activity_id(value: Any) -> pd.Timestamp:
    if not isinstance(value, str):
        return pd.NaT
    s = value.strip()
    for rgx in (_RE_PROD, _RE_APP, _RE_BAG):
        m = rgx.match(s)
        if m:
            try:
                return pd.to_datetime(m.group(1), format="%y%m%d")
            except Exception:
                return pd.NaT
    return pd.NaT


def to_float_safe(value: Any) -> tuple[float, bool]:
    """Return (float, was_comma_fixed)."""
    if pd.isna(value):
        return np.nan, False
    if isinstance(value, (int, float, np.integer, np.floating)):
        return float(value), False
    s = str(value).strip()
    if not s:
        return np.nan, False
    fixed = False
    if "," in s and "." not in s:
        s = s.replace(",", ".")
        fixed = True
    try:
        return float(s), fixed
    except ValueError:
        return np.nan, False


def parse_dt(value: Any) -> pd.Timestamp:
    return pd.NaT if pd.isna(value) else pd.to_datetime(value, errors="coerce")


def _norm_text(df: pd.DataFrame, cols: list[str]) -> int:
    n = 0
    for c in cols:
        if c not in df.columns:
            continue
        for idx, val in df[c].items():
            if isinstance(val, str):
                stripped = val.strip()
                if stripped != val:
                    df.at[idx, c] = stripped
                    n += 1
    return n


def _push(queue: list[dict], **fields) -> None:
    fields.setdefault("detected_at",
                      datetime.now().strftime("%Y-%m-%dT%H:%M:%S"))
    fields["anomaly_name"] = ANOMALY_NAMES.get(fields["anomaly_type"], "")
    queue.append(fields)


# ─────────────────────────────────────────────────────────────────────── #
# Validator                                                               #
# ─────────────────────────────────────────────────────────────────────── #

@dataclass
class DataBundle:
    """Cleaned operational data + validation queue."""
    prod: pd.DataFrame
    bag_prod: pd.DataFrame
    app: pd.DataFrame
    bag_app: pd.DataFrame
    queue: pd.DataFrame
    fetched_at: datetime = field(default_factory=datetime.now)
    autofix_count: int = 0
    raw_sizes: dict[str, int] = field(default_factory=dict)


def _validate(raw: dict[str, pd.DataFrame]) -> DataBundle:
    today = pd.Timestamp.today().normalize()
    queue: list[dict] = []
    autofix = 0

    prod = raw["biochar_production"].copy().reset_index(drop=True)
    bag_prod = raw["bag_production"].copy().reset_index(drop=True)
    app = raw["biochar_application"].copy().reset_index(drop=True)
    bag_app = raw["bag_application"].copy().reset_index(drop=True)

    # ── bag_production ───────────────────────────────────────────────── #
    # TYPE 1 — comma decimals (temuan auto-fix)
    if "weight" in bag_prod.columns:
        for idx, raw_w in bag_prod["weight"].items():
            if isinstance(raw_w, str):
                new_val, fixed = to_float_safe(raw_w)
                bag_prod.at[idx, "weight"] = new_val
                if fixed:
                    autofix += 1
                    _push(queue, sheet="bag_production", row_index=int(idx),
                          record_id=str(bag_prod.at[idx, "bag_id"]),
                          anomaly_type=1,
                          description="Comma decimal separator detected and auto-corrected.",
                          field="weight", original_value=raw_w,
                          suggested_action=f"Auto-fixed → {new_val}",
                          severity="LOW", status="AUTO_FIXED")
        bag_prod["weight"] = pd.to_numeric(bag_prod["weight"], errors="coerce")
    autofix += _norm_text(bag_prod, ["feedstock_type", "username"])

    neg_cols = ["weight", "co2e_persistent", "co2e_100", "spc",
                "margin_of_safety", "electricity_emission"]
    for idx, row in bag_prod.iterrows():
        for col in neg_cols:
            v = row.get(col)
            if pd.notna(v) and isinstance(v, (int, float, np.integer, np.floating)) and v < 0:
                _push(queue, sheet="bag_production", row_index=int(idx),
                      record_id=str(row.get("bag_id", "")),
                      anomaly_type=2,
                      description=f"Negative value in non-negative field '{col}'.",
                      field=col, original_value=v,
                      suggested_action="Verify measurement; correct sign or discard.",
                      severity="HIGH", status="REVIEW_REQUIRED")
        if pd.isna(row.get("weight")):
            _push(queue, sheet="bag_production", row_index=int(idx),
                  record_id=str(row.get("bag_id", "")),
                  anomaly_type=3,
                  description="Missing critical field: weight.",
                  field="weight", original_value=None,
                  suggested_action="Re-collect bag weight from operator.",
                  severity="HIGH", status="REVIEW_REQUIRED")

    dups = bag_prod[bag_prod.duplicated(subset=["bag_id"], keep=False)]
    for idx, row in dups.iterrows():
        _push(queue, sheet="bag_production", row_index=int(idx),
              record_id=str(row["bag_id"]), anomaly_type=4,
              description="bag_id appears more than once in bag_production.",
              field="bag_id", original_value=row["bag_id"],
              suggested_action="Keep one canonical record; merge or discard duplicate.",
              severity="HIGH", status="REVIEW_REQUIRED")

    for idx, row in bag_prod.iterrows():
        ts = parse_dt(row.get("Timestamp"))
        if pd.isna(ts):
            continue
        bd = date_from_activity_id(row.get("bag_id"))
        future = ts.normalize() > today
        far = pd.notna(bd) and (ts.normalize() - bd).days > ACTIVITY_ID_LAG_DAYS
        if future or far:
            why = "beyond today" if future else (
                f"differs from id-encoded date ({bd.date()}) by "
                f"{(ts.normalize() - bd).days} days"
            )
            _push(queue, sheet="bag_production", row_index=int(idx),
                  record_id=str(row.get("bag_id", "")),
                  anomaly_type=5,
                  description=f"Implausible Timestamp ({why}).",
                  field="Timestamp", original_value=row["Timestamp"],
                  suggested_action="Verify and correct timestamp.",
                  severity="MEDIUM", status="REVIEW_REQUIRED")

    # ── biochar_production ───────────────────────────────────────────── #
    autofix += _norm_text(prod, ["feedstock_type", "feedstock_humidity",
                                 "feedstock_size", "username"])
    for idx, row in prod.iterrows():
        for col in ("biochar_amount_kg", "carbon_content_%"):
            if col in prod.columns and pd.isna(row.get(col)):
                _push(queue, sheet="biochar_production", row_index=int(idx),
                      record_id=str(row.get("activity_id", "")),
                      anomaly_type=3,
                      description=f"Missing critical field: {col}.",
                      field=col, original_value=None,
                      suggested_action="Operator must re-submit production record.",
                      severity="HIGH", status="REVIEW_REQUIRED")
        ts = parse_dt(row.get("Timestamp"))
        bd = date_from_activity_id(row.get("activity_id"))
        if pd.notna(ts):
            future = ts.normalize() > today
            far = pd.notna(bd) and (ts.normalize() - bd).days > ACTIVITY_ID_LAG_DAYS
            if future or far:
                why = "beyond today" if future else (
                    f"differs from id-encoded date ({bd.date()}) by "
                    f"{(ts.normalize() - bd).days} days"
                )
                _push(queue, sheet="biochar_production", row_index=int(idx),
                      record_id=str(row.get("activity_id", "")),
                      anomaly_type=5,
                      description=f"Implausible Timestamp ({why}).",
                      field="Timestamp", original_value=row["Timestamp"],
                      suggested_action="Verify and correct timestamp.",
                      severity="MEDIUM", status="REVIEW_REQUIRED")

    # ── biochar_application ──────────────────────────────────────────── #
    autofix += _norm_text(app, ["application_type", "purpose",
                                "charging_material", "username",
                                "methane_compensation"])
    for idx, row in app.iterrows():
        bd = date_from_activity_id(row.get("activity_id"))
        for f in ("Timestamp", "application_date"):
            if f not in app.columns:
                continue
            d = parse_dt(row.get(f))
            if pd.isna(d):
                continue
            future = d.normalize() > today
            far = pd.notna(bd) and (d.normalize() - bd).days > ACTIVITY_ID_LAG_DAYS
            if future or far:
                why = "beyond today" if future else (
                    f"differs from id-encoded date ({bd.date()}) by "
                    f"{(d.normalize() - bd).days} days"
                )
                _push(queue, sheet="biochar_application", row_index=int(idx),
                      record_id=str(row.get("activity_id", "")),
                      anomaly_type=5,
                      description=f"Implausible {f} ({why}).",
                      field=f, original_value=row[f],
                      suggested_action="Verify and correct date.",
                      severity="MEDIUM", status="REVIEW_REQUIRED")
        if "application_type" in app.columns and \
                row.get("application_type") not in VALID_APPLICATION_TYPES:
            _push(queue, sheet="biochar_application", row_index=int(idx),
                  record_id=str(row.get("activity_id", "")),
                  anomaly_type=6,
                  description="application_type is not in the allowed set.",
                  field="application_type",
                  original_value=row.get("application_type"),
                  suggested_action=f"Must be one of: {sorted(VALID_APPLICATION_TYPES)}.",
                  severity="HIGH", status="REVIEW_REQUIRED")

    # ── bag_application + cross-sheet ───────────────────────────────── #
    autofix += _norm_text(bag_app, ["feedstock_type", "username"])

    if "bag_id" in bag_prod.columns and "weight" in bag_prod.columns:
        prod_weights = (bag_prod.dropna(subset=["weight"])
                        .groupby("bag_id")["weight"].mean().to_dict())
        prod_bag_set = set(bag_prod["bag_id"].dropna().unique())
    else:
        prod_weights, prod_bag_set = {}, set()

    if "application_id" in bag_app.columns and "bag_id" in bag_app.columns:
        multi = set(bag_app.groupby("bag_id")["application_id"].nunique()
                    .loc[lambda s: s > 1].index)
    else:
        multi = set()

    for idx, row in bag_app.iterrows():
        bag_id = row.get("bag_id")
        ts = parse_dt(row.get("Timestamp"))
        bd = date_from_activity_id(bag_id)
        if pd.notna(ts):
            future = ts.normalize() > today
            far = pd.notna(bd) and (ts.normalize() - bd).days > ACTIVITY_ID_LAG_DAYS * 6
            if future or far:
                why = "beyond today" if future else (
                    f"differs from bag-id-encoded date ({bd.date()}) by "
                    f"{(ts.normalize() - bd).days} days"
                )
                _push(queue, sheet="bag_application", row_index=int(idx),
                      record_id=str(bag_id), anomaly_type=5,
                      description=f"Implausible Timestamp ({why}).",
                      field="Timestamp", original_value=row.get("Timestamp"),
                      suggested_action="Verify and correct timestamp.",
                      severity="MEDIUM", status="REVIEW_REQUIRED")

        if pd.notna(bag_id) and bag_id not in prod_bag_set:
            _push(queue, sheet="bag_application", row_index=int(idx),
                  record_id=str(bag_id), anomaly_type=7,
                  description="bag_id is not present in bag_production.",
                  field="bag_id", original_value=bag_id,
                  suggested_action="Verify origin; add to bag_production or discard.",
                  severity="HIGH", status="REVIEW_REQUIRED")

        pw = prod_weights.get(bag_id)
        aw = row.get("bag_weight")
        if pw is not None and pd.notna(aw) and pw > 0:
            try:
                diff = abs(float(aw) - float(pw)) / float(pw)
            except Exception:
                diff = 0
            if diff > WEIGHT_DISCREPANCY_PCT:
                _push(queue, sheet="bag_application", row_index=int(idx),
                      record_id=str(bag_id), anomaly_type=8,
                      description=(f"bag_weight={aw} differs from production "
                                   f"weight={pw:.2f} by {diff*100:.2f}%."),
                      field="bag_weight", original_value=aw,
                      suggested_action="Investigate scale calibration / bag identity.",
                      severity="MEDIUM", status="REVIEW_REQUIRED")

        if bag_id in multi:
            _push(queue, sheet="bag_application", row_index=int(idx),
                  record_id=str(bag_id), anomaly_type=10,
                  description="bag_id appears in more than one application batch.",
                  field="bag_id", original_value=bag_id,
                  suggested_action="Each bag must be applied in only one batch.",
                  severity="HIGH", status="REVIEW_REQUIRED")

    # TYPE 9 — batch sum mismatch
    if {"bag_id", "weight", "production_id"}.issubset(bag_prod.columns):
        sums = (bag_prod.dropna(subset=["weight"])
                .drop_duplicates("bag_id", keep="first")
                .groupby("production_id")["weight"].sum())
    else:
        sums = pd.Series(dtype=float)
    for idx, row in prod.iterrows():
        target = row.get("biochar_amount_kg")
        if pd.isna(target) or target == 0:
            continue
        actual = float(sums.get(row.get("activity_id"), 0.0))
        diff_abs = abs(actual - float(target))
        diff_pct = diff_abs / float(target)
        if diff_abs > BATCH_SUM_KG and diff_pct > BATCH_SUM_PCT:
            _push(queue, sheet="biochar_production", row_index=int(idx),
                  record_id=str(row.get("activity_id", "")),
                  anomaly_type=9,
                  description=(f"Σ(bag weights)={actual:.2f} kg vs "
                               f"biochar_amount_kg={float(target):.2f} kg "
                               f"(Δ={diff_abs:.2f} kg, {diff_pct*100:.2f}%)."),
                  field="biochar_amount_kg", original_value=target,
                  suggested_action="Reconcile bag inventory or batch total.",
                  severity="MEDIUM", status="REVIEW_REQUIRED")

    queue_df = (pd.DataFrame(queue) if queue
                else pd.DataFrame(columns=[
                    "detected_at", "sheet", "row_index", "record_id",
                    "anomaly_type", "anomaly_name", "description", "field",
                    "original_value", "suggested_action", "severity", "status",
                ]))

    # Useful derived columns for the dashboard
    if "Timestamp" in prod.columns:
        prod["_date"] = pd.to_datetime(prod["Timestamp"], errors="coerce").dt.date
    if "feedstock_amount" in prod.columns and "biochar_amount_kg" in prod.columns:
        prod["_yield_pct"] = (prod["biochar_amount_kg"]
                              / prod["feedstock_amount"]) * 100
    if not sums.empty:
        prod["_bag_sum_kg"] = prod["activity_id"].map(sums)
        if "feedstock_amount" in prod.columns:
            prod["_bag_yield_pct"] = (prod["_bag_sum_kg"]
                                      / prod["feedstock_amount"]) * 100

    if "Timestamp" in app.columns:
        app["_date"] = pd.to_datetime(app["Timestamp"], errors="coerce").dt.date

    return DataBundle(
        prod=prod, bag_prod=bag_prod, app=app, bag_app=bag_app,
        queue=queue_df, autofix_count=autofix,
        raw_sizes={k: len(v) for k, v in raw.items()},
    )


@st.cache_data(ttl=300, show_spinner=False)
def load_bundle(sheet_url: str) -> DataBundle:
    """Top-level entry: fetch + validate, cached for 5 minutes."""
    raw = fetch_raw_sheets(sheet_url)
    return _validate(raw)


def clear_cache() -> None:
    fetch_raw_sheets.clear()
    load_bundle.clear()
