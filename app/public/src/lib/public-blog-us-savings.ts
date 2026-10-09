import type { BlogContent } from './public-blog-content.ts';
import type { PublicLocale } from './public-locale.ts';

export const US_SAVINGS_SOURCES = [
  { id: 'ally-us', title: 'Ally Bank — Savings Account', href: 'https://www.ally.com/bank/online-savings-account/' },
  { id: 'capital-one-us', title: 'Capital One — 360 Performance Savings', href: 'https://www.capitalone.com/bank/savings-accounts/online-performance-savings-account/' },
  { id: 'amex-us', title: 'American Express — High Yield Savings Account', href: 'https://www.americanexpress.com/en-us/banking/online-savings/high-yield-savings-account/' },
  { id: 'cfpb-apy', title: 'CFPB — Annual Percentage Yield Calculation', href: 'https://www.consumerfinance.gov/rules-policy/regulations/1030/a/' }
] as const;

export const US_SAVINGS_CONTENT: Record<PublicLocale, BlogContent> = {
  en: {
    title: 'Ally vs Capital One vs Amex: high-yield savings compared',
    description: 'Compare US high-yield savings accounts from Ally, Capital One and American Express: monthly fees, variable APY, withdrawal access and a USD 10,000 example.',
    intro: 'Three US savings accounts. No monthly maintenance fee. Different ways to use your money. Here is what to compare before moving your savings.',
    takeaway: 'Compare today’s eligible APY, then check fees and your route back to checking. A higher yield helps only when you can access the money when you need it.',
    tableHeaders: ['Account', 'Monthly fee', 'Access and conditions'],
    rows: [
      { bank: 'Ally', code: 'AB', name: 'Savings Account', fee: 'USD 0', detail: 'No minimum balance. Savings buckets organize goals; certain withdrawals and transfers have a combined limit of 10 per statement cycle. No excess-transaction fee, but repeated excess use can lead to account closure.', source: 'ally-us' },
      { bank: 'Capital One', code: 'CONA', name: '360 Performance Savings', fee: 'USD 0', detail: 'No minimum balance. No direct ATM withdrawal: transfer to checking first if you need ATM access.', source: 'capital-one-us' },
      { bank: 'American Express', code: 'AE', name: 'High Yield Savings Account', fee: 'USD 0', detail: 'No minimum balance. No ATM card, debit card or checks are provided; plan your transfer to a spending account.', source: 'amex-us' }
    ],
    infographic: { title: 'Compare in this order', steps: [
      { title: 'APY', text: 'Same day. Same eligibility.' },
      { title: 'Fees', text: 'Monthly and service charges.' },
      { title: 'Access', text: 'Transfer time and limits.' }
    ] },
    sections: [
      { id: 'compare-apy', title: '1. Compare APY, not a headline interest rate', paragraphs: ['Annual percentage yield (APY) includes compounding. These three accounts have variable rates, so today’s APY is not a one-year guarantee. Check each official page on the same day and separate standard APY from any targeted offer.'], sources: ['ally-us', 'capital-one-us', 'amex-us', 'cfpb-apy'] },
      { id: 'check-access', title: '2. Check how the money gets back to you', paragraphs: ['Ally’s buckets help separate savings goals. Capital One requires a transfer to checking for ATM access. Amex HYSA does not provide spending cards or checks. Before a large payment, confirm transfer limits, processing time and deposit holds. USD 0 monthly maintenance does not mean every optional service is free.'], sources: ['ally-us', 'capital-one-us', 'amex-us'] },
      { id: 'worked-example', title: '3. What is one percentage point worth?', paragraphs: ['A fictional USD 10,000 deposit, left for one year at an unchanged APY, makes the difference easy to see. These are illustrative yields, not offers from the three banks.'], sources: ['cfpb-apy'] },
      { id: 'compare-on-switchabank', title: '4. Compare the account, then confirm with the bank', paragraphs: ['Open the US savings catalog and add available accounts to your comparison list. Check each product’s verification date, then confirm current APY and access terms on the bank’s site. An account discussed here may not be listed.'] }
    ],
    example: { title: 'Same deposit. One year. USD 100 difference.', intro: 'APY already includes compounding; do not add compound interest again.', headers: ['Assumed APY', 'One-year calculation', 'Interest'],
      rows: [['3% APY', 'USD 10,000 × 3%', 'USD 300'], ['4% APY', 'USD 10,000 × 4%', 'USD 400']],
      chart: { values: [300, 400], difference: '+USD 100 over one year' },
      note: 'Hypothetical, not current bank rates. Assumes unchanged APY for one year, interest kept in the account, no deposits or withdrawals, and no fees or tax. Actual earnings change if these assumptions change.' },
    checklist: ['Confirm the exact account name and current eligible APY.', 'Read service fees, transfer limits and availability rules.', 'Test the transfer route before relying on it for a payment.'],
    faq: [
      { question: 'Which account has the highest APY?', answer: 'Check the three official pages on the same day. Rates and targeted offers change; this article does not name a current rate winner.' },
      { question: 'Does no monthly fee mean no charges at all?', answer: 'No. Monthly maintenance and optional service charges are different. Read the fee schedule for services you use.' },
      { question: 'Can I use these accounts like checking?', answer: 'Confirm the withdrawal route first. Capital One savings has no direct ATM withdrawal, and Amex HYSA provides no ATM card, debit card or checks.' }
    ]
  },
  ko: {
    title: 'Ally·Capital One·Amex 미국 고금리 저축계좌 비교',
    description: 'Ally, Capital One, American Express의 미국 고금리 저축계좌를 비교합니다. 월 수수료, 변동 APY, 출금 방식과 USD 10,000 가상 예시를 확인하세요.',
    intro: '미국 저축계좌 세 가지. 월 유지 수수료는 모두 0달러지만 돈을 꺼내 쓰는 방식은 다릅니다. 저축을 옮기기 전 확인할 핵심만 정리했습니다.',
    takeaway: '현재 적용 가능한 APY를 비교한 뒤 수수료와 생활비 계좌로 돌아오는 경로를 확인하세요. 수익률만큼 필요한 날 돈을 쓸 수 있는지도 중요합니다.',
    tableHeaders: ['계좌', '월 수수료', '출금 방식과 조건'],
    rows: [
      { bank: 'Ally', code: 'AB', name: 'Savings Account', fee: 'USD 0', detail: '최소 잔액 조건 없음. 저축 버킷으로 목표를 나눌 수 있으며, 특정 출금·이체는 명세 주기당 합산 10회로 제한됩니다. 초과 수수료는 없지만 반복 초과 시 계좌가 해지될 수 있습니다.', source: 'ally-us' },
      { bank: 'Capital One', code: 'CONA', name: '360 Performance Savings', fee: 'USD 0', detail: '최소 잔액 조건 없음. ATM에서 직접 출금할 수 없으므로 ATM 이용 시 체킹계좌로 먼저 이체해야 합니다.', source: 'capital-one-us' },
      { bank: 'American Express', code: 'AE', name: 'High Yield Savings Account', fee: 'USD 0', detail: '최소 잔액 조건 없음. ATM 카드·직불카드·수표를 제공하지 않으므로 생활비 계좌로 이체할 경로를 확인하세요.', source: 'amex-us' }
    ],
    infographic: { title: '이 순서로 비교하세요', steps: [
      { title: 'APY', text: '같은 날짜, 같은 적용 자격' },
      { title: '수수료', text: '월 유지비와 서비스 비용' },
      { title: '자금 접근', text: '이체 시간과 횟수·금액 제한' }
    ] },
    sections: [
      { id: 'compare-apy', title: '1. 표면금리 대신 APY를 비교하세요', paragraphs: ['연 수익률(APY)은 복리를 반영합니다. 세 계좌 모두 변동금리이므로 오늘의 APY가 1년간 보장되지는 않습니다. 같은 날 공식 페이지를 확인하고 기본 APY와 특정 고객 대상 혜택을 구분하세요.'], sources: ['ally-us', 'capital-one-us', 'amex-us', 'cfpb-apy'] },
      { id: 'check-access', title: '2. 돈을 꺼내 쓰는 경로를 확인하세요', paragraphs: ['Ally 버킷은 저축 목표를 나누는 기능입니다. Capital One 저축계좌는 ATM 이용 전 체킹계좌로 이체해야 하며 Amex HYSA는 결제 카드나 수표를 제공하지 않습니다. 큰돈을 쓰기 전 이체 한도·처리 시간·입금 보류를 확인하세요. 월 유지 수수료 0달러가 모든 부가 서비스의 무료 이용을 뜻하지는 않습니다.'], sources: ['ally-us', 'capital-one-us', 'amex-us'] },
      { id: 'worked-example', title: '3. 1%포인트 차이는 얼마일까요?', paragraphs: ['가상의 USD 10,000을 APY가 변하지 않는 조건으로 1년간 유지한다고 가정합니다. 아래 수익률은 비교용 예시이며 세 은행의 실제 제안이 아닙니다.'], sources: ['cfpb-apy'] },
      { id: 'compare-on-switchabank', title: '4. 계좌를 비교한 뒤 은행에서 확인하세요', paragraphs: ['미국 저축상품 목록에서 공개된 계좌를 비교 목록에 담으세요. 상품별 확인일을 읽고 은행 사이트에서 최신 APY와 출금 조건을 확인하세요. 이 글에 나온 계좌가 모두 목록에 있는 것은 아닙니다.'] }
    ],
    example: { title: '같은 원금, 1년, USD 100 차이', intro: 'APY에 복리가 포함되어 있으므로 복리 이자를 다시 더하지 않습니다.', headers: ['가정한 APY', '1년 계산식', '이자'],
      rows: [['APY 3%', 'USD 10,000 × 3%', 'USD 300'], ['APY 4%', 'USD 10,000 × 4%', 'USD 400']],
      chart: { values: [300, 400], difference: '1년 이자 +USD 100' },
      note: '현재 은행 금리가 아닌 가상 예시입니다. 1년간 APY가 일정하고 이자를 계좌에 유지하며 추가 입금·출금·수수료·세금이 없다고 가정합니다. 조건이 달라지면 실제 이자도 달라집니다.' },
    checklist: ['정확한 계좌명과 현재 적용 가능한 APY를 확인합니다.', '서비스 수수료·이체 한도·자금 이용 가능 시점을 확인합니다.', '실제 결제에 쓰기 전 이체 경로를 시험합니다.'],
    faq: [
      { question: '어느 계좌의 APY가 가장 높은가요?', answer: '같은 날 세 은행의 공식 페이지를 확인하세요. 금리와 고객별 혜택은 바뀌므로 이 글은 현재 금리 1위 계좌를 선정하지 않습니다.' },
      { question: '월 수수료가 없으면 모든 비용이 0인가요?', answer: '아닙니다. 월 유지 수수료와 부가 서비스 비용은 다릅니다. 이용할 서비스의 수수료표를 확인하세요.' },
      { question: '체킹계좌처럼 사용할 수 있나요?', answer: '출금 경로부터 확인하세요. Capital One 저축계좌는 ATM에서 직접 출금할 수 없고 Amex HYSA는 ATM 카드·직불카드·수표를 제공하지 않습니다.' }
    ]
  },
  ja: {
    title: 'Ally・Capital One・Amexの米国高金利貯蓄口座比較',
    description: '米国のAlly、Capital One、American Expressの高金利貯蓄口座を比較。月額手数料、変動APY、出金方法とUSD 10,000の仮定例を確認できます。',
    intro: '米国の貯蓄口座3つ。月額維持手数料はいずれもゼロですが、お金の引き出し方は異なります。資金を移す前の要点をまとめました。',
    takeaway: '現在適用されるAPYを比べてから、手数料と決済口座への移動方法を確認しましょう。必要な日に資金を使えるかも大切です。',
    tableHeaders: ['口座', '月額手数料', '出金方法と条件'],
    rows: [
      { bank: 'Ally', code: 'AB', name: 'Savings Account', fee: 'USD 0', detail: '最低残高条件なし。貯蓄バケットで目的別に整理でき、特定の出金・振替は明細期間ごとに合計10回までです。超過手数料はありませんが、繰り返すと口座閉鎖の対象になります。', source: 'ally-us' },
      { bank: 'Capital One', code: 'CONA', name: '360 Performance Savings', fee: 'USD 0', detail: '最低残高条件なし。ATMから直接出金できません。ATMを使うには先にチェッキング口座へ振り替えます。', source: 'capital-one-us' },
      { bank: 'American Express', code: 'AE', name: 'High Yield Savings Account', fee: 'USD 0', detail: '最低残高条件なし。ATMカード・デビットカード・小切手は提供されないため、決済口座への振替方法を確認します。', source: 'amex-us' }
    ],
    infographic: { title: 'この順番で比較', steps: [
      { title: 'APY', text: '同じ日・同じ対象条件' },
      { title: '手数料', text: '月額維持費とサービス料金' },
      { title: '資金アクセス', text: '振替時間と限度額・回数' }
    ] },
    sections: [
      { id: 'compare-apy', title: '1. 表面金利ではなくAPYを比較', paragraphs: ['年利回り（APY）は複利を含みます。3口座とも変動金利なので、今日のAPYが1年間保証されるわけではありません。同じ日に公式ページを確認し、通常APYと特定顧客向けの特典を分けて比較しましょう。'], sources: ['ally-us', 'capital-one-us', 'amex-us', 'cfpb-apy'] },
      { id: 'check-access', title: '2. 資金を使うまでの経路を確認', paragraphs: ['Allyのバケットは貯蓄目的を整理する機能です。Capital OneはATM利用前にチェッキング口座への振替が必要で、Amex HYSAは決済カードや小切手を提供しません。大きな支払いの前に振替限度額・処理時間・入金保留を確認してください。月額維持費ゼロはすべての追加サービスが無料という意味ではありません。'], sources: ['ally-us', 'capital-one-us', 'amex-us'] },
      { id: 'worked-example', title: '3. 1ポイントの差はいくら？', paragraphs: ['仮のUSD 10,000を、APYが変わらない条件で1年間預けた場合です。以下は比較用の仮定で、3銀行の実際の提示利回りではありません。'], sources: ['cfpb-apy'] },
      { id: 'compare-on-switchabank', title: '4. 口座を比較して銀行で最終確認', paragraphs: ['米国の貯蓄商品一覧で公開中の口座を比較リストに追加します。各商品の確認日を読み、銀行サイトで最新APYと出金条件を確認してください。この記事の口座がすべて一覧にあるとは限りません。'] }
    ],
    example: { title: '同じ元本、1年間でUSD 100の差', intro: 'APYは複利込みなので、複利分をもう一度足しません。', headers: ['仮定のAPY', '1年間の計算', '利息'],
      rows: [['APY 3%', 'USD 10,000 × 3%', 'USD 300'], ['APY 4%', 'USD 10,000 × 4%', 'USD 400']],
      chart: { values: [300, 400], difference: '1年間の利息 +USD 100' },
      note: '現在の銀行金利ではない仮定例です。1年間APYが一定で、利息を口座に残し、追加入金・出金・手数料・税金がないと仮定します。条件が変われば実際の利息も変わります。' },
    checklist: ['正確な口座名と現在適用されるAPYを確認する。', 'サービス料金・振替限度額・資金利用可能日を読む。', '支払いに使う前に振替経路を試す。'],
    faq: [
      { question: 'どの口座のAPYが一番高いですか？', answer: '同じ日に3銀行の公式ページを確認してください。金利や対象者限定の特典は変わるため、この記事では現在の1位を選んでいません。' },
      { question: '月額手数料ゼロなら費用は一切ありませんか？', answer: '月額維持費と追加サービスの料金は別です。利用するサービスの手数料表を確認してください。' },
      { question: 'チェッキング口座のように使えますか？', answer: 'まず出金方法を確認してください。Capital Oneの貯蓄口座はATMから直接出金できず、Amex HYSAはATMカード・デビットカード・小切手を提供しません。' }
    ]
  }
};
export const US_SAVINGS_PRESENTATION = {
  en: { scope: 'United States · High-yield savings', comparison: 'Three accounts at a glance', compare: 'Compare US savings accounts', compareBody: 'Use SwitchaBank’s published US savings details to build your shortlist.', action: 'Explore US savings', about: 'US high-yield savings account comparisons' },
  ko: { scope: '미국 · 고금리 저축계좌', comparison: '세 계좌 한눈에 비교', compare: '미국 저축계좌 비교하기', compareBody: 'SwitchaBank에 공개된 미국 저축상품 조건으로 후보를 좁혀 보세요.', action: '미국 저축상품 보기', about: '미국 고금리 저축계좌 비교' },
  ja: { scope: '米国 · 高金利貯蓄口座', comparison: '3口座をひと目で比較', compare: '米国の貯蓄口座を比較', compareBody: 'SwitchaBankで公開中の米国貯蓄商品の条件から候補を絞れます。', action: '米国の貯蓄商品を見る', about: '米国高金利貯蓄口座の比較' }
} satisfies Record<PublicLocale, object>;
