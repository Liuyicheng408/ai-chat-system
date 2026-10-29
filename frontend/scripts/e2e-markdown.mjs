import puppeteer from 'puppeteer-core'
const EDGE = 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe'
const SHOTS = 'C:\\Users\\lyc20\\Documents\\deepseek-harness\\default-workspace\\shots\\'
const wait = (ms) => new Promise((r) => setTimeout(r, ms))

const browser = await puppeteer.launch({ executablePath: EDGE, headless: 'new', args: ['--no-sandbox'], defaultViewport: { width: 1440, height: 900 } })
const page = await browser.newPage()
await page.goto('http://localhost:5173/login', { waitUntil: 'networkidle2' })
await wait(700)
await page.type('input[autocomplete="username"]', 'student')
await page.type('input[autocomplete="current-password"]', 'Passw0rd123')
await page.click('.submit-btn')
await page.waitForFunction(() => location.pathname === '/', { timeout: 20000 })
await wait(1200)

await page.click('.new-chat')
await wait(900)

// 先发一条短消息，确保模型已加载
await page.type('.composer-input textarea', '你好')
await wait(150)
await page.click('.send-btn')
await wait(14000)

await page.type('.composer-input textarea', '用 Python 写一个冒泡排序函数，并用 markdown 代码块输出，再列三条注意事项')
await wait(150)
await page.click('.send-btn')

// 生成 3 秒后点停止
await wait(3000)
const stopBtn = await page.$('.stop-btn')
if (stopBtn) {
  await stopBtn.click()
  console.log('clicked stop')
}
await wait(1500)
const state = await page.evaluate(() => ({
  hasStop: !!document.querySelector('.stop-btn'),
  hasSend: !!document.querySelector('.send-btn'),
  aiText: Array.from(document.querySelectorAll('.bubble-ai')).map((e) => e.textContent.length),
}))
console.log('after stop:', JSON.stringify(state))
await page.screenshot({ path: SHOTS + 'stop-test.png' })
await browser.close()
