import sys, re, urllib.request

url = sys.argv[1]
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
html = urllib.request.urlopen(req, timeout=10).read().decode("utf-8", errors="replace")

# Try Next.js __NEXT_DATA__ JSON
m = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html, re.DOTALL)
if m:
    import json
    data = json.loads(m.group(1))
    # Walk the props to find page content
    props = data.get("props", {}).get("pageProps", {})
    content = json.dumps(props, ensure_ascii=False, indent=2)
    print(content[:10000])
else:
    print("No __NEXT_DATA__ found")
    # Fallback: strip tags
    html2 = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL)
    html2 = re.sub(r'<style[^>]*>.*?</style>', '', html2, flags=re.DOTALL)
    html2 = re.sub(r'<[^>]+>', '\n', html2)
    lines = [l.strip() for l in html2.split('\n') if l.strip() and len(l.strip()) > 5]
    for l in lines[:80]:
        print(l)
