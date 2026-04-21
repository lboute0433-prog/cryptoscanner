import os, sys
# Add project root to path
sys.path.insert(0, os.getcwd())

from news_macro import fetch_economic_calendar
import json

def test_calendar():
    print("Fetching economic calendar...")
    try:
        data = fetch_economic_calendar(view="week")
        print(f"Status: OK")
        print(f"Event count: {data.get('count', 0)}")
        events = data.get('events', [])
        for i, ev in enumerate(events[:5]):
            print(f"{i+1}. {ev['date']} {ev['time']} | {ev['currency']} | {ev['title']} | Actual: {ev.get('actual', 'N/A')}")
        
        if not events:
            print("WARNING: No events found in calendar.")
            
    except Exception as e:
        print(f"ERROR fetching calendar: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_calendar()
