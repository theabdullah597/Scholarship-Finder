import React, { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';
import { AlertCircle, Loader2, LogOut, ShieldCheck } from 'lucide-react';
import { AdminAnalytics, AdminUserItem } from '@opportunity-abroad/shared';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export const AdminDashboard: React.FC = () => {
  const { t } = useTranslation();
  const { logout } = useAuth();
  const [analytics, setAnalytics] = useState<AdminAnalytics | null>(null);
  const [users, setUsers] = useState<AdminUserItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [broadcast, setBroadcast] = useState({ title: '', message: '', audience: '' });
  const [broadcastResult, setBroadcastResult] = useState<string | null>(null);

  const load = useCallback(async () => {
    try {
      const [analyticsData, usersData] = await Promise.all([api.admin.analytics(), api.admin.users.list()]);
      setAnalytics(analyticsData);
      setUsers(usersData);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('admin.load_error'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => {
    void load();
  }, [load]);

  const updateUser = async (user: AdminUserItem, payload: { role?: string; is_suspended?: boolean }) => {
    try {
      const updated = await api.admin.users.update(user.id, payload);
      setUsers((items) => items.map((item) => (item.id === updated.id ? updated : item)));
      setAnalytics(await api.admin.analytics());
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('admin.update_error'));
    }
  };

  const sendBroadcast = async (event: React.FormEvent) => {
    event.preventDefault();
    try {
      const result = await api.admin.broadcast({
        title: broadcast.title,
        message: broadcast.message,
        audience: broadcast.audience || undefined,
      });
      setBroadcastResult(t('admin.broadcast_sent', { count: result.recipients }));
      setBroadcast({ title: '', message: '', audience: '' });
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('admin.broadcast_error'));
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100">
      <header className="border-b border-slate-700 bg-slate-800">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
          <div className="flex items-center gap-3">
            <ShieldCheck className="h-8 w-8 text-amber-500" aria-hidden="true" />
            <h1 className="text-xl font-bold">{t('admin.title')}</h1>
          </div>
          <button onClick={() => void logout()} className="flex items-center gap-2 text-sm text-slate-300 hover:text-white">
            <LogOut className="h-4 w-4" aria-hidden="true" /> {t('common.logout')}
          </button>
        </div>
      </header>
      <main className="mx-auto max-w-7xl space-y-6 px-4 py-8">
        {loading && <Loader2 className="h-6 w-6 animate-spin text-amber-400" aria-label={t('common.loading')} />}
        {error && <div className="flex items-center gap-2 rounded-lg border border-red-800 bg-red-950/50 p-4 text-red-200"><AlertCircle className="h-5 w-5" />{error}</div>}
        {analytics && (
          <section aria-labelledby="analytics-title">
            <h2 id="analytics-title" className="mb-3 text-lg font-bold">{t('admin.analytics_title')}</h2>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              {Object.entries(analytics).map(([key, value]) => (
                <div key={key} className="rounded-xl border border-slate-700 bg-slate-800 p-4">
                  <p className="text-xs text-slate-400">{t(`admin.metrics.${key}`)}</p>
                  <p className="mt-1 text-2xl font-bold text-amber-400">{value}</p>
                </div>
              ))}
            </div>
          </section>
        )}
        <section className="rounded-xl border border-slate-700 bg-slate-800 p-5">
          <h2 className="mb-4 text-lg font-bold">{t('admin.users_title')}</h2>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead><tr className="border-b border-slate-700 text-slate-400"><th className="p-2">{t('common.email')}</th><th className="p-2">{t('admin.role')}</th><th className="p-2">{t('admin.status')}</th><th className="p-2">{t('common.actions')}</th></tr></thead>
              <tbody>{users.map((user) => <tr key={user.id} className="border-b border-slate-700/50">
                <td className="p-2">{user.email}</td>
                <td className="p-2">
                  <select value={user.role} onChange={(event) => void updateUser(user, { role: event.target.value })} className="rounded bg-slate-700 p-1">
                    <option value="student">{t('admin.student')}</option><option value="admin">{t('admin.admin')}</option>
                  </select>
                </td>
                <td className="p-2">{user.is_suspended ? t('admin.suspended') : t('admin.active')}</td>
                <td className="p-2"><button onClick={() => void updateUser(user, { is_suspended: !user.is_suspended })} className="text-amber-400 hover:underline">{user.is_suspended ? t('admin.restore') : t('admin.suspend')}</button></td>
              </tr>)}</tbody>
            </table>
          </div>
        </section>
        <form onSubmit={sendBroadcast} className="space-y-3 rounded-xl border border-slate-700 bg-slate-800 p-5">
          <h2 className="text-lg font-bold">{t('admin.broadcast_title')}</h2>
          <input required value={broadcast.title} onChange={(e) => setBroadcast({ ...broadcast, title: e.target.value })} placeholder={t('admin.broadcast_subject')} className="w-full rounded bg-slate-700 p-2" />
          <textarea required value={broadcast.message} onChange={(e) => setBroadcast({ ...broadcast, message: e.target.value })} placeholder={t('admin.broadcast_message')} className="w-full rounded bg-slate-700 p-2" rows={3} />
          <select value={broadcast.audience} onChange={(e) => setBroadcast({ ...broadcast, audience: e.target.value })} className="rounded bg-slate-700 p-2"><option value="">{t('admin.all_users')}</option><option value="student">{t('admin.student')}</option><option value="admin">{t('admin.admin')}</option></select>
          <button type="submit" className="rounded bg-amber-500 px-4 py-2 font-bold text-slate-900">{t('admin.send_broadcast')}</button>
          {broadcastResult && <p className="text-emerald-300">{broadcastResult}</p>}
        </form>
      </main>
    </div>
  );
};

export default AdminDashboard;
