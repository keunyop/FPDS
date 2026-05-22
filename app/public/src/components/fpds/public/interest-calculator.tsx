"use client";

import { Calculator } from "lucide-react";
import { useMemo, useState } from "react";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";

type InterestCalculatorProps = {
  currency: string;
  locale: string;
  minimumBalance: number | null;
  minimumDeposit: number | null;
  productType: string;
  rate: number | null;
  termLengthDays: number | null;
};

export function InterestCalculator({
  currency,
  locale,
  minimumBalance,
  minimumDeposit,
  productType,
  rate,
  termLengthDays,
}: InterestCalculatorProps) {
  const startingAmount = firstFiniteNumber(minimumDeposit, minimumBalance, 10000);
  const [amount, setAmount] = useState(String(Math.max(0, startingAmount)));
  const parsedAmount = Number(amount.replace(/,/g, ""));
  const annualRate = Number.isFinite(rate ?? NaN) ? Number(rate) : null;
  const termYears = productType === "gic" && Number.isFinite(termLengthDays) && termLengthDays ? termLengthDays / 365 : 1;
  const estimatedInterest = annualRate === null || !Number.isFinite(parsedAmount) ? null : parsedAmount * (annualRate / 100) * termYears;
  const labels = useMemo(() => calculatorLabels(locale), [locale]);

  return (
    <Card>
      <CardHeader>
        <CardDescription className="flex items-center gap-2">
          <Calculator className="size-4" aria-hidden="true" />
          {labels.eyebrow}
        </CardDescription>
        <CardTitle className="text-base">{labels.title}</CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4">
        <label className="grid gap-2 text-sm">
          <span className="font-medium text-foreground">{labels.amount}</span>
          <Input
            className="h-10 rounded-lg bg-background"
            inputMode="decimal"
            min="0"
            onChange={(event) => setAmount(event.target.value)}
            type="number"
            value={amount}
          />
        </label>
        <dl className="grid gap-3 rounded-lg border border-border bg-muted/25 p-4 sm:grid-cols-3">
          <CalculatorFact label={labels.rate} value={annualRate === null ? labels.notAvailable : `${annualRate.toFixed(2).replace(/\.?0+$/, "")}%`} />
          <CalculatorFact label={labels.term} value={formatTermYears(termYears, locale)} />
          <CalculatorFact
            label={labels.interest}
            value={estimatedInterest === null ? labels.notAvailable : formatCurrency(estimatedInterest, currency, locale)}
          />
        </dl>
        <p className="text-xs leading-5 text-muted-foreground">{labels.note}</p>
      </CardContent>
    </Card>
  );
}

function CalculatorFact({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-xs font-medium text-muted-foreground">{label}</dt>
      <dd className="mt-1 text-base font-semibold tabular-nums text-foreground">{value}</dd>
    </div>
  );
}

function calculatorLabels(locale: string) {
  if (locale === "ko") {
    return {
      amount: "예금 금액",
      eyebrow: "이자 계산기",
      interest: "예상 이자",
      note: "표시된 연 금리를 기준으로 한 단순 추정치입니다. 실제 이자, 복리, 세금, 가입 조건은 가입 시점에 달라질 수 있습니다.",
      notAvailable: "n/a",
      rate: "금리",
      term: "기간",
      title: "예상 이자 계산",
    };
  }
  if (locale === "ja") {
    return {
      amount: "Deposit amount",
      eyebrow: "Interest calculator",
      interest: "Estimated interest",
      note: "Simple estimate using the displayed annual rate. Actual interest, compounding, tax, and eligibility can differ at signup.",
      notAvailable: "n/a",
      rate: "Rate",
      term: "Term",
      title: "Estimate interest",
    };
  }
  return {
    amount: "Deposit amount",
    eyebrow: "Interest calculator",
    interest: "Estimated interest",
    note: "Simple estimate using the displayed annual rate. Actual interest, compounding, tax, and eligibility can differ at signup.",
    notAvailable: "n/a",
    rate: "Rate",
    term: "Term",
    title: "Estimate interest",
  };
}

function formatCurrency(value: number, currency: string, locale: string) {
  if (!Number.isFinite(value)) {
    return calculatorLabels(locale).notAvailable;
  }
  return new Intl.NumberFormat(intlLocale(locale), {
    currency: normalizeCurrency(currency),
    maximumFractionDigits: 2,
    style: "currency",
  }).format(value);
}

function formatTermYears(termYears: number, locale: string) {
  if (!Number.isFinite(termYears) || termYears <= 0) {
    return "1 year";
  }
  const value = Number.isInteger(termYears) ? String(termYears) : termYears.toFixed(2).replace(/\.?0+$/, "");
  if (locale === "ko" || locale === "ja") {
    return locale === "ko" ? `${value}년` : `${value}年`;
  }
  return `${value} year${value === "1" ? "" : "s"}`;
}

function intlLocale(locale: string) {
  if (locale === "ko") {
    return "ko-KR";
  }
  if (locale === "ja") {
    return "ja-JP";
  }
  return "en-CA";
}

function firstFiniteNumber(...values: Array<number | null>) {
  return values.find((value): value is number => typeof value === "number" && Number.isFinite(value)) ?? 10000;
}

function normalizeCurrency(currency: string) {
  const normalized = currency.trim().toUpperCase();
  return /^[A-Z]{3}$/.test(normalized) ? normalized : "CAD";
}
