# Archive Session — Zones d'Intensité au Modal Graphique
**Date:** 2026-05-04  
**Sujet:** Intégration des zones bleu/orange/rouge au modal graphique  
**Status:** ✅ Complétée

---

## Briefing Initial
Utilisateur voulait ajouter les zones d'intensité (bleu/orange/rouge) comme **overlay sur le graphique existant** du modal (chart-modal), plutôt que remplacer TradingView entièrement.

## Découverte Clé
Le graphique n'était **pas un iframe TradingView**, mais un **canvas HTML5 personnalisé** avec :
- Candlesticks OHLC
- Indicateurs MACD/RSI déjà présents
- Rendering custom en JavaScript

## Solution Implémentée

### 1. Rendu des Zones (lignes 5558-5606 dans index.html)
```javascript
// Calcule 7 niveaux de prix : -3% à +3% du prix courant
// Groupe par couleur d'intensité (bleu/orange/rouge)
// Dessine bandes semi-transparentes + lignes limites
```

- **Bleu** (intensity < 0.4): Zones externes (-3% à -2%, +2% à +3%)
- **Orange** (0.4-0.7): Zones du milieu (-1%, +1%)
- **Rouge** (≥ 0.7): Zone centrale (prix actuel)

### 2. Ajustements Rendus
- Opacity initial: 0.08 → Trop faible, invisible
- Opacity final: 0.15 → Bon équilibre visibilité/subtilité
- Lignes: 2px avec globalAlpha 0.5

### 3. Légende Explicative (lignes 4828-4844)
Ajout d'une section qui explique **concrètement** ce que chaque zone signifie :
- **ROUGE** : Zone "chaude", action immédiate, TP/SL court terme (15m-1h)
- **ORANGE** : Rebonds, niveaux clés (1h-4h)
- **BLEU** : Support lointains, long terme (1J+)

## Comportement Final
✅ Les zones s'affichent sur le canvas  
✅ Elles se mettent à jour quand l'utilisateur change de crypto  
✅ Elles suivent le zoom/scroll du canvas (native series)  
✅ Légende claire pour l'utilisateur

## Fichiers Modifiés
- `templates/index.html`
  - Lignes 4828-4844: Légende explicative
  - Lignes 5558-5606: Rendu des zones

## Prochaines Étapes Suggérées
1. ✅ Tester en local avec plusieurs cryptos
2. ✅ Upload sur serveur (fichier prêt)
3. Monitorer le feedback utilisateur sur clarté des zones
4. Éventuellement: ajouter contrôle utilisateur pour show/hide zones

---

**Livrables:**
- ✅ Zones visibles et fonctionnelles
- ✅ Légende de trading intégrée
- ✅ Prêt pour production
