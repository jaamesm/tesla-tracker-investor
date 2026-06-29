# tesla-tracker-investor

**An automated, AI-driven paper-trading engine tracking a dynamic-leverage TSLA strategy from a virtual £100 baseline.**

![Tracker Status](https://github.com/jaamesm/tesla-tracker-investor/actions/workflows/tracker.yml/badge.svg)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## 1. Project Overview

**tesla-tracker-investor** is a zero-brokerage-dependency paper trading engine. It runs on a live daily heartbeat to track how a baseline **£100** compounds under an optimised dynamic leverage strategy applied to Tesla (TSLA).

No real capital, broker API, or order execution is involved at any stage — every position, fill, and balance update is simulated and recorded directly within this repository. Performance is tracked natively via version-controlled **JSON** and **CSV** log files, giving a fully transparent, auditable history of every rebalancing decision the model has made since inception.

The system is designed to answer one question with discipline and rigour: *how does a small, fixed amount of capital compound over time under a rules-based, signal-driven exposure strategy — without any of the operational noise of real trading?*

---

## 2. Investment System Methodology

### 2.1 Asset Allocation Strategy

The model holds a **permanent, cash-backed equity position** in TSLA, modulated within a narrow leverage corridor:

| Parameter | Value |
|---|---|
| Baseline exposure | **1.00x** |
| Maximum leverage ceiling | **1.15x** |
| Minimum exposure floor | **1.00x** |

This corridor was not chosen arbitrarily. Backtesting across the model's development cycle showed:

- **Wider floors below 1.00x** (e.g. 0.80x or 0.90x) severely penalised long-run compounding. TSLA's structural upside bias over the backtest period meant that any meaningful reduction below full exposure consistently cost more in foregone gains than it saved in avoided drawdowns.
- **Wider corridors in general** bled value to transaction friction — more frequent, larger rebalancing moves increased simulated slippage and turnover without a proportionate improvement in risk-adjusted return.

The result is a **narrow, permanent-exposure corridor**: the model is never meaningfully short its own conviction, and leverage is used only as a precision instrument to lean further into high-conviction regimes — never to retreat from the asset entirely.

### 2.2 Alpha Modifiers

Three independent signal layers adjust exposure within the 1.00x–1.15x corridor each trading day:

**Upside Sentiment Acceleration**
Uses **RoBERTa-based AI conviction scores**, derived from daily sentiment analysis of news and market commentary, to scale exposure upward as sentiment moves into ultra-bullish territory. Higher conviction scores push leverage progressively toward the 1.15x ceiling.

**Downside Volatility Mitigation**
When sentiment turns negative, the model does not cut exposure abruptly. Instead, the size of the correction is scaled against a **short-to-long-term volatility ratio** — the 10-day rolling return variance relative to the 60-day rolling return variance. This smooths the response: a negative sentiment reading during a genuinely calm volatility regime produces a gentler reduction than the same reading during a regime of elevated short-term turbulence.

**RSI Exhaustion Switch**
A strict technical overlay sits on top of both modifiers. If the **14-day RSI drops below 30**, the model is forced back to a **minimum 1.00x position**, overriding any sentiment-driven reduction. This is designed to capitalise on local market capitulation — the model refuses to be underweight TSLA at the precise moments oversold conditions have historically preceded sharp reversions.

---

## 3. Repository Architecture

```
tesla-tracker-investor/
├── .github/
│   └── workflows/
│       └── tracker.yml                  — automated cron scheduling workflow
├── src/
│   └── local_live_tracker.py            — main execution script: market data parsing,
│                                           signal computation, and rebalancing math
├── data/
│   ├── live_portfolio.json              — persistent state engine: cash balance,
│   │                                       shares held, spot price, current leverage
│   ├── live_execution_log.csv           — continuous transaction ledger, full
│   │                                       historical timeline of every rebalance
│   └── quantpad_roberta_signals.csv     — pipeline source matrix: daily AI
│                                           conviction scores feeding the sentiment layer
├── README.md
└── requirements.txt
```

---

## 4. Automation & Infrastructure

The engine runs **completely serverless**, with no persistent compute, database, or hosting cost of any kind.

- **Trigger:** a scheduled cron job inside `.github/workflows/tracker.yml`, firing automatically every weekday at **3:45 PM EST (20:45 UTC)** — 15 minutes before the US market close, ensuring the day's price action is effectively final before the model computes its rebalance.
  > Note: EST is used as the reference time zone in the schedule definition; during daylight saving (EDT), the equivalent local close-adjacent trigger shifts by one hour.
- **Execution:** `src/local_live_tracker.py` pulls the day's market data and AI conviction signal, computes the target leverage for the session, and updates the simulated position.
- **State persistence:** the workflow is granted explicit `contents: write` permissions, allowing it to commit and push the updated `live_portfolio.json` and `live_execution_log.csv` directly back to the repository — fully on autopilot, with no manual intervention required at any stage.

---

## 5. How to Run & Test

### 5.1 Manual trigger via GitHub Actions

1. Go to the **Actions** tab of this repository.
2. Select the **tracker** workflow from the left-hand sidebar.
3. Click **Run workflow** to execute an out-of-schedule cycle on demand.

This is useful for verifying the pipeline end-to-end without waiting for the next scheduled run, or for re-running a cycle after a fix.

### 5.2 Local execution

**Prerequisites:**

| Requirement | Version |
|---|---|
| Python | 3.10+ |
| pandas | latest |
| numpy | latest |
| yfinance | latest |

```bash
pip install pandas numpy yfinance
python src/local_live_tracker.py
```

Running locally executes the same logic as the scheduled workflow, but will not commit the resulting state back to the repository unless run with the appropriate git credentials configured.

---

## Disclaimer

This repository is a research and educational simulation tool. All positions, balances, and performance figures are **paper-traded** against a virtual starting balance — no real capital is deployed, and no brokerage account is connected at any point. Nothing in this repository constitutes financial advice or a recommendation to trade any security.

---

Built by [James Murphy](https://github.com/jaamesm) — MMath Mathematics, University of York. Part of a broader quantitative finance portfolio alongside [options-pricer](https://github.com/jaamesm/options-pricer).
