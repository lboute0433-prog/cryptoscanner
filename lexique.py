#!/usr/bin/env python3
"""
CryptoScanner Pro V10 — Lexique & Documentation
Glossaire complet des termes techniques
"""

GLOSSARY = {
    # ── Indicateurs techniques ────────────────────────────────
    "RSI": {
        "full": "Relative Strength Index",
        "category": "indicateur",
        "level": "débutant",
        "emoji": "📈",
        "short": "Mesure si un actif est suracheté ou survendu (0-100)",
        "detail": """Le RSI est un indicateur de momentum qui mesure la vitesse et l'amplitude des mouvements de prix.
        
• RSI < 30 : Zone de SURVENTE — l'actif a peut-être trop baissé, rebond possible
• RSI > 70 : Zone de SURACHAT — l'actif a peut-être trop monté, correction possible  
• RSI = 50 : Zone neutre

Le RSI est calculé sur 14 périodes par défaut. Plus la période est courte, plus le RSI est sensible.""",
        "example": "Bitcoin à RSI 28 = potentiellement survendu, les acheteurs pourraient revenir",
        "related": ["MACD", "Bollinger Bands", "Divergence RSI"]
    },
    "MACD": {
        "full": "Moving Average Convergence Divergence",
        "category": "indicateur",
        "level": "intermédiaire",
        "emoji": "〰️",
        "short": "Indicateur de tendance basé sur la différence entre deux moyennes mobiles",
        "detail": """Le MACD est composé de :
• Ligne MACD : différence entre EMA 12 et EMA 26
• Ligne Signal : EMA 9 du MACD
• Histogramme : différence entre MACD et Signal

SIGNAL D'ACHAT : Ligne MACD croise Signal vers le haut
SIGNAL DE VENTE : Ligne MACD croise Signal vers le bas
MACD > 0 : Tendance haussière
MACD < 0 : Tendance baissière""",
        "example": "MACD croise la ligne Signal vers le haut = signal d'achat potentiel",
        "related": ["RSI", "EMA", "Tendance"]
    },
    "EMA": {
        "full": "Exponential Moving Average",
        "category": "indicateur",
        "level": "débutant",
        "emoji": "📊",
        "short": "Moyenne mobile qui donne plus de poids aux prix récents",
        "detail": """L'EMA est une moyenne mobile qui accorde plus d'importance aux données récentes qu'une simple moyenne (SMA).
        
• EMA 20 : Tendance à court terme
• EMA 50 : Tendance à moyen terme  
• EMA 200 : Tendance long terme (très importante)

Si le prix est au-dessus de l'EMA = tendance haussière
Si le prix est en-dessous de l'EMA = tendance baissière

Golden Cross : EMA 50 croise EMA 200 vers le haut → signal haussier fort
Death Cross : EMA 50 croise EMA 200 vers le bas → signal baissier fort""",
        "example": "Prix au-dessus de l'EMA 200 = marché en tendance haussière long terme",
        "related": ["SMA", "MACD", "Tendance"]
    },
    "Bollinger Bands": {
        "full": "Bandes de Bollinger",
        "category": "indicateur",
        "level": "intermédiaire",
        "emoji": "📏",
        "short": "Enveloppe autour du prix basée sur la volatilité",
        "detail": """Les Bandes de Bollinger sont composées de :
• Bande centrale : EMA 20
• Bande supérieure : EMA 20 + 2 × écart-type
• Bande inférieure : EMA 20 - 2 × écart-type

LECTURE :
• Prix touche la bande supérieure : possible surachat
• Prix touche la bande inférieure : possible survente
• Bandes se resserrent (squeeze) : faible volatilité, explosion imminent
• Bandes s'élargissent : forte volatilité en cours""",
        "example": "Quand les bandes se resserrent fortement, une forte bougie est souvent imminente",
        "related": ["RSI", "ATR", "Volatilité"]
    },
    "ATR": {
        "full": "Average True Range",
        "category": "indicateur",
        "level": "intermédiaire",
        "emoji": "📐",
        "short": "Mesure la volatilité moyenne d'un actif sur une période",
        "detail": """L'ATR mesure l'amplitude moyenne des mouvements de prix.
        
UTILISATION :
• ATR élevé = marché volatil, amplitudes importantes
• ATR faible = marché calme, amplitudes faibles
• Utile pour placer les Stop-Loss (ex: SL = prix - 2×ATR)

L'ATR ne donne pas de direction, uniquement l'amplitude probable.""",
        "example": "ATR BTC à $1500 signifie que BTC bouge en moyenne $1500 par jour",
        "related": ["Volatilité", "Stop-Loss", "Bollinger Bands"]
    },

    # ── Termes institutionnels ────────────────────────────────
    "COT": {
        "full": "Commitment of Traders",
        "category": "institutionnel",
        "level": "avancé",
        "emoji": "🏦",
        "short": "Rapport hebdomadaire de la CFTC montrant les positions des grands acteurs",
        "detail": """Le COT est publié chaque vendredi par la CFTC (régulateur américain).
Il montre les positions des différents acteurs sur les marchés futures :

• LEVERAGED FUNDS (Hedge Funds) : Spéculateurs professionnels
  → Leur position est souvent contrariante (ils ont souvent tort aux extrêmes)
  → Si ils shortent massivement = rebond potentiel imminent

• ASSET MANAGERS : Gestionnaires institutionnels (fonds de pension, etc.)
  → Ils ont généralement raison sur la tendance longue
  → Accumulation = signal haussier

• COMMERCIALS : Producteurs, utilisateurs réels
  → Pour l'or : mines d'or qui se couvrent
  → Leur position opposée au mouvement est normale (couverture)

LECTURE CONTRARIANTE :
Quand les Leveraged Funds sont au maximum de leurs shorts
et que les Asset Managers achètent = signal HAUSSIER fort""",
        "example": "LF avec 70% de shorts sur BTC = signal contrarien haussier très fort",
        "related": ["Leveraged Funds", "Asset Managers", "Open Interest", "CFTC"]
    },
    "Leveraged Funds": {
        "full": "Fonds à Effet de Levier (Hedge Funds)",
        "category": "institutionnel",
        "level": "avancé",
        "emoji": "💼",
        "short": "Hedge funds et fonds spéculatifs utilisant l'effet de levier",
        "detail": """Les Leveraged Funds regroupent principalement les hedge funds et autres fonds spéculatifs.
        
CARACTÉRISTIQUES :
• Utilisent un fort effet de levier (peuvent perdre plus qu'investi)
• Trading actif, prennent souvent des positions contraires
• Souvent "contrariants" aux extrêmes de marché

LECTURE DU COT :
• Leveraged Funds net short (+ de shorts que de longs) = 
  Souvent précède une hausse (squeeze de shorts)
• Leveraged Funds net long = 
  Tendance haussière confirmée OU sommet proche

INDICATEUR CONTRARIEN :
Quand les LF sont à un extrême de shorts → chercher un signal d'achat""",
        "example": "LF avec 15 000 shorts vs 8 000 longs sur BTC = fort potentiel de short squeeze",
        "related": ["COT", "Asset Managers", "Short Squeeze", "Open Interest"]
    },
    "Asset Managers": {
        "full": "Gestionnaires d'actifs institutionnels",
        "category": "institutionnel",
        "level": "avancé",
        "emoji": "🏛️",
        "short": "Fonds de pension, assurances, fonds d'investissement traditionnels",
        "detail": """Les Asset Managers sont les grands gestionnaires institutionnels :
fonds de pension, compagnies d'assurance, fonds souverains.

CARACTÉRISTIQUES :
• Positions longues uniquement ou quasi
• Horizons d'investissement long (mois/années)
• Suivre leur accumulation = signal haussier fiable
• Leur distribution = signal baissier sérieux

LECTURE DU COT :
• Asset Managers accumulent (net long en hausse) → tendance haussière confirmée
• Asset Managers distribuent (net long en baisse) → prudence, possible correction""",
        "example": "AM passant de 5000 à 8000 longs sur 4 semaines = forte accumulation institutionnelle",
        "related": ["COT", "Leveraged Funds", "Open Interest"]
    },
    "Open Interest": {
        "full": "Intérêt Ouvert",
        "category": "institutionnel",
        "level": "intermédiaire",
        "emoji": "📈",
        "short": "Nombre total de contrats futures ouverts sur un marché",
        "detail": """L'Open Interest (OI) représente le nombre total de contrats futures qui sont ouverts et non encore clôturés.

LECTURE :
• OI en hausse + Prix en hausse = Tendance haussière forte (nouveaux acheteurs entrent)
• OI en hausse + Prix en baisse = Tendance baissière forte (nouveaux vendeurs entrent)
• OI en baisse + Prix en hausse = Rebond technique (positions courtes fermées = short squeeze)
• OI en baisse + Prix en baisse = Correction saine (longs ferment leurs positions)

PIÈGE :
Un OI très élevé signifie qu'il y a beaucoup de positions ouvertes.
Si le marché bouge contre la majorité = liquidations massives possibles""",
        "example": "BTC OI à $18B avec prix en hausse = tendance haussière solide soutenue par nouveaux capitaux",
        "related": ["Liquidations", "Funding Rate", "Leveraged Funds"]
    },
    "Funding Rate": {
        "full": "Taux de Financement",
        "category": "futures",
        "level": "intermédiaire",
        "emoji": "💸",
        "short": "Coût de maintien d'une position sur les contrats futures perpétuels",
        "detail": """Le Funding Rate est un mécanisme des exchanges pour maintenir le prix des futures proches du spot.

FONCTIONNEMENT (toutes les 8h généralement) :
• Funding positif : Les longs paient les shorts
  → Marché biaisé vers la hausse (beaucoup de longs)
  → Signal baissier contrarien si très élevé

• Funding négatif : Les shorts paient les longs
  → Marché biaisé vers la baisse (beaucoup de shorts)  
  → Signal haussier contrarien si très négatif

INTERPRÉTATION :
• Funding > 0.05% = Surachat, correction possible
• Funding < -0.05% = Survente, rebond possible
• Funding ≈ 0% = Marché équilibré""",
        "example": "Funding BTC à +0.08% = trop de longs, les bears peuvent attaquer",
        "related": ["Open Interest", "Liquidations", "Futures Perpétuels"]
    },
    "Liquidation": {
        "full": "Liquidation de position",
        "category": "futures",
        "level": "intermédiaire",
        "emoji": "💧",
        "short": "Fermeture forcée d'une position à effet de levier par l'exchange",
        "detail": """Une liquidation se produit quand une position avec levier perd trop de valeur.
L'exchange ferme alors automatiquement la position pour éviter une dette.

EXEMPLE :
Tu achètes $1000 de BTC avec ×10 levier = position de $10 000
Si BTC baisse de 10% → tu perds $1000 = 100% de ta mise → LIQUIDATION

IMPACT SUR LE MARCHÉ :
• Liquidations massives de longs = ventes forcées → accélère la baisse
• Liquidations massives de shorts = rachats forcés → accélère la hausse

LECTURE :
• Beaucoup de longs liquidés → pression vendeuse, prudence
• Beaucoup de shorts liquidés → pression acheteuse, "short squeeze"

CONSEIL :
Ne jamais utiliser plus de ×3 levier si débutant""",
        "example": "100M$ de longs liquidés en 1h = vente massive, le prix peut encore baisser",
        "related": ["Open Interest", "Effet de Levier", "Funding Rate", "Short Squeeze"]
    },

    # ── Patterns de prix ──────────────────────────────────────
    "Engulfing": {
        "full": "Bougie Englobante",
        "category": "pattern",
        "level": "intermédiaire",
        "emoji": "🕯️",
        "short": "Pattern de retournement : une bougie englobe entièrement la précédente",
        "detail": """L'Engulfing est l'un des patterns de retournement les plus fiables.

ENGULFING HAUSSIER :
• Première bougie : rouge (baissière)
• Deuxième bougie : verte (haussière) qui englobe entièrement la rouge
• Signal : retournement à la hausse probable
• Fiabilité : 75-85%

ENGULFING BAISSIER :
• Première bougie : verte (haussière)
• Deuxième bougie : rouge (baissière) qui englobe entièrement la verte
• Signal : retournement à la baisse probable
• Fiabilité : 75-85%

CONFIRMATION RECOMMANDÉE :
Attendre une 3ème bougie dans la direction du signal avant d'entrer""",
        "example": "Après une baisse de 3 jours, un Engulfing haussier = fort signal de rebond",
        "related": ["Morning Star", "Evening Star", "Marteau", "Doji"]
    },
    "Doji": {
        "full": "Doji",
        "category": "pattern",
        "level": "débutant",
        "emoji": "✙",
        "short": "Bougie avec ouverture et clôture quasiment identiques — indécision",
        "detail": """Le Doji apparaît quand le prix ouvre et clôture au même niveau (ou très proche).
Il représente l'indécision entre acheteurs et vendeurs.

TYPES DE DOJI :
• Doji classique : ouverture = clôture, mèches équilibrées
• Doji Libellule : longue mèche basse, corps en haut → bullish
• Doji Tombe : longue mèche haute, corps en bas → bearish
• Doji 4 prix : pas de mèche, très rare

LECTURE :
• Doji après tendance haussière → possible retournement baissier
• Doji après tendance baissière → possible retournement haussier
• Toujours confirmer avec la bougie suivante""",
        "example": "Doji au sommet d'un rally = les acheteurs perdent de la force",
        "related": ["Engulfing", "Marteau", "Morning Star"]
    },
    "Short Squeeze": {
        "full": "Compression des Vendeurs à Découvert",
        "category": "pattern",
        "level": "intermédiaire",
        "emoji": "🔥",
        "short": "Hausse brutale causée par le rachat forcé des positions short",
        "detail": """Un Short Squeeze se produit quand un actif monte fortement, forçant les vendeurs à découvert à racheter leurs positions en urgence, ce qui amplifie la hausse.

MÉCANISME :
1. Beaucoup de traders shortent un actif (parient sur la baisse)
2. L'actif monte quand même
3. Les shorts commencent à perdre de l'argent
4. Pour limiter les pertes, ils rachètent → cela fait encore plus monter
5. Les autres shorts voient la hausse et rachètent aussi → effet boule de neige

COMMENT LE DÉTECTER :
• Open Interest très élevé avec beaucoup de positions short
• Funding Rate très négatif (shorts paient)
• Volume élevé sur une hausse soudaine
• COT : Leveraged Funds très short""",
        "example": "GameStop 2021 = short squeeze classique, prix multiplié ×20 en quelques jours",
        "related": ["Liquidations", "Funding Rate", "Open Interest", "COT"]
    },

    # ── ETF & Institutionnel ──────────────────────────────────
    "ETF": {
        "full": "Exchange Traded Fund",
        "category": "institutionnel",
        "level": "débutant",
        "emoji": "📦",
        "short": "Fonds d'investissement coté en bourse qui réplique un actif",
        "detail": """Un ETF Bitcoin Spot est un fonds coté en bourse qui détient réellement du Bitcoin.
Les investisseurs achètent des parts de ce fonds sans avoir à gérer eux-mêmes du BTC.

PRINCIPAUX ETF BITCOIN SPOT (USA, approuvés 2024) :
• IBIT (BlackRock) : Le plus gros, +$50B d'AUM
• FBTC (Fidelity) : 2ème plus gros
• GBTC (Grayscale) : Historique, converti en ETF
• ARKB (Ark Invest) : De Cathie Wood

POURQUOI C'EST IMPORTANT :
• Les ETF permettent aux grands fonds (retraites, assurances) d'acheter BTC
• Flux entrants (inflows) = achat de BTC → pression haussière
• Flux sortants (outflows) = vente de BTC → pression baissière
• Surveiller les flux quotidiens = indicateur d'appétit institutionnel""",
        "example": "IBIT reçoit +$500M en un jour = BlackRock achète $500M de BTC → haussier",
        "related": ["Flux ETF", "Institutionnel", "Bitcoin"]
    },
    "Fear & Greed Index": {
        "full": "Indice Peur & Avidité",
        "category": "sentiment",
        "level": "débutant",
        "emoji": "😱",
        "short": "Indicateur 0-100 mesurant l'état émotionnel du marché crypto",
        "detail": """L'indice Fear & Greed mesure le sentiment général du marché crypto de 0 (peur extrême) à 100 (avidité extrême).

NIVEAUX :
• 0-24 : 😱 PEUR EXTRÊME → Souvent le meilleur moment pour acheter
• 25-49 : 😟 PEUR → Opportunité d'achat potentielle
• 50 : 😐 NEUTRE
• 51-74 : 😊 AVIDITÉ → Prudence, le marché devient euphorique
• 75-100 : 🤑 AVIDITÉ EXTRÊME → Souvent près d'un sommet

COMPOSANTES :
• Volatilité (25%)
• Volume et momentum (25%)
• Réseaux sociaux (15%)
• Dominance Bitcoin (10%)
• Google Trends (10%)
• Enquêtes (15%)

CITATION WARREN BUFFETT :
"Soyez craintif quand les autres sont avides, soyez avide quand les autres sont craintifs"
""",
        "example": "Fear & Greed à 12 (Peur Extrême) en juin 2022 = fond du marché bear",
        "related": ["Dominance BTC", "Score ADN Marché", "Sentiment"]
    },
    "DXY": {
        "full": "Dollar Index (US Dollar Index)",
        "category": "macro",
        "level": "avancé",
        "emoji": "💵",
        "short": "Indice mesurant la force du dollar américain face à 6 devises",
        "detail": """Le DXY mesure la valeur du dollar américain par rapport à un panier de 6 devises :
Euro (57.6%), Yen (13.6%), Livre Sterling (11.9%), Dollar Canadien (9.1%), Couronne Suédoise (4.2%), Franc Suisse (3.6%).

CORRÉLATION AVEC CRYPTO :
• DXY monte = Dollar fort = les actifs risqués (crypto, actions) baissent souvent
• DXY baisse = Dollar faible = capitaux vers les actifs risqués → crypto monte

POURQUOI ?
Beaucoup d'actifs sont libellés en USD. Quand le dollar est fort,
les investisseurs étrangers ont moins de pouvoir d'achat pour acheter du BTC.

SEUILS IMPORTANTS :
• DXY > 104 : Dollar très fort, prudence sur crypto
• DXY < 100 : Dollar faible, favorable aux cryptos""",
        "example": "DXY monte de 100 à 107 = BTC baisse souvent de 15-25% en conséquence",
        "related": ["Macro", "Corrélation", "Risk-Off", "Risk-On"]
    },
    "Score ADN Marché": {
        "full": "Score ADN du Marché",
        "category": "exclusif",
        "level": "débutant",
        "emoji": "🧬",
        "short": "Score exclusif CryptoScanner 0-100 résumant l'état global du marché",
        "detail": """Le Score ADN Marché est un indicateur exclusif à CryptoScanner Pro.
Il combine plusieurs données en un seul score de 0 à 100.

COMPOSITION :
• Fear & Greed Index (25%)
• Ratio Gainers/Losers (25%)
• Dominance BTC (25%)
• Nombre de signaux actifs (25%)

INTERPRÉTATION :
• 0-25 : 🔴 BEARISH FORT → Prudence maximale
• 26-40 : 🟠 BEARISH → Réduire l'exposition
• 41-60 : ⚪ NEUTRE → Attendre la direction
• 61-75 : 🟡 BULLISH → Opportunités à surveiller
• 76-100 : 🟢 BULLISH FORT → Conditions favorables

Ce score se met à jour toutes les 10 secondes avec le scan du marché.""",
        "example": "Score ADN à 78 = marché en phase bullish, conditions favorables aux achats",
        "related": ["Fear & Greed Index", "Dominance BTC", "Signaux"]
    },

    # ── Bases trading ─────────────────────────────────────────
    "Stop-Loss": {
        "full": "Ordre Stop-Loss (Coupe-Perte)",
        "category": "gestion_risque",
        "level": "débutant",
        "emoji": "🛑",
        "short": "Ordre automatique pour vendre si le prix descend à un niveau défini",
        "detail": """Le Stop-Loss est un ordre qui se déclenche automatiquement si le prix atteint un niveau de perte maximal.

EXEMPLE :
Tu achètes BTC à $70 000. Tu places un SL à $66 500 (-5%).
Si BTC descend à $66 500, ta position est vendue automatiquement.
Tu perds 5% maximum, pas plus.

RÈGLE D'OR :
Ne jamais trader sans Stop-Loss. C'est la règle numéro 1.

PLACEMENT DU STOP-LOSS :
• En-dessous d'un support important
• En-dessous de la dernière bougie basse
• À 1-2× l'ATR sous le point d'entrée

CALCULATEUR INTÉGRÉ :
Utilise notre onglet 🎯 CALCULATEUR pour calculer automatiquement
la taille de position selon ton stop-loss et ton risque maximum.""",
        "example": "Risque 2% du capital, SL à 5% sous l'entrée = taille de position = 40% du capital",
        "related": ["Take Profit", "Ratio R/R", "ATR", "Position Sizing"]
    },
    "Take Profit": {
        "full": "Ordre Take Profit (Prise de Bénéfices)",
        "category": "gestion_risque",
        "level": "débutant",
        "emoji": "✅",
        "short": "Ordre automatique pour vendre quand le prix atteint un objectif de gain",
        "detail": """Le Take Profit (TP) est l'ordre opposé au Stop-Loss.
Il vend automatiquement ta position quand elle atteint ton objectif de profit.

EXEMPLE :
Tu achètes BTC à $70 000 avec SL à $66 500 et TP à $77 000.
Si BTC monte à $77 000, ta position est vendue automatiquement.
Tu empoches +$7 000 par BTC sans avoir à surveiller l'écran.

RATIO R/R (Risque/Récompense) :
SL à -$3 500 | TP à +$7 000 = Ratio 1:2
→ Pour 1€ risqué, tu peux gagner 2€

RÈGLE MINIMUM :
Toujours viser un ratio R/R d'au moins 1:2.
Avec un winrate de 40%, tu es quand même rentable en 1:2.""",
        "example": "Achat à $2000, SL à $1900 (-5%), TP à $2200 (+10%) = ratio R/R de 1:2",
        "related": ["Stop-Loss", "Ratio R/R", "Position Sizing"]
    },
    "Ratio R/R": {
        "full": "Ratio Risque/Récompense",
        "category": "gestion_risque",
        "level": "intermédiaire",
        "emoji": "⚖️",
        "short": "Rapport entre le gain potentiel et la perte maximale d'un trade",
        "detail": """Le Ratio Risque/Récompense est l'une des métriques les plus importantes du trading.

CALCUL :
R/R = Distance vers TP ÷ Distance vers SL

EXEMPLE :
Entrée : $100 | SL : $95 | TP : $115
R/R = ($115-$100) / ($100-$95) = $15 / $5 = 3:1

POURQUOI C'EST CRUCIAL ?
Avec un R/R de 1:2 et un winrate de seulement 40% :
• 4 trades gagnants × 2 = +8
• 6 trades perdants × 1 = -6
• Résultat net = +2 (PROFITABLE malgré 60% de pertes !)

RÈGLE MINIMUM : Toujours viser un R/R ≥ 1:2""",
        "example": "R/R 1:3 = tu peux perdre 2 fois sur 3 et rester profitable si les gains valent 3×",
        "related": ["Stop-Loss", "Take Profit", "Position Sizing"]
    },
    "Position Sizing": {
        "full": "Dimensionnement de Position",
        "category": "gestion_risque",
        "level": "intermédiaire",
        "emoji": "📐",
        "short": "Calcul de la taille optimale d'une position selon son capital et son risque",
        "detail": """Le Position Sizing détermine combien investir dans chaque trade.

FORMULE :
Taille de position = (Capital × % risque) ÷ Distance au SL

EXEMPLE :
Capital : $10 000
Risque par trade : 2% = $200
Entrée BTC : $70 000 | SL : $66 500 (distance : $3 500)
Taille = $200 ÷ $3 500 × $70 000 = 4 000$ (0.057 BTC)

RÈGLES D'OR :
• Ne jamais risquer plus de 2% du capital par trade
• Ne jamais avoir plus de 6% du capital en risque total
• Plus le SL est loin = plus la position est petite

Notre onglet 🎯 CALCULATEUR fait tous ces calculs automatiquement.""",
        "example": "Capital $1000 · Risque 2% · SL 5% sous entrée = investir $400 dans ce trade",
        "related": ["Stop-Loss", "Ratio R/R", "Take Profit"]
    },
    "DCA": {
        "full": "Dollar Cost Averaging",
        "category": "stratégie",
        "level": "débutant",
        "emoji": "🔄",
        "short": "Stratégie d'achat régulier à intervalles fixes pour lisser le prix d'entrée",
        "detail": """Le DCA consiste à investir un montant fixe à intervalles réguliers, quel que soit le prix.

EXEMPLE :
Au lieu d'acheter $1200 de BTC en une fois,
tu achètes $100 de BTC chaque semaine pendant 12 semaines.

AVANTAGES :
• Élimine le stress du "bon moment"
• Lisse automatiquement les prix (tu achètes plus quand c'est bas)
• Simple à mettre en place, pas de surveillance requise
• Parfait pour l'investissement long terme

INCONVÉNIENTS :
• Moins rentable qu'un achat unique au parfait timing
• Le timing parfait est impossible à prédire

IDÉAL POUR :
Investisseurs débutants ou ceux qui veulent investir sans analyse technique.""",
        "example": "DCA $200/mois sur BTC pendant 2 ans = prix moyen très favorable malgré la volatilité",
        "related": ["Position Sizing", "Stratégie", "Long terme"]
    },
    "Pump & Dump": {
        "full": "Manipulation de marché par montée/chute artificielle",
        "category": "risque",
        "level": "débutant",
        "emoji": "⚠️",
        "short": "Manipulation : gonfler artificiellement un prix puis vendre massivement",
        "detail": """Le Pump & Dump est une manipulation de marché illégale mais fréquente sur les petites cryptos.

MÉCANISME :
1. Un groupe achète massivement une crypto à faible capitalisation (Pump)
2. Les réseaux sociaux annoncent des "opportunités" pour attirer les acheteurs
3. Le prix monte fortement attirant les FOMO
4. Le groupe vend tout en une fois (Dump)
5. Le prix s'effondre, les acheteurs tardifs perdent tout

COMMENT RECONNAÎTRE :
• Volume anormal ×10 ou plus sans raison fondamentale
• Coin à faible capitalisation (<$50M)
• Annonces sur Telegram/Discord peu connus
• Montée de 50-200% en quelques heures

CryptoScanner filtre les coins avec volume minimum $2M
pour éviter de signaler les P&D comme de vrais signaux.""",
        "example": "Coin inconnu monte +300% en 2h avec des appels Telegram = probablement un P&D, éviter",
        "related": ["Volume", "Manipulation", "Capitalisation"]
    },
    # ── Price Action & Smart Money ──────────────────────────────
    "FVG": {
        "full": "Fair Value Gap",
        "category": "price_action",
        "level": "avancé",
        "short": "Zone de déséquilibre laissée par un mouvement rapide et violent des prix.",
        "long": "Un FVG se forme quand une bougie se déplace si vite qu'elle laisse un vide entre la mèche haute de la bougie N-1 et la mèche basse de la bougie N+1. Le marché cherche naturellement à combler ces inefficiences. En SMC, les FVG sont des zones clés d'entrée lors du retour du prix.",
        "example": "BTC monte brutalement de 82k à 88k en 1h → FVG entre 83k-84k = zone de support probable au prochain retrace.",
        "related": ["Order Block", "SMC", "Liquidité"]
    },
    "Order Block": {
        "full": "Order Block",
        "category": "price_action",
        "level": "avancé",
        "short": "Dernière bougie opposée avant un mouvement institutionnel fort.",
        "long": "Un Order Block est la dernière bougie haussière avant une forte chute (OB baissier), ou la dernière baissière avant une forte hausse (OB haussier). Ce sont les zones où les institutions ont placé leurs gros ordres. Le prix y retourne souvent pour tester avant de repartir.",
        "example": "Dernière bougie rouge avant un pump de 20% = Order Block haussier. Zone d'achat lors du retrace.",
        "related": ["FVG", "SMC", "Liquidité"]
    },
    "SMC": {
        "full": "Smart Money Concept",
        "category": "price_action",
        "level": "avancé",
        "short": "Approche d'analyse qui suit les mouvements des institutions.",
        "long": "Le SMC analyse les prix selon la logique institutionnelle : accumulation secrète, manipulation des stops (stop hunts), puis distribution. Concepts clés : Order Blocks, FVG, Break of Structure, Change of Character, Liquidity Pools. L'objectif est de trader avec les institutions.",
        "example": "Prix chasse les stops sous un support (manipulation), puis repart à la hausse = signal long SMC.",
        "related": ["Order Block", "FVG", "Break of Structure", "Liquidité"]
    },
    "Fibonacci": {
        "full": "Retracements de Fibonacci",
        "category": "technique",
        "level": "intermédiaire",
        "short": "Niveaux de support/résistance basés sur la suite de Fibonacci (0.382, 0.5, 0.618...).",
        "long": "Les retracements Fibonacci identifient des zones de correction probables. Le niveau 0.618 (Golden Ratio) est le plus surveillé. On trace du bas au haut d'une impulsion haussière. Les niveaux 0.382, 0.5, 0.618 et 0.786 sont les plus utilisés comme zones d'entrée en continuation.",
        "example": "BTC monte de 60k à 100k. Fibonacci 0.618 = 75 200$ → zone de support clé pour un re-test.",
        "related": ["Support", "Résistance", "EMA", "Market Structure"]
    },
    "Break of Structure": {
        "full": "Break of Structure (BOS)",
        "category": "price_action",
        "level": "avancé",
        "short": "Cassure d'un niveau structurel clé confirmant la continuation de tendance.",
        "long": "Un BOS confirme la direction de marché. En tendance haussière, chaque nouveau plus haut rompu = BOS bullish. Un CHOCH (Change of Character) = BOS contre-tendance signalant un retournement potentiel. Ces niveaux servent de zones d'entrée en position dans la direction du BOS.",
        "example": "BTC casse le dernier sommet à 85k → BOS bullish confirmé, continuation probable vers 90k.",
        "related": ["SMC", "Market Structure", "Order Block"]
    },
    "Volume Profile": {
        "full": "Volume Profile",
        "category": "technique",
        "level": "avancé",
        "short": "Distribution du volume par niveaux de prix révélant les zones d'intérêt institutionnel.",
        "long": "Le Volume Profile montre où le volume a été échangé par niveau de prix. Le Point of Control (POC) = niveau le plus traité = aimant à prix. Les Low Volume Nodes = peu de résistance, le prix traverse vite. Les High Volume Nodes = support/résistance forts. Indispensable pour identifier les vraies zones d'intérêt.",
        "example": "POC mensuel à 82k → si BTC revient sur cette zone, rebond probable grâce au fort intérêt institutionnel.",
        "related": ["Support", "Résistance", "Open Interest"]
    },
    "DCA": {
        "full": "Dollar Cost Averaging",
        "category": "stratégie",
        "level": "débutant",
        "short": "Investissement régulier à montant fixe pour lisser le prix d'entrée moyen.",
        "long": "Le DCA consiste à investir un montant fixe à intervalles réguliers (hebdo, mensuel) indépendamment du cours. Cette stratégie réduit l'impact de la volatilité sur le prix moyen d'entrée. Idéale pour l'investisseur long terme qui ne souhaite pas timer le marché.",
        "example": "Acheter 100€ de BTC chaque lundi pendant 52 semaines → prix moyen lissé sur les hauts et les bas.",
        "related": ["Halving", "TVL", "Market Cap"]
    },
    "Halving": {
        "full": "Bitcoin Halving",
        "category": "crypto",
        "level": "débutant",
        "short": "Division par 2 de la récompense des mineurs BTC tous les ~4 ans (~210 000 blocs).",
        "long": "Le halving réduit de moitié les nouveaux BTC créés à chaque bloc miné. Dernier halving : avril 2024 (3.125 BTC/bloc). Historiquement, les halvings précèdent des bull runs majeurs car l'offre diminue. La prochaine réduction en 2028 portera la récompense à 1.5625 BTC.",
        "example": "Après les halvings 2012, 2016, 2020, BTC a atteint de nouveaux ATH dans les 12-18 mois suivants.",
        "related": ["Mining", "Supply", "Bull Market"]
    },
    "TVL": {
        "full": "Total Value Locked",
        "category": "defi",
        "level": "débutant",
        "short": "Valeur totale des actifs déposés dans un protocole DeFi.",
        "long": "Le TVL mesure l'utilisation réelle d'un protocole DeFi. Ratio TVL/MarketCap clé : si MCap < TVL, le token est potentiellement sous-évalué. TVL en hausse + prix stable = accumulation. TVL en baisse = fuite des capitaux = signal baissier.",
        "example": "AAVE TVL = 24B$, MCap = 1.5B$ → ratio 16x = protocole très utilisé par rapport à sa valorisation.",
        "related": ["DeFi", "FDV", "Market Cap"]
    },
    "Liquidité": {
        "full": "Zone de Liquidité",
        "category": "price_action",
        "level": "intermédiaire",
        "short": "Zones où se concentrent les stops loss et ordres des traders retail.",
        "long": "Les institutions cherchent la liquidité pour exécuter leurs gros ordres. Les liquidités se concentrent au-dessus des résistances (stops des vendeurs), sous les supports (stops des acheteurs), et autour des Equal Highs/Lows. Le prix est manipulé pour sweeper ces zones avant de repartir.",
        "example": "Double top à 90k → liquidité buy-side. Le prix monte à 90 500$ pour chasser les stops → puis retournement.",
        "related": ["SMC", "Order Block", "Stop Loss"]
    },

}

def get_all_terms():
    """Retourne tous les termes du glossaire"""
    return [{"id": k, "title": k, **{kk: vv for kk, vv in v.items()}}
            for k, v in GLOSSARY.items()]

def get_term(term_id):
    """Retourne un terme spécifique"""
    term = GLOSSARY.get(term_id)
    if not term: return None
    return {"id": term_id, "title": term_id, **term}

def get_by_category(category):
    """Retourne les termes d'une catégorie"""
    return [{"id": k, "title": k, **v}
            for k, v in GLOSSARY.items() if v.get("category") == category]

def search_terms(query):
    """Recherche dans le glossaire"""
    q = query.lower()
    results = []
    for term_id, term in GLOSSARY.items():
        if (q in term_id.lower() or
            q in term.get("short","").lower() or
            q in term.get("full","").lower()):
            results.append({"id": term_id, "title": term_id, **term})
    return results

def get_categories():
    cats = {}
    for term in GLOSSARY.values():
        cat = term.get("category","autre")
        cats[cat] = cats.get(cat, 0) + 1
    labels = {
        "indicateur": "📊 Indicateurs Techniques",
        "institutionnel": "🏦 Institutionnel & COT",
        "futures": "⚡ Futures & Dérivés",
        "pattern": "🕯️ Patterns de Bougies",
        "gestion_risque": "🛡️ Gestion du Risque",
        "macro": "🌍 Macro-économie",
        "sentiment": "😱 Sentiment de Marché",
        "stratégie": "🎯 Stratégies",
        "risque": "⚠️ Risques à Connaître",
        "exclusif": "🧬 Exclusif CryptoScanner",
    }
    return [{"id": cat, "label": labels.get(cat, cat.capitalize()), "count": count}
            for cat, count in cats.items()]