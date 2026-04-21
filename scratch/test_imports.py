import sys, os
import traceback

# --- Bootstrap Path ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

print(f"ROOT: {BASE_DIR}")
print(f"PATH: {sys.path[:3]}")

try:
    import config
    print("CONFIG OK")
    import db
    print("DB OK")
    import scanner_engine
    print("SCANNER_ENGINE OK")
    import news_macro
    print("NEWS_MACRO OK")
    import app
    print("APP OK")
except Exception:
    traceback.print_exc()
