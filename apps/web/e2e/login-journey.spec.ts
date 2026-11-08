import { test, expect } from '@playwright/test';

test.describe('Student Authentication Journey', () => {
  test('user can view login page, fill credentials, access dashboard, stay logged in across refresh, and log out', async ({ page }) => {
    // Intercept backend auth calls for isolated E2E assertion
    await page.route('**/api/v1/auth/login', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'fake-jwt-access-token',
          token_type: 'bearer',
          user: {
            id: '11111111-2222-3333-4444-555555555555',
            email: 'student@example.com',
            role: 'student',
            is_verified: true,
            created_at: new Date().toISOString(),
            profile: {
              id: '22222222-3333-4444-5555-666666666666',
              full_name: 'Alex Student',
              citizenship: 'US',
              target_countries: ['DE', 'CA'],
              fields_of_interest: ['Computer Science'],
              target_degree_level: 'masters',
              timezone: 'UTC',
            },
          },
        }),
      });
    });

    await page.route('**/api/v1/auth/refresh', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          access_token: 'fake-refreshed-jwt-token',
          token_type: 'bearer',
        }),
      });
    });

    await page.route('**/api/v1/users/me', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({
          id: '11111111-2222-3333-4444-555555555555',
          email: 'student@example.com',
          role: 'student',
          is_verified: true,
          created_at: new Date().toISOString(),
          profile: {
            id: '22222222-3333-4444-5555-666666666666',
            full_name: 'Alex Student',
            citizenship: 'US',
            target_countries: ['DE', 'CA'],
            fields_of_interest: ['Computer Science'],
            target_degree_level: 'masters',
            timezone: 'UTC',
          },
        }),
      });
    });

    await page.route('**/api/v1/auth/logout', async (route) => {
      await route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ message: 'Successfully logged out.' }),
      });
    });

    // 1. Visit Login Page
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: /Sign in to OpportunityAbroad/i })).toBeVisible();

    // 2. Fill credentials
    await page.getByLabel(/Email address/i).fill('student@example.com');
    await page.getByLabel(/Password/i).fill('Password123!');

    // 3. Submit Login
    await page.getByRole('button', { name: /Sign In/i }).click();

    // 4. Verify redirected to Dashboard and user info is visible
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.getByText(/Alex Student/i)).toBeVisible();
    await expect(page.getByText(/Role: Student/i)).toBeVisible();

    // 5. Page Refresh test: reload and verify staying logged in
    await page.reload();
    await expect(page).toHaveURL(/.*dashboard/);
    await expect(page.getByText(/Alex Student/i)).toBeVisible();

    // 6. Log out
    await page.getByRole('button', { name: /Log out/i }).click();

    // 7. Verify logged out and redirected to login or home
    await expect(page).toHaveURL(/.*login/);
  });
});

