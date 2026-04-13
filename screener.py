"""
screener.py
AAOIFI-based Shariah screening engine for Bursa Malaysia stocks.

Criteria applied:
  1. Business Activity Exclusion  — sector/keyword blocklist
  2. Debt Ratio                   — total debt / market cap < 33%
  3. Cash & Interest-Bearing Sec  — (cash + receivables) / market cap < 33%
  4. Revenue Purification         — interest income / total revenue < 5%
                                    (if 5–33%: conditionally compliant with purification)

Verdict logic:
  HALAL          — passes all 4 criteria
  PURIFY         — passes sectors + ratios, but interest revenue 5–33% (needs purification donation)
  NOT COMPLIANT  — fails any hard criterion
  INSUFFICIENT DATA — missing financials to screen
"""

import pandas as pd
import numpy as np
from dataclasses import dataclass, field, asdict
from typing import Optional
import logging

log = logging.getLogger(__name__)

# ── Thresholds (AAOIFI standard) ─────────────────────────────────────────────
DEBT_RATIO_THRESHOLD        = 0.33   # total debt / market cap
CASH_RATIO_THRESHOLD        = 0.33   # (cash + receivables) / market cap
INTEREST_HARD_THRESHOLD     = 0.33   # > 33%  → not compliant
INTEREST_PURIFY_THRESHOLD   = 0.05   # 5–33%  → compliant with purification
# < 5%  → fully compliant

# Excluded sectors (AAOIFI business activity screen)
EXCLUDED_SECTORS = {
    "financial services", "banks", "insurance", "diversified financial services",
    "consumer finance", "capital markets", "credit services",
    "beverages—brewers", "distillers & vintners", "beverages - brewers",
    "gambling", "casinos & gaming",
    "tobacco",
    "adult entertainment",
    "defense",
}

EXCLUDED_KEYWORDS = [
    "bank", "banking", "insurance", "gaming", "casino", "genting",
    "alcohol", "tobacco", "brewery", "distill", "pork", "wine",
    "beer", "spirits", "betting", "lottery", "weapon", "defense", "armament"
]

VERDICT_HALAL   = "HALAL"
VERDICT_PURIFY  = "PURIFY"
VERDICT_FAIL    = "NOT COMPLIANT"
VERDICT_NODATA  = "INSUFFICIENT DATA"


@dataclass
class ScreenResult:
    ticker:               str
    name:                 str
    sector:               str
    industry:             str
    price:                Optional[float]
    market_cap:           Optional[float]
    currency:             str

    # Raw financials
    total_debt:           Optional[float]
    cash_and_equivalents: Optional[float]
    receivables:          Optional[float]
    total_assets:         Optional[float]
    total_revenue:        Optional[float]
    interest_income_expense: float

    # Computed ratios
    debt_ratio:           Optional[float] = None
    cash_ratio:           Optional[float] = None
    interest_revenue_ratio: Optional[float] = None
    purification_pct:     Optional[float] = None   # % of income to donate

    # Per-criterion results
    pass_sector:          Optional[bool] = None
    pass_debt:            Optional[bool] = None
    pass_cash:            Optional[bool] = None
    pass_interest:        Optional[bool] = None   # None = no data

    # Failure reasons
    fail_reasons:         list = field(default_factory=list)

    # Final verdict
    verdict:              str = VERDICT_NODATA
    verdict_color:        str = "#6b7280"   # CSS color for UI


def _safe(val, default=None):
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return default
    return val


def screen_stock(row: dict) -> ScreenResult:
    r = ScreenResult(
        ticker=row["ticker"],
        name=row["name"],
        sector=row.get("sector", "Unknown"),
        industry=row.get("industry", "Unknown"),
        price=_safe(row.get("price")),
        market_cap=_safe(row.get("market_cap")),
        currency=row.get("currency", "MYR"),
        total_debt=_safe(row.get("total_debt")),
        cash_and_equivalents=_safe(row.get("cash_and_equivalents")),
        receivables=_safe(row.get("receivables")),
        total_assets=_safe(row.get("total_assets")),
        total_revenue=_safe(row.get("total_revenue")),
        interest_income_expense=_safe(row.get("interest_income_expense"), 0.0),
    )
    desc = str(row.get("description", "")).lower()

    # ── 1. Business Activity Screen ──────────────────────────────────────────
    sector_lower = r.sector.lower()
    industry_lower = r.industry.lower()

    sector_fail = sector_lower in EXCLUDED_SECTORS or industry_lower in EXCLUDED_SECTORS
    keyword_fail = any(kw in desc or kw in r.name.lower() for kw in EXCLUDED_KEYWORDS)

    r.pass_sector = not (sector_fail or keyword_fail)
    if not r.pass_sector:
        reason = f"Excluded sector/activity: {r.sector}"
        if keyword_fail and not sector_fail:
            reason = f"Business activity flag: keyword match in description"
        r.fail_reasons.append(reason)

    # ── 2. Debt Ratio ────────────────────────────────────────────────────────
    if r.total_debt is not None and r.market_cap and r.market_cap > 0:
        r.debt_ratio = r.total_debt / r.market_cap
        r.pass_debt = r.debt_ratio < DEBT_RATIO_THRESHOLD
        if not r.pass_debt:
            r.fail_reasons.append(
                f"Debt ratio {r.debt_ratio:.1%} exceeds 33% threshold"
            )
    else:
        r.pass_debt = None  # insufficient data

    # ── 3. Cash & Receivables Ratio ──────────────────────────────────────────
    cash = r.cash_and_equivalents or 0.0
    recv = r.receivables or 0.0
    if r.market_cap and r.market_cap > 0 and (cash > 0 or recv > 0):
        r.cash_ratio = (cash + recv) / r.market_cap
        r.pass_cash = r.cash_ratio < CASH_RATIO_THRESHOLD
        if not r.pass_cash:
            r.fail_reasons.append(
                f"Cash+receivables ratio {r.cash_ratio:.1%} exceeds 33% threshold"
            )
    else:
        r.pass_cash = None

    # ── 4. Interest / Revenue (Purification) ─────────────────────────────────
    if r.total_revenue and r.total_revenue > 0:
        interest = r.interest_income_expense or 0.0
        r.interest_revenue_ratio = interest / r.total_revenue
        r.purification_pct = r.interest_revenue_ratio * 100  # % to donate

        if r.interest_revenue_ratio >= INTEREST_HARD_THRESHOLD:
            r.pass_interest = False
            r.fail_reasons.append(
                f"Interest income {r.interest_revenue_ratio:.1%} exceeds 33% hard limit"
            )
        elif r.interest_revenue_ratio >= INTEREST_PURIFY_THRESHOLD:
            r.pass_interest = True   # passes but needs purification
        else:
            r.pass_interest = True
    else:
        r.pass_interest = None

    # ── Final Verdict ─────────────────────────────────────────────────────────
    has_data = any(x is not None for x in [r.pass_debt, r.pass_cash, r.pass_interest])

    if not r.pass_sector:
        r.verdict = VERDICT_FAIL
        r.verdict_color = "#ef4444"

    elif not has_data:
        r.verdict = VERDICT_NODATA
        r.verdict_color = "#6b7280"

    elif r.pass_debt is False or r.pass_cash is False or r.pass_interest is False:
        r.verdict = VERDICT_FAIL
        r.verdict_color = "#ef4444"

    elif (r.interest_revenue_ratio is not None and
          r.interest_revenue_ratio >= INTEREST_PURIFY_THRESHOLD):
        r.verdict = VERDICT_PURIFY
        r.verdict_color = "#f59e0b"

    else:
        r.verdict = VERDICT_HALAL
        r.verdict_color = "#10b981"

    return r


def run_screening(df: pd.DataFrame) -> pd.DataFrame:
    """Screen all rows and return a results DataFrame."""
    results = [screen_stock(row) for row in df.to_dict(orient="records")]
    out = pd.DataFrame([asdict(r) for r in results])

    # Summary log
    counts = out["verdict"].value_counts()
    log.info("=== Screening complete ===")
    for verdict, count in counts.items():
        log.info(f"  {verdict}: {count}")

    return out


def summary_stats(df: pd.DataFrame) -> dict:
    """Return summary counts for dashboard metrics."""
    total = len(df)
    halal   = (df["verdict"] == VERDICT_HALAL).sum()
    purify  = (df["verdict"] == VERDICT_PURIFY).sum()
    fail    = (df["verdict"] == VERDICT_FAIL).sum()
    nodata  = (df["verdict"] == VERDICT_NODATA).sum()
    return {
        "total":   total,
        "halal":   int(halal),
        "purify":  int(purify),
        "fail":    int(fail),
        "nodata":  int(nodata),
        "halal_pct": round(halal / total * 100, 1) if total else 0,
    }


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        df_raw = pd.read_csv(sys.argv[1])
    else:
        from scraper import scrape_all
        df_raw = scrape_all()

    df_results = run_screening(df_raw)
    print(df_results[["name", "sector", "verdict", "debt_ratio", "interest_revenue_ratio"]].to_string())
