import { chromium } from '@playwright/test'

const [
  url = 'http://127.0.0.1:5173/',
  out = '../screenshots/shot.png',
  w = '1440',
  h = '1100',
  waitFor = '.board-row',
  watch = '',
] = process.argv.slice(2)

const browser = await chromium.launch()
const page = await browser.newPage({
  viewport: { width: Number(w), height: Number(h) },
  deviceScaleFactor: 1,
})
const errors = []
page.on('console', (message) => {
  if (message.type() === 'error') errors.push(message.text())
})
page.on('pageerror', (error) => errors.push(String(error)))
if (watch) {
  await page.addInitScript((value) => {
    localStorage.setItem('openstock:watchlist', value)
  }, JSON.stringify(watch.split(',')))
}
await page.goto(url, { waitUntil: 'networkidle' })
if (waitFor) await page.waitForSelector(waitFor, { timeout: 30000 }).catch(() => {})
await page.waitForTimeout(1200)
await page.screenshot({ path: out, fullPage: true })
await browser.close()
console.log('saved', out, errors.length ? `console errors: ${errors.length}` : 'no console errors')
if (errors.length) console.log(errors.join('\n'))
