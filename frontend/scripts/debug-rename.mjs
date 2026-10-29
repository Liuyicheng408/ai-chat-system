import puppeteer from 'puppeteer-core'
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const wait = (ms) => new Promise((r) => setTimeout(r, ms))
const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'], defaultViewport: { width: 1440, height: 900 } })
const page = await browser.newPage()
page.on('pageerror', (e) => console.log('[err]', e.message))
await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2' })
await wait(600)
await page.type('input[autocomplete="username"]', 'student')
await page.type('input[autocomplete="current-password"]', 'Passw0rd123')
await page.click('.submit-btn')
await page.waitForFunction(() => location.pathname === '/', { timeout: 20000 })
await wait(1200)
const first = await page.$('.conv-item')
await first.hover()
await wait(300)
await first.$eval('.conv-more', (el) => el.click())
await wait(700)

const handles = await page.$$('.el-dropdown-menu__item')
for (const h of handles) {
  const box = await h.boundingBox()
  if (box) {
    const text = await h.evaluate((el) => el.textContent.trim())
    console.log('visible item:', text, JSON.stringify(box))
    if (text.includes('重命名')) {
      await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2)
      break
    }
  }
}
await wait(1000)
console.log('conv-rename count:', await page.$$eval('.conv-rename', (e) => e.length))
await page.screenshot({ path: 'C:\\Users\\lyc20\\Documents\\deepseek-harness\\default-workspace\\shots\\debug-rename.png' })
await browser.close()
