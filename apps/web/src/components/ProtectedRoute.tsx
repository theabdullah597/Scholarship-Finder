import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ShieldAlert, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { UserRole } from '@opportunity-abroad/shared';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredRole?: UserRole;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredRole }) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();
  const { t } = useTranslation();

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="flex flex-col items-center space-y-3">
          <Loader2 className="h-8 w-8 animate-spin text-brand-600" aria-label={t('common.loading')} />
          <p className="text-sm text-slate-500">{t('common.verifying_session')}</p>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (requiredRole && user?.role !== requiredRole) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
        <div className="max-w-md w-full text-center bg-white p-8 rounded-2xl shadow-sm border border-slate-200">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-red-100 mb-4">
            <ShieldAlert className="h-6 w-6 text-red-600" aria-hidden="true" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">{t('auth.forbidden_title')}</h2>
          <p className="mt-2 text-sm text-slate-600">{t('auth.forbidden_description')}</p>
          <div className="mt-6">
            <a
              href="/dashboard"
              className="inline-flex items-center justify-center rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 transition"
            >
              {t('auth.return_to_dashboard')}
            </a>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
};

export default ProtectedRoute;

