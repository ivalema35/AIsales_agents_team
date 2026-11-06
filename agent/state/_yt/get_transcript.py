import json, re, sys, urllib.request, html
vid = sys.argv[1]
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept-Language": "en-US,en;q=0.9", "Cookie": "CONSENT=YES+1"}
def get(u):
    return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30).read().decode("utf-8", "replace")
page = get("https://www.youtube.com/watch?v=%s" % vid)
m = re.search(r"ytInitialPlayerResponse\s*=\s*(\{.+?\});(?:var|</script>)", page, re.S)
if not m:
    print("no player response; page size", len(page)); sys.exit(1)
pr = json.loads(m.group(1))
det = pr.get("videoDetails", {})
print("TITLE:", det.get("title"), "| author:", det.get("author"), "| length s:", det.get("lengthSeconds"), "| views:", det.get("viewCount"))
print("DESC:", (det.get("shortDescription") or "")[:1500].replace("\n", " / "))
tracks = (((pr.get("captions") or {}).get("playerCaptionsTracklistRenderer") or {}).get("captionTracks")) or []
print("caption tracks:", [(t.get("languageCode"), t.get("kind")) for t in tracks])
if not tracks:
    sys.exit(2)
t = next((x for x in tracks if x.get("languageCode", "").startswith("en")), tracks[0])
raw = get(t["baseUrl"] + "&fmt=json3")
data = json.loads(raw)
out = []
for ev in data.get("events", []):
    segs = "".join(s.get("utf8", "") for s in ev.get("segs", []) or [])
    if segs.strip():
        out.append((ev.get("tStartMs", 0) // 1000, segs.replace("\n", " ").strip()))
open("_yt/transcript_%s.txt" % vid, "w", encoding="utf-8").write("\n".join("[%d:%02d] %s" % (s // 60, s % 60, x) for s, x in out))
print("transcript lines:", len(out), "chars:", sum(len(x) for _, x in out))
