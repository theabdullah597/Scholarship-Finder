import React, { useCallback, useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Calendar,
  DollarSign,
  Filter,
  Globe,
  GraduationCap,
  Loader2,
  RotateCcw,
  Search,
} from 'lucide-react';
import {
  FundingType,
  OpportunityFilterParams,
  OpportunityItem,
  OpportunityKind,
} from '@opportunity-abroad/shared';
import { api } from '../services/api';

export const Browse: React.FC = () => {
  const { t } = useTranslation();
  const [searchParams, setSearchParams] = useSearchParams();

  // Local state for opportunities & pagination
  const [items, setItems] = useState<OpportunityItem[]>([]);
  const [nextCursor, setNextCursor] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [isLoadingMore, setIsLoadingMore] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Extracted filter values from URL search params
  const kind = (searchParams.get('kind') as OpportunityKind) || undefined;
  const country = searchParams.get('country') || '';
  const funding = (searchParams.get('funding') as FundingType) || undefined;
  const field = searchParams.get('field') || '';
  const stipendMin = searchParams.get('stipend_min') || '';
  const stipendMax = searchParams.get('stipend_max') || '';
  const includeExpired = searchParams.get('include_expired') === 'true';
  const sort = (searchParams.get('sort') as 'created_desc' | 'deadline_asc' | 'deadline_desc') || 'created_desc';

  // Fetch initial filtered page
  const fetchOpportunities = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    try {
      const params: OpportunityFilterParams = {
        kind,
        country: country || undefined,
        funding,
        field: field || undefined,
        stipend_min: stipendMin ? Number(stipendMin) : undefined,
        stipend_max: stipendMax ? Number(stipendMax) : undefined,
        include_expired: includeExpired,
        sort,
        limit: 12,
      };

      const res = await api.opportunities.list(params);
      setItems(res.items);
      setNextCursor(res.next_cursor);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch opportunities.';
      setError(msg);
    } finally {
      setIsLoading(false);
    }
  }, [kind, country, funding, field, stipendMin, stipendMax, includeExpired, sort]);

  useEffect(() => {
    fetchOpportunities();
  }, [fetchOpportunities]);

  // Load more with keyset cursor
  const handleLoadMore = async () => {
    if (!nextCursor || isLoadingMore) return;
    setIsLoadingMore(true);
    try {
      const params: OpportunityFilterParams = {
        kind,
        country: country || undefined,
        funding,
        field: field || undefined,
        stipend_min: stipendMin ? Number(stipendMin) : undefined,
        stipend_max: stipendMax ? Number(stipendMax) : undefined,
        include_expired: includeExpired,
        sort,
        cursor: nextCursor,
        limit: 12,
      };

      const res = await api.opportunities.list(params);
      setItems((prev) => [...prev, ...res.items]);
      setNextCursor(res.next_cursor);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load more opportunities.';
      setError(msg);
    } finally {
      setIsLoadingMore(false);
    }
  };

  // Helper to update a URL parameter
  const updateFilter = (key: string, value: string | boolean | undefined) => {
    const nextParams = new URLSearchParams(searchParams);
    if (value === undefined || value === '' || value === false) {
      nextParams.delete(key);
    } else {
      nextParams.set(key, String(value));
    }
    setSearchParams(nextParams);
  };

  const handleClearFilters = () => {
    setSearchParams(new URLSearchParams());
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center space-x-2 rtl:space-x-reverse">
            <GraduationCap className="h-8 w-8 text-brand-600" aria-hidden="true" />
            <span className="text-xl font-bold tracking-tight text-slate-900">
              {t('app.title')}
            </span>
          </Link>
          <div className="flex items-center space-x-4 rtl:space-x-reverse">
            <Link
              to="/dashboard"
              className="text-sm font-semibold text-slate-700 hover:text-brand-600 transition"
            >
              {t('dashboard.title')}
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        <div className="mb-8">
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
            {t('browse.title')}
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            {t('browse.subtitle')}
          </p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          {/* Filter Sidebar */}
          <aside aria-label={t('browse.filters_title')} className="lg:col-span-1">
            <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-6 sticky top-24">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <div className="flex items-center space-x-2 rtl:space-x-reverse text-slate-900 font-bold text-sm">
                  <Filter className="h-4 w-4 text-brand-600" aria-hidden="true" />
                  <span>{t('browse.filters_title')}</span>
                </div>
                <button
                  type="button"
                  onClick={handleClearFilters}
                  className="text-xs font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1 transition"
                >
                  <RotateCcw className="h-3 w-3" aria-hidden="true" />
                  <span>{t('browse.clear_filters')}</span>
                </button>
              </div>

              {/* Opportunity Kind Filter */}
              <div>
                <label htmlFor="filter-kind" className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                  {t('browse.kind_label')}
                </label>
                <select
                  id="filter-kind"
                  value={kind || ''}
                  onChange={(e) => updateFilter('kind', e.target.value || undefined)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  <option value="">{t('browse.all_kinds')}</option>
                  <option value="scholarship">{t('kinds.scholarship')}</option>
                  <option value="internship">{t('kinds.internship')}</option>
                  <option value="fellowship">{t('kinds.fellowship')}</option>
                  <option value="grant">{t('kinds.grant')}</option>
                </select>
              </div>

              {/* Funding Type Filter */}
              <div>
                <label htmlFor="filter-funding" className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                  {t('browse.funding_label')}
                </label>
                <select
                  id="filter-funding"
                  value={funding || ''}
                  onChange={(e) => updateFilter('funding', e.target.value || undefined)}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-1 focus:ring-brand-500"
                >
                  <option value="">{t('browse.all_funding')}</option>
                  <option value="fully_funded">{t('funding.fully_funded')}</option>
                  <option value="partially_funded">{t('funding.partially_funded')}</option>
                  <option value="unfunded">{t('funding.unfunded')}</option>
                  <option value="other">{t('funding.other')}</option>
                </select>
              </div>

              {/* Country ISO code filter */}
              <div>
                <label htmlFor="filter-country" className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                  {t('browse.country_label')}
                </label>
                <input
                  id="filter-country"
                  type="text"
                  maxLength={2}
                  placeholder={t('browse.country_placeholder')}
                  value={country}
                  onChange={(e) => updateFilter('country', e.target.value.toUpperCase().trim() || undefined)}
                  className="w-full uppercase rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>

              {/* Discipline / Field Filter */}
              <div>
                <label htmlFor="filter-field" className="block text-xs font-semibold uppercase tracking-wider text-slate-500 mb-2">
                  {t('browse.field_label')}
                </label>
                <div className="relative">
                  <input
                    id="filter-field"
                    type="text"
                    placeholder={t('browse.field_placeholder')}
                    value={field}
                    onChange={(e) => updateFilter('field', e.target.value.trim() || undefined)}
                    className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                  <Search className="h-4 w-4 text-slate-400 absolute end-3 top-2.5 pointer-events-none" aria-hidden="true" />
                </div>
              </div>

              {/* Include Past Deadlines Checkbox */}
              <div className="pt-2 border-t border-slate-100">
                <label className="flex items-center space-x-2.5 rtl:space-x-reverse cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeExpired}
                    onChange={(e) => updateFilter('include_expired', e.target.checked ? true : undefined)}
                    className="rounded text-brand-600 focus:ring-brand-500 h-4 w-4"
                  />
                  <span className="text-xs font-medium text-slate-700">
                    {t('browse.include_expired_label')}
                  </span>
                </label>
              </div>
            </div>
          </aside>

          {/* Results Grid */}
          <section aria-label="Opportunity Results" className="lg:col-span-3">
            {/* Sort & Count Header */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-4 rounded-xl border border-slate-200 mb-6 shadow-sm">
              <span className="text-sm font-semibold text-slate-700">
                {t('browse.results_found', { count: items.length })}
              </span>

              <div className="flex items-center space-x-2 rtl:space-x-reverse">
                <label htmlFor="sort-select" className="text-xs font-semibold text-slate-500 whitespace-nowrap">
                  {t('browse.sort_label')}:
                </label>
                <select
                  id="sort-select"
                  value={sort}
                  onChange={(e) => updateFilter('sort', e.target.value)}
                  className="rounded-lg border border-slate-300 px-3 py-1.5 text-xs font-medium text-slate-800 focus:outline-none focus:ring-1 focus:ring-brand-500 bg-white"
                >
                  <option value="created_desc">{t('browse.sort_created_desc')}</option>
                  <option value="deadline_asc">{t('browse.sort_deadline_asc')}</option>
                  <option value="deadline_desc">{t('browse.sort_deadline_desc')}</option>
                </select>
              </div>
            </div>

            {error && (
              <div role="alert" className="mb-6 rounded-lg bg-red-50 p-4 border border-red-200 text-sm text-red-800">
                {error}
              </div>
            )}

            {isLoading ? (
              <div className="flex flex-col items-center justify-center py-24 space-y-3">
                <Loader2 className="h-8 w-8 text-brand-600 animate-spin" aria-label={t('common.loading')} />
                <p className="text-sm text-slate-500">{t('common.loading')}</p>
              </div>
            ) : items.length === 0 ? (
              <div className="bg-white rounded-2xl border border-slate-200 p-12 text-center shadow-sm">
                <GraduationCap className="h-12 w-12 text-slate-400 mx-auto mb-3" aria-hidden="true" />
                <h2 className="text-base font-bold text-slate-900">{t('browse.no_results_title')}</h2>
                <p className="text-sm text-slate-500 mt-1 max-w-md mx-auto">{t('browse.no_results_desc')}</p>
                <button
                  type="button"
                  onClick={handleClearFilters}
                  className="mt-6 inline-flex items-center px-4 py-2 rounded-lg bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 transition"
                >
                  {t('browse.clear_filters')}
                </button>
              </div>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {items.map((opp) => (
                    <article
                      key={opp.id}
                      className="bg-white rounded-2xl border border-slate-200 p-5 shadow-sm hover:shadow-md transition flex flex-col justify-between"
                    >
                      <div>
                        {/* Top Badges */}
                        <div className="flex items-center justify-between gap-2 mb-3">
                          <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-brand-50 text-brand-700">
                            {t(`kinds.${opp.kind}` as never)}
                          </span>
                          <span
                            className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ${
                              opp.funding_type === 'fully_funded'
                                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                : 'bg-slate-100 text-slate-700'
                            }`}
                          >
                            {t(`funding.${opp.funding_type}` as never)}
                          </span>
                        </div>

                        {/* Title & Organization */}
                        <h2 className="text-base font-bold text-slate-900 line-clamp-2 hover:text-brand-600 transition">
                          <Link to={`/opportunities/${opp.id}`}>
                            {opp.title}
                          </Link>
                        </h2>
                        <p className="text-xs font-semibold text-slate-500 mt-1 flex items-center gap-1.5">
                          <Globe className="h-3.5 w-3.5 flex-shrink-0" aria-hidden="true" />
                          <span>{opp.organization} ({opp.country})</span>
                        </p>

                        {/* Fields */}
                        {opp.fields && opp.fields.length > 0 && (
                          <div className="mt-3 flex flex-wrap gap-1">
                            {opp.fields.slice(0, 3).map((f) => (
                              <span
                                key={f}
                                className="inline-flex items-center px-2 py-0.5 rounded bg-slate-100 text-slate-600 text-[11px] font-medium"
                              >
                                {f}
                              </span>
                            ))}
                            {opp.fields.length > 3 && (
                              <span className="text-[11px] text-slate-400 self-center">
                                +{opp.fields.length - 3}
                              </span>
                            )}
                          </div>
                        )}
                      </div>

                      {/* Footer Details */}
                      <div className="mt-5 pt-4 border-t border-slate-100 flex items-center justify-between text-xs">
                        {/* Stipend */}
                        <div className="flex items-center gap-1 text-slate-600 font-medium">
                          {opp.stipend_amount_min ? (
                            <>
                              <DollarSign className="h-3.5 w-3.5 text-emerald-600" aria-hidden="true" />
                              <span>
                                {opp.stipend_currency || ''} {Number(opp.stipend_amount_min).toLocaleString()}
                              </span>
                            </>
                          ) : (
                            <span className="text-slate-400">{t('funding.unfunded')}</span>
                          )}
                        </div>

                        {/* Deadline */}
                        <div className="flex items-center gap-1 text-slate-500">
                          <Calendar className="h-3.5 w-3.5" aria-hidden="true" />
                          <span>
                            {opp.deadline
                              ? new Date(opp.deadline).toLocaleDateString()
                              : t('browse.no_deadline')}
                          </span>
                        </div>
                      </div>
                    </article>
                  ))}
                </div>

                {/* Keyset Load More */}
                {nextCursor && (
                  <div className="mt-8 text-center">
                    <button
                      type="button"
                      onClick={handleLoadMore}
                      disabled={isLoadingMore}
                      className="inline-flex items-center px-6 py-3 rounded-xl bg-white border border-slate-300 shadow-sm text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50 transition"
                    >
                      {isLoadingMore ? (
                        <>
                          <Loader2 className="h-4 w-4 animate-spin me-2" aria-hidden="true" />
                          <span>{t('browse.loading_more')}</span>
                        </>
                      ) : (
                        <span>{t('browse.load_more')}</span>
                      )}
                    </button>
                  </div>
                )}
              </>
            )}
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500 bg-white">
        <p>&copy; {new Date().getFullYear()} OpportunityAbroad. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default Browse;
