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
USD_TOMAN = 266020        # free-market rate, 11 Mehr 1405
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
"""


def doc(title, body, alt=False):
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


# ================================================================= BUYER REPORT
SRC_ROW = lambda t, u: f'<li><a href="{u}">{t}</a></li>'

buyer = f"""
<div class="banner">
  <h1>معدن مس و طلای شیخ‌علی</h1>
  <div class="sub">گزارش معرفی برای خریدار و سرمایه‌گذار</div>
  <div class="meta">شهرستان ارزوئیه، استان کرمان &nbsp;|&nbsp; ۱۳ مهر ۱۴۰۵ &nbsp;|&nbsp;
  پیش‌نویس ۱ — بخش‌های زردرنگ باید توسط مالک تکمیل شود</div>
</div>

<div class="kpis">
  <div class="kpi"><b>{fa(ORE_T)} تن</b><span>ذخیرهٔ برآوردی سنگ (برآورد اولیه، تأییدنشده)</span></div>
  <div class="kpi"><b>۵٫۲۹٪ مس</b><span>عیار متوسط در برآورد ذخیره (مطالعهٔ دیگر: ۲٫۵٪)</span></div>
  <div class="kpi"><b>{fa(cu_lo/1000,1)} تا {fa(cu_hi/1000,1)} هزار تن</b><span>مس فلزی محتوا (بسته به عیار)</span></div>
  <div class="kpi alt"><b>تا ۰٫۶۴ گرم طلا</b><span>در هر تن کانهٔ توده‌ای (حداکثر عیار منتشرشده)</span></div>
  <div class="kpi alt"><b>تا ۷۵ گرم نقره</b><span>در هر تن کانهٔ توده‌ای (حداکثر عیار منتشرشده)</span></div>
  <div class="kpi"><b>{fa(CU_PRICE)} دلار</b><span>قیمت هر تن مس، ۹ مهر ۱۴۰۵ (حدود ۳۰٪ بالاتر از پارسال)</span></div>
</div>

<h2>۱. خلاصهٔ اجرایی</h2>
<p>شیخ‌علی یک کانسار مس سولفیدی توده‌ای از نوع قبرس (VMS درون افیولیت) در شهرستان ارزوئیه، حدود ۳۰۰ کیلومتری جنوب‌شرق شهر کرمان است. معدن از دوران باستان فعال بوده و آثار معدنکاری و سرباره‌های مس باستانی در آن بررسی شده است. کانهٔ آن علاوه بر مس، طلا و نقره هم دارد.</p>
<p>برآورد اولیهٔ دانشگاهی، ذخیره را حدود {fa(ORE_T)} تن سنگ با عیار متوسط ۵٫۲۹٪ مس می‌داند. این عیار حدود هفت برابر عیار متوسط معدن سرچشمه (۰٫۷٪) است. یک بررسی زمین‌شناسی ایران، شیخ‌علی را تنها نمونهٔ این نوع سولفید توده‌ای غنی از طلا در بخش جنوبی پهنهٔ سنندج–سیرجان می‌نامد.</p>
<div class="callout">
  <b>فرصت برای خریدار:</b> عیار بالا، کانهٔ سولفیدی مناسب فلوتاسیون، طلا و نقره همراه، قیمت بالای مس، و نزدیکی به کارخانه‌های تغلیظ و ذوب مس استان کرمان. معدن کوچک است و برای خریداری مناسب است که واحد استخراج کوچک تا متوسط می‌خواهد.
</div>

<h2>۲. موقعیت و مشخصات</h2>
<table>
  <tr><th style="width:30%">مشخصه</th><th>مقدار</th></tr>
  <tr><td>مادهٔ معدنی</td><td>مس، با طلا و نقره و روی (از اسفالریت) همراه</td></tr>
  <tr><td>موقعیت</td><td>شهرستان ارزوئیه، استان کرمان؛ حدود ۳۰۰ کیلومتر جنوب‌شرق شهر کرمان</td></tr>
  <tr><td>واحد زمین‌شناسی</td><td>ملانژ رنگی افیولیتی، بخش جنوب‌شرقی زون رورانده زاگرس</td></tr>
  <tr><td>نوع کانسار</td><td>مس سولفیدی توده‌ای از نوع قبرس (VMS درون افیولیت)</td></tr>
  <tr><td>مختصات رئوس (UTM)</td><td>{todo()}</td></tr>
  <tr><td>مساحت محدودهٔ پروانه (کیلومتر مربع)</td><td>{todo()}</td></tr>
  <tr><td>دسترسی (فاصله تا جادهٔ اصلی و شهر)</td><td>{todo()}</td></tr>
</table>

<h2>۳. زمین‌شناسی و کانه‌زایی</h2>
<p>کانسار در یک برش آتشفشانی–رسوبی از ملانژ افیولیتی، بین سرپانتینیت و سنگ‌های فراباز مانند دونیت و هارزبورژیت قرار دارد. سنگ میزبان شامل گدازه‌های بالشی بازالتی، دیاباز، آهک پلاژیک، چرت رادیولاریتی و گریواک (کرتاسهٔ بالایی) است. مطالعات، کانسار را حاصل برون‌دم‌های زیردریایی هم‌زمان با تشکیل سنگ‌های میزبان می‌دانند (راستاد و همکاران، ۲۰۰۲).</p>
<table>
  <tr><th style="width:30%">ویژگی</th><th>توضیح</th></tr>
  <tr><td>هندسهٔ کانه</td><td>عدسی‌های توده‌ای ناپیوسته، هم‌راستا با آهک پلاژیک و گدازهٔ بالشی؛ ضخامت ۰٫۷ تا ۸٫۵ متر</td></tr>
  <tr><td>طول افق کانه‌دار</td><td>حدود ۵۵۰ متر</td></tr>
  <tr><td>کانی‌ها</td><td>پیریت، کالکوپیریت، اسفالریت، کوولیت، دیژنیت، بورنیت، اسپکولاریت و مس طبیعی</td></tr>
  <tr><td>بافت کانه</td><td>توده‌ای، لایه‌ای، کلوفرم، پراکنده و به‌ندرت رگچه‌ای</td></tr>
  <tr><td>مطالعات منتشرشده</td><td>زمین‌شناسی و ژئوشیمی (راستاد و همکاران، ۲۰۰۲)، مدل‌سازی سه‌بعدی و برآورد ذخیره، طراحی شبکهٔ اکتشاف تکمیلی ژئوشیمی و ژئوفیزیک (پایان‌نامهٔ دانشگاه صنعتی اصفهان)، باستان‌فلزشناسی سرباره‌ها (امامی و پرورش، ۲۰۱۶)، آنالیز پالادیم، پلاتین و رودیم ({LTR('USGS')})</td></tr>
</table>
<p>آنالیز <span class="ltr">USGS</span> نشان داد پتانسیل پالادیم، پلاتین و رودیم برای محصول جانبی پایین است؛ پس ارزش معدن بر مس، طلا و نقره استوار است.</p>

<h2>۴. ذخیره، عیار و فلز محتوا</h2>
<table>
  <tr><th style="width:36%">شاخص</th><th style="width:26%">مقدار</th><th>منبع</th></tr>
  <tr><td>ذخیرهٔ کل برآوردی (تن سنگ)</td><td class="n">{fa(ORE_T)}</td><td>مدل‌سازی سه‌بعدی و برآورد اولیهٔ ذخیره</td></tr>
  <tr><td>عیار متوسط مس در برآورد ذخیره</td><td class="n">۵٫۲۹٪</td><td>همان منبع</td></tr>
  <tr><td>عیار متوسط / حداکثر مس در کانهٔ توده‌ای</td><td class="n">۲٫۵٪ / ۴٫۸٪</td><td>راستاد و همکاران، ۲۰۰۲ (به نقل از نتایج جست‌وجو)</td></tr>
  <tr><td>مس فلزی محتوا (تن، محاسبه‌شده)</td><td class="n">{fa(cu_lo)} تا {fa(cu_hi)}</td><td>ذخیره × عیار</td></tr>
  <tr><td>حداکثر عیار طلا (گرم در تن)</td><td class="n">۰٫۶۴</td><td>راستاد و همکاران، ۲۰۰۲</td></tr>
  <tr><td>حداکثر عیار نقره (گرم در تن)</td><td class="n">۷۵</td><td>راستاد و همکاران، ۲۰۰۲</td></tr>
  <tr><td>روش استخراج</td><td class="n">{todo('روباز / زیرزمینی؟')}</td><td></td></tr>
</table>
<div class="callout warn">
  <b>محدودیت اعداد:</b> ذخیره یک برآورد اولیهٔ دانشگاهی است و ذخیرهٔ قطعی تأییدشدهٔ سازمان صمت نیست. عیار طلا و نقره فقط حداکثر منتشر شده و عیار متوسط آن‌ها باید با آنالیز تازه تعیین شود. دو مطالعه برای عیار مس عددهای متفاوت (۵٫۲۹٪ و ۲٫۵٪) داده‌اند. خریدار باید پیش از تصمیم، نمونه‌برداری مستقل انجام دهد.
</div>

<h2>۵. وضعیت حقوقی و مجوزها</h2>
<p>طبق قانون معادن، پروانهٔ بهره‌برداری سندی رسمی، قابل معامله، تمدید و توثیق است. موارد زیر باید از اسناد مالک تکمیل شود و در اتاق داده در اختیار خریدار قرار گیرد.</p>
<table>
  <tr><th style="width:55%">مورد</th><th>وضعیت</th></tr>
  <tr><td>نوع مجوز و شمارهٔ پروانه</td><td>{todo()}</td></tr>
  <tr><td>تاریخ صدور و انقضا</td><td>{todo()}</td></tr>
  <tr><td>ظرفیت استخراج مجاز (تن در سال)</td><td>{todo()}</td></tr>
  <tr><td>حقوق دولتی و بدهی معوق</td><td>{todo()}</td></tr>
  <tr><td>مجوز محیط‌زیست و منابع طبیعی</td><td>{todo()}</td></tr>
  <tr><td>استعلام میراث فرهنگی</td><td>{todo()}</td></tr>
</table>
<p>حقوق دولتی درصدی از بهای فروش مادهٔ معدنی است؛ برای ۱۴۰۴ نرخ ۱۵٪ تعیین شد و برای شش ماه نخست ۱۴۰۵ بر پایهٔ استخراج واقعی محاسبه می‌شود.</p>

<h2>۶. زیرساخت و تجهیزات</h2>
<table>
  <tr><th style="width:55%">مورد</th><th>وضعیت</th></tr>
  <tr><td>جادهٔ دسترسی (نوع و طول)</td><td>{todo()}</td></tr>
  <tr><td>برق (شبکه / ژنراتور)</td><td>{todo()}</td></tr>
  <tr><td>آب (منبع و مجوز)</td><td>{todo()}</td></tr>
  <tr><td>ماشین‌آلات موجود و سال ساخت</td><td>{todo()}</td></tr>
  <tr><td>ابنیه (کمپ، انبار، دفتر)</td><td>{todo()}</td></tr>
</table>

<h2>۷. بازار محصول</h2>
<p>محصول معدن سنگ سولفیدی مس (و کنسانتره) است. خریداران طبیعی آن کارخانه‌های فلوتاسیون و تغلیظ مس در استان کرمان هستند. قیمت مس در بورس فلزات لندن در ۹ مهر ۱۴۰۵ حدود {fa(CU_PRICE)} دلار در تن بود؛ حدود ۳۰٪ بالاتر از یک سال قبل ({LTR('Trading Economics')}). طلا و نقره در کنسانترهٔ مس بازیابی و جداگانه قیمت‌گذاری می‌شوند.</p>

<h2>۸. ریسک‌ها و راه کاهش آن‌ها</h2>
<table>
  <tr><th style="width:30%">ریسک</th><th>راه کاهش</th></tr>
  <tr><td>اندازهٔ کوچک ذخیره و ناپیوستگی عدسی‌ها</td><td>استخراج مرحله‌ای عدسی‌به‌عدسی؛ اکتشاف تکمیلی اطراف عدسی‌ها (طرح شبکه در پایان‌نامهٔ دانشگاه صنعتی اصفهان آمده است)</td></tr>
  <tr><td>اختلاف عیار مس در دو مطالعه</td><td>نمونه‌برداری و آنالیز مستقل در آزمایشگاه معتبر پیش از معامله</td></tr>
  <tr><td>محدودیت میراث فرهنگی (آثار معدنکاری باستانی)</td><td>استعلام رسمی و مستندسازی آثار پیش از فروش</td></tr>
  <tr><td>زهاب اسیدی از کانهٔ پرپیریت</td><td>طرح مدیریت پساب و باطله در طرح بهره‌برداری</td></tr>
  <tr><td>نوسان قیمت مس و ارز</td><td>ارزش‌گذاری با چند سناریوی قیمت</td></tr>
</table>

<h2>۹. اتاق داده: مدارک قابل ارائه به خریدار</h2>
<ul class="check">
  <li>تصویر پروانهٔ بهره‌برداری و نقشهٔ محدوده</li>
  <li>گزارش پایان عملیات اکتشافی و گواهی کشف</li>
  <li>طرح بهره‌برداری مصوب</li>
  <li>نتایج آنالیز نمونه‌ها (مس، طلا، نقره، روی) از آزمایشگاه معتبر</li>
  <li>مفاصاحساب حقوق دولتی و بیمه</li>
  <li>فهرست تجهیزات با عکس</li>
</ul>
<p><b>تماس:</b> {todo('نام و شمارهٔ تماس فروشنده')}</p>

<h2>۱۰. منابع</h2>
<p class="note">اعداد این گزارش از چکیده و نتایج جست‌وجوی این منابع آمده است. متن کامل بیشتر آن‌ها از محیط تهیهٔ گزارش باز نشد؛ پیش از ارائه به خریدار باید با متن اصلی تطبیق داده شود.</p>
<ul class="src">
  {SRC_ROW('Rastad, Monazzami Miralipour &amp; Momenzadeh (2002). Sheikh-Ali Copper Deposit, a Cyprus-Type VMS Deposit in Southeast Iran. Journal of Sciences, Islamic Republic of Iran, 13, 51–63','https://www.researchgate.net/publication/228463812_Sheikh-Ali_Copper_Deposit_a_Cyprus-Type_VMS_Deposit_in_Southeast_Iran')}
  {SRC_ROW('3D Modeling and preliminary ore reserve estimation of Sheikh-Ali Copper deposit','https://www.academia.edu/12113978/3D_Modeling_and_preliminary_ore_reserve_estimation_of_Sheikh_Ali_Copper_deposit')}
  {SRC_ROW('Metallogeny of volcanogenic massive sulfide deposits of Iran (ScienceDirect)','https://www.sciencedirect.com/science/article/abs/pii/S016913681730495X')}
  {SRC_ROW('Mindat — Sheikh Ali mine, Arzuiyeh County, Kerman','https://www.mindat.org/locentry-615796.html')}
  {SRC_ROW('پایان‌نامهٔ اکتشاف تکمیلی ژئوشیمیایی و ژئوفیزیکی کانسار مس شیخ‌علی — دانشگاه صنعتی اصفهان','https://thesis.iut.ac.ir/complementary-geochemical-and-geophysical-exploration-sheikh-ali-copper-deposit-order-design')}
  {SRC_ROW('مطالعات ژئوشیمی و ژئوفیزیک کانسار شیخ‌علی — دانشگاه تهران','https://jsciences.ut.ac.ir/article_31754.html')}
  {SRC_ROW('USGS Open-File Report 79-840 — Pd, Pt and Rh in mafic and ultramafic rocks of Turkey and Iran','https://pubs.usgs.gov/publication/ofr79840')}
  <li>Emami &amp; Parvaresh (2016). Mineralogical and petrochemical investigation of copper slags from Sheikh-Ali ophiolite copper deposits, Kerman. Archäometrie und Denkmalpflege 2016, Göttingen, pp. 205–208 (از خلاصهٔ نتایج جست‌وجو؛ پیوند مستقیم تأیید نشد)</li>
  {SRC_ROW('Trading Economics — Copper','https://tradingeconomics.com/commodity/copper')}
  {SRC_ROW('حقوق دولتی معادن ۱۵ درصد — انتخاب','https://www.entekhab.ir/fa/news/834576/')}
  {SRC_ROW('محاسبهٔ حقوق دولتی بر مبنای استخراج واقعی — فلزات خاورمیانه','https://felezatkhavarmianeh.ir/fa/news/404062/')}
  <li>قانون معادن و اصلاحیهٔ آن (متن در ویکی‌حقوق) — قابل‌معامله‌بودن پروانهٔ بهره‌برداری؛ شمارهٔ ماده در نتایج جست‌وجو مشخص نشد و باید از متن قانون تأیید شود</li>
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

aud_lo_t, aud_hi_t = cu_lo, cu_hi
internal = f"""
<div class="banner alt">
  <h1>ارزش‌گذاری و راهبرد فروش معدن شیخ‌علی</h1>
  <div class="sub">سند داخلی فروشنده — برای خریدار ارسال نشود</div>
  <div class="meta">۱۳ مهر ۱۴۰۵ &nbsp;|&nbsp; دلار آزاد ۱۱ مهر ۱۴۰۵: {fa(USD_TOMAN)} تومان &nbsp;|&nbsp; مس: {fa(CU_PRICE)} دلار در تن</div>
</div>

<div class="kpis">
  <div class="kpi alt"><b>{fa(ASK,0)} میلیون دلار</b><span>قیمت اولیهٔ پیشنهادی ≈ {fa(toman_b(ASK))} میلیارد تومان</span></div>
  <div class="kpi alt"><b>{fa(FLOOR,0)} میلیون دلار</b><span>کف مذاکره ≈ {fa(toman_b(FLOOR))} میلیارد تومان</span></div>
  <div class="kpi"><b>{fa(insitu_lo)} تا {fa(insitu_hi)} میلیون دلار</b><span>ارزش مس درجا (سقف نظری، نه قیمت معدن)</span></div>
</div>

<h2>۱. جمع‌بندی</h2>
<p>با اطلاعات فعلی، قیمت منطقی فروش بین <b>{fa(FLOOR,0)} تا {fa(ASK,0)} میلیون دلار</b> است. این بازه از دو روش مستقل و یک مقایسهٔ بازار به دست آمد و جایگزین ارزیابی کارشناس رسمی نیست. مهم‌ترین عامل قیمت <b>عیار واقعی مس</b> است: اگر عیار ۵٪ با آنالیز تازه تأیید شود، بالای بازه قابل دفاع می‌شود؛ اگر عیار نزدیک ۲٫۵٪ باشد، قیمت به پایین بازه یا کمتر می‌رسد.</p>

<h2>۲. روش‌ها و فرض‌ها</h2>
<h3>روش الف: درصدی از ارزش مس درجا</h3>
<p>ارزش مس درجا = ذخیره × عیار × قیمت مس. معدن کوچک با ذخیرهٔ غیرقطعی معمولاً ۱ تا ۳٪ این ارزش فروخته می‌شود. <span class="note">(این نسبت تقریبی و برآورد خود ماست؛ منبع منتشرشده ندارد.)</span></p>
<table>
  <tr><th>سناریو</th><th class="n">مس محتوا (تن)</th><th class="n">ارزش درجا (میلیون دلار)</th><th class="n">۱٪ تا ۳٪ آن (میلیون دلار)</th></tr>
  <tr><td>عیار ۵٫۲۹٪</td><td class="n">{fa(cu_hi)}</td><td class="n">{fa(insitu_hi)}</td><td class="n">{fa(pr_hi_lo,1)} تا {fa(pr_hi_hi,1)}</td></tr>
  <tr><td>عیار ۲٫۵٪</td><td class="n">{fa(cu_lo)}</td><td class="n">{fa(insitu_lo)}</td><td class="n">{fa(pr_lo_lo,1)} تا {fa(pr_lo_hi,1)}</td></tr>
</table>
<h3>روش ب: ارزش فعلی سودهای آینده (DCF ساده)</h3>
<table>
  <tr><th style="width:42%">فرض</th><th>مقدار</th></tr>
  <tr><td>ظرفیت استخراج</td><td>{fa(TPY)} تن در سال؛ عمر معدن حدود {fa(ORE_T/TPY,1)} سال</td></tr>
  <tr><td>بازیابی فرآوری / درصد قابل پرداخت مس</td><td>{fa(REC*100)}٪ / {fa(PAY*100)}٪</td></tr>
  <tr><td>هزینهٔ استخراج و فرآوری</td><td>{fa(COST)} دلار در هر تن سنگ</td></tr>
  <tr><td>حقوق دولتی / مالیات</td><td>{fa(ROY*100)}٪ درآمد / {fa(TAX*100)}٪ سود</td></tr>
  <tr><td>سرمایهٔ اولیه / نرخ تنزیل</td><td>{fa(CAPEX/1e6)} میلیون دلار / {fa(DISC*100)}٪</td></tr>
  <tr><td>طلا و نقره</td><td>در محاسبه نیامده (عیار متوسط معلوم نیست)</td></tr>
</table>
<p>نتیجه: ارزش فعلی خالص حدود {fa(npv_hi,1)} میلیون دلار (عیار ۵٫۲۹٪) و {fa(npv_lo,1)} میلیون دلار (عیار ۲٫۵٪). چون ذخیره فقط برآورد دانشگاهی است و پروانه و دسترسی روشن نیست، خریدار این عدد را تخفیف می‌دهد. ما {fa(HAIRCUT*100)}٪ آن را گرفتیم: {fa(dcf_hi,1)} و {fa(dcf_lo,1)} میلیون دلار. <span class="note">(ضریب {fa(HAIRCUT*100)}٪ فرض ماست.)</span></p>

<h2>۳. بازهٔ ارزش</h2>
<figure>{football()}
<figcaption>نمودار ۱. بازهٔ ارزش به میلیون دلار؛ دو میلهٔ بالا از محاسبهٔ بالا، میلهٔ پایین بازهٔ پیشنهادی است.</figcaption></figure>

<h2>۴. حساسیت به عیار و قیمت مس</h2>
<p>ارزش پیشنهادی (میلیون دلار) = {fa(HAIRCUT*100)}٪ ارزش فعلی خالص، با فرض‌های بخش ۲:</p>
<table>
  <tr><th>عیار مس</th><th class="n">مس ۱۱٬۰۰۰ دلار</th><th class="n">مس {fa(CU_PRICE)} دلار (فعلی)</th><th class="n">مس ۱۷٬۰۰۰ دلار</th></tr>
  {sens_rows}
</table>
<p>قیمت مس تقریباً به اندازهٔ عیار اهمیت دارد، ولی عیار در دست خود شماست: با یک آنالیز تازه عدم قطعیت اصلی کم می‌شود.</p>

<h2>۵. مقایسه با بازار</h2>
<p>بررسی جهانی معاملات مس نشان می‌دهد شرکت‌های توسعه‌دهندهٔ مس معمولاً با ۰٫۵ تا ۰٫۸ برابر ارزش خالص دارایی و معاملات با کنترل کامل نزدیک ۰٫۸۵ تا ۱٫۱ برابر معامله می‌شوند. کوچک‌ترها در استرالیا معمولاً ۱۵۰ تا ۴۰۰ دلار استرالیا به‌ازای هر تن مس معادل منبع ارزش‌گذاری می‌شوند (نتایج جست‌وجو دربارهٔ ارزش‌گذاری معادن مس، از جمله {LTR('Skillings Mining Intelligence')}؛ منبع دقیق هر عدد تأیید نشد). با {fa(cu_lo)} تا {fa(cu_hi)} تن مس، این معیار {fa(cu_lo*150/1e6,1)} تا {fa(cu_hi*400/1e6,1)} میلیون دلار استرالیا می‌دهد.</p>
<div class="callout warn">این معیارها برای بازارهای دیگر و پروژه‌های بزرگ‌تر است. آن‌ها فقط برای سنجش مرتبه‌بزرگی (نه تعیین قیمت) به کار رفتند؛ ریسک ایران، کوچکی ذخیره و نبودن پروانه و ذخیرهٔ تأییدشده معمولاً قیمت را پایین‌تر از این معیارها می‌برد. ضریب ۰٫۵ تا ۰٫۸ به ارزش خالص، عددی بالاتر از بازهٔ ما می‌دهد؛ ما عمداً محافظه‌کارتر ماندیم.</div>

<h2>۶. چه کارهایی قیمت را بالا می‌برد</h2>
<table>
  <tr><th style="width:5%" class="n">#</th><th style="width:40%">اقدام</th><th>اثر بر قیمت</th></tr>
  <tr><td class="n">۱</td><td>آنالیز تازهٔ مس، طلا و نقره از چند نقطه، در آزمایشگاه معتبر</td><td>عدم قطعیت اصلی (۲٫۵٪ در برابر ۵٫۲۹٪) را برطرف می‌کند؛ بیشترین اثر</td></tr>
  <tr><td class="n">۲</td><td>پروانهٔ بهره‌برداری معتبر با ظرفیت و مدت کافی</td><td>خریدار را از ریسک حقوقی رها می‌کند</td></tr>
  <tr><td class="n">۳</td><td>گزارش پایان عملیات اکتشافی یا ذخیرهٔ تأییدشدهٔ صمت</td><td>تخفیف «برآورد دانشگاهی» را کم می‌کند</td></tr>
  <tr><td class="n">۴</td><td>استعلام میراث فرهنگی</td><td>اگر محدودیتی نباشد، ریسک مهمی حذف می‌شود</td></tr>
  <tr><td class="n">۵</td><td>تعیین عیار متوسط طلا و نقره</td><td>ارزش افزوده روی مس؛ اکنون در قیمت نیامده</td></tr>
  <tr><td class="n">۶</td><td>تأیید جاده، برق و آب</td><td>هزینهٔ راه‌اندازی خریدار را روشن می‌کند</td></tr>
</table>

<h2>۷. راهبرد مذاکره</h2>
<ul>
  <li>با {fa(ASK,0)} میلیون دلار شروع کنید و کف {fa(FLOOR,0)} میلیون دلار را فاش نکنید. گزارش خریدار فقط مشخصات فنی دارد و قیمتی در آن نیست.</li>
  <li>مدارک را پس از امضای تعهد محرمانگی (NDA) و در اتاق داده بدهید.</li>
  <li>پرداخت را مرحله‌ای ببندید: بخشی هنگام امضا، بخشی پس از انتقال پروانه، بخشی پس از تأیید آنالیز مستقل.</li>
  <li>قبل از اعلام قیمت نهایی، ارزیابی یک کارشناس رسمی معدن بگیرید؛ عدد او مبنای قابل‌استناد در مذاکره و دادگاه است.</li>
  <li>اگر قیمت مس بیشتر از ۱۷٬۰۰۰ دلار شد، بالای بازه واقع‌بینانه‌تر می‌شود؛ اگر زیر ۱۱٬۰۰۰ رفت، فروش را به تأخیر نیندازید.</li>
</ul>

<h2>۸. اعتبار منابع و اعداد</h2>
<table>
  <tr><th style="width:30%">عدد</th><th style="width:30%">منبع</th><th>وضعیت بررسی</th></tr>
  <tr><td>ذخیره {fa(ORE_T)} تن، عیار ۵٫۲۹٪</td><td>مدل‌سازی سه‌بعدی (دانشگاهی)</td><td>فقط از چکیدهٔ نتایج جست‌وجو؛ متن کامل باز نشد؛ نویسنده و سال معلوم نشد</td></tr>
  <tr><td>عیار مس ۲٫۵٪، طلا ۰٫۶۴ و نقره ۷۵ گرم در تن</td><td>راستاد و همکاران، ۲۰۰۲</td><td>از چکیدهٔ نتایج جست‌وجو؛ متن کامل باز نشد</td></tr>
  <tr><td>«تنها نمونهٔ سولفید توده‌ای غنی از طلا»</td><td>بررسی متالوژنی VMS ایران (ScienceDirect)</td><td>از چکیدهٔ نتایج جست‌وجو؛ باید با متن اصلی تطبیق شود</td></tr>
  <tr><td>قیمت مس {fa(CU_PRICE)} دلار</td><td>{LTR('Trading Economics')}</td><td>صفحه از محیط ما باز نشد؛ عدد از نتایج جست‌وجو</td></tr>
  <tr><td>دلار {fa(USD_TOMAN)} تومان</td><td>اقتصادآنلاین، ۱۱ مهر ۱۴۰۵</td><td>از نتایج جست‌وجو؛ نرخ روزانه تغییر می‌کند</td></tr>
  <tr><td>هزینه، بازیابی، ضریب ۳۰٪ و نسبت ۱ تا ۳٪</td><td>فرض تحلیلی ما</td><td>منبع منتشرشده ندارد؛ با کارشناس معدن بازبینی شود</td></tr>
</table>
<ul class="src">
  {SRC_ROW('Skillings Mining Intelligence — copper M&amp;A and valuation commentary','https://skillings.net/skillings-mining-intelligence-copper-records-ma-sequencing-and-streaming-discipline')}
  {SRC_ROW('اقتصادآنلاین — قیمت دلار بازار آزاد ۱۱ مهر ۱۴۰۵','https://www.eghtesadonline.com/fa/news/2166737/')}
  {SRC_ROW('Trading Economics — Copper','https://tradingeconomics.com/commodity/copper')}
</ul>
"""

(HERE / "buyer.html").write_text(doc("معدن مس و طلای شیخ‌علی — گزارش معرفی", buyer), encoding="utf8")
(HERE / "internal.html").write_text(doc("ارزش‌گذاری و راهبرد فروش معدن شیخ‌علی — داخلی", internal, alt=True), encoding="utf8")
print("ok", f"insitu {insitu_lo:.0f}-{insitu_hi:.0f}  npv {npv_lo:.1f}-{npv_hi:.1f}  dcf {dcf_lo:.1f}-{dcf_hi:.1f}  "
      f"pct {pr_lo_lo:.1f}-{pr_hi_hi:.1f}  ask {toman_b(ASK):.0f}B floor {toman_b(FLOOR):.0f}B")
