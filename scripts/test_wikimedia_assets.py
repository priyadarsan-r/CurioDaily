import json
import re
import requests

headers = {"User-Agent": "CurioDailyBot/1.0 (Educational Social Engine; contact@curiodaily.org)"}

queries = {
    "money_secrets": ["Compound interest", "Stock market", "Gold coins", "Wealth"],
    "human_psychology": ["Human brain", "Cognitive psychology", "Thinking", "Neuron"],
    "future_is_here": ["Lithium-ion battery", "Electric vehicle", "Artificial intelligence", "Clean energy"],
    "daily_mystery": ["Richat Structure", "Eye of the Sahara", "Radio telescope", "Outer space"]
}

print("=== TESTING REAL INTERNET IMAGES (WIKIMEDIA/WIKIPEDIA) ===")
for cat, terms in queries.items():
    print(f"\n--- Pillar: {cat.upper()} ---")
    for term in terms[:2]:
        url = (
            f"https://en.wikipedia.org/w/api.php?action=query&format=json&generator=search"
            f"&gsrsearch={requests.utils.quote(term)}&gsrlimit=2&prop=pageimages&pithumbsize=1080"
        )
        try:
            r = requests.get(url, headers=headers, timeout=5)
            if r.status_code == 200:
                pages = r.json().get("query", {}).get("pages", {})
                for pid, p in pages.items():
                    thumb = p.get("thumbnail", {}).get("source")
                    if thumb:
                        print(f"  [Found Photo] {p.get('title')}: {thumb[:85]}...")
                        break
        except Exception as e:
            print(f"  Error for {term}: {e}")

print("\n=== TESTING MIXKIT REAL STOCK VIDEO CLIPS ===")
mixkit_cats = ["money", "technology", "nature", "space"]
for mc in mixkit_cats:
    url = f"https://mixkit.co/free-stock-video/{mc}/"
    try:
        r = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}, timeout=6)
        if r.status_code == 200:
            vids = list(set(re.findall(r'https://assets\.mixkit\.co/videos/\d+/\d+-720\.mp4', r.text)))
            if not vids:
                vids = list(set(re.findall(r'https://assets\.mixkit\.co/videos/[^\s"\'<>]+\.mp4', r.text)))
            print(f"  Mixkit [{mc}]: Found {len(vids)} clips! Example: {vids[0] if vids else 'none'}")
    except Exception as e:
        print(f"  Mixkit error for {mc}: {e}")
