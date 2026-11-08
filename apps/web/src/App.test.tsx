import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import App from './App';

// Mock API so AuthProvider.refreshAuth doesn't make real fetch calls
vi.mock('./services/api', () => ({
  api: {
    auth: {
      refresh: vi.fn().mockResolvedValue(null),
      login: vi.fn(),
      register: vi.fn(),
      logout: vi.fn(),
      verifyEmail: vi.fn(),
      forgotPassword: vi.fn(),
      resetPassword: vi.fn(),
    },
    users: {
      getMe: vi.fn(),
      updateMe: vi.fn(),
    },
    admin: {
      testRbac: vi.fn(),
    },
  },
  getAccessToken: vi.fn().mockReturnValue(null),
  setAccessToken: vi.fn(),
}));

describe('App', () => {
  it('renders the OpportunityAbroad home page with navigation', () => {
    render(<App />);
    const headingElements = screen.getAllByText(/OpportunityAbroad/i);
    expect(headingElements.length).toBeGreaterThan(0);
    // "Sign In" appears in both header nav and hero CTA
    const signInElements = screen.getAllByText(/Sign In/i);
    expect(signInElements.length).toBeGreaterThanOrEqual(1);
    const createAccountElements = screen.getAllByText(/Create Account/i);
    expect(createAccountElements.length).toBeGreaterThanOrEqual(1);
  });

  it('renders system status section', () => {
    render(<App />);
    expect(screen.getByText(/System Status/i)).toBeInTheDocument();
    expect(screen.getByText(/PostgreSQL 16 \+ pgvector: Ready/i)).toBeInTheDocument();
  });
});
