// usage: node pdf.js            -> builds both PDFs into the repo root
const { chromium } = require('playwright');
const path = require('path');
const jobs = [
  ['buyer.html',    '../../Sheikh_Ali_report_buyer_fa.pdf',     'معدن مس و طلای شیخ‌علی — گزارش معرفی'],
  ['internal.html', '../../Sheikh_Ali_valuation_internal_fa.pdf','ارزش‌گذاری شیخ‌علی — داخلی، برای خریدار ارسال نشود'],
];
(async () => {
  const b = await chromium.launch();
  for (const [html, out, title] of jobs) {
    const p = await b.newPage();
    await p.goto('file://' + path.join(__dirname, html));
    await p.evaluate(() => document.fonts.ready);
    await p.pdf({ path: path.join(__dirname, out), format: 'A4', printBackground: true,
      displayHeaderFooter: true, headerTemplate: '<div></div>',
      footerTemplate: `<div style="width:100%;font-family:'Vazirmatn UI FD';font-size:8.5px;color:#5d6975;direction:rtl;display:flex;justify-content:space-between;padding:0 20mm"><span>${title}</span><span>صفحهٔ <span class="pageNumber"></span> از <span class="totalPages"></span></span></div>`,
      margin: { top: '16mm', bottom: '16mm', left: '19mm', right: '19mm' } });
    await p.close();
  }
  await b.close();
})();
