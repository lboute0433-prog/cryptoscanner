import feedparser
import requests

def debug_ff():
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
    print(f"Testing URL: {url}")
    try:
        r = requests.get(url, timeout=10)
        print(f"HTTP Status: {r.status_code}")
        print(f"Response snippet: {r.text[:500]}")
        
        feed = feedparser.parse(r.text)
        print(f"Feed entries count: {len(feed.entries)}")
        for i, entry in enumerate(feed.entries[:5]):
            print(f"Entry {i+1}: {entry.get('title')} | {entry.get('ff_country')} | {entry.get('ff_actual')}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_ff()
