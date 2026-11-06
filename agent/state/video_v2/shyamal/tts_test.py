import sys, json
sys.path.insert(0, "C:/Users/Administrator/Desktop/AISales_agent_team/agent/pilot/video")
import kie_lib as K
b0 = K.credits()
for model, inp in [
    ("elevenlabs/text-to-speech-multilingual-v2", {"text": "Shyamal Park Lane. A Diwali offer for the first five bookings.", "voice": "Aria", "stability": 0.5, "similarity_boost": 0.75, "style": 0, "speed": 1.0}),
]:
    tid = K.create(model, inp)
    print(model, "task", tid)
    if tid:
        d = K.wait(tid, every=4, max_s=120)
        print(d.get("state"), d.get("creditsConsumed"), d.get("failMsg"), K.urls(d)[:1])
        us = K.urls(d)
        if us:
            K.download(us[0], "tts_test.mp3"); print("saved tts_test.mp3")
print("spent:", b0 - K.credits())
