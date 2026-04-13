"""
scraper.py
Fetches financial data for Bursa Malaysia stocks via yfinance.
Bursa tickers on Yahoo Finance use the suffix .KL
"""

import yfinance as yf
import pandas as pd
import time
import logging

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger(__name__)

# ── KLSE universe ────────────────────────────────────────────────────────────
# Curated list: mix of blue-chips, mid-caps, known halal and non-halal names
BURSA_TICKERS = {
    # Financials (banks — expected to fail Islamic screening)
    "MAYBANK":   "1155.KL",
    "CIMB":      "1023.KL",
    "PUBLIC BK": "1295.KL",
    "RHB BANK":  "1066.KL",
    "HLBANK":    "5819.KL",
    # Plantations
    "IOI CORP":  "1961.KL",
    "KLK":       "2445.KL",
    "SIMEPLT":   "5285.KL",
    "BPLANT":    "5254.KL",
    # Technology
    "MY EG":     "0138.KL",
    "INARI":     "0166.KL",
    "FRONTKN":   "0128.KL",
    "MMSV":      "0241.KL",
    "REVENUE":   "0200.KL",
    # Healthcare
    "IHH":       "5225.KL",
    "KPJ":       "5878.KL",
    "PHARMNIAG": "7081.KL",
    # Consumer
    "NESTLE":    "4707.KL",
    "DLADY":     "3026.KL",
    "QL":        "7084.KL",
    "PADINI":    "7052.KL",
    # Utilities
    "TENAGA":    "5347.KL",
    "YTLPOWER":  "6742.KL",
    "PETRONAS":  "5183.KL",
    # Telco
    "MAXIS":     "6012.KL",
    "DIGI":      "6947.KL",
    "AXIATA":    "6888.KL",
    # Construction / Infra
    "GAMUDA":    "5398.KL",
    "IJM":       "3336.KL",
    "SUNCON":    "5263.KL",
    # Gaming (expected to fail — haram sector)
    "GENTING":   "3182.KL",
    "GENTINGM":  "4715.KL",
    # REITs
    "KLCC":      "5235SS.KL",
    "PAVREIT":   "5212.KL",
}

# Sectors that auto-fail business activity screening (AAOIFI)
EXCLUDED_SECTORS = {
    "Financial Services", "Banks", "Insurance", "Diversified Financial Services",
    "Consumer Finance", "Capital Markets",
    "Beverages—Brewers", "Distillers & Vintners",
    "Gambling", "Casinos & Gaming",
    "Tobacco",
    "Adult Entertainment",
    "Defense",
    "Pork",
}

# Keywords in company name / business summary that trigger exclusion
EXCLUDED_KEYWORDS = [
    "bank", "insurance", "gaming", "casino", "genting", "alcohol",
    "tobacco", "brewery", "distill", "pork", "wine", "beer", "spirits",
    "betting", "lottery", "weapons", "defense"
]


def fetch_stock_data(ticker_symbol: str, company_name: str) -> dict:
    """Fetch financials for a single ticker. Returns a flat dict."""
    try:
        t = yf.Ticker(ticker_symbol)
        info = t.info

        # Basic identity
        row = {
            "ticker":        ticker_symbol,
            "name":          info.get("longName") or company_name,
            "sector":        info.get("sector", "Unknown"),
            "industry":      info.get("industry", "Unknown"),
            "currency":      info.get("currency", "MYR"),
            "price":         info.get("currentPrice") or info.get("regularMarketPrice"),
            "market_cap":    info.get("marketCap"),
            "description":   (info.get("longBusinessSummary") or "").lower(),
        }

        # ── Balance sheet items ───────────────────────────────────────────
        bs = t.balance_sheet
        if bs is not None and not bs.empty:
            latest = bs.iloc[:, 0]  # most recent period

            total_debt = 0
            for key in ["Total Debt", "Long Term Debt", "Short Long Term Debt"]:
                val = latest.get(key)
                if val is not None and not pd.isna(val):
                    total_debt = max(total_debt, float(val))
            row["total_debt"] = total_debt

            cash = 0
            for key in ["Cash And Cash Equivalents", "Cash Cash Equivalents And Short Term Investments"]:
                val = latest.get(key)
                if val is not None and not pd.isna(val):
                    cash = float(val)
                    break
            row["cash_and_equivalents"] = cash

            receivables = 0
            for key in ["Net Receivables", "Accounts Receivable"]:
                val = latest.get(key)
                if val is not None and not pd.isna(val):
                    receivables = float(val)
                    break
            row["receivables"] = receivables

            total_assets = latest.get("Total Assets")
            row["total_assets"] = float(total_assets) if total_assets and not pd.isna(total_assets) else None

        else:
            row.update({"total_debt": None, "cash_and_equivalents": None,
                        "receivables": None, "total_assets": None})

        # ── Income statement items ────────────────────────────────────────
        inc = t.financials
        if inc is not None and not inc.empty:
            latest_inc = inc.iloc[:, 0]
            total_rev = latest_inc.get("Total Revenue")
            row["total_revenue"] = float(total_rev) if total_rev and not pd.isna(total_rev) else None

            interest_exp = latest_inc.get("Interest Expense")
            row["interest_income_expense"] = abs(float(interest_exp)) if interest_exp and not pd.isna(interest_exp) else 0.0
        else:
            row["total_revenue"] = None
            row["interest_income_expense"] = 0.0

        log.info(f"  ✓ {company_name} ({ticker_symbol})")
        return row

    except Exception as e:
        log.warning(f"  ✗ {company_name} ({ticker_symbol}): {e}")
        return {
            "ticker": ticker_symbol, "name": company_name,
            "sector": "Unknown", "industry": "Unknown",
            "price": None, "market_cap": None,
            "total_debt": None, "cash_and_equivalents": None,
            "receivables": None, "total_assets": None,
            "total_revenue": None, "interest_income_expense": 0.0,
            "description": "", "currency": "MYR",
        }


def scrape_all(delay: float = 0.5) -> pd.DataFrame:
    """Fetch data for all tickers and return a DataFrame."""
    log.info(f"Fetching {len(BURSA_TICKERS)} tickers from Yahoo Finance...")
    rows = []
    for name, ticker in BURSA_TICKERS.items():
        rows.append(fetch_stock_data(ticker, name))
        time.sleep(delay)

    df = pd.DataFrame(rows)
    log.info(f"Fetched {len(df)} stocks.")
    return df


if __name__ == "__main__":
    df = scrape_all()
    df.to_csv("raw_data.csv", index=False)
    print(df[["name", "sector", "market_cap", "total_debt"]].to_string())
