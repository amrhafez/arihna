#!/usr/bin/env python3
"""Build the city prayer-times pages (approved by Amr, 21 Nov 2026).

Input: data/cities-ae.json, exported from the Arihna app's own engine (official Awqaf timetables):
  days [{y,m,d,wd}], cities {slug: {times:[[fajr..isha minutes] per day], loc:{lat,lng,name}}},
  names {slug: Arabic name}, hijri {en:[...], ar:[...]}, ev [{n,g,isl}]
Output: prayer-times/<slug>/index.html and ar/prayer-times/<slug>/index.html for every city.

Each page carries every day in the file. The HTML shows the build day (what search engines read);
a small inline script picks today's row and the next prayer by the UAE clock. It sends nothing anywhere.
Refresh: re-export and rebuild about once a month, so the file always reaches a few months ahead.
"""
import json, html, math, os, sys

CTRY = {
 "ae": dict(zone="Asia/Dubai", order=["abu-dhabi", "dubai", "sharjah", "al-ain", "ajman", "umm-al-quwain", "ras-al-khaimah", "fujairah"],
   en=dict(name="the UAE", src="From the official Awqaf timetable for {c}", calc="", auth="the official Awqaf timetable",
           a1="In the UAE, Arihna follows the official Awqaf timetable for your area. A mosque may round or adjust by a minute."),
   ar=dict(name="الإمارات", src="من جدول الأوقاف الرسمي لـ{c}", calc="", auth="جدول الأوقاف الرسمي",
           a1="في الإمارات يتبع أرحنا جدول الأوقاف الرسمي لمنطقتك. قد يقرّب المسجد الوقت أو يعدّله بدقيقة.")),
 "sa": dict(zone="Asia/Riyadh", order=["mecca", "medina", "riyadh", "jeddah", "dammam", "al-khobar", "taif", "abha", "tabuk", "buraydah"],
   en=dict(name="Saudi Arabia", src="From the official Umm al-Qura timetable for {c}", calc="", auth="the official Umm al-Qura timetable",
           a1="In Saudi Arabia, Arihna follows the official Umm al-Qura timetable for your city. A mosque may round or adjust by a minute."),
   ar=dict(name="السعودية", src="من تقويم أم القرى الرسمي لـ{c}", calc="", auth="تقويم أم القرى الرسمي",
           a1="في السعودية يتبع أرحنا تقويم أم القرى الرسمي لمدينتك. قد يقرّب المسجد الوقت أو يعدّله بدقيقة.")),
 "eg": dict(zone="Africa/Cairo", order=["cairo", "alexandria", "mansoura", "tanta", "port-said", "suez", "asyut", "luxor", "aswan", "hurghada"],
   en=dict(name="Egypt", src="From the official Survey Authority timetable for {c}", calc="Calculated with the Egyptian Survey Authority's method until its 2027 timetable is published", auth="the Egyptian Survey Authority's timetable",
           a1="In Egypt, Arihna follows the Egyptian General Authority for Survey's timetable for your city, and its method on days the timetable does not yet cover. A mosque may round or adjust by a minute."),
   ar=dict(name="مصر", src="من جدول هيئة المساحة الرسمي لـ{c}", calc="محسوبة بطريقة الهيئة المصرية العامة للمساحة حتى نشر جدول 2027", auth="جدول الهيئة المصرية العامة للمساحة",
           a1="في مصر يتبع أرحنا جدول الهيئة المصرية العامة للمساحة لمدينتك، وطريقتها في الأيام التي لم يصدر جدولها بعد. قد يقرّب المسجد الوقت أو يعدّله بدقيقة.")),
}
DATA = {}
for cc in CTRY:
    d = json.load(open(f"data/cities-{cc}.json", encoding="utf-8"))
    if cc != "ae":  # exported with the app's ids, e.g. "sa-riyadh"
        for k in ("cities", "names", "official"):
            if k in d: d[k] = {c.split("-", 1)[1]: v for c, v in d[k].items()}
    DATA[cc] = d
KEYS = ["fajr", "sunrise", "dhuhr", "asr", "maghrib", "isha"]
NAMES = {"en": ["Fajr", "Shurooq", "Dhuhr", "Asr", "Maghrib", "Isha"], "ar": ["الفجر", "الشروق", "الظهر", "العصر", "المغرب", "العشاء"]}
WIND = {"en": ["north", "north-northeast", "northeast", "east-northeast", "east", "east-southeast", "southeast", "south-southeast", "south", "south-southwest", "southwest", "west-southwest", "west", "west-northwest", "northwest", "north-northwest"],
        "ar": ["الشمال", "شمال الشمال الشرقي", "الشمال الشرقي", "شرق الشمال الشرقي", "الشرق", "شرق الجنوب الشرقي", "الجنوب الشرقي", "جنوب الجنوب الشرقي", "الجنوب", "جنوب الجنوب الغربي", "الجنوب الغربي", "غرب الجنوب الغربي", "الغرب", "غرب الشمال الغربي", "الشمال الغربي", "شمال الشمال الغربي"]}
OCC_AR = {"Founding Day": "يوم التأسيس", "Flag Day": "يوم العلم", "Saudi National Day": "اليوم الوطني السعودي", "Coptic Christmas": "عيد الميلاد المجيد",
          "25 January Revolution and Police Day": "عيد ثورة 25 يناير وعيد الشرطة", "Sinai Liberation Day": "عيد تحرير سيناء", "Sham El Nessim": "شم النسيم", "Labour Day": "عيد العمال",
          "UAE National Day": "عيد الاتحاد", "New Year's Day": "رأس السنة الميلادية", "Isra and Mi'raj": "الإسراء والمعراج",
          "Zayed the Founder Day": "يوم زايد المؤسِّس", "Mid-Sha'ban": "منتصف شعبان", "Ramadan begins": "بداية رمضان",
          "Laylat al-Qadr": "ليلة القدر", "Eid al-Fitr": "عيد الفطر", "Arafat Day": "يوم عرفة", "Eid al-Adha": "عيد الأضحى",
          "Islamic New Year": "رأس السنة الهجرية", "Ashura": "عاشوراء", "The Prophet's Birthday": "المولد النبوي"}
WD = {"en": ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"], "ar": ["الأحد", "الاثنين", "الثلاثاء", "الأربعاء", "الخميس", "الجمعة", "السبت"]}
WDL = {"en": ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"], "ar": WD["ar"]}
MON = {"en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
       "ar": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"]}
MONL = {"en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"], "ar": MON["ar"]}
STORE = "https://apps.apple.com/app/apple-store/id6828256774?pt=95948779&amp;mt=8&amp;ct=website-city-"


def vincenty(lat1, lon1, lat2=21.4225, lon2=39.8262):
    """Initial bearing and distance to the Kaaba on the WGS84 ellipsoid, as the app computes the Qibla."""
    a = 6378137.0; f = 1 / 298.257223563; b = (1 - f) * a
    L = math.radians(lon2 - lon1); U1 = math.atan((1 - f) * math.tan(math.radians(lat1))); U2 = math.atan((1 - f) * math.tan(math.radians(lat2)))
    sU1, cU1, sU2, cU2 = math.sin(U1), math.cos(U1), math.sin(U2), math.cos(U2); lam = L
    for _ in range(200):
        sl, cl = math.sin(lam), math.cos(lam); ss = math.hypot(cU2 * sl, cU1 * sU2 - sU1 * cU2 * cl); cs = sU1 * sU2 + cU1 * cU2 * cl; sig = math.atan2(ss, cs)
        sa = cU1 * cU2 * sl / ss; c2a = 1 - sa * sa; c2m = cs - 2 * sU1 * sU2 / c2a if c2a else 0; C = f / 16 * c2a * (4 + f * (4 - 3 * c2a))
        lp = lam; lam = L + (1 - C) * f * sa * (sig + C * ss * (c2m + C * cs * (-1 + 2 * c2m * c2m)))
        if abs(lam - lp) < 1e-12: break
    u2 = c2a * (a * a - b * b) / (b * b); A = 1 + u2 / 16384 * (4096 + u2 * (-768 + u2 * (320 - 175 * u2))); B = u2 / 1024 * (256 + u2 * (-128 + u2 * (74 - 47 * u2)))
    ds = B * ss * (c2m + B / 4 * (cs * (-1 + 2 * c2m * c2m) - B / 6 * c2m * (-3 + 4 * ss * ss) * (-3 + 4 * c2m * c2m)))
    az = math.degrees(math.atan2(cU2 * math.sin(lam), cU1 * sU2 - sU1 * cU2 * math.cos(lam))) % 360
    return az, b * A * (sig - ds) / 1000


def hm(m, lang):
    h, mi = divmod(int(m), 60)
    return f"{(h % 12) or 12}:{mi:02d}", (("AM" if h < 12 else "PM") if lang == "en" else ("ص" if h < 12 else "م"))


def iso(x): return f"{x['y']}-{x['m']:02d}-{x['d']:02d}"
def gshort(x, lang): return f"{WD[lang][x['wd']]} {x['d']} {MON[lang][x['m'] - 1]}" if lang == "en" else f"{WD[lang][x['wd']]}، {x['d']} {MON[lang][x['m'] - 1]}"
def glong(x, lang): return f"{WDL[lang][x['wd']]} {x['d']} {MONL[lang][x['m'] - 1]} {x['y']}" if lang == "en" else f"{WDL[lang][x['wd']]} {x['d']} {MONL[lang][x['m'] - 1]} {x['y']}"


def page(cc, slug, lang):
    D = DATA[cc]; K = CTRY[cc]; Kl = K[lang]; ORDER = K["order"]; mecca = slug == "mecca"
    rtl = lang == "ar"; en_name = D["cities"][slug]["loc"]["name"]; ar_name = D["names"][slug]; city = ar_name if rtl else en_name
    loc = D["cities"][slug]["loc"]; az, km = vincenty(loc["lat"], loc["lng"]); wind = WIND[lang][round(az / 22.5) % 16]
    deg = f"{az:.1f}°"; dist = f"{round(km):,}"
    times = D["cities"][slug]["times"]; days = D["days"]; hij = D["hijri"][lang]
    pre = "../../../" if rtl else "../../"
    self_href = f"https://getarihna.com/{'ar/' if rtl else ''}prayer-times/{slug}/"
    L = {
     "en": dict(title=f"Prayer times in {city} today | Arihna",
       desc=f"Today's prayer times in {city} from {Kl['auth']}: Fajr, Shurooq, Dhuhr, Asr, Maghrib and Isha, this week's times and the Qibla direction.",
       h1=f"Prayer times in {city}", src=Kl["src"].format(c=city), calc=Kl["calc"], week="This week", day="Day", qibla="Qibla",
       qline=f"from true north · {wind.capitalize()} · {dist} km to the Kaaba", occ="Next occasion", app="The sky, the countdown and alerts, in the app",
       applead="Arihna draws these times on the sun's real path, with a Qibla compass, the moon and the Hijri calendar. Free, no ads, no tracking.",
       faq="Questions", q1="Times differ from the mosque by a minute?", a1=Kl["a1"],
       q2=f"Which direction is the Qibla from {city}?", a2=f"{deg} from true north ({wind}), along the shortest path to the Kaaba over the round Earth.",
       more=f"Other cities in {Kl['name']}", home="Arihna", other="العربية", dl="Download on the App Store",
       rights="© 2026 Amr Hafez. All rights reserved", privacy="Privacy", support="Support", upd="Updated monthly", nowin="{p} in {t}", exp="expected", today="Today", tomorrow="Tomorrow", indays="in {n} days", old="These times are being updated. Open Arihna for today's times."),
     "ar": dict(title=f"مواقيت الصلاة في {city} اليوم | أرحنا",
       desc=f"مواقيت الصلاة اليوم في {city} من {Kl['auth']}: الفجر والشروق والظهر والعصر والمغرب والعشاء، ومواقيت هذا الأسبوع واتجاه القبلة.",
       h1=f"مواقيت الصلاة في {city}", src=Kl["src"].format(c=city), calc=Kl["calc"], week="هذا الأسبوع", day="اليوم", qibla="القبلة",
       qline=f"من الشمال الحقيقي · {wind} · {dist} كم إلى الكعبة", occ="المناسبة القادمة", app="السماء والعد التنازلي والتنبيهات، في التطبيق",
       applead="يرسم أرحنا هذه المواقيت على مسار الشمس الحقيقي، مع بوصلة القبلة والقمر والتقويم الهجري. مجاني، بلا إعلانات ولا تتبّع.",
       faq="أسئلة", q1="المواقيت تختلف عن المسجد بدقيقة؟", a1=Kl["a1"],
       q2=f"ما اتجاه القبلة من {city}؟", a2=f"{deg} من الشمال الحقيقي (جهة {wind})، على أقصر مسار إلى الكعبة على الأرض الكروية.",
       more=f"مدن أخرى في {Kl['name']}", home="أرحنا", other="English", dl="حمّل من App Store",
       rights="© 2026 عمرو حافظ. جميع الحقوق محفوظة", privacy="الخصوصية", support="الدعم", upd="تُحدَّث شهريًا", nowin="{p} بعد {t}", exp="متوقع", today="اليوم", tomorrow="غدًا", indays="بعد {n} يومًا", old="يجري تحديث هذه المواقيت. افتح أرحنا لمواقيت اليوم."),
    }[lang]
    d0 = days[0]; t0 = times[0]
    def tiles(t):
        o = []
        for i, k in enumerate(KEYS):
            a, s = hm(t[i], lang)
            o.append(f'<li{" class=minor" if k == "sunrise" else ""}><span class="n">{NAMES[lang][i]}</span><b>{a}</b><small>{s}</small></li>')
        return "".join(o)
    def rows(i0):
        o = []
        for i in range(i0, min(i0 + 7, len(days))):
            cells = "".join(f"<td>{hm(m, lang)[0]}</td>" for m in times[i])
            o.append(f'<tr><th scope="row"><b>{gshort(days[i], lang)}</b><span>{html.escape(hij[i])}</span></th>{cells}</tr>')
        return "".join(o)
    evs = []
    for e in D["ev"]:
        nm = e["n"] if lang == "en" else OCC_AR.get(e["n"], e["n"])
        g = e["g"]; g.setdefault("wd", 0)
        evs.append([iso(g), nm, glong(g, lang), 1 if e.get("isl") else 0])
    ev0 = evs[0]
    def evline(ev, n):
        when = L["today"] if n == 0 else L["tomorrow"] if n == 1 else L["indays"].format(n=n)
        return f'{ev[2]}{" · " + L["exp"] if ev[3] else ""} · {when}'
    import datetime
    n0 = (datetime.date.fromisoformat(ev0[0]) - datetime.date(d0["y"], d0["m"], d0["d"])).days
    OFFI = D.get("official", {}).get(slug) or [1] * len(days)
    DAYS = [[iso(days[i]), gshort(days[i], lang), hij[i], times[i], OFFI[i]] for i in range(len(days))]
    others = "".join(f'<a href="../{s}/">{D["names"][s] if rtl else D["cities"][s]["loc"]["name"]}</a>' for s in ORDER if s != slug)
    ld = {"@context": "https://schema.org", "@graph": [
        {"@type": "WebPage", "@id": self_href, "url": self_href, "name": L["title"], "description": L["desc"], "inLanguage": lang,
         "about": {"@type": "City", "name": city, "address": {"@type": "PostalAddress", "addressLocality": en_name, "addressCountry": cc.upper()}},
         "isPartOf": {"@id": "https://getarihna.com/#site"}},
        {"@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": "Arihna" if not rtl else "أرحنا", "item": "https://getarihna.com/" + ("ar/" if rtl else "")},
            {"@type": "ListItem", "position": 2, "name": L["h1"], "item": self_href}]},
        {"@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": L["q1"], "acceptedAnswer": {"@type": "Answer", "text": L["a1"]}}] + ([] if mecca else [
            {"@type": "Question", "name": L["q2"], "acceptedAnswer": {"@type": "Answer", "text": L["a2"]}}])}]}
    head_cells = "".join(f'<th scope="col">{x}</th>' for x in NAMES[lang])
    J = lambda o: json.dumps(o, ensure_ascii=False, separators=(",", ":"))
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
<link rel="alternate" hreflang="en" href="https://getarihna.com/prayer-times/{slug}/">
<link rel="alternate" hreflang="ar" href="https://getarihna.com/ar/prayer-times/{slug}/">
<link rel="alternate" hreflang="x-default" href="https://getarihna.com/prayer-times/{slug}/">
<meta property="og:type" content="website"><meta property="og:site_name" content="Arihna · أرحنا"><meta property="og:title" content="{L["title"]}"><meta property="og:description" content="{L["desc"]}">
<meta property="og:url" content="{self_href}"><meta property="og:image" content="https://getarihna.com/img/og-12-{lang}.jpg">
<link rel="icon" href="{pre}icons/icon-192.png"><link rel="apple-touch-icon" href="{pre}icons/apple-touch-icon.png">
<link rel="preload" href="{pre}fonts/{'NotoSansArabic' if rtl else 'Outfit'}-400.woff2" as="font" type="font/woff2" crossorigin>
<script type="application/ld+json">{J(ld)}</script>
<style>
@font-face{{font-family:'Outfit';font-weight:300;font-display:swap;src:url({pre}fonts/Outfit-300.woff2) format('woff2')}}
@font-face{{font-family:'Outfit';font-weight:400;font-display:swap;src:url({pre}fonts/Outfit-400.woff2) format('woff2')}}
@font-face{{font-family:'Outfit';font-weight:500;font-display:swap;src:url({pre}fonts/Outfit-500.woff2) format('woff2')}}
@font-face{{font-family:'Noto Sans Arabic';font-weight:400;font-display:swap;src:url({pre}fonts/NotoSansArabic-400.woff2) format('woff2')}}
@font-face{{font-family:'Noto Sans Arabic';font-weight:500;font-display:swap;src:url({pre}fonts/NotoSansArabic-500.woff2) format('woff2')}}
:root{{--ink:#0A1117;--ink2:#0F1920;--fg:#F1F5F4;--fg2:#C9D4D3;--muted:#8E9DA0;--line:rgba(255,255,255,.09);--accent:#7BE3BE;--sun:#F6C35B;color-scheme:dark}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--ink);color:var(--fg);font-family:{"'Noto Sans Arabic','Outfit'" if rtl else "'Outfit','Noto Sans Arabic'"},system-ui,sans-serif;-webkit-font-smoothing:antialiased;line-height:1.5}}
::selection{{background:rgba(246,195,91,.35);color:#fff}}
a{{color:inherit}}a:focus-visible,summary:focus-visible{{outline:2px solid var(--accent);outline-offset:3px;border-radius:6px}}
.w{{max-width:760px;margin:0 auto;padding-left:max(18px,env(safe-area-inset-left));padding-right:max(18px,env(safe-area-inset-right))}}
header{{padding-top:max(16px,env(safe-area-inset-top))}}
.top{{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:14px 0}}
.brand{{display:flex;align-items:center;gap:10px;text-decoration:none;font-weight:500}}.brand img{{width:32px;height:32px;border-radius:8px}}
.lang{{font-size:14px;color:var(--fg2);text-decoration:none;padding:6px 12px;border-radius:999px;box-shadow:inset 0 0 0 1px var(--line)}}
.hero{{position:relative;margin-top:8px;padding:28px 22px 22px;border-radius:28px;overflow:hidden;background:radial-gradient(120% 90% at 80% 0%,rgba(246,195,91,.16),transparent 55%),linear-gradient(180deg,#132447 0%,#1B2F57 55%,#0F1A2C 100%);box-shadow:inset 0 0 0 1px var(--line)}}
h1{{margin:0;font-size:clamp(28px,6vw,40px);font-weight:500;letter-spacing:-.01em;line-height:1.15;text-wrap:balance}}
.date{{margin:8px 0 0;color:var(--fg2);font-size:15px}}.date b{{color:var(--fg);font-weight:500}}
.cd{{margin:18px 0 0;font-size:16px;color:var(--fg2);min-height:24px}}.cd b{{color:var(--accent);font-weight:500;font-variant-numeric:tabular-nums}}
.times{{list-style:none;margin:20px 0 0;padding:0;display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:8px}}
@media (min-width:620px){{.times{{grid-template-columns:repeat(6,minmax(0,1fr))}}}}
.times li{{padding:12px 6px;border-radius:18px;background:rgba(255,255,255,.06);box-shadow:inset 0 0 0 1px rgba(255,255,255,.08);text-align:center}}
.times .n{{display:block;font-size:13.5px;color:var(--fg2)}}.times b{{display:block;font-size:26px;font-weight:300;line-height:1.2;font-variant-numeric:tabular-nums}}.times small{{font-size:12px;color:var(--muted)}}
.times li.minor b{{color:var(--fg2)}}
.times li.nx{{background:rgba(123,227,190,.12);box-shadow:inset 0 0 0 1px rgba(123,227,190,.42)}}.times li.nx .n{{color:var(--accent)}}
.hero.old .times,.hero.old .date{{opacity:.35}}
.src{{display:inline-flex;align-items:center;gap:7px;margin-top:16px;padding:6px 12px;border-radius:999px;font-size:13px;color:var(--accent);background:rgba(123,227,190,.1)}}.src svg{{width:14px;height:14px;flex:none}}.src.calc{{color:var(--fg2);background:rgba(255,255,255,.07)}}.src.calc svg{{display:none}}
section{{margin-top:34px}}h2{{font-size:20px;font-weight:500;margin:0 0 12px}}
.tw{{overflow-x:auto;border-radius:20px;box-shadow:inset 0 0 0 1px var(--line);background:var(--ink2)}}
table{{border-collapse:collapse;width:100%;min-width:500px;font-size:14.5px;font-variant-numeric:tabular-nums}}
th,td{{padding:11px 12px;text-align:start;border-bottom:1px solid var(--line);white-space:nowrap}}
thead th{{font-size:12.5px;font-weight:500;color:var(--muted)}}
tbody th{{font-weight:400}}tbody th b{{display:block;font-weight:500}}tbody th span{{font-size:12px;color:var(--muted)}}
tbody tr:last-child th,tbody tr:last-child td{{border-bottom:0}}
tbody tr:first-child{{background:rgba(123,227,190,.07)}}tbody tr:first-child th b{{color:var(--accent)}}
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
footer{{margin-top:44px;padding:22px 0 max(26px,env(safe-area-inset-bottom));border-top:1px solid var(--line);color:var(--muted);font-size:13px;display:flex;flex-wrap:wrap;gap:14px;justify-content:space-between}}footer a{{text-decoration:none}}
</style>
</head>
<body>
<div class="w">
<header><div class="top"><a class="brand" href="{pre}{'ar/' if rtl else ''}"><img src="{pre}icons/icon-192.png" alt="" width="32" height="32"><span>{L["home"]}</span></a><a class="lang" href="{'https://getarihna.com/prayer-times/' if rtl else 'https://getarihna.com/ar/prayer-times/'}{slug}/" hreflang="{'en' if rtl else 'ar'}">{L["other"]}</a></div></header>
<main>
<div class="hero">
<h1>{L["h1"]}</h1>
<p class="date" id="date"><b>{gshort(d0, lang)}</b> · {html.escape(hij[0])}</p>
<p class="cd" id="cd" aria-live="polite"></p>
<ul class="times" id="times">{tiles(t0)}</ul>
<span class="src{"" if OFFI[0] else " calc"}" id="srcw"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12.5l4.5 4.5L19 7.5"/></svg><span id="srct">{L["src"] if OFFI[0] else L["calc"]}</span></span>
</div>
<section aria-labelledby="wk"><h2 id="wk">{L["week"]}</h2><div class="tw"><table><thead><tr><th scope="col">{L["day"]}</th>{head_cells}</tr></thead><tbody id="wkb">{rows(0)}</tbody></table></div></section>
<section class="cards">
<div class="card"><small>{L["qibla"]}</small><b>{deg if not mecca else ("Al-Masjid al-Haram" if not rtl else "المسجد الحرام")}</b><span>{L["qline"] if not mecca else ("The Kaaba is in Makkah: face it from wherever you pray." if not rtl else "الكعبة المشرفة في مكة، فاستقبلها حيثما صليت.")}</span></div>
<div class="card"><small>{L["occ"]}</small><b id="evn">{ev0[1]}</b><span id="evd">{evline(ev0, n0)}</span></div>
</section>
<section class="app"><div><h2>{L["app"]}</h2><p>{L["applead"]}</p></div><a href="{STORE}{slug}-{lang}"><img src="{pre}img/badge-app-store.svg" alt="{L["dl"]}" width="150" height="50"></a></section>
<section aria-labelledby="fq"><h2 id="fq">{L["faq"]}</h2>
<details><summary>{L["q1"]}</summary><p>{L["a1"]}</p></details>
{"" if mecca else f'<details><summary>{L["q2"]}</summary><p>{L["a2"]}</p></details>'}</section>
<section aria-labelledby="oc"><h2 id="oc">{L["more"]}</h2><nav class="cities">{others}</nav></section>
</main>
<footer><span>{L["rights"]}</span><span><a href="{pre}privacy.html{'?lang=ar' if rtl else ''}">{L["privacy"]}</a> · <a href="{pre}support.html{'?lang=ar' if rtl else ''}">{L["support"]}</a> · {L["upd"]}</span></footer>
</div>
<script>
/* Today's times, this week and the next prayer, by the UAE clock. Runs on the page only; nothing is sent anywhere. */
(function(){{var D={J(DAYS)},E={J(evs)},N={J(NAMES[lang])},S={J({"nowin": L["nowin"], "exp": L["exp"], "today": L["today"], "tomorrow": L["tomorrow"], "indays": L["indays"], "old": L["old"], "src": L["src"], "calc": L["calc"]})},SUF={J(["AM", "PM"] if lang == "en" else ["ص", "م"])};
var f=new Intl.DateTimeFormat("en-CA",{{timeZone:"{K["zone"]}",year:"numeric",month:"2-digit",day:"2-digit",hour:"2-digit",minute:"2-digit",second:"2-digit",hourCycle:"h23"}});
function now(){{var p={{}};f.formatToParts(new Date()).forEach(function(x){{p[x.type]=x.value}});return {{d:p.year+"-"+p.month+"-"+p.day,m:(+p.hour)*60+(+p.minute)+(+p.second)/60}}}}
function hm(m){{var h=Math.floor(m/60),mi=m%60;return [(h%12||12)+":"+(mi<10?"0":"")+mi,SUF[h<12?0:1]]}}
function esc(s){{return String(s).replace(/&/g,"&amp;").replace(/</g,"&lt;")}}
var day=null;
function paint(i){{var d=D[i],li=document.querySelectorAll("#times li");document.getElementById("srct").textContent=d[4]?S.src:S.calc;document.getElementById("srcw").classList.toggle("calc",!d[4]);document.getElementById("date").innerHTML="<b>"+esc(d[1])+"</b> · "+esc(d[2]);
 [].forEach.call(li,function(x,j){{var t=hm(d[3][j]);x.querySelector("b").textContent=t[0];x.querySelector("small").textContent=t[1]}});
 var o="";for(var k=i;k<Math.min(i+7,D.length);k++){{o+='<tr><th scope="row"><b>'+esc(D[k][1])+"</b><span>"+esc(D[k][2])+"</span></th>"+D[k][3].map(function(m){{return "<td>"+hm(m)[0]+"</td>"}}).join("")+"</tr>"}}document.getElementById("wkb").innerHTML=o;
 var t0=Date.parse(d[0]+"T00:00:00Z");for(var e=0;e<E.length;e++){{var n=Math.round((Date.parse(E[e][0]+"T00:00:00Z")-t0)/864e5);if(n>=0){{document.getElementById("evn").textContent=E[e][1];
  document.getElementById("evd").textContent=E[e][2]+(E[e][3]?" · "+S.exp:"")+" · "+(n===0?S.today:n===1?S.tomorrow:S.indays.replace("{{n}}",n));break}}}}}}
function run(){{var n=now(),i=-1;for(var k=0;k<D.length;k++)if(D[k][0]===n.d){{i=k;break}}var cd=document.getElementById("cd");
 if(i<0){{if(n.d>D[D.length-1][0]&&!run.old){{run.old=1;document.querySelector(".hero").classList.add("old");cd.textContent=S.old}}return}}
 if(i!==day){{day=i;paint(i)}}var t=D[i][3],li=document.querySelectorAll("#times li"),x=-1,at=0;
 for(var j=0;j<6;j++){{if(j===1)continue;if(t[j]>n.m){{x=j;at=t[j];break}}}}
 /* after Isha: tomorrow's Fajr */
 if(x<0&&D[i+1]){{x=0;at=D[i+1][3][0]+1440}}
 [].forEach.call(li,function(e,j){{e.classList.toggle("nx",j===x&&at<1440)}});
 if(x<0){{cd.textContent="";return}}var s=Math.max(0,Math.round((at-n.m)*60)),h=Math.floor(s/3600),m=Math.floor(s%3600/60),c=h+":"+(m<10?"0":"")+m+":"+(s%60<10?"0":"")+s%60;
 cd.innerHTML=S.nowin.replace("{{p}}",N[x]).replace("{{t}}","<b>"+c+"</b>")}}
run();setInterval(run,1000)}})();
</script>
</body>
</html>
'''


def sitemap():
    pairs = [("https://getarihna.com/", "https://getarihna.com/ar/")] + [(f"https://getarihna.com/prayer-times/{s}/", f"https://getarihna.com/ar/prayer-times/{s}/") for cc in CTRY for s in CTRY[cc]["order"]]
    x = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
    for en, ar in pairs:
        for loc in (en, ar):
            x += [f"  <url><loc>{loc}</loc>", f'    <xhtml:link rel="alternate" hreflang="en" href="{en}"/>', f'    <xhtml:link rel="alternate" hreflang="ar" href="{ar}"/>', f'    <xhtml:link rel="alternate" hreflang="x-default" href="{en}"/>', "  </url>"]
    for p in ("privacy.html", "support.html"): x.append(f"  <url><loc>https://getarihna.com/{p}</loc></url>")
    x.append("</urlset>")
    open("sitemap.xml", "w").write("\n".join(x) + "\n")


n = 0
for cc in CTRY:
    for slug in CTRY[cc]["order"]:
        for lang in ("en", "ar"):
            out = f"prayer-times/{slug}/index.html" if lang == "en" else f"ar/prayer-times/{slug}/index.html"
            os.makedirs(os.path.dirname(out), exist_ok=True)
            open(out, "w", encoding="utf-8").write(page(cc, slug, lang)); n += 1
    print(cc, "days", iso(DATA[cc]["days"][0]), "to", iso(DATA[cc]["days"][-1]))
sitemap()
print("wrote", n, "city pages and sitemap.xml")
