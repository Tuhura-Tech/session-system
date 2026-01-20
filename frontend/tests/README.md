# End-to-End Testing with Playwright

This directory contains Playwright end-to-end tests for the Tūhura Tech Sessions frontend.

## Prerequisites

Before running the tests, ensure:

1. **Backend API is running** on `http://localhost:8000`
   ```bash
   cd backend
   docker-compose up
   ```

2. **Frontend dev server is running** on `http://localhost:4324`
   ```bash
   cd frontend
   npm run dev
   ```

## Running Tests

### Using nix-shell (Recommended)

The nix-shell provides all necessary dependencies for Playwright tests:

```bash
# Activate nix-shell
nix-shell ../shell.nix

# Run all tests
npm run test:e2e

# Run specific test file
npm run test:e2e -- auth-integration.spec.ts

# Run tests matching a pattern
npm run test:e2e -- --grep "should display login"

# Run tests in UI mode (interactive)
npm run test:e2e:ui
```

### Without nix-shell

If you have Playwright installed globally or locally:

```bash
# Install Playwright browsers (first time only)
npx playwright install chromium

# Run tests
npm run test:e2e
```

## Test Structure

### `auth-integration.spec.ts`
Comprehensive integration tests for the authentication and signup flow:
- **Magic Link Authentication**: Login page validation, email format checks, API request verification
- **Access Control**: Protected route redirects for unauthenticated users
- **Account Management**: Profile editing, child management (stub tests)
- **Signup Flow**: Session selection and form submission (stub tests)

## Configuration

Tests are configured in `playwright.config.ts`:
- **Base URL**: `http://localhost:4324` (configurable via `PLAYWRIGHT_BASE_URL` env var)
- **Browser**: Chromium (headless)
- **Timeout**: Default Playwright timeouts
- **Web Server**: Disabled (expects dev server to be running separately)

## Test Data

Tests use dynamically generated test data to avoid conflicts:
- Email addresses: `test-{timestamp}-{random}@test.local`
- Child names: `Test Child {timestamp}`
- Parent names: `Test Parent {timestamp}`

## Current Test Coverage

### ✅ Fully Implemented Tests
- Login page UI and validation
- Email format validation (HTML5)
- Magic link request API calls
- ReturnTo parameter handling
- Error handling and user feedback
- Protected route redirects
- Form state management

### 📝 Stub Tests (Documentation Only)
These tests document the expected behavior but require authentication setup:
- Account page profile management
- Child creation and listing
- Signup form submission
- Logout functionality

## Implementing Full Authentication Tests

To implement the stub tests, you'll need:

1. **Magic Link Token Extraction**: 
   - Use backend debug mode to get tokens from API response
   - Or integrate with a test email service (Mailhog, Mailtrap)
   - Or create a test-only API endpoint to generate valid session tokens

2. **Session Cookie Management**:
   - Store session cookies after magic link consumption
   - Reuse cookies across tests for performance

3. **Database Seeding**:
   - Create test sessions with known IDs
   - Pre-populate test data for consistent testing

Example:
```typescript
// Setup authenticated session
test.beforeEach(async ({ page, context }) => {
  // Option 1: Use magic link flow with debug token
  const { debugToken } = await requestMagicLink(email, '/account');
  await page.goto(`/api/v1/auth/magic-link/consume?token=${debugToken}`);
  
  // Option 2: Set session cookie directly (if you have a test helper)
  await context.addCookies([{
    name: 'caregiver_session',
    value: 'test-session-token',
    domain: 'localhost',
    path: '/',
  }]);
});
```

## Troubleshooting

### Tests fail with "ERR_CONNECTION_REFUSED"
- Ensure the frontend dev server is running on port 4324
- Check `PLAYWRIGHT_BASE_URL` matches your dev server port

### Tests timeout or hang
- Ensure the backend API is running and accessible
- Check CORS configuration includes `http://localhost:4324`
- Verify database is seeded with test data

### Playwright browser not found
- Run `nix-shell ../shell.nix` to activate the environment
- Or install browsers: `npx playwright install chromium`

### Library errors (libglib-2.0.so.0 not found)
- Always run tests within nix-shell: `nix-shell ../shell.nix --run "npm run test:e2e"`

## CI/CD Integration

For continuous integration:

```bash
# Set environment variables
export PLAYWRIGHT_BASE_URL=http://localhost:4324
export PUBLIC_API_BASE_URL=http://localhost:8000

# Start services in background
docker-compose up -d
npm run dev &

# Wait for services to be ready
npx wait-on http://localhost:8000/health http://localhost:4324

# Run tests
npm run test:e2e

# Cleanup
docker-compose down
```

## Debugging Tests

### View test reports
```bash
npx playwright show-report
```

### Run with headed browser
```bash
npm run test:e2e -- --headed
```

### Debug mode
```bash
npm run test:e2e -- --debug
```

### Verbose output
```bash
npm run test:e2e -- --reporter=line
```

## Next Steps

1. Implement magic link token extraction for full auth tests
2. Add visual regression testing for UI components
3. Add accessibility testing with @playwright/test
4. Implement API mocking for offline testing
5. Add performance testing (Lighthouse CI)
