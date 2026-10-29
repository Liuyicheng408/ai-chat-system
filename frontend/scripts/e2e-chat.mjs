import puppeteer from 'puppeteer-core'

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const SHOTS = 'C:\\Users\\lyc20\\Documents\\deepseek-harness\\default-workspace\\shots\\'

const browser = await puppeteer.launch({
  executablePath: EDGE,
  headless: 'new',
  args: ['--no-sandbox'],
  defaultViewport: { width: 1440, height: 900 },
})
const page = await browser.newPage()
page.on('pageerror', (e) => console.log('[pageerror]', e.message))
page.on('console', (m) => {
  if (m.type() === 'error' && !m.text().includes('favicon')) console.log('[console]', m.text())
})

const wait = (ms) => new Promise((r) => setTimeout(r, ms))

await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2' })
await wait(600)
await page.type('input[autocomplete="username"]', 'student')
await page.type('input[autocomplete="current-password"]', 'Passw0rd123')
await page.click('.submit-btn')
await page.waitForFunction(() => location.pathname === '/', { timeout: 20000 })
await wait(1000)

// 新建对话
await page.click('.new-chat')
await wait(800)

// 发送消息
await page.type('.composer-input textarea', '你好，简单介绍一下你自己')
await wait(200)
await page.click('.send-btn')
await wait(4000)
await page.screenshot({ path: SHOTS + 'chat-error.png' })

// 深色模式
await page.evaluate(() => localStorage.setItem('theme', 'dark'))
await page.reload({ waitUntil: 'networkidle2' })
await wait(1200)
await page.screenshot({ path: SHOTS + 'chat-dark.png' })

console.log('done')
await browser.close()
