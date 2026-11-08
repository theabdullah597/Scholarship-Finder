import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { GraduationCap, CheckCircle2, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const ForgotPassword: React.FC = () => {
  const { t } = useTranslation();
  const { forgotPassword } = useAuth();

  const [email, setEmail] = useState('');
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const res = await forgotPassword(email);
      setSuccess(res.message);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to submit password reset request.';
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link to="/" className="inline-flex items-center space-x-2 rtl:space-x-reverse mb-4">
          <GraduationCap className="h-10 w-10 text-brand-600" aria-hidden="true" />
          <span className="text-2xl font-bold tracking-tight text-slate-900">
            {t('app.title')}
          </span>
        </Link>
        <h1 className="text-2xl font-extrabold text-slate-900 tracking-tight">
          {t('auth.forgot_password_title')}
        </h1>
        <p className="mt-2 text-sm text-slate-600">
          {t('auth.forgot_password_subtitle')}
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-white py-8 px-6 shadow-sm rounded-2xl border border-slate-200 sm:px-10">
          {success ? (
            <div className="text-center space-y-4">
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100">
                <CheckCircle2 className="h-6 w-6 text-emerald-600" aria-hidden="true" />
              </div>
              <p className="text-sm text-slate-700 leading-relaxed">{success}</p>
              <Link
                to="/login"
                className="inline-block font-semibold text-brand-600 hover:text-brand-500 text-sm"
              >
                {t('common.back_to_login')}
              </Link>
            </div>
          ) : (
            <>
              {error && (
                <div
                  role="alert"
                  className="mb-6 rounded-lg bg-red-50 p-4 border border-red-200 flex items-start space-x-3 rtl:space-x-reverse"
                >
                  <AlertCircle className="h-5 w-5 text-red-600 flex-shrink-0 mt-0.5" aria-hidden="true" />
                  <div className="text-sm text-red-800">{error}</div>
                </div>
              )}

              <form className="space-y-4" onSubmit={handleSubmit}>
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-slate-700">
                    {t('common.email')}
                  </label>
                  <div className="mt-1">
                    <input
                      id="email"
                      name="email"
                      type="email"
                      autoComplete="email"
                      required
                      placeholder={t('auth.email_placeholder')}
                      value={email}
                      onChange={(e) => setEmail(e.target.value)}
                      className="block w-full appearance-none rounded-lg border border-slate-300 px-3 py-2 placeholder-slate-400 shadow-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500 sm:text-sm"
                    />
                  </div>
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full flex justify-center items-center py-2.5 px-4 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 disabled:opacity-50 transition"
                >
                  {loading ? (
                    <Loader2 className="h-5 w-5 animate-spin" aria-label={t('common.loading')} />
                  ) : (
                    <span>{t('auth.send_reset_link')}</span>
                  )}
                </button>
              </form>

              <div className="mt-6 text-center text-sm">
                <Link to="/login" className="font-semibold text-brand-600 hover:text-brand-500">
                  {t('common.back_to_login')}
                </Link>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default ForgotPassword;
