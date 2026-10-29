import puppeteer from 'puppeteer-core'

const url = process.argv[2]
const out = process.argv[3]
const full = process.argv[4] !== 'viewport'

const browser = await puppeteer.launch({
  executablePath: 'C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
  headless: 'new',
  args: ['--no-sandbox'],
  defaultViewport: { width: 1440, height: 900 },
})
const page = await browser.newPage()
await page.goto(url, { waitUntil: 'networkidle2' })
await new Promise((r) => setTimeout(r, 1500))
// 触发所有滚动动画
await page.evaluate(async () => {
  const step = window.innerHeight * 0.8
  for (let y = 0; y < document.body.scrollHeight; y += step) {
    window.scrollTo(0, y)
    await new Promise((r) => setTimeout(r, 220))
  }
  window.scrollTo(0, 0)
})
await new Promise((r) => setTimeout(r, 900))
await page.screenshot({ path: out, fullPage: full })
console.log('saved', out)
await browser.close()
