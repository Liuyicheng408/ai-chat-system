import puppeteer from 'puppeteer-core'

const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const SHOTS = 'C:\\Users\\lyc20\\Documents\\deepseek-harness\\default-workspace\\shots\\'

const browser = await puppeteer.launch({
  executablePath: EDGE,
  headless: 'new',
  args: ['--no-sandbox', '--window-size=1440,900'],
  defaultViewport: { width: 1440, height: 900 },
})
const page = await browser.newPage()
page.on('console', (m) => {
  if (m.type() === 'error') console.log('[console.error]', m.text())
})
page.on('pageerror', (e) => console.log('[pageerror]', e.message))

await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2' })
await new Promise((r) => setTimeout(r, 800))

await page.click('input[autocomplete="username"]')
await page.type('input[autocomplete="username"]', 'student', { delay: 30 })
await page.click('input[autocomplete="current-password"]')
await page.type('input[autocomplete="current-password"]', 'Passw0rd123', { delay: 30 })
await page.screenshot({ path: SHOTS + 'login-filled.png' })

await page.click('.submit-btn')
await page.waitForFunction(() => location.pathname === '/', { timeout: 20000 })
await new Promise((r) => setTimeout(r, 1200))
await page.screenshot({ path: SHOTS + 'chat-empty.png' })
console.log('chat url:', page.url())

// 新建一个会话再截图
const convs = await page.$$('.conv-item')
console.log('conversation count:', convs.length)

await page.goto('http://localhost:5173/profile', { waitUntil: 'networkidle2' })
await new Promise((r) => setTimeout(r, 900))
await page.screenshot({ path: SHOTS + 'profile.png' })
console.log('profile ok')

await browser.close()
