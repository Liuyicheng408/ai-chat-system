import puppeteer from 'puppeteer-core'

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const SHOTS = 'C:\\Users\\lyc20\\Documents\\deepseek-harness\\default-workspace\\shots\\'
const wait = (ms) => new Promise((r) => setTimeout(r, ms))

const browser = await puppeteer.launch({
  executablePath: EDGE, headless: 'new', args: ['--no-sandbox'],
  defaultViewport: { width: 1440, height: 900 },
})
const page = await browser.newPage()
page.on('pageerror', (e) => console.log('[pageerror]', e.message))

async function pickModel(keyword) {
  await page.click('.model-select')
  await wait(600)
  const opts = await page.$$('.el-select-dropdown__item')
  for (const o of opts) {
    const box = await o.boundingBox()
    if (!box) continue
    const t = await o.evaluate((el) => el.textContent)
    if (t.includes(keyword)) {
      await page.mouse.click(box.x + box.width / 2, box.y + box.height / 2)
      return true
    }
  }
  return false
}

async function ask(text, waitMs) {
  await page.type('.composer-input textarea', text)
  await wait(150)
  await page.click('.send-btn')
  await wait(waitMs)
}

await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2' })
await wait(700)
await page.type('input[autocomplete="username"]', 'student')
await page.type('input[autocomplete="current-password"]', 'Passw0rd123')
await page.click('.submit-btn')
await page.waitForFunction(() => location.pathname === '/', { timeout: 20000 })
await wait(4200)

await page.click('.new-chat')
await wait(800)

// 1) 远端模型
await pickModel('DeepSeek')
await wait(600)
await ask('用一句话解释什么是 LoRA', 9000)

// 2) 切到本地微调模型
await pickModel('course-assistant-lora')
await wait(800)
await ask('它和全量微调相比有什么优势？', 16000)

await page.screenshot({ path: SHOTS + 'demo-mixed.png' })
const bubbles = await page.$$eval('.bubble-ai', (els) => els.map((e) => e.textContent.trim().slice(0, 50)))
console.log('AI 回复:', JSON.stringify(bubbles, null, 1))

// 3) 深色版留档
await page.evaluate(() => localStorage.setItem('theme', 'dark'))
await page.reload({ waitUntil: 'networkidle2' })
await wait(2000)
await page.screenshot({ path: SHOTS + 'demo-mixed-dark.png' })
await page.evaluate(() => localStorage.setItem('theme', 'light'))
await browser.close()
