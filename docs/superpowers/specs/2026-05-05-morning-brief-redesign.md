# Morning Brief Redesign — Spec Complète

**Date** : 2026-05-05  
**Auteur** : Claude Orchestrateur  
**Status** : 🎯 Prêt pour implémentation  
**Approche** : Interactif Pro+ (Approche C)

---

## Vue d'ensemble

Redesigner la page `/brief` (morning brief généré chaque matin à 8h) pour un rendu **professionnel, moderne et cohérent**. Focus sur :
- Gradient subtil (bleu/violet foncé)
- Tableaux interactifs avec ranking, tri, barres visuelles
- Typographie hiérarchisée
- Espacements professionnels
- Hover effects et micro-interactions

---

## Architecture & Palette

### Couleurs

| Rôle | Valeur | Usage |
|------|--------|-------|
| Gradient BG | `#0f1428` → `#1e1a4a` | Fond principal (135deg) |
| Accent Primary | `#ffd700` | Headers, symboles, accents clés |
| Bullish | `#4caf50` | Gains, sentiment positif, barres + |
| Bearish | `#f44336` | Pertes, sentiment négatif, barres - |
| Neutral | `#ffd700` | Sentiment neutre (gold) |
| Text Primary | `#e0e0f0` | Texte principal |
| Text Secondary | `#ccc` | Texte secondaire |
| Text Muted | `#aaa` | Texte tertiaire |
| Text Subtle | `#666` | Labels, headers |
| Card BG | `rgba(37,37,64,0.8)` | Cartes et sections |
| Row Hover | `rgba(76,175,80,0.15)` ou `rgba(244,67,54,0.15)` | Au survol (vert/rouge) |
| Row Alt 1 | `rgba(255,255,255,0.02)` | Alternating rows |
| Row Alt 2 | `rgba(0,0,0,0.2)` | Alternating rows |

### Typographie

| Élément | Size | Weight | Color | Notes |
|---------|------|--------|-------|-------|
| h2 (Section title) | 20-24px | bold | `#ffd700` | Margin-bottom 12px |
| h3 (Subsection) | 16px | 600 | `#e0e0f0` | - |
| Body text | 14px | 400 | `#ccc` | - |
| Table header | 11px | 600 | `#aaa` | UPPERCASE, letter-spacing 0.8px |
| Table cell | 13-14px | varies | varies | - |
| Small/Label | 11-12px | 600 | `#666` | UPPERCASE |
| Large number (Score) | 72px | bold | `#ffd700` ou sentiment color | - |

### Espacements

| Element | Value |
|---------|-------|
| Section padding (internal) | 20px |
| Gap between sections | 16px |
| Table padding (cell) | 14px vertical, 16px horizontal |
| Row height | 50-55px |
| Page max-width | 900px |
| Page margin | 20px auto |
| Page padding | 0 16px 60px |

### Transitions & Interactions

- Default transition : `0.15s ease` ou `0.25s ease`
- Hover sur row : background change + subtle glow
- Section expand/collapse : chevron anime ▲/▼
- En-tête cliquable : cursor pointer

---

## Composants

### 1. Header & Score Card

**Layout :**
```
┌─────────────────────────────────────────┐
│ 📊 CryptoScanner Pro    Lundi 5 mai 2026
│ Morning Brief · Membres            08:42
│
│ ┌──────────────────────────────────┐
│ │ 72 / 100                         │
│ │ BULLISH                          │
│ │ [████████████░░░░░░] (barre %)   │
│ │                                  │
│ │ F&G 68 (Greed) | BTC +2.1%       │
│ │ OI $8.2B | Funding +0.05%        │
│ └──────────────────────────────────┘
└─────────────────────────────────────────┘
```

**Style détails :**
- Header : Background linear-gradient bleu → or subtil
- Logo "📊 CryptoScanner Pro" : 20px gold bold
- Date/heure : right-align, 11px gris
- Score card : Background `rgba(30,30,48,0.6)`, padding 20px
- Score (72) : 72px bold, color = sentiment color (vert/rouge/gold)
- Signal text (BULLISH) : 20px bold, color = sentiment
- Barre progression : width 100%, height 10px, linear-gradient (red → gold → green)
- Micro-stats : 2 lignes, format `Label value | Label value`, 13px

### 2. Sections (Expand/Collapse)

**Markup :**
```html
<div class="sec">
  <div class="sec-head" onclick="tog(this)">
    <span>🪙 Altcoins</span>
    <span>▼</span>
  </div>
  <div class="sec-body"><!-- Contenu --></div>
</div>
```

**Style :**
- `.sec-head` : Background `rgba(0,0,0,0.3)`, padding 13px 18px, cursor pointer
- `.sec-head:hover` : Background `rgba(37,37,64,0.5)`
- Border-bottom : 2px gold
- `.sec-body` : display none par défaut, padding 16px 18px
- `.sec.open .sec-body` : display block
- Chevrons animate : ▲ quand open, ▼ quand closed

### 3. Tableaux (Interactif Pro+)

**Structure générale :**
- Max-width: 100%
- Border-collapse: collapse
- Background : `linear-gradient(135deg, #0a0e27 0%, #1a1a3a 100%)`
- Font : Segoe UI, 14px

**Thead (Headers) :**
- Background : `rgba(0,0,0,0.3)` avec dégradé vers `rgba(255,215,0,0.1)`
- Border-bottom : 2px solid `#ffd700`
- Border-top : 1px solid `rgba(255,215,0,0.2)`
- Th : padding 14px 16px, color `#ffd700` (première colonne) ou `#aaa` (autres)
- Font-size : 11px UPPERCASE, letter-spacing 0.8px
- Font-weight : 700 (first col) ou 600 (others)
- Cursor pointer (pour tri cliquable)

**Tbody (Rows) :**
- Alternating backgrounds :
  - Row 1,3,5... : `rgba(255,255,255,0.02)`
  - Row 2,4,6... : `rgba(0,0,0,0.2)`
- Border-bottom : 1px solid `rgba(255,255,255,0.05)`
- Border-left : 4px solid (vert `#4caf50` si positif, rouge `#f44336` si négatif)
- Transition : `all 0.25s ease`
- **Hover** : Background change vers sentiment color (ex: `rgba(76,175,80,0.15)` pour vert)
- Td : padding 14px 16px

**Colonnes spécifiques :**

1. **Ranking (№)** :
   - Width: 30px, text-align center
   - Content: `🥇 1`, `🥈 2`, `🥉 3`
   - Color : sentiment color (vert/rouge), 12px bold

2. **Symbole** :
   - Color: `#ffd700`, font-weight 700, font-size 15px
   - Cliquable (tri), cursor pointer

3. **Nom** :
   - Color: `#ccc`, font-size 13px
   - Muted, lisibilité secondaire

4. **Performance (barre %)** :
   - Flexbox : align-items center, gap 6px
   - Barre : width 50px, height 5px, border-radius 2px
   - Fill : gradient 0 → X% (vert ou rouge)
   - Unfill : rgba(same color, 0.3)
   - Text : bold, 13px, color sentiment, min-width 50px

5. **Prix** :
   - Text-align right
   - Color: `#aaa`, font-size 13px
   - Format: `$XXX.XX`

**S'applique à :**
- Altcoins (5-10 rows)
- COT Positions (3-4 rows)
- ETF Flows (2 rows)
- Dérivés (2 rows)

### 4. BTC/ETH Cards

**Layout :**
```
<div style="display: flex; gap: 12px; flex-wrap: wrap; margin-top: 8px;">
  <div class="ccard">...</div>
  <div class="ccard">...</div>
</div>
```

**Style :**
- `.ccard` : Background `rgba(37,37,64,0.8)`, padding 16px, flex 1, min-width 200px
- Border-left : 4px gold
- Border-radius : 8px
- Transition : `all 0.2s ease`
- **Hover** : Background `rgba(37,37,64,1)`, subtle shadow

**Content :**
- Symbole (₿/Ξ) : 16px bold, color gold
- Prix : 22px bold, color white
- Change 24h : 16px bold, color sentiment
- Change 7j : 11px muted, gris
- Analyse : 11px italic, gris, margin-top 6px

### 5. Fear & Greed Card

**Layout :**
```
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
  <div>AUJOURD'HUI: 68</div>
  <div>HIER: 62</div>
</div>
```

**Style :**
- Grid 2 colonnes
- Chaque cell : background `rgba(37,37,64,0.6)`, padding 14px, border-radius 8px
- Center-aligned
- Label : 10px uppercase, color `#888`, margin-bottom 4px
- Value : 36px bold, color gold ou sentiment
- Classification : 11px, color `#aaa` ou sentiment

### 6. Gagnants/Perdants

**Layout :**
```
<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 12px;">
  <div>🟢 Gagnants</div>
  <div>🔴 Perdants</div>
</div>
```

**Style :**
- Grid 1fr 1fr
- Chaque section : padding 10px, border-radius 6px
- Gagnants : background `rgba(76,175,80,0.1)`, border-left 3px `#4caf50`
- Perdants : background `rgba(244,67,54,0.1)`, border-left 3px `#f44336`
- Titre : 12px bold, color vert/rouge respectif, margin-bottom 6px
- Items : format `▸ SYMBOL +X.XX%`, font-size 12px, padding 2px 0

### 7. News & Macro (listes)

**Markup :**
```html
<ul style="list-style: none; margin-top: 8px;">
  <li>▸ Item 1</li>
  <li>▸ Item 2</li>
</ul>
```

**Style :**
- List-style : none
- Chaque li : padding 8px 0, border-bottom 1px solid `rgba(255,255,255,0.05)`
- Bullet ▸ : inline, color gold, flex-shrink 0
- Text : color `#ccc`, font-size 13px, flex 1
- Layout : display flex, gap 8px

### 8. COT Section

**Header** :
- Format : `📊 COT — Positionnement | 🟢 HAUSSIER`
- Emoji sentiment inline
- Color : vert/rouge/gold selon signal

**Content** :
- Rows simples (pas de barres)
- Format : `Label: value`
- Gros nombres : format `+45,234` ou `1.2M`
- **Bloc "Alignement"** : 
  - Background : `rgba(76,175,80,0.1)` (vert) ou `rgba(244,67,54,0.1)` (rouge)
  - Border-left : 3px colored
  - Padding : 10px 12px
  - Border-radius : 6px
  - Margin-top : 10px
  - Font : 13px, bold label

### 9. Footer

```
© 2026 CryptoScanner Pro · Données techniques
Brief expire à minuit · Usage personnel
```

- Text-align : center
- Padding : 30px 20px
- Border-top : 1px solid `#1a1a28`
- Color : `#444`, font-size 12px
- Margin-top : 40px

---

## Responsive Design

- **Desktop (>600px)** : Layout complet, flex horizontal
- **Mobile (<600px)** : 
  - Stack vertical
  - Padding réduit : 12px
  - Font-size réduite : -1-2px
  - Tables scrollable horizontalement (ou collapse)

---

## Animations & Transitions

- Hover sur rows : `transition: all 0.25s ease`
- Expand/collapse sections : chevron ▲/▼ (no CSS animation, just toggle)
- Score barre : static, pas d'animation
- Couleurs : smooth transition au hover

---

## Données & Binding

La page doit afficher :
1. **Score** → `analysis.score.valeur` et `.signal`
2. **BTC/ETH** → `analysis.btc` et `.eth` (prix, change_24h, change_7j, analyse)
3. **Altcoins** → `analysis.altcoins` (nom, symbole, variation_24h)
4. **Gagnants/Perdants** → `analysis.top_gagnants` et `.top_perdants`
5. **Dérivés** → `analysis.derives` (funding, OI, analyse)
6. **ETF** → `analysis.etf` (BTC, ETH flux, analyse)
7. **COT** → `analysis.cot` (signal BTC/ETH, lf_net, am_net, oi, alignement)
8. **Fear & Greed** → `analysis.fear_greed` (valeur, label, interpretation)
9. **Macro** → `analysis.macro` (liste des événements)
10. **News** → `analysis.news` (liste des news)
11. **Résumé** → `analysis.resume` (biais, drivers, risques, catalyseurs)

Tous les champs doivent être bindés via Python (Jinja2) lors de la génération HTML.

---

## Fichier à modifier

- **`morning_brief.py`** : Fonction `build_brief_html()`
  - Ligne ~420-639 : HTML génération
  - Ajouter CSS cohérent
  - Refactoriser le HTML avec les designs de cette spec

---

## Checklist de validation

- [ ] Gradient bleu/violet visible et subtil
- [ ] Gold accents sur headers et symboles
- [ ] Tableaux avec ranking 🥇🥈🥉
- [ ] Barres de progression % visuelles
- [ ] Hover effects sur rows
- [ ] Bordures latérales coloriées (vert/rouge)
- [ ] Typographie hiérarchisée (h2, h3, body)
- [ ] Espacements cohérents
- [ ] Sections expand/collapse fonctionnelles
- [ ] Responsive mobile OK
- [ ] Toutes les données bindées correctement
- [ ] Fear & Greed 2-colonnes
- [ ] COT avec emoji sentiment inline
- [ ] Footer avec copyright
- [ ] Pas de bugs HTML/CSS

---

## Notes d'implémentation

1. **CSS interne** : Tout le CSS doit être dans un `<style>` tag en haut du HTML (pour Telegram compatibility)
2. **Pas de JavaScript** : Utiliser uniquement CSS transitions + onclick handlers simples pour expand/collapse
3. **Format Jinja2** : Utiliser `{{ variable }}` pour binder les données Python
4. **Variables helper** : 
   - `clr(value)` → retourne `#4caf50` si positif, `#f44336` si négatif
   - `pct(value)` → retourne `+X.XX%` ou `-X.XX%`
   - `fmtVol(value)` → retourne `$XXM` ou `$XXB`

---

**Status** : Approuvé ✅  
**Prêt pour** : Implementation planning
