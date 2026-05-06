Voici une **liste structurée des API gratuites (ou avec plan gratuit)** pour récupérer des données **crypto, forex, actions, on-chain, analytics**. Je les ai classées par type de données pour que tu puisses les intégrer facilement dans un bot ou un dashboard trading.

---

# 1. API crypto (prix, market cap, historiques)

### 1. CoinGecko API

- Site : [https://www.coingecko.com/en/api](https://www.coingecko.com/en/api?utm_source=chatgpt.com)
    
- Gratuit : oui (plan demo)
    
- Limite : ~30 requêtes/min, 10 000/mois
    
- Données :
    
    - prix temps réel
        
    - market cap
        
    - volume
        
    - historique
        
    - exchanges
        
    - NFT
        
    - données on-chain
        
- Endpoint exemple :
    

https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=usd

CoinGecko agrège les données de **1000+ exchanges et des milliers de cryptos**.

---

### 2. CoinMarketCap API

- Site : [https://coinmarketcap.com/api/](https://coinmarketcap.com/api/)
    
- Gratuit : oui
    
- Limite : ~10 000 requêtes/mois
    
- Données :
    
    - prix
        
    - ranking
        
    - market cap
        
    - historique
        
    - dominance BTC
        
    - reserves exchange
        

Endpoint exemple :

https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest

---

### 3. CoinPaprika API

- Site : [https://api.coinpaprika.com](https://api.coinpaprika.com)
    
- Gratuit : oui
    
- Limite : ~20 000 appels/mois
    
- Données :
    
    - prix
        
    - historique
        
    - tickers
        
    - exchanges
        

Exemple :

https://api.coinpaprika.com/v1/tickers/btc-bitcoin

---

### 4. CryptoCompare API

- Site : [https://min-api.cryptocompare.com](https://min-api.cryptocompare.com)
    
- Gratuit : oui
    
- Données :
    
    - prix
        
    - historique
        
    - news crypto
        
    - mining
        
    - social stats
        

Exemple :

https://min-api.cryptocompare.com/data/price?fsym=BTC&tsyms=USD

---

---### 5. FreeCryptoAPI

- Site : [https://freecryptoapi.com](https://freecryptoapi.com)
    
- Gratuit : oui
    
- Limite : ~100k requêtes/mois
    
- Données :
    
    - prix
        
    - conversions
        
    - market data
        

---

# 2. API on-chain / wallets / smart money

### 6. Arkham Intelligence API

- Site : https://arkhamintelligence.com
    
- Données :
    
    - wallets
        
    - smart money
        
    - transactions
        
    - mouvements des whales
        

---

### 7. Glassnode API

- Site : [https://glassnode.com](https://glassnode.com)
    
- Gratuit : limité
    
- Données :
    
    - on-chain metrics
        
    - exchange inflow
        
    - supply metrics
        
    - whales
        

Exemple :

https://api.glassnode.com/v1/metrics/market/price_usd

---

### 8. DEX Screener API

- Site : [https://docs.dexscreener.com](https://docs.dexscreener.com)
    
- Gratuit : oui
    
- Données :
    
    - prix DEX
        
    - liquidity
        
    - token pairs
        
    - volume
        

Exemple :

https://api.dexscreener.com/latest/dex/pairs/ethereum/0x...

---

### 9. Moralis API

- Site : [https://moralis.io](https://moralis.io)
    
- Gratuit : oui
    
- Données :
    
    - transactions
        
    - NFT
        
    - balances
        
    - token transfers
        

---

### 10. Alchemy API

- Site : [https://alchemy.com](https://alchemy.com)
    
- Gratuit : oui
    
- Données :
    
    - blockchain
        
    - smart contracts
        
    - tokens
        
    - NFT
        

---

# 3. API exchange (crypto trading direct)

### 11. Binance API

- Site : https://binance-docs.github.io
    
- Gratuit : oui
    
- Données :
    
    - prix
        
    - orderbook
        
    - trades
        
    - futures
        

Exemple :

https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT

---

### 12. Kraken API

- Site : [https://docs.kraken.com](https://docs.kraken.com)
    
- Gratuit : oui
    
- Données :
    
    - prix
        
    - OHLC
        
    - trades
        

---

### 13. Coinbase API

- Site : [https://developers.coinbase.com](https://developers.coinbase.com)
    
- Gratuit : oui
    
- Données :
    
    - prix
        
    - order book
        
    - historique
        

---

# 4. API actions / forex

### 14. Finnhub

- Site : [https://finnhub.io](https://finnhub.io)
    
- Gratuit : oui
    
- Données :
    
    - actions
        
    - forex
        
    - crypto
        
    - news
        
    - fundamentals
        

---

### 15. Alpha Vantage

- Site : [https://www.alphavantage.co](https://www.alphavantage.co)
    
- Gratuit : oui
    
- Données :
    
    - actions
        
    - forex
        
    - crypto
        
    - indicateurs techniques
        

Exemple :

https://www.alphavantage.co/query?function=FX_INTRADAY

---

### 16. TwelveData

- Site : [https://twelvedata.com](https://twelvedata.com)
    
- Gratuit : oui
    
- Données :
    
    - actions
        
    - forex
        
    - crypto
        
    - indicateurs
        

---

# 5. API analytics crypto

### 17. Santiment API

- Données :
    
    - sentiment social
        
    - données on-chain
        
    - développement github
        

---

### 18. LunarCrush API

- Données :
    
    - sentiment crypto
        
    - social metrics
        
    - trending coins
        

---

### 19. Mobula API

- Données :
    
    - token analytics
        
    - portfolio
        
    - market data
        

---

# 6. APIs utiles pour un bot trading / dashboard

Très utilisées ensemble :

- CoinGecko → prix
    
- Binance → orderbook
    
- Glassnode → on-chain
    
- Arkham → whales
    
- Finnhub → actions
    
- Alpha Vantage → forex
    
- DexScreener → DEX
    

---

