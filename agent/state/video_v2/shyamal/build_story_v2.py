# -*- coding: utf-8 -*-
"""Lead video v2, round 2 (after QA): lead.json + timeline -> story_v2.html (deterministic window.setT(t)).
Rules baked in from the QA: essential content in y 140..1080, cards in y 560..920, caption pill y 950..1050 (36px, navy + gold line, <= 8 words),
EXAMPLE labels on every mock, no lead-logo bug on the illustrated scenes (a small 'Concept by IV Infotech' mark instead), sender + independence line in scene 1 and scene 6,
no 'Hot'/'booked'/'From Diwali ad', staged beats in scene 4, plain-text CTA in scene 6. Sirf local file banata hai."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, "C:/Users/Administrator/Desktop/AISales_agent_team/agent/pilot/video")
import story_build as sb  # noqa: E402

lead = json.loads((HERE / "lead.json").read_text(encoding="utf-8"))
tl = json.loads((HERE / (sys.argv[1] if len(sys.argv) > 1 else "timeline.json")).read_text(encoding="utf-8"))
out_name = sys.argv[2] if len(sys.argv) > 2 else "story_v2.html"

IV_WAVE = sb.iv("happy", True, 230)
IV_STILL = sb.iv("happy", False, 215)
CHAT = '<svg viewBox="0 0 24 24" width="34" height="34"><path fill="#fff" d="M4 4h16a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H9l-5 4V6a2 2 0 0 1 2-2z"/></svg>'
TOUCH = ('<svg viewBox="0 0 24 24" width="62" height="62"><path fill="#fff" stroke="#10222f" stroke-width="1" d="M9 11.24V7.5C9 6.12 10.12 5 11.5 5S14 6.12 14 7.5v3.74c1.21-.81 2-2.18 2-3.74C16 5.01 13.99 3 11.5 3S7 5.01 7 7.5c0 1.56.79 2.93 2 3.74zm9.84 4.63l-4.54-2.26c-.17-.07-.35-.11-.54-.11H13v-6c0-.83-.67-1.5-1.5-1.5S10 6.67 10 7.5v10.74l-3.43-.72c-.08-.01-.15-.03-.24-.03-.31 0-.59.13-.79.33l-.79.8 4.94 4.94c.27.27.65.44 1.06.44h6.79c.75 0 1.33-.55 1.44-1.28l.69-5.1c.01-.07.02-.13.02-.2 0-.62-.38-1.16-.91-1.38z"/></svg>')
ARROW = '<svg viewBox="0 0 24 24" width="74" height="74"><path fill="none" stroke="#bda588" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round" d="M12 3v16M5 12l7 7 7-7"/></svg>'
ICON = '<div class="lg-ic"><img src="%s" alt=""></div>' % lead["logo"]
CONCEPT = '<div class="concept"><span>Concept by</span><img src="assets/iv-infotech-logo.png" alt="IV Infotech"></div>'

T = """<!doctype html><html><head><meta charset="utf-8"><title>story v2</title>
<style>
@font-face{font-family:"Inter";src:url("assets/fonts/inter.woff2") format("woff2");font-weight:100 900}
@font-face{font-family:"SG";src:url("assets/fonts/space-grotesk.woff2") format("woff2");font-weight:300 700}
:root{--navy:__NAVY__;--navy2:__NAVY2__;--gold:__GOLD__;--gold2:__GOLD2__;--wa:#25D366;--wag:#075E54}
*{box-sizing:border-box}
html,body{margin:0;background:#06121e;width:720px;height:1280px;overflow:hidden;font-family:"Inter","Segoe UI",Arial,sans-serif;color:#10222f}
#stage{position:relative;width:720px;height:1280px;overflow:hidden;background:var(--navy)}
.scene{position:absolute;inset:0;overflow:hidden;display:none}
.bg{position:absolute;inset:-30px;background-size:cover;background-position:center top;will-change:transform}
.lg-ic{width:54px;height:54px;overflow:hidden;border-radius:12px;position:relative;flex:none;background:var(--navy)}
.lg-ic img{position:absolute;width:75px;height:auto;left:-10px;top:-4.2px}
/* caption pill: one per scene, 36px */
.cap{position:absolute;left:34px;right:34px;top:950px;display:flex;justify-content:center}
.cap div{background:rgba(14,36,58,.95);border:3px solid var(--gold);border-radius:44px;padding:18px 34px;font:600 36px/1.18 "SG","Inter",sans-serif;color:#fff;text-align:center;box-shadow:0 12px 34px rgba(0,0,0,.35)}
/* concept mark */
.concept{position:absolute;left:34px;top:150px;display:flex;align-items:center;gap:12px;background:rgba(255,255,255,.95);border-radius:30px;padding:8px 18px;box-shadow:0 8px 22px rgba(0,0,0,.22)}
.concept span{font:600 24px "Inter",sans-serif;color:#47596a}.concept img{height:34px;display:block}
.tag{position:absolute;top:14px;right:16px;background:var(--gold);color:var(--navy);font:800 22px "Inter",sans-serif;letter-spacing:.07em;padding:6px 14px;border-radius:20px;z-index:5}
.card{position:absolute;background:#fff;border-radius:34px;box-shadow:0 22px 60px rgba(8,20,32,.4);overflow:hidden}
/* scene 1 */
#s1 .dim{position:absolute;inset:0;background:radial-gradient(circle at 50% 38%,rgba(14,36,58,.55) 0%,rgba(14,36,58,.2) 60%,rgba(14,36,58,0) 100%)}
#s1 .logo{position:absolute;left:0;right:0;top:170px;display:flex;justify-content:center}
#s1 .logo img{width:400px;height:auto;filter:drop-shadow(0 18px 40px rgba(0,0,0,.5))}
#s1 .t1{position:absolute;left:0;right:0;top:622px;text-align:center;font:600 62px "SG",sans-serif;color:#e7d3b4;text-shadow:0 4px 18px rgba(0,0,0,.45)}
#s1 .t2{position:absolute;left:0;right:0;top:706px;text-align:center;font:500 32px "Inter",sans-serif;color:#e9eff5;text-shadow:0 3px 12px rgba(0,0,0,.5)}
#s1 .rib{position:absolute;left:0;right:0;top:782px;display:flex;justify-content:center}
#s1 .rib div{background:linear-gradient(90deg,var(--gold2),var(--gold));color:var(--navy);font:700 31px "SG",sans-serif;padding:14px 56px;clip-path:polygon(0 0,100% 0,calc(100% - 22px) 50%,100% 100%,0 100%,22px 50%);box-shadow:0 10px 28px rgba(0,0,0,.35)}
#s1 .sender{position:absolute;left:40px;right:40px;top:985px;text-align:center;font:500 24px/1.3 "Inter",sans-serif;color:#e6edf3;text-shadow:0 2px 10px rgba(0,0,0,.6)}
.sp{position:absolute;width:10px;height:10px;border-radius:50%;background:radial-gradient(circle,#ffe9b8 0%,var(--gold) 55%,rgba(189,165,136,0) 100%)}
/* scene 2 ad card */
#s2 .ad{left:56px;top:556px;width:608px;height:368px}
.ad .hd{display:flex;align-items:center;gap:14px;padding:12px 20px;height:70px}
.ad .hd b{font:700 25px "Inter",sans-serif;display:block;line-height:1.1}.ad .hd small{font:500 19px "Inter",sans-serif;color:#5b6b78}
.ad .cr{height:158px;background:linear-gradient(135deg,var(--navy2),var(--navy));position:relative;display:flex;align-items:center;gap:22px;padding:0 26px}
.ad .cr img{height:132px;width:auto}
.ad .cr .tx b{display:block;font:700 37px/1.05 "SG",sans-serif;color:#e7d3b4}
.ad .cr .tx span{display:inline-block;margin-top:10px;background:var(--gold);color:var(--navy);font:700 20px "Inter",sans-serif;padding:6px 14px;border-radius:30px}
.ad .ln{padding:10px 24px 0;font:600 25px "Inter",sans-serif;height:46px}
.ad .cta{margin:8px 24px 0;height:68px;border-radius:18px;background:var(--wa);display:flex;align-items:center;justify-content:center;gap:14px;color:#fff;font:700 28px "Inter",sans-serif;position:relative}
.ripple{position:absolute;border-radius:50%;border:5px solid rgba(255,255,255,.95);opacity:0;pointer-events:none}
.finger{position:absolute;opacity:0;pointer-events:none;filter:drop-shadow(0 4px 6px rgba(0,0,0,.4))}
/* chat card (scenes 3, 4) */
.chatcard{left:70px;top:590px;width:580px;height:330px;border-radius:36px}
.wh{height:84px;background:var(--wag);display:flex;align-items:center;gap:14px;padding:0 20px;color:#fff;position:relative;z-index:3}
.wh b{font:700 26px "Inter",sans-serif;display:block;line-height:1.1}.wh small{font:600 20px "Inter",sans-serif;opacity:.92}
.cbody{position:absolute;left:0;right:0;top:84px;bottom:0;background:#ECE5DD}
.bub{border-radius:18px;padding:12px 18px;font:500 26px/1.25 "Inter",sans-serif;box-shadow:0 1px 1px rgba(0,0,0,.12);position:absolute}
.bub.out{right:20px;top:34px;background:#DCF8C6;border-top-right-radius:4px;max-width:420px}
.bub small{display:block;text-align:right;font:500 20px "Inter",sans-serif;color:#5b6b78;margin-top:4px}
.beat{position:absolute;left:22px;right:22px;top:20px;bottom:14px;display:flex;flex-direction:column;justify-content:center;align-items:flex-start;gap:14px;opacity:0}
.beat .hdg{font:700 26px "Inter",sans-serif;color:#10222f}
.beat .atag{font:700 22px "Inter",sans-serif;color:#0d6b3a;background:#d9f3e4;border-radius:20px;padding:5px 14px}
.pdf{display:flex;align-items:center;gap:16px;background:#fff;border-radius:16px;padding:14px 18px;width:100%;box-shadow:0 1px 2px rgba(0,0,0,.12)}
.pdf i{display:block;width:50px;height:60px;border-radius:9px;background:#E5484D;color:#fff;font:800 17px/60px "Inter",sans-serif;text-align:center;font-style:normal}
.pdf b{font:700 26px "Inter",sans-serif;display:block}.pdf span{font:500 22px "Inter",sans-serif;color:#4a5a67}
.qs{display:flex;flex-wrap:wrap;gap:12px}
.qs span{border:3px solid #18a05a;color:#0f6a3c;background:#fff;border-radius:34px;padding:10px 20px;font:700 25px "Inter",sans-serif}
.stamp{font:600 22px "Inter",sans-serif;color:#4a5a67}
#s4 .iv{position:absolute;left:470px;top:330px;width:215px}
/* scene 5 */
#s5 .iv{position:absolute;left:480px;top:210px;width:230px}
#s5 .lst{left:56px;top:560px;width:608px;height:364px}
.lst .hd{display:flex;align-items:center;gap:14px;padding:12px 22px;height:66px;border-bottom:2px solid #eef2f5}
.lst .hd b{font:700 26px "Inter",sans-serif;display:block;line-height:1.1}.lst .hd small{font:500 20px "Inter",sans-serif;color:#4a5a67}
.row{display:flex;align-items:center;gap:16px;padding:0 22px;height:92px;border-bottom:2px solid #f1f4f6}
.row .av{width:54px;height:54px;border-radius:50%;background:var(--navy2);color:#fff;font:700 25px/54px "Inter",sans-serif;text-align:center;flex:none}
.row .mid{flex:1}.row .mid b{font:700 24px "Inter",sans-serif;display:block}.row .mid span{font:500 21px "Inter",sans-serif;color:#4a5a67}
.row .st{font:700 21px "Inter",sans-serif;padding:6px 14px;border-radius:30px;text-align:center;line-height:1.2;display:inline-block}
.st.ok{background:#DDF3E5;color:#0d6b3a}.st.ask{background:#E4EEFF;color:#1D4ED8}
.row .vs{display:block;font:500 20px "Inter",sans-serif;color:#4a5a67;margin-top:4px;text-align:right}
/* scene 6 */
#s6 .dim{position:absolute;inset:0;background:linear-gradient(180deg,rgba(10,28,46,.72) 0%,rgba(10,28,46,.82) 100%)}
#s6 .ivlogo{position:absolute;left:0;right:0;top:150px;display:flex;justify-content:center}
#s6 .ivlogo div{background:#fff;border-radius:26px;padding:16px 38px;box-shadow:0 18px 50px rgba(0,0,0,.4)}
#s6 .ivlogo img{height:78px;display:block}
#s6 .robot{position:absolute;left:0;right:0;top:290px;display:flex;justify-content:center}
#s6 h1{position:absolute;left:50px;right:50px;top:545px;margin:0;text-align:center;font:600 54px/1.12 "SG",sans-serif;color:#fff}
#s6 h1 em{font-style:normal;color:#e7d3b4}
#s6 .cta1{position:absolute;left:0;right:0;top:700px;text-align:center;font:600 32px "Inter",sans-serif;color:#e7d3b4}
#s6 .cta2{position:absolute;left:0;right:0;top:748px;text-align:center;font:700 44px "SG",sans-serif;color:#fff}
#s6 .arrow{position:absolute;left:0;right:0;top:830px;display:flex;justify-content:center}
#s6 .foot{position:absolute;left:46px;right:46px;top:940px;text-align:center;font:500 28px/1.32 "Inter",sans-serif;color:rgba(255,255,255,.92)}
</style></head><body><div id="stage">

<div class="scene" id="s1" data-start="__S1A__" data-end="__S1B__" data-kb0="1.0" data-kb1="1.05">
  <div class="bg" style="background-image:url('__STILL1__')"></div><div class="dim"></div>
  <div class="sparks"></div>
  <div class="logo" data-in="0.1" data-dur="0.9" data-fx="pop"><img src="__LOGO__" alt=""></div>
  <div class="t1" data-in="0.7" data-dur="0.6">__PROJECT__</div>
  <div class="t2" data-in="0.95" data-dur="0.6">__AREA__</div>
  <div class="rib" data-in="1.3" data-dur="0.6" data-fx="pop"><div>Your Diwali offer \u00b7 first 5 bookings only</div></div>
  <div class="cap" style="top:872px" data-in="1.6" data-dur="0.5"><div>An IV Infotech idea</div></div>
  <div class="sender" data-in="2.0" data-dur="0.5">A concept by IV Infotech \u00b7 not affiliated with __NAME__</div>
</div>

<div class="scene" id="s2" data-start="__S2A__" data-end="__S2B__" data-kb0="1.0" data-kb1="1.05">
  <div class="bg" style="background-image:url('__STILL2__')"></div>
  __CONCEPT__
  <div class="card ad" data-in="0.4" data-dur="0.8"><span class="tag">ILLUSTRATION</span>
    <div class="hd">__ICON__<div><b>__ADPAGE__</b><small>Sponsored</small></div></div>
    <div class="cr"><img src="__LOGO__" alt=""><div class="tx"><b>__PROJECT__</b><span>Diwali offer \u00b7 first 5 bookings</span></div></div>
    <div class="ln">__UNITS__ \u00b7 __AREA__</div>
    <div class="cta" id="ctabtn">__CHAT__ Send WhatsApp message</div>
    <div class="ripple" id="rip"></div><div class="finger" id="fing">__TOUCH__</div>
  </div>
  <div class="cap" data-in="0.7" data-dur="0.5"><div>One of your Diwali ads: Send WhatsApp message</div></div>
</div>

<div class="scene" id="s3" data-start="__S3A__" data-end="__S3B__" data-kb0="1.0" data-kb1="1.05">
  <div class="bg" style="background-image:url('__STILL3__')"></div>
  __CONCEPT__
  <div class="card chatcard" data-in="0.2" data-dur="0.7"><span class="tag">EXAMPLE</span>
    <div class="wh">__ICON__<div><b>__PROJECT__</b><small>Example chat</small></div></div>
    <div class="cbody"><div class="bub out" data-inf="0.10" data-dur="0.4" data-fx="left">Hi, I want details of __PROJECT__<small>__TIME__ \u2713\u2713</small></div></div>
  </div>
  <div class="cap" data-in="0.5" data-dur="0.5"><div>Example: __TIME__, a buyer asks for details</div></div>
</div>

<div class="scene" id="s4" data-start="__S4A__" data-end="__S4B__" data-kb0="1.1" data-kb1="1.15" data-ty0="-52" data-ty1="-62">
  <div class="bg" style="background-image:url('__STILL4__')"></div>
  __CONCEPT__
  <div class="iv" data-in="0.3" data-dur="0.6" data-fx="pop">__IVSTILL__</div>
  <div class="card chatcard"><span class="tag">EXAMPLE</span>
    <div class="wh">__ICON__<div><b>__PROJECT__</b><small>Example chat</small></div></div>
    <div class="cbody">
      <div class="beat" data-f0="0.04" data-f1="0.42"><span class="atag">Automatic reply \u00b7 10:48 PM</span><div class="pdf"><i>PDF</i><div><b>Project brochure</b><span>Sent automatically</span></div></div></div>
      <div class="beat" data-f0="0.42" data-f1="0.72"><span class="hdg">Three quick questions</span><div class="qs"><span>Budget?</span><span>3 or 4 BHK?</span><span>Buying timeline?</span></div></div>
      <div class="beat" data-f0="0.72" data-f1="9"><span class="hdg">Visit time</span><div class="qs"><span>Sat 11:00 AM</span><span>Sat 4:00 PM</span></div><span class="stamp">Example times</span></div>
    </div>
  </div>
  <div class="cap" data-in="0.3" data-dur="0.5"><div>Example: automatic reply, about a minute</div></div>
</div>

<div class="scene" id="s5" data-start="__S5A__" data-end="__S5B__" data-kb0="1.0" data-kb1="1.05">
  <div class="bg" style="background-image:url('__STILL5__')"></div>
  __CONCEPT__
  <div class="iv" data-in="0.4" data-dur="0.6" data-fx="pop">__IVWAVE__</div>
  <div class="card lst" data-in="0.3" data-dur="0.8"><span class="tag">EXAMPLE</span>
    <div class="hd">__ICON__<div><b>__PROJECT__</b><small>All enquiries in one list</small></div></div>
    <div class="row" data-inf="0.30" data-dur="0.5"><div class="av">A</div><div class="mid"><b>Example buyer A</b><span>3 BHK</span></div><div style="text-align:right"><span class="st ok">Visit picked</span><span class="vs">Sat 11:00 AM</span></div></div>
    <div class="row" data-inf="0.50" data-dur="0.5"><div class="av">B</div><div class="mid"><b>Example buyer B</b><span>4 BHK</span></div><div style="text-align:right"><span class="st ok">Visit picked</span><span class="vs">Sat 4:00 PM</span></div></div>
    <div class="row" data-inf="0.66" data-dur="0.5"><div class="av">C</div><div class="mid"><b>Example buyer C</b><span>3 BHK</span></div><div style="text-align:right"><span class="st ask">Asked</span><span class="vs">No slot yet</span></div></div>
  </div>
  <div class="cap" data-in="0.5" data-dur="0.5"><div>Next morning: who asked, who picked a visit</div></div>
</div>

<div class="scene" id="s6" data-start="__S6A__" data-end="__S6B__" data-kb0="1.0" data-kb1="1.04">
  <div class="bg" style="background-image:url('__STILL1__')"></div><div class="dim"></div>
  <div class="ivlogo" data-in="0.1" data-dur="0.6" data-fx="pop"><div><img src="assets/iv-infotech-logo.png" alt="IV Infotech"></div></div>
  <div class="robot" data-in="0.3" data-dur="0.6" data-fx="pop">__IVWAVE__</div>
  <h1 data-in="0.6" data-dur="0.6">See it for<br><em>__PROJECT__</em></h1>
  <div class="cta1" data-inf="0.50" data-dur="0.5">Tap the button below:</div>
  <div class="cta2" data-inf="0.62" data-dur="0.5">\u201cYes, send the demo\u201d</div>
  <div class="arrow" data-inf="0.72" data-dur="0.5">__ARROW__</div>
  <div class="foot" data-in="1.0" data-dur="0.5">Independent concept by IV Infotech. Voice is AI. Not affiliated with __NAME__, WhatsApp or Meta.</div>
</div>

</div>
<script>
const TL = __TL__;
const sc = {}; TL.scenes.forEach(s => sc[s.id] = s);
const XF = 0.4;
function ease(x){x=Math.max(0,Math.min(1,x));return 1-Math.pow(1-x,3)}
const sparks = document.querySelector('#s1 .sparks');
for(let i=0;i<20;i++){const d=document.createElement('div');d.className='sp';sparks.appendChild(d)}
function sparkles(local){
  document.querySelectorAll('#s1 .sp').forEach((d,i)=>{
    const side = (i%2===0) ? 20+((i*53)%90) : 600+((i*47)%90);   // sparks only near the left/right edges, never across the text
    const sy=(i*181)%1100+40, ph=i*1.7;
    d.style.left=(side+Math.sin(local*0.7+ph)*10)+'px';
    d.style.top=(sy-local*12*(0.4+(i%5)*0.15)+1100)%1140+40+'px';
    d.style.opacity=0.25+0.55*Math.abs(Math.sin(local*1.6+ph)); d.style.transform='scale('+(0.6+0.9*((i%4)/3))+')';
  });
}
function setT(t){
  [1,2,3,4,5,6].forEach(id=>{
    const s=sc[id], el=document.getElementById('s'+id);
    const start=s.start-(id===1?0:XF);
    const vis=t>=start && t<s.end;
    el.style.display=vis?'block':'none';
    if(!vis) return;
    el.style.opacity = id===1 ? 1 : Math.min(1,(t-start)/XF);
    const local=t-s.start, base=s.voice_at-s.start, vd=s.voice_dur;
    const bg=el.querySelector('.bg');
    if(bg){const k0=+(el.dataset.kb0||1), k1=+(el.dataset.kb1||1.05); const k=Math.max(0,Math.min(1,(t-start)/(s.end-start)));
      const ty0=+(el.dataset.ty0||0), ty1=+(el.dataset.ty1||0);
      bg.style.transform='translateY('+(ty0+(ty1-ty0)*k)+'px) scale('+(k0+(k1-k0)*k)+')'}
    el.querySelectorAll('[data-in],[data-inf]').forEach(n=>{
      const a=(n.dataset.inf!==undefined)?(base+(+n.dataset.inf)*vd):+n.dataset.in, d=+(n.dataset.dur||0.5), fx=n.dataset.fx||'up';
      const p=ease((local-a)/d);
      n.style.opacity=p;
      if(fx==='up') n.style.transform='translateY('+((1-p)*26)+'px)';
      else if(fx==='pop') n.style.transform='scale('+(0.86+0.14*p)+')';
      else if(fx==='left') n.style.transform='translateX('+((1-p)*-36)+'px)';
    });
    if(id===1) sparkles(local);
    if(id===2){
      const rip=document.getElementById('rip'), fing=document.getElementById('fing'), btn=document.getElementById('ctabtn');
      const a=base+0.80*vd, p=(local-a)/0.9;
      const r=btn.getBoundingClientRect(), card=btn.parentElement.getBoundingClientRect(); const sc2=card.width/608;
      const cx=(r.left-card.left)/sc2 + 150, cy=(r.top-card.top)/sc2 + 34;
      if(p>-0.35&&p<1){
        const fp=ease((p+0.35)/0.35); fing.style.opacity=Math.min(1,fp)*(p<0.7?1:Math.max(0,1-(p-0.7)/0.3));
        fing.style.left=(cx-18)+'px'; fing.style.top=(cy-6+(1-fp)*34 + (p>0&&p<0.18?5:0))+'px';
      } else fing.style.opacity=0;
      if(p>0&&p<1){rip.style.opacity=1-p; const z=36+p*130; rip.style.width=z+'px'; rip.style.height=z+'px'; rip.style.left=(cx-z/2)+'px'; rip.style.top=(cy-z/2)+'px'} else rip.style.opacity=0;
      btn.style.transform=(p>0&&p<0.2)?'scale(0.97)':'scale(1)';
    }
    if(id===4){
      el.querySelectorAll('.beat').forEach(b=>{
        const f0=+b.dataset.f0, f1=+b.dataset.f1, x0=base+f0*vd, x1=base+f1*vd;
        const fi=ease((local-x0)/0.35), fo=(f1>=9)?1:ease((x1-local)/0.3);
        b.style.opacity=Math.max(0,Math.min(fi,fo)); b.style.transform='translateY('+((1-fi)*16)+'px)';
      });
      const iv=el.querySelector('.iv'); const p=ease((local-0.3)/0.6); iv.style.transform='translateY('+(Math.sin(local*2.2)*9+(1-p)*24)+'px) scale('+(0.86+0.14*p)+')';
    }
    if(id===5){const iv=el.querySelector('.iv'); const p=ease((local-0.4)/0.6); iv.style.transform='translateY('+(Math.sin(local*2.0)*8+(1-p)*24)+'px) scale('+(0.86+0.14*p)+')'}
    if(id===6){const ar=el.querySelector('.arrow'); const p=ease((local-(base+0.72*vd))/0.5); ar.style.transform='translateY('+(Math.abs(Math.sin(local*3.2))*14+(1-p)*14)+'px)'}
  });
}
window.setT=setT;
document.fonts.ready.then(()=>{setT(0);window.READY=true});
</script></body></html>"""

ap = lead["brand"]
st = lead["stills"]
rep = {
    "__NAVY__": ap["navy"], "__NAVY2__": ap["navy2"], "__GOLD__": ap["gold"], "__GOLD2__": ap["gold2"],
    "__LOGO__": lead["logo"], "__PROJECT__": lead["project"], "__AREA__": lead["area"], "__UNITS__": lead["units"],
    "__NAME__": lead["name"], "__ADPAGE__": lead["ad_page"], "__TIME__": lead["chat_time"],
    "__ICON__": ICON, "__CONCEPT__": CONCEPT, "__CHAT__": CHAT, "__TOUCH__": TOUCH, "__ARROW__": ARROW, "__IVWAVE__": IV_WAVE, "__IVSTILL__": IV_STILL,
    "__STILL1__": st["1"], "__STILL2__": st["2"], "__STILL3__": st["3"], "__STILL4__": st["4"], "__STILL5__": st["5"],
    "__TL__": json.dumps(tl),
}
for s in tl["scenes"]:
    rep["__S%dA__" % s["id"]] = str(s["start"])
    rep["__S%dB__" % s["id"]] = str(s["end"])
html = T
for k, v in rep.items():
    html = html.replace(k, v)
(HERE / out_name).write_text(html, encoding="utf-8")
print("wrote", out_name, len(html), "bytes")
