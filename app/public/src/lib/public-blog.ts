import type { PublicLocale } from './public-locale.ts';

export const BLOG_POSTS = [{
  slug: 'eq-bank-vs-tangerine-vs-td-savings',
  publishedAt: '2026-09-30',
  modifiedAt: '2026-09-30',
  sourcesCheckedAt: '2026-09-30',
  country: 'CA',
  minutes: 7
}] as const;
export type BlogSlug = typeof BLOG_POSTS[number]['slug'];
export type BlogPath = '/blog' | `/blog/${BlogSlug}`;
export function isBlogSlug(slug: string): slug is BlogSlug {
  return BLOG_POSTS.some(post => post.slug === slug);
}
export function blogHref(slug: BlogSlug | null, locale: string) {
  return `${slug ? `/blog/${slug}` : '/blog'}${locale === 'ko' || locale === 'ja' ? `?locale=${locale}` : ''}`;
}
export function isBlogIndexableQuery(query: Record<string, string | string[] | undefined>) {
  return Object.entries(query).every(([key, value]) => key === 'locale' && typeof value === 'string' && ['en', 'ko', 'ja'].includes(value));
}
// Editorial coverage is explicitly Canadian. Country changes leave the article.
export function blogCountryDestination(path: string, locale: string, country: string) {
  if (country === 'CA' || (path !== '/blog' && !path.startsWith('/blog/'))) return null;
  const params = new URLSearchParams({ country_code: country, product_type: 'savings' });
  if (locale === 'ko' || locale === 'ja') params.set('locale', locale);
  return `/products?${params}`;
}
export const BLOG_COPY = {
  en: {
    nav: 'Blog', heading: 'A clearer view of your banking.',
    intro: 'Bank comparisons, practical examples, and the small print that makes a difference.',
    scope: 'Canada · Savings', latest: 'Latest story', read: 'Read the comparison',
    minutes: 'min read', by: 'By SwitchaBank', published: 'Published', checked: 'Sources checked',
    contents: 'In this article', takeaway: 'The short version', comparison: 'Three accounts, three things to check',
    compare: 'Take the next step with real product details', compareBody: 'Browse the Canadian savings catalog, select available products, and compare their published terms. Check each product’s verification date and confirm the details with the bank.',
    action: 'Compare savings accounts', related: 'Go deeper', sources: 'Official sources',
    sourcesNote: 'Checked on the date shown above. Fees, offers and terms can change.',
    editorial: 'How this article was made', method: 'Published by SwitchaBank. Written and translated with AI assistance and checked against the linked official sources. It has not received independent financial-expert review. General information, not personal financial advice.',
    correction: 'Found something that needs correcting? Use site feedback and include the article title and passage.',
    disclosure: 'SwitchaBank receives no compensation from the institutions discussed in this article.',
    faq: 'Common questions', checklist: 'Before you move your money',
    tableHeaders: ['Account', 'Monthly fee', 'What changes the comparison'],
    home: 'Home', all: 'All articles', example: 'Illustrative example · CAD'
  },
  ko: {
    nav: '블로그', heading: '은행 선택, 조건부터 선명하게.',
    intro: '은행과 상품의 차이를 읽고, 실제 예시로 이해하고, 내게 필요한 조건을 직접 비교하세요.',
    scope: '캐나다 · 저축계좌', latest: '최신 글', read: '비교 글 읽기',
    minutes: '분 읽기', by: 'SwitchaBank 작성', published: '발행일', checked: '출처 확인일',
    contents: '이 글의 목차', takeaway: '먼저 읽는 핵심', comparison: '세 계좌, 서로 다른 확인 포인트',
    compare: '읽었다면, 실제 상품 조건을 비교해 보세요', compareBody: '캐나다 저축상품 목록에서 공개 중인 상품을 선택해 조건을 나란히 확인하세요. 상품별 확인일을 살펴보고 최종 조건은 은행에서 확인하세요.',
    action: '저축계좌 비교하기', related: '함께 읽으면 좋은 가이드', sources: '공식 출처',
    sourcesNote: '위 확인일을 기준으로 대조했습니다. 수수료·혜택·조건은 변경될 수 있습니다.',
    editorial: '작성 및 정정 안내', method: 'SwitchaBank가 발행하며, AI를 활용해 작성·번역하고 연결된 공식 출처와 대조했습니다. 독립된 금융 전문가의 검수는 받지 않았습니다. 일반 정보이며 개인별 금융 자문은 아닙니다.',
    correction: '수정이 필요한 내용을 발견하셨나요? 사이트 피드백에 글 제목과 해당 문장을 남겨 주세요.',
    disclosure: 'SwitchaBank는 이 글에서 다룬 금융기관으로부터 보상을 받지 않습니다.',
    faq: '자주 묻는 질문', checklist: '돈을 옮기기 전 확인할 항목',
    tableHeaders: ['계좌', '월 수수료', '비교를 달라지게 하는 조건'],
    home: '홈', all: '전체 글', example: '이해를 위한 가상 예시 · CAD'
  },
  ja: {
    nav: 'ブログ', heading: '銀行選びを、もっとわかりやすく。',
    intro: '銀行や商品の違いを、具体例と見落としやすい条件から読み解きます。',
    scope: 'カナダ · 貯蓄口座', latest: '最新の記事', read: '比較記事を読む',
    minutes: '分で読めます', by: '執筆：SwitchaBank', published: '公開日', checked: '出典確認日',
    contents: 'この記事の目次', takeaway: '最初に押さえるポイント', comparison: '3つの口座、異なる確認ポイント',
    compare: '実際の商品条件を比較してみましょう', compareBody: 'カナダの貯蓄商品一覧から公開中の商品を選び、条件を比較できます。各商品の確認日を読み、最新の条件は銀行で確認してください。',
    action: '貯蓄口座を比較する', related: 'あわせて読みたいガイド', sources: '公式の出典',
    sourcesNote: '上記の確認日に照合しました。手数料・特典・条件は変更される場合があります。',
    editorial: '作成・訂正について', method: '発行：SwitchaBank。AIを活用して作成・翻訳し、リンク先の公式情報と照合しました。独立した金融専門家による監修は受けていません。一般的な情報であり、個別の金融アドバイスではありません。',
    correction: '訂正が必要な場合は、サイトへのフィードバックに記事名と該当箇所をお知らせください。',
    disclosure: 'SwitchaBankは、この記事で扱う金融機関から報酬を受け取っていません。',
    faq: 'よくある質問', checklist: '資金を移す前のチェック',
    tableHeaders: ['口座', '月額手数料', '比較を左右する条件'],
    home: 'ホーム', all: '記事一覧', example: '仮定に基づく計算例 · CAD'
  }
} satisfies Record<PublicLocale, object>;
export function blogCopy(locale: string) { return BLOG_COPY[locale === 'ko' || locale === 'ja' ? locale : 'en']; }
