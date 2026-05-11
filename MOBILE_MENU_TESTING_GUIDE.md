# Guide de Test - Menu Hamburger iOS

## 📋 État du Code

✅ **Status**: Menu hamburger complètement implémenté  
✅ **Commit**: `56f4267` - feat: force mobile menu on iOS with device media queries  
✅ **Fichier**: `templates/index.html`  

## 🎯 Ce qui a été fait

### 1. Structure HTML (lignes 12473-12479)
```html
<nav class="mobile-nav">
  <div class="mobile-nav-items">
    <button class="mobile-nav-btn active" id="mn-home" onclick="mobileGo('dashboard')">
      <span class="mn-icon">🏠</span>HOME
    </button>
    <button class="mobile-nav-btn" id="mn-analyse" onclick="toggleMobileSubmenu('sub-analyse','mn-analyse')">
      <span class="mn-icon">📊</span>ANALYSE
    </button>
    <!-- ... autres boutons ... -->
  </div>
</nav>
```

### 2. CSS Styles (lignes 972-984)
- `.mobile-nav` - Barre de navigation fixée en bas
- `.mobile-nav-btn` - Boutons du menu
- `.mobile-submenu` - Sous-menus avec animation
- Styles actifs et hover

### 3. CSS Media Queries - iOS & Tablettes (lignes 1033-1043)

**Portrait (iPhone, iPad):**
```css
@media (max-device-width:812px) and (orientation:portrait) {
  nav { display:none !important; }
  .mobile-nav { display:block !important; }
  body { padding-bottom:68px !important; }
}
```

**Landscape (iPad):**
```css
@media (max-device-width:1024px) and (orientation:landscape) {
  nav { display:none !important; }
  .mobile-nav { display:block !important; }
  body { padding-bottom:68px !important; }
}
```

### 4. JavaScript Functions (lignes 12484-12508)
- `toggleMobileSubmenu()` - Ouvre/ferme les sous-menus
- `closeMobileSubmenu()` - Ferme les sous-menus
- `mobileGo()` - Navigation et mise à jour des états actifs

## 📱 Instructions de Test

### Sur iPhone / iPad avec Firefox iOS

1. **Ouvrir le site**
   - URL: https://46.225.234.71:5000
   - Vérifier que le certificat SSL est accepté

2. **Vérifier le menu hamburger**
   - Le menu de navigation du haut devrait être CACHÉ
   - Une barre avec 5 boutons devrait apparaître EN BAS:
     - 🏠 HOME
     - 📊 ANALYSE  
     - 🌐 DATA
     - 💼 TRADING
     - ⋯ PLUS

3. **Tester les boutons**
   - Tapper sur HOME → Va à la page dashboard
   - Tapper sur ANALYSE → Affiche sous-menu avec:
     - COT, Market, Signals, Heatmap, Smart Signals, Forex, Indices, Mood, Investor
   - Tapper sur un sous-menu → Change de page
   - Tapper sur le bouton actif → Ferme le sous-menu

4. **Tester l'Escape**
   - Quand un sous-menu est ouvert
   - Tapper en dehors → Le sous-menu se ferme

5. **Orientation**
   - Portrait (812px max): Menu mobile visible
   - Landscape (1024px max): Menu mobile visible
   - Rotation: Menu s'adapte correctement

### Sur Desktop/PC (regression test)

1. **Navigation normale**
   - Menu horizontale du haut visible
   - Pas de menu mobile en bas
   - Tous les onglets accessibles

2. **Responsive desktop**
   - Redimensionner en moins de 768px
   - Menu mobile apparaît
   - Menu du haut disparaît

### Vérifier les Permissions

- [ ] FREE: Watchlist disabled
- [ ] MEMBRE: Watchlist avec max 5 items
- [ ] PAYANT: Watchlist avec max 10 items
- [ ] VIP: Watchlist illimité
- [ ] Alerts: Même system que watchlist

## 🔧 Cache Clearing (IMPORTANT)

Si le menu n'apparaît pas:

**Sur iOS Firefox:**
- Settings → Privacy → Clear History, Website Data, Cookies
- Ou: Swipe sur l'onglet vers la gauche → "Fermer l'onglet"
- Ouvrir un nouvel onglet et recharger

**Ou sur le site:**
- `Ctrl+Shift+Delete` (Windows) ou `Cmd+Shift+Delete` (Mac)
- Cocher "Cache" et "Cookies"
- Cliquer "Clear Now"

## 📊 Vérification Technique

### Dans la Console (DevTools)

```javascript
// Vérifier que les éléments existent
document.querySelector('.mobile-nav')  // Doit retourner l'élément nav

// Vérifier l'état du CSS
getComputedStyle(document.querySelector('.mobile-nav')).display
// En portrait iOS: "block"
// En landscape iPad: "block"  
// En desktop: "none"

// Tester les fonctions
mobileGo('cot')  // Doit changer vers la page COT
toggleMobileSubmenu('sub-analyse', 'mn-analyse')  // Doit afficher le sous-menu
```

### Vérifier le Commit

```bash
git log --oneline templates/index.html | head -1
# Doit afficher: 56f4267 feat: force mobile menu on iOS with device media queries

git show 56f4267 | grep -A 3 "max-device-width:812px"
# Doit afficher les media queries
```

## ⚠️ Problèmes Connus & Solutions

| Problème | Cause | Solution |
|----------|-------|----------|
| Menu n'apparaît pas sur iOS | Cache ou déploiement | Effacer le cache du navigateur |
| Menu apparaît sur desktop | Media query 768px | Redimensionner > 768px |
| Boutons ne répondent pas | JavaScript non chargé | Vérifier console pour erreurs |
| Sous-menu décalé | Pas de safe-area-inset | Vérifier CSS ligne 972 |
| Permissions perdues | Hoisting error | Vérifier TAB_ACCESS_RULES avant showTab() |

## 🚀 Déploiement

Le code est prêt à être déployé sur le serveur Hetzner.

**Fichier de déploiement:**
```bash
./deploy_mobile_menu.py  # Script SFTP + restart service
```

**Ou manuellement:**
```bash
# 1. Copier index.html sur le serveur
scp templates/index.html root@46.225.234.71:/app/templates/

# 2. Redémarrer le service
ssh root@46.225.234.71 "sudo systemctl restart cryptoscanner"

# 3. Vérifier les logs
ssh root@46.225.234.71 "sudo journalctl -u cryptoscanner -n 5"
```

## ✅ Checklist de Validation

- [ ] Menu hamburger visible sur iPhone portrait
- [ ] Menu hamburger visible sur iPad landscape
- [ ] Boutons HOME/ANALYSE/DATA/TRADING/PLUS cliquables
- [ ] Sous-menus s'ouvrent/ferment correctement
- [ ] Permissions tier fonctionnent (FREE/MEMBRE/PAYANT/VIP)
- [ ] Navigation fonctionne (pas de liens cassés)
- [ ] Données arrivent correctement (websocket ok)
- [ ] Desktop normal (pas de régression)
- [ ] Cache des utilisateurs clear
- [ ] Service redémarré après déploiement

## 📞 Support

Si le menu ne fonctionne pas:
1. Vérifier le cache (Ctrl+Shift+Delete)
2. Vérifier la console pour erreurs JS
3. Vérifier que le service est running
4. Vérifier les logs du serveur
5. Redéployer avec `deploy_mobile_menu.py`

---
**Last Updated**: 2026-05-11  
**Commit**: 56f4267  
**Status**: ✅ Ready to test
