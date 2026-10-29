import puppeteer from 'puppeteer-core'

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const SHOTS = 'C:\\Users\\lyc20\\Documents\\deepseek-harness\\default-workspace\\shots\\'
const wait = (ms) => new Promise((r) => setTimeout(r, ms))

const browser = await puppeteer.launch({
  executablePath: EDGE,
  headless: 'new',
  args: ['--no-sandbox'],
  defaultViewport: { width: 1440, height: 900 },
})
const page = await browser.newPage()
page.on('pageerror', (e) => console.log('[pageerror]', e.message))

async function clickMenu(text) {
  const handles = await page.$$('.el-dropdown-menu__item')
  for (const h of handles) {
    const box = await h.boundingBox()
    if (!box) continue
    const label = await h.evaluate((el) => el.textContent.trim())
    if (label.includes(text)) {
      await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2)
      return true
    }
  }
  console.log('menu item not found:', text)
  return false
}

await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2' })
await wait(600)
await page.type('input[autocomplete="username"]', 'student')
await page.type('input[autocomplete="current-password"]', 'Passw0rd123')
await page.click('.submit-btn')
await page.waitForFunction(() => location.pathname === '/', { timeout: 20000 })
await wait(1200)

await page.click('.new-chat')
await wait(900)
console.log('before:', await page.$$eval('.conv-item .conv-title', (e) => e.map((x) => x.textContent)))

const first = await page.$('.conv-item')
await first.hover()
await wait(300)
await first.$eval('.conv-more', (el) => el.click())
await wait(600)
await clickMenu('重命名')
await wait(800)

const input = await page.$('.conv-rename input')
if (input) {
  await input.click({ clickCount: 3 })
  await page.keyboard.type('面试准备清单')
  await page.keyboard.press('Enter')
  await wait(1100)
} else {
  console.log('rename input missing')
}
console.log('after rename:', await page.$$eval('.conv-item .conv-title', (e) => e.map((x) => x.textContent)))
await page.screenshot({ path: SHOTS + 'crud-rename.png' })

const target = await page.$('.conv-item')
await target.hover()
await wait(300)
await target.$eval('.conv-more', (el) => el.click())
await wait(600)
await clickMenu('删除')
await wait(900)
await page.screenshot({ path: SHOTS + 'crud-confirm.png' })

const btn = await page.$('.el-message-box__btns .el-button--primary')
if (btn) {
  await btn.click()
  await wait(1400)
} else {
  console.log('confirm button not found')
}
console.log('after delete:', await page.$$eval('.conv-item .conv-title', (e) => e.map((x) => x.textContent)))
await page.screenshot({ path: SHOTS + 'crud-after.png' })
await browser.close()
