import { getPublicRateMetric, type PublicRate } from './public-rate.ts';

export type RatePresentation = { label: string; value: string; details?: string; entries?: { label: string; value: string }[] };
const COPY = {
  en: { schedule: 'Rates by term / amount', conditions: 'Rate details & conditions' },
  ko: { schedule: '기간·금액별 금리', conditions: '금리 상세 및 적용 조건' },
  ja: { schedule: '期間・金額別の金利', conditions: '金利の詳細・適用条件' }
};
export function ratePresentationCopy(locale: string) { return COPY[locale === 'ko' || locale === 'ja' ? locale : 'en']; }

/** Presentation only: exact source spans never become comparison or calculator rates. */
export function presentPublicRate(product: Parameters<typeof getPublicRateMetric>[0], locale: string): RatePresentation {
  const metric = getPublicRateMetric(product, locale);
  const source = product.rate?.source_text || product.purchase_interest_rate_summary || product.interest_rate_summary || product.mortgage_rate || product.interest_rate;
  if (!source) return metric;
  const result: RatePresentation = { ...metric, details: source };
  if (product.rate?.kind === 'absolute') return result;
  const kind: PublicRate['kind'] = product.rate?.kind ?? 'unknown';
  // A literal range retains BOTH endpoints. Never select its lowest number.
  const range = source.match(/(?<![\d.])\d+(?:\.\d+)?\s*%\s*(?:-|–|to)\s*\d+(?:\.\d+)?\s*%/i);
  if (kind === 'range' && range) return { ...result, value: range[0].replace(/\s+/g, ' ') };
  const entries: { label: string; value: string }[] = [];
  // Preserve exact term and any benchmark formula beside each disclosed rate.
  for (const match of source.matchAll(/(\d+[- ]year\s+(?:closed|open)(?:\s*\([^)]*\))?)\s+(\d+(?:\.\d+)?\s*%)/gi)) {
    const following = source.slice(match.index! + match[0].length);
    if (/^\s*(?:down\s*payment|LTV|CLTV|discount|cash\s*back|fee)\b/i.test(following)) continue;
    entries.push({ label: match[1], value: `${match[2]}${/APR \(%\)/.test(source) ? ' APR' : ''}` });
  }
  // Explicit multiline table headers bind units and open/closed scope. No naked numbers.
  if (!entries.length && /Fixed rate \(%\)/i.test(source)) {
    const lines = source.split('\n').map(line => line.trim()).filter(Boolean);
    let scope = '';
    for (let i = 0; i < lines.length - 2; i++) {
      if (/^(Open|Closed|Convertible)\b/i.test(lines[i])) scope = lines[i];
      if (/^(?:Promotional rate - )?\d+\s+(?:months?|years?)$/i.test(lines[i]) && /^Fixed rate \(%\)$/i.test(lines[i+1]) && /^\d+(?:\.\d+)?$/.test(lines[i+2])) {
        entries.push({ label: `${scope} · ${lines[i]}`, value: `${lines[i+2]}%` });
      }
    }
  }
  // Credit-limit rows remain tied to their amount and stated formula.
  if (!entries.length) for (const match of source.matchAll(/(ALOC\+\s+(?:Quick|Max)\s+\$[\d,]+\s+(?:to\s+\$[\d,]+|and greater)(?:\s*\([^)]*\))?)\s+(\d+(?:\.\d+)?%)/gi)) {
    entries.push({ label: match[1], value: match[2] });
  }
  if (entries.length) return { ...result, value: ratePresentationCopy(locale).schedule, entries };
  // A single explicitly stated benchmark formula is readable without inventing today's prime.
  const formulas = [...source.matchAll(/(?:[\w]+(?: Bank)?[’']?s?\s+)?(?:Prime(?: rate)?|Base Rate)\s*(?:plus|minus|[+−-])\s*\d*(?:\.\d+)?\s*%/gi)].map(match => match[0]);
  const unique = [...new Set(formulas)];
  if (kind === 'reference' && unique.length === 1) return { ...result, value: unique[0] };
  // An adjacent quoted rate and explicitly labelled APR are distinct numbers.
  const apr = source.match(/(?:^|\n)(\d+(?:\.\d+)?%)\s*\n(\d+(?:\.\d+)?%)\s+APR\b/);
  if (kind === 'conditional' && apr) return { ...result, value: `${apr[1]} · APR ${apr[2]}` };
  // Unrecognized prose remains fully readable in the disclosure, never guessed.
  return { ...result, value: source.length <= 65 ? source : metric.label };
}
