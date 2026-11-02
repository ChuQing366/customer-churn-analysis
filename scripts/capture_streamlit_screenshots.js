const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const outDir = path.join(process.cwd(), 'reports', 'screenshots');
fs.mkdirSync(outDir, { recursive: true });

async function clickTab(page, name) {
  const tab = page.getByRole('tab', { name: new RegExp(name) });
  await tab.click();
  await page.waitForTimeout(1800);
}

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 1100 }, deviceScaleFactor: 1 });
  await page.goto('http://localhost:8501', { waitUntil: 'networkidle', timeout: 60000 });
  await page.waitForTimeout(2500);

  await page.screenshot({ path: path.join(outDir, '01_streamlit_business_overview.png'), fullPage: true });

  const targets = [
    ['NLP|文本|情感', '02_streamlit_nlp.png'],
    ['聚类|分群', '03_streamlit_cluster.png'],
    ['模型评估|评估', '04_streamlit_model_metrics.png'],
    ['单客预测|预测', '05_streamlit_single_customer_prediction.png'],
    ['输出图表|图表', '06_streamlit_output_gallery.png'],
  ];

  for (const [name, file] of targets) {
    try {
      await clickTab(page, name);
      await page.screenshot({ path: path.join(outDir, file), fullPage: true });
    } catch (err) {
      console.error(`Failed to capture ${name}: ${err.message}`);
    }
  }

  await browser.close();
  console.log(outDir);
})();
