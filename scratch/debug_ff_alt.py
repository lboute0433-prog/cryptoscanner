import requests
import feedparser

def debug_ff_alternative():
    urls = [
        "https://www.forexfactory.com/ff_calendar_thisweek.xml",
        "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
    ]
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    
    for url in urls:
        print(f"Testing URL: {url}")
        try:
            r = requests.get(url, headers=headers, timeout=10)
            print(f"HTTP Status: {r.status_code}")
            if r.status_code == 200:
                feed = feedparser.parse(r.text)
                print(f"Feed entries count: {len(feed.entries)}")
                break
        except Exception as e:
            print(f"Error for {url}: {e}")

if __name__ == "__main__":
    debug_ff_alternative()
