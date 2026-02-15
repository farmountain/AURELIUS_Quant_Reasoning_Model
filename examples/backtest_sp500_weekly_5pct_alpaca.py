#!/usr/bin/env python3
"""Backtest weekly threshold strategies on S&P 500 symbols using Alpaca daily bars.

Supported strategies:
- trend_5: If prior week was up >= +5%, long; if down <= -5%, short.
- mr_ladder_5_10: Mean-reversion ladder
    - prior week <= -5%  => long 1 portion
    - prior week <= -10% => long 2 portions
    - prior week >= +5%  => short 1 portion
    - prior week >= +10% => short 2 portions

Portfolio construction:
- Equal-weight across all active weekly signals.
- Rebalanced weekly.
- No transaction costs/slippage in this simplified version.

Notes:
- User requested "Fortune 500". This script uses S&P 500 constituents as a practical ticker proxy.
- Requires Alpaca Data API credentials in environment variables:
  APCA_API_KEY_ID, APCA_API_SECRET_KEY
"""

from __future__ import annotations

import argparse
import json
import math
import os
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from io import StringIO
from pathlib import Path
from typing import Dict, Iterable
from urllib.parse import urlencode
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

SP500_CONSTITUENTS_CSV = "https://datahub.io/core/s-and-p-500-companies/r/constituents.csv"
ALPACA_BARS_URL = "https://data.alpaca.markets/v2/stocks/bars"


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    weekly_returns: pd.Series
    symbol_stats: pd.DataFrame


def _get_creds() -> tuple[str, str]:
    key = os.getenv("APCA_API_KEY_ID")
    secret = os.getenv("APCA_API_SECRET_KEY")
    if not key or not secret:
        raise RuntimeError(
            "Missing Alpaca credentials. Set APCA_API_KEY_ID and APCA_API_SECRET_KEY."
        )
    return key, secret


def fetch_sp500_symbols(limit: int | None = None) -> list[str]:
    req = Request(
        SP500_CONSTITUENTS_CSV,
        headers={"Accept": "text/csv"},
    )
    with urlopen(req, timeout=30) as resp:
        csv_text = resp.read().decode("utf-8")

    df = pd.read_csv(StringIO(csv_text))
    if "Symbol" not in df.columns:
        raise RuntimeError("Unexpected S&P 500 constituents CSV format")

    symbols = [str(s).strip().upper() for s in df["Symbol"].dropna().tolist()]

    # Deduplicate, keep order
    seen = set()
    unique_symbols = []
    for s in symbols:
        if s and s not in seen:
            seen.add(s)
            unique_symbols.append(s)

    if limit is not None and limit > 0:
        return unique_symbols[:limit]
    return unique_symbols


def load_symbols_from_file(path: str, limit: int | None = None) -> list[str]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Symbols file not found: {path}")

    if p.suffix.lower() == ".csv":
        df = pd.read_csv(p)
        candidates = ["symbol", "Symbol", "ticker", "Ticker"]
        col = next((c for c in candidates if c in df.columns), df.columns[0])
        symbols = [str(s).strip().upper() for s in df[col].dropna().tolist()]
    else:
        symbols = [
            line.strip().upper()
            for line in p.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]

    seen = set()
    out = []
    for s in symbols:
        if s and s not in seen:
            seen.add(s)
            out.append(s)

    if limit is not None and limit > 0:
        return out[:limit]
    return out


def chunked(items: Iterable[str], n: int) -> Iterable[list[str]]:
    batch: list[str] = []
    for x in items:
        batch.append(x)
        if len(batch) >= n:
            yield batch
            batch = []
    if batch:
        yield batch


def fetch_daily_bars(symbols: list[str], start: str, end: str, feed: str = "iex") -> pd.DataFrame:
    api_key, api_secret = _get_creds()

    rows: list[dict] = []
    for batch in chunked(symbols, 50):
        active_batch = list(batch)

        while active_batch:
            params = {
                "symbols": ",".join(active_batch),
                "start": start,
                "end": end,
                "timeframe": "1Day",
                "feed": feed,
                "adjustment": "all",
                "sort": "asc",
                "limit": 10000,
            }

            page_token = None
            try:
                while True:
                    if page_token:
                        params["page_token"] = page_token
                    elif "page_token" in params:
                        del params["page_token"]

                    url = f"{ALPACA_BARS_URL}?{urlencode(params)}"
                    req = Request(
                        url,
                        headers={
                            "APCA-API-KEY-ID": api_key,
                            "APCA-API-SECRET-KEY": api_secret,
                            "Accept": "application/json",
                        },
                    )

                    with urlopen(req, timeout=60) as resp:
                        payload = json.loads(resp.read().decode("utf-8"))

                    bars_by_symbol: Dict[str, list[dict]] = payload.get("bars", {})
                    for sym, bars in bars_by_symbol.items():
                        for b in bars:
                            rows.append(
                                {
                                    "symbol": sym,
                                    "timestamp": pd.to_datetime(b["t"], utc=True),
                                    "open": float(b["o"]),
                                    "high": float(b["h"]),
                                    "low": float(b["l"]),
                                    "close": float(b["c"]),
                                    "volume": float(b.get("v", 0.0)),
                                }
                            )

                    page_token = payload.get("next_page_token")
                    if not page_token:
                        break

                break
            except HTTPError as e:
                body = e.read().decode("utf-8", errors="ignore")
                if e.code == 400 and "invalid symbol:" in body:
                    invalid_symbol = body.split("invalid symbol:", 1)[1].strip().strip('"{} ')
                    invalid_symbol = invalid_symbol.replace('"', "").replace("}", "")
                    if invalid_symbol in active_batch:
                        active_batch.remove(invalid_symbol)
                        print(f"Skipping invalid symbol from Alpaca: {invalid_symbol}")
                        continue
                raise

    if not rows:
        raise RuntimeError("No bars returned from Alpaca for requested symbols/date range")

    df = pd.DataFrame(rows).sort_values(["symbol", "timestamp"]).reset_index(drop=True)
    return df


def weekly_signal_backtest(
    df: pd.DataFrame,
    initial_capital: float = 100_000.0,
    strategy_mode: str = "trend_5",
) -> BacktestResult:
    if df.empty:
        raise ValueError("Input data is empty")

    x = df.copy()
    x["date"] = x["timestamp"].dt.tz_convert("UTC").dt.tz_localize(None)
    x = x.sort_values(["symbol", "date"])

    # Friday-based weeks to align with market week close.
    weekly_close = (
        x.set_index("date")
        .groupby("symbol")["close"]
        .resample("W-FRI")
        .last()
        .rename("close")
        .reset_index()
    )

    if weekly_close.empty:
        raise RuntimeError("No weekly bars produced from daily input")

    weekly_close["weekly_return"] = weekly_close.groupby("symbol")["close"].pct_change(fill_method=None)

    # Signal for week t uses return from week t-1
    weekly_close["signal"] = 0.0
    prev_ret = weekly_close.groupby("symbol")["weekly_return"].shift(1)
    if strategy_mode == "trend_5":
        weekly_close.loc[prev_ret >= 0.05, "signal"] = 1.0
        weekly_close.loc[prev_ret <= -0.05, "signal"] = -1.0
    elif strategy_mode == "mr_ladder_5_10":
        weekly_close.loc[prev_ret <= -0.05, "signal"] = 1.0
        weekly_close.loc[prev_ret <= -0.10, "signal"] = 2.0
        weekly_close.loc[prev_ret >= 0.05, "signal"] = -1.0
        weekly_close.loc[prev_ret >= 0.10, "signal"] = -2.0
    else:
        raise ValueError(f"Unsupported strategy_mode: {strategy_mode}")

    weekly_close["strategy_return_raw"] = weekly_close["signal"] * weekly_close["weekly_return"]

    # Equal weight over active names each week
    def _portfolio_return(g: pd.DataFrame) -> float:
        active = g[g["signal"] != 0]
        if active.empty:
            return 0.0
        gross_portions = float(active["signal"].abs().sum())
        if math.isclose(gross_portions, 0.0, abs_tol=1e-12):
            return 0.0
        return float(active["strategy_return_raw"].sum() / gross_portions)

    portfolio_weekly = (
        weekly_close.groupby("date", as_index=True)
        .apply(_portfolio_return, include_groups=False)
        .rename("portfolio_return")
        .sort_index()
    )

    equity = (1.0 + portfolio_weekly.fillna(0.0)).cumprod() * float(initial_capital)

    # Per-symbol diagnostics
    sym = weekly_close.copy()
    sym["active"] = (sym["signal"] != 0).astype(int)
    symbol_stats = (
        sym.groupby("symbol", as_index=False)
        .agg(
            signal_weeks=("active", "sum"),
            avg_weekly_return=("strategy_return_raw", "mean"),
            cumulative_return=("strategy_return_raw", lambda s: (1.0 + s.fillna(0.0)).prod() - 1.0),
        )
        .sort_values("cumulative_return", ascending=False)
        .reset_index(drop=True)
    )

    return BacktestResult(equity_curve=equity, weekly_returns=portfolio_weekly, symbol_stats=symbol_stats)


def normalize_bars_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    required = {"timestamp", "symbol", "open", "high", "low", "close", "volume"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Input bars missing required columns: {sorted(missing)}")

    out = df.copy()
    if np.issubdtype(out["timestamp"].dtype, np.number):
        out["timestamp"] = pd.to_datetime(out["timestamp"], unit="s", utc=True)
    else:
        out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True)

    out["symbol"] = out["symbol"].astype(str).str.upper()
    for c in ["open", "high", "low", "close", "volume"]:
        out[c] = pd.to_numeric(out[c], errors="coerce")

    out = out.dropna(subset=["timestamp", "symbol", "close"]).sort_values(["symbol", "timestamp"]).reset_index(drop=True)
    return out


def max_drawdown(equity_curve: pd.Series) -> float:
    rolling_peak = equity_curve.cummax()
    drawdown = equity_curve / rolling_peak - 1.0
    return float(drawdown.min()) if len(drawdown) else 0.0


def sharpe_ratio(weekly_returns: pd.Series) -> float:
    r = weekly_returns.dropna()
    if len(r) < 2:
        return 0.0
    vol = float(r.std(ddof=1))
    if math.isclose(vol, 0.0, abs_tol=1e-12):
        return 0.0
    return float((r.mean() / vol) * math.sqrt(52.0))


def print_summary(result: BacktestResult, initial_capital: float, strategy_mode: str) -> None:
    eq = result.equity_curve
    wr = result.weekly_returns.fillna(0.0)

    final_equity = float(eq.iloc[-1]) if len(eq) else initial_capital
    total_return = final_equity / initial_capital - 1.0
    mdd = max_drawdown(eq)
    sharpe = sharpe_ratio(wr)
    win_rate = float((wr > 0).mean()) if len(wr) else 0.0

    print(f"\n=== Weekly Strategy Backtest (S&P 500 proxy) [{strategy_mode}] ===")
    print(f"Weeks tested      : {len(wr)}")
    print(f"Initial capital   : ${initial_capital:,.2f}")
    print(f"Final equity      : ${final_equity:,.2f}")
    print(f"Total return      : {total_return * 100:.2f}%")
    print(f"Sharpe (weekly)   : {sharpe:.3f}")
    print(f"Max drawdown      : {mdd * 100:.2f}%")
    print(f"Weekly win rate   : {win_rate * 100:.2f}%")

    top = result.symbol_stats.head(10).copy()
    if not top.empty:
        top["cumulative_return"] = top["cumulative_return"] * 100.0
        print("\nTop 10 symbols by strategy cumulative return (%):")
        print(top[["symbol", "signal_weeks", "cumulative_return"]].to_string(index=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backtest weekly threshold strategy using Alpaca daily bars")
    parser.add_argument("--start", help="ISO timestamp, default: now-1 month UTC")
    parser.add_argument("--end", help="ISO timestamp, default: now UTC")
    parser.add_argument("--feed", default="iex", choices=["iex", "sip"], help="Alpaca data feed")
    parser.add_argument("--input-parquet", help="Use existing Alpaca parquet file instead of API fetch")
    parser.add_argument("--input-csv", help="Use existing Alpaca CSV file instead of API fetch")
    parser.add_argument("--symbols-limit", type=int, default=500, help="How many S&P symbols to include")
    parser.add_argument("--symbols-file", help="Optional .txt/.csv with Fortune 500 tickers")
    parser.add_argument(
        "--strategy",
        default="trend_5",
        choices=["trend_5", "mr_ladder_5_10"],
        help="Strategy mode",
    )
    parser.add_argument("--initial-capital", type=float, default=100000.0)
    parser.add_argument("--out-dir", default="examples/output_alpaca_sp500_weekly_5pct")
    return parser.parse_args()


def default_dates() -> tuple[str, str]:
    end_dt = datetime.now(timezone.utc)
    start_dt = end_dt - timedelta(days=31)
    return start_dt.isoformat().replace("+00:00", "Z"), end_dt.isoformat().replace("+00:00", "Z")


def main() -> int:
    args = parse_args()
    start, end = default_dates()
    start = args.start or start
    end = args.end or end

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.input_parquet:
        print(f"Loading existing Alpaca data: {args.input_parquet}")
        bars = pd.read_parquet(args.input_parquet)
        bars = normalize_bars_dataframe(bars)
        if not args.start and not args.end and not bars.empty:
            end_dt = bars["timestamp"].max()
            start_dt = end_dt - pd.Timedelta(days=31)
            start = start_dt.isoformat().replace("+00:00", "Z")
            end = end_dt.isoformat().replace("+00:00", "Z")
        bars = bars[(bars["timestamp"] >= pd.to_datetime(start, utc=True)) & (bars["timestamp"] <= pd.to_datetime(end, utc=True))]
        print(f"Rows loaded after date filter: {len(bars):,}")
    elif args.input_csv:
        print(f"Loading existing Alpaca data: {args.input_csv}")
        bars = pd.read_csv(args.input_csv)
        bars = normalize_bars_dataframe(bars)
        if not args.start and not args.end and not bars.empty:
            end_dt = bars["timestamp"].max()
            start_dt = end_dt - pd.Timedelta(days=31)
            start = start_dt.isoformat().replace("+00:00", "Z")
            end = end_dt.isoformat().replace("+00:00", "Z")
        bars = bars[(bars["timestamp"] >= pd.to_datetime(start, utc=True)) & (bars["timestamp"] <= pd.to_datetime(end, utc=True))]
        print(f"Rows loaded after date filter: {len(bars):,}")
    else:
        if args.symbols_file:
            print(f"Loading symbols from file: {args.symbols_file}")
            symbols = load_symbols_from_file(args.symbols_file, limit=args.symbols_limit)
            print(f"Symbols loaded (file): {len(symbols)}")
        else:
            print("Fetching S&P 500 symbols...")
            symbols = fetch_sp500_symbols(limit=args.symbols_limit)
            print(f"Symbols loaded (S&P proxy): {len(symbols)}")

        print(f"Fetching Alpaca daily bars from {start} to {end}...")
        bars = fetch_daily_bars(symbols=symbols, start=start, end=end, feed=args.feed)
        print(f"Rows fetched: {len(bars):,}")

    result = weekly_signal_backtest(
        bars,
        initial_capital=args.initial_capital,
        strategy_mode=args.strategy,
    )
    print_summary(result, initial_capital=args.initial_capital, strategy_mode=args.strategy)

    bars_out = out_dir / "alpaca_daily_bars.csv"
    eq_out = out_dir / "equity_curve_weekly.csv"
    ret_out = out_dir / "weekly_returns.csv"
    sym_out = out_dir / "symbol_stats.csv"

    bars.to_csv(bars_out, index=False)
    result.equity_curve.rename("equity").to_csv(eq_out, index_label="week_end")
    result.weekly_returns.rename("portfolio_return").to_csv(ret_out, index_label="week_end")
    result.symbol_stats.to_csv(sym_out, index=False)

    print("\nSaved outputs:")
    print(f"- {bars_out}")
    print(f"- {eq_out}")
    print(f"- {ret_out}")
    print(f"- {sym_out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
