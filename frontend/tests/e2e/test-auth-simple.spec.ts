import { expect, test } from '@playwright/test';

test('Simple authentication test', async ({ page, context }) => {
	console.log('🔵 Starting simple auth test');

	// Step 1: Navigate to frontend
	// console.log('🟢 Navigating to frontend...');
	await page.goto('http://localhost:4324/', { waitUntil: 'domcontentloaded' });
	// console.log('✅ Frontend loaded');

	// Step 2: Request magic link
	// console.log('🟢 Requesting magic link...');
	const response = await page.evaluate(async () => {
		const resp = await fetch('http://localhost:8000/api/v1/auth/magic-link', {
			method: 'POST',
			headers: { 'Content-Type': 'application/json' },
			credentials: 'include',
			body: JSON.stringify({ email: 'test@example.com', return_to: '/account' }),
		});
		// console.log('Response status:', resp.status);
		const data = await resp.json();
		// console.log('Response data:', data);
		return {
			status: resp.status,
			data: data,
		};
	});

	// console.log('Magic link response:', response);
	const token = response.data.debugToken;
	expect(token).toBeDefined();
	// console.log('✅ Got token:', token);

	// Step 3: Try to consume the token
	// console.log('🟢 Consuming token...');
	const consumeUrl = `http://localhost:8000/api/v1/auth/magic-link/consume?token=${token}&returnTo=/account`;
	await page.goto(consumeUrl, { waitUntil: 'load', timeout: 10000 });

	// Step 4: Check where we ended up
	// console.log('🟢 Checking current URL...');
	const currentUrl = page.url();
	// console.log('Current URL:', currentUrl);

	// Step 5: Check cookies
	// console.log('🟢 Checking cookies...');
	await context.cookies();
	// console.log('Cookies:', cookies);

	// Step 6: Try to access the account page
	// console.log('🟢 Trying to access account page...');
	if (currentUrl.includes('login')) {
		// console.log('❌ Still on login page, authentication failed');
		throw new Error('Authentication failed - still on login page');
	}

	// console.log('✅ Authentication successful');
});
