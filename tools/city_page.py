#!/usr/bin/env python3
"""Build a city prayer-times page (mock-up for the SEO plan, 20 Nov 2026).

Input: a JSON list of days exported from the Arihna app's own engine (official timetable where one exists),
one entry per day and language: {d, lang, t:{fajr..isha minutes}, hijri, greg, ev:[...]}
Output: prayer-times/<slug>/index.html and ar/prayer-times/<slug>/index.html

The page is static. A small inline script picks today's row by the city's clock and highlights the next prayer;
it sends nothing anywhere. A daily scheduled build would refresh the week.
"""
import json, sys, html, os

SRC, SLUG = sys.argv[1], sys.argv[2]
CITY = {"en": "Abu Dhabi", "ar": "أبوظبي"}
COUNTRY = {"en": "UAE", "ar": "الإمارات"}
ZONE = "Asia/Dubai"
QIBLA = {"deg": "260.8°", "dist": "1,539", "wind": {"en": "West", "ar": "الغرب"}}
OTHERS = [("dubai", "Dubai", "دبي"), ("al-ain", "Al Ain", "العين"), ("sharjah", "Sharjah", "الشارقة"),
          ("ajman", "Ajman", "عجمان"), ("ras-al-khaimah", "Ras Al Khaimah", "رأس الخيمة"), ("fujairah", "Fujairah", "الفجيرة")]
KEYS = ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]
NAMES = {"en": ["Fajr", "Shurooq", "Dhuhr", "Asr", "Maghrib", "Isha"],
         "ar": ["الفجر", "الشروق", "الظهر", "العصر", "المغرب", "العشاء"]}
STORE = "https://apps.apple.com/app/apple-store/id6828256774?pt=95948779&amp;mt=8&amp;ct=website-city-" + SLUG

T = {
 "en": dict(title=f"Prayer times in {CITY['en']} today | Arihna",
   desc=f"Today's prayer times in {CITY['en']} from the official Awqaf timetable: Fajr, Shurooq, Dhuhr, Asr, Maghrib and Isha, this week's times and the Qibla direction.",
   h1=f"Prayer times in {CITY['en']}", today="Today", next="Next", src="From the official Awqaf timetable for Abu Dhabi",
   week="This week", day="Day", qibla="Qibla", qfrom="from true north", qkm="km to the Kaaba",
   occ="Next occasion", indays="in {n} days", app="The sky, the countdown and alerts, in the app",
   applead="Arihna draws these times on the sun's real path, with a Qibla compass, the moon and the Hijri calendar. Free, no ads, no tracking.",
   faq="Questions", q1="Times differ from the mosque by a minute?", a1="In the UAE, Arihna follows the official Awqaf timetable for your area. A mosque may round or adjust by a minute.",
   q2="Which direction is the Qibla from Abu Dhabi?", a2=f"{QIBLA['deg']} from true north, a little south of due west, along the shortest path to the Kaaba over the round Earth.",
   more="Other cities", home="Arihna", lang_other="العربية", upd="Updated daily", dlbadge="Download on the App Store",
   rights="© 2026 Amr Hafez. All rights reserved", privacy="Privacy", support="Support", nowin="{p} in {t}", began="{p} began"),
 "ar": dict(title=f"مواقيت الصلاة في {CITY['ar']} اليوم | أرحنا",
   desc=f"مواقيت الصلاة اليوم في {CITY['ar']} من جدول الأوقاف الرسمي: الفجر والشروق والظهر والعصر والمغرب والعشاء، ومواقيت هذا الأسبوع واتجاه القبلة.",
   h1=f"مواقيت الصلاة في {CITY['ar']}", today="اليوم", next="التالية", src="من جدول الأوقاف الرسمي لأبوظبي",
   week="هذا الأسبوع", day="اليوم", qibla="القبلة", qfrom="من الشمال الحقيقي", qkm="كم إلى الكعبة",
   occ="المناسبة القادمة", indays="بعد {n} يومًا", app="السماء والعد التنازلي والتنبيهات، في التطبيق",
   applead="يرسم أرحنا هذه المواقيت على مسار الشمس الحقيقي، مع بوصلة القبلة والقمر والتقويم الهجري. مجاني، بلا إعلانات ولا تتبّع.",
   faq="أسئلة", q1="المواقيت تختلف عن المسجد بدقيقة؟", a1="في الإمارات يتبع أرحنا جدول الأوقاف الرسمي لمنطقتك. قد يقرّب المسجد الوقت أو يعدّله بدقيقة.",
   q2="ما اتجاه القبلة من أبوظبي؟", a2=f"{QIBLA['deg']} من الشمال الحقيقي، جنوب الغرب بقليل، على أقصر مسار إلى الكعبة على الأرض الكروية.",
   more="مدن أخرى", home="أرحنا", lang_other="English", upd="تُحدَّث يوميًا", dlbadge="حمّل من App Store",
   rights="© 2026 عمرو حافظ. جميع الحقوق محفوظة", privacy="الخصوصية", support="الدعم", nowin="{p} بعد {t}", began="بدأ {p}"),
}
OCC_AR = {"UAE National Day": "عيد الاتحاد", "New Year's Day": "رأس السنة الميلادية"}

def hm(m, lang):
    h, mi = divmod(int(m), 60)
    suf = ("AM" if h < 12 else "PM") if lang == "en" else ("ص" if h < 12 else "م")
    return f"{(h % 12) or 12}:{mi:02d}", suf

data = json.load(open(SRC, encoding="utf-8"))

def page(lang):
    L = T[lang]; rtl = lang == "ar"; days = [x for x in data if x["lang"] == lang]
    pre = "../../" if not rtl else "../../../"
    d0 = days[0]
    def tiles(day):
        o = []
        for i, k in enumerate(KEYS):
            t, s = hm(day["t"][k], lang)
            o.append(f'<li data-k="{k}" data-m="{day["t"][k]}"{" class=minor" if k == "sunrise" else ""}><span class="n">{NAMES[lang][i]}</span><b>{t}</b><small>{s}</small></li>')
        return "".join(o)
    rows = []
    for x in days:
        cells = "".join(f"<td>{hm(x['t'][k], lang)[0]}</td>" for k in KEYS)
        rows.append(f'<tr data-d="2026-11-{x["d"]:02d}"><th scope="row"><b>{html.escape(x["greg"])}</b><span>{html.escape(x["hijri"])}</span></th>{cells}</tr>')
    ev = d0["ev"][0]; n = (ev["g"]["d"] - d0["d"]) + (30 if ev["g"]["m"] == 12 else 0)
    evn = ev["n"] if lang == "en" else OCC_AR.get(ev["n"], ev["n"])
    evd = "Wednesday 2 December 2026" if lang == "en" else "الأربعاء 2 ديسمبر 2026"
    week_json = json.dumps({f"2026-11-{x['d']:02d}": [x["t"][k] for k in KEYS] for x in days})
    others = "".join(f'<a href="{"../" if True else ""}{s}/">{(e if lang == "en" else a)}</a>' for s, e, a in OTHERS)
    alt_href = f"https://getarihna.com/ar/prayer-times/{SLUG}/" if not rtl else f"https://getarihna.com/prayer-times/{SLUG}/"
    self_href = f"https://getarihna.com/{'ar/' if rtl else ''}prayer-times/{SLUG}/"
    ld = {
      "@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": self_href, "url": self_href, "name": L["title"], "description": L["desc"], "inLanguage": lang,
         "about": {"@type": "Place", "name": CITY[lang], "address": {"@type": "PostalAddress", "addressLocality": CITY["en"], "addressCountry": "AE"}},
         "isPartOf": {"@type": "WebSite", "name": "Arihna", "url": "https://getarihna.com/"}},
        {"@type": "BreadcrumbList", "itemListElement": [
          {"@type": "ListItem", "position": 1, "name": "Arihna", "item": "https://getarihna.com/" + ("ar/" if rtl else "")},
          {"@type": "ListItem", "position": 2, "name": L["h1"], "item": self_href}]},
        {"@type": "FAQPage", "mainEntity": [
          {"@type": "Question", "name": L["q1"], "acceptedAnswer": {"@type": "Answer", "text": L["a1"]}},
          {"@type": "Question", "name": L["q2"], "acceptedAnswer": {"@type": "Answer", "text": L["a2"]}}]}]}
    head_cells = "".join(f'<th scope="col">{x}</th>' for x in NAMES[lang])
    return f'''<!doctype html>
<html lang="{lang}" dir="{'rtl' if rtl else 'ltr'}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{L["title"]}</title>
<meta name="description" content="{L["desc"]}">
<meta name="theme-color" content="#081428">
<meta name="apple-itunes-app" content="app-id=6828256774">
<link rel="canonical" href="{self_href}">
<link rel="alternate" hreflang="en" href="https://getarihna.com/prayer-times/{SLUG}/">
<link rel="alternate" hreflang="ar" href="https://getarihna.com/ar/prayer-times/{SLUG}/">
<link rel="alternate" hreflang="x-default" href="https://getarihna.com/prayer-times/{SLUG}/">
<meta property="og:type" content="website"><meta property="og:title" content="{L["title"]}"><meta property="og:description" content="{L["desc"]}">
<meta property="og:url" content="{self_href}"><meta property="og:image" content="https://getarihna.com/img/og-12-{lang}.jpg">
<link rel="icon" href="{pre}icons/icon-192.png"><link rel="apple-touch-icon" href="{pre}icons/apple-touch-icon.png">
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>
<style>
@font-face{{font-family:'Outfit';font-weight:300;font-display:swap;src:url({pre}fonts/Outfit-300.woff2) format('woff2')}}
@font-face{{font-family:'Outfit';font-weight:400;font-display:swap;src:url({pre}fonts/Outfit-400.woff2) format('woff2')}}
@font-face{{font-family:'Outfit';font-weight:500;font-display:swap;src:url({pre}fonts/Outfit-500.woff2) format('woff2')}}
@font-face{{font-family:'Noto Sans Arabic';font-weight:400;font-display:swap;src:url({pre}fonts/NotoSansArabic-400.woff2) format('woff2')}}
@font-face{{font-family:'Noto Sans Arabic';font-weight:500;font-display:swap;src:url({pre}fonts/NotoSansArabic-500.woff2) format('woff2')}}
:root{{--ink:#0A1117;--ink2:#0F1920;--fg:#F1F5F4;--fg2:#C9D4D3;--muted:#8E9DA0;--line:rgba(255,255,255,.09);--accent:#7BE3BE;--sun:#F6C35B;color-scheme:dark}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--ink);color:var(--fg);font-family:'Outfit','Noto Sans Arabic',system-ui,sans-serif;-webkit-font-smoothing:antialiased;line-height:1.5}}
[dir=rtl] body,body[dir=rtl]{{font-family:'Noto Sans Arabic','Outfit',system-ui,sans-serif}}
::selection{{background:rgba(246,195,91,.35);color:#fff}}
a{{color:inherit}}a:focus-visible,button:focus-visible{{outline:2px solid var(--accent);outline-offset:3px;border-radius:6px}}
.w{{max-width:760px;margin:0 auto;padding-left:max(18px,env(safe-area-inset-left));padding-right:max(18px,env(safe-area-inset-right))}}
header{{padding-top:max(16px,env(safe-area-inset-top))}}
.top{{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 0}}
.brand{{display:flex;align-items:center;gap:10px;text-decoration:none;font-weight:500}}
.brand img{{width:32px;height:32px;border-radius:8px}}
.lang{{font-size:14px;color:var(--fg2);text-decoration:none;padding:6px 12px;border-radius:999px;box-shadow:inset 0 0 0 1px var(--line)}}
.hero{{position:relative;margin-top:8px;padding:28px 22px 22px;border-radius:28px;overflow:hidden;background:radial-gradient(120% 90% at 80% 0%,rgba(246,195,91,.16),transparent 55%),linear-gradient(180deg,#132447 0%,#1B2F57 55%,#0F1A2C 100%);box-shadow:inset 0 0 0 1px var(--line)}}
.hero::after{{content:"";position:absolute;left:0;right:0;bottom:0;height:64px;background:linear-gradient(180deg,transparent,rgba(8,14,22,.55))}}
h1{{margin:0;font-size:clamp(28px,6vw,40px);font-weight:500;letter-spacing:-.01em;line-height:1.15;text-wrap:balance}}
.date{{margin:8px 0 0;color:var(--fg2);font-size:15px}}.date b{{color:var(--fg);font-weight:500}}
.cd{{margin:18px 0 0;font-size:16px;color:var(--fg2);min-height:24px}}.cd b{{color:var(--accent);font-weight:500;font-variant-numeric:tabular-nums}}
.times{{position:relative;z-index:1;list-style:none;margin:20px 0 0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}}
@media (min-width:620px){{.times{{grid-template-columns:repeat(6,minmax(0,1fr))}}}}
.times li{{padding:12px 10px;border-radius:18px;background:rgba(255,255,255,.06);box-shadow:inset 0 0 0 1px rgba(255,255,255,.08);text-align:center}}
.times .n{{display:block;font-size:13.5px;color:var(--fg2)}}.times b{{display:block;font-size:26px;font-weight:300;line-height:1.2;font-variant-numeric:tabular-nums}}.times small{{font-size:12px;color:var(--muted)}}
.times li.minor b{{color:var(--fg2)}}
.times li.nx{{background:rgba(123,227,190,.12);box-shadow:inset 0 0 0 1px rgba(123,227,190,.42)}}.times li.nx .n{{color:var(--accent)}}
.src{{position:relative;z-index:1;display:inline-flex;align-items:center;gap:7px;margin-top:16px;padding:6px 12px;border-radius:999px;font-size:13px;color:var(--accent);background:rgba(123,227,190,.1)}}
.src svg{{width:14px;height:14px}}
section{{margin-top:34px}}
h2{{font-size:20px;font-weight:500;margin:0 0 12px}}
.tw{{overflow-x:auto;border-radius:20px;box-shadow:inset 0 0 0 1px var(--line);background:var(--ink2)}}
table{{border-collapse:collapse;width:100%;min-width:500px;font-size:14.5px;font-variant-numeric:tabular-nums}}
th,td{{padding:11px 12px;text-align:start;border-bottom:1px solid var(--line);white-space:nowrap}}
thead th{{font-size:12.5px;font-weight:500;color:var(--muted)}}
tbody th{{font-weight:400}}tbody th b{{display:block;font-weight:500}}tbody th span{{font-size:12px;color:var(--muted)}}
tbody tr:last-child th,tbody tr:last-child td{{border-bottom:0}}
tr.today{{background:rgba(123,227,190,.07)}}tr.today th b{{color:var(--accent)}}
.cards{{display:grid;grid-template-columns:1fr;gap:10px}}@media (min-width:620px){{.cards{{grid-template-columns:1fr 1fr}}}}
.card{{padding:18px;border-radius:20px;background:var(--ink2);box-shadow:inset 0 0 0 1px var(--line)}}
.card small{{display:block;font-size:13px;color:var(--muted)}}.card b{{display:block;font-size:28px;font-weight:300;margin-top:2px}}.card span{{font-size:14px;color:var(--fg2)}}
.app{{display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:space-between;padding:22px;border-radius:24px;background:linear-gradient(135deg,#14243F,#0F1A2C);box-shadow:inset 0 0 0 1px var(--line)}}
.app div{{flex:1 1 280px;min-width:0}}.app h2{{margin:0 0 6px}}.app p{{margin:0;color:var(--fg2);font-size:15px;max-width:52ch}}
.app a{{display:inline-block;transition:transform 160ms cubic-bezier(.23,1,.32,1)}}.app a:active{{transform:scale(.97)}}
details{{border-radius:18px;background:var(--ink2);box-shadow:inset 0 0 0 1px var(--line);padding:0 16px;margin-bottom:8px}}
summary{{cursor:pointer;padding:15px 0;font-weight:500;list-style:none}}summary::-webkit-details-marker{{display:none}}
details p{{margin:0 0 15px;color:var(--fg2);font-size:15px;max-width:65ch}}
.cities{{display:flex;flex-wrap:wrap;gap:8px}}.cities a{{text-decoration:none;padding:8px 14px;border-radius:999px;box-shadow:inset 0 0 0 1px var(--line);font-size:14.5px;color:var(--fg2)}}
footer{{margin-top:44px;padding:22px 0 max(26px,env(safe-area-inset-bottom));border-top:1px solid var(--line);color:var(--muted);font-size:13px;display:flex;flex-wrap:wrap;gap:14px;justify-content:space-between}}
footer a{{text-decoration:none}}
</style>
</head>
<body>
<div class="w">
<header><div class="top"><a class="brand" href="{pre}{'ar/' if rtl else ''}"><img src="{pre}icons/icon-192.png" alt="" width="32" height="32"><span>{L["home"]}</span></a><a class="lang" href="{alt_href}" hreflang="{'en' if rtl else 'ar'}">{L["lang_other"]}</a></div></header>
<main>
<div class="hero">
<h1>{L["h1"]}</h1>
<p class="date" id="date"><b>{html.escape(d0["greg"])}</b> · {html.escape(d0["hijri"])}</p>
<p class="cd" id="cd" aria-live="polite"></p>
<ul class="times" id="times">{tiles(d0)}</ul>
<span class="src"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg>{L["src"]}</span>
</div>
<section aria-labelledby="wk"><h2 id="wk">{L["week"]}</h2><div class="tw"><table><thead><tr><th scope="col">{L["day"]}</th>{head_cells}</tr></thead><tbody>{"".join(rows)}</tbody></table></div></section>
<section class="cards" aria-label="{L["qibla"]}, {L["occ"]}">
<div class="card"><small>{L["qibla"]}</small><b>{QIBLA["deg"]}</b><span>{L["qfrom"]} · {QIBLA["wind"][lang]} · {QIBLA["dist"]} {L["qkm"]}</span></div>
<div class="card"><small>{L["occ"]}</small><b>{evn}</b><span>{evd} · {L["indays"].format(n=n)}</span></div>
</section>
<section class="app"><div><h2>{L["app"]}</h2><p>{L["applead"]}</p></div><a href="{STORE}"><img src="{pre}img/badge-app-store.svg" alt="{L["dlbadge"]}" width="150" height="50"></a></section>
<section aria-labelledby="fq"><h2 id="fq">{L["faq"]}</h2>
<details><summary>{L["q1"]}</summary><p>{L["a1"]}</p></details>
<details><summary>{L["q2"]}</summary><p>{L["a2"]}</p></details></section>
<section aria-labelledby="oc"><h2 id="oc">{L["more"]}</h2><nav class="cities" id="oc-n">{others}</nav></section>
</main>
<footer><span>{L["rights"]}</span><span><a href="{pre}privacy.html{'?lang=ar' if rtl else ''}">{L["privacy"]}</a> · <a href="{pre}support.html{'?lang=ar' if rtl else ''}">{L["support"]}</a> · {L["upd"]}</span></footer>
</div>
<script>
/* Today's row by the city's clock, and the next prayer. Runs on the page only; nothing is sent anywhere. */
(function(){{var W={week_json},K={json.dumps(KEYS)},N={json.dumps(NAMES[lang], ensure_ascii=False)},AR={'true' if rtl else 'false'};
var f=new Intl.DateTimeFormat("en-CA",{{timeZone:"{ZONE}",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",second:"2-digit",hourCycle:"h23"}});
function now(){{var p={{}};f.formatToParts(new Date()).forEach(function(x){{p[x.type]=x.value}});return {{d:p.year+"-"+p.month+"-"+p.day,m:(+p.hour)*60+(+p.minute)+(+p.second)/60}}}}
var tr=document.querySelectorAll("tbody tr");
function run(){{var n=now(),t=W[n.d],li=document.querySelectorAll("#times li"),cd=document.getElementById("cd");
 [].forEach.call(tr,function(r){{r.classList.toggle("today",r.getAttribute("data-d")===n.d)}});
 if(!t){{cd.textContent="";return}}
 var i=-1;for(var k=0;k<6;k++){{if(k===1)continue;if(t[k]>n.m){{i=k;break}}}}
 [].forEach.call(li,function(x,j){{x.classList.toggle("nx",j===i)}});
 if(i<0){{cd.textContent="";return}}var s=Math.max(0,Math.round((t[i]-n.m)*60)),h=Math.floor(s/3600),m=Math.floor(s%3600/60),c=(h?h+":"+(m<10?"0":"")+m:m+":"+((s%60)<10?"0":"")+(s%60));
 cd.innerHTML={json.dumps(L["nowin"], ensure_ascii=False)}.replace("{{p}}",N[i]).replace("{{t}}","<b>"+c+"</b>")}}
run();setInterval(run,1000)}})();
</script>
</body>
</html>
'''

for lang in ("en", "ar"):
    out = f"prayer-times/{SLUG}/index.html" if lang == "en" else f"ar/prayer-times/{SLUG}/index.html"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    open(out, "w", encoding="utf-8").write(page(lang))
    print("wrote", out)
