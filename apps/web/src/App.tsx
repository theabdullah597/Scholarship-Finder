import React from 'react';
import { useTranslation } from 'react-i18next';
import { Compass, GraduationCap, ShieldCheck, Zap, Database, Server, Clock } from 'lucide-react';

export const App: React.FC = () => {
  const { t } = useTranslation();

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 to-slate-100 flex flex-col justify-between">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3 rtl:space-x-reverse">
            <GraduationCap className="h-8 w-8 text-brand-600" aria-hidden="true" />
            <span className="text-xl font-bold tracking-tight text-slate-900">
              {t('app.title')}
            </span>
          </div>
          <div className="flex items-center gap-3">
            <span className="inline-flex items-center rounded-full bg-emerald-50 px-3 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
              {t('app.phase_badge')}
            </span>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12 flex-1 flex flex-col items-center justify-center text-center">
        <div className="max-w-3xl space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-brand-50 text-brand-700 text-sm font-semibold">
            <Compass className="h-4 w-4" aria-hidden="true" />
            <span>{t('app.tagline')}</span>
          </div>

          <h1 className="text-4xl sm:text-5xl font-extrabold text-slate-900 tracking-tight">
            {t('app.title')}
          </h1>

          <p className="text-lg sm:text-xl text-slate-600 leading-relaxed">
            {t('app.description')}
          </p>

          {/* Core Feature Pillars */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-start pt-6">
            <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-sm flex items-start space-x-3 rtl:space-x-reverse">
              <Zap className="h-5 w-5 text-brand-600 mt-1 flex-shrink-0" aria-hidden="true" />
              <div>
                <p className="font-semibold text-slate-800 text-sm">{t('app.features.hybrid_search')}</p>
                <p className="text-xs text-slate-500 mt-0.5">PostgreSQL pgvector (0.6) + Full-text (0.4)</p>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-sm flex items-start space-x-3 rtl:space-x-reverse">
              <ShieldCheck className="h-5 w-5 text-brand-600 mt-1 flex-shrink-0" aria-hidden="true" />
              <div>
                <p className="font-semibold text-slate-800 text-sm">{t('app.features.verified_ops')}</p>
                <p className="text-xs text-slate-500 mt-0.5">Database ground-truth with LLM validation</p>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-sm flex items-start space-x-3 rtl:space-x-reverse">
              <Clock className="h-5 w-5 text-brand-600 mt-1 flex-shrink-0" aria-hidden="true" />
              <div>
                <p className="font-semibold text-slate-800 text-sm">{t('app.features.deadline_tracking')}</p>
                <p className="text-xs text-slate-500 mt-0.5">Automated notifications at 14, 7, and 1 day milestones</p>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-slate-200 bg-white shadow-sm flex items-start space-x-3 rtl:space-x-reverse">
              <Server className="h-5 w-5 text-brand-600 mt-1 flex-shrink-0" aria-hidden="true" />
              <div>
                <p className="font-semibold text-slate-800 text-sm">{t('app.features.privacy_first')}</p>
                <p className="text-xs text-slate-500 mt-0.5">Argon2id, rotating refresh tokens, and GDPR export</p>
              </div>
            </div>
          </div>

          {/* System Status Indicators */}
          <section aria-labelledby="system-status-heading" className="pt-8">
            <h2 id="system-status-heading" className="text-sm font-semibold uppercase tracking-wider text-slate-400 mb-4">
              {t('app.system_status.title')}
            </h2>
            <div className="inline-flex flex-wrap justify-center gap-3">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-white border border-slate-200 text-xs text-slate-700 shadow-sm">
                <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true"></span>
                {t('app.system_status.api')}
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-white border border-slate-200 text-xs text-slate-700 shadow-sm">
                <Database className="h-3 w-3 text-slate-500" aria-hidden="true" />
                {t('app.system_status.db')}
              </span>
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-md bg-white border border-slate-200 text-xs text-slate-700 shadow-sm">
                <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true"></span>
                {t('app.system_status.redis')}
              </span>
            </div>
          </section>
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 py-6 text-center text-xs text-slate-500">
        <p>&copy; {new Date().getFullYear()} OpportunityAbroad. All rights reserved.</p>
      </footer>
    </div>
  );
};

export default App;

