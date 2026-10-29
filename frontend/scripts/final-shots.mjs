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
await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2' })
await wait(800)
await page.screenshot({ path: SHOTS + 'final-login.png' })

await page.type('input[autocomplete="username"]', 'student')
await page.type('input[autocomplete="current-password"]', 'Passw0rd123')
await page.click('.submit-btn')
await page.waitForFunction(() => location.pathname === '/', { timeout: 20000 })
await wait(1500)
await page.screenshot({ path: SHOTS + 'final-chat.png' })

await page.evaluate(() => localStorage.setItem('theme', 'dark'))
await page.reload({ waitUntil: 'networkidle2' })
await wait(1500)
await page.screenshot({ path: SHOTS + 'final-chat-dark.png' })

await page.goto('http://localhost:5173/profile', { waitUntil: 'networkidle2' })
await wait(1000)
await page.screenshot({ path: SHOTS + 'final-profile.png' })

await page.evaluate(() => localStorage.setItem('theme', 'light'))
console.log('shots done')
await browser.close()
