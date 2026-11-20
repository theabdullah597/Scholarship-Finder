import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { ArrowLeft, Loader2, Play, Plus, RefreshCw } from 'lucide-react';
import { SourceItem, SourceType, IngestionRunItem } from '@opportunity-abroad/shared';
import { api } from '../../services/api';

const emptyForm = { name: '', source_type: 'rss' as SourceType, url: '', fetch_interval_minutes: 720 };

export const AdminSources: React.FC = () => {
  const { t } = useTranslation();
  const [sources, setSources] = useState<SourceItem[]>([]);
  const [runs, setRuns] = useState<IngestionRunItem[]>([]);
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [runningId, setRunningId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [sourceData, runData] = await Promise.all([api.admin.sources.list(), api.admin.sources.runs()]);
      setSources(sourceData);
      setRuns(runData);
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('admin_sources.load_error'));
    } finally {
      setLoading(false);
    }
  }, [t]);

  useEffect(() => { void load(); }, [load]);

  const createSource = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    try {
      await api.admin.sources.create(form);
      setForm(emptyForm);
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('admin_sources.save_error'));
    } finally {
      setSubmitting(false);
    }
  };

  const toggleSource = async (source: SourceItem) => {
    try {
      await api.admin.sources.update(source.id, { is_active: !source.is_active });
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('admin_sources.save_error'));
    }
  };

  const runSource = async (source: SourceItem) => {
    setRunningId(source.id);
    try {
      await api.admin.sources.runNow(source.id);
      await load();
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : t('admin_sources.run_error'));
    } finally {
      setRunningId(null);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="border-b border-slate-200 bg-white">
        <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-4">
          <h1 className="text-xl font-bold text-slate-900">{t('admin_sources.title')}</h1>
          <Link to="/admin" className="inline-flex items-center gap-1 text-sm text-slate-600 hover:text-brand-600">
            <ArrowLeft className="h-4 w-4" aria-hidden="true" /> {t('admin_sources.back')}
          </Link>
        </div>
      </header>
      <main className="mx-auto max-w-7xl space-y-6 px-4 py-8">
        {error && <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-800">{error}</div>}
        <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <h2 className="mb-4 text-lg font-semibold text-slate-900">{t('admin_sources.add_title')}</h2>
          <form onSubmit={createSource} className="grid gap-3 md:grid-cols-5">
            <input required minLength={2} aria-label={t('admin_sources.name')} placeholder={t('admin_sources.name')} value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            <select aria-label={t('admin_sources.type')} value={form.source_type} onChange={(e) => setForm({ ...form, source_type: e.target.value as SourceType })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm">
              <option value="rss">RSS</option>
              <option value="json_api">JSON API</option>
              <option value="html_scraper">HTML</option>
            </select>
            <input required type="url" aria-label={t('admin_sources.url')} placeholder={t('admin_sources.url')} value={form.url} onChange={(e) => setForm({ ...form, url: e.target.value })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm md:col-span-2" />
            <input required type="number" min={15} max={10080} aria-label={t('admin_sources.interval')} value={form.fetch_interval_minutes} onChange={(e) => setForm({ ...form, fetch_interval_minutes: Number(e.target.value) })} className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
            <button disabled={submitting} className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700 disabled:opacity-50 md:col-span-5">
              <Plus className="h-4 w-4" aria-hidden="true" /> {t('admin_sources.add_button')}
            </button>
          </form>
        </section>
        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center justify-between border-b border-slate-200 p-5">
            <h2 className="text-lg font-semibold text-slate-900">{t('admin_sources.sources_title')}</h2>
            <button type="button" onClick={() => void load()} className="inline-flex items-center gap-2 text-sm text-slate-600 hover:text-brand-600"><RefreshCw className="h-4 w-4" aria-hidden="true" /> {t('admin_sources.refresh')}</button>
          </div>
          {loading ? <div className="p-8 text-center"><Loader2 className="mx-auto h-6 w-6 animate-spin text-brand-600" aria-label={t('common.loading')} /></div> : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-4">{t('admin_sources.name')}</th><th className="p-4">{t('admin_sources.type')}</th><th className="p-4">{t('admin_sources.interval')}</th><th className="p-4">{t('admin_sources.status')}</th><th className="p-4">{t('common.actions')}</th></tr></thead>
                <tbody>{sources.map((source) => <tr key={source.id} className="border-t border-slate-100"><td className="p-4"><div className="font-medium text-slate-900">{source.name}</div><div className="max-w-xs truncate text-xs text-slate-500">{source.url}</div></td><td className="p-4">{source.source_type}</td><td className="p-4">{source.fetch_interval_minutes} min</td><td className="p-4">{source.is_active ? t('admin_sources.active') : t('admin_sources.paused')}</td><td className="flex gap-2 p-4"><button type="button" onClick={() => void toggleSource(source)} className="rounded border border-slate-300 px-2 py-1 text-xs">{source.is_active ? t('admin_sources.pause') : t('admin_sources.activate')}</button><button type="button" disabled={runningId === source.id} onClick={() => void runSource(source)} className="inline-flex items-center gap-1 rounded bg-brand-600 px-2 py-1 text-xs text-white disabled:opacity-50"><Play className="h-3 w-3" aria-hidden="true" /> {runningId === source.id ? t('admin_sources.running') : t('admin_sources.run_now')}</button></td></tr>)}</tbody>
              </table>
            </div>
          )}
        </section>
        <section className="rounded-xl border border-slate-200 bg-white shadow-sm">
          <h2 className="border-b border-slate-200 p-5 text-lg font-semibold text-slate-900">{t('admin_sources.history_title')}</h2>
          <div className="overflow-x-auto"><table className="w-full text-left text-sm"><thead className="bg-slate-50 text-xs uppercase text-slate-500"><tr><th className="p-4">{t('admin_sources.started')}</th><th className="p-4">{t('admin_sources.source')}</th><th className="p-4">{t('admin_sources.status')}</th><th className="p-4">{t('admin_sources.counts')}</th></tr></thead><tbody>{runs.map((run) => <tr key={run.id} className="border-t border-slate-100"><td className="p-4">{new Date(run.started_at).toLocaleString()}</td><td className="p-4">{run.source_name || run.source_id}</td><td className="p-4">{run.status}</td><td className="p-4">{run.items_found} / {run.items_created} / {run.items_updated} / {run.items_failed}</td></tr>)}</tbody></table></div>
        </section>
      </main>
    </div>
  );
};

export default AdminSources;
