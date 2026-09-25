import type { CuratedSlug } from './public-curated.ts';

const COPY = {
  en: {
    shortcuts: 'Compare by purpose', feeLink: 'Compare monthly fees', savingsLink: 'Compare savings', gicLink: 'Compare GIC terms',
    scopeLabel: 'Comparison scope', scope: 'Canada · CAD', coverage: '{products} products · {banks} banks', product: 'Product', actions: 'Actions',
    baseRate: 'Base rate', offer: 'Promotions / conditions', transactions: 'Included transactions', withdrawals: 'Withdrawal conditions',
    minimumBalance: 'Minimum balance', monthlyFee: 'Base monthly fee', conditions: 'Conditions', minimum: 'Minimum deposit', termRate: '1-year rate',
    annual: 'Annual rates', apy: 'APY', zero: 'No base monthly fee', waiver: 'Monthly fee with waiver conditions', qualified: 'Promotional or qualified rates',
    redeemable: 'Redeemable', non_redeemable: 'Non-redeemable', checkBank: 'Check with the bank',
    compare: 'Add to comparison', selected: 'Added', viewCompare: 'View comparison',
    loading: 'Loading comparison…', pending: 'This comparison is not ready yet.', unavailable: 'Comparison data is temporarily unavailable.',
    pendingBody: 'Browse available products while we verify enough matching accounts.', browse: 'Browse products', retry: 'Try again',
    boundary: 'Published accounts in CAD; not the whole market. Check eligibility and current terms with the bank.',
    savingsNote: 'Base rates exclude promotional and bonus offers. Withdrawal limits and fees are shown only when disclosed.',
    feeNote: 'A $0 base monthly fee differs from a fee waived after meeting conditions. Transaction fees and eligibility may still apply.',
    gicNote: 'Only verified 12-month rates with the same rate basis and redemption terms are grouped together.',
    pages: {
      'savings-accounts': { title: 'Compare Canadian savings accounts', description: 'Compare CAD savings accounts by base rate, promotional conditions and withdrawals, with product check dates and official bank links.' },
      'no-monthly-fee-chequing': { title: 'Compare no-monthly-fee chequing accounts', description: 'Compare Canadian CAD chequing accounts with a $0 base monthly fee separately from accounts with conditional fee waivers.' },
      '1-year-gic': { title: 'Compare 1-year GICs in Canada', description: 'Compare verified CAD 12-month GIC rates by redemption terms, rate basis and minimum deposit.' }
    }
  },
  ko: {
    shortcuts: '목적별 비교', feeLink: '월 수수료 비교', savingsLink: 'Savings 비교', gicLink: 'GIC 기간별 비교',
    scopeLabel: '비교 범위', scope: '캐나다 · CAD', coverage: '상품 {products}개 · 은행 {banks}곳', product: '상품', actions: '비교·은행 확인',
    baseRate: '기본 금리', offer: '프로모션·우대 조건', transactions: '포함 거래', withdrawals: '인출 조건',
    minimumBalance: '최소 잔액', monthlyFee: '기본 월 수수료', conditions: '적용 조건', minimum: '최소 예치금', termRate: '1년 금리',
    annual: '연 금리', apy: 'APY', zero: '기본 월 수수료 0', waiver: '조건 충족 시 월 수수료 면제', qualified: '프로모션·조건부 금리',
    redeemable: '중도해지 가능', non_redeemable: '중도해지 불가', checkBank: '은행에서 확인',
    compare: '비교에 추가', selected: '추가됨', viewCompare: '선택 상품 비교',
    loading: '비교 정보를 불러오는 중…', pending: '비교 정보를 준비하고 있습니다.', unavailable: '비교 정보를 불러올 수 없습니다.',
    pendingBody: '비교 조건 확인 중인 상품은 기존 목록에서 살펴볼 수 있습니다.', browse: '상품 보기', retry: '다시 시도',
    boundary: '공개된 CAD 상품만 비교하며 전체 시장을 포함하지 않습니다. 가입 자격과 최신 조건은 은행에서 확인하세요.',
    savingsNote: '기본 금리와 프로모션·우대 금리를 구분합니다. 인출 제한과 비용은 공개된 정보만 표시합니다.',
    feeNote: '기본 월 수수료 0과 조건 충족 시 면제는 다릅니다. 거래 수수료와 가입 자격은 별도로 확인하세요.',
    gicNote: '확인된 12개월 금리만 연율 기준과 중도해지 조건별로 나누어 비교합니다.',
    pages: {
      'savings-accounts': { title: '캐나다 Savings 계좌 비교', description: 'CAD Savings 계좌의 기본 금리, 프로모션·우대 조건, 인출 조건과 상품별 확인일을 비교하고 은행 공식 페이지에서 확인하세요.' },
      'no-monthly-fee-chequing': { title: '월 수수료 없는 캐나다 Chequing 비교', description: '캐나다 CAD Chequing 계좌의 기본 월 수수료 0과 조건 충족 시 수수료 면제를 구분해 비교하세요.' },
      '1-year-gic': { title: '캐나다 1년 GIC 비교', description: '검증된 CAD 12개월 GIC 금리를 중도해지 조건, 연율 기준, 최소 예치금별로 비교하세요.' }
    }
  },
  ja: {
    shortcuts: '目的別に比較', feeLink: '月額手数料を比較', savingsLink: 'Savingsを比較', gicLink: 'GICを期間別に比較',
    scopeLabel: '比較範囲', scope: 'カナダ · CAD', coverage: '{products}商品 · {banks}銀行', product: '商品', actions: '比較・銀行で確認',
    baseRate: '基本金利', offer: 'キャンペーン・優遇条件', transactions: '利用可能な取引', withdrawals: '引出し条件',
    minimumBalance: '最低残高', monthlyFee: '基本月額手数料', conditions: '適用条件', minimum: '最低預入金額', termRate: '1年金利',
    annual: '年利', apy: 'APY', zero: '基本月額手数料が0', waiver: '条件付き月額手数料免除', qualified: 'キャンペーン・条件付き金利',
    redeemable: '中途解約可', non_redeemable: '中途解約不可', checkBank: '銀行で確認',
    compare: '比較に追加', selected: '追加済み', viewCompare: '選択した商品を比較',
    loading: '比較情報を読み込み中…', pending: '比較情報を準備しています。', unavailable: '比較情報を読み込めません。',
    pendingBody: '条件を確認中の商品は既存の商品一覧でご覧いただけます。', browse: '商品を見る', retry: '再試行',
    boundary: '公開されたCAD商品のみで、市場全体は網羅しません。対象条件と最新情報は銀行で確認してください。',
    savingsNote: '基本金利とキャンペーン・優遇金利を分けて比較します。引出し制限や費用は公開情報のみ表示します。',
    feeNote: '基本月額手数料0と条件付き免除は異なります。取引手数料や対象条件は別途確認してください。',
    gicNote: '確認済みの12か月金利を、年利の基準と中途解約条件ごとに比較します。',
    pages: {
      'savings-accounts': { title: 'カナダのSavings口座を比較', description: 'CAD Savings口座の基本金利、キャンペーン・優遇条件、引出し条件と確認日を比較し、銀行公式ページで確認できます。' },
      'no-monthly-fee-chequing': { title: '月額手数料のないカナダのChequingを比較', description: 'カナダのCAD Chequing口座を、基本月額手数料0と条件付き免除に分けて比較できます。' },
      '1-year-gic': { title: 'カナダの1年GICを比較', description: '確認済みのCAD 12か月GIC金利を、中途解約条件、年利の基準、最低預入金額別に比較できます。' }
    }
  }
} as const;
export function curatedCopy(locale: string) { return COPY[locale === 'ko' || locale === 'ja' ? locale : 'en']; }
export function curatedNote(slug: CuratedSlug, locale: string) {
  const copy = curatedCopy(locale);
  return slug === 'savings-accounts' ? copy.savingsNote : slug === '1-year-gic' ? copy.gicNote : copy.feeNote;
}
export function curatedGroupTitle(key: string, locale: string) {
  const copy = curatedCopy(locale);
  return key.split('|').map(part => copy[part as 'annual' | 'apy' | 'zero' | 'waiver' | 'qualified' | 'redeemable' | 'non_redeemable']).join(' · ');
}
