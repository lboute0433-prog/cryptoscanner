
# Verif.md — État des items

## ✅ Traités (session 2026-04-12 20h00)

**1** ✅ Page signaux — tri des colonnes corrigé (sortSignals + ▼/▲)
**2a** ✅ Heatmap / popup graphique — bouton TradingView ajouté dans chart-modal
**2b** ✅ Smart Signals — bloc historique des signaux (table DB + route API + UI filtrable + clic → graphique)
**3** ✅ Page CVD Flow — tableau défilant corrigé (header sticky, overflow propre)
**5** ✅ Mon compte / IA personnelle — dropdown provider Groq/Anthropic/OpenAI + bouton ? procédure
**6** ✅ Création compte — redirection auto vers Mon Compte après inscription
**7** ✅ Permissions par page — matrice complète (visitor/member/paid/admin) + badges nav
**9** ✅ Bloc "Accès limité" — messages dynamiques selon rôle requis vs rôle actuel

## ✅ Traités (session 2026-04-12 22h00)

**4** ✅ Page admin → Paramètres Plateforme — pump_pct(5) / scan_interval(10) / vol_mult(3) / exchange(coingecko) → table SQLite settings via _get_setting/_set_setting, dynamique sans redémarrage

## ⏳ Restant

**10** : Page marchés — affichage "marchés ouverts" le dimanche — logique ou bug ?
  → Crypto 24/7 = logique. Actions (NASDAQ, SP500) fermées week-end = à vérifier si le site les affiche comme ouverts

**11** : Arkham Intelligence (https://intel.arkm.com/)
  → Tracker on-chain : wallets identifiés (exchanges, fonds), gros mouvements
  → Pertinent pour Portfolio Tracker / Wallet Scanner (samedi.md item 5)
  → API publique limitée, données publiques via leur interface
  → Grand chantier — à traiter quand samedi.md item 5 est lancé
