# Watchlist Workflow — Améliorations & Roadmap

## ✅ Livré dans SKILL.md (v2)

### ✅ #1 — Score de conviction multi-signal
Chaque ticker accumule des points à travers les étapes :
- Step 2 (screener) : new high +2, optionable +2, channel up +1, insider buy +3/+3, perf week +1
- Step 4 (trading-skills) : bull ≥6 +2, ≥7 +4, ≥8 +6
- Step 6 (PMCC) : pmcc ≥8 +2, spread tight +1
- Step 7 (deep dive) : analyst upgrade +2

Seuil minimum : **6 pts** pour entrer dans le top 8. Max théorique : 18 pts.

### ✅ #2 — Filtre earnings intelligent
Quatre niveaux distincts au lieu d'un simple flag :
- ≤ 5 jours → EXCLUDE
- 6–14 jours → FLAG "Wait for print"
- 15–30 jours → FLAG "IV elevated" (vendre du premium)
- > 30 jours → CLEAN entry

### ✅ #3 — Contexte macro SPY/QQQ/IWM
Step 0 dédié avec 4 régimes : BULL / EXTENDED / CAUTION / BEAR.
Chaque régime mappe directement sur un style de trade (PMCC vs spreads vs CSP vs monitor only).

---

## 🔜 Roadmap — Prochaines améliorations

### #4 — Persistence watchlist (JSON daté)
Sauvegarder chaque run dans :
```
D:\XAVIER\DEV\Python Projects\finviz-mcp\watchlists\
├── watchlist_2026-04-04.json
├── watchlist_2026-03-28.json
└── watchlist_index.json
```
Format JSON :
```json
{
  "date": "2026-04-04",
  "regime": "BULL",
  "top_sectors": ["Technology", "Energy"],
  "tickers": [
    {
      "ticker": "GLW", "conviction": 14, "bull_score": 6.5,
      "pmcc_score": 9, "setup": "PMCC", "earnings": "2026-04-28",
      "earnings_flag": "IV_ELEVATED", "price_entry": 147.92,
      "flags": []
    }
  ],
  "excluded": [
    {"ticker": "DOCN", "reason": "dilution + insider selling"},
    {"ticker": "LUNR", "reason": "earnings in 3 days"}
  ]
}
```
Permet un `diff` semaine-sur-semaine : "quels tickers sont revenus ?"

### #5 — Performance tracker (`/watchlist-review`)
Lancer le dimanche suivant le run :
```
Pour chaque ticker dans le JSON de la semaine précédente :
  trading-skills:stock_quote(symbol)
  → P&L théorique (prix vendredi close entry vs prix actuel)
  → Win rate global du workflow
  → Identifier quels signaux ont le mieux prédit les gagnants
```

### #6 — Channel Up + Double Bottom screeners supplémentaires
```
finviz_screen_by_signal(signal="Double Bottom", ...)
finviz_screen_by_signal(signal="TL Support", ...)
```
À ajouter en Step 2 pour élargir le pool sur marchés en consolidation.

### #7 — Piotroski F-Score filter (Step 6.5)
Après PMCC scan, avant deep dive :
```
trading-skills:piotroski_score(symbol)
```
Score < 4 = risque fondamental → baisser la conviction de 2 pts.
Score ≥ 7 = qualité élevée → +1 pt conviction.

### #8 — Risk sizing dans l'output
Ajouter dans le tableau final :
- **Stop loss naturel** : prix entry − 1.5× ATR(14)
- **Beta-weighted position size** : si beta > 1.5, réduire taille de 30%
- **Short float %** : > 20% → noter "squeeze potential"

### #9 — Option flow Unusual Whales (dès abonnement)
Quand accès disponible :
- Call sweep non couvert > $500K même direction → +3 pts conviction
- Dark pool print significatif → +2 pts
- Croiser avec bull score ≥ 7 → conviction maximale (tier 1 pick)

---

## 🗺️ Phases moyen terme

### Phase 2 — Script CLI (`run_watchlist.py`)
- Exécutable le samedi matin via cron Oracle Cloud
- Génère JSON + rapport Markdown automatiquement
- Envoie un résumé par email ou webhook

### Phase 3 — Dashboard React
- Intégré dans le projet options flow
- Affiche watchlist courante + heatmap conviction
- Calendrier earnings visuel
- Historique semaines + courbe de performance du workflow

### Phase 4 — Backtesting du workflow
- Rejouer les watchlists passées sur prix historiques
- Comparer différents seuils de conviction
- Utiliser `backtesting-frameworks` skill
