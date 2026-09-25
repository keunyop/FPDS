"use client";
import { useEffect, useState } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import { Bookmark, Link2, RefreshCw, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { ComparisonSelection } from '@/components/fpds/public/comparison-controls';
import { useComparison } from '@/components/fpds/public/comparison-provider';
import { comparisonHref, parseComparison } from '@/lib/public-comparison';
import { comparisonCopy } from '@/lib/public-comparison-copy';
import { buildPublicHref, parseProductGridPageFilters } from '@/lib/public-query';

export function ComparisonSurface() {
  const params = useSearchParams();
  const scope = parseComparison(new URLSearchParams(params.toString()));
  const copy = comparisonCopy(scope.locale);
  const filters = parseProductGridPageFilters({ country_code: scope.countryCode, locale: scope.locale });
  const { entries, savedList, save, forget, clear, refresh, ready, restoreSaved } = useComparison(scope.countryCode);
  const [message, setMessage] = useState('');
  const [shareUrl, setShareUrl] = useState('');
  const [saving, setSaving] = useState(false);
  const selectionKey = `${scope.countryCode}:${scope.locale}:${entries.map(item => item.id).join(',')}`;
  useEffect(() => { setMessage(''); setShareUrl(''); }, [selectionKey]);
  const loading = entries.some(item => item.status === 'loading');
  async function copyLink() {
    const url = new URL(comparisonHref(entries.map(item => item.id), scope), window.location.origin).href;
    try { await navigator.clipboard.writeText(url); setMessage(copy.copied); setShareUrl(''); }
    catch { setShareUrl(url); setMessage(copy.copyFailed); }
  }
  async function saveHere() {
    setSaving(true);
    try { await save(scope.countryCode, entries); setMessage(copy.saved); }
    catch { setMessage(copy.storageError); }
    finally { setSaving(false); }
  }
  return <main className="mx-auto min-h-[60vh] w-full max-w-7xl px-4 py-8 md:px-6" data-comparison-page>
    <div className="mb-5 flex flex-wrap items-center justify-between gap-3 border-b border-border pb-4">
      <h1 className="font-display text-3xl font-semibold tracking-tight">{copy.title}</h1>
      <span className="text-sm text-muted-foreground" role="status">{copy.count.replace('{count}', String(entries.length))} / 4</span>
    </div>
    {!scope.valid ? <p role="alert" className="mb-4 text-destructive">{copy.invalid}</p> : null}
    <div className="mb-4 flex flex-wrap gap-2">
      {entries.length ? <>
        <Button onClick={copyLink} variant="outline"><Link2 className="size-4" aria-hidden="true" />{copy.share}</Button>
        <Button onClick={saveHere} variant="outline" disabled={saving || entries.some(item => item.status !== 'ready')}><Bookmark className="size-4" aria-hidden="true" />{copy.save}</Button>
        <Button onClick={refresh} variant="ghost" disabled={loading}><RefreshCw className="size-4" aria-hidden="true" />{copy.refresh}</Button>
        <Button onClick={() => { clear(); setMessage(''); setShareUrl(''); }} variant="ghost">{copy.clear}</Button>
      </> : null}
      {savedList ? <>
        <Button variant="outline" onClick={() => { restoreSaved(); setMessage(''); }}>{copy.openSaved}</Button>
        <Button variant="ghost" onClick={() => { try { forget(scope.countryCode); setMessage(copy.deleted); } catch { setMessage(copy.storageError); } }}><Trash2 className="size-4" aria-hidden="true" />{copy.deleteSaved}</Button>
      </> : null}
    </div>
    {savedList ? <p className="mb-4 text-xs text-muted-foreground">{copy.local}</p> : null}
    <p role="status" className="mb-3 text-sm text-primary">{message}</p>
    {shareUrl ? <input aria-label={copy.copyFailed} className="mb-4 min-h-11 w-full rounded-md border border-input bg-background px-3 text-sm" readOnly value={shareUrl} onFocus={event => event.target.select()} /> : null}
    {!ready ? <p role="status">{copy.loading}</p> : !entries.length ? <p className="py-8 text-muted-foreground">{copy.empty}</p> : <ComparisonSelection filters={filters} locale={scope.locale} />}
    <Button asChild variant="outline" className="mt-6"><Link href={buildPublicHref('/products', filters)}>{copy.browse}</Link></Button>
  </main>;
}
