import requests
import feedparser

def test_trading_economics():
    url = "https://tradingeconomics.com/rss/calendar.xml"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    print(f"Testing URL: {url}")
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"HTTP Status: {r.status_code}")
        if r.status_code == 200:
            feed = feedparser.parse(r.text)
            print(f"Feed entries count: {len(feed.entries)}")
            for i, entry in enumerate(feed.entries[:3]):
                print(f"Entry {i+1}: {entry.get('title')} | {entry.get('description')}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_trading_economics()
