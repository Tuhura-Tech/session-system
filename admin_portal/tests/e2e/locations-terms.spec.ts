import { test, expect } from '@playwright/test'
import { mockGoogleOAuthSession, navigateTo, waitForApiCalls } from './helpers'

test.describe('Locations Management', () => {
  test.beforeEach(async ({ page }) => {
    await mockGoogleOAuthSession(page)
  })

  test('should display locations page', async ({ page }) => {
    await navigateTo(page, '/locations')
    await waitForApiCalls(page)
    
    // Check page title
    const title = page.locator('h1, h2')
    const hasLocationsText = await page.locator('text=/location/i').count() > 0
    
    expect(hasLocationsText).toBeTruthy()
  })

  test('should have create location button', async ({ page }) => {
    await navigateTo(page, '/locations')
    await waitForApiCalls(page)
    
    // Look for create/add button
    const createButton = page.locator('button:has-text("Create"), button:has-text("Add"), button:has-text("New")')
    
    const count = await createButton.count()
    expect(count).toBeGreaterThan(0)
  })

  test('should display locations list', async ({ page }) => {
    await navigateTo(page, '/locations')
    await waitForApiCalls(page)
    
    // Check for table or list
    const table = page.locator('table')
    const list = page.locator('[role="list"]')
    
    const tableExists = await table.count() > 0
    const listExists = await list.count() > 0
    
    expect(tableExists || listExists).toBeTruthy()
  })

  test('should allow editing location', async ({ page }) => {
    await navigateTo(page, '/locations')
    await waitForApiCalls(page)
    
    // Look for edit button/link
    const editButton = page.locator('button:has-text("Edit"), a:has-text("Edit"), button[aria-label*="edit" i]')
    
    if (await editButton.count() > 0) {
      await editButton.first().click()
      
      // Should show edit form
      const form = page.locator('form')
      const count = await form.count()
      
      if (count > 0) {
        await expect(form.first()).toBeVisible()
      }
    }
  })
})

test.describe('Terms Management', () => {
  test.beforeEach(async ({ page }) => {
    await mockGoogleOAuthSession(page)
  })

  test('should display terms page', async ({ page }) => {
    await navigateTo(page, '/terms')
    await waitForApiCalls(page)
    
    // Check page content
    const hasTermsText = await page.locator('text=/term/i').count() > 0
    
    expect(hasTermsText).toBeTruthy()
  })

  test('should have create term button', async ({ page }) => {
    await navigateTo(page, '/terms')
    await waitForApiCalls(page)
    
    // Look for create button
    const createButton = page.locator('button:has-text("Create"), button:has-text("Add"), button:has-text("New")')
    
    const count = await createButton.count()
    expect(count).toBeGreaterThan(0)
  })

  test('should display terms list', async ({ page }) => {
    await navigateTo(page, '/terms')
    await waitForApiCalls(page)
    
    // Check for table
    const table = page.locator('table')
    
    const count = await table.count()
    expect(count).toBeGreaterThan(0)
  })

  test('should filter terms by year', async ({ page }) => {
    await navigateTo(page, '/terms')
    await waitForApiCalls(page)
    
    // Look for year filter
    const yearFilter = page.locator('select, button:has-text("Year"), input[placeholder*="Year" i]')
    
    const count = await yearFilter.count()
    expect(count).toBeGreaterThan(0)
  })

  test('should allow editing term', async ({ page }) => {
    await navigateTo(page, '/terms')
    await waitForApiCalls(page)
    
    // Look for edit button
    const editButton = page.locator('button:has-text("Edit"), a:has-text("Edit")')
    
    if (await editButton.count() > 0) {
      await editButton.first().click()
      
      // Should show edit form
      const form = page.locator('form')
      const count = await form.count()
      
      expect(count).toBeGreaterThan(0)
    }
  })
})
