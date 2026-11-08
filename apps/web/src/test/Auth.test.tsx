import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { MemoryRouter } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import { ProtectedRoute } from '../components/ProtectedRoute';
import Login from '../pages/Login';
import Register from '../pages/Register';

// Mock API calls
vi.mock('../services/api', () => ({
  api: {
    auth: {
      refresh: vi.fn().mockResolvedValue(null),
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
    },
    users: {
      getMe: vi.fn(),
    },
  },
  getAccessToken: vi.fn().mockReturnValue(null),
  setAccessToken: vi.fn(),
}));

describe('Auth Pages & ProtectedRoute', () => {
  it('renders Login form with email and password fields', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <Login />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
  });

  it('renders Register form with full name, email and password', () => {
    render(
      <MemoryRouter>
        <AuthProvider>
          <Register />
        </AuthProvider>
      </MemoryRouter>
    );

    expect(screen.getByLabelText(/Full name/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Email address/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/^Password/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Confirm password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Create Account/i })).toBeInTheDocument();
  });

  it('redirects unauthenticated user from ProtectedRoute to /login', () => {
    render(
      <MemoryRouter initialEntries={['/dashboard']}>
        <AuthProvider>
          <ProtectedRoute>
            <div>Sensitive Student Data</div>
          </ProtectedRoute>
        </AuthProvider>
      </MemoryRouter>
    );

    // Because user is null, ProtectedRoute renders Navigate to /login
    expect(screen.queryByText(/Sensitive Student Data/i)).not.toBeInTheDocument();
  });
});

