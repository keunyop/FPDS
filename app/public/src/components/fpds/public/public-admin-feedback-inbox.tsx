import Link from 'next/link';
import type { ReactNode } from 'react';

export type PublicAdminFeedbackItem = {
  category: string;
  country_code: string;
  details: string | null;
  locale: string;
  product: {
    bank_code: string;
    bank_name: string;
    product_id: string;
    product_name: string;
    product_type: string;
  } | null;
  snapshot_id: string | null;
  submission_id: string;
  submission_type: 'product_error' | 'site_feedback';
  submitted_at: string | null;
};

export type PublicAdminFeedbackResponse = {
  has_next_page: boolean;
  items: PublicAdminFeedbackItem[];
  page: number;
  page_size: number;
  summary: {
    product_error_items: number;
    site_feedback_items: number;
    total_items: number;
  };
  total_items: number;
  total_pages: number;
};

export type PublicAdminFeedbackFilters = {
  category: string;
  countryCode: string;
  page: number;
  query: string;
  submissionType: string;
};

type PublicAdminFeedbackInboxProps = {
  feedback: PublicAdminFeedbackResponse | null;
  filters: PublicAdminFeedbackFilters;
};

const CATEGORIES = [
  'incorrect_rate_or_fee',
  'incorrect_product_details',
  'outdated_information',
  'missing_information',
  'broken_link',
  'content_issue',
  'usability_issue',
  'feature_suggestion',
  'accessibility_issue',
  'other'
] as const;

const CATEGORY_LABELS: Record<string, string> = {
  accessibility_issue: 'Accessibility issue',
  broken_link: 'Broken link',
  content_issue: 'Content issue',
  feature_suggestion: 'Feature suggestion',
  incorrect_product_details: 'Incorrect product details',
  incorrect_rate_or_fee: 'Incorrect rate or fee',
  missing_information: 'Missing information',
  other: 'Other',
  outdated_information: 'Outdated information',
  usability_issue: 'Usability issue'
};

const fieldClass = 'h-11 min-w-0 rounded-lg border border-input bg-background px-3 text-sm font-normal outline-none focus-visible:border-ring focus-visible:ring-3 focus-visible:ring-ring/40';

export function PublicAdminFeedbackInbox({ feedback, filters }: PublicAdminFeedbackInboxProps) {
  if (!feedback) {
    return (
      <section aria-labelledby='feedback-inbox-title' className='border border-destructive/25 bg-destructive/5 p-5'>
        <h2 className='font-semibold text-destructive' id='feedback-inbox-title'>Feedback is temporarily unavailable</h2>
        <p className='mt-2 text-sm leading-6 text-muted-foreground'>Check the Public API credential, API deployment, and feedback storage migration.</p>
      </section>
    );
  }

  const firstItem = feedback.total_items === 0 ? 0 : (feedback.page - 1) * feedback.page_size + 1;
  const lastItem = Math.min(feedback.page * feedback.page_size, feedback.total_items);
  return (
    <section aria-labelledby='feedback-inbox-title' className='grid gap-5'>
      <div>
        <h2 className='text-xl font-semibold tracking-[-0.02em]' id='feedback-inbox-title'>Feedback inbox</h2>
        <p className='mt-1 max-w-3xl text-sm leading-6 text-muted-foreground'>Anonymous product error reports and site feedback. Product context is copied from the active Public snapshot at submission time.</p>
      </div>

      <div className='grid gap-3 sm:grid-cols-3'>
        <Metric label='All feedback' value={feedback.summary.total_items} />
        <Metric label='Product errors' value={feedback.summary.product_error_items} />
        <Metric label='Site feedback' value={feedback.summary.site_feedback_items} />
      </div>

      <FeedbackFilters filters={filters} />

      <div className='flex flex-wrap items-center justify-between gap-2 border-b border-foreground/15 pb-3'>
        <p className='text-sm font-semibold'>Reports</p>
        <p className='text-xs text-muted-foreground'>Showing {firstItem}-{lastItem} of {feedback.total_items}</p>
      </div>

      {feedback.items.length === 0 ? (
        <div className='border border-dashed border-border bg-card/55 px-5 py-8'>
          <h3 className='font-semibold'>No feedback matches these filters</h3>
          <p className='mt-2 text-sm text-muted-foreground'>Clear the feedback filters or select another country.</p>
          <Link className='mt-4 inline-flex min-h-11 items-center rounded-lg border border-border bg-background px-4 text-sm font-semibold hover:bg-muted' href={resetHref(filters.countryCode)}>Clear feedback filters</Link>
        </div>
      ) : (
        <>
          <div className='grid gap-3 lg:hidden'>
            {feedback.items.map((item) => <FeedbackCard item={item} key={item.submission_id} />)}
          </div>
          <FeedbackTable items={feedback.items} />
          <Pagination feedback={feedback} filters={filters} />
        </>
      )}
    </section>
  );
}

function FeedbackFilters({ filters }: { filters: PublicAdminFeedbackFilters }) {
  return (
    <form className='grid gap-3 rounded-lg border border-border bg-card/65 p-4 md:grid-cols-[minmax(12rem,1.4fr)_minmax(10rem,0.8fr)_minmax(12rem,1fr)_auto] md:items-end' method='get'>
      {filters.countryCode ? <input name='country_code' type='hidden' value={filters.countryCode} /> : null}
      <label className='grid gap-1.5 text-sm font-semibold'>
        Search
        <input className={fieldClass} defaultValue={filters.query} maxLength={200} name='feedback_q' placeholder='Details, product, bank, category, or ID' type='search' />
      </label>
      <label className='grid gap-1.5 text-sm font-semibold'>
        Type
        <select className={fieldClass} defaultValue={filters.submissionType} name='feedback_type'>
          <option value=''>All types</option>
          <option value='product_error'>Product error</option>
          <option value='site_feedback'>Site feedback</option>
        </select>
      </label>
      <label className='grid gap-1.5 text-sm font-semibold'>
        Category
        <select className={fieldClass} defaultValue={filters.category} name='feedback_category'>
          <option value=''>All categories</option>
          {CATEGORIES.map((category) => <option key={category} value={category}>{CATEGORY_LABELS[category]}</option>)}
        </select>
      </label>
      <div className='flex flex-wrap gap-2'>
        <button className='inline-flex min-h-11 items-center rounded-lg bg-primary px-4 text-sm font-semibold text-primary-foreground' type='submit'>Apply</button>
        <Link className='inline-flex min-h-11 items-center rounded-lg border border-border bg-background px-4 text-sm font-semibold hover:bg-muted' href={resetHref(filters.countryCode)}>Clear</Link>
      </div>
    </form>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return <article className='border border-foreground/15 bg-card/75 p-4'><p className='text-xs font-semibold text-muted-foreground'>{label}</p><p className='mt-2 font-display text-3xl font-semibold tabular-nums'>{value.toLocaleString()}</p></article>;
}

function FeedbackCard({ item }: { item: PublicAdminFeedbackItem }) {
  return (
    <article className='grid gap-4 border border-border bg-card/75 p-4'>
      <div className='flex flex-wrap items-start justify-between gap-3'>
        <div>
          <span className={typeBadgeClass(item.submission_type)}>{typeLabel(item.submission_type)}</span>
          <p className='mt-2 text-sm font-semibold'>{categoryLabel(item.category)}</p>
        </div>
        <div className='text-right text-xs text-muted-foreground'>
          <p className='font-mono'>{formatSubmittedAt(item.submitted_at)}</p>
          <p className='mt-1'>{item.country_code}</p>
        </div>
      </div>
      <ProductContext item={item} />
      <div>
        <p className='text-xs font-semibold text-muted-foreground'>Details</p>
        <p className='mt-1 whitespace-pre-wrap break-words text-sm leading-6'>{item.details ?? 'No details provided.'}</p>
      </div>
      <div className='border-t border-border pt-3 text-[11px] text-muted-foreground'>
        <p className='break-all font-mono'>{item.submission_id}</p>
        <p className='mt-1'>Locale: {item.locale.toUpperCase()}</p>
        {item.snapshot_id ? <p className='mt-1 break-all font-mono'>{item.snapshot_id}</p> : null}
      </div>
    </article>
  );
}

function FeedbackTable({ items }: { items: PublicAdminFeedbackItem[] }) {
  return (
    <div aria-label='Feedback reports' className='hidden max-w-full overflow-x-auto border border-border lg:block' role='region' tabIndex={0}>
      <table className='w-full min-w-[68rem] table-fixed text-left text-sm'>
        <thead className='bg-muted/60 text-xs text-muted-foreground'>
          <tr>
            <Th className='w-44'>Submitted</Th>
            <Th className='w-52'>Type / category</Th>
            <Th className='w-72'>Product</Th>
            <Th>Details</Th>
            <Th className='w-52'>Reference</Th>
          </tr>
        </thead>
        <tbody className='divide-y divide-border'>
          {items.map((item) => (
            <tr className='align-top' key={item.submission_id}>
              <Td>
                <p className='font-mono text-xs font-semibold'>{formatSubmittedAt(item.submitted_at)}</p>
                <p className='mt-2 text-xs text-muted-foreground'>{item.country_code}</p>
              </Td>
              <Td>
                <span className={typeBadgeClass(item.submission_type)}>{typeLabel(item.submission_type)}</span>
                <p className='mt-2 font-semibold leading-5'>{categoryLabel(item.category)}</p>
              </Td>
              <Td><ProductContext item={item} /></Td>
              <Td><p className='max-w-xl whitespace-pre-wrap break-words leading-6'>{item.details ?? 'No details provided.'}</p></Td>
              <Td>
                <p className='break-all font-mono text-[11px]'>{item.submission_id}</p>
                <p className='mt-2 text-xs text-muted-foreground'>Locale: {item.locale.toUpperCase()}</p>
                {item.snapshot_id ? <p className='mt-1 break-all font-mono text-[10px] text-muted-foreground'>{item.snapshot_id}</p> : null}
              </Td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function ProductContext({ item }: { item: PublicAdminFeedbackItem }) {
  if (!item.product) return <p className='text-sm text-muted-foreground'>General site feedback</p>;
  return (
    <div className='grid gap-1 text-sm'>
      <p className='font-semibold'>{item.product.bank_name} · {item.product.product_name}</p>
      <p className='text-xs text-muted-foreground'>{humanize(item.product.product_type)} · {item.product.bank_code}</p>
      <p className='break-all font-mono text-[11px] text-muted-foreground'>{item.product.product_id}</p>
    </div>
  );
}

function Pagination({ feedback, filters }: { feedback: PublicAdminFeedbackResponse; filters: PublicAdminFeedbackFilters }) {
  if (feedback.total_pages <= 1) return null;
  return (
    <nav aria-label='Feedback pages' className='flex flex-wrap items-center justify-between gap-3 border-t border-border pt-4'>
      <p className='text-xs text-muted-foreground'>Page {feedback.page} of {feedback.total_pages}</p>
      <div className='flex gap-2'>
        {feedback.page > 1 ? <Link className='inline-flex min-h-11 items-center rounded-lg border border-border bg-background px-4 text-sm font-semibold hover:bg-muted' href={buildFeedbackHref(filters, feedback.page - 1)}>Previous</Link> : <span aria-disabled='true' className='inline-flex min-h-11 items-center rounded-lg border border-border bg-muted px-4 text-sm font-semibold text-muted-foreground opacity-60'>Previous</span>}
        {feedback.has_next_page ? <Link className='inline-flex min-h-11 items-center rounded-lg border border-border bg-background px-4 text-sm font-semibold hover:bg-muted' href={buildFeedbackHref(filters, feedback.page + 1)}>Next</Link> : <span aria-disabled='true' className='inline-flex min-h-11 items-center rounded-lg border border-border bg-muted px-4 text-sm font-semibold text-muted-foreground opacity-60'>Next</span>}
      </div>
    </nav>
  );
}

function typeBadgeClass(type: PublicAdminFeedbackItem['submission_type']) {
  const tone = type === 'product_error'
    ? 'border-warning/25 bg-warning-soft text-warning'
    : 'border-verification/20 bg-verification-soft text-verification';
  return 'inline-flex rounded-full border px-2.5 py-1 text-xs font-semibold ' + tone;
}

function typeLabel(type: PublicAdminFeedbackItem['submission_type']) {
  return type === 'product_error' ? 'Product error' : 'Site feedback';
}

function categoryLabel(category: string) {
  return CATEGORY_LABELS[category] ?? humanize(category);
}

function humanize(value: string) {
  return value.replaceAll('-', ' ').replaceAll('_', ' ').replace(/\b\w/g, (character) => character.toUpperCase());
}

function formatSubmittedAt(value: string | null) {
  if (!value) return '—';
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return value;
  return parsed.toISOString().replace('T', ' ').slice(0, 19);
}

function buildFeedbackHref(filters: PublicAdminFeedbackFilters, page: number) {
  const params = new URLSearchParams();
  if (filters.countryCode) params.set('country_code', filters.countryCode);
  if (filters.query) params.set('feedback_q', filters.query);
  if (filters.submissionType) params.set('feedback_type', filters.submissionType);
  if (filters.category) params.set('feedback_category', filters.category);
  if (page > 1) params.set('feedback_page', String(page));
  const query = params.toString();
  return query ? '/admin?' + query : '/admin';
}

function resetHref(countryCode: string) {
  return countryCode ? '/admin?country_code=' + encodeURIComponent(countryCode) : '/admin';
}

function Th({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <th className={'whitespace-nowrap px-3 py-3 font-semibold ' + className}>{children}</th>;
}

function Td({ children }: { children: ReactNode }) {
  return <td className='px-3 py-4'>{children}</td>;
}
