import { chromium } from 'playwright';
import fs from 'fs';
(async () => {
    const browser = await chromium.launch();
    const page = await browser.newPage();
    const logs = [];
    page.on('console', msg => logs.push('BROWSER CONSOLE: ' + msg.type() + ' ' + msg.text()));
    page.on('pageerror', error => logs.push('PAGE ERROR: ' + error.message));
    console.log('Navigating to http://localhost:8080');
    await page.goto('http://localhost:8080');
    await page.waitForTimeout(4000);
    fs.writeFileSync('err.txt', logs.join('\n'));
    await browser.close();
})();
