import { expect, test } from '@playwright/test';
import { mockGoogleOAuthSession, navigateTo, waitForApiCalls } from './helpers';

test.describe('Dashboard', () => {
	test.beforeEach(async ({ page }) => {
		// Mock authenticated session for all tests
		await mockGoogleOAuthSession(page);
	});

	test('should display dashboard page', async ({ page }) => {
		await navigateTo(page, '/dashboard');

		// Wait for page to fully load
		await waitForApiCalls(page);

		// Check page title
		await expect(page.locator('text=Dashboard')).toBeVisible();
	});

	test('should display statistics', async ({ page }) => {
		await navigateTo(page, '/dashboard');
		await waitForApiCalls(page);

		// Check for statistics sections
		const statElements = page.locator('[class*="stat"]');
		const count = await statElements.count();

		// Should have at least some statistics displayed
		expect(count).toBeGreaterThan(0);
	});

	test('should have navigation links to main sections', async ({ page }) => {
		await navigateTo(page, '/dashboard');
		await waitForApiCalls(page);

		// Check for sidebar navigation
		const sidebar = page.locator('nav');
		await expect(sidebar).toBeVisible();

		// Check for common navigation items
		const hasSessionsLink = (await page.locator('a:has-text("Sessions")').count()) > 0;
		const hasAttendanceLink = (await page.locator('a:has-text("Attendance")').count()) > 0;
		const hasLocationsLink = (await page.locator('a:has-text("Locations")').count()) > 0;

		expect(hasSessionsLink || hasAttendanceLink || hasLocationsLink).toBeTruthy();
	});

	test('should have logout button', async ({ page }) => {
		await navigateTo(page, '/dashboard');
		await waitForApiCalls(page);

		// Find logout button (may be in menu or directly visible)
		const logoutButton = page.locator(
			'button:has-text("Logout"), button:has-text("Sign Out"), [aria-label*="logout" i]',
		);

		// At least one logout option should exist
		const count = await logoutButton.count();
		expect(count).toBeGreaterThan(0);
	});

	test('should be responsive on mobile', async ({ page }) => {
		// Set mobile viewport
		await page.setViewportSize({ width: 375, height: 667 });

		await navigateTo(page, '/dashboard');
		await waitForApiCalls(page);

		// Page should still render
		await expect(page.locator('text=Dashboard')).toBeVisible();
	});
});
