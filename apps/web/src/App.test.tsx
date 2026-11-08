import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import App from './App';

describe('App', () => {
  it('renders the OpportunityAbroad placeholder page and key heading', () => {
    render(<App />);
    const headingElements = screen.getAllByText(/OpportunityAbroad/i);
    expect(headingElements.length).toBeGreaterThan(0);
    expect(screen.getByText(/Phase 0: Foundations Active/i)).toBeInTheDocument();
  });

  it('renders system status section', () => {
    render(<App />);
    expect(screen.getByText(/System Status/i)).toBeInTheDocument();
    expect(screen.getByText(/PostgreSQL 16 \+ pgvector: Ready/i)).toBeInTheDocument();
  });
});

