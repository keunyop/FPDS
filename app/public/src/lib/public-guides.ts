import type { PublicLocale } from './public-locale.ts';
import { curatedCatalogHref, type CuratedSlug } from './public-curated.ts';

export const GUIDE_SLUGS = ['base-and-promotional-rates', 'monthly-fee-waivers', 'gic-maturity-and-withdrawals', 'switching-bank-accounts'] as const;
export type GuideSlug = typeof GUIDE_SLUGS[number];
export type GuidePath = '/guides' | `/guides/${GuideSlug}`;
export const GUIDE_REVIEWED_AT = '2026-09-26';
export const GUIDE_COMPARISONS: Record<GuideSlug, CuratedSlug> = {
  'base-and-promotional-rates': 'savings-accounts',
  'monthly-fee-waivers': 'no-monthly-fee-chequing',
  'gic-maturity-and-withdrawals': '1-year-gic',
  'switching-bank-accounts': 'no-monthly-fee-chequing'
};
export function isGuideSlug(value: string): value is GuideSlug {
  return (GUIDE_SLUGS as readonly string[]).includes(value);
}
export function guideHref(slug: GuideSlug | null, locale: string) {
  return `${slug ? `/guides/${slug}` : '/guides'}${locale === 'ko' || locale === 'ja' ? `?locale=${locale}` : ''}`;
}
export function isGuideIndexableQuery(query: Record<string, string | string[] | undefined>) {
  return Object.entries(query).every(([key, value]) => key === 'locale' && typeof value === 'string' && ['en', 'ko', 'ja'].includes(value));
}
export function guideCountryDestination(path: string, locale: string, country: string) {
  if (country === 'CA' || (path !== '/guides' && !path.startsWith('/guides/'))) return null;
  const slug = path.slice('/guides/'.length);
  if (isGuideSlug(slug)) return curatedCatalogHref(GUIDE_COMPARISONS[slug], locale, country);
  const params = new URLSearchParams({ country_code: country });
  if (locale === 'ko' || locale === 'ja') params.set('locale', locale);
  return `/products?${params}`;
}
export const GUIDE_COPY = {
  en: {
    nav: 'Comparison guides', scope: 'Canada · Comparison guides', title: 'Understand the terms. Then compare.',
    intro: 'Start with a question. You do not need to own a product to compare.', newcomer: 'New to comparing? Start here',
    read: 'Read guide', compare: 'Put it into practice', table: 'Open comparison table', browse: 'Browse related products',
    next: 'Select products in the table or catalog, open your comparison, then check the bank’s latest terms. With two deposits selected, you can also try the calculator.',
    sources: 'Sources', sourceLanguage: 'Official guidance in English', checked: 'Guide sources checked',
    editorial: 'About these guides', publisher: 'Published by SwitchaBank, the comparison service on this site.',
    method: 'These guides use AI-assisted writing and translation, checked against the linked official sources. They have not received independent financial-expert review. They explain comparisons, not individual financial advice.',
    language: 'Bank names and product conditions stay in their source language. The guide date is separate from each product’s verification date.',
    corrections: 'Report a correction through site feedback, with the guide title and passage. Corrections are checked against the source; confirmed changes update the text and guide review date.',
    topics: {
      'base-and-promotional-rates': 'Base and promotional rates',
      'monthly-fee-waivers': 'Reading monthly fee waivers',
      'gic-maturity-and-withdrawals': 'GIC maturity and early withdrawals',
      'switching-bank-accounts': 'Switching bank accounts in Canada'
    }
  },
  ko: {
    nav: '비교 가이드', scope: '캐나다 · 비교 가이드', title: '조건을 이해하고 비교하세요.',
    intro: '궁금한 항목부터 시작하세요. 보유 상품이 없어도 비교할 수 있습니다.', newcomer: '처음 비교하시나요? 여기서 시작하세요',
    read: '가이드 읽기', compare: '이제 비교해 보세요', table: '비교 표 보기', browse: '관련 상품 목록 보기',
    next: '표나 목록에서 상품을 선택해 비교한 뒤 은행에서 최신 조건을 확인하세요. 예금 2개를 선택하면 계산기도 이용할 수 있습니다.',
    sources: '출처', sourceLanguage: '영문 공식 안내', checked: '가이드 출처 확인일',
    editorial: '가이드 작성·정정 안내', publisher: '발행: 이 사이트의 비교 서비스 SwitchaBank.',
    method: 'AI를 활용해 작성·번역하고 연결된 공식 출처와 대조했습니다. 독립된 금융 전문가의 검수는 받지 않았습니다. 비교를 돕는 일반 설명이며 개인별 금융 자문은 아닙니다.',
    language: '은행명과 상품 조건은 원문을 유지합니다. 가이드 확인일은 개별 상품의 확인일과 다릅니다.',
    corrections: '사이트 피드백에 가이드 제목과 수정할 문장을 남겨 주세요. 출처와 대조해 오류를 확인하면 본문과 가이드 확인일을 갱신합니다.',
    topics: {
      'base-and-promotional-rates': '기본 금리와 프로모션 금리',
      'monthly-fee-waivers': '월 수수료 면제 조건 읽기',
      'gic-maturity-and-withdrawals': 'GIC 만기와 중도 인출',
      'switching-bank-accounts': '캐나다 계좌 이전 전 확인할 항목'
    }
  },
  ja: {
    nav: '比較ガイド', scope: 'カナダ · 比較ガイド', title: '条件を理解してから比較。',
    intro: '気になる項目から始めましょう。利用中の商品がなくても比較できます。', newcomer: '比較が初めての方はこちら',
    read: 'ガイドを読む', compare: '実際に比較する', table: '比較表を見る', browse: '関連商品を見る',
    next: '表や一覧から商品を選んで比較し、銀行で最新の条件を確認してください。預金を2件選ぶと計算ツールも利用できます。',
    sources: '出典', sourceLanguage: '英語の公式案内', checked: 'ガイドの出典確認日',
    editorial: '作成・訂正について', publisher: '発行：このサイトの比較サービス SwitchaBank。',
    method: 'AIを活用して作成・翻訳し、リンク先の公式情報と照合しています。独立した金融専門家による監修は受けていません。比較のための一般的な説明であり、個別の金融アドバイスではありません。',
    language: '銀行名と商品条件は原文のまま表示します。ガイドの確認日と各商品の確認日は別です。',
    corrections: 'サイトへのフィードバックにガイド名と訂正が必要な箇所をお知らせください。出典と照合して誤りが確認された場合、本文とガイドの確認日を更新します。',
    topics: {
      'base-and-promotional-rates': '基本金利とキャンペーン金利',
      'monthly-fee-waivers': '月額手数料の免除条件を読む',
      'gic-maturity-and-withdrawals': 'GICの満期と中途解約',
      'switching-bank-accounts': 'カナダで口座を移す前の確認事項'
    }
  }
} satisfies Record<PublicLocale, object>;
export function guideCopy(locale: string) { return GUIDE_COPY[locale === 'ko' || locale === 'ja' ? locale : 'en']; }
