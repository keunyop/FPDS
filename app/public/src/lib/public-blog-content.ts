import { US_SAVINGS_CONTENT, US_SAVINGS_PRESENTATION, US_SAVINGS_SOURCES } from './public-blog-us-savings.ts';
import { GIC_CONTENT, GIC_PRESENTATION, GIC_SOURCES } from './public-blog-gic.ts';
import type { PublicLocale } from './public-locale.ts';
import type { BlogSlug } from './public-blog.ts';
import { blogCopy } from './public-blog.ts';
import { CHEQUING_CONTENT, CHEQUING_PRESENTATION, CHEQUING_SOURCES } from './public-blog-chequing.ts';
import type { CuratedSlug } from './public-curated.ts';
import type { GuideSlug } from './public-guides.ts';

export const BLOG_SOURCES = [
  { id: 'eq', title: 'EQ Bank — Personal Account', href: 'https://www.eqbank.ca/personal-banking/personal-account' },
  { id: 'tangerine', title: 'Tangerine — Savings Account', href: 'https://www.tangerine.ca/en/personal/save/savings-account' },
  { id: 'td', title: 'TD — Every Day Savings Account', href: 'https://www.td.com/ca/en/personal-banking/products/bank-accounts/savings-accounts/every-day-savings-account' },
  { id: 'fcac', title: 'FCAC — Savings accounts', href: 'https://www.canada.ca/en/financial-consumer-agency/services/banking/bank-accounts/savings-account.html' }
] as const;
export type BlogSource = { id: string; title: string; href: string };
type SourceId = typeof BLOG_SOURCES[number]['id'] | typeof CHEQUING_SOURCES[number]['id'] | typeof GIC_SOURCES[number]['id'] | typeof US_SAVINGS_SOURCES[number]['id'];
export type BlogSection = { id: string; title: string; paragraphs: string[]; sources?: SourceId[] };
export type BlogContent = {
  infographic?: { title: string; steps: { title: string; text: string }[] };
  tableHeaders?: [string, string, string];
  title: string; description: string; intro: string; takeaway: string;
  rows: { bank: string; code: string; name: string; fee: string; detail: string; source: SourceId }[];
  sections: BlogSection[];
  example: { chart?: { values: number[]; difference: string }; title: string; intro: string; rows: [string, string, string][]; headers: [string, string, string]; note: string };
  checklist: string[];
  faq: { question: string; answer: string }[];
};
const content: Record<PublicLocale, BlogContent> = {
  en: {
    title: 'EQ Bank vs Tangerine vs TD: how to compare savings accounts',
    description: 'Compare EQ Bank, Tangerine and TD savings account conditions: monthly fees, bonus requirements, promotional rates and transaction costs, with a worked example.',
    intro: 'A savings account can look attractive until you ask two questions: what will it earn after the offer ends, and what will it cost to use? EQ Bank, Tangerine and TD illustrate three different details to read before moving your money.',
    takeaway: 'Compare the rate you actually qualify for over the time you plan to save. Then check transaction costs and access to your money. A zero monthly fee answers only one part of the question.',
    rows: [
      { bank: 'EQ Bank', code: 'EQBANK', name: 'Personal Account', fee: 'CAD 0', detail: 'No minimum balance. A higher rate requires qualifying recurring direct deposits; separate the base rate from that conditional rate.', source: 'eq' },
      { bank: 'Tangerine', code: 'TANGERINE', name: 'Savings Account', fee: 'CAD 0', detail: 'No minimum balance. Read any new-client offer alongside the regular rate, eligibility and end date.', source: 'tangerine' },
      { bank: 'TD', code: 'TD', name: 'Every Day Savings Account', fee: 'CAD 0', detail: 'One included transaction per month; additional chargeable transactions cost CAD 3 each. Eligible transfers to your other TD deposit accounts are treated separately.', source: 'td' }
    ],
    sections: [
      { id: 'start-with-purpose', title: '1. Start with when you need the money',
        paragraphs: [
          'Money for next month’s rent has a different job from savings for a purchase next year. Before comparing accounts, write down your expected balance, how long it can stay there, and how often you need to move it. Those three inputs make a rate comparison useful.',
          'This article compares Canadian-dollar, non-registered accounts. EQ’s Personal Account combines everyday transactions with interest; Tangerine Savings and TD Every Day Savings are savings products. The comparison explains their conditions, without treating every account as interchangeable or ranking an entire bank from one product.'
        ] },
      { id: 'read-the-rate', title: '2. Put the base rate and the conditions on separate lines',
        paragraphs: [
          'For EQ’s Personal Account, the higher-rate condition on the checked page requires qualifying recurring direct deposits of at least CAD 2,000 a month. A balance requirement and a direct-deposit requirement are different: leaving money in the account does not by itself establish that you qualify.',
          'For Tangerine, distinguish the regular Savings rate from a new-client promotion. Write down the eligible deposits, offer length and rate afterward before comparing it with another account. A headline offer cannot tell you what a full year will earn.',
          'This article does not reproduce a changing interest-rate table. Use the official pages for current percentages and offer terms. FCAC also advises checking introductory rates, balance thresholds and how interest is calculated.'
        ], sources: ['eq', 'tangerine', 'fcac'] },
      { id: 'count-the-cost', title: '3. Read past the zero monthly fee',
        paragraphs: [
          'TD Every Day Savings shows why account fees need more than one column. Its eligible transfers to your other TD deposit accounts have their own free-transfer rule. Other transactions can consume the included allowance and trigger a charge. Read the transaction definition and exceptions before counting your likely costs.',
          'Make a short list of the actions you actually use: transferring savings to spending, withdrawing cash, sending money, or requesting a paper statement. A useful comparison follows those actions through each bank’s current fee schedule. “No monthly fee” should never become “every service is free.”'
        ], sources: ['td'] },
      { id: 'worked-example', title: '4. Turn a promotional rate into a time-based comparison',
        paragraphs: ['The following invented offers show why the comparison period matters. They are not EQ, Tangerine or TD rates. Assume CAD 10,000 stays deposited for 12 months, rates do not change within each stated period, and interest is simple annual interest.'] },
      { id: 'access-and-switching', title: '5. Check the route back to your money',
        paragraphs: [
          'An account can earn interest and still require several steps before the money reaches the account you spend from. Check transfer limits, processing times and any deposit holds for your intended route. If you need a branch, cash deposits or a particular payment method, verify those services for the exact account.',
          'You can compare a savings account without moving every banking service at once. If you later switch recurring payments or direct deposits, check that they work at the receiving account before closing the old one. A rate comparison is the beginning of that decision, not confirmation that the transfer is complete.'
        ] },
      { id: 'make-a-shortlist', title: '6. Build a shortlist you can explain',
        paragraphs: [
          'Keep the reason for each account in one sentence: the base rate, a condition you can meet, or a service you need. Then write down the tradeoff beside it. That is more useful than declaring one bank “best” without specifying balance, period or usage.',
          'SwitchaBank lets you inspect available published products and select them for comparison. Availability and verification dates can differ from this article’s source-check date. If an account is absent, that does not establish that the bank has stopped offering it; check the linked official page.',
          'For eligible deposit pairs, the comparison calculator can show supported scenarios. It does not model every promotional schedule, transaction fee or tax outcome. Keep those conditions in your own comparison and confirm the final terms with the bank.'
        ] }
    ],
    example: {
      title: 'A higher opening rate can produce less interest over a year',
      intro: 'Both offers below use the same amount and 12-month period.',
      headers: ['Hypothetical offer', 'Simple-interest calculation', '12-month interest'],
      rows: [
        ['A: 5% for 3 months, then 1% for 9 months', '10,000 × 5% × 3/12 + 10,000 × 1% × 9/12', 'CAD 200'],
        ['B: 3% for all 12 months', '10,000 × 3% × 12/12', 'CAD 300']
      ],
      note: 'Offer B produces CAD 100 more under these assumptions. This excludes compounding, exact daily accrual, taxes, fees and balance changes. These are illustrative annual rates, not APYs or current bank offers.'
    },
    checklist: [
      'Record the exact account, currency and current official terms.',
      'Separate the base rate, conditional bonus and temporary promotion.',
      'Use the same balance and saving period for both accounts.',
      'Check chargeable transactions, transfer timing and the services you need.',
      'Confirm eligibility and current terms with the bank before applying.'
    ],
    faq: [
      { question: 'Which of these accounts pays the highest interest?', answer: 'That depends on current rates, your eligibility and the saving period. Compare the base rates first, then add only the conditions or promotions that apply. This article does not declare a current rate winner.' },
      { question: 'Does a zero monthly fee mean the account is free to use?', answer: 'It means there is no recurring monthly account fee. Transaction charges and other service fees may still apply. Check the fee schedule for the actions you expect to take.' },
      { question: 'Can I compare these accounts with a GIC?', answer: 'Start by separating access and maturity conditions. A savings account and a fixed-term GIC can serve different needs. Compare GICs with matching maturity and redemption terms rather than mixing headline rates.' }
    ]
  },
  ko: {
    title: 'EQ Bank·Tangerine·TD 저축계좌 비교: 금리보다 먼저 읽을 조건',
    description: '캐나다 EQ Bank, Tangerine, TD 저축계좌의 월 수수료·우대금리 조건·프로모션·거래 비용을 비교합니다. 가상 이자 계산과 계좌 이전 체크리스트도 확인하세요.',
    intro: '저축계좌 광고에서 가장 먼저 눈에 들어오는 것은 금리입니다. 하지만 돈을 옮기기 전에는 두 가지를 더 물어야 합니다. 혜택이 끝난 뒤에는 얼마를 받는지, 돈을 꺼내 쓸 때는 비용이 드는지입니다. EQ Bank·Tangerine·TD의 세 상품으로 그 차이를 살펴봅니다.',
    takeaway: '실제로 충족할 수 있는 조건과 돈을 맡길 기간을 기준으로 금리를 비교하세요. 거래 비용과 자금 접근성까지 확인해야 합니다. 월 수수료 0달러는 비교의 출발점입니다.',
    rows: [
      { bank: 'EQ Bank', code: 'EQBANK', name: 'Personal Account', fee: 'CAD 0', detail: '최소 잔액 조건이 없습니다. 더 높은 금리에는 적격 정기 직접입금 조건이 있으므로 기본금리와 구분해 읽어야 합니다.', source: 'eq' },
      { bank: 'Tangerine', code: 'TANGERINE', name: 'Savings Account', fee: 'CAD 0', detail: '최소 잔액 조건이 없습니다. 신규 고객 프로모션은 일반 금리, 적용 대상, 종료일을 함께 확인하세요.', source: 'tangerine' },
      { bank: 'TD', code: 'TD', name: 'Every Day Savings Account', fee: 'CAD 0', detail: '월 1회 거래가 포함되며 추가 과금 대상 거래는 건당 CAD 3입니다. 본인의 다른 TD 예금계좌로 보내는 적격 이체는 별도 규정이 적용됩니다.', source: 'td' }
    ],
    sections: [
      { id: 'start-with-purpose', title: '1. 돈이 필요한 날짜부터 정하세요',
        paragraphs: [
          '다음 달 월세로 쓸 돈과 내년의 큰 지출을 위해 모으는 돈은 역할이 다릅니다. 비교를 시작하기 전에 예상 잔액, 맡겨둘 기간, 이체나 인출 빈도를 적어 보세요. 같은 금리도 이 세 가지에 따라 의미가 달라집니다.',
          '이 글은 캐나다 달러 비등록 계좌를 다룹니다. EQ의 Personal Account는 일상 거래와 이자 지급을 결합한 계좌이며, Tangerine Savings와 TD Every Day Savings는 저축상품입니다. 개별 계좌의 조건을 비교하는 글이므로 은행 전체의 우열이나 모든 상품의 대체 가능성을 뜻하지는 않습니다.'
        ] },
      { id: 'read-the-rate', title: '2. 기본금리와 우대조건은 다른 줄에 적으세요',
        paragraphs: [
          '확인한 EQ Personal Account 안내에서 더 높은 금리를 받으려면 월 CAD 2,000 이상의 적격 정기 직접입금을 유지해야 합니다. 잔액 조건과 직접입금 조건은 다릅니다. 계좌에 돈을 넣어두었다는 사실만으로 우대 자격이 생기는 것은 아닙니다.',
          'Tangerine은 일반 Savings 금리와 신규 고객 프로모션을 구분해 읽어야 합니다. 어떤 입금액에 적용되는지, 얼마 동안 적용되는지, 종료 후 금리는 무엇인지 먼저 적어 보세요. 광고 첫 화면의 숫자 하나로 1년 이자를 알 수는 없습니다.',
          '이 글에는 계속 바뀌는 금리표를 옮겨 적지 않았습니다. 현재 금리와 행사 조건은 공식 페이지에서 확인하세요. 캐나다 금융소비자청 FCAC 역시 초기 우대금리, 잔액 구간, 이자 계산 방식을 확인하도록 안내합니다.'
        ], sources: ['eq', 'tangerine', 'fcac'] },
      { id: 'count-the-cost', title: '3. 월 수수료가 없어도 거래 비용은 확인하세요',
        paragraphs: [
          'TD Every Day Savings는 수수료를 한 칸으로 정리하면 놓치는 부분을 보여줍니다. 본인의 다른 TD 예금계좌로 보내는 적격 이체에는 별도의 무료 규정이 있습니다. 그 외 거래는 포함 횟수를 사용하거나 추가 비용을 발생시킬 수 있으므로, 거래의 정의와 예외부터 읽어야 합니다.',
          '저축한 돈을 생활비 계좌로 옮기기, 현금 인출하기, 송금하기, 종이 명세서 받기처럼 실제로 할 행동을 적어 보세요. 그 행동을 각 은행의 수수료표에 대입하는 것이 실용적인 비교입니다. 월 수수료가 없다는 설명을 모든 서비스가 무료라는 의미로 넓혀 읽으면 안 됩니다.'
        ], sources: ['td'] },
      { id: 'worked-example', title: '4. 프로모션 금리는 맡길 기간 전체로 계산하세요',
        paragraphs: ['아래는 비교 방법을 설명하기 위한 가상의 두 조건입니다. EQ·Tangerine·TD의 실제 금리가 아닙니다. CAD 10,000을 12개월 동안 유지하고, 각 구간의 금리가 변하지 않으며, 연 단리로 계산한다고 가정합니다.'] },
      { id: 'access-and-switching', title: '5. 다시 꺼내 쓰는 경로까지 살펴보세요',
        paragraphs: [
          '이자가 붙는 계좌라고 해서 결제할 계좌로 돈이 즉시 이동하는 것은 아닙니다. 사용할 이체 경로의 한도, 처리 시간, 입금 보류 가능성을 확인하세요. 지점 방문이나 현금 입금, 특정 결제 수단이 필요하다면 해당 계좌가 그 서비스를 제공하는지도 확인해야 합니다.',
          '저축계좌 비교를 시작하면서 모든 은행 업무를 한 번에 옮길 필요는 없습니다. 나중에 자동이체나 급여 입금까지 옮긴다면 새 계좌에서 정상 처리되는 것을 확인한 뒤 기존 계좌 해지를 검토하세요. 금리 비교를 마친 것과 계좌 이전을 마친 것은 별개의 일입니다.'
        ] },
      { id: 'make-a-shortlist', title: '6. 선택 이유를 한 문장으로 설명해 보세요',
        paragraphs: [
          '각 계좌를 후보로 남기는 이유를 적어 보세요. 기본금리인지, 충족할 수 있는 우대조건인지, 필요한 서비스인지가 드러나면 됩니다. 바로 옆에는 감수할 조건도 적으세요. 잔액·기간·사용 방식을 정하지 않은 채 어느 은행이 최고인지 묻는 것보다 판단하기 쉬워집니다.',
          'SwitchaBank에서는 공개 중인 상품을 찾아 비교 목록에 담고 조건을 나란히 볼 수 있습니다. 상품의 공개 여부와 확인일은 이 글의 출처 확인일과 다를 수 있습니다. 목록에 없다는 이유만으로 판매가 종료됐다고 판단하지 말고 공식 페이지를 확인하세요.',
          '비교 가능한 예금 두 개를 선택하면 계산기에서 지원하는 시나리오도 확인할 수 있습니다. 모든 프로모션 구간, 거래 수수료, 세금까지 계산하는 것은 아니므로 해당 조건은 별도로 비교하고 최종 조건은 은행에서 확인하세요.'
        ] }
    ],
    example: {
      title: '처음 금리가 높아도 1년 이자는 적을 수 있습니다',
      intro: '두 조건 모두 같은 원금과 12개월을 기준으로 계산했습니다.',
      headers: ['가상 조건', '단리 계산식', '12개월 이자'],
      rows: [
        ['A: 첫 3개월 연 5%, 이후 9개월 연 1%', '10,000 × 5% × 3/12 + 10,000 × 1% × 9/12', 'CAD 200'],
        ['B: 12개월 내내 연 3%', '10,000 × 3% × 12/12', 'CAD 300']
      ],
      note: '이 가정에서는 B의 이자가 CAD 100 더 많습니다. 복리, 정확한 일별 이자, 세금, 수수료, 잔액 변동은 제외했습니다. 예시의 금리는 연 단리이며 APY나 실제 은행의 현재 제안이 아닙니다.'
    },
    checklist: [
      '정확한 상품명·통화·현재 공식 조건을 기록합니다.',
      '기본금리·조건부 우대금리·기간 한정 프로모션을 구분합니다.',
      '두 계좌에 같은 잔액과 저축 기간을 적용합니다.',
      '과금 대상 거래·이체 시간·필요한 서비스를 확인합니다.',
      '신청 전 은행에서 자격 요건과 최신 조건을 확인합니다.'
    ],
    faq: [
      { question: '세 계좌 중 어디의 금리가 가장 높나요?', answer: '현재 금리, 적용 자격, 저축 기간에 따라 달라집니다. 먼저 기본금리를 비교하고 본인에게 적용되는 우대조건과 프로모션만 추가하세요. 이 글은 특정 계좌를 현재 금리 1위로 선정하지 않습니다.' },
      { question: '월 수수료가 0달러면 무료 계좌인가요?', answer: '정기적으로 부과하는 월 계좌 수수료가 없다는 의미입니다. 거래 비용이나 기타 서비스 수수료는 발생할 수 있으므로 실제 이용할 항목의 수수료표를 확인하세요.' },
      { question: '저축계좌와 GIC를 함께 비교해도 되나요?', answer: '먼저 자금 접근성과 만기 조건을 구분하세요. 저축계좌와 만기가 정해진 GIC는 다른 목적에 쓰일 수 있습니다. GIC끼리도 만기와 중도 인출 조건을 맞춘 뒤 금리를 비교하는 것이 좋습니다.' }
    ]
  },
  ja: {
    title: 'EQ Bank・Tangerine・TDの貯蓄口座比較：金利と手数料の読み方',
    description: 'カナダのEQ Bank、Tangerine、TDを月額手数料、優遇条件、キャンペーン金利、取引費用で比較。仮定の利息計算と資金移動前の確認事項も紹介します。',
    intro: '貯蓄口座の広告では金利が目を引きます。しかし資金を移す前には、特典終了後にいくら受け取れるか、お金を使うときに費用がかかるかも確認が必要です。EQ Bank・Tangerine・TDの3商品から、その違いを読み解きます。',
    takeaway: '実際に満たせる条件と預ける期間をそろえて金利を比較しましょう。取引費用と資金へのアクセスも確認が必要です。月額手数料ゼロは比較の出発点です。',
    rows: [
      { bank: 'EQ Bank', code: 'EQBANK', name: 'Personal Account', fee: 'CAD 0', detail: '最低残高の条件はありません。高い金利には対象となる定期的な直接入金の条件があるため、基本金利と分けて確認します。', source: 'eq' },
      { bank: 'Tangerine', code: 'TANGERINE', name: 'Savings Account', fee: 'CAD 0', detail: '最低残高の条件はありません。新規顧客向け特典は通常金利、対象条件、終了日をあわせて確認します。', source: 'tangerine' },
      { bank: 'TD', code: 'TD', name: 'Every Day Savings Account', fee: 'CAD 0', detail: '月1回の取引を含み、追加の課金対象取引は1回CAD 3。本人名義の他のTD預金口座への対象振替には別の規定があります。', source: 'td' }
    ],
    sections: [
      { id: 'start-with-purpose', title: '1. お金を使う日から考える',
        paragraphs: [
          '来月の家賃に使うお金と、来年の大きな支出のためのお金は役割が違います。想定残高、預けられる期間、資金を動かす頻度を書き出すと、金利比較の前提が明確になります。',
          'この記事はカナダドル建ての非登録口座を対象にしています。EQのPersonal Accountは日常取引と利息を組み合わせた口座で、Tangerine SavingsとTD Every Day Savingsは貯蓄商品です。個別口座の条件を比較しており、銀行全体の順位や、すべての口座が同じ用途に使えることを示すものではありません。'
        ] },
      { id: 'read-the-rate', title: '2. 基本金利と優遇条件を分けて読む',
        paragraphs: [
          '確認したEQ Personal Accountの案内では、高い金利の対象となるには月CAD 2,000以上の対象となる定期的な直接入金を維持する必要があります。残高条件と直接入金条件は別です。口座に資金を置くだけで優遇条件を満たすとは限りません。',
          'Tangerineでは通常のSavings金利と新規顧客向けキャンペーンを区別します。対象の入金、適用期間、終了後の金利を記録してから比較しましょう。広告の数字だけで1年間の利息はわかりません。',
          'この記事には変動する金利表を転載していません。現在の利率と特典条件は公式ページで確認してください。カナダ金融消費者庁FCACも、当初の優遇金利、残高区分、利息の計算方法を確認するよう案内しています。'
        ], sources: ['eq', 'tangerine', 'fcac'] },
      { id: 'count-the-cost', title: '3. 月額ゼロでも取引費用を確認する',
        paragraphs: [
          'TD Every Day Savingsでは、本人名義の他のTD預金口座への対象振替に別の無料規定があります。それ以外の取引は無料回数を消費したり、追加費用がかかったりする場合があります。取引の定義と例外を読んでから費用を見積もりましょう。',
          '生活費口座への振替、現金の引き出し、送金、紙の明細など、実際に使うサービスを書き出してください。それぞれを銀行の手数料表で確認すると実用的な比較になります。月額手数料がないことを、すべてのサービスが無料という意味に広げてはいけません。'
        ], sources: ['td'] },
      { id: 'worked-example', title: '4. キャンペーンは預ける期間全体で計算する',
        paragraphs: ['以下は比較方法を示す仮の条件で、EQ・Tangerine・TDの実際の金利ではありません。CAD 10,000を12か月維持し、各期間の金利は変わらず、年単利で計算すると仮定します。'] },
      { id: 'access-and-switching', title: '5. 使う口座に戻す経路まで確認する',
        paragraphs: [
          '利息が付く口座でも、支払いに使う口座へ即座に資金を移せるとは限りません。利用する振替方法の限度額、処理時間、入金保留の可能性を確認しましょう。支店や現金入金、特定の支払い方法が必要なら、その口座で使えるかも調べます。',
          '貯蓄口座を比較する段階ですべての銀行取引を移す必要はありません。後から定期支払いや給与入金も移す場合は、新口座で正常に処理されることを確認してから旧口座の解約を検討してください。金利比較と口座移行の完了は別のことです。'
        ] },
      { id: 'make-a-shortlist', title: '6. 候補に残す理由を一文にする',
        paragraphs: [
          '基本金利、満たせる優遇条件、必要なサービスなど、各口座を候補に残す理由を一文で書き、注意点を隣に添えましょう。残高、期間、使い方を決めずに一番の銀行を探すより判断しやすくなります。',
          'SwitchaBankでは公開中の商品を探し、比較リストに追加して条件を並べられます。商品の公開状況や確認日は、この記事の出典確認日と異なる場合があります。一覧にないことだけで販売終了とは判断せず、公式ページを確認してください。',
          '対応する預金商品を2件選ぶと、計算ツールでシナリオを確認できます。すべてのキャンペーン期間、取引手数料、税金を計算するわけではありません。これらは別に比較し、最終条件は銀行で確認しましょう。'
        ] }
    ],
    example: {
      title: '当初の金利が高くても年間利息は少なくなる場合がある',
      intro: 'どちらも同じ元本と12か月で計算しています。',
      headers: ['仮の条件', '単利の計算式', '12か月の利息'],
      rows: [
        ['A：最初の3か月は年5%、残り9か月は年1%', '10,000 × 5% × 3/12 + 10,000 × 1% × 9/12', 'CAD 200'],
        ['B：12か月を通して年3%', '10,000 × 3% × 12/12', 'CAD 300']
      ],
      note: 'この仮定ではBの利息がCAD 100多くなります。複利、正確な日割り計算、税金、手数料、残高変動は含みません。例示した年単利であり、APYや銀行の現在の特典ではありません。'
    },
    checklist: [
      '正確な商品名、通貨、最新の公式条件を記録する。',
      '基本金利、条件付き優遇、期間限定特典を分ける。',
      '両口座に同じ残高と貯蓄期間を適用する。',
      '課金対象取引、振替時間、必要なサービスを確認する。',
      '申込前に銀行で対象条件と最新情報を確認する。'
    ],
    faq: [
      { question: 'どの口座の金利が最も高いですか？', answer: '現在の金利、対象条件、預ける期間によって変わります。まず基本金利を比較し、適用される優遇や特典だけを加えてください。この記事では現在の金利1位を選んでいません。' },
      { question: '月額手数料ゼロなら無料で使えますか？', answer: '毎月の口座維持手数料がないという意味です。取引やその他のサービスに料金がかかる場合があるため、利用予定の項目を手数料表で確認してください。' },
      { question: '貯蓄口座とGICを比較できますか？', answer: 'まず資金へのアクセスと満期条件を分けて考えます。貯蓄口座と固定期間のGICは用途が異なる場合があります。GIC同士も満期と中途解約条件をそろえて金利を比較しましょう。' }
    ]
  }
};
const articles: Record<BlogSlug, Record<PublicLocale, BlogContent>> = {
  'ally-vs-capital-one-vs-amex-high-yield-savings': US_SAVINGS_CONTENT,
  'cashable-vs-non-cashable-gic-canada': GIC_CONTENT,
  'eq-bank-vs-tangerine-vs-td-savings': content,
  'tangerine-vs-simplii-vs-cibc-chequing-fees': CHEQUING_CONTENT
};
export function blogSources(slug: BlogSlug): readonly BlogSource[] {
  if (slug === 'ally-vs-capital-one-vs-amex-high-yield-savings') return US_SAVINGS_SOURCES;
  if (slug === 'cashable-vs-non-cashable-gic-canada') return GIC_SOURCES;
  return slug === 'tangerine-vs-simplii-vs-cibc-chequing-fees' ? CHEQUING_SOURCES : BLOG_SOURCES;
}
export function blogPresentation(slug: BlogSlug, locale: string) {
  if (slug === 'ally-vs-capital-one-vs-amex-high-yield-savings') return {
    ...US_SAVINGS_PRESENTATION[locale === 'ko' || locale === 'ja' ? locale : 'en'],
    catalog: 'savings-accounts' as CuratedSlug, guides: [] as GuideSlug[], relatedArticle: null
  };
  if (slug === 'cashable-vs-non-cashable-gic-canada') return {
    ...GIC_PRESENTATION[locale === 'ko' || locale === 'ja' ? locale : 'en'],
    catalog: '1-year-gic' as CuratedSlug, guides: ['gic-maturity-and-withdrawals', 'base-and-promotional-rates'] as GuideSlug[],
    relatedArticle: { slug: 'eq-bank-vs-tangerine-vs-td-savings' as BlogSlug, label: content[locale === 'ko' || locale === 'ja' ? locale : 'en'].title }
  };
  const copy = blogCopy(locale);
  const chequing = slug === 'tangerine-vs-simplii-vs-cibc-chequing-fees';
  const localized = CHEQUING_PRESENTATION[locale === 'ko' || locale === 'ja' ? locale : 'en'];
  return {
    ...(chequing ? localized : {
      scope: copy.scope, comparison: copy.comparison, compare: copy.compare,
      compareBody: copy.compareBody, action: copy.action,
      about: 'Canadian savings account comparisons'
    }),
    catalog: (chequing ? 'no-monthly-fee-chequing' : 'savings-accounts') as CuratedSlug,
    guides: (chequing ? ['monthly-fee-waivers', 'switching-bank-accounts'] :
      ['base-and-promotional-rates', 'monthly-fee-waivers', 'switching-bank-accounts']) as GuideSlug[],
    relatedArticle: chequing ? {
      slug: 'eq-bank-vs-tangerine-vs-td-savings' as BlogSlug, label: localized.relatedArticle
    } : {
      slug: 'tangerine-vs-simplii-vs-cibc-chequing-fees' as BlogSlug,
      label: CHEQUING_CONTENT[locale === 'ko' || locale === 'ja' ? locale : 'en'].title
    }
  };
}
export function blogContent(slug: BlogSlug, locale: string): BlogContent {
  return articles[slug][locale === 'ko' || locale === 'ja' ? locale : 'en'];
}
