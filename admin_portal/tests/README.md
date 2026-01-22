# Admin Portal - Playwright Tests

Comprehensive E2E testing suite using Playwright for the admin portal application.

## Setup

### Install Dependencies

```bash
pnpm install
```

Playwright and its browsers are already included in devDependencies.

### Install Playwright Browsers

```bash
pnpm exec playwright install
```

## Running Tests

### Run All Tests

```bash
pnpm test
```

### Run Tests in UI Mode (Interactive)

```bash
pnpm test:ui
```

This opens an interactive test explorer where you can:

- See all tests organized by spec
- Run individual tests
- Watch tests execute in real-time
- Step through test execution
- Inspect elements
- Replay failed tests

### Run Tests in Headed Mode (See Browser)

```bash
pnpm test:headed
```

Tests run with visible browser windows so you can watch execution.

### Run Tests in Debug Mode

```bash
pnpm test:debug
```

Launches debugger with step-through capability and Inspector tool.

### Run Specific Test File

```bash
pnpm test tests/e2e/auth.spec.ts
```

### Run Tests Matching Pattern

```bash
pnpm test -g "should display login page"
```

### Run Tests with Verbose Output

```bash
pnpm test --reporter=verbose
```

## Test Structure

```
tests/e2e/
├── helpers.ts              # Shared test utilities
├── auth.spec.ts            # Authentication tests
├── dashboard.spec.ts       # Dashboard tests
├── sessions.spec.ts        # Sessions management tests
├── attendance.spec.ts      # Attendance tracking tests
├── locations-terms.spec.ts # Locations & terms tests
└── api.spec.ts            # API integration tests
```

## Test Coverage

### Authentication (`auth.spec.ts`)

- [x] Login page display
- [x] Login button verification
- [x] Authenticated redirect to dashboard
- [x] Protected route enforcement
- [x] Session validation
- [x] Failed session handling

### Dashboard (`dashboard.spec.ts`)

- [x] Dashboard page load
- [x] Statistics display
- [x] Navigation links
- [x] Logout button presence
- [x] Mobile responsiveness

### Sessions (`sessions.spec.ts`)

- [x] Sessions list display
- [x] Search functionality
- [x] Filter options
- [x] Create session navigation
- [x] Session detail navigation
- [x] Empty state handling
- [x] Mobile responsiveness

### Attendance (`attendance.spec.ts`)

- [x] Attendance roll display
- [x] Attendance marking options
- [x] Status selection
- [x] Save/submit functionality
- [x] CSV export
- [x] Form handling

### Locations & Terms (`locations-terms.spec.ts`)

- [x] Locations page display
- [x] Create location button
- [x] Locations list display
- [x] Edit location functionality
- [x] Terms page display
- [x] Create term button
- [x] Terms list display
- [x] Year filtering
- [x] Edit term functionality

### API Integration (`api.spec.ts`)

- [x] Error handling (API failures)
- [x] 401 unauthorized handling
- [x] 500 server error handling
- [x] Request retry logic
- [x] Request headers validation
- [x] Credentials inclusion
- [x] Network timeout handling

## Configuration

### Playwright Config

`playwright.config.ts` contains:

- Test directory: `tests/e2e`
- Base URL: `http://localhost:3001`
- Browsers: Chromium, Firefox, WebKit
- Mobile viewports: Pixel 5, iPhone 12
- Screenshots: Only on failure
- Videos: Retained on failure
- Trace: On first retry
- Dev server auto-launch

### Environment Variables

Create `.env.test` if needed for test-specific configuration:

```bash
# .env.test (optional)
VITE_API_URL=http://localhost:8000
PLAYWRIGHT_HEADLESS=true
```

## Key Test Patterns

### Authentication Mocking

```typescript
await mockGoogleOAuthSession(page);
```

Sets a valid session cookie for authenticated tests.

### API Mocking

```typescript
await page.route('**/api/v1/admin/sessions', async (route) => {
	await route.continue(); // or abort, respond with custom data, etc.
});
```

### Waiting for APIs

```typescript
await waitForApiCalls(page);
```

Waits for all network requests to complete.

### Navigation

```typescript
await navigateTo(page, '/dashboard');
```

Navigates and waits for page load.

## Test Data

Tests use:

- Mocked session cookies for authentication
- Mocked API responses for data
- No actual backend data is required
- Tests are isolated and can run in any order

## CI/CD Integration

The tests are configured for CI with:

- Automatic browser installation
- Artifact collection (screenshots, videos, traces)
- HTML report generation
- Retry logic on failure
- Single worker for stability

To run in CI:

```bash
CI=true pnpm test
```

## Troubleshooting

### Tests timeout

Increase timeout in specific tests:

```typescript
test('my test', async ({ page }) => {
	await page.goto('/dashboard', { waitUntil: 'networkidle', timeout: 30000 });
});
```

### Backend not running

Tests expect backend at `http://localhost:8000`. Either:

1. Start backend: `cd ../backend && python main.py`
2. Or mock all API calls in tests

### Port already in use

If port 3001 is in use:

1. Kill process: `lsof -ti:3001 | xargs kill -9`
2. Or configure different port in `playwright.config.ts`

### Browser not installed

```bash
pnpm exec playwright install
```

### Clear test cache

```bash
rm -rf tests/.cache
rm -rf .playwright
```

## Viewing Results

### HTML Report

After tests run:

```bash
pnpm exec playwright show-report
```

Opens interactive HTML report showing:

- Test results
- Screenshots
- Videos
- Trace files (timeline)
- Error details

### Screenshots & Videos

Located in `tests/e2e/test-results/` on failure.

## Adding New Tests

1. Create new spec file: `tests/e2e/myfeature.spec.ts`
2. Import test framework and helpers:
   ```typescript
   import { test, expect } from '@playwright/test';
   import { mockGoogleOAuthSession, navigateTo } from './helpers';
   ```
3. Create test suite and cases:

   ```typescript
   test.describe('My Feature', () => {
   	test.beforeEach(async ({ page }) => {
   		await mockGoogleOAuthSession(page);
   	});

   	test('should do something', async ({ page }) => {
   		// Test implementation
   	});
   });
   ```

4. Run: `pnpm test tests/e2e/myfeature.spec.ts`

## Best Practices

1. **Use helpers** - Leverage shared utilities in `helpers.ts`
2. **Mock APIs** - Don't depend on backend state
3. **Wait properly** - Use `waitForApiCalls()` not arbitrary delays
4. **Test user flows** - Not implementation details
5. **Keep tests isolated** - Each test should be independent
6. **Use descriptive names** - Test names explain what is tested
7. **Avoid hardcoding** - Use selectors/locators properly
8. **Test mobile** - Include mobile viewport tests
9. **Handle errors** - Tests should handle API failures gracefully
10. **Document complex tests** - Add comments for non-obvious logic

## Performance Tips

1. Run tests in parallel (default): `workers: 4` in config
2. Use `fullyParallel: true` for independent tests
3. Reuse browser context when possible
4. Mock expensive API calls
5. Use retries only when necessary

## Maintenance

- Review tests monthly for flakiness
- Update selectors if UI changes
- Add tests for new features
- Remove tests for deprecated features
- Keep helpers up to date with common patterns

## Resources

- [Playwright Docs](https://playwright.dev)
- [Playwright API Reference](https://playwright.dev/docs/api/class-test)
- [Best Practices](https://playwright.dev/docs/best-practices)
- [Debugging](https://playwright.dev/docs/debug)

## Support

For issues with tests:

1. Run in debug mode: `pnpm test:debug`
2. Check HTML report: `pnpm exec playwright show-report`
3. Review test videos/traces in test results
4. Check browser console for errors
5. Verify backend is running and accessible
