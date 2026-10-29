import puppeteer from 'puppeteer-core'
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const SHOTS = 'C:\\Users\\lyc20\\Documents\\deepseek-harness\\default-workspace\\shots\\'
const wait = (ms) => new Promise((r) => setTimeout(r, ms))

const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'] })
const page = await browser.newPage()
await page.setViewport({ width: 1366, height: 768 })
await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2' })
await wait(600)
await page.type('input[autocomplete="username"]', 'student')
await page.type('input[autocomplete="current-password"]', 'Passw0rd123')
await page.click('.submit-btn')
await page.waitForFunction(() => location.pathname === '/', { timeout: 20000 })
await wait(1400)
await page.screenshot({ path: SHOTS + 'r-1366.png' })

const overflow1366 = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)
console.log('1366 overflow:', overflow1366)

await page.setViewport({ width: 390, height: 844 })
await wait(900)
await page.screenshot({ path: SHOTS + 'r-390.png' })
const overflow390 = await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth)
console.log('390 overflow:', overflow390)

// 个人站移动端
await page.goto('http://localhost:5174', { waitUntil: 'networkidle2' })
await wait(1500)
await page.screenshot({ path: SHOTS + 'r-portfolio-390.png' })
console.log('portfolio 390 overflow:', await page.evaluate(() => document.documentElement.scrollWidth > window.innerWidth))
await browser.close()
