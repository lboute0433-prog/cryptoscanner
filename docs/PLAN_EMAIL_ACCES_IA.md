# CryptoScanner - Recap Email, Acces, IA et Priorites

Date: 2026-04-08

## 1. Objectif du document

Ce document sert de point de reprise rapide sur les chantiers deja traites dans CryptoScanner, ce qui est en production dans le code, ce qui reste a valider apres redeploiement, et ce qui est volontairement reporte.

Il couvre principalement:

- l'administration,
- les roles et acces,
- l'email,
- l'IA,
- le bloc COT / ETF,
- les news et le calendrier,
- la logique de sources de donnees crypto.

## 2. Recap des modifications deja integrees

### 2.1 Admin

Ce qui a ete corrige:

- bouton `ADMIN` de l'accueil remplace par un vrai lien vers `/admin`,
- ajout d'un formulaire HTML de secours vers `/admin/login`,
- correction d'une erreur JavaScript qui bloquait la page admin,
- ajout de l'email utilisateur dans la table admin,
- ajout du role et du statut d'abonnement dans les donnees admin,
- amelioration du bloc Morning Brief admin,
- ajout d'un bloc de diagnostic SMTP dans l'admin,
- ajout d'un test d'envoi email admin.

Ce qui doit etre visible en admin apres redeploiement:

- colonne `EMAIL`,
- colonne `ABONNEMENT`,
- roles modernes: `visitor`, `member`, `paid`, `vip`, `admin`, `banned`,
- statuts affiches en francais: `Inactif`, `Essai`, `Actif`, `En retard`, `Annule`.

### 2.2 Roles, abonnements et acces

Le projet ne repose plus uniquement sur `admin / non-admin`.

Modele maintenant en place:

- roles:
  - `visitor`
  - `member`
  - `paid`
  - `vip`
  - `admin`
  - `banned`
- statuts d'abonnement:
  - `inactive`
  - `trial`
  - `active`
  - `overdue`
  - `canceled`

Compatibilite assuree:

- `viewer` est remappe vers `visitor`
- `trader` est remappe vers `member`

Restrictions deja appliquees:

- `member+`:
  - portefeuille,
  - journal,
  - alertes,
  - watchlist,
  - exchange connect,
  - smart features utilisateur.
- `paid+`:
  - COT,
  - ETF,
  - open interest,
  - liquidations,
  - analyse IA,
  - backtests,
  - fonctions premium.
- `admin`:
  - blacklist globale,
  - certains controles globaux,
  - rapports manuels,
  - routes admin.

Les gardes existent maintenant:

- cote interface,
- cote backend.

### 2.3 COT / ETF

Ce qui a ete corrige:

- page COT reorganisee pour etre plus lisible,
- changement de date COT mieux reflechi visuellement,
- fallback ETF ameliore quand la source principale repond mal,
- ajout des ETF ETH,
- ajout des totaux ETF BTC et ETH,
- extension des rapports Telegram ETF pour inclure ETH,
- verrouillage du COT en premium `paid+`.

Limite connue:

- si la source officielle ETF ne repond pas, les chiffres de secours restent des estimations et doivent etre consideres comme tels.

### 2.4 News / Macro / Calendrier

Ce qui a ete etendu:

- nouvelles categories:
  - `Adoption`
  - `Geopolitique`
- nouvelles sources FR:
  - CoinTelegraph FR
  - Cryptoast
  - Journal du Coin
  - Coinactu
  - The Coin Tribune
- nouvelles sources EN:
  - CoinDesk
  - CoinTelegraph
  - Decrypt
  - Bitcoin Magazine
  - The Block
  - BeInCrypto
  - Reuters Markets
  - Yahoo Finance

Comportement calendrier maintenant attendu:

- sur l'accueil, le bloc macro privilegie les dernieres stats publiees les plus recentes,
- sur le calendrier complet, une stat publiee affiche:
  - la valeur,
  - une lecture courte,
  - un petit texte du type `Plutot bon`, `Plutot mauvais`, `Conforme`.

### 2.5 IA

Le projet dispose maintenant d'une couche commune:

- `ai_provider.py`

Ce qui est deja branche:

- Morning Brief via la couche commune,
- analyse investisseur via `/api/ai/analyze`,
- support Groq et Anthropic,
- nettoyage progressif des references "Claude" dans l'interface,
- gestion plus generique des cles utilisateur.

Strategie retenue:

- Groq comme chemin principal si une cle Groq est presente,
- Anthropic conserve en fallback si besoin.

Etat actuel:

- unification fonctionnelle en place,
- harmonisation de libelles encore perfectible dans toute l'interface.

### 2.6 Sources de donnees crypto

Strategie retenue par module:

- `CoinGecko`:
  - couverture large,
  - discovery,
  - univers crypto et investor.
- `Binance` ou `Kraken`:
  - scanner spot principal,
  - signaux lies a un marche executable.
- `Bybit` et `OKX`:
  - multi-exchange,
  - perps,
  - vues de marche secondaires.

Conclusion de design:

- ne pas limiter tout le projet a une seule source,
- utiliser une source maitresse differente selon le module.

## 3. Sujet email

### 3.1 Ce qui a ete fait

Le systeme email a ete renforce:

- diagnostic SMTP visible dans l'admin,
- test d'envoi manuel admin,
- support `SSL` et `STARTTLS`,
- support `SMTP_LOGIN`,
- support `SMTP_FROM_EMAIL`,
- retour d'erreur plus clair dans les reponses backend,
- suppression du faux message d'activation email a l'inscription.

### 3.2 Diagnostic actuel

Le code email est mieux structure, mais l'envoi de production n'est pas encore valide de bout en bout.

Constat fait pendant les tests:

- Gmail SMTP a bien ete configure,
- mais l'envoi a timeout depuis l'hebergement,
- le probleme semble plus lie a l'environnement d'envoi qu'a la logique applicative.

Resend a ete prepare comme piste plus propre:

- le code accepte maintenant une configuration compatible,
- mais l'integration n'est pas finalisee faute de domaine d'envoi verifie.

### 3.3 Decision actuelle

Pour le moment:

- on reporte la finalisation email,
- on continue les autres chantiers produit,
- on reprendra l'envoi proprement avec:
  - un vrai domaine,
  - un provider transactionnel,
  - ou une infra plus maitrisee.

## 4. Matrice d'acces recommandee

| Module / Zone | Visiteur | Membre | Payant | VIP | Admin |
| --- | --- | --- | --- | --- | --- |
| Dashboard public | Oui | Oui | Oui | Oui | Oui |
| Profil utilisateur | Limite | Oui | Oui | Oui | Oui |
| Watchlist / alertes | Non | Oui | Oui | Oui | Oui |
| Portfolio / journal | Non | Oui | Oui | Oui | Oui |
| COT / ETF / institutionnel | Non | Non | Oui | Oui | Oui |
| Analyse IA investisseur | Non | Non | Oui | Oui | Oui |
| Backtests | Non | Non | Oui | Oui | Oui |
| Smart signals avances | Non | Oui | Oui | Oui | Oui |
| Multi-exchange | Non | Non | Oui | Oui | Oui |
| Blacklist globale | Non | Non | Non | Non | Oui |
| Gestion utilisateurs | Non | Non | Non | Non | Oui |

## 5. Points encore a verifier apres redeploiement

- affichage exact des nouveaux roles et statuts dans l'admin,
- validation du bloc COT sur un compte non premium et premium,
- verification visuelle finale du calendrier sur l'accueil,
- verification du wording IA partout ou un ancien texte "Claude" pourrait rester,
- validation utilisateur de la nouvelle logique de sources de marche.

## 6. Prochaines priorites conseillees

Ordre recommande:

1. finaliser le nettoyage des labels et messages restants,
2. consolider le portfolio multi-exchange,
3. uniformiser encore les modules investor / IA,
4. preparer une vraie migration email vers domaine + provider transactionnel,
5. a terme, envisager une infra plus stable si le projet grossit.

## 7. Resume court

Le projet est nettement plus structure qu'au debut de la session:

- admin plus fiable,
- acces par role reellement poses,
- COT premium verrouille,
- news et calendrier etendus,
- couche IA unifiee,
- logique de sources de donnees crypto clarifiee.

Le principal sujet volontairement laisse en attente est l'email de production, qui depend maintenant davantage de l'infrastructure et du provider que du code applicatif lui-meme.
