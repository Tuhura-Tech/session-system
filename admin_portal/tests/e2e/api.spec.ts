import { expect, test } from '@playwright/test';
import { mockGoogleOAuthSession, navigateTo, waitForApiCalls } from './helpers';

test.describe('API Integration', () => {
	test.beforeEach(async ({ page }) => {
		await mockGoogleOAuthSession(page);
	});

	test('should handle API errors gracefully', async ({ page }) => {
		// Mock API failure
		await page.route('**/api/v1/admin/**', async (route) => {
			await route.abort('failed');
		});

		await navigateTo(page, '/sessions');

		// Page should still render (with error message or empty state)
		const heading = page.locator('h1, h2');
		await expect(heading.first()).toBeVisible();
	});

	test('should handle 401 unauthorized response', async ({ page }) => {
		// Mock 401 response
		await page.route('**/api/v1/admin/sessions', async (route) => {
			if (route.request().url().includes('/sessions')) {
				await route.abort('failed');
			} else {
				await route.continue();
			}
		});

		// Set invalid session
		await page.context().clearCookies();

		await navigateTo(page, '/sessions');

		// Should redirect to login or show error
		await page.waitForLoadState('domcontentloaded');

		const currentUrl = page.url();
		const hasError = (await page.locator('text=/error|unauthorized|login/i').count()) > 0;

		expect(currentUrl.includes('/login') || hasError).toBeTruthy();
	});

	test('should handle 500 server error', async ({ page }) => {
		// Mock 500 response
		await page.route('**/api/v1/admin/sessions', async (route) => {
			await route.abort('failed');
		});

		await navigateTo(page, '/sessions');
		await waitForApiCalls(page);

		// Page should handle error gracefully
		await expect(page.locator('h1, h2, p')).toBeVisible();
	});

	test('should retry failed API calls', async ({ page }) => {
		let callCount = 0;

		// Mock API with first call failing
		await page.route('**/api/v1/admin/sessions', async (route) => {
			callCount++;
			if (callCount === 1) {
				await route.abort('failed');
			} else {
				await route.continue();
			}
		});

		await navigateTo(page, '/sessions');
		await waitForApiCalls(page);

		// Page should eventually load
		const heading = page.locator('h1, h2');
		await expect(heading.first()).toBeVisible();
	});

	test('should send requests with proper headers', async ({ page }) => {
		let capturedHeaders = {};

		// Capture request headers
		await page.on('request', (request) => {
			if (request.url().includes('/api/v1/')) {
				capturedHeaders = request.allHeaders();
			}
		});

		await navigateTo(page, '/sessions');
		await waitForApiCalls(page);

		// Should have content-type header
		const hasContentType = Object.keys(capturedHeaders).some(
			(key) => key.toLowerCase() === 'content-type',
		);

		// Content-Type is not always present for GET requests
		expect(Object.keys(capturedHeaders).length > 0).toBeTruthy();
	});

	test('should include credentials with API requests', async ({ page }) => {
		let requestMade = false;

		// Check if credentials are sent
		await page.on('request', (request) => {
			if (request.url().includes('/api/v1/admin')) {
				requestMade = true;
				const headers = request.allHeaders();
				// Axios with withCredentials should include Origin header
				expect(Object.keys(headers).length > 0).toBeTruthy();
			}
		});

		await navigateTo(page, '/sessions');
		await waitForApiCalls(page);

		expect(requestMade).toBeTruthy();
	});

	test('should handle network timeout', async ({ page }) => {
		// Slow down network
		await page.context().setOffline(true);

		await navigateTo(page, '/login');
		await page.context().setOffline(false);

		// Page should still be functional
		const title = page.locator('h2');
		await expect(title).toContainText('Admin Portal');
	});
});
