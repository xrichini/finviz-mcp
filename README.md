# finviz-mcp

MCP Server exposing **finvizfinance** as tools for Claude Desktop.
Conçu pour s'intégrer avec `trading-skills` dans des workflows de watchlist automatisés.

## Outils disponibles

### 📊 Group / Sector
| Tool | Description |
|------|-------------|
| `finviz_get_sector_performance` | Performance des secteurs US, triée par période |
| `finviz_get_industry_performance` | Performance des industries (par secteur optionnel) |
| `finviz_get_group_overview` | Vue fondamentale d'un groupe (Market Cap, P/E, EPS...) |

### 🔍 Screener
| Tool | Description |
|------|-------------|
| `finviz_screen_new_highs` | Tickers au 52-week new high (breakout) |
| `finviz_screen_bullish_technicals` | Setup bullish (SMA50/200, RSI, performance) |
| `finviz_screen_by_signal` | Screener par signal Finviz (pattern, news, insider) |
| `finviz_screen_technical` | Données techniques (RSI, Beta, ATR, volatilité) |
| `finviz_screen_performance` | Classement performance (momentum ranking) |
| `finviz_screen_optionable_bullish` | Candidats optionables bullish (PMCC, spreads) |

### 📋 Quote (par ticker)
| Tool | Description |
|------|-------------|
| `finviz_get_ticker_fundamentals` | Tous les fondamentaux d'un ticker |
| `finviz_get_ticker_news` | Dernières news (avec liens) |
| `finviz_get_ticker_insider` | Transactions insiders récentes |
| `finviz_get_ticker_ratings` | Historique ratings analystes |
| `finviz_get_ticker_peers` | Tickers peers (même secteur/industrie) |
| `finviz_get_ticker_full_info` | Tout en un seul appel |
| `finviz_get_ticker_description` | Description de la société |

### 🏦 Insider (marché entier)
| Tool | Description |
|------|-------------|
| `finviz_get_market_insiders` | Achats/ventes insiders récents (marché entier) |
| `finviz_get_insider_by_owner` | Transactions d'un insider spécifique |

---

## Installation

### 1. Créer l'environnement virtuel

```bash
cd "D:\XAVIER\DEV\Python Projects\finviz-mcp"
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

> **Note :** `finvizfinance` est installé depuis PyPI.
> Si tu veux utiliser ta version locale (avec tes éventuelles modifs), remplace dans `requirements.txt` :
> ```
> finvizfinance>=0.14.0
> ```
> par :
> ```
> -e ../finvizfinance
> ```

### 2. Test local (optionnel)

```bash
mcp dev server.py
```

### 3. Configurer Claude Desktop

Édite `%APPDATA%\Claude\claude_desktop_config.json` :

```json
{
  "mcpServers": {
    "finviz": {
      "command": "D:\\XAVIER\\DEV\\Python Projects\\finviz-mcp\\.venv\\Scripts\\python.exe",
      "args": [
        "D:\\XAVIER\\DEV\\Python Projects\\finviz-mcp\\server.py"
      ]
    }
  }
}
```

Redémarre Claude Desktop — les outils `finviz_*` apparaissent dans la liste.

---

## Workflow type : Watchlist Builder

```
1. finviz_get_sector_performance(period="Performance (Quarter)", top_n=3)
   → Trouve les 3 secteurs leaders

2. finviz_screen_new_highs(sector="Technology", min_market_cap="+Mid (over $2bln)")
   + finviz_screen_bullish_technicals(sector="Technology")
   → Top tickers bullish dans ces secteurs

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
