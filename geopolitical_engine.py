"""
Geopolitical Engine — Macro/policy analysis for crypto markets.
Integrates economic calendar, regulatory news, and geopolitical sentiment.
"""
import os
import requests
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

GEOPOL_TZ = ZoneInfo(os.environ.get("REPORT_TIMEZONE", "Europe/Paris"))

def fetch_geopolitical_events():
    """Fetch high-impact geopolitical and policy events affecting crypto markets."""
    try:
        from news_macro import fetch_economic_calendar
        cal = fetch_economic_calendar(view="day")

        # Filter for high-impact events
        high_impact = []
        for event in (cal.get("events") or []):
            importance = event.get("importance", "").lower()
            if importance in ["high", "critical", "major"]:
                high_impact.append({
                    "title": event.get("title", ""),
                    "currency": event.get("currency", ""),
                    "importance": importance,
                    "time": event.get("time", ""),
                    "forecast": event.get("forecast", ""),
                    "previous": event.get("previous", ""),
                    "category": event.get("category", "Economic"),
                    "impact_crypto": assess_crypto_impact(event)
                })

        # Include recent economic releases
        recent = []
        for event in (cal.get("recent_releases") or []):
            recent.append({
                "title": event.get("title", ""),
                "currency": event.get("currency", ""),
                "actual": event.get("actual", ""),
                "forecast": event.get("forecast", ""),
                "assessment": event.get("assessment_label", "In Line"),
                "time": event.get("time", ""),
                "impact_crypto": assess_crypto_impact(event)
            })

        return {
            "upcoming_events": high_impact[:5],
            "recent_releases": recent[:3],
            "timestamp": datetime.now(GEOPOL_TZ).isoformat()
        }
    except Exception as e:
        print(f"[GeoMacro] Economic calendar: {e}")
        return {"upcoming_events": [], "recent_releases": [], "timestamp": datetime.now(GEOPOL_TZ).isoformat()}

def fetch_regulatory_news():
    """Fetch regulatory and policy news related to crypto."""
    try:
        from news_macro import get_news_from_db

        # Keywords for regulatory/policy events (FR + EN)
        keywords = ["regulation", "sec", "cftc", "central bank", "policy", "ban", "approve", "etf", "cbdc", "license",
                   "réglementation", "autorité", "banque centrale", "politique", "interdire", "approbation", "licence"]

        regulatory_news = []
        all_news = get_news_from_db(limit=20, critical_only=False, lang=None, prefer_lang="fr")

        for news in all_news:
            title_lower = (news.get("title", "") or "").lower()
            category = news.get("category", "").lower()

            if any(kw in title_lower or kw in category for kw in keywords):
                regulatory_news.append({
                    "title": news.get("title", ""),
                    "summary": news.get("summary", ""),
                    "source": news.get("source", ""),
                    "url": news.get("url", ""),
                    "published": news.get("published", ""),
                    "category": news.get("category", "Regulation"),
                    "crypto_relevance": assess_regulation_impact(news)
                })

        return regulatory_news[:5]
    except Exception as e:
        print(f"[GeoMacro] Regulatory news: {e}")
        return []

def assess_crypto_impact(event):
    """Determine potential crypto market impact of an economic event."""
    title = (event.get("title", "") or "").lower()
    importance = (event.get("importance", "") or "").lower()
    currency = (event.get("currency", "") or "").upper()

    # USD/EUR events have higher crypto correlation
    is_major_currency = currency in ["USD", "EUR", "GBP", "JPY", "CHF"]

    impact_score = 0
    if "interest rate" in title or "fed" in title or "ecb" in title:
        impact_score = 9 if is_major_currency else 6
    elif "inflation" in title or "cpi" in title or "pce" in title:
        impact_score = 8 if is_major_currency else 5
    elif "employment" in title or "nonfarm" in title:
        impact_score = 7 if is_major_currency else 4
    elif "gdp" in title or "growth" in title:
        impact_score = 6 if is_major_currency else 3
    elif "central bank" in title or "policy" in title:
        impact_score = 8 if is_major_currency else 5
    else:
        impact_score = int(importance == "high") * 3 + int(importance == "critical") * 5 + 1

    return {
        "score": min(10, impact_score),
        "direction": assess_event_direction(event),
        "reasoning": f"{'USD/EUR impact (high correlation with crypto)' if is_major_currency else 'Secondary market event'}"
    }

def assess_regulation_impact(news):
    """Score regulatory/policy news impact on crypto."""
    title = (news.get("title", "") or "").lower()
    summary = (news.get("summary", "") or "").lower()

    impact = 0

    # Positive impacts
    if any(w in title for w in ["approve", "etf", "license", "framework", "open", "embrace"]):
        impact += 5
    if "spot bitcoin" in title or "spot eth" in title:
        impact += 3
    if "framework" in title or "regulation" in title:
        impact += 2

    # Negative impacts
    if any(w in title for w in ["ban", "restrict", "crackdown", "investigation", "penalty"]):
        impact -= 5
    if "sec" in title or "cftc" in title:
        impact -= 2
    if "risk" in title or "fraud" in title or "scam" in title:
        impact -= 3

    return {
        "score": max(-10, min(10, impact)),
        "sentiment": "positive" if impact > 0 else "negative" if impact < 0 else "neutral",
        "sectors_affected": identify_affected_sectors(title)
    }

def assess_event_direction(event):
    """Assess whether event is hawkish (bearish) or dovish (bullish) for risk assets."""
    title = (event.get("title", "") or "").lower()
    assessment = (event.get("assessment_label", "") or "").lower()

    if any(w in assessment for w in ["worse", "beat negative", "miss expected"]):
        return "dovish"
    elif any(w in assessment for w in ["better", "beat", "exceed"]):
        return "hawkish"
    else:
        return "neutral"

def identify_affected_sectors(news_title):
    """Identify which crypto sectors are affected by regulation/policy."""
    title_lower = news_title.lower()
    sectors = []

    if any(w in title_lower for w in ["defi", "decentralized", "uniswap", "aave"]):
        sectors.append("DeFi")
    if any(w in title_lower for w in ["stablecoin", "usdc", "usdt", "dai"]):
        sectors.append("Stablecoins")
    if any(w in title_lower for w in ["bitcoin", "ethereum", "btc", "eth"]):
        sectors.append("Major Assets")
    if any(w in title_lower for w in ["exchange", "cex", "binance", "kraken", "coinbase"]):
        sectors.append("Exchanges")
    if any(w in title_lower for w in ["nft", "token", "altcoin"]):
        sectors.append("Altcoins")
    if any(w in title_lower for w in ["cbdc", "digital currency"]):
        sectors.append("CBDC")

    return sectors[:3] if sectors else ["General"]

def get_geopolitical_summary(market_data=None):
    """
    Comprehensive geopolitical analysis for VIP brief.

    Returns:
        {
            "events": [...],
            "regulations": [...],
            "risk_score": 0-10,
            "sentiment": "risk-on|neutral|risk-off",
            "top_risks": [...],
            "catalysts": [...],
            "vip_insights": "..."
        }
    """
    events = fetch_geopolitical_events()
    regulations = fetch_regulatory_news()

    # Calculate risk score
    risk_score = 5  # neutral baseline

    # Adjust based on events
    for event in events.get("upcoming_events", []):
        impact = event.get("impact_crypto", {}).get("score", 0)
        direction = event.get("impact_crypto", {}).get("direction", "neutral")
        if direction == "hawkish" and impact > 5:
            risk_score += 1
        elif direction == "dovish" and impact > 5:
            risk_score -= 1

    # Adjust based on regulations
    for reg in regulations:
        score = reg.get("crypto_relevance", {}).get("score", 0)
        sentiment = reg.get("crypto_relevance", {}).get("sentiment", "neutral")
        if sentiment == "negative" and abs(score) > 3:
            risk_score += 1.5
        elif sentiment == "positive" and score > 3:
            risk_score -= 1

    risk_score = max(1, min(10, risk_score))

    # Determine overall sentiment
    if risk_score >= 7:
        sentiment = "risk-off"
    elif risk_score <= 3:
        sentiment = "risk-on"
    else:
        sentiment = "neutral"

    # Extract top risks and catalysts
    top_risks = []
    catalysts = []

    for event in events.get("upcoming_events", []):
        impact = event.get("impact_crypto", {}).get("score", 0)
        if impact >= 7:
            catalysts.append({
                "title": event.get("title", ""),
                "time": event.get("time", ""),
                "impact": "High",
                "direction": event.get("impact_crypto", {}).get("direction", "neutral")
            })

    for reg in regulations:
        score = reg.get("crypto_relevance", {}).get("score", 0)
        if score < -5:
            top_risks.append({
                "title": reg.get("title", ""),
                "source": reg.get("source", ""),
                "impact": "High",
                "sectors": reg.get("crypto_relevance", {}).get("sectors_affected", [])
            })
        elif score > 5:
            catalysts.append({
                "title": reg.get("title", ""),
                "source": reg.get("source", ""),
                "impact": "High",
                "direction": "positive"
            })

    # Generate VIP insights
    vip_insights = _generate_vip_insights(risk_score, sentiment, catalysts, regulations)

    return {
        "economic_calendar": events,
        "regulatory_news": regulations,
        "risk_score": round(risk_score, 1),
        "sentiment": sentiment,
        "top_risks": top_risks[:3],
        "catalysts": catalysts[:3],
        "vip_insights": vip_insights,
        "timestamp": datetime.now(GEOPOL_TZ).isoformat()
    }

def _generate_vip_insights(risk_score, sentiment, catalysts, regulations):
    """Generate strategic insights for VIP members."""
    insights = []

    if risk_score >= 8:
        insights.append("🔴 Elevated geopolitical risk — tighten stops, consider de-risking non-core positions")
    elif risk_score >= 6:
        insights.append("🟠 Moderate geopolitical concerns — maintain hedges, watch central bank actions")
    else:
        insights.append("🟢 Favorable geopolitical backdrop — risk-on conditions support alt season potential")

    if catalysts:
        upcoming = catalysts[0]
        if upcoming.get("direction") == "dovish":
            insights.append(f"📉 Dovish catalyst incoming: {upcoming.get('title', '')} — potential support for risk assets")
        elif upcoming.get("direction") == "hawkish":
            insights.append(f"📈 Hawkish catalyst incoming: {upcoming.get('title', '')} — watch for margin calls")

    # Regulatory sentiment
    positive_regs = sum(1 for r in regulations if r.get("crypto_relevance", {}).get("sentiment") == "positive")
    negative_regs = sum(1 for r in regulations if r.get("crypto_relevance", {}).get("sentiment") == "negative")

    if negative_regs > positive_regs:
        insights.append(f"⚠️ Negative regulatory tone ({negative_regs} items) — monitor compliance-sensitive sectors (DeFi, exchanges)")
    elif positive_regs > negative_regs:
        insights.append(f"✅ Positive regulatory momentum ({positive_regs} items) — institutional adoption likely to accelerate")

    return insights[:3]  # Return top 3 insights
