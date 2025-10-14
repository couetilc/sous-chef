import { describe, it, expect, beforeAll } from 'vitest';
import { Api } from './useApi.jsx';

/**
 * Integration tests for the Api class against a real Django backend.
 *
 * Prerequisites:
 * - Backend must be running (docker compose up backend db)
 * - Backend should be accessible at http://backend:8000 (from Docker) or http://localhost:8000 (from host)
 *
 * Run with: docker compose run frontend pnpm test:integration
 */

// Use backend service name when running in Docker, localhost otherwise
const BACKEND_URL = process.env.BACKEND_URL || 'http://backend:8000';
const TEST_USERNAME = `testuser_${Date.now()}`;
const TEST_EMAIL = `${TEST_USERNAME}@example.com`;
const TEST_PASSWORD = 'TestPassword123!';

describe('Api Integration Tests', () => {
  let originalFetch;

  beforeAll(async () => {
    // Save original fetch for all tests
    originalFetch = global.fetch;

    // Check if backend is available
    try {
      const response = await originalFetch(`${BACKEND_URL}/api/`);
      if (!response.ok) {
        throw new Error('Backend responded with error');
      }
    } catch (error) {
      throw new Error(
        `Backend is not available at ${BACKEND_URL}. ` +
        'Please start it with: docker compose up -d backend db'
      );
    }
  });

  describe('CSRF Token Management', () => {
    it('should fetch CSRF token from backend', async () => {
      // Override fetch to use real backend
      global.fetch = (url, options) => {
        const fullUrl = url.startsWith('/') ? `${BACKEND_URL}${url}` : url;
        return originalFetch(fullUrl, options);
      };

      const api = new Api();
      await api.becomeReady();

      expect(api.isReady()).toBe(true);
      expect(api.csrfToken).toBeDefined();
      expect(api.csrfToken).not.toBe('');
    });

    it('should handle multiple concurrent CSRF requests efficiently', async () => {
      global.fetch = (url, options) => {
        const fullUrl = url.startsWith('/') ? `${BACKEND_URL}${url}` : url;
        return originalFetch(fullUrl, options);
      };

      const api = new Api();

      // Make multiple concurrent calls
      await Promise.all([
        api.becomeReady(),
        api.becomeReady(),
        api.becomeReady(),
      ]);

      expect(api.isReady()).toBe(true);
      expect(api.csrfToken).toBeDefined();
    });
  });

  describe('User Registration Flow', () => {
    it('should successfully register a new user', async () => {
      global.fetch = (url, options) => {
        const fullUrl = url.startsWith('/') ? `${BACKEND_URL}${url}` : url;
        return originalFetch(fullUrl, options);
      };

      const api = new Api();

      const result = await api.register({
        username: TEST_USERNAME,
        email: TEST_EMAIL,
        password: TEST_PASSWORD,
        password_confirm: TEST_PASSWORD,
        first_name: 'Test',
        last_name: 'User'
      });

      expect(result).toBeDefined();
      expect(result.username).toBe(TEST_USERNAME);
      expect(result.email).toBe(TEST_EMAIL);
      expect(result.first_name).toBe('Test');
      expect(result.last_name).toBe('User');
    });

    it('should reject registration with mismatched passwords', async () => {
      global.fetch = (url, options) => {
        const fullUrl = url.startsWith('/') ? `${BACKEND_URL}${url}` : url;
        return originalFetch(fullUrl, options);
      };

      const api = new Api();

      await expect(api.register({
        username: `testuser_mismatch_${Date.now()}`,
        email: 'mismatch@example.com',
        password: 'Password123!',
        password_confirm: 'DifferentPassword123!',
        first_name: 'Test',
        last_name: 'User'
      })).rejects.toThrow();
    });

    it('should reject duplicate username registration', async () => {
      global.fetch = (url, options) => {
        const fullUrl = url.startsWith('/') ? `${BACKEND_URL}${url}` : url;
        return originalFetch(fullUrl, options);
      };

      const api = new Api();

      // Try to register with the same username again
      await expect(api.register({
        username: TEST_USERNAME,
        email: `different_${TEST_EMAIL}`,
        password: TEST_PASSWORD,
        password_confirm: TEST_PASSWORD,
        first_name: 'Test',
        last_name: 'User'
      })).rejects.toThrow();
    });
  });

  describe('Login Flow', () => {
    it('should successfully login with valid credentials', async () => {
      global.fetch = (url, options) => {
        const fullUrl = url.startsWith('/') ? `${BACKEND_URL}${url}` : url;
        return originalFetch(fullUrl, options);
      };

      const api = new Api();

      const result = await api.login({
        username: TEST_USERNAME,
        password: TEST_PASSWORD
      });

      expect(result).toBeDefined();
      expect(result.username).toBe(TEST_USERNAME);
      expect(result.id).toBeDefined();
    });

    it('should reject login with invalid password', async () => {
      global.fetch = (url, options) => {
        const fullUrl = url.startsWith('/') ? `${BACKEND_URL}${url}` : url;
        return originalFetch(fullUrl, options);
      };

      const api = new Api();

      await expect(api.login({
        username: TEST_USERNAME,
        password: 'WrongPassword123!'
      })).rejects.toMatchObject({
        status: 401
      });
    });

    it('should reject login with non-existent user', async () => {
      global.fetch = (url, options) => {
        const fullUrl = url.startsWith('/') ? `${BACKEND_URL}${url}` : url;
        return originalFetch(fullUrl, options);
      };

      const api = new Api();

      await expect(api.login({
        username: 'nonexistent_user_12345',
        password: 'SomePassword123!'
      })).rejects.toMatchObject({
        status: 401
      });
    });
  });

  describe('Full Authentication Flow', () => {
    // Note: This test may fail in test environments due to cookie handling limitations.
    // In a real browser, session cookies are maintained automatically.
    it.skip('should complete register → login → authenticated request flow', async () => {
      global.fetch = (url, options) => {
        const fullUrl = url.startsWith('/') ? `${BACKEND_URL}${url}` : url;
        return originalFetch(fullUrl, options);
      };

      const api = new Api();
      const uniqueUsername = `fullflow_${Date.now()}`;
      const uniqueEmail = `${uniqueUsername}@example.com`;

      // Step 1: Register
      const registerResult = await api.register({
        username: uniqueUsername,
        email: uniqueEmail,
        password: TEST_PASSWORD,
        password_confirm: TEST_PASSWORD,
        first_name: 'Full',
        last_name: 'Flow'
      });

      expect(registerResult.username).toBe(uniqueUsername);

      // Step 2: Login
      const loginResult = await api.login({
        username: uniqueUsername,
        password: TEST_PASSWORD
      });

      expect(loginResult.username).toBe(uniqueUsername);
      expect(loginResult.id).toBeDefined();

      // Step 3: Make authenticated request
      const currentUserResult = await api.fetch('/api/user/', {});

      expect(currentUserResult.username).toBe(uniqueUsername);
      expect(currentUserResult.email).toBe(uniqueEmail);
    });
  });

  describe('API Call with Automatic Initialization', () => {
    it('should automatically fetch CSRF token before API call', async () => {
      global.fetch = (url, options) => {
        const fullUrl = url.startsWith('/') ? `${BACKEND_URL}${url}` : url;
        return originalFetch(fullUrl, options);
      };

      const api = new Api();

      // Make API call without manually calling becomeReady
      // This should automatically fetch CSRF token and then make the request
      const result = await api.login({
        username: TEST_USERNAME,
        password: TEST_PASSWORD
      });

      expect(result.username).toBe(TEST_USERNAME);
      expect(api.csrfToken).toBeDefined();
    });
  });
});
