#!/usr/bin/env python3
"""Builds the two Sheikh-Ali reports (buyer-facing + internal valuation) as RTL HTML.

Run:  python3 build.py && node pdf.js
All valuation numbers are computed here so the text and the tables cannot drift apart.
"""
import pathlib

HERE = pathlib.Path(__file__).parent

# ---------------------------------------------------------------- numbers
CU_PRICE = 14335          # USD/t, LME, 1 Oct 2026 (Trading Economics snippet)
ORE_T = 305263            # t, 3-D model reserve estimate
G_HI, G_LO = 0.0529, 0.025
USD_TOMAN = 268300        # free-market rate, morning of 13 Mehr 1405
TPY, REC, PAY, ROY, COST, TAX, DISC, CAPEX = 50000, .85, .90, .15, 100, .25, .20, 8e6


def npv(g, price, ore=ORE_T):
    rev = g * REC * PAY * price
    margin = rev - ROY * rev - COST
    yrs = ore / TPY
    cf = margin * TPY * (1 - TAX)
    af = (1 - (1 + DISC) ** -yrs) / DISC
    return cf * af - CAPEX


def fa(x, nd=0):
    """Persian digits, Persian separators."""
    if isinstance(x, (int, float)):
        s = f"{x:,.{nd}f}"
    else:
        s = str(x)
    s = s.replace(",", "٬").replace(".", "٫")
    return s.translate(str.maketrans("0123456789", "۰۱۲۳۴۵۶۷۸۹"))


cu_hi, cu_lo = ORE_T * G_HI, ORE_T * G_LO
insitu_hi, insitu_lo = cu_hi * CU_PRICE / 1e6, cu_lo * CU_PRICE / 1e6
npv_hi, npv_lo = npv(G_HI, CU_PRICE) / 1e6, npv(G_LO, CU_PRICE) / 1e6
HAIRCUT = .30
dcf_hi, dcf_lo = npv_hi * HAIRCUT, npv_lo * HAIRCUT
pct_lo, pct_hi = .01, .03
pr_hi_lo, pr_hi_hi = insitu_hi * pct_lo, insitu_hi * pct_hi
pr_lo_lo, pr_lo_hi = insitu_lo * pct_lo, insitu_lo * pct_hi
ASK, FLOOR = 7.0, 3.0
toman_b = lambda musd: musd * 1e6 * USD_TOMAN / 1e9

# ---------------------------------------------------------------- shared css
CSS = """
@page { size: A4; }
:root { --ink:#1c232b; --muted:#5d6975; --line:#cfd5dc; --head:#eef1f5; --accent:#8a4b16;
        --accent2:#1f5f6b; --warn:#fff3c4; --warnline:#e0b93a; }
html, body { background:#fff; }
body { font-family:"Vazirmatn UI FD","Vazirmatn",sans-serif; font-size:10.6pt; line-height:1.85;
       color:var(--ink); direction:rtl; text-align:justify; text-justify:inter-word; margin:0; }
.ltr { direction:ltr; unicode-bidi:isolate; font-family:"Vazirmatn",sans-serif; }
.banner { background:var(--accent); color:#fff; padding:15pt 18pt 12pt; border-radius:6pt; margin-bottom:12pt; }
.banner.alt { background:var(--accent2); }
.banner h1 { margin:0; font-size:21pt; line-height:1.5; font-weight:700; text-align:right; }
.banner .sub { font-size:11.5pt; opacity:.95; margin-top:2pt; text-align:right; }
.banner .meta { font-size:9.5pt; opacity:.9; margin-top:8pt; text-align:right; border-top:1px solid rgba(255,255,255,.4); padding-top:6pt; }
.kpis { display:grid; grid-template-columns:repeat(3,1fr); gap:7pt; margin:0 0 12pt; }
.kpi { border:1px solid var(--line); border-radius:5pt; padding:6pt 9pt; background:#fafbfc; break-inside:avoid; }
.kpi b { display:block; font-size:15pt; line-height:1.5; color:var(--accent); text-align:right; }
.kpi span { font-size:9.2pt; color:var(--muted); line-height:1.6; display:block; text-align:right; }
.kpi.alt b { color:var(--accent2); }
h2 { font-size:14pt; font-weight:700; margin:15pt 0 5pt; color:var(--accent); text-align:right; break-after:avoid;
     border-bottom:1px solid var(--line); padding-bottom:2pt; }
.alt-doc h2 { color:var(--accent2); }
h3 { font-size:11.5pt; margin:9pt 0 3pt; text-align:right; break-after:avoid; }
p { margin:0 0 7pt; }
ul { margin:0 0 7pt; padding-right:17pt; padding-left:0; }
li { margin-bottom:2.5pt; text-align:justify; }
ul.check { list-style:none; padding-right:3pt; }
ul.check li::before { content:"☐"; margin-left:6pt; font-family:"DejaVu Sans"; }
table { width:100%; border-collapse:collapse; margin:5pt 0 9pt; font-size:10pt; direction:rtl; }
tr { break-inside:avoid; }
table.keep { break-inside:avoid; }
th, td { border:1px solid var(--line); padding:3.5pt 7pt; text-align:right; vertical-align:top; line-height:1.7; }
th { background:var(--head); font-weight:700; }
td.n, th.n { text-align:center; }
.todo { background:var(--warn); border:1px dashed var(--warnline); border-radius:3pt; padding:0 4pt;
        font-size:9.2pt; color:#6b5200; white-space:nowrap; }
.callout { border-right:4px solid var(--accent); background:#fbf5ef; padding:6pt 10pt; margin:6pt 0 9pt;
           border-radius:3pt; break-inside:avoid; }
.alt-doc .callout { border-right-color:var(--accent2); background:#eef6f7; }
.callout.warn { border-right-color:var(--warnline); background:#fffaf0; }
.note { color:var(--muted); font-size:9.5pt; line-height:1.8; }
.formula { text-align:center; padding:5pt; background:#f4f5f7; border-radius:4pt; margin:4pt 0 8pt; font-size:10.5pt; }
.src li { text-align:right; font-size:9.5pt; line-height:1.75; }
a { color:#1f5fa8; text-decoration:none; }
.keep { break-inside:avoid; }
figure { margin:6pt 0 10pt; break-inside:avoid; }
figcaption { font-size:9.2pt; color:var(--muted); text-align:right; }
.pagebreak { break-before:page; }
.figpair { display:grid; grid-template-columns:1fr 1fr; gap:10pt; align-items:start; break-inside:avoid; margin:6pt 0 8pt; }
.figpair figure { margin:0; }
.fig-sm { width:62%; margin-left:auto; margin-right:auto; }
.charts { display:grid; grid-template-columns:1fr 1fr; gap:10pt; break-inside:avoid; }
.charts figure { margin:4pt 0 8pt; }
ol { margin:0 0 7pt; padding-right:19pt; padding-left:0; }
h3 { color:var(--ink); }
"""


def doc(title, body, alt=False):
    import re
    body = re.sub(r"<table>(.*?)</table>", lambda m: ("<table class=\"keep\">" if m.group(1).count("<tr") <= 8 else "<table>") + m.group(1) + "</table>", body, flags=re.S)
    return f"""<!doctype html>
<html lang="fa" dir="rtl"><head><meta charset="utf-8"><title>{title}</title>
<style>{CSS}</style></head>
<body class="{'alt-doc' if alt else ''}">
{body}
</body></html>"""


def todo(txt="تکمیل توسط مالک"):
    return f'<span class="todo">{txt}</span>'


LTR = lambda s: f'<span class="ltr">{s}</span>'

# ---------------------------------------------------------------- football field svg
def football():
    W, H = 700, 190
    x0, x1, vmax = 100, 500, 14.0
    X = lambda v: x1 - (x1 - x0) * v / vmax
    rows = [
        ("۱ تا ۳٪ ارزش فلز درجا", min(pr_lo_lo, pr_hi_lo), pr_hi_hi, "#b9855a"),
        ("۳۰٪ ارزش فعلی سود (DCF)", dcf_lo, dcf_hi, "#b9855a"),
        ("بازهٔ پیشنهادی فروش", FLOOR, ASK, "#1f5f6b"),
    ]
    out = [f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" '
           f'font-family="Vazirmatn UI FD, Vazirmatn, sans-serif" font-size="12">']
    for v in range(0, 15, 2):
        out.append(f'<line x1="{X(v):.1f}" y1="14" x2="{X(v):.1f}" y2="140" stroke="#dde2e8"/>')
        out.append(f'<text x="{X(v):.1f}" y="156" text-anchor="middle" fill="#5d6975">{fa(v)}</text>')
    out.append(f'<text x="{(x0+x1)/2:.1f}" y="178" text-anchor="middle" fill="#5d6975">میلیون دلار آمریکا</text>')
    for i, (lab, lo, hi, col) in enumerate(rows):
        y = 26 + i * 40
        out.append(f'<rect x="{X(hi):.1f}" y="{y}" width="{X(lo)-X(hi):.1f}" height="22" rx="3" fill="{col}"/>')
        out.append(f'<text x="{X(hi)-6:.1f}" y="{y+16}" text-anchor="start" fill="#1c232b">{fa(lo,1)} تا {fa(hi,1)}</text>')
        out.append(f'<text x="690" y="{y+16}" text-anchor="start" fill="#1c232b" font-weight="{700 if i==2 else 400}">{lab}</text>')
    out.append("</svg>")
    return "".join(out)


# ================================================================= DATA FROM THE EXPLORATION REPORT
BOREHOLES = [  # name, X, Y, collar elev, length
    ("BH1", "477,931.8", "3,112,400", "1902.00", "140"), ("BH2", "477,936.1", "3,112,386", "1902.17", "164"),
    ("BH3", "478,095.2", "3,112,460", "1928.35", "170"), ("BH4", "477,905.3", "3,112,416", "1896.34", "230"),
    ("BH5", "478,071", "3,112,445", "1918.04", "85"), ("BH6", "478,017", "3,112,445", "1913.43", "186"),
    ("BH7", "478,071", "3,112,460", "1916.11", "191"), ("BH8", "477,988", "3,112,440", "1915.00", "166"),
    ("BH9", "477,952", "3,112,392", "1910.00", "150"), ("BH10", "478,070.4", "3,112,389", "1928.47", "95"),
    ("BH11", "477,872", "3,112,357", "1914.00", "150"), ("BH12", "477,822.8", "3,112,560", "1887.50", "210"),
    ("BH13", "477,905.3", "3,112,296", "1903.94", "237"), ("BH14", "477,871", "3,112,348", "1915.70", "135"),
    ("BH15", "478,071", "3,112,330", "1921.71", "210"), ("BH16", "477,905.3", "3,112,452", "1904.00", "158.5"),
]
HIST = [("۰٫۶۱–۲٫۴۷", 12), ("۲٫۴۷–۴٫۳۳", 8), ("۴٫۳۳–۶٫۱۹", 6), ("۶٫۱۹–۸٫۰۵", 5), ("۸٫۰۵–۹٫۹۲", 6), ("۹٫۹۲–۱۱٫۷۸", 6)]
VARIO = [(5, 3.04, 147), (10, 7.76, 115), (15, 11.73, 72), (20, 10.14, 54), (25, 4.24, 35)]


def hist_svg():
    W, H, x0, base, hmax = 340, 205, 38, 150, 12
    bw = (W - x0 - 8) / len(HIST)
    o = [f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" direction="ltr" '
         f'font-family="Vazirmatn UI FD, Vazirmatn, sans-serif" font-size="10">']
    for v in (0, 4, 8, 12):
        y = base - v / hmax * 112
        o.append(f'<line x1="{x0}" y1="{y:.1f}" x2="{W-6}" y2="{y:.1f}" stroke="#dde2e8"/>')
        o.append(f'<text x="{x0-6}" y="{y+3:.1f}" text-anchor="end" fill="#5d6975">{fa(v)}</text>')
    for k, (lab, n) in enumerate(HIST):
        x = x0 + k * bw + 4
        h = n / hmax * 112
        o.append(f'<rect x="{x:.1f}" y="{base-h:.1f}" width="{bw-8:.1f}" height="{h:.1f}" rx="2" fill="#b9855a"/>')
        o.append(f'<text x="{x+(bw-8)/2:.1f}" y="{base-h-4:.1f}" text-anchor="middle" fill="#1c232b">{fa(n)}</text>')
        o.append(f'<text x="{x+(bw-8)/2:.1f}" y="{base+13}" text-anchor="middle" fill="#5d6975" font-size="8">{lab}</text>')
    o.append(f'<text x="{(x0+W)/2:.1f}" y="{H-8}" text-anchor="middle" fill="#5d6975">رده عیار مس (٪)</text>')
    o.append("</svg>")
    return "".join(o)


def vario_svg():
    W, H, x0, base, ymax = 340, 205, 38, 150, 14
    X = lambda d: x0 + d / 30 * (W - x0 - 10)
    Y = lambda g: base - g / ymax * 120
    o = [f'<svg viewBox="0 0 {W} {H}" width="100%" xmlns="http://www.w3.org/2000/svg" direction="ltr" '
         f'font-family="Vazirmatn UI FD, Vazirmatn, sans-serif" font-size="10">']
    for v in (0, 4, 8, 12):
        o.append(f'<line x1="{x0}" y1="{Y(v):.1f}" x2="{W-6}" y2="{Y(v):.1f}" stroke="#dde2e8"/>')
        o.append(f'<text x="{x0-6}" y="{Y(v)+3:.1f}" text-anchor="end" fill="#5d6975">{fa(v)}</text>')
    for d in (0, 5, 10, 15, 20, 25, 30):
        o.append(f'<text x="{X(d):.1f}" y="{base+14}" text-anchor="middle" fill="#5d6975">{fa(d)}</text>')
    pts = " ".join(f"{X(d):.1f},{Y(g):.1f}" for d, g, _ in VARIO)
    o.append(f'<polyline points="{pts}" fill="none" stroke="#1f5f6b" stroke-width="2"/>')
    for d, g, n in VARIO:
        o.append(f'<circle cx="{X(d):.1f}" cy="{Y(g):.1f}" r="3.5" fill="#1f5f6b"/>')
        o.append(f'<text x="{X(d):.1f}" y="{Y(g)-8:.1f}" text-anchor="middle" fill="#1c232b">{fa(g,1)}</text>')
    o.append(f'<text x="{(x0+W)/2:.1f}" y="{H-8}" text-anchor="middle" fill="#5d6975">فاصله بین نمونه‌ها (متر)</text>')
    o.append("</svg>")
    return "".join(o)


def fig(src, caption, cls=""):
    return f'<figure class="{cls}"><img src="figs/{src}" alt="" style="width:100%;display:block"><figcaption>{caption}</figcaption></figure>'


bh_rows = "".join(
    f'<tr><td>{n}</td><td class="n">{fa(x)}</td><td class="n">{fa(y)}</td><td class="n">{fa(z,2)}</td><td class="n">{fa(l)}</td></tr>'
    for n, x, y, z, l in BOREHOLES)
tot_len = 2677.5
SRC_ROW = lambda t, u: f'<li><a href="{u}">{t}</a></li>'
EXPL = "گزارش اکتشاف تفصیلی و برآورد ذخیره کانسار مس شیخ‌عالی"

# ================================================================= BUYER REPORT
buyer = f"""
<div class="banner">
  <h1>کانسار مس شیخ‌عالی</h1>
  <div class="sub">گزارش معرفی و برآورد ذخیره — برای خریدار و سرمایه‌گذار</div>
  <div class="meta">جنوب‌شرق ایران، استان هرمزگان &nbsp;|&nbsp; ۱۳ مهر ۱۴۰۵ &nbsp;|&nbsp;
  پیش‌نویس ۲ — بخش‌های زردرنگ باید توسط مالک تکمیل شود</div>
</div>

<div class="kpis">
  <div class="kpi"><b>{fa(ORE_T)} تن</b><span>ماده معدنی برآوردی (مدل بلوکی)</span></div>
  <div class="kpi"><b>۵٫۲۹٪ مس</b><span>عیار متوسط بلوک‌ها (میانگین نمونه‌ها: ۵٫۳۷٪)</span></div>
  <div class="kpi"><b>حدود {fa(16148)} تن</b><span>مس فلزی محتوا (برآورد مدل)</span></div>
  <div class="kpi alt"><b>۱۶ گمانه، {fa(2675)} متر</b><span>حفاری ۱۳۷۷ تا ۱۳۸۱ + ژئوفیزیک IP–RS</span></div>
  <div class="kpi"><b>{fa(CU_PRICE)} دلار</b><span>قیمت هر تن مس، ۹ مهر ۱۴۰۵ (حدود ۳۰٪ بالاتر از پارسال)</span></div>
  <div class="kpi alt"><b>۰٫۱۸ تا ۰٫۶۴ گرم طلا</b><span>در هر تن، ۸ نمونهٔ ماسیو مقالهٔ علمی؛ در اکتشاف تجزیه نشده</span></div>
</div>

<h2>۱. خلاصهٔ اجرایی</h2>
<p>کانسار مس شیخ‌عالی یک توده سولفیدی ماسیو از نوع VMS در جنوب‌شرق ایران است که در منابع علمی با نام {LTR('Sheikh-Ali')} شناخته می‌شود. اکتشاف تفصیلی آن بین سال‌های ۱۳۷۷ تا ۱۳۸۱ انجام شده و شامل نقشهٔ زمین‌شناسی، ژئوفیزیک IP–RS و ۱۶ گمانه است. مدل‌سازی سه‌بعدی و برآورد بلوکی در نرم‌افزار {LTR('Gemcom')} حدود <b>{fa(ORE_T)} تن ماده معدنی با عیار متوسط ۵٫۲۹٪ مس</b> و محتوای حدود <b>{fa(16148)} تن مس فلزی</b> نشان می‌دهد.</p>
<p>این عیار حدود هفت برابر عیار متوسط معدن سرچشمه (۰٫۷٪) است. مقالهٔ علمی ۲۰۰۲ بر پایهٔ نمونه‌های سطحی عیار پایین‌تری گزارش می‌کند (هشت نمونهٔ ماسیو: ۱٫۶۴ تا ۴٫۸۰٪ مس)، و طلا و نقره را هم در کانه نشان می‌دهد (۰٫۱۸ تا ۰٫۶۴ گرم طلا و ۱۰ تا ۷۵ گرم نقره در تن). یک بررسی زمین‌شناسی ایران، شیخ‌عالی را تنها نمونهٔ این نوع سولفید توده‌ای غنی از طلا در بخش جنوبی پهنهٔ سنندج–سیرجان می‌نامد. در اکتشاف تفصیلی فقط مس تجزیه شده؛ پس تفاوت عیار مس و عیار طلا و نقره باید با آنالیز تازه روشن شود.</p>
<table>
  <tr><th style="width:34%">شاخص</th><th style="width:34%">مقدار</th><th>توضیح</th></tr>
  <tr><td>نوع کانسار</td><td>سولفید توده‌ای (VMS) مرتبط با ولکانیسم</td><td>مطالعات زمین‌شناسی محدوده</td></tr>
  <tr><td>ارتفاع محدوده</td><td>حدود ۲٬۰۰۰ متر از سطح دریا</td><td></td></tr>
  <tr><td>نمونه‌های تجزیه‌شده</td><td>۴۴ نمونه از BH1، BH5، BH9 و BH11</td><td>تجزیهٔ عیار مس</td></tr>
  <tr><td>دامنهٔ عیار نمونه‌ها</td><td>۰٫۶۱ تا ۱۱٫۷۸٪ مس</td><td>میانگین ≈ ۵٫۳۷٪</td></tr>
  <tr><td>حجم توده</td><td>{fa(65648)} مترمکعب</td><td>مدل بلوکی؛ مدل سه‌بعدی: {fa(65714)}</td></tr>
  <tr><td>وزن مخصوص</td><td>۴٫۶۵ تن بر مترمکعب</td><td>متوسط ماده معدنی</td></tr>
  <tr><td>تناژ</td><td>{fa(ORE_T)} تن</td><td>{fa(65648)} × ۴٫۶۵</td></tr>
  <tr><td>محتوای فلزی</td><td>{fa(16148)} تن مس</td><td>تناژ × ۵٫۲۹٪</td></tr>
</table>
<div class="callout warn">
  <b>سه نکته برای تصمیم خریدار:</b> (۱) برآورد به چهار گمانهٔ برخوردکننده با ماده معدنی (و ۴۴ نمونه) متکی است؛ (۲) طبقه‌بندی استاندارد منابع (مانند JORC) انجام نشده؛ (۳) اطلاعات فرآوری، روش استخراج، هزینه‌ها و پروانه در گزارش اکتشاف نیست. جزئیات در بخش ۹ آمده است.
</div>

<h2>۲. موقعیت و دسترسی</h2>
<p>کانسار در استان هرمزگان و در مختصات {LTR('28°09′00″N, 56°46′20″E')} قرار دارد.</p>
<table>
  <tr><th style="width:44%">مرجع</th><th class="n">فاصلهٔ تقریبی</th><th>جهت</th></tr>
  <tr><td>کرمان</td><td class="n">{fa(300)} کیلومتر</td><td>جنوب</td></tr>
  <tr><td>بندرعباس</td><td class="n">{fa(150)} کیلومتر</td><td>شمال‌شرق</td></tr>
  <tr><td>دولت‌آباد</td><td class="n">{fa(30)} کیلومتر</td><td>جنوب‌شرق</td></tr>
  <tr><td>روستای عشایری شیخ‌عالی</td><td class="n">{fa(2)} کیلومتر</td><td>جنوب‌شرق</td></tr>
</table>
<p>مقالهٔ علمی ({LTR('Rastad et al.')}، ۲۰۰۲) موقعیت را حدود ۳۰۰ کیلومتر جنوب‌شرق کرمان، ۱۵۰ کیلومتر جنوب‌شرق بافت و ۱۳۰ کیلومتر شرق حاجی‌آباد می‌داند.</p>
<p><b>راه‌های دسترسی:</b></p>
<ol>
  <li><b>از سمت دولت‌آباد:</b> جادهٔ آسفالتهٔ بافت–دولت‌آباد (حدود ۱۳۰ کیلومتر)، سپس جادهٔ خاکی دولت‌آباد–شیخ‌عالی (حدود ۲۷ کیلومتر).</li>
  <li><b>از سمت بندرعباس:</b> جادهٔ بندرعباس–سیرجان تا سه‌راهی احمدی (کیلومتر ۷۵)، سپس بخش احمدی (حدود ۶۵ کیلومتر) و جادهٔ خاکی احمدی–شیخ‌عالی (حدود ۳۰ کیلومتر).</li>
</ol>
<p>منطقه از نظر امکانات رفاهی و صنعتی محروم است و جمعیت آن را بیشتر عشایر تشکیل می‌دهند. مختصات رئوس محدودهٔ پروانه و شهرستان طبق پروانه: {todo()}</p>
{fig('loc_map.jpg','شکل ۱ — موقعیت کانسار در ایران (نقطهٔ قرمز). منبع: گزارش اکتشاف تفصیلی','fig-sm')}
{fig('satellite.jpg','شکل ۲ — تصویر ماهواره‌ای محدودهٔ کانسار (کادر زرد: محدودهٔ اکتشافی؛ مقیاس: ۲ کیلومتر)')}

<h2>۳. زمین‌شناسی و کانه‌زایی</h2>
<p>کانسار از تیپ سولفید توده‌ای آتشفشانی است و با واحدهای ولکانیکی منطقه ارتباط مستقیم دارد. نقشهٔ توپوگرافی–زمین‌شناسی محدوده‌ای حدود ۲ کیلومترمربع تهیه شده است. در محدوده سه واحد اصلی دیده می‌شود:</p>
<table>
  <tr><th style="width:28%">واحد</th><th>شرح</th></tr>
  <tr><td>بازالت‌های اسپیلیتی</td><td>بازالت اسپیلیتی تیره، بازالت کلریتی، بازالت‌های شدیداً کلریتی‌شده و مواد هیالوکلاستیک</td></tr>
  <tr><td>آهک‌های پلاژیک</td><td>آهک پلاژیک صورتی تا قرمز و کرم‌رنگ</td></tr>
  <tr><td>رادیولاریت چرتی و شیل سیلیسی</td><td>رادیولاریت چرتی و شیل سیلیسی قرمز تا قهوه‌ای، حاوی ماده معدنی</td></tr>
</table>
<p>بخش اعظم ماده معدنی در افقی از رادیولاریت چرتی قرار دارد که با کنتاکت گدازه‌های بالشی و آهک‌های پلاژیک مرتبط است. این افق به‌صورت نواری منقطع و عدسی‌شکل در محل ترانشهٔ اصلی رخنمون دارد و ضخامتش حدود ۱۰ تا ۳۰ متر تغییر می‌کند. در نمونه‌برداری گمانه‌ها، ماده معدنی به‌صورت ماسیو، پراکنده و رگه‌ای ({LTR('stockwork')}) و نیز زون اکسیداسیون ثبت شده است. در BH5 و BH10 فواصلی با عنوان «حفره» ({LTR('Cave')}) ثبت شده است.</p>
<h3>تطبیق با پژوهش علمی منتشرشده</h3>
<p>گزارش اکتشاف با مقالهٔ راستاد، منظمی میرعلی‌پور و مؤمن‌زاده (۲۰۰۲، ژورنال علوم جمهوری اسلامی ایران، شمارهٔ ۱۳: ۵۱–۶۳) سنجیده شد. این مقاله پژوهشی دانشگاهی دربارهٔ زمین‌شناسی، کانی‌شناسی و ژئوشیمی همین کانسار است. یکی از نویسندگان آن در مقالهٔ برآورد ذخیرهٔ ۲۰۱۰ هم نام برده شده، پس استقلال کامل دو منبع قطعی نیست.</p>
<table>
  <tr><th style="width:24%">موضوع</th><th>یافتهٔ مقاله</th></tr>
  <tr><td>نوع کانسار</td><td>سولفید توده‌ای آتشفشانی‌زاد از نوع قبرس، میزبان‌شده در افیولیت؛ نویسندگان آن را به «افیولیت رسوب‌دار» ({LTR('sedimented ophiolite')}) شبیه‌تر می‌دانند، مانند کانسار {LTR('Anayatak')} ترکیه</td></tr>
  <tr><td>سنگ میزبان</td><td>گدازهٔ بالشی بازالتی، دیاباز، آهک پلاژیک (کرتاسهٔ بالایی، ماستریشتین)، چرت رادیولاریتی، ماسه‌سنگ آهکی و گریواک؛ بازالت‌ها از نوع {LTR('E-MORB')} تولئیتی</td></tr>
  <tr><td>شکل ماده معدنی</td><td>عدسی‌های ناپیوستهٔ سولفید ماسیو هم‌شیب با لایه‌بندی آهک پلاژیک؛ افق سیلیسی حدود ۵۵۰ متر طول</td></tr>
  <tr><td>کانی‌شناسی</td><td>پیریت و کالکوپیریت (اصلی)، اسفالریت (فرعی)، اسپکولاریت؛ کوولیت، دیژنیت، بورنیت و مس طبیعی در زون برونزاد؛ در سطح گوتیت، مالاکیت و آزوریت. بافت: ماسیو، لایه‌ای و کلوفرم</td></tr>
  <tr><td>دگرسانی و ژئوشیمی</td><td>دگرسانی کلریتی و پروپیلیتی (سریسیتی کم)؛ همبستگی بسیار خوب Cu و Zn؛ نسبت {LTR('Cu/(Cu+Zn)')} در نمونه‌های ماسیو ۰٫۷۶ تا ۱٫۰۰ است، یعنی مس فلز اصلی است</td></tr>
  <tr><td>معدنکاری باستانی</td><td>سرباره‌های مس نشانهٔ استخراج باستانی در محدودهٔ شیخ‌عالی و احمدآباد است (امامی و پرورش، ۲۰۱۶)</td></tr>
</table>
<p><b>نمونه‌های سطحی و برش‌های لیتوژئوشیمیایی (جدول ۲ مقاله):</b></p>
<table>
  <tr><th>نوع نمونه</th><th class="n">تعداد</th><th class="n">مس</th><th class="n">طلا (ppb)</th><th class="n">نقره (ppm)</th></tr>
  <tr><td>ماده معدنی ماسیو</td><td class="n">۸</td><td class="n">۱٫۶۴ تا ۴٫۸۰٪</td><td class="n">۱۸۰ تا ۶۴۰</td><td class="n">۱۰ تا ۷۵</td></tr>
  <tr><td>ماده معدنی پراکنده</td><td class="n">۵</td><td class="n">۰٫۱۷ تا ۰٫۸۵٪</td><td class="n">۱۲۲ تا ۳۰۱</td><td class="n">۹ تا ۲۵</td></tr>
  <tr><td>بازالت میزبان</td><td class="n">۷</td><td class="n">۱۷۲ تا ۵۷۸ ppm</td><td class="n">۸ تا ۷۲</td><td class="n">۲ تا ۵</td></tr>
</table>
<p>عیار نمونه‌های حفاری (تا ۱۱٫۷۸٪ مس) بسیار بالاتر از نمونه‌های سطحی این مقاله است. احتمالاً مقاله بر نمونه‌های سطحی و برش‌های لیتوژئوشیمیایی و گزارش اکتشاف بر مغزهٔ حفاری تکیه دارد، ولی این توجیه تأیید نشده و تیم اکتشاف باید دو مجموعه را با هم تطبیق دهد. طلا و نقره در ماده معدنی ماسیو حضور دارند اما نمونه‌ها برای ارزش‌گذاری کافی نیستند و در برآورد ذخیره نیامده‌اند. آنالیز <span class="ltr">USGS</span> پتانسیل پالادیم، پلاتین و رودیم را پایین ارزیابی کرده است.</p>
<p><b>پتانسیل اکتشافی نزدیک (فقط نشانه، نه ذخیره):</b> مقاله از چند رخداد دیگر در همین مجموعهٔ افیولیتی نام می‌برد: معدن متروک احمدآباد و نشانه‌های مس بقچنار، ماهستان، دهانه‌کوجین و رزدار. این‌ها در گزارش اکتشاف بررسی نشده‌اند.</p>
<div class="figpair">
  {fig('rastad_fig3_geologic_map.jpg','شکل ۳ — نقشهٔ زمین‌شناسی کانسار؛ افق کانه‌دار سیلیسی (ماسیو سولفید) سیاه است. منبع: راستاد و همکاران (۲۰۰۲)، شکل ۳')}
  {fig('rastad_fig4_section.jpg','شکل ۴ — برش عمومی واحدهای سنگی و جایگاه افق کانه‌دار سیلیسی. منبع: راستاد و همکاران (۲۰۰۲)، شکل ۴')}
</div>
<div class="figpair">
  {fig('rastad_fig11_ore_samples.jpg','شکل ۵ — نمونهٔ دستی: الف) کانی‌های ماسیو (پیریت و کالکوپیریت)؛ ب) افق سیلیسی غنی از سولفید با کالکوپیریت لایه‌ای و سیلیس. منبع: راستاد و همکاران (۲۰۰۲)، شکل ۱۱')}
  {fig('rastad_fig14_paragenesis.jpg','شکل ۶ — ترتیب پاراژنتیک کانی‌ها در افق سیلیسی (نهشت، دیاژنز و دگرسانی برونزاد). منبع: راستاد و همکاران (۲۰۰۲)، شکل ۱۴')}
</div>

<h2>۴. عملیات اکتشافی و داده‌های حفاری</h2>
<p>اکتشاف تفصیلی بین سال‌های ۱۳۷۷ تا ۱۳۸۱ سه بخش داشت: تهیهٔ نقشهٔ توپوگرافی–زمین‌شناسی (حدود ۲ کیلومترمربع)، اکتشاف سطحی برای شناخت گسترش ماده معدنی سولفیدی در عمق، و برداشت ژئوفیزیک IP–RS. بر پایهٔ تلفیق این نتایج، ۱۶ گمانه با طول کل حدود {fa(2675)} متر حفاری شد. گمانه‌ها عمدتاً شیب‌دار (۷۰ تا ۸۷ درجه) هستند.</p>
{fig('bh_plan.jpg','شکل ۷ — موقعیت گمانه‌های حفرشده (پلان). مختصات UTM بر حسب متر','fig-sm')}
<table>
  <tr><th>گمانه</th><th class="n">X (شرقی)</th><th class="n">Y (شمالی)</th><th class="n">ارتفاع دهانه (م)</th><th class="n">طول (م)</th></tr>
  {bh_rows}
</table>
<p>ماده معدنی در چهار گمانه نمونه‌برداری و از نظر مس تجزیه شده است. طول‌های زیر طول نمونه‌برداری در امتداد گمانه است، نه ضخامت واقعی.</p>
<table>
  <tr><th>گمانه</th><th>بازهٔ ماده معدنی در گمانه (م)</th><th class="n">طول نمونه‌برداری‌شده (م)</th><th class="n">تعداد نمونه</th></tr>
  <tr><td>BH1</td><td>۶۹ تا ۹۹</td><td class="n">حدود ۳۰</td><td class="n">۲۸</td></tr>
  <tr><td>BH5</td><td>۶۰ تا ۶۲</td><td class="n">۲</td><td class="n">۱</td></tr>
  <tr><td>BH9</td><td>حدود ۷۳٫۵ تا ۸۳٫۵</td><td class="n">حدود ۱۰</td><td class="n">۱۰</td></tr>
  <tr><td>BH11</td><td>۳۲ تا ۳۷</td><td class="n">۵</td><td class="n">۵</td></tr>
  <tr><th>جمع</th><th></th><th></th><th class="n">۴۴</th></tr>
</table>
<p>داده‌ها (دهانه، پیمایش، لیتولوژی و عیار) در چهار فایل ساختاریافته وارد {LTR('Gemcom')} شده است. نتیجهٔ ۱۲ گمانهٔ دیگر (برخورد یا عدم برخورد با ماده معدنی) در گزارش اکتشاف صریحاً ذکر نشده و باید روشن شود.</p>
{fig('bh_3d.jpg','شکل ۸ — موقعیت فضایی گمانه‌ها (بخش قرمز: ماده معدنی). راست: همهٔ گمانه‌ها؛ چپ: گمانه‌های برخوردکننده با ماده معدنی')}

<h2>۵. مدل‌سازی و برآورد ذخیره</h2>
<p>مدل سه‌بعدی توده از یک پلان افقی (نقشهٔ زمین‌شناسی سطحی) و یک مقطع شیب‌دار از گمانه‌های BH1، BH9 و BH11 ساخته شده است؛ نتیجه جسمی کاسه‌ای‌شکل است که از سطح به عمق می‌رود. مراحل: ساخت مدل توپوگرافی (شبکهٔ مثلثی نامنظم)، مدل‌سازی گمانه‌ها و لیتولوژی، ترسیم پلان و مقطع، و اتصال مقاطع برای ساخت مدل سه‌بعدی.</p>
{fig('plan.jpg','شکل ۹ — پلان افقی ماده معدنی بر اساس نقشهٔ زمین‌شناسی سطحی','fig-sm')}
{fig('model3d.jpg','شکل ۱۰ — مدل سه‌بعدی هندسی کانسار؛ راست: Wireframe، چپ: مدل جامد')}
<table>
  <tr><th style="width:55%">مشخصهٔ مدل</th><th>مقدار</th></tr>
  <tr><td>حجم مدل سه‌بعدی</td><td>{fa(65713.835,0)} مترمکعب</td></tr>
  <tr><td>مساحت سطح</td><td>{fa(29445.789,0)} مترمربع</td></tr>
  <tr><td>گره‌ها / لبه‌ها / مثلث‌ها</td><td>{fa(164)} / {fa(486)} / {fa(324)}</td></tr>
  <tr><td>تناژ از حجم مدل سه‌بعدی</td><td>≈ {fa(305565)} تن</td></tr>
</table>
<p>برای برآورد عیار، توده به بلوک‌های ۱×۱×۱ متری تقسیم و عیار هر بلوک با روش عکس مجذور فاصله (توان ۲) تخمین زده شد. روش زمین‌آماری به این دلیل کنار گذاشته شد که تغییرنما ساختار فضایی نشان نداد (بخش ۶).</p>
<table>
  <tr><th style="width:42%">پارامتر</th><th>مقدار</th></tr>
  <tr><td>فضای تخمین</td><td>۱۹۰ ستون، ۱۲۰ ردیف، ۱۳۰ تراز (مبدأ: X=۴۷۷٬۸۳۵، Y=۳٬۱۱۲٬۳۳۹، Z=۱٬۹۲۰)</td></tr>
  <tr><td>حداقل / حداکثر نمونهٔ مؤثر در هر بلوک</td><td>۲ / ۱۲</td></tr>
  <tr><td>بیضی جستجو</td><td>بدون چرخش، شعاع نامحدود (۹٬۹۹۹)</td></tr>
</table>
<table>
  <tr><th style="width:55%">نتیجهٔ برآورد</th><th>مقدار</th></tr>
  <tr><td>تعداد بلوک (هر بلوک ۱ مترمکعب)</td><td>{fa(65648)}، همه تخمین‌خورده</td></tr>
  <tr><td>تناژ = {fa(65648)} × ۴٫۶۵</td><td><b>{fa(ORE_T)} تن</b></td></tr>
  <tr><td>عیار متوسط بلوک‌ها</td><td><b>۵٫۲۹٪ مس</b> (میانگین نمونه‌ها ۵٫۳۷٪)</td></tr>
  <tr><td>محتوای فلزی = {fa(ORE_T)} × ۵٫۲۹٪</td><td><b>{fa(16148)} تن مس</b></td></tr>
</table>
{fig('blockmodel.jpg','شکل ۱۱ — بلوک‌بندی کانسار و رنگ‌بندی بلوک‌ها بر اساس عیار مس (BH11 در چپ، BH9 در راست)')}
<p><b>اعتبارسنجی متقابل:</b> برای تنظیم پارامترها (شعاع، حداقل و حداکثر نمونه) آزمون اعتبار متقابل روی ۴۴ نمونه انجام شد. میانگین عیار برآوردشده در محل نمونه‌ها ۵٫۳۵٪ است و با میانگین واقعی (۵٫۳۷٪) نزدیک است؛ یعنی مدل میانگین را بیش یا کم برآورد نمی‌کند. این آزمون درستی توزیع عیار در مناطق بدون حفاری را تضمین نمی‌کند.</p>

<h2>۶. مطالعات آماری</h2>
<p>عیار مس نمونه‌ها از ۰٫۶۱ تا ۱۱٫۷۸٪ تغییر می‌کند و میانگین آن ۵٫۳۸٪ است. ضریب تغییرات ۰٫۶۳ تغییرپذیری متوسط را نشان می‌دهد. حدود ۴۶٫۵٪ نمونه‌ها زیر ۴٫۳۳٪ و ۷۲٪ زیر ۸٫۰۵٪ مس هستند.</p>
<table>
  <tr><th>پارامتر</th><th class="n">تعداد</th><th class="n">کمینه</th><th class="n">بیشینه</th><th class="n">میانگین</th><th class="n">انحراف معیار</th><th class="n">ضریب تغییرات</th><th class="n">چولگی</th><th class="n">کشیدگی</th></tr>
  <tr><td>عیار مس (٪)</td><td class="n">۴۳</td><td class="n">۰٫۶۱</td><td class="n">۱۱٫۷۸</td><td class="n">۵٫۳۸</td><td class="n">۳٫۴۱</td><td class="n">۰٫۶۳</td><td class="n">۰٫۲۷</td><td class="n">۱٫۶۵</td></tr>
</table>
<div class="charts">
  <figure>{hist_svg()}<figcaption>شکل ۱۲ — توزیع فراوانی عیار مس نمونه‌ها (۴۳ نمونه)</figcaption></figure>
  <figure>{vario_svg()}<figcaption>شکل ۱۳ — نیم‌تغییرنمای عیار مس (گام ۵ متر)</figcaption></figure>
</div>
<p>تغییرنما در همهٔ جهت‌ها مشابه است، پس ذخیره همسانگرد فرض شده است. اما پس از اوج حدود ۱۱٫۷ در فاصلهٔ ۱۰ تا ۱۵ متر دوباره کاهش می‌یابد و به حد ثابتی نمی‌رسد. گزارش اکتشاف نتیجه می‌گیرد ساختار فضایی قابل‌اتکایی دیده نمی‌شود و کریجینگ مناسب نیست. باید توجه داشت که ۲۸ نمونه از ۴۴ نمونه از یک گمانه (BH1) است و جفت‌های نزدیک بیشتر از درون همان گمانه می‌آیند.</p>

<h2>۷. تحلیل حساسیت</h2>
<p><b>شعاع جستجو:</b> با کوچک‌تر شدن شعاع، بلوک‌های کمتری تخمین می‌خورند. در شعاع ۵۰ متر فقط حدود نیمی از حجم مدل شرط حداقل دو نمونه را دارد و عیار متوسط این بخش بالاتر است (۸٫۵۷٪). یعنی بخش بزرگی از مدل با فاصلهٔ زیاد از نمونه‌ها و به‌صورت برون‌یابی تخمین زده شده است.</p>
<table>
  <tr><th>شعاع جستجو</th><th class="n">حجم بلوک‌های تخمین‌خورده (م³)</th><th class="n">سهم از کل مدل</th><th class="n">عیار متوسط (٪ Cu)</th></tr>
  <tr><td>۵۰ متر</td><td class="n">{fa(32702)}</td><td class="n">۴۹٫۸٪</td><td class="n">۸٫۵۷</td></tr>
  <tr><td>۱۰۰ متر</td><td class="n">{fa(61060)}</td><td class="n">۹۳٫۰٪</td><td class="n">نیاز به بازمحاسبه</td></tr>
  <tr><td>بدون محدودیت</td><td class="n">{fa(65648)}</td><td class="n">۱۰۰٪</td><td class="n">۵٫۲۹</td></tr>
</table>
<p><b>عیار حد:</b> میانگین عیار بلوک‌ها با بالا رفتن عیار حد از ۵٫۲۹٪ (حد ۰٫۵٪) به ۱۰٫۶۱٪ (حد ۱۰٪) می‌رسد. جدول تناژ–عیار صحیح (تناژ باقی‌مانده بالاتر از هر عیار حد) در گزارش اکتشاف نیست؛ محتوای فلزی ارائه‌شده در آن از ضرب کل تناژ در عیار هر رده به دست آمده و درست نیست. این جدول باید از مدل بلوکی بازمحاسبه شود و در اینجا ارائه نشده است.</p>

<h2>۸. وضعیت حقوقی، زیرساخت و بازار</h2>
<p>طبق قانون معادن، پروانهٔ بهره‌برداری قابل معامله، تمدید و توثیق است. موارد زیر باید از اسناد مالک تکمیل و در اتاق داده ارائه شود.</p>
<table>
  <tr><th style="width:55%">مورد</th><th>وضعیت</th></tr>
  <tr><td>نوع مجوز، شماره و تاریخ صدور / انقضا</td><td>{todo()}</td></tr>
  <tr><td>ظرفیت استخراج مجاز (تن در سال)</td><td>{todo()}</td></tr>
  <tr><td>حقوق دولتی و بدهی معوق</td><td>{todo()}</td></tr>
  <tr><td>مجوز محیط‌زیست و منابع طبیعی؛ استعلام میراث فرهنگی</td><td>{todo()}</td></tr>
  <tr><td>برق (شبکه / ژنراتور)؛ آب (منبع و مجوز)</td><td>{todo()}</td></tr>
  <tr><td>ماشین‌آلات، ابنیه (کمپ، انبار، دفتر)</td><td>{todo()}</td></tr>
  <tr><td>روش استخراج (روباز / زیرزمینی)</td><td>{todo()}</td></tr>
</table>
<p>حقوق دولتی درصدی از بهای فروش مادهٔ معدنی است؛ برای ۱۴۰۴ نرخ ۱۵٪ تعیین شد و برای شش ماه نخست ۱۴۰۵ بر پایهٔ استخراج واقعی محاسبه می‌شود.</p>
<p><b>بازار:</b> محصول، سنگ سولفیدی مس است و خریداران طبیعی آن کارخانه‌های فلوتاسیون و تغلیظ مس استان کرمان هستند. قیمت مس در بورس فلزات لندن در ۹ مهر ۱۴۰۵ حدود {fa(CU_PRICE)} دلار در تن بود؛ حدود ۳۰٪ بالاتر از یک سال قبل ({LTR('Trading Economics')}).</p>

<h2>۹. نقاط قوت، محدودیت‌ها و ریسک‌ها</h2>
<h3>نقاط قوت</h3>
<ul>
  <li>عیار متوسط بالا (۵٫۳٪ مس) و وزن مخصوص ۴٫۶۵ نشان‌دهندهٔ ماده معدنی سولفیدی ماسیو است.</li>
  <li>مدل سه‌بعدی، مدل بلوکی و آزمون اعتبار متقابل آماده است.</li>
  <li>دسترسی جاده‌ای از دو مسیر و داده‌های اکتشافی منظم (نقشه، ژئوفیزیک، ۱۶ گمانه) موجود است.</li>
  <li>مقالهٔ علمی مستقل‌تری (۲۰۰۲) نوع کانسار، میزبان و حضور طلا و نقره را تأیید می‌کند (عیار طلا و نقره باید با آنالیز تأیید شود).</li>
  <li>نشانه‌های مس در رخدادهای نزدیک (احمدآباد، بقچنار، ماهستان و ...) پتانسیل اکتشافی برای خریدار است.</li>
</ul>
<h3>محدودیت‌ها و راه کاهش آن‌ها</h3>
<table>
  <tr><th style="width:34%">محدودیت</th><th>راه کاهش / اقدام</th></tr>
  <tr><td>پایهٔ داده: ۴۴ نمونه از چهار گمانه؛ ۲۸ نمونه از BH1؛ نتیجهٔ ۱۲ گمانهٔ دیگر ذکر نشده</td><td>مستندسازی نتیجهٔ همهٔ گمانه‌ها؛ حفاری تکمیلی برای کاهش فاصلهٔ نمونه‌ها</td></tr>
  <tr><td>برآورد با کد استاندارد (JORC، PERC و مانند آن) طبقه‌بندی نشده</td><td>طبقه‌بندی منابع توسط شخص صالح</td></tr>
  <tr><td>تغییرنما ساختار نشان نمی‌دهد؛ شعاع جستجو نامحدود؛ حدود نیمی از مدل برون‌یابی است</td><td>بازبرآورد با شعاع محدود؛ اعتبار برآورد برای کل توده سنجیده شود نه هر بلوک</td></tr>
  <tr><td>جدول تناژ–عیار با عیار حد اقتصادی ندارد</td><td>بازمحاسبه از مدل بلوکی</td></tr>
  <tr><td>وزن مخصوص ۴٫۶۵ بدون ذکر روش اندازه‌گیری</td><td>اندازه‌گیری مستقل و کنترل کیفیت نمونه‌برداری و تجزیه</td></tr>
  <tr><td>داده‌ها قدیمی است (حفاری ۱۳۷۷ تا ۱۳۸۱)</td><td>نمونه‌برداری و آنالیز تازه</td></tr>
  <tr><td>«حفره» در BH5 و BH10</td><td>بررسی بازیابی نمونه و زمین‌شناسی مهندسی</td></tr>
  <tr><td>فرآوری، روش استخراج، هزینه و پروانه در گزارش اکتشاف نیست</td><td>آزمایش فرآوری؛ مطالعات امکان‌سنجی؛ ارائهٔ پروانه</td></tr>
  <tr><td>عیار مس گمانه‌ها (تا ۱۱٫۷۸٪) بسیار بالاتر از نمونه‌های سطحی مقالهٔ علمی (۱٫۶۴ تا ۴٫۸٪)</td><td>تطبیق دو مجموعه با نمونه‌برداری مستقل از سطح و مغزه</td></tr>
  <tr><td>طلا و نقره در اکتشاف تجزیه نشده (فقط ۸ نمونهٔ مقاله)</td><td>آنالیز طلا، نقره و روی روی مغزه‌ها</td></tr>
  <tr><td>میراث فرهنگی (آثار معدنکاری باستانی)</td><td>استعلام رسمی و مستندسازی آثار</td></tr>
  <tr><td>زهاب اسیدی از کانهٔ پرپیریت؛ نوسان قیمت مس و ارز</td><td>طرح مدیریت پساب؛ ارزش‌گذاری با چند سناریو</td></tr>
</table>

<h2>۱۰. اتاق داده و گام‌های بعدی</h2>
<p>جدول کامل نتایج تجزیهٔ ۴۴ نمونه، لاگ لیتولوژی گمانه‌ها و جدول پیمایش (شیب و آزیموت) در گزارش اکتشاف موجود است و پس از امضای تعهد محرمانگی به خریدار داده می‌شود.</p>
<ul class="check">
  <li>گزارش اکتشاف تفصیلی و برآورد ذخیره (فایل ۴۸ صفحه‌ای) و داده‌های Gemcom</li>
  <li>جدول نتایج تجزیه، لاگ گمانه‌ها و پیمایش گمانه‌ها</li>
  <li>تصویر پروانهٔ بهره‌برداری، نقشهٔ محدوده و طرح بهره‌برداری مصوب</li>
  <li>مفاصاحساب حقوق دولتی و بیمه؛ فهرست تجهیزات با عکس</li>
  <li>نتایج آنالیز تازهٔ نمونه‌ها (مس، طلا، نقره، روی) در آزمایشگاه معتبر</li>
  <li>مدرک مجوز بازنشر شکل‌های مقالهٔ راستاد و همکاران (۲۰۰۲)</li>
</ul>
<p><b>تماس:</b> {todo('نام و شمارهٔ تماس فروشنده')}</p>

<h2>۱۱. مأخذ داده‌ها و منابع</h2>
<p class="note">همهٔ ارقام مربوط به اکتشاف و برآورد ذخیره از «{EXPL}» (فایل ارائهٔ ۴۸ صفحه‌ای) گرفته شده و مستقلاً با داده خام آزمایشگاهی یا خروجی نرم‌افزار تطبیق داده نشده است. شکل‌های ۱، ۲ و ۷ تا ۱۱ از همان گزارش برش خورده‌اند، شکل‌های ۳ تا ۶ با مجوز از مقالهٔ راستاد و همکاران (۲۰۰۲) نقل شده‌اند و شکل‌های ۱۲ و ۱۳ از جدول‌های گزارش اکتشاف دوباره رسم شده‌اند. اطلاعات تکمیلی از چکیدهٔ منابع زیر در نتایج جست‌وجو آمده؛ متن کامل بیشتر آن‌ها باز نشد.</p>
<ul class="src">
  <li>{EXPL} (۱۳۷۷–۱۳۸۱)، فایل ارائهٔ ۴۸ صفحه‌ای، محدودهٔ بهره‌برداری مس شیخ‌عالی — منبع اصلی</li>
  {SRC_ROW('Rastad, Monazami Miralipour &amp; Momenzadeh (2002). Sheikh-Ali Copper Deposit, a Cyprus-Type VMS Deposit in Southeast Iran. Journal of Sciences, Islamic Republic of Iran, 13(1), 51–63','https://www.researchgate.net/publication/228463812_Sheikh-Ali_Copper_Deposit_a_Cyprus-Type_VMS_Deposit_in_Southeast_Iran')}
  {SRC_ROW('3D Modeling and preliminary ore reserve estimation of Sheikh-Ali Copper deposit','https://www.academia.edu/12113978/3D_Modeling_and_preliminary_ore_reserve_estimation_of_Sheikh_Ali_Copper_deposit')}
  {SRC_ROW('Metallogeny of volcanogenic massive sulfide deposits of Iran (ScienceDirect)','https://www.sciencedirect.com/science/article/abs/pii/S016913681730495X')}
  {SRC_ROW('پایان‌نامهٔ اکتشاف تکمیلی ژئوشیمیایی و ژئوفیزیکی کانسار مس شیخ‌علی — دانشگاه صنعتی اصفهان','https://thesis.iut.ac.ir/complementary-geochemical-and-geophysical-exploration-sheikh-ali-copper-deposit-order-design')}
  {SRC_ROW('USGS Open-File Report 79-840 — Pd, Pt and Rh in mafic and ultramafic rocks of Turkey and Iran','https://pubs.usgs.gov/publication/ofr79840')}
  <li>Emami &amp; Parvaresh (2016). Copper slags from Sheikh-Ali ophiolite copper deposits, Kerman. Archäometrie und Denkmalpflege 2016, Göttingen, pp. 205–208 (از خلاصهٔ نتایج جست‌وجو؛ پیوند مستقیم تأیید نشد)</li>
  {SRC_ROW('Trading Economics — Copper','https://tradingeconomics.com/commodity/copper')}
  {SRC_ROW('حقوق دولتی معادن ۱۵ درصد — انتخاب','https://www.entekhab.ir/fa/news/834576/')}
  {SRC_ROW('محاسبهٔ حقوق دولتی بر مبنای استخراج واقعی — فلزات خاورمیانه','https://felezatkhavarmianeh.ir/fa/news/404062/')}
  {SRC_ROW('تشریح فعالیت‌های معدن مس سرچشمه — اخبار معدن','https://www.akhbaremadan.ir/news/1007/')}
</ul>
"""

# ================================================================= INTERNAL VALUATION
sens_rows = ""
for g, lab in ((.025, "۲٫۵٪"), (.035, "۳٫۵٪"), (.0529, "۵٫۲۹٪")):
    cells = "".join(
        f'<td class="n">{fa(max(npv(g, p), 0) * HAIRCUT / 1e6, 1)}</td>' for p in (11000, CU_PRICE, 17000)
    )
    sens_rows += f"<tr><td>{lab}</td>{cells}</tr>"

internal = f"""
<div class="banner alt">
  <h1>ارزش‌گذاری و راهبرد فروش کانسار مس شیخ‌عالی</h1>
  <div class="sub">سند داخلی فروشنده — برای خریدار ارسال نشود</div>
  <div class="meta">۱۳ مهر ۱۴۰۵ &nbsp;|&nbsp; دلار آزاد صبح ۱۳ مهر ۱۴۰۵: {fa(USD_TOMAN)} تومان &nbsp;|&nbsp; مس: {fa(CU_PRICE)} دلار در تن</div>
</div>

<div class="kpis">
  <div class="kpi alt"><b>{fa(ASK,0)} میلیون دلار</b><span>قیمت اولیهٔ پیشنهادی ≈ {fa(toman_b(ASK))} میلیارد تومان</span></div>
  <div class="kpi alt"><b>{fa(FLOOR,0)} میلیون دلار</b><span>کف مذاکره ≈ {fa(toman_b(FLOOR))} میلیارد تومان</span></div>
  <div class="kpi"><b>{fa(insitu_lo)} تا {fa(insitu_hi)} میلیون دلار</b><span>ارزش مس درجا (سقف نظری، نه قیمت معدن)</span></div>
</div>

<h2>۱. جمع‌بندی</h2>
<p>با اطلاعات فعلی، قیمت منطقی فروش بین <b>{fa(FLOOR,0)} تا {fa(ASK,0)} میلیون دلار</b> است. این بازه از دو روش مستقل و یک مقایسهٔ بازار به دست آمد و جایگزین ارزیابی کارشناس رسمی نیست. مهم‌ترین عامل قیمت <b>اعتبار عیار ۵٫۲۹٪</b> است. گزارش اکتشاف این عیار را از ۴۴ نمونهٔ چهار گمانه (۲۸ نمونه از یک گمانه) و با شعاع جستجوی نامحدود به دست آورده؛ مقالهٔ علمی میانگین کانهٔ توده‌ای را ۲٫۵٪ می‌داند. اگر آنالیز تازه عیار ۵٪ را تأیید کند، بالای بازه قابل دفاع می‌شود؛ اگر نزدیک ۲٫۵٪ باشد، قیمت به پایین بازه یا کمتر می‌رسد.</p>

<h2>۲. داده‌های گزارش اکتشاف و اثر آن‌ها بر قیمت</h2>
<table>
  <tr><th style="width:50%">به نفع قیمت</th><th>به ضرر قیمت</th></tr>
  <tr>
    <td>گزارش اکتشاف تفصیلی با ۱۶ گمانه، ژئوفیزیک، مدل سه‌بعدی و بلوکی و اعتبارسنجی متقابل دارد؛ خریدار داده‌های منظم می‌بیند.<br>میانگین برآوردی مدل (۵٫۳۵٪) با میانگین نمونه‌ها (۵٫۳۷٪) نزدیک است.<br>مقالهٔ علمی ۲۰۰۲ نوع کانسار، میزبان و حضور طلا و نقره را تأیید می‌کند.</td>
    <td>فقط ۴ گمانه ماده معدنی دارند و ۲۸ از ۴۴ نمونه از BH1 است؛ نتیجهٔ ۱۲ گمانهٔ دیگر ذکر نشده.<br>تغییرنما ساختار ندارد، شعاع نامحدود است و حدود نیمی از مدل برون‌یابی است (در شعاع ۵۰ متر فقط ۴۹٫۸٪).<br>طبقه‌بندی JORC ندارد؛ جدول عیار حد غلط است؛ فرآوری، هزینه و پروانه در دست نیست؛ داده‌ها از ۱۳۷۷ تا ۱۳۸۱ است.</td>
  </tr>
</table>

<h2>۳. روش‌ها و فرض‌ها</h2>
<h3>روش الف: درصدی از ارزش مس درجا</h3>
<p>ارزش مس درجا = ذخیره × عیار × قیمت مس. معدن کوچک با ذخیرهٔ غیرقطعی معمولاً ۱ تا ۳٪ این ارزش فروخته می‌شود. <span class="note">(این نسبت تقریبی و برآورد خود ماست؛ منبع منتشرشده ندارد.)</span></p>
<table>
  <tr><th>سناریو</th><th class="n">مس محتوا (تن)</th><th class="n">ارزش درجا (میلیون دلار)</th><th class="n">۱٪ تا ۳٪ آن (میلیون دلار)</th></tr>
  <tr><td>عیار ۵٫۲۹٪ (مدل بلوکی)</td><td class="n">{fa(cu_hi)}</td><td class="n">{fa(insitu_hi)}</td><td class="n">{fa(pr_hi_lo,1)} تا {fa(pr_hi_hi,1)}</td></tr>
  <tr><td>عیار ۲٫۵٪ (چکیدهٔ مقالهٔ علمی)</td><td class="n">{fa(cu_lo)}</td><td class="n">{fa(insitu_lo)}</td><td class="n">{fa(pr_lo_lo,1)} تا {fa(pr_lo_hi,1)}</td></tr>
</table>
<h3>روش ب: ارزش فعلی سودهای آینده (DCF ساده)</h3>
<table>
  <tr><th style="width:42%">فرض</th><th>مقدار</th></tr>
  <tr><td>ظرفیت استخراج</td><td>{fa(TPY)} تن در سال؛ عمر معدن حدود {fa(ORE_T/TPY,1)} سال</td></tr>
  <tr><td>بازیابی فرآوری / درصد قابل پرداخت مس</td><td>{fa(REC*100)}٪ / {fa(PAY*100)}٪</td></tr>
  <tr><td>هزینهٔ استخراج و فرآوری</td><td>{fa(COST)} دلار در هر تن سنگ</td></tr>
  <tr><td>حقوق دولتی / مالیات</td><td>{fa(ROY*100)}٪ درآمد / {fa(TAX*100)}٪ سود</td></tr>
  <tr><td>سرمایهٔ اولیه / نرخ تنزیل</td><td>{fa(CAPEX/1e6)} میلیون دلار / {fa(DISC*100)}٪</td></tr>
  <tr><td>طلا و نقره</td><td>در محاسبه نیامده (در اکتشاف تجزیه نشده)</td></tr>
</table>
<p>اگر میانگین جدول ۲ مقاله (حدود ۳٫۷٪، بخش ۸) درست باشد، سناریوی میانی ۳٫۵٪ در جدول حساسیت (بخش ۵) به آن نزدیک است.</p>
<p>نتیجه: ارزش فعلی خالص حدود {fa(npv_hi,1)} میلیون دلار (عیار ۵٫۲۹٪) و {fa(npv_lo,1)} میلیون دلار (عیار ۲٫۵٪). چون ذخیره طبقه‌بندی‌نشده است و پروانه و دسترسی روشن نیست، خریدار این عدد را تخفیف می‌دهد. ما {fa(HAIRCUT*100)}٪ آن را گرفتیم: {fa(dcf_hi,1)} و {fa(dcf_lo,1)} میلیون دلار. <span class="note">(ضریب {fa(HAIRCUT*100)}٪ فرض ماست.)</span></p>

<h2>۴. بازهٔ ارزش</h2>
<figure>{football()}
<figcaption>نمودار ۱. بازهٔ ارزش به میلیون دلار؛ دو میلهٔ بالا از محاسبهٔ بالا، میلهٔ پایین بازهٔ پیشنهادی است.</figcaption></figure>

<h2>۵. حساسیت به عیار و قیمت مس</h2>
<p>ارزش پیشنهادی (میلیون دلار) = {fa(HAIRCUT*100)}٪ ارزش فعلی خالص، با فرض‌های بخش ۳:</p>
<table>
  <tr><th>عیار مس</th><th class="n">مس ۱۱٬۰۰۰ دلار</th><th class="n">مس {fa(CU_PRICE)} دلار (فعلی)</th><th class="n">مس ۱۷٬۰۰۰ دلار</th></tr>
  {sens_rows}
</table>
<p>قیمت مس تقریباً به اندازهٔ عیار اهمیت دارد، ولی عیار در دست خود شماست: با یک آنالیز تازه عدم قطعیت اصلی کم می‌شود.</p>

<h2>۶. مقایسه با بازار</h2>
<p>بررسی جهانی معاملات مس نشان می‌دهد شرکت‌های توسعه‌دهندهٔ مس معمولاً با ۰٫۵ تا ۰٫۸ برابر ارزش خالص دارایی و معاملات با کنترل کامل نزدیک ۰٫۸۵ تا ۱٫۱ برابر معامله می‌شوند. کوچک‌ترها در استرالیا معمولاً ۱۵۰ تا ۴۰۰ دلار استرالیا به‌ازای هر تن مس معادل منبع ارزش‌گذاری می‌شوند (نتایج جست‌وجو دربارهٔ ارزش‌گذاری معادن مس، از جمله {LTR('Skillings Mining Intelligence')}؛ منبع دقیق هر عدد تأیید نشد). با {fa(cu_lo)} تا {fa(cu_hi)} تن مس، این معیار {fa(cu_lo*150/1e6,1)} تا {fa(cu_hi*400/1e6,1)} میلیون دلار استرالیا می‌دهد.</p>
<div class="callout warn">این معیارها برای بازارهای دیگر و پروژه‌های بزرگ‌تر است و فقط برای سنجش مرتبه‌بزرگی به کار رفتند؛ ریسک ایران، کوچکی ذخیره و نبود پروانه و ذخیرهٔ تأییدشده معمولاً قیمت را پایین‌تر می‌برد. ضریب ۰٫۵ تا ۰٫۸ به ارزش خالص، عددی بالاتر از بازهٔ ما می‌دهد؛ ما عمداً محافظه‌کارتر ماندیم.</div>

<h2>۷. اقدامات پیش از فروش (به ترتیب اثر بر قیمت)</h2>
<table>
  <tr><th style="width:5%" class="n">#</th><th style="width:44%">اقدام</th><th>اثر بر قیمت</th></tr>
  <tr><td class="n">۱</td><td>آنالیز تازهٔ مس، طلا و نقره از چند نقطه و چند گمانه، در آزمایشگاه معتبر؛ تعیین نتیجهٔ ۱۲ گمانهٔ دیگر</td><td>عدم قطعیت اصلی (۲٫۵٪ در برابر ۵٫۲۹٪) را برطرف می‌کند؛ بیشترین اثر</td></tr>
  <tr><td class="n">۲</td><td>پروانهٔ بهره‌برداری معتبر با ظرفیت و مدت کافی</td><td>خریدار را از ریسک حقوقی رها می‌کند</td></tr>
  <tr><td class="n">۳</td><td>طبقه‌بندی منابع با کد استاندارد توسط شخص صالح؛ بازمحاسبهٔ مدل بلوکی (شعاع محدود) و جدول تناژ–عیار</td><td>تخفیف «برآورد طبقه‌بندی‌نشده» را کم می‌کند</td></tr>
  <tr><td class="n">۴</td><td>استعلام میراث فرهنگی</td><td>اگر محدودیتی نباشد، ریسک مهمی حذف می‌شود</td></tr>
  <tr><td class="n">۵</td><td>تعیین عیار متوسط طلا و نقره</td><td>ارزش افزوده روی مس؛ اکنون در قیمت نیامده</td></tr>
  <tr><td class="n">۶</td><td>اندازه‌گیری وزن مخصوص؛ آزمایش فرآوری؛ تأیید برق و آب</td><td>هزینهٔ راه‌اندازی خریدار را روشن می‌کند</td></tr>
</table>

<h2>۸. ناسازگاری‌ها که پیش از ارائه به خریدار باید روشن شود</h2>
<table>
  <tr><th style="width:26%">موضوع</th><th>ناسازگاری</th><th style="width:30%">اقدام</th></tr>
  <tr><td>استان و شهرستان</td><td>گزارش اکتشاف: استان هرمزگان ({LTR('28°09′N, 56°46′E')}). در نتایج جست‌وجو (Mindat) شهرستان ارزوئیه، استان کرمان آمده است.</td><td>با پروانه تأیید شود؛ گزارش خریدار «هرمزگان» دارد</td></tr>
  <tr><td>عیار مس</td><td>۵٫۲۹٪ (گمانه‌ها؛ نمونه تا ۱۱٫۷۸٪) در برابر مقالهٔ ۲۰۰۲: هشت نمونهٔ ماسیو ۱٫۶۴ تا ۴٫۸۰٪. خود مقاله میانگین را ۲٫۵٪ (چکیده) و فایل شما از جدول ۲ حدود ۳٫۶۷٪ آورده که با هم نمی‌خوانند. علت اختلاف با گمانه‌ها هم معلوم نیست</td><td>متن اصلی مقاله بررسی شود؛ آنالیز تازه</td></tr>
  <tr><td>غلط تایپی در فایل مبدأ</td><td>میانگین مس ماسیو «۳٬۶۷۱۲ ppm (۳٫۶۷٪)»؛ باید ۳۶٬۷۱۲ ppm باشد. میانگین مس بازالت: متن مقاله ۶۰۰ و جدول ۲ حدود ۳۲۳ ppm</td><td>اصلاح در فایل مبدأ</td></tr>
  <tr><td>استقلال منابع</td><td>مقالهٔ ۲۰۰۲ و مقالهٔ برآورد ذخیرهٔ ۲۰۱۰ نویسندهٔ مشترک دارند؛ ذخیرهٔ ۳۰۵ هزار تن در مقالهٔ ۲۰۱۰ همان داده‌های گزارش اکتشاف است و تأیید مستقل به شمار نمی‌آید. مقالهٔ ۲۰۱۰ استان را کرمان نوشته</td><td>در مذاکره «دو منبع مستقل» نگویید</td></tr>
  <tr><td>حق نشر شکل‌ها</td><td>چهار شکل مقالهٔ ۲۰۰۲ (نقشهٔ زمین‌شناسی، برش، نمونهٔ دستی، پاراژنز) با مجوز در گزارش خریدار آمده‌اند؛ مجوز به اظهار شما ثبت شد و من آن را ندیده‌ام</td><td>نامه یا ایمیل مجوز را نگه دارید و در اتاق داده بگذارید</td></tr>
  <tr><td>ضخامت</td><td>افق ۱۰ تا ۳۰ متر (گزارش اکتشاف) در برابر عدسی‌های ۰٫۷ تا ۸٫۵ متر (مقاله)</td><td>لاگ گمانه‌ها بررسی شود</td></tr>
  <tr><td>طلا و نقره</td><td>فقط در ۸ نمونهٔ ماسیو مقاله (۱۸۰ تا ۶۴۰ ppb و ۱۰ تا ۷۵ ppm؛ میانگین‌ها حدود ۳۳۷ ppb و ۲۸ ppm به حساب فایل شما)؛ در اکتشاف تجزیه نشده</td><td>آنالیز طلا و نقره</td></tr>
  <tr><td>تعداد نمونه و میانگین</td><td>۴۳ نمونه در آمار و ۴۴ در مدل؛ میانگین ۵٫۳۸٪، ۵٫۳۷٪ و ۵٫۳۶٪</td><td>یکسان‌سازی در گزارش مبدأ</td></tr>
  <tr><td>تعداد گمانه و متراژ</td><td>نتیجه‌گیری مبدأ «۳ گمانه» دارد ولی ۱۶ گمانه حفر شده؛ متراژ ۲٬۶۷۵ متر در متن و ۲٬۶۷۷٫۵ متر در جدول</td><td>اصلاح متن مبدأ</td></tr>
  <tr><td>تناژ</td><td>۳۰۵٬۵۶۵ تن (مدل سه‌بعدی) و ۳۰۵٬۲۶۳ تن (مدل بلوکی)</td><td>مدل بلوکی ملاک است (اختلاف ۰٫۱٪)</td></tr>
  <tr><td>محتوای فلزی در عیار حدها</td><td>از ضرب کل تناژ محاسبه شده و با بالا رفتن عیار حد از ۱۶٬۱۰۰ به ۳۲٬۰۰۰ تن می‌رسد که ممکن نیست</td><td>بازمحاسبه از مدل بلوکی</td></tr>
  <tr><td>آمارهای لگاریتمی و ردیف شعاع ۱۰۰ متر</td><td>جدول لگاریتمی عیناً همان ارقام خام است؛ عیار ردیف ۱۰۰ متر با حجم سازگار نیست</td><td>بازمحاسبه</td></tr>
  <tr><td>مقیاس نقشه</td><td>۱:۱۰۰۰ برای محدودهٔ حدود ۲ کیلومترمربع غیرمعمول است</td><td>تأیید شود</td></tr>
</table>

<h2>۹. راهبرد مذاکره</h2>
<ul>
  <li>با {fa(ASK,0)} میلیون دلار شروع کنید و کف {fa(FLOOR,0)} میلیون دلار را فاش نکنید. گزارش خریدار فقط مشخصات فنی دارد و قیمتی در آن نیست.</li>
  <li>مدارک را پس از امضای تعهد محرمانگی (NDA) و در اتاق داده بدهید.</li>
  <li>پرداخت را مرحله‌ای ببندید: بخشی هنگام امضا، بخشی پس از انتقال پروانه، بخشی پس از تأیید آنالیز مستقل.</li>
  <li>قبل از اعلام قیمت نهایی، ارزیابی یک کارشناس رسمی معدن بگیرید؛ عدد او مبنای قابل‌استناد در مذاکره است.</li>
  <li>اگر قیمت مس بیشتر از ۱۷٬۰۰۰ دلار شد، بالای بازه واقع‌بینانه‌تر می‌شود؛ اگر زیر ۱۱٬۰۰۰ رفت، فروش را به تأخیر نیندازید.</li>
  <li>ناسازگاری‌های بخش ۸ را قبل از دادن گزارش اکتشاف به خریدار اصلاح یا توضیح دهید؛ خریدار حرفه‌ای آن‌ها را پیدا می‌کند و اعتماد را کم می‌کند.</li>
</ul>

<h2>۱۰. اعتبار منابع و اعداد</h2>
<table>
  <tr><th style="width:30%">عدد</th><th style="width:30%">منبع</th><th>وضعیت بررسی</th></tr>
  <tr><td>ذخیره {fa(ORE_T)} تن، عیار ۵٫۲۹٪، {fa(16148)} تن مس</td><td>{EXPL} (فایل شما)</td><td>منبع اصلی؛ با داده خام آزمایشگاه و خروجی نرم‌افزار تطبیق داده نشده</td></tr>
  <tr><td>عیار مس سطحی، طلا و نقره (جدول ۲ مقاله)</td><td>راستاد و همکاران، ۲۰۰۲</td><td>از خلاصهٔ فایل شما و چکیدهٔ نتایج جست‌وجو؛ متن اصلی مقاله را ندیدم</td></tr>
  <tr><td>«تنها نمونهٔ سولفید توده‌ای غنی از طلا»</td><td>بررسی متالوژنی VMS ایران (ScienceDirect)</td><td>از چکیدهٔ نتایج جست‌وجو؛ باید با متن اصلی تطبیق شود</td></tr>
  <tr><td>قیمت مس {fa(CU_PRICE)} دلار</td><td>{LTR('Trading Economics')}</td><td>صفحه از محیط ما باز نشد؛ عدد از نتایج جست‌وجو</td></tr>
  <tr><td>دلار {fa(USD_TOMAN)} تومان</td><td>تعادل، ۱۳ مهر ۱۴۰۵</td><td>از نتایج جست‌وجو؛ منابع دیگر تا ۲۶۹٬۲۰۰ تومان هم گفته‌اند و نرخ روزانه تغییر می‌کند</td></tr>
  <tr><td>هزینه، بازیابی، ضریب ۳۰٪ و نسبت ۱ تا ۳٪</td><td>فرض تحلیلی ما</td><td>منبع منتشرشده ندارد؛ با کارشناس معدن بازبینی شود</td></tr>
</table>
<ul class="src">
  {SRC_ROW('Skillings Mining Intelligence — copper M&amp;A and valuation commentary','https://skillings.net/skillings-mining-intelligence-copper-records-ma-sequencing-and-streaming-discipline')}
  {SRC_ROW('تعادل — قیمت دلار و یورو ۱۳ مهر ۱۴۰۵','https://www.taadolnewspaper.ir/fa/news/405830/')}
  {SRC_ROW('Trading Economics — Copper','https://tradingeconomics.com/commodity/copper')}
</ul>
"""

(HERE / "buyer.html").write_text(doc("کانسار مس شیخ‌عالی — گزارش معرفی", buyer), encoding="utf8")
(HERE / "internal.html").write_text(doc("ارزش‌گذاری و راهبرد فروش کانسار مس شیخ‌عالی — داخلی", internal, alt=True), encoding="utf8")
print("ok", f"insitu {insitu_lo:.0f}-{insitu_hi:.0f}  npv {npv_lo:.1f}-{npv_hi:.1f}  dcf {dcf_lo:.1f}-{dcf_hi:.1f}  "
      f"pct {pr_lo_lo:.1f}-{pr_hi_hi:.1f}  ask {toman_b(ASK):.0f}B floor {toman_b(FLOOR):.0f}B  sumlen {sum(float(b[4]) for b in BOREHOLES)}")
