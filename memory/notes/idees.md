# Idées — CryptoScanner Pro

<!-- Idées futures, fonctionnalités à explorer, pistes -->



![[IMG_2771.png|465]]






![[IMG_2773.png]]



![[IMG_2774.png]]




![[Intégration_de_Données_Crypto_dans_un_Dashboard_Temps_Réel.pdf]]
 Tu reçois le fichier PDF Intégration_de_Données_Crypto_dans_un_Dashboard_Temps_Réel.pdf.
Tu dois implémenter le module Heatmap OI + Volume pour CryptoScanner Pro dans une architecture temps réel.
Fonctionnalité principale : heatmap cliquable multi-crypto

L’utilisateur voit une heatmap globale qui liste toutes les cryptos disponibles sur Binance Futures (ou au minimum les 20 plus grosses par volume).
Chaque ligne affiche :

    Le symbole de la crypto

    L’intensité combinée Open Interest + Volume (sous forme de valeur et de couleur)

    Le volume sur 24h

    La variation de l’Open Interest sur la dernière heure

Lorsque l’utilisateur clique sur une ligne (une crypto), tout le dashboard se met à jour :

    Le graphique TradingView change pour afficher cette crypto

    Une heatmap détaillée apparaît sous le graphique, avec des bandes horizontales colorées représentant l’intensité OI + Volume par niveau de prix

    Les zones de liquidité, la structure de marché (HH/HL, Break of Structure, Change of Character) et les scores (trend, volatilité, liquidité, momentum) se rafraîchissent pour la crypto sélectionnée

Backend à développer

Tu exposes deux endpoints API :

Premier endpoint : retourne la heatmap globale pour toutes les cryptos

    Appel : GET /api/heatmap/all

    Retourne une liste : pour chaque crypto, son symbole, son intensité, son volume 24h, sa variation d’OI sur 1h, et une couleur associée (bleu pour faible, orange pour moyen, rouge pour élevé)

Deuxième endpoint : retourne la heatmap détaillée pour une crypto spécifique

    Appel : GET /api/heatmap/{symbole}

    Retourne les niveaux de prix avec leur intensité et leur couleur associée, ainsi qu’un timestamp

Tu peux aussi ajouter un troisième endpoint pour les scores et la structure de marché si cela facilite l’organisation du code.
Sources de données

Tu utilises exclusivement l’API Binance Futures :

    Pour récupérer les données de toutes les cryptos : endpoint REST des tickers 24h

    Pour l’Open Interest : endpoint REST dédié

    Pour le temps réel : WebSocket public de Binance Futures qui diffuse les mises à jour des tickers et des OI

Tu ne codes en dur aucun symbole. La liste des cryptos est dynamique.
Calcul de l’intensité

Pour chaque crypto, tu calcules :

    Une normalisation du volume sur l’ensemble des cryptos disponibles

    Une normalisation de la variation d’Open Interest sur la dernière heure

    L’intensité avec la formule : soixante pour cent du volume normalisé plus quarante pour cent de la variation d’OI normalisée

Le seuil pour les couleurs est le suivant :

    Intensité inférieure à 0,4 → bleu

    Intensité entre 0,4 et 0,7 → orange

    Intensité supérieure à 0,7 → rouge

Ces seuils et la pondération peuvent être modifiés via des variables d’environnement.
Interface utilisateur

La heatmap globale est un composant cliquable. Au chargement de la page, toutes les cryptos sont affichées avec leur intensité. Un clic sur une ligne déclenche un rechargement complet du dashboard pour cette crypto.

Le graphique TradingView change de symbole dynamiquement. La heatmap détaillée se superpose en overlay sur le graphique sous forme de bandes horizontales colorées.

Un panneau latéral ou inférieur affiche les scores, la structure de marché et les zones de liquidité.
Temps réel

Un WebSocket maintient la heatmap globale à jour. Les intensités se rafraîchissent automatiquement toutes les dix secondes maximum sans rafraîchir la page. L’utiliteur n’a pas besoin de cliquer pour voir évoluer les données globales.
Contraintes absolues

    Pas de données forex, uniquement des cryptos

    Pas de symboles codés en dur : la heatmap s’adapte à toutes les paires disponibles

    Le clic est le cœur de l’interaction : une crypto cliquée = tout le dashboard se met à jour

    Le code est modulaire, documenté et sépare clairement backend, frontend et l’overlay TradingView

Livrables

Tu fournis :

    Le code backend avec les deux ou trois endpoints API

    Le code frontend avec la heatmap globale cliquable

    L’intégration de l’overlay TradingView

    Un fichier README expliquant comment lancer le projet, configurer les variables d’environnement et ajouter une nouvelle crypto si nécessaire

Validation attendue

Tu vérifies que :

    La heatmap globale liste bien plusieurs cryptos différentes, pas seulement Bitcoin

    Un clic sur une crypto change bien le graphique, la heatmap détaillée, les scores et les zones

    Les données se mettent à jour en temps réel via WebSocket

