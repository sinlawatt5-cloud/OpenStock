import { expect, test } from '@playwright/test'

test('dashboard loads indices, movers and the news summary', async ({ page }) => {
  await page.goto('/')
  await expect(page.locator('h1')).toHaveText('ภาพรวมตลาดสหรัฐ')
  await expect(page.locator('.index-card')).toHaveCount(5, { timeout: 30_000 })
  await expect(page.locator('.board-row').first()).toBeVisible({ timeout: 30_000 })
  await expect(page.locator('.summary-text')).toBeVisible({ timeout: 30_000 })
  await expect(page.locator('.summary-text')).not.toBeEmpty()
  expect(await page.locator('.board').count()).toBe(3)
})

test('search opens a symbol page with four support/resistance levels', async ({ page }) => {
  await page.goto('/')
  await page.getByRole('button', { name: 'ค้นหาหุ้น' }).click()
  const input = page.getByLabel('คำค้นหา')
  await input.fill('NVDA')
  await page.locator('.dialog-row', { hasText: 'NVDA' }).first().click()

  await expect(page).toHaveURL(/\/symbol\/NVDA/)
  await expect(page.locator('h1')).toContainText('เอ็นวิเดีย', { timeout: 30_000 })
  await expect(page.locator('.level-price')).toHaveCount(4, { timeout: 30_000 })
  await expect(page.locator('.level-card.res')).toHaveCount(2)

  const levelPrices = (await page.locator('.level-price').allTextContents()).map((value) =>
    Number(value.replace(/,/g, '')),
  )
  const current = Number((await page.locator('.price-big').innerText()).replace(/,/g, ''))
  expect(levelPrices[0]).toBeLessThan(current)
  expect(levelPrices[1]).toBeLessThan(current)
  expect(levelPrices[2]).toBeGreaterThan(current)
  expect(levelPrices[3]).toBeGreaterThan(current)

  await page.getByRole('checkbox').first().uncheck()
  await expect(page.locator('.level-card')).toHaveCount(0)
})

test('watchlist persists after reload', async ({ page }) => {
  await page.goto('/watchlist')
  await expect(page.locator('h1')).toHaveText('Watchlist ของคุณ')
  await page.locator('.suggest-card', { hasText: 'AAPL' }).first().click()
  await expect(page.locator('.watch-table')).toContainText('AAPL')
  await page.reload()
  await expect(page.locator('.watch-table')).toContainText('AAPL')
  await expect(page.locator('h1')).toBeVisible()
})

test('flow filters update the URL and the board', async ({ page }) => {
  await page.goto('/flows')
  await expect(page.locator('.flow-row').first()).toBeVisible({ timeout: 30_000 })
  const initialRows = await page.locator('.flow-row').count()
  expect(initialRows).toBeGreaterThan(5)

  await page.getByRole('button', { name: 'ไหลออก', exact: true }).click()
  await expect(page).toHaveURL(/mode=outflow/)
  // Outflow mode must only keep negative rows, whatever the market does today.
  const outflowPcts = await page.locator('.flow-pct').allTextContents()
  for (const value of outflowPcts) {
    expect(Number(value.replace('%', '').replace('+', ''))).toBeLessThan(0)
  }
  await expect(page.locator('.flow-summary')).toBeVisible({ timeout: 30_000 })

  await page.getByRole('button', { name: 'ภาพใหญ่', exact: true }).click()
  await expect(page).toHaveURL(/group=broad/)
  // Back to the full board so the SPY benchmark row is always present.
  await page.locator('.segmented').first().getByRole('button', { name: 'ทั้งหมด', exact: true }).click()
  await expect(page).toHaveURL(/mode=all/)
  await expect(page.locator('.flow-row--bench')).toHaveCount(1)
})

test('mobile keeps the brand and stacks the dashboard', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 })
  await page.goto('/')
  await expect(page.locator('.brand-mark')).toBeVisible()
  await expect(page.locator('.brand-name')).toBeHidden()
  const overflow = await page.evaluate(
    () => document.documentElement.scrollWidth - document.documentElement.clientWidth,
  )
  expect(overflow).toBeLessThanOrEqual(1)
})

test('flows shows the risk-on panel with six signals for the broad view', async ({ page }) => {
  const errors: string[] = []
  page.on('console', (message) => {
    if (message.type() === 'error') errors.push(message.text())
  })

  await page.goto('/flows?group=broad&range=1w')
  await expect(page.locator('.risk-panel')).toBeVisible({ timeout: 30_000 })
  await expect(page.locator('.risk-signal')).toHaveCount(6, { timeout: 30_000 })
  await expect(page.locator('.risk-score strong')).toHaveText(/^\d+\/6$/)
  await expect(page.locator('.risk-note')).toContainText('ไม่ใช่ยอดเงินไหลเข้า/ออกกองทุนจริง')

  // The panel must disappear for a non-broad group.
  await page.goto('/flows?group=sectors&range=1w')
  await expect(page.locator('.flow-row').first()).toBeVisible({ timeout: 30_000 })
  await expect(page.locator('.risk-panel')).toHaveCount(0)

  expect(errors).toEqual([])
})
