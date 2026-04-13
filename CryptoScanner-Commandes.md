# CryptoScanner Pro — Guide des Commandes
## Système Agentique ICA

---

## Slash Commands

### `/recall cryptoscanner`
**Quand :** Au début de chaque session, après un `/clear`, ou si Claude semble avoir perdu le contexte.

**Ce que ça fait :**
- Charge le snapshot du projet (`memory/projets/cryptoscanner/contexte.md`)
- Recharge l'historique des sessions passées
- Présente un briefing : état du projet, décisions clés, prochaines étapes

**Exemple :**
```
/recall cryptoscanner
→ Claude répond avec l'état du projet et propose de reprendre
```

---

### `/archive`
**Quand :** Avant de fermer la session ou de faire `/clear`. Sans ça, le contexte est perdu.

**Ce que ça fait :**
- Crée un fichier archive dans `memory/archives/` (immuable)
- Met à jour `memory/projets/cryptoscanner/contexte.md` (état courant)
- Met à jour `memory/projets/cryptoscanner/historique.md`
- Met à jour `memory/_index.md`

**Exemple :**
```
/archive
→ Claude crée memory/archives/2026-04-11-14h30-cryptoscanner-ajout-feature.md
→ Contexte sauvegardé — /clear est safe
```

---

### `/status`
**Quand :** Pour voir ce que le système connaît — agents disponibles, projets actifs, règles chargées.

**Ce que ça fait :**
- Liste les 6 agents par département
- Affiche le projet actif et sa phase
- Liste les directives, rules, commands et MCP connectés

**Exemple :**
```
/status
→ Agents (6) : dev/debugger, dev/feature, marche/scanner...
→ Projets (1) : cryptoscanner — Phase : En cours
→ Rules (5) : ica-compliance, qualite, communication...
```

---

### `/nouveau-agent`
**Quand :** Tu veux ajouter un nouveau spécialiste au système (ex: agent on-chain, agent portfolio).

**Ce que ça fait :**
- Guide interactif : Claude te pose des questions sur le rôle, le département, les limites
- Crée le fichier `.claude/agents/{dept}/{nom}.md` conforme ICA
- Crée `memory/agents/{nom}/notes.md`

**Exemple :**
```
/nouveau-agent analyste on-chain
→ Claude crée .claude/agents/marche/onchain.md
```

---

### `/nouveau-projet`
**Quand :** Tu veux gérer un deuxième projet avec le même système (ex: un bot de trading séparé).

**Ce que ça fait :**
- Crée `memory/projets/{nom}/contexte.md` et `historique.md`
- Met à jour `memory/_index.md`

**Exemple :**
```
/nouveau-projet trading-bot
→ Claude initialise la mémoire pour un nouveau projet
```

---

### `/review`
**Quand :** Tu veux vérifier qu'un agent ou un livrable est bien conforme aux standards ICA.

**Ce que ça fait :**
- Audit ICA : I défini ? C défini ? A défini ? Règle d'Or respectée ?
- Audit qualité : format de livraison respecté ? fichiers aux bons endroits ?
- Donne un verdict : Conforme / À améliorer / Non conforme

**Exemples :**
```
/review .claude/agents/dev/debugger.md
/review dernier
```

---

## Agents — Langage Naturel

Pas besoin de commande — parle directement. Claude route vers le bon agent automatiquement.

---

### Agent Debugger
**Département :** dev/
**Déclencheurs :** "bug", "erreur", "crash", "traceback", "ne fonctionne pas"

**Exemples de demandes :**
```
"j'ai une erreur dans daily_report.py :
  Traceback: AttributeError: 'NoneType' object has no attribute 'send'"

"le scanner plante au démarrage, voilà l'erreur..."

"la route /admin retourne 500"
```

**Ce qu'il fait :** Lit l'erreur → identifie la cause racine → applique le fix minimal → valide
**Ce qu'il ne fait pas :** Refactorer du code non lié, toucher aux features existantes

---

### Agent Feature
**Département :** dev/
**Déclencheurs :** "feature", "implémenter", "ajouter", "créer", "refactor"

**Exemples de demandes :**
```
"ajoute une page de statistiques pour les membres paid"

"je veux un système d'alertes email quand un signal fort est détecté"

"crée un endpoint API pour récupérer les derniers signaux en JSON"
```

**Ce qu'il fait :** Lit l'existant → propose un plan → implémente → teste
**Ce qu'il ne fait pas :** Toucher à security.py sans confirmation, créer un script si un existant suffit

---

### Agent Scanner
**Département :** marche/
**Déclencheurs :** "scanner", "prix", "signal", "exchange", "alerte"

**Exemples de demandes :**
```
"lance un scan sur Binance et dis-moi les signaux du moment"

"quels sont les altcoins avec un fort volume ce matin ?"

"analyse les perpétuels sur Bybit"
```

**Ce qu'il fait :** Exécute scanner_engine.py → filtre via smart_signals.py → rapport structuré
**Ce qu'il ne fait pas :** Modifier le code du scanner, prendre des décisions de trading

---

### Agent Analyse
**Département :** marche/
**Déclencheurs :** "COT", "ETF", "macro", "open interest", "liquidations", "analyse"

**Exemples de demandes :**
```
"analyse le rapport COT BTC de cette semaine"

"que dit le positionnement institutionnel sur l'or en ce moment ?"

"donne-moi une synthèse macro : DXY, VIX, taux"
```

**Ce qu'il fait :** Lit cot_engine.py, indices_engine.py, forex_engine.py → synthèse structurée
**Ce qu'il ne fait pas :** Donner des signaux de trading directs ou des recommandations de position

---

### Agent Morning Brief
**Département :** reporting/
**Déclencheurs :** "morning brief", "briefing", "rapport matin"

**Exemples de demandes :**
```
"génère le morning brief d'aujourd'hui"

"crée le briefing du matin avec les données du scanner"
```

**Ce qu'il fait :** Exécute morning_brief.py → valide la structure → présente pour validation
**Ce qu'il ne fait pas :** Publier sans ta validation, appeler Groq/Anthropic directement

---

### Agent Rapport
**Département :** reporting/
**Déclencheurs :** "rapport", "telegram", "daily", "notification"

**Exemples de demandes :**
```
"envoie le rapport Telegram d'aujourd'hui"

"le rapport ne s'envoie plus, voilà l'erreur Telegram..."

"vérifie que le daily report s'est bien envoyé ce matin"
```

**Ce qu'il fait :** Exécute daily_report.py → confirme l'envoi Telegram → diagnostique si erreur
**Ce qu'il ne fait pas :** Modifier le contenu des données sources, toucher au code sans demande

---

## Workflow Type d'une Session

```
┌─────────────────────────────────────┐
│  1. Ouvrir CryptoScanner dans       │
│     Claude Code                     │
├─────────────────────────────────────┤
│  2. /recall cryptoscanner           │
│     → Contexte rechargé en 30s      │
├─────────────────────────────────────┤
│  3. Travail normal                  │
│     "corrige ce bug..."             │
│     "ajoute cette feature..."       │
│     "génère le morning brief..."    │
├─────────────────────────────────────┤
│  4. /archive  (avant de fermer)     │
│     → Mémoire sauvegardée           │
│     → /clear safe                   │
└─────────────────────────────────────┘
```

---

## Règle d'Or ICA

```
I sans C  =  Agent aveugle   (sait qui il est, manque de contexte)
C sans I  =  Agent perdu     (a les infos, ne sait pas les filtrer)
I+C sans A = Agent paralysé  (comprend, ne peut pas agir)
I + C + A = Agent autonome
```

---

*CryptoScanner Pro — Système Agentique ICA — Fractality Studio*
