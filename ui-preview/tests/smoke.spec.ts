import { test, expect } from '@playwright/test'

test('loads dashboard and shows nav', async ({ page }) => {
  await page.goto('/')
  await expect(page.getByText('BERHAN ERP — UI Preview')).toBeVisible()
  await expect(page.getByRole('button', { name: 'Inventory' })).toBeVisible()
})
