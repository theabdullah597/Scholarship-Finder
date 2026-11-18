import React, { useCallback, useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  AlertCircle,
  Archive,
  CheckCircle2,
  ChevronLeft,
  Edit,
  GraduationCap,
  Loader2,
  Plus,
  Search,
  ShieldCheck,
  X,
} from 'lucide-react';
import {
  FundingType,
  OpportunityCreatePayload,
  OpportunityItem,
  OpportunityKind,
  OpportunityPatchPayload,
} from '@opportunity-abroad/shared';
import { api } from '../../services/api';

export const AdminOpportunities: React.FC = () => {
  const { t } = useTranslation();

  const [items, setItems] = useState<OpportunityItem[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  // Modal State
  const [modalOpen, setModalOpen] = useState<boolean>(false);
  const [editingOpp, setEditingOpp] = useState<OpportunityItem | null>(null);

  // Form Fields
  const [formKind, setFormKind] = useState<OpportunityKind>('scholarship');
  const [formTitle, setFormTitle] = useState('');
  const [formOrg, setFormOrg] = useState('');
  const [formCountry, setFormCountry] = useState('');
  const [formFunding, setFormFunding] = useState<FundingType>('fully_funded');
  const [formFieldsStr, setFormFieldsStr] = useState('');
  const [formStipendMin, setFormStipendMin] = useState('');
  const [formStipendMax, setFormStipendMax] = useState('');
  const [formCurrency, setFormCurrency] = useState('USD');
  const [formDeadline, setFormDeadline] = useState('');
  const [formSourceUrl, setFormSourceUrl] = useState('');
  const [formCanonicalUrl, setFormCanonicalUrl] = useState('');
  const [formDescription, setFormDescription] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const fetchOpportunities = useCallback(async () => {
    setLoading(true);
    try {
      const res = await api.admin.opportunities.list(
        statusFilter || undefined,
        searchQuery || undefined,
        50,
        0
      );
      setItems(res.items);
      setTotalCount(res.total_count || res.items.length);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to fetch opportunities.';
      setNotification({ type: 'error', message: msg });
    } finally {
      setLoading(false);
    }
  }, [statusFilter, searchQuery]);

  useEffect(() => {
    fetchOpportunities();
  }, [fetchOpportunities]);

  const openCreateModal = () => {
    setEditingOpp(null);
    setFormKind('scholarship');
    setFormTitle('');
    setFormOrg('');
    setFormCountry('');
    setFormFunding('fully_funded');
    setFormFieldsStr('');
    setFormStipendMin('');
    setFormStipendMax('');
    setFormCurrency('USD');
    setFormDeadline('');
    setFormSourceUrl('');
    setFormCanonicalUrl('');
    setFormDescription('');
    setFormError(null);
    setModalOpen(true);
  };

  const openEditModal = (opp: OpportunityItem) => {
    setEditingOpp(opp);
    setFormKind(opp.kind);
    setFormTitle(opp.title);
    setFormOrg(opp.organization);
    setFormCountry(opp.country);
    setFormFunding(opp.funding_type);
    setFormFieldsStr(opp.fields ? opp.fields.join(', ') : '');
    setFormStipendMin(opp.stipend_amount_min ? String(opp.stipend_amount_min) : '');
    setFormStipendMax(opp.stipend_amount_max ? String(opp.stipend_amount_max) : '');
    setFormCurrency(opp.stipend_currency || 'USD');
    setFormDeadline(opp.deadline ? opp.deadline.slice(0, 10) : '');
    setFormSourceUrl(opp.source_url);
    setFormCanonicalUrl(opp.canonical_url);
    setFormDescription(opp.description);
    setFormError(null);
    setModalOpen(true);
  };

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);

    // Form Validation
    if (!formTitle.trim() || !formOrg.trim() || !formCountry.trim() || !formSourceUrl.trim() || !formCanonicalUrl.trim() || !formDescription.trim()) {
      setFormError('Please fill in all required fields.');
      return;
    }
    if (formCountry.trim().length !== 2) {
      setFormError('Country must be a 2-letter ISO code (e.g. DE, US).');
      return;
    }

    const fieldsArray = formFieldsStr
      .split(',')
      .map((f) => f.trim())
      .filter(Boolean);

    try {
      if (editingOpp) {
        const patchPayload: OpportunityPatchPayload = {
          kind: formKind,
          title: formTitle.trim(),
          organization: formOrg.trim(),
          country: formCountry.trim().toUpperCase(),
          funding_type: formFunding,
          fields: fieldsArray,
          stipend_amount_min: formStipendMin ? Number(formStipendMin) : null,
          stipend_amount_max: formStipendMax ? Number(formStipendMax) : null,
          stipend_currency: formCurrency.trim().toUpperCase(),
          deadline: formDeadline ? new Date(formDeadline).toISOString() : null,
          source_url: formSourceUrl.trim(),
          canonical_url: formCanonicalUrl.trim(),
          description: formDescription.trim(),
        };

        await api.admin.opportunities.patch(editingOpp.id, patchPayload);
        setNotification({ type: 'success', message: t('admin_ops.success_updated') });
      } else {
        const createPayload: OpportunityCreatePayload = {
          kind: formKind,
          title: formTitle.trim(),
          organization: formOrg.trim(),
          country: formCountry.trim().toUpperCase(),
          funding_type: formFunding,
          fields: fieldsArray,
          stipend_amount_min: formStipendMin ? Number(formStipendMin) : null,
          stipend_amount_max: formStipendMax ? Number(formStipendMax) : null,
          stipend_currency: formCurrency.trim().toUpperCase(),
          deadline: formDeadline ? new Date(formDeadline).toISOString() : null,
          source_url: formSourceUrl.trim(),
          canonical_url: formCanonicalUrl.trim(),
          description: formDescription.trim(),
        };

        await api.admin.opportunities.create(createPayload);
        setNotification({ type: 'success', message: t('admin_ops.success_created') });
      }

      setModalOpen(false);
      fetchOpportunities();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to save opportunity.';
      setFormError(msg);
    }
  };

  const handleVerify = async (id: string) => {
    setActionLoading(id);
    try {
      await api.admin.opportunities.verify(id);
      setNotification({ type: 'success', message: t('admin_ops.success_verified') });
      fetchOpportunities();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to verify opportunity.';
      setNotification({ type: 'error', message: msg });
    } finally {
      setActionLoading(null);
    }
  };

  const handleArchive = async (id: string) => {
    setActionLoading(id);
    try {
      await api.admin.opportunities.archive(id);
      setNotification({ type: 'success', message: t('admin_ops.success_archived') });
      fetchOpportunities();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to archive opportunity.';
      setNotification({ type: 'error', message: msg });
    } finally {
      setActionLoading(null);
    }
  };

  const handleBulkAction = async (action: 'publish' | 'reject' | 'archive') => {
    if (selectedIds.length === 0) return;
    try {
      await api.admin.opportunities.bulkModerate({
        items: selectedIds.map((id) => ({ id, action })),
      });
      setNotification({ type: 'success', message: t('admin_ops.success_bulk') });
      setSelectedIds([]);
      fetchOpportunities();
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Bulk action failed.';
      setNotification({ type: 'error', message: msg });
    }
  };

  const toggleSelectAll = (checked: boolean) => {
    if (checked) {
      setSelectedIds(items.map((i) => i.id));
    } else {
      setSelectedIds([]);
    }
  };

  const toggleSelectId = (id: string) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((i) => i !== id) : [...prev, id]
    );
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-between">
      {/* Header */}
      <header className="border-b border-slate-200 bg-white sticky top-0 z-40">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3 rtl:space-x-reverse">
            <Link to="/" className="flex items-center space-x-2 rtl:space-x-reverse">
              <GraduationCap className="h-8 w-8 text-brand-600" aria-hidden="true" />
              <span className="text-xl font-bold tracking-tight text-slate-900">
                {t('app.title')}
              </span>
            </Link>
            <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-50 text-indigo-700">
              Admin Portal
            </span>
          </div>

          <div className="flex items-center space-x-3 rtl:space-x-reverse">
            <Link
              to="/admin"
              className="text-xs font-semibold text-slate-600 hover:text-brand-600 flex items-center gap-1 transition"
            >
              <ChevronLeft className="h-4 w-4" aria-hidden="true" />
              <span>{t('admin.title')}</span>
            </Link>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full">
        {/* Banner Title */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
          <div>
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              {t('admin_ops.title')}
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              {t('admin_ops.subtitle')} ({totalCount} total)
            </p>
          </div>

          <button
            type="button"
            onClick={openCreateModal}
            className="inline-flex items-center px-4 py-2.5 rounded-xl bg-brand-600 text-white font-semibold text-sm shadow-sm hover:bg-brand-700 transition self-start sm:self-auto"
          >
            <Plus className="h-4 w-4 me-1.5" aria-hidden="true" />
            <span>{t('admin_ops.create_button')}</span>
          </button>
        </div>

        {/* Notifications */}
        {notification && (
          <div
            role="alert"
            className={`mb-6 rounded-lg p-4 flex items-center justify-between border ${
              notification.type === 'success'
                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                : 'bg-red-50 border-red-200 text-red-800'
            }`}
          >
            <div className="flex items-center gap-2">
              {notification.type === 'success' ? (
                <CheckCircle2 className="h-5 w-5 text-emerald-600" aria-hidden="true" />
              ) : (
                <AlertCircle className="h-5 w-5 text-red-600" aria-hidden="true" />
              )}
              <span className="text-sm font-medium">{notification.message}</span>
            </div>
            <button
              type="button"
              onClick={() => setNotification(null)}
              className="text-slate-400 hover:text-slate-600"
            >
              <X className="h-4 w-4" aria-hidden="true" />
            </button>
          </div>
        )}

        {/* Filter & Search Bar */}
        <div className="bg-white p-4 rounded-xl border border-slate-200 mb-6 shadow-sm flex flex-col sm:flex-row gap-3">
          <div className="relative flex-1">
            <input
              type="text"
              placeholder={t('admin_ops.search_placeholder')}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full rounded-lg border border-slate-300 ps-9 pe-3 py-2 text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:ring-1 focus:ring-brand-500"
            />
            <Search className="h-4 w-4 text-slate-400 absolute start-3 top-2.5 pointer-events-none" aria-hidden="true" />
          </div>

          <div className="w-full sm:w-48">
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm text-slate-800 focus:outline-none focus:ring-1 focus:ring-brand-500"
            >
              <option value="">{t('admin_ops.all_statuses')}</option>
              <option value="pending_review">{t('statuses.pending_review')}</option>
              <option value="published">{t('statuses.published')}</option>
              <option value="archived">{t('statuses.archived')}</option>
              <option value="rejected">{t('statuses.rejected')}</option>
            </select>
          </div>
        </div>

        {/* Bulk Action Bar */}
        {selectedIds.length > 0 && (
          <div className="bg-brand-50 border border-brand-200 rounded-xl p-3 mb-6 flex flex-wrap items-center justify-between gap-3">
            <span className="text-xs font-semibold text-brand-900">
              {t('admin_ops.bulk_bar_selected', { count: selectedIds.length })}
            </span>
            <div className="flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => handleBulkAction('publish')}
                className="px-3 py-1.5 rounded-lg bg-emerald-600 text-white text-xs font-semibold hover:bg-emerald-700 transition"
              >
                {t('admin_ops.bulk_approve')}
              </button>
              <button
                type="button"
                onClick={() => handleBulkAction('reject')}
                className="px-3 py-1.5 rounded-lg bg-red-600 text-white text-xs font-semibold hover:bg-red-700 transition"
              >
                {t('admin_ops.bulk_reject')}
              </button>
              <button
                type="button"
                onClick={() => handleBulkAction('archive')}
                className="px-3 py-1.5 rounded-lg bg-slate-600 text-white text-xs font-semibold hover:bg-slate-700 transition"
              >
                {t('admin_ops.bulk_archive')}
              </button>
            </div>
          </div>
        )}

        {/* Opportunities Table */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20">
              <Loader2 className="h-8 w-8 text-brand-600 animate-spin" aria-label={t('common.loading')} />
              <p className="text-xs text-slate-500 mt-2">{t('common.loading')}</p>
            </div>
          ) : items.length === 0 ? (
            <div className="py-16 text-center text-sm text-slate-500">
              {t('browse.no_results_title')}
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm text-slate-600">
                <thead className="bg-slate-50 text-xs uppercase tracking-wider text-slate-500 border-b border-slate-200">
                  <tr>
                    <th scope="col" className="p-4 w-4">
                      <input
                        type="checkbox"
                        checked={selectedIds.length === items.length && items.length > 0}
                        onChange={(e) => toggleSelectAll(e.target.checked)}
                        className="rounded text-brand-600 focus:ring-brand-500 h-4 w-4"
                      />
                    </th>
                    <th scope="col" className="py-3 px-4 font-semibold">{t('admin_ops.col_title')}</th>
                    <th scope="col" className="py-3 px-4 font-semibold">{t('admin_ops.col_kind')}</th>
                    <th scope="col" className="py-3 px-4 font-semibold">{t('admin_ops.col_country')}</th>
                    <th scope="col" className="py-3 px-4 font-semibold">{t('admin_ops.col_funding')}</th>
                    <th scope="col" className="py-3 px-4 font-semibold">{t('admin_ops.col_status')}</th>
                    <th scope="col" className="py-3 px-4 font-semibold text-end">{t('admin_ops.col_actions')}</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 font-normal">
                  {items.map((opp) => (
                    <tr key={opp.id} className="hover:bg-slate-50/75 transition">
                      <td className="p-4 w-4">
                        <input
                          type="checkbox"
                          checked={selectedIds.includes(opp.id)}
                          onChange={() => toggleSelectId(opp.id)}
                          className="rounded text-brand-600 focus:ring-brand-500 h-4 w-4"
                        />
                      </td>
                      <td className="py-3 px-4">
                        <div className="font-semibold text-slate-900 line-clamp-1">
                          <Link to={`/opportunities/${opp.id}`} className="hover:text-brand-600">
                            {opp.title}
                          </Link>
                        </div>
                        <div className="text-xs text-slate-400 mt-0.5">{opp.organization}</div>
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span className="inline-flex px-2 py-0.5 rounded text-xs font-medium bg-slate-100 text-slate-700">
                          {t(`kinds.${opp.kind}` as never)}
                        </span>
                      </td>
                      <td className="py-3 px-4 font-mono text-xs">{opp.country}</td>
                      <td className="py-3 px-4 text-xs">
                        {t(`funding.${opp.funding_type}` as never)}
                      </td>
                      <td className="py-3 px-4 whitespace-nowrap">
                        <span
                          className={`inline-flex px-2 py-0.5 rounded-full text-[11px] font-semibold ${
                            opp.status === 'published'
                              ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                              : opp.status === 'pending_review'
                              ? 'bg-amber-50 text-amber-700 border border-amber-200'
                              : opp.status === 'rejected'
                              ? 'bg-red-50 text-red-700 border border-red-200'
                              : 'bg-slate-100 text-slate-600'
                          }`}
                        >
                          {t(`statuses.${opp.status}` as never)}
                        </span>
                      </td>
                      <td className="py-3 px-4 text-end whitespace-nowrap space-x-1 rtl:space-x-reverse">
                        {opp.status !== 'published' && (
                          <button
                            type="button"
                            onClick={() => handleVerify(opp.id)}
                            disabled={actionLoading === opp.id}
                            className="p-1 text-emerald-600 hover:text-emerald-700 rounded transition"
                            title={t('admin_ops.action_verify')}
                          >
                            <ShieldCheck className="h-4 w-4 inline" aria-hidden="true" />
                          </button>
                        )}
                        <button
                          type="button"
                          onClick={() => openEditModal(opp)}
                          className="p-1 text-slate-600 hover:text-brand-600 rounded transition"
                          title={t('admin_ops.action_edit')}
                        >
                          <Edit className="h-4 w-4 inline" aria-hidden="true" />
                        </button>
                        {opp.status !== 'archived' && (
                          <button
                            type="button"
                            onClick={() => handleArchive(opp.id)}
                            disabled={actionLoading === opp.id}
                            className="p-1 text-slate-400 hover:text-slate-600 rounded transition"
                            title={t('admin_ops.action_archive')}
                          >
                            <Archive className="h-4 w-4 inline" aria-hidden="true" />
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* Create / Edit Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 overflow-y-auto bg-slate-900/50 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl border border-slate-200 max-w-2xl w-full p-6 sm:p-8 shadow-xl max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100 mb-6">
              <h2 className="text-xl font-bold text-slate-900">
                {editingOpp ? t('admin_ops.modal_edit_title') : t('admin_ops.modal_create_title')}
              </h2>
              <button
                type="button"
                onClick={() => setModalOpen(false)}
                className="text-slate-400 hover:text-slate-600"
              >
                <X className="h-5 w-5" aria-hidden="true" />
              </button>
            </div>

            {formError && (
              <div role="alert" className="mb-4 rounded-lg bg-red-50 p-3 border border-red-200 text-xs text-red-800">
                {formError}
              </div>
            )}

            <form onSubmit={handleFormSubmit} className="space-y-4 text-xs font-medium text-slate-700">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block mb-1">{t('admin_ops.form_title')} *</label>
                  <input
                    type="text"
                    required
                    value={formTitle}
                    onChange={(e) => setFormTitle(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block mb-1">{t('admin_ops.form_org')} *</label>
                  <input
                    type="text"
                    required
                    value={formOrg}
                    onChange={(e) => setFormOrg(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block mb-1">{t('admin_ops.form_kind')} *</label>
                  <select
                    value={formKind}
                    onChange={(e) => setFormKind(e.target.value as OpportunityKind)}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  >
                    <option value="scholarship">{t('kinds.scholarship')}</option>
                    <option value="internship">{t('kinds.internship')}</option>
                    <option value="fellowship">{t('kinds.fellowship')}</option>
                    <option value="grant">{t('kinds.grant')}</option>
                  </select>
                </div>
                <div>
                  <label className="block mb-1">{t('admin_ops.form_country')} *</label>
                  <input
                    type="text"
                    maxLength={2}
                    required
                    placeholder="DE"
                    value={formCountry}
                    onChange={(e) => setFormCountry(e.target.value.toUpperCase())}
                    className="w-full uppercase rounded-lg border border-slate-300 p-2 text-sm text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block mb-1">{t('admin_ops.form_funding')} *</label>
                  <select
                    value={formFunding}
                    onChange={(e) => setFormFunding(e.target.value as FundingType)}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  >
                    <option value="fully_funded">{t('funding.fully_funded')}</option>
                    <option value="partially_funded">{t('funding.partially_funded')}</option>
                    <option value="unfunded">{t('funding.unfunded')}</option>
                    <option value="other">{t('funding.other')}</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block mb-1">{t('admin_ops.form_fields')}</label>
                <input
                  type="text"
                  placeholder="Computer Science, Engineering, Physics"
                  value={formFieldsStr}
                  onChange={(e) => setFormFieldsStr(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2 text-sm text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                <div>
                  <label className="block mb-1">{t('admin_ops.form_stipend_min')}</label>
                  <input
                    type="number"
                    value={formStipendMin}
                    onChange={(e) => setFormStipendMin(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block mb-1">{t('admin_ops.form_stipend_max')}</label>
                  <input
                    type="number"
                    value={formStipendMax}
                    onChange={(e) => setFormStipendMax(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block mb-1">{t('admin_ops.form_stipend_currency')}</label>
                  <input
                    type="text"
                    maxLength={3}
                    value={formCurrency}
                    onChange={(e) => setFormCurrency(e.target.value.toUpperCase())}
                    className="w-full uppercase rounded-lg border border-slate-300 p-2 text-sm text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="block mb-1">{t('admin_ops.form_deadline')}</label>
                <input
                  type="date"
                  value={formDeadline}
                  onChange={(e) => setFormDeadline(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2 text-sm text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block mb-1">{t('admin_ops.form_source_url')} *</label>
                  <input
                    type="url"
                    required
                    value={formSourceUrl}
                    onChange={(e) => setFormSourceUrl(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
                <div>
                  <label className="block mb-1">{t('admin_ops.form_canonical_url')} *</label>
                  <input
                    type="url"
                    required
                    value={formCanonicalUrl}
                    onChange={(e) => setFormCanonicalUrl(e.target.value)}
                    className="w-full rounded-lg border border-slate-300 p-2 text-sm text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                  />
                </div>
              </div>

              <div>
                <label className="block mb-1">{t('admin_ops.form_description')} *</label>
                <textarea
                  rows={4}
                  required
                  value={formDescription}
                  onChange={(e) => setFormDescription(e.target.value)}
                  className="w-full rounded-lg border border-slate-300 p-2 text-sm text-slate-900 focus:outline-none focus:ring-1 focus:ring-brand-500"
                />
              </div>

              <div className="pt-4 border-t border-slate-100 flex items-center justify-end gap-3">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-300 text-sm font-semibold text-slate-700 hover:bg-slate-50 transition"
                >
                  {t('admin_ops.cancel_btn')}
                </button>
                <button
                  type="submit"
                  className="px-5 py-2 rounded-lg bg-brand-600 text-white text-sm font-semibold hover:bg-brand-700 transition"
                >
                  {t('admin_ops.save_btn')}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default AdminOpportunities;
