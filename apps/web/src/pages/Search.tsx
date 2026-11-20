import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { GraduationCap, Loader2, Search as SearchIcon, Sparkles } from 'lucide-react';
import { SearchResultItem } from '@opportunity-abroad/shared';
import { api } from '../services/api';

const Search: React.FC = () => {
  const { t } = useTranslation();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResultItem[]>([]);
  const [fallback, setFallback] = useState(false);
  const [cached, setCached] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    if (query.trim().length < 2) return;
    setLoading(true);
    setError(null);
    try {
      const response = await api.search(query.trim());
      setResults(response.results);
      setFallback(response.fallback);
      setCached(response.cached);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('search.error'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4">
          <Link to="/" className="flex items-center gap-2">
            <GraduationCap className="h-7 w-7 text-brand-600" aria-hidden="true" />
            <span className="font-bold text-slate-900">{t('app.title')}</span>
          </Link>
          <Link to="/opportunities" className="text-sm font-semibold text-brand-600">{t('search.browse_link')}</Link>
        </div>
      </header>
      <main className="mx-auto max-w-4xl px-4 py-10">
        <div className="mb-8 text-center">
          <div className="mb-3 inline-flex rounded-full bg-brand-50 p-3 text-brand-600">
            <Sparkles className="h-6 w-6" aria-hidden="true" />
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900">{t('search.title')}</h1>
          <p className="mt-2 text-slate-600">{t('search.subtitle')}</p>
        </div>
        <form onSubmit={submit} className="flex gap-2 rounded-xl border border-slate-200 bg-white p-2 shadow-sm">
          <input
            aria-label={t('search.input_label')}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder={t('search.placeholder')}
            className="min-w-0 flex-1 rounded-lg px-3 py-2 text-slate-900 outline-none"
            minLength={2}
            maxLength={500}
          />
          <button type="submit" disabled={loading || query.trim().length < 2} className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 font-semibold text-white disabled:opacity-50">
            {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <SearchIcon className="h-4 w-4" aria-hidden="true" />}
            {t('search.button')}
          </button>
        </form>
        {error && <div role="alert" className="mt-4 rounded-lg border border-red-200 bg-red-50 p-3 text-red-800">{error}</div>}
        {results.length > 0 && (
          <div className="mt-6 space-y-3">
            <p className="text-sm text-slate-500">
              {fallback ? t('search.fallback_notice') : t('search.ai_notice')} {cached && t('search.cached_notice')}
            </p>
            {results.map((result) => (
              <article key={result.opportunity.id} className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <Link to={`/opportunities/${result.opportunity.id}`} className="text-lg font-bold text-slate-900 hover:text-brand-600">
                      {result.opportunity.title}
                    </Link>
                    <p className="mt-1 text-sm text-slate-600">{result.opportunity.organization} · {result.opportunity.country}</p>
                  </div>
                  <span className="rounded-full bg-brand-50 px-2 py-1 text-xs font-semibold text-brand-700">{Math.round(result.score * 100)}%</span>
                </div>
                <p className="mt-3 text-sm text-slate-700">{result.reason}</p>
              </article>
            ))}
          </div>
        )}
        {!loading && query && results.length === 0 && !error && <p className="mt-8 text-center text-slate-500">{t('search.no_results')}</p>}
      </main>
    </div>
  );
};

export default Search;
