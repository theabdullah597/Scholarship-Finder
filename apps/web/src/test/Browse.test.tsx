import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { MemoryRouter, Route, Routes } from 'react-router-dom';
import { AuthProvider } from '../context/AuthContext';
import Browse from '../pages/Browse';
import OpportunityDetail from '../pages/OpportunityDetail';
import AdminOpportunities from '../pages/admin/Opportunities';
import { OpportunityItem } from '@opportunity-abroad/shared';

const mockOpportunities: OpportunityItem[] = [
  {
    id: '11111111-1111-1111-1111-111111111111',
    kind: 'scholarship',
    title: 'DAAD Helmut Schmidt Master Grant',
    organization: 'DAAD Germany',
    description: 'Master degree scholarship in Germany for public policy.',
    country: 'DE',
    fields: ['Public Policy', 'Economics'],
    funding_type: 'fully_funded',
    stipend_amount_min: 934,
    stipend_amount_max: 1200,
    stipend_currency: 'EUR',
    deadline: '2026-12-31T00:00:00Z',
    source_url: 'https://daad.de',
    canonical_url: 'https://daad.de/opp-1',
    status: 'published',
    created_at: '2026-01-01T00:00:00Z',
    updated_at: '2026-01-01T00:00:00Z',
  },
  {
    id: '22222222-2222-2222-2222-222222222222',
    kind: 'internship',
    title: 'CERN Summer Computing Programme',
    organization: 'CERN Geneva',
    description: 'Paid computing summer internship at CERN.',
    country: 'CH',
    fields: ['Computer Science', 'Physics'],
    funding_type: 'fully_funded',
    stipend_amount_min: 3400,
    stipend_amount_max: 3400,
    stipend_currency: 'CHF',
    deadline: '2026-11-30T00:00:00Z',
    source_url: 'https://cern.ch',
    canonical_url: 'https://cern.ch/opp-2',
    status: 'published',
    created_at: '2026-01-02T00:00:00Z',
    updated_at: '2026-01-02T00:00:00Z',
  },
];

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
    opportunities: {
      list: vi.fn(),
      getById: vi.fn(),
    },
    admin: {
      testRbac: vi.fn(),
      opportunities: {
        list: vi.fn(),
        create: vi.fn(),
        patch: vi.fn(),
        verify: vi.fn(),
        archive: vi.fn(),
        bulkModerate: vi.fn(),
      },
      auditLogs: vi.fn(),
    },
  },
  getAccessToken: vi.fn().mockReturnValue('mock-token'),
  setAccessToken: vi.fn(),
}));

import { api } from '../services/api';

describe('Opportunities Browse & Detail & Admin Pages', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Browse page and displays opportunities from API', async () => {
    vi.mocked(api.opportunities.list).mockResolvedValueOnce({
      items: mockOpportunities,
      next_cursor: 'cursor-token-page-2',
    });

    render(
      <MemoryRouter initialEntries={['/opportunities']}>
        <AuthProvider>
          <Browse />
        </AuthProvider>
      </MemoryRouter>
    );

    // Filter controls present
    expect(screen.getByText(/Explore International Opportunities/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Kind/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/Country/i)).toBeInTheDocument();

    // Opportunities loaded and rendered
    await waitFor(() => {
      expect(screen.getByText('DAAD Helmut Schmidt Master Grant')).toBeInTheDocument();
      expect(screen.getByText('CERN Summer Computing Programme')).toBeInTheDocument();
    });

    // Keyset pagination Load More button appears
    expect(screen.getByRole('button', { name: /Load More Opportunities/i })).toBeInTheDocument();
  });

  it('calls API with updated URL search params when user filters', async () => {
    vi.mocked(api.opportunities.list).mockResolvedValue({
      items: [mockOpportunities[0]],
      next_cursor: null,
    });

    render(
      <MemoryRouter initialEntries={['/opportunities']}>
        <AuthProvider>
          <Browse />
        </AuthProvider>
      </MemoryRouter>
    );

    const kindSelect = screen.getByLabelText(/Kind/i);
    fireEvent.change(kindSelect, { target: { value: 'scholarship' } });

    await waitFor(() => {
      expect(api.opportunities.list).toHaveBeenCalledWith(
        expect.objectContaining({
          kind: 'scholarship',
        })
      );
    });
  });

  it('renders Opportunity Detail page with full info', async () => {
    vi.mocked(api.opportunities.getById).mockResolvedValueOnce(mockOpportunities[0]);

    render(
      <MemoryRouter initialEntries={['/opportunities/11111111-1111-1111-1111-111111111111']}>
        <AuthProvider>
          <Routes>
            <Route path="/opportunities/:id" element={<OpportunityDetail />} />
          </Routes>
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText('DAAD Helmut Schmidt Master Grant')).toBeInTheDocument();
      expect(screen.getByText(/DAAD Germany/i)).toBeInTheDocument();
      expect(screen.getByText(/Master degree scholarship in Germany for public policy/i)).toBeInTheDocument();
      expect(screen.getByRole('link', { name: /Apply on Official Portal/i })).toHaveAttribute(
        'href',
        'https://daad.de'
      );
    });
  });

  it('renders Admin Opportunities management table with create modal', async () => {
    vi.mocked(api.admin.opportunities.list).mockResolvedValueOnce({
      items: mockOpportunities,
      total_count: 2,
      next_cursor: null,
    });

    render(
      <MemoryRouter initialEntries={['/admin/opportunities']}>
        <AuthProvider>
          <AdminOpportunities />
        </AuthProvider>
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(screen.getByText(/Opportunity Management & Moderation/i)).toBeInTheDocument();
      expect(screen.getByText('DAAD Helmut Schmidt Master Grant')).toBeInTheDocument();
    });

    // Click "+ New Opportunity" button
    const newBtn = screen.getByRole('button', { name: /\+ New Opportunity/i });
    fireEvent.click(newBtn);

    // Modal opens
    expect(screen.getByText(/Create New Opportunity/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /Save Opportunity/i })).toBeInTheDocument();
  });
});
