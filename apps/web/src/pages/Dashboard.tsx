import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { GraduationCap, LogOut, CheckCircle, User as UserIcon, Globe, BookOpen, Clock, Shield } from 'lucide-react';
import { useAuth } from '../context/AuthContext';

export const Dashboard: React.FC = () => {
  const { t } = useTranslation();
  const { user, logout, updateProfile } = useAuth();

  const [fullName, setFullName] = useState(user?.profile?.full_name || '');
  const [citizenship, setCitizenship] = useState(user?.profile?.citizenship || '');
  const [targetCountries, setTargetCountries] = useState(user?.profile?.target_countries?.join(', ') || '');
  const [fieldsOfInterest, setFieldsOfInterest] = useState(user?.profile?.fields_of_interest?.join(', ') || '');
  const [degreeLevel, setDegreeLevel] = useState(user?.profile?.target_degree_level || 'masters');
  const [timezone, setTimezone] = useState(user?.profile?.timezone || 'UTC');

  const [saving, setSaving] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setError(null);
    setSuccess(false);

    try {
      const parsedCountries = targetCountries
        .split(',')
        .map((c) => c.trim().toUpperCase())
        .filter(Boolean);

      const parsedFields = fieldsOfInterest
        .split(',')
        .map((f) => f.trim())
        .filter(Boolean);

      await updateProfile({
        full_name: fullName,
        citizenship: citizenship.trim().toUpperCase() || null,
        target_countries: parsedCountries,
        fields_of_interest: parsedFields,
        target_degree_level: degreeLevel,
        timezone: timezone.trim() || 'UTC',
      });
      setSuccess(true);
      setTimeout(() => setSuccess(false), 4000);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save profile changes.';
      setError(msg);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Navigation */}
      <header className="bg-white border-b border-slate-200 sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3 rtl:space-x-reverse">
            <GraduationCap className="h-8 w-8 text-brand-600" aria-hidden="true" />
            <span className="text-xl font-bold tracking-tight text-slate-900">
              {t('app.title')}
            </span>
            <span className="ms-2 inline-flex items-center rounded-md bg-brand-50 px-2 py-1 text-xs font-medium text-brand-700 ring-1 ring-inset ring-brand-700/10">
              {t('dashboard.role_badge')}
            </span>
          </div>

          <div className="flex items-center space-x-4 rtl:space-x-reverse">
            <span className="text-sm text-slate-600 hidden sm:inline-block">
              {user?.email}
            </span>
            {user?.role === 'admin' && (
              <a
                href="/admin"
                className="text-xs font-semibold text-brand-600 hover:text-brand-700 bg-brand-50 px-3 py-1.5 rounded-lg border border-brand-200 transition"
              >
                Admin Portal
              </a>
            )}
            <button
              onClick={() => logout()}
              className="inline-flex items-center space-x-1.5 rtl:space-x-reverse text-sm font-medium text-slate-600 hover:text-red-600 transition"
            >
              <LogOut className="h-4 w-4" aria-hidden="true" />
              <span>{t('common.logout')}</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Welcome Banner */}
          <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                {t('dashboard.welcome')}, {user?.profile?.full_name || user?.email}!
              </h1>
              <p className="text-sm text-slate-500 mt-1">
                {t('app.description')}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <Shield className="h-3.5 w-3.5" aria-hidden="true" />
                Session Active (In-Memory JWT)
              </span>
            </div>
          </div>

          {/* Profile Form */}
          <div className="bg-white p-6 sm:p-8 rounded-2xl border border-slate-200 shadow-sm">
            <div className="border-b border-slate-200 pb-4 mb-6">
              <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <UserIcon className="h-5 w-5 text-brand-600" aria-hidden="true" />
                {t('dashboard.profile_section')}
              </h2>
            </div>

            {success && (
              <div
                role="status"
                className="mb-6 rounded-lg bg-emerald-50 p-4 border border-emerald-200 flex items-center space-x-3 rtl:space-x-reverse text-emerald-800 text-sm"
              >
                <CheckCircle className="h-5 w-5 text-emerald-600 flex-shrink-0" aria-hidden="true" />
                <span>{t('dashboard.profile_saved_success')}</span>
              </div>
            )}

            {error && (
              <div
                role="alert"
                className="mb-6 rounded-lg bg-red-50 p-4 border border-red-200 text-red-800 text-sm"
              >
                {error}
              </div>
            )}

            <form onSubmit={handleSave} className="space-y-6">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="fullName" className="block text-sm font-medium text-slate-700">
                    {t('common.full_name')}
                  </label>
                  <input
                    id="fullName"
                    type="text"
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>

                <div>
                  <label htmlFor="citizenship" className="block text-sm font-medium text-slate-700">
                    {t('dashboard.citizenship')}
                  </label>
                  <input
                    id="citizenship"
                    type="text"
                    maxLength={2}
                    placeholder="e.g. US, DE, PK, IN"
                    value={citizenship}
                    onChange={(e) => setCitizenship(e.target.value)}
                    className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm uppercase focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
              </div>

              <div>
                <label htmlFor="targetCountries" className="block text-sm font-medium text-slate-700 flex items-center gap-1.5">
                  <Globe className="h-4 w-4 text-slate-400" aria-hidden="true" />
                  {t('dashboard.target_countries')}
                </label>
                <input
                  id="targetCountries"
                  type="text"
                  placeholder="DE, CA, US, GB, SE"
                  value={targetCountries}
                  onChange={(e) => setTargetCountries(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm uppercase focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <div>
                <label htmlFor="fieldsOfInterest" className="block text-sm font-medium text-slate-700 flex items-center gap-1.5">
                  <BookOpen className="h-4 w-4 text-slate-400" aria-hidden="true" />
                  {t('dashboard.fields_of_interest')}
                </label>
                <input
                  id="fieldsOfInterest"
                  type="text"
                  placeholder="Computer Science, Renewable Energy, Public Health"
                  value={fieldsOfInterest}
                  onChange={(e) => setFieldsOfInterest(e.target.value)}
                  className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="degreeLevel" className="block text-sm font-medium text-slate-700">
                    {t('dashboard.degree_level')}
                  </label>
                  <select
                    id="degreeLevel"
                    value={degreeLevel}
                    onChange={(e) => setDegreeLevel(e.target.value)}
                    className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm bg-white focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  >
                    <option value="bachelors">{t('dashboard.degree_levels.bachelors')}</option>
                    <option value="masters">{t('dashboard.degree_levels.masters')}</option>
                    <option value="phd">{t('dashboard.degree_levels.phd')}</option>
                    <option value="postdoc">{t('dashboard.degree_levels.postdoc')}</option>
                  </select>
                </div>

                <div>
                  <label htmlFor="timezone" className="block text-sm font-medium text-slate-700 flex items-center gap-1.5">
                    <Clock className="h-4 w-4 text-slate-400" aria-hidden="true" />
                    {t('dashboard.timezone')}
                  </label>
                  <input
                    id="timezone"
                    type="text"
                    value={timezone}
                    onChange={(e) => setTimezone(e.target.value)}
                    className="mt-1 block w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:border-brand-500 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
              </div>

              <div className="flex justify-end pt-4 border-t border-slate-100">
                <button
                  type="submit"
                  disabled={saving}
                  className="inline-flex justify-center items-center py-2 px-5 border border-transparent rounded-lg shadow-sm text-sm font-semibold text-white bg-brand-600 hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-brand-500 disabled:opacity-50 transition"
                >
                  {saving ? t('common.loading') : t('common.save')}
                </button>
              </div>
            </form>
          </div>
        </div>
      </main>
    </div>
  );
};

export default Dashboard;
