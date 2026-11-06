import json, re, sys, urllib.request
vid = "k6KvIidRsFY"
H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124 Safari/537.36", "Accept-Language": "en-US,en;q=0.9", "Cookie": "CONSENT=YES+1"}
def get(u):
    r = urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30)
    return r.status, r.read().decode("utf-8", "replace")
st, page = get("https://www.youtube.com/watch?v=%s" % vid)
pr = json.loads(re.search(r"ytInitialPlayerResponse\s*=\s*(\{.+?\});(?:var|</script>)", page, re.S).group(1))
tracks = pr["captions"]["playerCaptionsTracklistRenderer"]["captionTracks"]
for t in tracks[:3]:
    for suffix in ("", "&fmt=json3", "&fmt=srv3"):
        try:
            st, body = get(t["baseUrl"] + suffix)
            print(t["languageCode"], repr(suffix), st, len(body), body[:80].replace("\n", " "))
        except Exception as e:
            print(t["languageCode"], suffix, "ERR", e)
print("translation languages:", [x.get("languageCode") for x in pr["captions"]["playerCaptionsTracklistRenderer"].get("translationLanguages", [])][:8])
print("default audio track:", pr["captions"]["playerCaptionsTracklistRenderer"].get("audioTracks"))
