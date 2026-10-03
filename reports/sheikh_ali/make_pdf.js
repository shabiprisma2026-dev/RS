const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch();
  const p = await b.newPage();
  await p.goto('file://' + __dirname + '/report.html');
  await p.evaluate(() => document.fonts.ready);
  await p.pdf({ path: '' + __dirname + '/../../Sheikh_Ali_mine_sale_report_fa.pdf', format: 'A4', printBackground: true,
    displayHeaderFooter: true, headerTemplate: '<div></div>',
    footerTemplate: '<div style="width:100%;text-align:center;font-family:\'Vazirmatn UI FD\';font-size:9px;color:#5b6672;direction:rtl">صفحهٔ <span class="pageNumber"></span> از <span class="totalPages"></span></div>',
    margin: { top: '20mm', bottom: '18mm', left: '20mm', right: '20mm' } });
  await b.close();
})();
