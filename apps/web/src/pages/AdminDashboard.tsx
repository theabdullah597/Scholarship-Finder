import React, { useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { ShieldCheck, LogOut, ArrowLeft, Loader2, AlertCircle } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export const AdminDashboard: React.FC = () => {
  const { t } = useTranslation();
  const { user, logout } = useAuth();

  const [rbacStatus, setRbacStatus] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const verifyRbac = async () => {
      try {
        const res = await api.admin.testRbac();
        setRbacStatus(res.message);
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : 'RBAC verification failed';
        setError(msg);
      } finally {
        setLoading(false);
      }
    };
    verifyRbac();
  }, []);

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 flex flex-col">
      {/* Admin Header */}
      <header className="bg-slate-800 border-b border-slate-700 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3 rtl:space-x-reverse">
            <ShieldCheck className="h-8 w-8 text-amber-500" aria-hidden="true" />
            <span className="text-xl font-bold tracking-tight text-white">
              {t('admin.title')}
            </span>
            <span className="ms-2 inline-flex items-center rounded-md bg-amber-400/10 px-2 py-1 text-xs font-medium text-amber-400 ring-1 ring-inset ring-amber-400/20">
              {t('admin.role_badge')}
            </span>
          </div>

          <div className="flex items-center space-x-4 rtl:space-x-reverse">
            <a
              href="/dashboard"
              className="inline-flex items-center space-x-1.5 rtl:space-x-reverse text-xs text-slate-300 hover:text-white bg-slate-700 px-3 py-1.5 rounded-lg border border-slate-600 transition"
            >
              <ArrowLeft className="h-3.5 w-3.5" aria-hidden="true" />
              <span>Student View</span>
            </a>
            <button
              onClick={() => logout()}
              className="inline-flex items-center space-x-1.5 rtl:space-x-reverse text-sm font-medium text-slate-400 hover:text-red-400 transition"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
              <span>{t('common.logout')}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Admin Area */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* RBAC Verification Alert */}
          {loading ? (
            <div className="p-6 bg-slate-800 rounded-2xl border border-slate-700 flex items-center gap-3">
              <Loader2 className="h-5 w-5 animate-spin text-amber-400" aria-hidden="true" />
              <span className="text-sm text-slate-300">Executing server-side RBAC validation...</span>
            </div>
          ) : error ? (
            <div className="p-6 bg-red-950/60 rounded-2xl border border-red-800 flex items-center gap-3 text-red-200">
              <AlertCircle className="h-5 w-5 text-red-400" aria-hidden="true" />
              <span className="text-sm">{error}</span>
            </div>
          ) : (
            <div className="p-6 bg-emerald-950/40 rounded-2xl border border-emerald-800 flex items-center gap-3 text-emerald-200">
              <ShieldCheck className="h-6 w-6 text-emerald-400 flex-shrink-0" aria-hidden="true" />
              <div>
                <p className="font-semibold text-sm">{t('admin.rbac_verified')}</p>
                <p className="text-xs text-emerald-400/80 mt-0.5">Status: {rbacStatus} (Admin user: {user?.email})</p>
              </div>
            </div>
          )}

          {/* Phase 2 Opportunity Management Link */}
          <div className="bg-slate-800 p-6 rounded-2xl border border-slate-700 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h2 className="text-lg font-bold text-white mb-1">{t('admin_ops.title')}</h2>
              <p className="text-sm text-slate-400 leading-relaxed">
                {t('admin_ops.subtitle')}
              </p>
            </div>
            <a
              href="/admin/opportunities"
              className="inline-flex items-center px-4 py-2.5 rounded-xl bg-amber-500 hover:bg-amber-600 text-slate-900 font-bold text-sm shadow transition"
            >
              <span>{t('admin.manage_ops_link')}</span>
            </a>
          </div>
        </div>
      </main>
    </div>
  );
};

export default AdminDashboard;
