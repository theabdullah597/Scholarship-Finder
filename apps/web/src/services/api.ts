import { UserData, StudentProfileData } from '@opportunity-abroad/shared';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// In-memory token storage (never placed in localStorage or sessionStorage)
let inMemoryAccessToken: string | null = null;
let refreshPromise: Promise<string | null> | null = null;

export const setAccessToken = (token: string | null): void => {
  inMemoryAccessToken = token;
};

export const getAccessToken = (): string | null => {
  return inMemoryAccessToken;
};

export class ApiError extends Error {
  status: number;
  data: unknown;

  constructor(status: number, message: string, data?: unknown) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

/**
 * Perform token refresh with single-flight mutex to avoid duplicate refresh calls
 */
export const refreshSession = async (): Promise<string | null> => {
  if (refreshPromise) {
    return refreshPromise;
  }

  refreshPromise = (async () => {
    try {
      const response = await fetch(`${BASE_URL}/auth/refresh`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include', // sends httpOnly refresh_token cookie
      });

      if (!response.ok) {
        setAccessToken(null);
        window.dispatchEvent(new CustomEvent('auth:expired'));
        return null;
      }

      const data = await response.json();
      const newToken = data.access_token as string;
      setAccessToken(newToken);
      return newToken;
    } catch {
      setAccessToken(null);
      window.dispatchEvent(new CustomEvent('auth:expired'));
      return null;
    } finally {
      refreshPromise = null;
    }
  })();

  return refreshPromise;
};

/**
 * Core fetch wrapper with in-memory JWT attachment and automatic 401 refresh
 */
export const fetchWithAuth = async (endpoint: string, options: RequestInit = {}): Promise<Response> => {
  const url = endpoint.startsWith('http') ? endpoint : `${BASE_URL}${endpoint}`;
  const headers = new Headers(options.headers || {});

  if (inMemoryAccessToken && !headers.has('Authorization')) {
    headers.set('Authorization', `Bearer ${inMemoryAccessToken}`);
  }
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: 'include',
  });

  // If 401 Unauthorized occurs on an authenticated route (not on /auth/login or /auth/refresh)
  if (response.status === 401 && !endpoint.includes('/auth/login') && !endpoint.includes('/auth/refresh')) {
    const refreshedToken = await refreshSession();
    if (refreshedToken) {
      headers.set('Authorization', `Bearer ${refreshedToken}`);
      return fetch(url, {
        ...options,
        headers,
        credentials: 'include',
      });
    }
  }

  return response;
};

export const api = {
  auth: {
    register: async (payload: { email: string; password: string; full_name?: string }) => {
      const res = await fetchWithAuth('/auth/register', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new ApiError(res.status, data.detail || 'Registration failed', data);
      return data;
    },

    verifyEmail: async (token: string) => {
      const res = await fetchWithAuth('/auth/verify-email', {
        method: 'POST',
        body: JSON.stringify({ token }),
      });
      const data = await res.json();
      if (!res.ok) throw new ApiError(res.status, data.detail || 'Email verification failed', data);
      return data;
    },

    login: async (payload: { email: string; password: string }) => {
      const res = await fetchWithAuth('/auth/login', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new ApiError(res.status, data.detail || 'Login failed', data);
      setAccessToken(data.access_token);
      return data;
    },

    refresh: refreshSession,

    logout: async () => {
      try {
        await fetchWithAuth('/auth/logout', { method: 'POST' });
      } finally {
        setAccessToken(null);
      }
    },

    forgotPassword: async (email: string) => {
      const res = await fetchWithAuth('/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ email }),
      });
      const data = await res.json();
      if (!res.ok) throw new ApiError(res.status, data.detail || 'Request failed', data);
      return data;
    },

    resetPassword: async (payload: { token: string; new_password: string }) => {
      const res = await fetchWithAuth('/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new ApiError(res.status, data.detail || 'Password reset failed', data);
      return data;
    },
  },

  users: {
    getMe: async (): Promise<UserData> => {
      const res = await fetchWithAuth('/users/me');
      const data = await res.json();
      if (!res.ok) throw new ApiError(res.status, data.detail || 'Failed to fetch user', data);
      return data;
    },

    updateMe: async (payload: Partial<StudentProfileData>): Promise<UserData> => {
      const res = await fetchWithAuth('/users/me', {
        method: 'PATCH',
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok) throw new ApiError(res.status, data.detail || 'Failed to update user', data);
      return data;
    },
  },

  admin: {
    testRbac: async () => {
      const res = await fetchWithAuth('/admin/test-rbac');
      const data = await res.json();
      if (!res.ok) throw new ApiError(res.status, data.detail || 'RBAC check failed', data);
      return data;
    },
  },
};
