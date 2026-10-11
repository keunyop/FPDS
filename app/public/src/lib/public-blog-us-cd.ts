import type { BlogContent } from './public-blog-content.ts';
import type { PublicLocale } from './public-locale.ts';

export const US_CD_SOURCES = [
  { id: 'capital-one-us-cd-guide', title: 'Capital One — 360 Performance Savings', href: 'https://www.capitalone.com/bank/savings-accounts/online-performance-savings-account/' },
  { id: 'marcus-cd-guide', title: 'Marcus by Goldman Sachs — How Our CDs Work', href: 'https://www.marcus.com/us/en/savings/cd-info-guide' },
  { id: 'ally-no-penalty', title: 'Ally Bank — No Penalty CD', href: 'https://www.ally.com/bank/no-penalty-cd/' },
  { id: 'cfpb-cd', title: 'CFPB — What is a certificate of deposit (CD)?', href: 'https://www.consumerfinance.gov/ask-cfpb/what-is-a-certificate-of-deposit-cd-en-917/' }
] as const;

export const US_CD_CONTENT: Record<PublicLocale, BlogContent> = {
  en: {
    title: 'High-yield savings vs CDs: rates, access and penalties',
    description: 'Compare US high-yield savings, standard CDs and no-penalty CDs. See fixed vs variable rates, withdrawal rules and a USD 10,000 early-exit cost example.',
    intro: 'A high APY is only part of the comparison. Before choosing a US savings account or certificate of deposit (CD), check when you can take your money out—and what leaving early costs.',
    takeaway: 'Start with your spending date. Compare access and term first, then the eligible APY. A no-penalty CD still has withdrawal conditions.',
    tableHeaders: ['Account', 'Rate type', 'Access and conditions'],
    rows: [
      { bank: 'Capital One', code: 'CONA', name: '360 Performance Savings', fee: 'Variable APY', detail: 'No monthly fee or minimum balance. Withdraw online or at a branch; ATM access requires a transfer to checking first.', source: 'capital-one-us-cd-guide' },
      { bank: 'Marcus', code: 'GSBU', name: 'High-Yield CD', fee: 'Fixed rate', detail: 'USD 500 minimum balance; terms from 6 months to 6 years. Withdrawing the balance before maturity incurs an early withdrawal penalty.', source: 'marcus-cd-guide' },
      { bank: 'Ally', code: 'AB', name: 'No Penalty CD', fee: 'Fixed APY', detail: '11-month term, no minimum opening deposit or monthly maintenance fee. Withdraw the full balance and interest without penalty after the first 6 days following funding.', source: 'ally-no-penalty' }
    ],
    infographic: { title: 'Three ways to hold cash', steps: [
      { title: 'Savings', text: 'Variable APY. Check the transfer route.' },
      { title: 'Standard CD', text: 'Fixed term. Price the early exit.' },
      { title: 'No-penalty CD', text: 'Check the waiting period and full-balance rule.' }
    ] },
    sections: [
      { id: 'rates-and-access', title: '1. Match the term to when you need the money', paragraphs: ['Savings can accommodate changing plans, but transfer timing still matters. Capital One’s APY can change after opening. The Marcus High-Yield CD fixes its rate once its minimum funding requirement is met; Ally’s No Penalty CD fixes APY for its term. APY includes compounding—compare current offers on the same day.'], sources: ['capital-one-us-cd-guide', 'marcus-cd-guide', 'ally-no-penalty', 'cfpb-cd'] },
      { id: 'no-penalty-conditions', title: '2. Read the no-penalty withdrawal conditions', paragraphs: ['For Ally’s 11-month No Penalty CD, penalty-free withdrawal means the full balance plus interest, after the first six days following funding. That differs from transferring a chosen amount out of savings. Confirm the funding date and transfer timing before relying on the money for a payment.'], sources: ['ally-no-penalty'] },
      { id: 'worked-example', title: '3. Calculate the cost of leaving a CD early', paragraphs: ['Marcus bases its High-Yield CD penalty on the original principal: 90 days of interest for terms up to and including one year, 180 days for terms over one through five years, and 270 days for terms over five years. The example below shows how crossing the one-year term boundary changes the cost.'], sources: ['marcus-cd-guide'] }
    ],
    example: { title: 'Same deposit and rate. Different exit cost.', intro: 'Assume full withdrawal before maturity, USD 10,000 original principal and a hypothetical 4.00% annual interest rate. These bars show penalties, not earnings.', headers: ['Original CD term', 'Penalty calculation', 'Early withdrawal penalty'],
      rows: [['12-month CD · 90 days', 'USD 10,000 × 0.04 ÷ 365 × 90', 'USD 98.63'], ['18-month CD · 180 days', 'USD 10,000 × 0.04 ÷ 365 × 180', 'USD 197.26']],
      chart: { values: [98.63, 197.26], difference: '18-month early-exit penalty: +USD 98.63' },
      note: 'Illustrative 4.00% interest rate, not APY or a current Marcus quote. Assumes a 365-day year and rounds to cents; Marcus uses 366 days in a leap year. This compares penalties only, before any tax effects.' },
    checklist: ['Record the exact account, eligible APY and funding date.', 'Check transfer timing, early withdrawal rules and the minimum deposit.', 'For a CD, check maturity instructions and any automatic renewal.'],
    faq: [
      { question: 'Is a CD always better than high-yield savings?', answer: 'Compare the current APY, term and access rules. A fixed CD rate can suit a known time horizon, but an early withdrawal penalty changes the outcome.' },
      { question: 'Can I withdraw an Ally No Penalty CD immediately?', answer: 'Penalty-free full-balance withdrawal is available after the first six days following funding. It is not immediate access on the funding date.' },
      { question: 'Does a 12-month Marcus CD use a 180-day penalty?', answer: 'No. Its disclosed boundary includes one year in the 90-day band. The 180-day band applies to terms over one year through five years.' }
    ]
  },
  ko: {
    title: '미국 고금리 저축계좌 vs CD: 금리·출금·중도해지 비교',
    description: '미국 고금리 저축계좌, 일반 CD, 무위약금 CD의 차이를 비교합니다. 고정·변동금리, 출금 조건과 USD 10,000 중도해지 비용을 인포그래픽으로 확인하세요.',
    intro: '높은 APY만으로는 비교가 끝나지 않습니다. 미국 저축계좌나 정기예금 CD를 고르기 전에 돈을 언제 꺼낼 수 있는지, 일찍 해지하면 얼마가 드는지 확인하세요.',
    takeaway: '돈을 쓸 날짜부터 정하세요. 출금 조건과 만기를 맞춘 뒤 적용 가능한 APY를 비교합니다. 무위약금 CD에도 출금 조건은 있습니다.',
    tableHeaders: ['계좌', '금리 유형', '출금 방식과 조건'],
    rows: [
      { bank: 'Capital One', code: 'CONA', name: '360 Performance Savings', fee: '변동 APY', detail: '월 수수료·최소 잔액 조건 없음. 온라인 또는 지점에서 출금하며, ATM을 쓰려면 먼저 체킹계좌로 이체해야 합니다.', source: 'capital-one-us-cd-guide' },
      { bank: 'Marcus', code: 'GSBU', name: 'High-Yield CD', fee: '고정금리', detail: '최소 잔액 USD 500. 기간은 6개월~6년이며, 만기 전에 잔액을 인출하면 중도해지 위약금이 발생합니다.', source: 'marcus-cd-guide' },
      { bank: 'Ally', code: 'AB', name: 'No Penalty CD', fee: '고정 APY', detail: '11개월 만기. 최소 개설 입금액·월 유지 수수료 없음. 입금일 이후 첫 6일이 지난 뒤 원금 전액과 이자를 위약금 없이 인출할 수 있습니다.', source: 'ally-no-penalty' }
    ],
    infographic: { title: '현금을 보관하는 세 가지 방식', steps: [
      { title: '저축계좌', text: '변동 APY. 이체 경로를 확인합니다.' },
      { title: '일반 CD', text: '정해진 기간. 중도해지 비용을 계산합니다.' },
      { title: '무위약금 CD', text: '대기 기간과 전액 인출 조건을 확인합니다.' }
    ] },
    sections: [
      { id: 'rates-and-access', title: '1. 돈을 쓸 시점과 만기를 맞추세요', paragraphs: ['저축계좌는 계획이 바뀔 때 활용할 수 있지만 이체 시간은 확인해야 합니다. Capital One의 APY는 개설 후에도 바뀔 수 있습니다. Marcus High-Yield CD는 최소 입금 요건을 충족하면 금리가 고정되고, Ally No Penalty CD는 만기까지 APY가 고정됩니다. APY에는 복리가 반영되므로 현재 제안을 같은 날 비교하세요.'], sources: ['capital-one-us-cd-guide', 'marcus-cd-guide', 'ally-no-penalty', 'cfpb-cd'] },
      { id: 'no-penalty-conditions', title: '2. 무위약금의 출금 조건을 읽으세요', paragraphs: ['Ally의 11개월 No Penalty CD는 입금일 이후 첫 6일이 지난 뒤 잔액 전액과 이자를 위약금 없이 인출하는 조건입니다. 저축계좌에서 필요한 금액만 이체하는 방식과는 다릅니다. 결제에 쓸 돈이라면 입금일과 이체 소요 시간을 먼저 확인하세요.'], sources: ['ally-no-penalty'] },
      { id: 'worked-example', title: '3. 중도해지 비용을 계산하세요', paragraphs: ['Marcus High-Yield CD는 최초 원금을 기준으로 위약금을 계산합니다. 기간이 1년 이하면 90일분, 1년 초과~5년 이하면 180일분, 5년 초과면 270일분 이자입니다. 아래 예시는 계약 기간이 1년을 넘을 때 해지 비용이 어떻게 달라지는지 보여줍니다.'], sources: ['marcus-cd-guide'] }
    ],
    example: { title: '같은 원금과 금리, 다른 해지 비용', intro: '만기 전 전액 인출, 최초 원금 USD 10,000, 가상의 연 이자율 4.00%를 가정합니다. 막대는 수익이 아닌 위약금입니다.', headers: ['최초 CD 기간', '위약금 계산', '중도해지 위약금'],
      rows: [['12개월 CD · 90일분', 'USD 10,000 × 0.04 ÷ 365 × 90', 'USD 98.63'], ['18개월 CD · 180일분', 'USD 10,000 × 0.04 ÷ 365 × 180', 'USD 197.26']],
      chart: { values: [98.63, 197.26], difference: '18개월 CD 중도해지 위약금 +USD 98.63' },
      note: '4.00%는 가상의 연 이자율로, APY나 Marcus의 현재 제안이 아닙니다. 1년 365일을 가정해 센트 단위로 반올림했으며 Marcus는 윤년에 366일을 사용합니다. 세금 효과를 제외한 위약금만 비교합니다.' },
    checklist: ['정확한 계좌명, 적용 가능한 APY, 입금일을 기록합니다.', '이체 시간, 중도 인출 규정, 최소 입금액을 확인합니다.', 'CD는 만기 처리 지시와 자동 갱신 여부를 확인합니다.'],
    faq: [
      { question: 'CD가 고금리 저축계좌보다 항상 유리한가요?', answer: '현재 APY, 기간, 출금 조건을 함께 비교하세요. 사용 시점이 정해졌다면 고정 CD 금리를 검토할 수 있지만 중도해지 위약금이 결과를 바꿉니다.' },
      { question: 'Ally No Penalty CD는 바로 출금할 수 있나요?', answer: '입금일 이후 첫 6일이 지난 뒤 전액을 위약금 없이 인출할 수 있습니다. 입금 당일 바로 꺼내 쓸 수 있다는 의미는 아닙니다.' },
      { question: 'Marcus 12개월 CD의 위약금은 180일분인가요?', answer: '아닙니다. 1년까지는 90일분 구간에 포함됩니다. 180일분은 1년 초과~5년 이하 기간에 적용됩니다.' }
    ]
  },
  ja: {
    title: '米国の高金利貯蓄口座とCD：金利・出金・中途解約を比較',
    description: '米国の高金利貯蓄口座、通常のCD、違約金なしCDを比較。固定・変動金利、出金条件、USD 10,000の中途解約費用を図で確認できます。',
    intro: '高いAPYだけでは比較できません。米国の貯蓄口座や定期預金CDを選ぶ前に、いつ資金を引き出せるか、早く解約するといくらかかるかを確認しましょう。',
    takeaway: 'まずお金を使う日を決めます。出金条件と期間をそろえてから、適用されるAPYを比較しましょう。違約金なしCDにも出金条件があります。',
    tableHeaders: ['口座', '金利の種類', '出金方法と条件'],
    rows: [
      { bank: 'Capital One', code: 'CONA', name: '360 Performance Savings', fee: '変動APY', detail: '月額手数料・最低残高条件なし。オンラインまたは支店で出金できます。ATMを使うには先に当座口座へ振替が必要です。', source: 'capital-one-us-cd-guide' },
      { bank: 'Marcus', code: 'GSBU', name: 'High-Yield CD', fee: '固定金利', detail: '最低残高USD 500。期間は6か月〜6年。満期前に残高を引き出すと中途解約違約金が発生します。', source: 'marcus-cd-guide' },
      { bank: 'Ally', code: 'AB', name: 'No Penalty CD', fee: '固定APY', detail: '11か月満期。最低開設預入額・月額維持手数料なし。入金日の翌日から数えて最初の6日間が経過した後、残高全額と利息を違約金なしで引き出せます。', source: 'ally-no-penalty' }
    ],
    infographic: { title: '現金を預ける三つの方法', steps: [
      { title: '貯蓄口座', text: '変動APY。振替経路を確認。' },
      { title: '通常のCD', text: '期間が決まる。早期解約費用を計算。' },
      { title: '違約金なしCD', text: '待機期間と全額出金の条件を確認。' }
    ] },
    sections: [
      { id: 'rates-and-access', title: '1. お金を使う時期と満期をそろえる', paragraphs: ['貯蓄口座は予定の変更に対応しやすい一方、振替時間の確認は必要です。Capital OneのAPYは開設後も変わり得ます。Marcus High-Yield CDは最低入金条件を満たすと金利が固定され、Ally No Penalty CDは満期までAPYが固定されます。APYは複利を反映するため、現在の条件を同じ日に比較しましょう。'], sources: ['capital-one-us-cd-guide', 'marcus-cd-guide', 'ally-no-penalty', 'cfpb-cd'] },
      { id: 'no-penalty-conditions', title: '2. 違約金なしでも出金条件を読む', paragraphs: ['Allyの11か月No Penalty CDは、入金日後の最初の6日間が経過してから、残高全額と利息を違約金なしで引き出す条件です。貯蓄口座から必要額だけを振り替える方法とは異なります。支払いに使う前に入金日と振替所要時間を確認しましょう。'], sources: ['ally-no-penalty'] },
      { id: 'worked-example', title: '3. 中途解約費用を計算する', paragraphs: ['Marcus High-Yield CDの違約金は当初元本が基準です。契約期間が1年以下なら90日分、1年超〜5年以下なら180日分、5年超なら270日分の利息となります。以下は契約期間が1年を超えた場合の費用差です。'], sources: ['marcus-cd-guide'] }
    ],
    example: { title: '同じ元本と金利でも、解約費用は変わる', intro: '満期前の全額出金、当初元本USD 10,000、仮の年利率4.00%を想定します。棒グラフは収益ではなく違約金です。', headers: ['当初のCD期間', '違約金の計算', '中途解約違約金'],
      rows: [['12か月CD · 90日分', 'USD 10,000 × 0.04 ÷ 365 × 90', 'USD 98.63'], ['18か月CD · 180日分', 'USD 10,000 × 0.04 ÷ 365 × 180', 'USD 197.26']],
      chart: { values: [98.63, 197.26], difference: '18か月CDの中途解約違約金 +USD 98.63' },
      note: '4.00%は仮の年利率で、APYやMarcusの現在の提示金利ではありません。1年365日としてセント単位に丸めています。Marcusはうるう年に366日を使用します。税金の影響を除き、違約金のみを比較しています。' },
    checklist: ['正確な口座名、適用APY、入金日を記録する。', '振替時間、早期出金条件、最低預入額を確認する。', 'CDの満期時の指示と自動更新を確認する。'],
    faq: [
      { question: 'CDは高金利貯蓄口座より必ず有利ですか？', answer: '現在のAPY、期間、出金条件を比較しましょう。使う時期が決まっていれば固定金利のCDを検討できますが、中途解約違約金で結果が変わります。' },
      { question: 'Ally No Penalty CDはすぐ出金できますか？', answer: '入金日後の最初の6日間が経過してから、全額を違約金なしで引き出せます。入金当日から使えるという意味ではありません。' },
      { question: 'Marcusの12か月CDは180日分の違約金ですか？', answer: 'いいえ。1年以下は90日分の区分です。180日分は1年超〜5年以下の期間に適用されます。' }
    ]
  }
};

export const US_CD_PRESENTATION = {
  en: { scope: 'United States · Savings & CDs', comparison: 'Savings, a standard CD and a no-penalty CD', compare: 'Compare US CDs', compareBody: 'Browse published US CDs and compare their terms. Check verification dates and confirm current rates and withdrawal rules with the bank. The examples above may not all appear in the catalog.', action: 'Explore US CDs', about: 'US high-yield savings and certificate of deposit comparisons' },
  ko: { scope: '미국 · 저축계좌와 CD', comparison: '저축계좌·일반 CD·무위약금 CD 비교', compare: '미국 CD를 비교하세요', compareBody: '공개된 미국 CD의 조건을 비교하세요. 확인일을 살펴보고 최신 금리와 출금 규정은 은행에서 확인하세요. 위 예시 상품이 모두 목록에 있는 것은 아닙니다.', action: '미국 CD 살펴보기', about: '미국 고금리 저축계좌와 정기예금 CD 비교' },
  ja: { scope: '米国 · 貯蓄口座とCD', comparison: '貯蓄口座・通常のCD・違約金なしCDを比較', compare: '米国のCDを比較する', compareBody: '公開中の米国CDの条件を比較できます。確認日を読み、最新金利と出金条件は銀行で確認してください。上記の商品がすべて掲載されているとは限りません。', action: '米国のCDを見る', about: '米国の高金利貯蓄口座と定期預金CDの比較' }
} satisfies Record<PublicLocale, object>;
