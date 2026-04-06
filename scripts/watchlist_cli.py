"""Generate weekly watchlist and optionally push a summary to Telegram."""

from __future__ import annotations

import argparse
import json
import logging
import os
from dataclasses import dataclass
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

from finvizfinance.group.performance import Performance as GroupPerformance
from finvizfinance.insider import Insider
from finvizfinance.screener.overview import Overview
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from telegram_sender import TelegramSendError, send_watchlist_messages

LOG = logging.getLogger("watchlist_cli")


@dataclass
class WatchCandidate:
    ticker: str
    company: str = ""
    sector: str = ""
    price: str = ""
    performance_week: str = ""
    conviction: int = 0
    signals: set[str] | None = None
    earnings: str = ""
    earnings_flag: str = "UNKNOWN"

    def __post_init__(self) -> None:
        if self.signals is None:
            self.signals = set()


def _parse_percent(value: Any) -> float:
    if value is None:
        return 0.0
    text = str(value).strip().replace("%", "")
    if text in {"", "-", "nan", "None"}:
        return 0.0
    try:
        return float(text)
    except ValueError:
        return 0.0


def _parse_earnings_days(earnings_value: str, today: date) -> int | None:
    """Parse Finviz earnings date-like string and return days from today."""
    if not earnings_value:
        return None

    token = str(earnings_value).strip().split(" ")[0]
    if token in {"", "-", "N/A"}:
        return None

    for fmt in ("%b-%d-%y", "%b-%d-%Y", "%b-%d"):
        try:
            parsed = datetime.strptime(token, fmt)
            if fmt == "%b-%d":
                parsed = parsed.replace(year=today.year)
                if parsed.date() < today:
                    parsed = parsed.replace(year=today.year + 1)
            return (parsed.date() - today).days
        except ValueError:
            continue
    return None


def _classify_earnings(earnings_value: str, today: date) -> str:
    days = _parse_earnings_days(earnings_value, today)
    if days is None:
        return "UNKNOWN"
    if days <= 5:
        return "EXCLUDE_LE_5D"
    if days <= 14:
        return "WAIT_PRINT_6_14D"
    if days <= 30:
        return "IV_ELEVATED_15_30D"
    return "CLEAN_GT_30D"


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
def _safe_call(label: str, fn, *args, **kwargs):
    LOG.info("call_start %s", label)
    result = fn(*args, **kwargs)
    LOG.info("call_ok %s", label)
    return result


def _fetch_sector_table(period: str):
    g = GroupPerformance()
    df = _safe_call(
        f"sector_performance:{period}",
        g.screener_view,
        group="Sector",
        order=period,
    )
    return df.fillna("")


def _select_top_sectors() -> dict[str, Any]:
    week_col = "Performance (Week)"
    quarter_col = "Performance (Quarter)"

    week_df = _fetch_sector_table(week_col)
    quarter_df = _fetch_sector_table(quarter_col)

    week_map = {
        row.get("Name", ""): _parse_percent(row.get(week_col, "0"))
        for row in week_df.to_dict("records")
    }
    quarter_map = {
        row.get("Name", ""): _parse_percent(row.get(quarter_col, "0"))
        for row in quarter_df.to_dict("records")
    }

    sectors = sorted(
        set(week_map.keys()) | set(quarter_map.keys()),
        key=lambda s: (week_map.get(s, 0.0) + quarter_map.get(s, 0.0)),
        reverse=True,
    )

    confirmed = [
        s
        for s in sectors
        if week_map.get(s, 0.0) > 0 and quarter_map.get(s, 0.0) > 0
    ]
    avoid = [
        s
        for s in sectors
        if week_map.get(s, 0.0) < 0 and quarter_map.get(s, 0.0) < 0
    ][:3]
    selected = confirmed[:3] if len(confirmed) >= 3 else sectors[:3]

    return {
        "selected": selected,
        "confirmed": confirmed[:5],
        "avoid": avoid,
        "week": week_map,
        "quarter": quarter_map,
    }


def _run_overview_screen(
    filters: dict[str, str],
    signal: str = "",
    limit: int = 25,
    order: str = "",
):
    s = Overview()
    if signal:
        s.set_filter(signal=signal, filters_dict=filters)
    else:
        s.set_filter(filters_dict=filters)

    kwargs: dict[str, Any] = {"limit": limit, "verbose": 0}
    if order:
        kwargs["order"] = order
        kwargs["ascend"] = False

    df = _safe_call("overview_screen", s.screener_view, **kwargs)
    return df.fillna("")


def _collect_candidates(
    sectors: list[str],
    limit: int,
) -> dict[str, WatchCandidate]:
    candidates: dict[str, WatchCandidate] = {}

    def upsert(row: dict[str, Any], signal_name: str, points: int) -> None:
        ticker = str(row.get("Ticker", "")).strip().upper()
        if not ticker:
            return
        existing = candidates.get(ticker)
        if existing is None:
            existing = WatchCandidate(
                ticker=ticker,
                company=str(row.get("Company", "")),
                sector=str(row.get("Sector", "")),
                price=str(row.get("Price", "")),
                performance_week=str(
                    row.get("Performance (Week)", row.get("Perf Week", ""))
                ),
                earnings=str(row.get("Earnings", "")),
            )
            candidates[ticker] = existing

        if signal_name not in existing.signals:
            existing.signals.add(signal_name)
            existing.conviction += points

        if (
            _parse_percent(existing.performance_week) > 5.0
            and "perf_week_gt_5" not in existing.signals
        ):
            existing.signals.add("perf_week_gt_5")
            existing.conviction += 1

    for sector in sectors:
        base_filters = {
            "Market Cap.": "+Mid (over $2bln)",
            "Average Volume": "Over 500K",
            "Sector": sector,
        }

        new_high = _run_overview_screen(
            base_filters,
            signal="New High",
            limit=limit,
            order="Performance (Week)",
        )
        for row in new_high.to_dict("records"):
            upsert(row, "new_high", 2)

        optionable_filters = {
            **base_filters,
            "Option/Short": "Optionable and shortable",
            "50-Day Simple Moving Average": "Price above SMA50",
            "200-Day Simple Moving Average": "Price above SMA200",
            "RSI (14)": "Not Oversold (>50)",
            "Performance": "Quarter Up",
        }
        optionable = _run_overview_screen(
            optionable_filters,
            signal="",
            limit=limit,
            order="Performance (Quarter)",
        )
        for row in optionable.to_dict("records"):
            upsert(row, "optionable_bullish", 2)

        channel_up = _run_overview_screen(
            base_filters,
            signal="Channel Up",
            limit=limit,
        )
        for row in channel_up.to_dict("records"):
            upsert(row, "channel_up", 1)

    insider_signal_filters = {
        "Market Cap.": "+Mid (over $2bln)",
        "Average Volume": "Over 500K",
    }
    insider_signal = _run_overview_screen(
        insider_signal_filters, signal="Recent Insider Buying", limit=20
    )
    for row in insider_signal.to_dict("records"):
        upsert(row, "recent_insider_buying", 3)

    insider = Insider(option="top week buys")
    top_buys_df = _safe_call(
        "insider_top_week_buys",
        insider.get_insider,
    ).fillna("")
    top_buys_tickers = {
        str(row.get("Ticker", "")).strip().upper()
        for row in top_buys_df.to_dict("records")
        if str(row.get("Ticker", "")).strip()
    }
    for ticker in top_buys_tickers:
        if ticker not in candidates:
            candidates[ticker] = WatchCandidate(ticker=ticker)
        if "top_week_buys" not in candidates[ticker].signals:
            candidates[ticker].signals.add("top_week_buys")
            candidates[ticker].conviction += 3

    return candidates


def _build_output(
    *,
    sectors_info: dict[str, Any],
    candidates: dict[str, WatchCandidate],
    conviction_threshold: int,
    max_tickers: int,
) -> dict[str, Any]:
    today = datetime.now(UTC).date()

    for candidate in candidates.values():
        candidate.earnings_flag = _classify_earnings(candidate.earnings, today)

    excluded = []
    selected = []

    for c in sorted(
        candidates.values(),
        key=lambda x: x.conviction,
        reverse=True,
    ):
        if c.earnings_flag == "EXCLUDE_LE_5D":
            excluded.append(
                {
                    "ticker": c.ticker,
                    "reason": "earnings <= 5 days",
                    "conviction": c.conviction,
                }
            )
            continue

        if c.conviction < conviction_threshold:
            excluded.append(
                {
                    "ticker": c.ticker,
                    "reason": "conviction below threshold",
                    "conviction": c.conviction,
                }
            )
            continue

        selected.append(
            {
                "ticker": c.ticker,
                "company": c.company,
                "sector": c.sector,
                "price": c.price,
                "performance_week": c.performance_week,
                "conviction": c.conviction,
                "signals": sorted(c.signals),
                "earnings": c.earnings,
                "earnings_flag": c.earnings_flag,
            }
        )

    selected = selected[:max_tickers]

    return {
        "generated_at_utc": datetime.now(UTC).isoformat(),
        "regime": "UNKNOWN",
        "trade_style": "WATCHLIST_ONLY",
        "top_sectors": sectors_info["selected"],
        "sector_rotation": {
            "confirmed": sectors_info["confirmed"],
            "avoid": sectors_info["avoid"],
        },
        "watchlist": selected,
        "excluded": excluded[:40],
        "meta": {
            "candidate_count": len(candidates),
            "selected_count": len(selected),
            "conviction_threshold": conviction_threshold,
            "max_tickers": max_tickers,
            "notes": [
                "V1 CLI uses Finviz-only signals.",
                "Macro regime and trading-skills scoring can be added in V2.",
            ],
        },
    }


def format_telegram_summary(payload: dict[str, Any]) -> str:
    top_sectors = ", ".join(payload.get("top_sectors", [])[:3]) or "N/A"
    rows = payload.get("watchlist", [])
    lines = [
        f"WATCHLIST HEBDO - {datetime.now(UTC).strftime('%Y-%m-%d')} UTC",
        f"Regime: {payload.get('regime', 'UNKNOWN')}",
        f"Top secteurs: {top_sectors}",
        "",
        f"Top {len(rows)} tickers:",
    ]

    for idx, row in enumerate(rows, start=1):
        lines.append(
            f"{idx}. {row.get('ticker', '-'):<6} "
            f"conv={row.get('conviction', 0)} "
            f"wk={row.get('performance_week', '-')} "
            f"earnings={row.get('earnings_flag', 'UNKNOWN')}"
        )

    lines.append("")
    lines.append(
        f"Candidates: {payload.get('meta', {}).get('candidate_count', 0)}"
    )
    lines.append(f"Exclus: {len(payload.get('excluded', []))}")
    return "\n".join(lines)


def run(args: argparse.Namespace) -> int:
    logging.basicConfig(
        level=getattr(logging, args.log_level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    try:
        sectors_info = _select_top_sectors()
        candidates = _collect_candidates(
            sectors_info["selected"],
            limit=args.limit_per_screen,
        )
        payload = _build_output(
            sectors_info=sectors_info,
            candidates=candidates,
            conviction_threshold=args.conviction_threshold,
            max_tickers=args.max_tickers,
        )
    except Exception as exc:
        LOG.exception("watchlist_generation_failed")
        if args.fail_soft:
            payload = {
                "generated_at_utc": datetime.now(UTC).isoformat(),
                "watchlist": [],
                "excluded": [],
                "meta": {"error": str(exc)},
            }
        else:
            return 2

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.output_file:
        output_file = Path(args.output_file)
        if not output_file.is_absolute():
            output_file = output_dir / output_file
    else:
        stamp = datetime.now(UTC).strftime("%Y-%m-%d")
        output_file = output_dir / f"watchlist_{stamp}.json"

    output_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    (output_dir / "watchlist_latest.json").write_text(
        json.dumps(payload, indent=2),
        encoding="utf-8",
    )
    LOG.info("watchlist_written %s", output_file)

    summary = format_telegram_summary(payload)
    print(summary)

    if args.telegram:
        bot_token = args.telegram_bot_token or os.getenv(
            "TELEGRAM_BOT_TOKEN", ""
        )
        chat_id = args.telegram_chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        if not bot_token or not chat_id:
            LOG.error("telegram_enabled_but_missing_credentials")
            return 3

        try:
            sent_count = send_watchlist_messages(
                bot_token=bot_token,
                chat_id=chat_id,
                messages=[summary],
                logger=LOG,
            )
            LOG.info("telegram_sent_count=%d", sent_count)
        except (TelegramSendError, Exception):
            LOG.exception("telegram_send_failed")
            if not args.fail_soft:
                return 4

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate weekly Finviz watchlist"
    )
    parser.add_argument(
        "--output-dir",
        default="watchlists",
        help="Directory for JSON outputs",
    )
    parser.add_argument(
        "--output-file",
        default="",
        help="Optional output filename",
    )
    parser.add_argument("--conviction-threshold", type=int, default=6)
    parser.add_argument("--max-tickers", type=int, default=8)
    parser.add_argument("--limit-per-screen", type=int, default=25)
    parser.add_argument(
        "--telegram",
        action="store_true",
        help="Send summary to Telegram",
    )
    parser.add_argument("--telegram-bot-token", default="")
    parser.add_argument("--telegram-chat-id", default="")
    parser.add_argument(
        "--fail-soft",
        action="store_true",
        help="Do not fail hard on external errors",
    )
    parser.add_argument("--log-level", default="INFO")
    return parser


if __name__ == "__main__":
    raise SystemExit(run(build_parser().parse_args()))
