import re
import requests

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

# 1. Mixkit test
print("--- MIXKIT ---")
try:
    r = requests.get('https://mixkit.co/free-stock-video/money/', headers=headers, timeout=6)
    mp4s = list(set(re.findall(r'https://assets\.mixkit\.co/videos/[^\s"\'<>]+\.mp4', r.text)))
    print(f"Mixkit found {len(mp4s)} videos:")
    for v in mp4s[:3]:
        print(" ", v)
except Exception as e:
    print("Mixkit error:", e)

# 2. Wikimedia Commons Video URL resolver
print("\n--- WIKIMEDIA COMMONS ---")
try:
    r = requests.get(
        'https://commons.wikimedia.org/w/api.php?action=query&format=json&list=search&srsearch=space+filetype:video&srnamespace=6&srlimit=3',
        headers=headers,
        timeout=6
    )
    search_data = r.json().get('query', {}).get('search', [])
    for s in search_data:
        title = s['title']
        info_url = f"https://commons.wikimedia.org/w/api.php?action=query&format=json&titles={title}&prop=imageinfo&iiprop=url|mime"
        r_info = requests.get(info_url, headers=headers, timeout=6)
        pages = r_info.json().get('query', {}).get('pages', {})
        for _, p in pages.items():
            ii = p.get('imageinfo', [{}])[0]
            print(f"  {title}: {ii.get('url')}")
except Exception as e:
    print("Wikimedia error:", e)

# 3. Unsplash / Wikimedia Images
print("\n--- REAL IMAGES SEARCH ---")
try:
    # Wikimedia images
    wiki_img = 'https://en.wikipedia.org/w/api.php?action=query&format=json&generator=search&gsrsearch=stock+market+investment&gsrlimit=3&prop=pageimages&pithumbsize=1080'
    r2 = requests.get(wiki_img, headers=headers, timeout=6)
    pages = r2.json().get('query', {}).get('pages', {})
    for _, v in pages.items():
        thumb = v.get('thumbnail', {}).get('source')
        if thumb:
            print(f"  Wiki photo: {v.get('title')} -> {thumb}")
except Exception as e:
    print("Image search error:", e)
