# ☪ Bursa Shariah Screener

A free, open-source Shariah compliance screener for Bursa Malaysia stocks — built with Python, yfinance, and Streamlit. Applies AAOIFI (Accounting and Auditing Organisation for Islamic Financial Institutions) screening methodology.

<img width="1905" height="1027" alt="image" src="https://github.com/user-attachments/assets/b8c647ee-d9fc-489c-b83a-7129ff303e99" />

<img width="1453" height="619" alt="image" src="https://github.com/user-attachments/assets/955deeba-2c27-4e2c-bc9c-68b923a9a5bd" />


## Why This Exists

There is no free, well-built, regularly-updated Shariah screener for KLSE stocks. This project fills that gap for Malaysian Muslim retail investors.

---

## Features

- **Live data** from Yahoo Finance via `yfinance` (cached hourly)
- **4 AAOIFI screening criteria** applied automatically:
  1. Business activity exclusion (banking, gambling, alcohol, tobacco, etc.)
  2. Debt ratio: Total Debt / Market Cap < 33%
  3. Cash & receivables ratio: (Cash + Receivables) / Market Cap < 33%
  4. Revenue purification: Interest Income / Total Revenue < 5% (halal) or 5–33% (purify)
- **3-tier verdicts**: HALAL ✓ / PURIFY ◐ (with purification %) / NOT COMPLIANT ✗
- **Interactive dashboard** with charts, filters, and per-stock breakdown
- **33 KLSE stocks** across sectors (easily extendable)

---

## Project Structure

```
bursa_screener/
├── scraper.py          # yfinance data fetcher for KLSE tickers
├── screener.py         # AAOIFI screening engine (4 criteria)
├── app.py              # Streamlit dashboard
├── requirements.txt
└── README.md
```

---

## Quickstart

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run the screener CLI (optional - prints results to terminal)
python screener.py

# 3. Launch the dashboard
streamlit run app.py
```

Dashboard will open at `http://localhost:8501`

---

## Architecture

```
Yahoo Finance API
      │
      ▼
 scraper.py          ← fetches balance sheet, income statement, market data
      │               for ~33 KLSE tickers via yfinance
      ▼
 screener.py         ← applies AAOIFI 4-criteria engine
      │               outputs: verdict + ratios + purification %
      ▼
 app.py (Streamlit)  ← dashboard: KPIs, charts, filterable table, detail panel
```

---

## AAOIFI Methodology

### 1. Business Activity Screen
Hard exclusion for any company operating primarily in:
- Conventional banking, insurance, credit services
- Gambling and gaming
- Alcohol production/distribution
- Tobacco
- Adult entertainment
- Weapons/defense manufacturing

### 2. Debt Ratio
`Total Debt / Market Capitalization < 33%`

Measures leverage. Companies with excessive debt relative to their market value fail.

### 3. Cash & Interest-Bearing Securities
`(Cash + Receivables) / Market Capitalization < 33%`

Screens for companies that derive significant value from interest-bearing instruments.

### 4. Revenue Purification
`Interest Income / Total Revenue`:
- **< 5%** → Fully Halal ✓
- **5% – 33%** → Conditionally compliant, purification required ◐
  - The purification % shown = the % of dividends/income to donate to charity
- **> 33%** → Not compliant ✗

---

## Extending the Stock Universe

Add tickers to `BURSA_TICKERS` in `scraper.py`:
```python
BURSA_TICKERS = {
    "COMPANY NAME": "TICKER.KL",  # Yahoo Finance format
    ...
}
```

Find Yahoo Finance tickers: search `<stock_code>.KL` (e.g., `1155.KL` for Maybank).

---

## Limitations & Disclaimer

- Financial data sourced from Yahoo Finance — may have delays or gaps
- AAOIFI ratios use market cap as denominator (some scholars use total assets)
- Business activity keyword screening is heuristic-based — manual review recommended
- **Not a fatwa. Not financial advice.** Consult a qualified Islamic finance scholar for personal rulings.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Data Fetch | `yfinance` |
| Data Processing | `pandas`, `numpy` |
| Screening Engine | Pure Python (`screener.py`) |
| Dashboard | `streamlit` |
| Charts | `plotly` |

---

## Roadmap

- [ ] Add SC Malaysia's official Shariah-compliant list as a cross-reference
- [ ] Expand universe to 100+ stocks
- [ ] Add historical ratio trending (pass/fail drift over time)
- [ ] Email/Telegram alerts when a stock changes verdict
- [ ] Export to PDF report
- [ ] Deploy to Streamlit Cloud

---

Built by **Ikhmal** · KL, Malaysia  
Methodology: [AAOIFI Shariah Standards](https://aaoifi.com)
#
