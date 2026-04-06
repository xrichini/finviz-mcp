"""Telegram sender utilities for watchlist automation."""

from __future__ import annotations

import logging
from typing import Iterable, List

import requests

TELEGRAM_MAX_CHARS = 4096


class TelegramSendError(RuntimeError):
    """Raised when Telegram API returns an error."""


def split_message(
    text: str,
    max_chars: int = TELEGRAM_MAX_CHARS - 20,
) -> List[str]:
    """Split message without breaking lines when possible."""
    if len(text) <= max_chars:
        return [text]

    chunks: List[str] = []
    current: List[str] = []
    current_len = 0

    for line in text.splitlines() or [text]:
        line_len = len(line) + 1
        if current and current_len + line_len > max_chars:
            chunks.append("\n".join(current))
            current = [line]
            current_len = line_len
        else:
            current.append(line)
            current_len += line_len

    if current:
        chunks.append("\n".join(current))

    normalized: List[str] = []
    for chunk in chunks:
        if len(chunk) <= max_chars:
            normalized.append(chunk)
            continue
        start = 0
        while start < len(chunk):
            normalized.append(chunk[start:start + max_chars])
            start += max_chars

    return normalized


def send_telegram_message(
    *,
    bot_token: str,
    chat_id: str,
    text: str,
    parse_mode: str | None = None,
    timeout_seconds: int = 20,
) -> dict:
    """Send one message to Telegram."""
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "disable_web_page_preview": True,
    }
    if parse_mode:
        payload["parse_mode"] = parse_mode

    response = requests.post(url, json=payload, timeout=timeout_seconds)
    response.raise_for_status()
    data = response.json()

    if not data.get("ok"):
        raise TelegramSendError(
            f"Telegram API error: {data.get('description', 'unknown error')}"
        )

    return data


def send_watchlist_messages(
    *,
    bot_token: str,
    chat_id: str,
    messages: Iterable[str],
    parse_mode: str | None = None,
    logger: logging.Logger | None = None,
) -> int:
    """Send one or more watchlist messages and return sent count."""
    sent = 0
    for msg in messages:
        for chunk in split_message(msg):
            send_telegram_message(
                bot_token=bot_token,
                chat_id=chat_id,
                text=chunk,
                parse_mode=parse_mode,
            )
            sent += 1
            if logger:
                logger.info(
                    "telegram_chunk_sent",
                    extra={"chunk_len": len(chunk)},
                )
    return sent
