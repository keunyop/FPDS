import { BankLogo } from '@/components/fpds/public/bank-logo';

// Factual identities of the accounts discussed; no rates or ranking.
export function BlogVisual({ banks, issue }: { banks: { code: string; bank: string }[]; issue: string }) {
  return <div className="flex h-full min-h-56 flex-col justify-between border border-border bg-secondary/60 p-6 md:p-8" aria-hidden="true">
    <div className="flex items-center justify-between gap-4 font-mono text-xs text-secondary-foreground"><span>SWITCHABANK / JOURNAL</span><span>{issue}</span></div>
    <div className="grid grid-cols-3 divide-x divide-primary/20 py-9">
      {banks.map(({ code, bank }) =>
        <div key={code} className="flex min-w-0 flex-col items-center gap-3 px-2">
          <BankLogo bankCode={code} bankName={bank} size="sm" />
          <span className="text-center text-xs font-medium text-secondary-foreground">{bank}</span>
        </div>)}
    </div>
    <div className="h-1 w-12 bg-primary" />
  </div>;
}
