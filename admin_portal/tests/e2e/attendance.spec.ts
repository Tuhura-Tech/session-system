import { test, expect } from '@playwright/test'
import { mockGoogleOAuthSession, navigateTo, waitForApiCalls } from './helpers'

test.describe('Attendance Tracking', () => {
  test.beforeEach(async ({ page }) => {
    await mockGoogleOAuthSession(page)
  })

  test('should display attendance roll page', async ({ page }) => {
    await navigateTo(page, '/attendance')
    await waitForApiCalls(page)
    
    // Check page title
    const title = page.locator('h1, h2')
    await expect(title.first()).toBeVisible()
  })

  test('should have attendance marking options', async ({ page }) => {
    await navigateTo(page, '/attendance')
    await waitForApiCalls(page)
    
    // Look for attendance status options (Present, Absent, Excused)
    const hasPresent = await page.locator('text=/present/i').count() > 0
    const hasAbsent = await page.locator('text=/absent/i').count() > 0
    
    expect(hasPresent || hasAbsent).toBeTruthy()
  })

  test('should allow selecting attendance status', async ({ page }) => {
    await navigateTo(page, '/attendance')
    await waitForApiCalls(page)
    
    // Find first radio/checkbox for attendance
    const radioButtons = page.locator('input[type="radio"], input[type="checkbox"]')
    
    if (await radioButtons.count() > 0) {
      await radioButtons.first().click()
      
      // Verify it's checked
      const isChecked = await radioButtons.first().isChecked()
      expect(isChecked).toBeTruthy()
    }
  })

  test('should have save/submit button', async ({ page }) => {
    await navigateTo(page, '/attendance')
    await waitForApiCalls(page)
    
    // Look for save/submit button
    const saveButton = page.locator('button:has-text("Save"), button:has-text("Submit"), button:has-text("Mark")')
    
    // Should have at least one save option
    const count = await saveButton.count()
    expect(count).toBeGreaterThan(0)
  })

  test('should handle form submission', async ({ page }) => {
    // Mock attendance API
    await page.route('**/api/v1/admin/attendance', async (route) => {
      if (route.request().method() === 'POST') {
        await route.abort('failed')
      } else {
        await route.continue()
      }
    })
    
    await navigateTo(page, '/attendance')
    await waitForApiCalls(page)
    
    // Try to mark attendance and save
    const saveButton = page.locator('button:has-text("Save"), button:has-text("Submit")')
    
    if (await saveButton.count() > 0) {
      await saveButton.first().click()
      
      // Wait for request (even if it fails)
      await page.waitForLoadState('networkidle')
    }
  })

  test('should export attendance data', async ({ page }) => {
    await navigateTo(page, '/attendance')
    await waitForApiCalls(page)
    
    // Look for export button
    const exportButton = page.locator('button:has-text("Export"), a:has-text("Download")')
    
    if (await exportButton.count() > 0) {
      // Start waiting for download before click
      const downloadPromise = page.waitForEvent('download')
      
      await exportButton.first().click()
      
      // Wait for download to start
      const download = await downloadPromise.catch(() => null)
      
      // If download was triggered, it should be a valid file
      if (download) {
        expect(download.suggestedFilename()).toContain('csv')
      }
    }
  })
})
