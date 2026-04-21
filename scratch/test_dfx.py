import requests

def test_dailyfx():
    url = "https://www.dailyfx.com/calendar/calendar.json"
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    print(f"Testing URL: {url}")
    try:
        r = requests.get(url, headers=headers, timeout=10)
        print(f"HTTP Status: {r.status_code}")
        if r.status_code == 200:
            print(f"Success! Snippet: {r.text[:200]}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_dailyfx()
