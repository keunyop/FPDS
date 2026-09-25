"use client";

import { createContext, Suspense, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react';
import { usePathname, useSearchParams } from 'next/navigation';
import type { PublicProduct } from '@/lib/public-api';
import { COMPARISON_STORAGE_KEY, MAX_COMPARE_PRODUCTS, comparisonFingerprint, comparisonHref, parseComparison, readSavedComparison, type ComparisonResult, type SavedComparison } from '@/lib/public-comparison';

export type ComparisonEntry = { id: string; status: ComparisonResult['status'] | 'loading'; product?: PublicProduct; fingerprint?: string; changed?: boolean; name?: string };
type Update = (entries: ComparisonEntry[]) => ComparisonEntry[];
const EMPTY: ComparisonEntry[] = [];
type ComparisonContextValue = {
  selections: Record<string, ComparisonEntry[]>;
  saved: Record<string, SavedComparison | null>;
  prepared: Record<string, boolean>;
  update: (country: string, updater: Update, syncUrl?: boolean) => void;
  prepare: (country: string) => void;
  save: (country: string, entries: ComparisonEntry[]) => Promise<void>;
  forget: (country: string) => void;
  revision: number;
  refresh: () => void;
};
const ComparisonContext = createContext<ComparisonContextValue | null>(null);

export function ComparisonProvider({ children }: { children: ReactNode }) {
  const [selections, setSelections] = useState<Record<string, ComparisonEntry[]>>({});
  const [saved, setSaved] = useState<Record<string, SavedComparison | null>>({});
  const [prepared, setPrepared] = useState<Record<string, boolean>>({});
  const preparedRef = useRef(new Set<string>());
  const [revision, setRevision] = useState(0);
  const selectionsRef = useRef(selections);
  const update = useCallback((country: string, updater: Update, syncUrl = false) => {
    const previous = selectionsRef.current;
    const entries = updater(previous[country] ?? EMPTY);
    selectionsRef.current = { ...previous, [country]: entries };
    setSelections(selectionsRef.current);
    if (syncUrl && window.location.pathname === '/compare') {
      const scope = parseComparison(new URLSearchParams(window.location.search));
      if (scope.countryCode === country) window.history.replaceState(null, '', comparisonHref(entries.map(item => item.id), scope));
    }
  }, []);
  const prepare = useCallback((country: string) => {
    if (preparedRef.current.has(country)) return;
    preparedRef.current.add(country);
    let value: SavedComparison | null = null;
    try { value = readSavedComparison(localStorage.getItem(`${COMPARISON_STORAGE_KEY}.${country}`), country); } catch { /* Browsing works without storage. */ }
    setSaved(current => ({ ...current, [country]: value }));
    setPrepared(current => ({ ...current, [country]: true }));
  }, []);
  const save = useCallback(async (country: string, entries: ComparisonEntry[]) => {
    if (!entries.length || entries.some(item => item.status !== 'ready' || !item.product)) throw new Error('Unavailable comparison');
    const items = await Promise.all(entries.map(async item => ({ id: item.id, fingerprint: await comparisonFingerprint(item.product!), name: item.product!.product_name.slice(0, 300) })));
    const value = { countryCode: country, items };
    localStorage.setItem(`${COMPARISON_STORAGE_KEY}.${country}`, JSON.stringify({ version: 1, ...value }));
    setSaved(current => ({ ...current, [country]: value }));
    update(country, current => current.map(item => {
      const original = entries.find(entry => entry.id === item.id);
      const baseline = items.find(entry => entry.id === item.id);
      return baseline && original?.product === item.product ? { ...item, fingerprint: baseline.fingerprint, changed: false } : item;
    }));
  }, [update]);
  const forget = useCallback((country: string) => {
    localStorage.removeItem(`${COMPARISON_STORAGE_KEY}.${country}`);
    setSaved(current => ({ ...current, [country]: null }));
  }, []);
  const refresh = useCallback(() => setRevision(value => value + 1), []);
  const value = useMemo(() => ({ selections, saved, prepared, update, prepare, save, forget, revision, refresh }), [selections, saved, prepared, update, prepare, save, forget, revision, refresh]);
  return <ComparisonContext.Provider value={value}>{children}<Suspense fallback={null}><ComparisonSync /></Suspense></ComparisonContext.Provider>;
}

export function useComparison(countryCode: string) {
  const context = useContext(ComparisonContext);
  if (!context) throw new Error('ComparisonProvider is required');
  const { prepare } = context;
  useEffect(() => prepare(countryCode), [countryCode, prepare]);
  const entries = context.selections[countryCode] ?? EMPTY;
  return { ...context, entries, savedList: context.saved[countryCode] ?? null, ready: !!context.prepared[countryCode],
    toggle(product: PublicProduct) {
      if (product.country_code !== countryCode || product.status !== 'active') return;
      context.update(countryCode, current => current.some(item => item.id === product.product_id)
        ? current.filter(item => item.id !== product.product_id)
        : current.length < MAX_COMPARE_PRODUCTS ? [...current, { id: product.product_id, product, name: product.product_name, status: 'ready' }] : current, true);
    },
    restoreSaved() {
      const list = context.saved[countryCode];
      if (!list) return;
      context.update(countryCode, () => list.items.map(item => ({ ...item, status: 'loading' })), true);
      context.refresh();
    },
    remove(id: string) { context.update(countryCode, current => current.filter(item => item.id !== id), true); },
    clear() { context.update(countryCode, () => [], true); }
  };
}

function ComparisonSync() {
  const params = useSearchParams();
  const pathname = usePathname();
  const query = params.toString();
  const scope = parseComparison(new URLSearchParams(query));
  const { countryCode, locale } = scope;
  const { entries, ready, savedList, update, revision, refresh } = useComparison(countryCode);
  const idsKey = entries.map(item => item.id).join(',');
  const compareVisit = useRef('');
  // URL restoration replaces the current comparison, never merges an arbitrary fifth item.
  useEffect(() => {
    if (pathname !== '/compare') { compareVisit.current = ''; return; }
    if (!ready) return;
    const firstVisit = compareVisit.current !== countryCode;
    compareVisit.current = countryCode;
    const parsed = parseComparison(new URLSearchParams(query));
    if (!parsed.valid) return;
    const restoreIds = parsed.ids.length ? parsed.ids : firstVisit && savedList ? savedList.items.map(item => item.id) : [];
    if (!restoreIds.length) return;
    update(countryCode, current => {
      if (!parsed.ids.length && current.length) return current;
      return restoreIds.map(id => current.find(item => item.id === id)
        ?? { id, status: 'loading', fingerprint: savedList?.items.find(item => item.id === id)?.fingerprint, name: savedList?.items.find(item => item.id === id)?.name });
    }, !parsed.ids.length);

  }, [countryCode, pathname, query, ready, savedList, update]);

  useEffect(() => {
    if (pathname.startsWith('/admin') || !idsKey) return;
    const ids = idsKey.split(',');
    const controller = new AbortController();
    let previousEntries: ComparisonEntry[] = [];
    update(countryCode, current => { previousEntries = current; return current.map(item => ({ ...item, status: 'loading' })); });
    const timer = window.setTimeout(() => controller.abort(), 12000);
    let disposed = false;
    async function check() {
      try {
        const response = await fetch(comparisonHref(ids, { countryCode, locale }).replace('/compare?', '/api/public/compare?'), { cache: 'no-store', signal: controller.signal });
        if (!response.ok) throw new Error('Comparison unavailable');
        const { items } = await response.json() as { items: ComparisonResult[] };
        if (!Array.isArray(items) || items.length !== ids.length || items.some((item, index) => item.id !== ids[index]
          || !['ready', 'missing', 'error'].includes(item.status)
          || (item.status === 'ready' && (!item.product || item.product.product_id !== item.id || item.product.country_code !== countryCode || item.product.status !== 'active')))) throw new Error('Invalid comparison response');
        const fingerprints = await Promise.all(items.map(async item => item.product ? comparisonFingerprint(item.product) : undefined));
        const baselines = await Promise.all(previousEntries.map(async entry => ({ id: entry.id,
          fingerprint: entry.fingerprint ?? (entry.product ? await comparisonFingerprint(entry.product) : undefined) })));
        if (disposed) return;
        // Build from current entries so an in-flight read cannot resurrect removals.
        update(countryCode, current => current.map(entry => {
          const index = items.findIndex(item => item.id === entry.id);
          if (index < 0) return entry;
          const item = items[index];
          const fingerprint = entry.fingerprint ?? baselines.find(item => item.id === entry.id)?.fingerprint ?? fingerprints[index];
          return { ...entry, ...item, product: item.product, name: item.product?.product_name ?? entry.name, fingerprint,
            changed: item.status === 'ready' && !!fingerprint && fingerprint !== fingerprints[index] };
        }));
      } catch {
        if (!disposed) update(countryCode, current => current.map(item => ({ ...item, status: 'error', product: undefined })));
      } finally { window.clearTimeout(timer); }
    }
    void check();
    return () => { disposed = true; controller.abort(); window.clearTimeout(timer); };
  }, [countryCode, locale, idsKey, pathname, revision, update]);

  useEffect(() => {
    const recheck = () => { if (document.visibilityState === 'visible') refresh(); };
    document.addEventListener('visibilitychange', recheck);
    window.addEventListener('pageshow', recheck);
    return () => { document.removeEventListener('visibilitychange', recheck); window.removeEventListener('pageshow', recheck); };
  }, [refresh]);
  return null;
}
