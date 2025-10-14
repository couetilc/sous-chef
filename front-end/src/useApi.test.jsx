import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { Api } from './useApi.jsx';

describe('Api - CSRF Token Management', () => {
  let originalFetch;

  beforeEach(() => {
    originalFetch = global.fetch;
  });

  afterEach(() => {
    global.fetch = originalFetch;
  });

  describe('Initialization', () => {
    it('should successfully fetch CSRF token on first try', async () => {
      const api = new Api();

      global.fetch = vi.fn().mockResolvedValueOnce({
        json: async () => ({ csrfToken: 'test-token' }),
      });

      await api.becomeReady();

      expect(api.isReady()).toBe(true);
      expect(api.csrfToken).toBe('test-token');
    });

    it('should handle CSRF fetch failure and allow retry', async () => {
      const api = new Api();

      // First attempt fails
      global.fetch = vi.fn().mockResolvedValueOnce({
        json: async () => ({ csrfToken: null }),
      });

      await api.becomeReady();

      expect(api.isReady()).toBe(false);
      expect(api.csrfToken).toBeUndefined();

      // Second attempt succeeds
      global.fetch = vi.fn().mockResolvedValueOnce({
        json: async () => ({ csrfToken: 'retry-token' }),
      });

      await api.becomeReady();

      expect(api.isReady()).toBe(true);
      expect(api.csrfToken).toBe('retry-token');
    });

    it('should not fetch CSRF token if already ready', async () => {
      const api = new Api();
      const fetchMock = vi.fn().mockResolvedValue({
        json: async () => ({ csrfToken: 'test-token' }),
      });
      global.fetch = fetchMock;

      await api.becomeReady();
      await api.becomeReady(); // Call again

      // Should only fetch once
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });

    it('should prevent concurrent becomeReady calls from racing', async () => {
      const api = new Api();
      const fetchMock = vi.fn().mockResolvedValue({
        json: async () => ({ csrfToken: 'test-token' }),
      });
      global.fetch = fetchMock;

      // Call becomeReady multiple times concurrently
      await Promise.all([
        api.becomeReady(),
        api.becomeReady(),
        api.becomeReady(),
      ]);

      // Should only fetch once, not three times
      expect(fetchMock).toHaveBeenCalledTimes(1);
      expect(api.csrfToken).toBe('test-token');
    });
  });

  describe('API Calls with ensureReady', () => {
    it('should automatically initialize before making API call', async () => {
      const api = new Api();

      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          json: async () => ({ csrfToken: 'auto-token' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ data: 'response' }),
        });

      // Make API call without manually calling becomeReady
      const result = await api.fetch('/api/test/', {});

      expect(result).toEqual({ data: 'response' });
      expect(api.csrfToken).toBe('auto-token');
    });

    it('should retry initialization on API call after initial failure', async () => {
      const api = new Api();

      // First CSRF attempt fails
      global.fetch = vi.fn().mockResolvedValueOnce({
        json: async () => ({ csrfToken: null }),
      });

      await api.becomeReady();
      expect(api.isReady()).toBe(false);

      // Now mock successful CSRF and API call
      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          json: async () => ({ csrfToken: 'retry-token' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
        });

      // This should retry initialization and succeed
      const result = await api.fetch('/api/test/', {});

      expect(result).toEqual({ success: true });
      expect(api.csrfToken).toBe('retry-token');
    });

    it('should handle concurrent API calls during initialization', async () => {
      const api = new Api();

      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          json: async () => ({ csrfToken: 'concurrent-token' }),
        })
        .mockResolvedValue({
          ok: true,
          json: async () => ({ success: true }),
        });

      // Make multiple concurrent API calls
      const results = await Promise.all([
        api.fetch('/api/test1/', {}),
        api.fetch('/api/test2/', {}),
        api.fetch('/api/test3/', {}),
      ]);

      // All should succeed
      results.forEach(result => {
        expect(result).toEqual({ success: true });
      });

      // CSRF should only be fetched once
      expect(global.fetch).toHaveBeenCalledWith('/api/csrf/', { credentials: 'include' });
      const csrfCalls = global.fetch.mock.calls.filter(call => call[0] === '/api/csrf/');
      expect(csrfCalls).toHaveLength(1);
    });

    it('should include CSRF token in request headers', async () => {
      const api = new Api();

      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          json: async () => ({ csrfToken: 'header-token' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({ success: true }),
        });

      await api.fetch('/api/test/', { body: JSON.stringify({ data: 'test' }) });

      // Check that the second call (actual API call) has CSRF token
      const apiCall = global.fetch.mock.calls[1];
      expect(apiCall[1].headers['X-CSRFToken']).toBe('header-token');
    });
  });

  describe('Login and Authentication', () => {
    it('should successfully login with username and password', async () => {
      const api = new Api();

      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          json: async () => ({ csrfToken: 'login-token' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            success: true,
            user: { id: 1, username: 'testuser' }
          }),
        });

      const result = await api.login({
        username: 'testuser',
        password: 'password123'
      });

      expect(result.success).toBe(true);
      expect(result.user.username).toBe('testuser');
    });

    it('should handle login failure', async () => {
      const api = new Api();

      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          json: async () => ({ csrfToken: 'login-token' }),
        })
        .mockResolvedValueOnce({
          ok: false,
          status: 401,
          json: async () => ({
            error: 'Invalid credentials'
          }),
        });

      await expect(api.login({
        username: 'testuser',
        password: 'wrong'
      })).rejects.toEqual({
        status: 401,
        data: { error: 'Invalid credentials' }
      });
    });
  });

  describe('Registration', () => {
    it('should successfully register a new user', async () => {
      const api = new Api();

      global.fetch = vi.fn()
        .mockResolvedValueOnce({
          json: async () => ({ csrfToken: 'register-token' }),
        })
        .mockResolvedValueOnce({
          ok: true,
          json: async () => ({
            success: true,
            user: { id: 1, username: 'newuser' }
          }),
        });

      const result = await api.register({
        username: 'newuser',
        email: 'new@example.com',
        password: 'password123',
        password_confirm: 'password123',
        first_name: 'New',
        last_name: 'User'
      });

      expect(result.success).toBe(true);
      expect(result.user.username).toBe('newuser');
    });
  });
});
