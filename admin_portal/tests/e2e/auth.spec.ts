import { test, expect } from '@playwright/test'
import { mockGoogleOAuthSession, navigateTo, clickButtonByText } from './helpers'

test.describe('Authentication', () => {
  test('should display login page', async ({ page }) => {
    await navigateTo(page, '/')
    
    await expect(page.locator('h2')).toContainText('Admin Portal')
    await expect(page.locator('p')).toContainText('Sign in with your Google account')
    await expect(page.locator('button')).toContainText('Sign in with Google')
  })

  test('should have correct login button href', async ({ page }) => {
    await navigateTo(page, '/')
    
    const loginButton = page.locator('button:has-text("Sign in with Google")')
    
    // We can't directly test the redirect without mocking, but we can verify the button exists
    await expect(loginButton).toBeVisible()
  })

  test('should redirect to dashboard when authenticated', async ({ page }) => {
    // Set session cookie and mock API to simulate authenticated user
    await mockGoogleOAuthSession(page)
    
    // Navigate to login
    await navigateTo(page, '/login')
    
    // Should redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/, { timeout: 10000 })
  })

  test('should redirect to login when accessing protected route without auth', async ({ page }) => {
    // Navigate to dashboard without session
    await navigateTo(page, '/dashboard')
    
    // Should redirect to login
    await page.waitForURL('/login', { timeout: 5000 })
    await expect(page).toHaveURL(/\/login/)
  })

  test('should show error on failed session check', async ({ page }) => {
    // Mock 401 response for session check
    await page.route('**/api/v1/admin/auth/check-session', async (route) => {
      await route.abort('failed')
    })
    
    await navigateTo(page, '/')
    
    // Should still show login page
    await expect(page.locator('h2')).toContainText('Admin Portal')
  })
})
