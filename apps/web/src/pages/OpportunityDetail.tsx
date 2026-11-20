import React, { useEffect, useState } from 'react';
import { Link, useParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  ArrowLeft,
  Calendar,
  DollarSign,
  ExternalLink,
  Globe,
  GraduationCap,
  Loader2,
  Tag as TagIcon,
} from 'lucide-react';
import { OpportunityItem } from '@opportunity-abroad/shared';
import { api } from '../services/api';
import { useAuth } from '../context/AuthContext';

export const OpportunityDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { t } = useTranslation();
  const { isAuthenticated } = useAuth();

  const [opp, setOpp] = useState<OpportunityItem | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!id) return;
    const fetchDetail = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await api.opportunities.getById(id);
        setOpp(data);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'Failed to load opportunity details.';
        setError(msg);
      } finally {
        setLoading(false);
      }
    };

    fetchDetail();
  }, [id]);

  const saveOpportunity = async () => {
    if (!id) return;
    try {
      await api.student.applications.save(id);
      setSaved(true);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('detail.save_error'));
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center space-y-3">
        <Loader2 className="h-8 w-8 text-brand-600 animate-spin" aria-label={t('common.loading')} />
        <p className="text-sm text-slate-500">{t('common.loading')}</p>
      </div>
    );
  }

  if (error || !opp) {
    return (
      <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4">
        <div className="bg-white rounded-2xl border border-slate-200 p-8 max-w-md w-full text-center shadow-sm">
          <p className="text-sm text-red-600 mb-4">{error || 'Opportunity not found'}</p>
          <Link
            to="/opportunities"
            className="inline-flex items-center px-4 py-2 rounded-lg bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 transition"
          >
            <ArrowLeft className="h-4 w-4 me-2" aria-hidden="true" />
            <span>{t('detail.back_to_browse')}</span>
          </Link>
        </div>
      </div>
    );
  }

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
          <Link
            to="/opportunities"
            className="text-sm font-semibold text-brand-600 hover:text-brand-700 flex items-center gap-1.5 transition"
          >
            <ArrowLeft className="h-4 w-4 rtl:rotate-180" aria-hidden="true" />
            <span>{t('detail.back_to_browse')}</span>
          </Link>
        </div>
      </header>

      {/* Main Detail Content */}
      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-10 flex-1 w-full">
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-10 shadow-sm space-y-8">
          {/* Top badges & Title */}
          <div>
            <div className="flex flex-wrap items-center gap-2 mb-4">
              <span className="inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold bg-brand-50 text-brand-700">
                {t(`kinds.${opp.kind}` as never)}
              </span>
              <span
                className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                  opp.funding_type === 'fully_funded'
                    ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                    : 'bg-slate-100 text-slate-700'
                }`}
              >
                {t(`funding.${opp.funding_type}` as never)}
              </span>
            </div>

            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {opp.title}
            </h1>

            <p className="mt-2 text-base font-semibold text-slate-600 flex items-center gap-2">
              <Globe className="h-4 w-4 text-slate-400" aria-hidden="true" />
              <span>{opp.organization} &bull; {opp.country}</span>
            </p>
          </div>

          {/* Quick Metrics Bar */}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 p-4 rounded-xl bg-slate-50 border border-slate-100">
            {/* Stipend */}
            <div className="flex items-start space-x-3 rtl:space-x-reverse">
              <DollarSign className="h-5 w-5 text-emerald-600 mt-0.5 flex-shrink-0" aria-hidden="true" />
              <div>
                <span className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  {t('detail.stipend_amount')}
                </span>
                <span className="text-sm font-bold text-slate-900">
                  {opp.stipend_amount_min
                    ? `${opp.stipend_currency || ''} ${Number(opp.stipend_amount_min).toLocaleString()} ${
                        opp.stipend_amount_max ? `- ${Number(opp.stipend_amount_max).toLocaleString()}` : ''
                      }`
                    : t('detail.not_specified')}
                </span>
              </div>
            </div>

            {/* Deadline */}
            <div className="flex items-start space-x-3 rtl:space-x-reverse">
              <Calendar className="h-5 w-5 text-brand-600 mt-0.5 flex-shrink-0" aria-hidden="true" />
              <div>
                <span className="block text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  {t('detail.deadline')}
                </span>
                <span className="text-sm font-bold text-slate-900">
                  {opp.deadline
                    ? new Date(opp.deadline).toLocaleDateString(undefined, {
                        year: 'numeric',
                        month: 'long',
                        day: 'numeric',
                      })
                    : t('browse.no_deadline')}
                </span>
              </div>
            </div>
          </div>

          {/* Eligible Fields */}
          {opp.fields && opp.fields.length > 0 && (
            <div>
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-2">
                {t('detail.fields_title')}
              </h2>
              <div className="flex flex-wrap gap-2">
                {opp.fields.map((f) => (
                  <span
                    key={f}
                    className="inline-flex items-center px-3 py-1 rounded-lg bg-slate-100 text-slate-800 text-xs font-medium"
                  >
                    {f}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Tags */}
          {opp.tags && opp.tags.length > 0 && (
            <div>
              <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <TagIcon className="h-4 w-4 text-slate-400" aria-hidden="true" />
                <span>{t('detail.tags_title')}</span>
              </h2>
              <div className="flex flex-wrap gap-2">
                {opp.tags.map((tg) => (
                  <span
                    key={tg.id}
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full border border-slate-200 bg-white text-slate-700 text-xs font-medium"
                  >
                    {tg.name}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Full Description */}
          <div>
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider mb-3">
              {t('detail.description_title')}
            </h2>
            <div className="text-slate-700 text-sm leading-relaxed whitespace-pre-line bg-slate-50/50 p-5 rounded-xl border border-slate-100">
              {opp.description}
            </div>
          </div>

          {/* Action Button */}
          <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row items-center justify-between gap-4">
            {isAuthenticated && (
              <button
                type="button"
                onClick={() => void saveOpportunity()}
                disabled={saved}
                className="w-full sm:w-auto rounded-xl border border-brand-200 px-6 py-3 text-sm font-semibold text-brand-700 hover:bg-brand-50 disabled:opacity-60"
              >
                {saved ? t('detail.saved_button') : t('detail.save_button')}
              </button>
            )}
            <a
              href={opp.source_url}
              target="_blank"
              rel="noopener noreferrer"
              className="w-full sm:w-auto inline-flex items-center justify-center px-6 py-3 rounded-xl bg-brand-600 text-white font-semibold text-sm shadow-sm hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 transition"
            >
              <span>{t('detail.apply_button')}</span>
              <ExternalLink className="ms-2 h-4 w-4" aria-hidden="true" />
            </a>

            <a
              href={opp.canonical_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-xs text-slate-500 hover:text-slate-700 underline flex items-center gap-1"
            >
              <span>{t('detail.canonical_source')}</span>
              <ExternalLink className="h-3 w-3" aria-hidden="true" />
            </a>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500 bg-white">
        <p>&copy; {new Date().getFullYear()} OpportunityAbroad. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default OpportunityDetail;
