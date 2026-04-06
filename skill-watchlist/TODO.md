## Plan: Watchlist Durcie + Trading Skills + GitHub Hub

Objectif: améliorer la qualité de sélection (éviter les downtrends), intégrer des signaux techniques issus de trading-skills/tradingview, et faire de GitHub la source de vérité pour pousser la watchlist vers Telegram et l’exposer à Claude.ai via endpoint HTTP.

**Steps**
1. Phase 1 — Refactor architecture "core + adapters"
- Extraire la logique watchlist de l’orchestrateur actuel vers un core pur (fonctions déterministes testables).
- Garder un adapter CLI batch pour GitHub Actions.
- Préparer un adapter HTTP (remote MCP) pour exposition Claude.ai.
- Dépendance: aucune.

2. Phase 2 — Durcir le filtre technique (Trend Gate obligatoire)
- Ajouter un "Trend Gate" avant scoring final:
  - Prix > SMA50 > SMA200
  - pente SMA50 positive
  - ADX minimum
  - relative strength vs SPY positive
  - garde-fou RSI extrême (sur-extension)
- Exclure explicitement les tickers qui échouent ce gate, avec raison dans `excluded`.
- Dépend de 1.

3. Phase 3 — Intégrer trading-skills-mcp / tradingview-mcp en mode cross-projet
- Implémenter un provider technique abstrait avec 2 backends:
  - backend local Python (préféré CI)
  - backend HTTP/MCP (si services distants disponibles)
- Source des dépendances via GitHub (uv git dependency + pin commit/tag).
- Ajouter fallback Finviz-only si provider externe indisponible.
- Dépend de 1, parallèle partiel avec 2.

4. Phase 4 — Refonte scoring multi-source
- Scoring final en 3 couches:
  - couche structure trend (gate dur)
  - couche momentum/qualité technique (trading-skills/tradingview)
  - couche contexte marché (secteurs + insiders + earnings)
- Séparer "hard filters" et "soft scores" pour éviter d’élire un ticker baissier bien scoré par bruit.
- Dépend de 2 et 3.

5. Phase 5 — GitHub comme source de vérité de distribution
- Conserver l’artefact JSON, ajouter publication machine-readable:
  - `watchlists/latest.json` en artifact
  - option publication sur branche dédiée data (ex: `watchlist-data`) ou Release asset
- Versionner metadata de run (sha, date, provider, mode fallback).
- Dépend de 1.

6. Phase 6 — Exposition Claude.ai (remote)
- Ajouter endpoint HTTP lisant la dernière watchlist publiée depuis GitHub source (branche data ou release).
- Endpoint minimal: get latest + get history (n semaines).
- Auth légère (token header) pour usage privé.
- Dépend de 5.

7. Phase 7 — Workflow GitHub Actions étendu
- Étape 1: build/sync uv.
- Étape 2: génération watchlist avec providers techniques.
- Étape 3: validation qualité (règles anti-downtrend).
- Étape 4: publication GitHub source (artifact + data branch/release).
- Étape 5: notification Telegram enrichie (déjà en place) + lien vers source GitHub.
- Dépend de 4,5.

8. Phase 8 — Vérification et garde-fous
- Tests unitaires: trend gate, scoring, fallback provider.
- Tests d’intégration: provider GitHub dependency, mode dégradé.
- Smoke CI: comparaison distribution des scores, taux de rejet trend gate.
- Dépend de 2,3,4,7.

**Relevant files**
- d:/XAVIER/mcp/finviz-mcp/scripts/watchlist_cli.py — orchestrateur actuel à découper en core + adapter.
- d:/XAVIER/mcp/finviz-mcp/scripts/telegram_sender.py — conserver en sortie de pipeline, ajouter lien source GitHub.
- d:/XAVIER/mcp/finviz-mcp/.github/workflows/watchlist-telegram.yml — pipeline à étendre (providers techniques + publication data).
- d:/XAVIER/mcp/finviz-mcp/pyproject.toml — dépendances uv git (trading-skills/tradingview) avec pin version.
- d:/XAVIER/mcp/finviz-mcp/uv.lock — verrouillage reproductible CI.
- d:/XAVIER/mcp/finviz-mcp/README.md — docs architecture, modes provider, opérations.
- d:/XAVIER/mcp/finviz-mcp/skill-watchlist/SKILL.md — spec métier de référence pour mapping Step->Code.
- d:/XAVIER/mcp/finviz-mcp/tools/screener.py — source finviz pour couche contexte.
- d:/XAVIER/mcp/finviz-mcp/tools/group.py — source régime sectoriel.
- d:/XAVIER/mcp/finviz-mcp/tools/quote.py — enrichissement ticker.
- d:/XAVIER/mcp/finviz-mcp/tools/insider.py — contexte insider.

**Verification**
1. Vérifier qu’aucun ticker final ne viole le Trend Gate (assertion CI).
2. Vérifier le fallback automatique quand provider trading-skills/tradingview indisponible.
3. Vérifier publication GitHub data (latest + historique) et lisibilité par endpoint remote.
4. Vérifier notification Telegram inclut lien vers la source GitHub du run.
5. Vérifier que Claude.ai peut lire le remote endpoint et retourner la watchlist la plus récente.

**Decisions**
- Inclure en priorité: Trend Gate dur + intégration provider cross-repo + publication GitHub data.
- Exclure dans ce cycle: backtesting avancé, dashboard visuel.
- Préférence d’exécution: dépendances directes Python (plus fiable CI) avant orchestration MCP complexe.
- Déploiement Claude.ai: remote HTTP minimal branché sur la source GitHub publiée.

**Further Considerations**
1. Choix source GitHub pour exposition:
Option A: branche `watchlist-data` (simple lecture raw).
Option B: release assets (historisation propre, plus verbeux).
Recommandé: Option A d’abord.
2. Choix intégration trading-skills/tradingview:
Option A: git dependency Python.
Option B: appels HTTP remote MCP.
Recommandé: Option A pour CI, Option B pour mobilité Claude.ai.
3. Politique de rejet trend:
Option A: hard fail si top N insuffisant.
Option B: compléter avec candidats de secours marqués "weak trend".
Recommandé: Option B avec flag explicite.
