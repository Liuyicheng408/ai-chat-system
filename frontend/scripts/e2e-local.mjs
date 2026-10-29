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

await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2' })
await wait(600)
await page.type('input[autocomplete="username"]', 'student')
await page.type('input[autocomplete="current-password"]', 'Passw0rd123')
await page.click('.submit-btn')
await page.waitForFunction(() => location.pathname === '/', { timeout: 20000 })
await wait(1200)

await page.click('.new-chat')
await wait(900)

// 打开模型下拉，选择本地模型
await page.click('.model-select')
await wait(700)
const options = await page.$$('.el-select-dropdown__item')
console.log('options:', options.length)
for (const opt of options) {
  const box = await opt.boundingBox()
  if (!box) continue
  const text = await opt.evaluate((el) => el.textContent)
  if (text.includes('Qwen')) {
    await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2)
    break
  }
}
await wait(900)
await page.screenshot({ path: SHOTS + 'local-model-selected.png' })

await page.type('.composer-input textarea', '用两句话介绍一下杭州')
await wait(200)
await page.click('.send-btn')

// 等模型加载 + 生成
await wait(20000)
await page.screenshot({ path: SHOTS + 'local-reply.png' })
const reply = await page.$$eval('.bubble-ai', (els) => els.map((e) => e.textContent.trim()))
console.log('reply:', JSON.stringify(reply).slice(0, 400))
await browser.close()
