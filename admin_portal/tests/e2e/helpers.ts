import { Page, expect } from '@playwright/test'

/**
 * Helper functions for Playwright tests
 */

/**
 * Wait for API requests to complete
 */
export async function waitForApiCalls(page: Page, timeout = 5000) {
  await page.waitForLoadState('networkidle', { timeout })
}

/**
 * Mock Google OAuth callback
 * Sets the session cookie to bypass actual Google OAuth in tests
 */
export async function mockGoogleOAuthSession(page: Page) {
  // Mock the session check API to return authenticated
  await page.route('**/api/v1/admin/auth/me', async (route) => {
    await route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify({ authenticated: true }),
    })
  })
  
  // Set admin session cookie
  await page.context().addCookies([
    {
      name: 'admin_session',
      value: 'test-session-token-' + Date.now(),
      domain: 'localhost',
      path: '/',
      httpOnly: true,
      sameSite: 'Lax',
      expires: Math.floor(Date.now() / 1000) + 86400, // 24 hours
    },
  ])
}

/**
 * Navigate to page and wait for load
 */
export async function navigateTo(page: Page, url: string) {
  await page.goto(url)
  await page.waitForLoadState('domcontentloaded')
}

/**
 * Fill form and submit
 */
export async function fillFormAndSubmit(
  page: Page,
  formData: Record<string, string>,
  submitButtonSelector = 'button[type="submit"]'
) {
  // Fill each field
  for (const [selector, value] of Object.entries(formData)) {
    const field = page.locator(selector)
    await field.fill(value)
  }

  // Submit form
  await page.locator(submitButtonSelector).click()

  // Wait for navigation or API response
  await page.waitForLoadState('networkidle')
}

/**
 * Check if element is visible and contains text
 */
export async function expectElementWithText(
  page: Page,
  selector: string,
  text: string
) {
  const element = page.locator(selector)
  await element.isVisible()
  await expect(element).toContainText(text)
}

/**
 * Get table data as array of objects
 */
export async function getTableData(page: Page, tableSelector = 'table') {
  const rows = await page.locator(`${tableSelector} tbody tr`).all()
  const data = []

  for (const row of rows) {
    const cells = await row.locator('td').allTextContents()
    data.push(cells)
  }

  return data
}

/**
 * Click button by text
 */
export async function clickButtonByText(page: Page, text: string) {
  await page.locator(`button:has-text("${text}")`).click()
  await page.waitForLoadState('networkidle')
}

/**
 * Wait for notification/toast
 */
export async function waitForNotification(page: Page, text: string, timeout = 5000) {
  await page.locator(`text=${text}`).isVisible({ timeout })
}
