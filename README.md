# finviz-mcp

MCP Server exposing **finvizfinance** as tools for Claude Desktop and GitHub Actions. 

Insider trading data, market sentiment, sector performance, and technical screening — all accessible via MCP tools.

## Quick Start

### Claude Desktop (uvx from GitHub)

Add to your `claude_desktop_config.json`:

**Windows:**
```json
{
  "mcpServers": {
    "finviz-mcp": {
      "command": "cmd",
      "args": ["/c", "uvx", "--from", "git+https://github.com/xrichini/finviz-mcp.git", "finviz-mcp"]
    }
  }
}
```

**macOS/Linux:**
```json
{
  "mcpServers": {
    "finviz-mcp": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/xrichini/finviz-mcp.git", "finviz-mcp"]
    }
  }
}
```

Restart Claude Desktop. Tools like `finviz_get_market_insiders()` are now available.

### Local Development

```bash
git clone https://github.com/xrichini/finviz-mcp.git
cd finviz-mcp
uv sync
uv run python server.py
```

Test in Claude Desktop with local path or run tests:
```bash
uv run pytest tests/ -v
```

## Available Tools

### 🏦 Insider Trading

| Tool | Description |
|------|-------------|
| `finviz_get_market_insiders(option, limit)` | Latest insider buys/sells (market-wide). Options: "latest buys", "latest sales", "top week", "top owner", etc. |
| `finviz_get_insider_by_owner(insider_id, limit)` | All transactions for a specific insider. |

### 📊 Sector & Group

| Tool | Description |
|------|-------------|
| `finviz_get_sector_performance(period, top_n)` | US sector rankings (Day, Week, Month, Quarter, Year). |
| `finviz_get_industry_performance(sector, period)` | Industries within a sector or market-wide. |
| `finviz_get_group_overview(ticker, group_type)` | Fundamental metrics for a stock group. |

### 🔍 Screener

| Tool | Description |
|------|-------------|
| `finviz_screen_new_highs(sector, min_market_cap, limit)` | 52-week new highs (breakout candidates). |
| `finviz_screen_bullish_technicals(sector, limit)` | Bullish setup (SMA50/200, RSI, performance). |
| `finviz_screen_by_signal(signal, limit)` | Screen by Finviz signals (insider, news, pattern). |
| `finviz_screen_technical(sector, limit)` | Technical metrics (RSI, Beta, ATR, IV). |
| `finviz_screen_performance(sector, period, limit)` | Performance ranking by period. |
| `finviz_screen_optionable_bullish(sector, limit)` | Optionable tickers with bullish technicals. |

### 📋 Quote (by Ticker)

| Tool | Description |
|------|-------------|
| `finviz_get_ticker_fundamentals(ticker)` | All fundamentals (P/E, dividend, market cap, etc.). |
| `finviz_get_ticker_news(ticker, limit)` | Latest news with links. |
| `finviz_get_ticker_insider(ticker, limit)` | Recent insider transactions. |
| `finviz_get_ticker_ratings(ticker, limit)` | Analyst rating history. |
| `finviz_get_ticker_peers(ticker)` | Peers (sector/industry). |
| `finviz_get_ticker_full_info(ticker)` | All data in one call. |
| `finviz_get_ticker_description(ticker)` | Company description. |

---

## Usage Examples

### Claude Desktop

Ask Claude naturally:
```
"Show insider activity for AAPL"
"Find stocks with unusual insider buying"
"What's the insider sentiment for tech stocks?"
```

### Python (e.g., in GitHub Actions)

```python
# Import directly from tools
from tools.insider import finviz_get_market_insiders
import json

# Get recent insider buys
result = finviz_get_market_insiders(option="latest buys", limit=10)
data = json.loads(result)

for record in data:
    print(f"{record['Ticker']}: {record['Owner']} - {record['Relationship']}")
```

---

## GitHub Actions Integration (option-finder)

To integrate finviz-mcp into your scan pipeline:

### 1. Start MCP in background (scan.yml)

```yaml
- name: Start finviz-mcp server
  run: |
    uvx --from git+https://github.com/xrichini/finviz-mcp.git finviz-mcp &
    sleep 2  # Wait for server startup
  env:
    HOME: ${{ runner.temp }}
```

### 2. Call MCP tools from your Python script

```python
# scan_daemon.py
import subprocess
import json

def get_insider_signal(ticker):
    """Fetch insider data via MCP."""
    # Option A: HTTP wrapper (if you wrap MCP in HTTP layer)
    # Option B: Direct tool import (simpler)
    from tools.insider import finviz_get_market_insiders
    
    result = finviz_get_market_insiders(option="latest buys", limit=50)
    data = json.loads(result)
    
    # Filter by ticker
    ticker_insiders = [r for r in data if r.get('Ticker') == ticker]
    return {
        'insider_activity': len(ticker_insiders),
        'signal_strength': 'bullish' if len(ticker_insiders) > 2 else 'neutral'
    }

# In your scan loop:
for symbol in symbols:
    insider = get_insider_signal(symbol)
    # Enrich your latest_scan.json with insider field
```

### 3. Commit updated JSON with insider data

```yaml
- name: Commit enriched scan with insider data
  run: |
    git add data/latest_scan.json
    git commit -m "feat: add insider sentiment to scan ($(date +%s))"
    git push origin main
  if: always()
```

---

## Development

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest tests/ -v

# Format & lint
uv run ruff check .
uv run ruff format .

# Debug MCP with MCP Inspector
npx @modelcontextprotocol/inspector uv run python -m server
```

## Architecture

```
Claude Desktop / GitHub Actions
         ↓
  MCP Client (stdio/HTTP)
         ↓
  FastMCP Server (server.py)
         ↓
  Tool Handlers (tools/*.py)
         ↓
  finvizfinance Scraper
         ↓
  Finviz Website (data)
```

## Requirements

- **Python 3.12+**
- **uv** (Python package manager)
- **finvizfinance** ≥ 1.3.0
- **mcp** ≥ 1.27.0

## License

MIT

3. [Pour chaque ticker retenu]
   finviz_get_ticker_news(ticker)
   finviz_get_ticker_insider(ticker)
   → Confirmation news + insider

4. finviz_get_market_insiders(option="top week buys")
   → Cross-check avec les gros achats insiders du marché

5. [Passer à trading-skills]
   trading-skills: scan_bullish, ib_option_chain, spread_vertical, etc.
   → Analyse technique + option flow + proposition de trade
```

---

## Limites

- **Option flow** : non disponible dans finvizfinance → utiliser Unusual Whales ou `trading-skills:ib_option_chain`
- **Rate limiting** : Finviz peut throttler les requêtes intensives. Ajouter `sleep_sec=2` si besoin dans les screeners.
- **Finviz Elite** : certaines features (screener avancé, real-time) nécessitent un compte Elite.

---

## Automation hebdo GitHub Action + Telegram

Le repo inclut un workflow planifié:
- Fichier: `.github/workflows/watchlist-telegram.yml`
- Schedule: dimanche `20:00 UTC`
- Trigger manuel: `workflow_dispatch`

### Secrets GitHub requis

Dans GitHub > Settings > Secrets and variables > Actions:

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

### Exécution locale (test)

```bash
python scripts/watchlist_cli.py \
   --output-dir watchlists \
   --conviction-threshold 6 \
   --max-tickers 8 \
   --limit-per-screen 25
```

Avec envoi Telegram:

```bash
set TELEGRAM_BOT_TOKEN=xxx
set TELEGRAM_CHAT_ID=yyy
python scripts/watchlist_cli.py --telegram --fail-soft
```

### Sorties générées

- `watchlists/watchlist_YYYY-MM-DD.json`
- `watchlists/watchlist_latest.json`

Le script affiche aussi un résumé court (top tickers + scores) prêt pour Telegram.
