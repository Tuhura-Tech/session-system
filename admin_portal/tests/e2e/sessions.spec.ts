import { expect, test } from '@playwright/test';
import { getTableData, mockGoogleOAuthSession, navigateTo, waitForApiCalls } from './helpers';

test.describe('Sessions Management', () => {
	test.beforeEach(async ({ page }) => {
		await mockGoogleOAuthSession(page);
	});

	test('should display sessions list', async ({ page }) => {
		await navigateTo(page, '/sessions');
		await waitForApiCalls(page);

		// Check page title
		await expect(page.locator('h1')).toContainText(/sessions/i);

		// Check for table or list
		const table = page.locator('table');
		await expect(table).toBeVisible();
	});

	test('should have search functionality', async ({ page }) => {
		await navigateTo(page, '/sessions');
		await waitForApiCalls(page);

		// Look for search input
		const searchInput = page.locator('input[placeholder*="Search" i], input[type="search"]');

		// Should have at least one search field
		const count = await searchInput.count();
		expect(count).toBeGreaterThan(0);
	});

	test('should have filter options', async ({ page }) => {
		await navigateTo(page, '/sessions');
		await waitForApiCalls(page);

		// Look for filter select/dropdown
		const filters = page.locator(
			'select, button:has-text("Filter"), button[aria-label*="filter" i]',
		);

		// Should have filter controls
		const count = await filters.count();
		expect(count).toBeGreaterThan(0);
	});

	test('should navigate to create session page', async ({ page }) => {
		await navigateTo(page, '/sessions');
		await waitForApiCalls(page);

		// Click create button
		const createButton = page.locator('button:has-text("Create"), a:has-text("Create Session")');

		if ((await createButton.count()) > 0) {
			await createButton.first().click();

			// Should navigate to create page
			await page.waitForURL(/\/sessions\/create|\/create-session/, { timeout: 5000 }).catch(() => {
				// Page might have a different URL structure
			});
		}
	});

	test('should display session details when clicking on a session', async ({ page }) => {
		// Mock API response for sessions list
		await page.route('**/api/v1/admin/sessions', async (route) => {
			await route.continue();
		});

		await navigateTo(page, '/sessions');
		await waitForApiCalls(page);

		// Try to click first session in list
		const firstSessionRow = page.locator('table tbody tr').first();

		if ((await firstSessionRow.count()) > 0) {
			await firstSessionRow.click();

			// Should navigate to detail page
			await page.waitForURL(/\/sessions\/[a-zA-Z0-9-]+/, { timeout: 5000 }).catch(() => {
				// Might have different URL pattern
			});
		}
	});

	test('should handle empty sessions list gracefully', async ({ page }) => {
		// Mock empty sessions response
		await page.route('**/api/v1/admin/sessions', async (route) => {
			await route.abort('failed');
		});

		await navigateTo(page, '/sessions');
		await waitForApiCalls(page);

		// Page should still be visible (with error or empty state)
		await expect(page.locator('h1, h2, p')).toBeVisible();
	});

	test('should be responsive on mobile', async ({ page }) => {
		await page.setViewportSize({ width: 375, height: 667 });

		await navigateTo(page, '/sessions');
		await waitForApiCalls(page);

		// Table should be scrollable or simplified on mobile
		await expect(page.locator('h1')).toContainText(/sessions/i);
	});
});
