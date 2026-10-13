import type { BlogContent } from './public-blog-content.ts';
import type { EditorialLocale } from './public-locale.ts';

export const US_CHECKING_SOURCES = [
  { id: 'chase-checking-fees', title: 'Chase — Additional Banking Services and Fees (PDF)', href: 'https://www.chase.com/content/dam/chase-ux/documents/personal/checking/ABSF-en.pdf' },
  { id: 'bofa-plus-fees', title: 'Bank of America — Advantage Plus Clarity Statement (PDF)', href: 'https://www.bankofamerica.com/content/documents/deposits/service/pdf/docrepo/BofA_CoreChecking_en_ADA.pdf' },
  { id: 'wells-everyday-fees', title: 'Wells Fargo — Everyday Checking Quick View of Account Fees (PDF)', href: 'https://www.wellsfargo.com/fetch-pdf?formNumber=CNS2016ED&subProductCode=WRC' },
  { id: 'wells-deposit-waiver', title: 'Wells Fargo — How to avoid the Everyday Checking monthly service fee', href: 'https://www.wellsfargo.com/checking/everyday/everyday-monthly-service-fee/' },
  { id: 'cfpb-maintenance-fee', title: 'CFPB — Monthly maintenance fees and how to avoid them', href: 'https://www.consumerfinance.gov/ask-cfpb/why-am-i-being-charged-a-monthly-maintenance-fee-for-my-bank-or-credit-union-account-en-2151/' }
] as const;

export const US_CHECKING_CONTENT: Record<EditorialLocale, BlogContent> = {
  en: {
    title: 'Chase vs Bank of America vs Wells Fargo: checking fees',
    description: 'Compare Chase Total Checking, BofA Advantage Plus and Wells Fargo Everyday Checking: monthly fees, deposit waivers, ATM costs and a 12-period example.',
    intro: 'A checking account can cost USD 0 in one statement period and USD 15 in the next. Here is how three US accounts compare on monthly fees, deposit-based waivers and ATM withdrawals.',
    takeaway: 'Compare the fee you can actually avoid. A qualifying deposit has a specific definition, and a monthly fee waiver does not make every transaction free.',
    tableHeaders: ['Account', 'Base monthly fee', 'One deposit-based route to USD 0'],
    rows: [
      { bank: 'Chase', code: 'JCBN', name: 'Total Checking', fee: 'USD 15', detail: 'USD 500 or more in qualifying electronic deposits during each monthly statement period. Other balance or linked-account waiver routes are available.', source: 'chase-checking-fees' },
      { bank: 'Bank of America', code: 'BOAN', name: 'Advantage Plus Banking', fee: 'USD 12', detail: 'At least one qualifying direct deposit of USD 250 or more during each statement cycle. Other minimum-daily-balance or eligible BofA Rewards waiver routes are available.', source: 'bofa-plus-fees' },
      { bank: 'Wells Fargo', code: 'WFBN', name: 'Everyday Checking', fee: 'USD 15', detail: 'USD 500 or more in total qualifying electronic deposits each fee period. Other balance, age or qualifying military-deposit waiver routes are available.', source: 'wells-everyday-fees' }
    ],
    infographic: { title: 'Compare the cost in three steps', steps: [
      { title: 'Base fee', text: 'What is charged without a waiver?' },
      { title: 'Waiver', text: 'Which deposits qualify, and when?' },
      { title: 'ATM costs', text: 'Your bank’s fee plus the operator’s fee.' }
    ] },
    sections: [
      { id: 'qualifying-deposits', title: '1. Check the deposit, not just the total', paragraphs: ['Bank of America requires at least one qualifying direct deposit of USD 250: two USD 125 deposits do not satisfy that route. Chase and Wells Fargo use a USD 500 qualifying-electronic-deposit threshold for their respective periods. Chase excludes Zelle, cash, checks and wires; Wells Fargo excludes Zelle, account-to-account transfers, mobile deposits and branch or ATM deposits. Check how your payment is classified and when it posts.'], sources: ['chase-checking-fees', 'bofa-plus-fees', 'wells-deposit-waiver'] },
      { id: 'atm-costs', title: '2. Add ATM costs separately', paragraphs: ['For a cash withdrawal at another bank’s ATM in the US, the disclosed bank fee is USD 3 at Chase, USD 2.50 at Bank of America and USD 3 at Wells Fargo. The ATM operator may charge extra. Monthly maintenance, ATM, overdraft and other service charges are separate items; use each account’s fee schedule for your actual transactions.'], sources: ['chase-checking-fees', 'bofa-plus-fees', 'wells-everyday-fees'] },
      { id: 'worked-example', title: '3. Count the periods that will be charged', paragraphs: ['A waiver that you meet consistently matters more than a small difference in base fees. Other waiver routes may fit your circumstances; the table shows only the deposit route. Check the official requirements and your statement period dates.'], sources: ['cfpb-maintenance-fee'] }
    ],
    example: { title: '12 charged periods: USD 144 or USD 180', intro: 'Illustration: the base monthly fee is charged in each of 12 periods. These bars show maintenance costs only.', headers: ['Account', 'Calculation', 'Maintenance fees'],
      rows: [['Chase Total Checking', 'USD 15 × 12', 'USD 180'], ['BofA Advantage Plus', 'USD 12 × 12', 'USD 144'], ['Wells Fargo Everyday Checking', 'USD 15 × 12', 'USD 180']],
      chart: { values: [180, 144, 180], difference: 'USD 3 per period × 12 = USD 36 difference' },
      note: 'Assumes unchanged base fees with no waivers or introductory relief. This is not a first-year quote: new-account fee relief may change the number of charged periods. Excludes ATM, overdraft and all other service fees, bonuses and interest.' },
    checklist: ['Confirm your exact account and statement or fee-period dates.', 'Verify that a deposit qualifies before relying on a waiver.', 'Compare your ATM use and other service fees, then confirm current terms with the bank.'],
    faq: [
      { question: 'Does USD 250 in total deposits waive BofA Advantage Plus fees?', answer: 'For the deposit route, at least one qualifying direct deposit must be USD 250 or more. Two deposits of USD 125 do not meet that requirement. Other waiver routes are separate.' },
      { question: 'Do Zelle payments count for Chase or Wells Fargo?', answer: 'The checked disclosures exclude Zelle from these accounts’ qualifying electronic deposits. A credit arriving in the account does not automatically satisfy the waiver.' },
      { question: 'Does USD 0 monthly maintenance mean no fees at all?', answer: 'A monthly fee waiver covers that fee. Check ATM, overdraft and other service charges separately.' }
    ]
  },
  ko: {
    title: '미국 체킹계좌 비교: Chase·Bank of America·Wells Fargo 수수료',
    description: 'Chase Total Checking, BofA Advantage Plus, Wells Fargo Everyday Checking의 월 수수료·입금 면제 조건·ATM 비용을 비교합니다. 12회 청구 예시를 인포그래픽으로 확인하세요.',
    intro: '같은 체킹계좌도 이번 명세 기간에는 0달러, 다음 기간에는 15달러가 들 수 있습니다. 미국 계좌 세 가지의 월 수수료, 입금으로 면제받는 조건, ATM 출금 비용을 정리했습니다.',
    takeaway: '실제로 면제받을 수 있는 수수료를 비교하세요. 인정되는 입금에는 정해진 기준이 있으며, 월 수수료 면제가 모든 거래의 무료 이용을 뜻하지는 않습니다.',
    tableHeaders: ['계좌', '기본 월 수수료', '입금으로 USD 0이 되는 조건 한 가지'],
    rows: [
      { bank: 'Chase', code: 'JCBN', name: 'Total Checking', fee: 'USD 15', detail: '매월 명세 기간에 인정되는 전자 입금 USD 500 이상. 잔액 또는 연결 계좌를 통한 다른 면제 방법도 있습니다.', source: 'chase-checking-fees' },
      { bank: 'Bank of America', code: 'BOAN', name: 'Advantage Plus Banking', fee: 'USD 12', detail: '매 명세 주기에 인정되는 direct deposit이 건당 USD 250 이상으로 최소 1회. 최저 일일 잔액이나 자격을 갖춘 BofA Rewards를 통한 면제 방법도 있습니다.', source: 'bofa-plus-fees' },
      { bank: 'Wells Fargo', code: 'WFBN', name: 'Everyday Checking', fee: 'USD 15', detail: '수수료 산정 기간마다 인정되는 전자 입금 합계 USD 500 이상. 잔액·연령·인정되는 군 급여 입금에 따른 다른 면제 방법도 있습니다.', source: 'wells-everyday-fees' }
    ],
    infographic: { title: '비용은 세 단계로 비교하세요', steps: [
      { title: '기본 수수료', text: '면제받지 못하면 얼마가 드나요?' },
      { title: '면제 조건', text: '어떤 입금이 언제 인정되나요?' },
      { title: 'ATM 비용', text: '은행 수수료와 운영자 수수료를 더합니다.' }
    ] },
    sections: [
      { id: 'qualifying-deposits', title: '1. 입금 총액보다 인정 기준을 확인하세요', paragraphs: ['Bank of America의 입금 면제 조건은 인정되는 direct deposit이 건당 USD 250 이상으로 최소 1회입니다. USD 125씩 두 번으로는 이 조건을 충족하지 못합니다. Chase와 Wells Fargo는 각 산정 기간에 인정되는 전자 입금 USD 500을 기준으로 합니다. Chase는 Zelle·현금·수표·wire transfer를, Wells Fargo는 Zelle·계좌 간 이체·모바일 입금·지점 및 ATM 입금을 제외합니다. 입금의 분류와 실제 반영일을 확인하세요.'], sources: ['chase-checking-fees', 'bofa-plus-fees', 'wells-deposit-waiver'] },
      { id: 'atm-costs', title: '2. ATM 비용은 따로 더하세요', paragraphs: ['미국 내 타행 ATM에서 현금을 인출할 때 공시된 은행 수수료는 Chase USD 3, Bank of America USD 2.50, Wells Fargo USD 3입니다. ATM 운영자 수수료는 별도로 붙을 수 있습니다. 월 유지비, ATM, 잔액 부족 거래(overdraft), 기타 서비스 비용은 서로 다른 항목이므로 실제 이용할 거래를 수수료표에서 확인하세요.'], sources: ['chase-checking-fees', 'bofa-plus-fees', 'wells-everyday-fees'] },
      { id: 'worked-example', title: '3. 실제로 청구될 횟수를 세어보세요', paragraphs: ['기본 수수료의 작은 차이보다 꾸준히 충족할 수 있는 면제 조건이 중요합니다. 표에는 입금 조건 한 가지만 담았으며 다른 면제 방법도 있습니다. 공식 요건과 본인 계좌의 명세·산정 기간을 확인하세요.'], sources: ['cfpb-maintenance-fee'] }
    ],
    example: { title: '수수료 12회 청구: USD 144 또는 USD 180', intro: '각 산정 기간에 기본 월 수수료가 부과되고, 총 12회 청구된다고 가정합니다. 막대는 유지 수수료만 보여줍니다.', headers: ['계좌', '계산', '유지 수수료'],
      rows: [['Chase Total Checking', 'USD 15 × 12', 'USD 180'], ['BofA Advantage Plus', 'USD 12 × 12', 'USD 144'], ['Wells Fargo Everyday Checking', 'USD 15 × 12', 'USD 180']],
      chart: { values: [180, 144, 180], difference: '회당 USD 3 × 12회 = USD 36 차이' },
      note: '기본 수수료가 변하지 않고 면제나 초기 유예가 없다고 가정한 예시입니다. 첫해 비용 견적은 아니며, 신규 계좌의 수수료 유예로 실제 청구 횟수가 달라질 수 있습니다. ATM·overdraft·기타 서비스 비용, 보너스, 이자는 제외합니다.' },
    checklist: ['정확한 계좌명과 명세·수수료 산정 기간을 확인합니다.', '면제받으려는 입금이 인정되는지 확인합니다.', 'ATM 이용과 기타 서비스 비용을 비교한 뒤 은행에서 최신 조건을 확인합니다.'],
    faq: [
      { question: 'BofA Advantage Plus는 총 USD 250을 입금하면 면제되나요?', answer: '입금 조건을 쓰려면 인정되는 direct deposit이 건당 USD 250 이상으로 최소 1회 있어야 합니다. USD 125씩 두 번은 해당 조건에 맞지 않습니다. 다른 면제 방법은 별도입니다.' },
      { question: 'Zelle 입금도 Chase나 Wells Fargo에서 인정되나요?', answer: '확인한 공시에서는 Zelle을 해당 계좌의 인정되는 전자 입금에서 제외합니다. 계좌에 돈이 들어왔다고 면제 조건이 자동 충족되지는 않습니다.' },
      { question: '월 유지 수수료가 0이면 모든 비용이 없나요?', answer: '월 수수료 면제는 해당 항목의 면제입니다. ATM·overdraft·기타 서비스 비용은 따로 확인하세요.' }
    ]
  },
  ja: {
    title: '米国の当座口座比較：Chase・Bank of America・Wells Fargoの手数料',
    description: 'Chase Total Checking、BofA Advantage Plus、Wells Fargo Everyday Checkingの月額手数料、入金による免除条件、ATM費用を比較。12回請求の例を図で確認できます。',
    intro: '同じ当座口座でも、今期は0ドル、次の明細期間は15ドルになる場合があります。米国の三つの口座を、月額手数料、入金による免除条件、ATM出金費用で比較します。',
    takeaway: '実際に免除できる手数料を比較しましょう。対象入金には決まった定義があり、月額手数料の免除がすべての取引の無料利用を意味するわけではありません。',
    tableHeaders: ['口座', '基本月額手数料', '入金でUSD 0にする条件の一例'],
    rows: [
      { bank: 'Chase', code: 'JCBN', name: 'Total Checking', fee: 'USD 15', detail: '各月次明細期間に対象となる電子入金USD 500以上。残高や関連口座による別の免除方法もあります。', source: 'chase-checking-fees' },
      { bank: 'Bank of America', code: 'BOAN', name: 'Advantage Plus Banking', fee: 'USD 12', detail: '各明細サイクルに1回USD 250以上の対象ダイレクトデポジットが最低1回。最低日次残高や対象BofA Rewardsによる免除方法もあります。', source: 'bofa-plus-fees' },
      { bank: 'Wells Fargo', code: 'WFBN', name: 'Everyday Checking', fee: 'USD 15', detail: '各手数料算定期間に対象電子入金が合計USD 500以上。残高・年齢・対象軍給与入金による別の免除方法もあります。', source: 'wells-everyday-fees' }
    ],
    infographic: { title: '費用は三つの手順で比較', steps: [
      { title: '基本手数料', text: '免除がなければいくらかかる？' },
      { title: '免除条件', text: 'どの入金が、いつ対象になる？' },
      { title: 'ATM費用', text: '銀行手数料と運営者手数料を合算。' }
    ] },
    sections: [
      { id: 'qualifying-deposits', title: '1. 入金合計より対象条件を確認する', paragraphs: ['Bank of Americaの入金条件は1回USD 250以上の対象ダイレクトデポジットが最低1回。USD 125を2回ではこの条件を満たしません。ChaseとWells Fargoは、それぞれの期間に対象電子入金USD 500が基準です。ChaseはZelle・現金・小切手・電信送金を、Wells FargoはZelle・口座間振替・モバイル入金・支店やATMでの入金を対象外としています。入金の分類と計上日を確認しましょう。'], sources: ['chase-checking-fees', 'bofa-plus-fees', 'wells-deposit-waiver'] },
      { id: 'atm-costs', title: '2. ATM費用は別に加える', paragraphs: ['米国内の他行ATMで現金を引き出す際の公表銀行手数料は、ChaseがUSD 3、Bank of AmericaがUSD 2.50、Wells FargoがUSD 3です。ATM運営者の手数料が加わる場合もあります。月額維持費、ATM、当座貸越（overdraft）、その他サービスの費用は別項目です。実際に使う取引を手数料表で確認してください。'], sources: ['chase-checking-fees', 'bofa-plus-fees', 'wells-everyday-fees'] },
      { id: 'worked-example', title: '3. 実際に請求される回数を数える', paragraphs: ['基本手数料の小さな差よりも、継続して満たせる免除条件が重要です。表には入金条件の一例だけを示しており、他の免除方法もあります。公式要件と自分の口座の明細・算定期間を確認しましょう。'], sources: ['cfpb-maintenance-fee'] }
    ],
    example: { title: '12回請求：USD 144またはUSD 180', intro: '基本月額手数料が各期間に発生し、合計12回請求される例です。棒グラフは維持手数料のみを示します。', headers: ['口座', '計算', '維持手数料'],
      rows: [['Chase Total Checking', 'USD 15 × 12', 'USD 180'], ['BofA Advantage Plus', 'USD 12 × 12', 'USD 144'], ['Wells Fargo Everyday Checking', 'USD 15 × 12', 'USD 180']],
      chart: { values: [180, 144, 180], difference: '1回USD 3 × 12回 = USD 36の差' },
      note: '基本手数料が変わらず、免除や当初の猶予がない仮定です。初年度の見積もりではなく、新規口座の手数料猶予により請求回数は変わり得ます。ATM・overdraft・その他サービスの費用、特典、利息は含みません。' },
    checklist: ['正確な口座名と明細・手数料算定期間を確認する。', '免除に使う入金が対象になるか確認する。', 'ATM利用とその他費用を比較し、銀行で最新条件を確認する。'],
    faq: [
      { question: 'BofA Advantage Plusは合計USD 250の入金で免除されますか？', answer: '入金条件を使うには、1回USD 250以上の対象ダイレクトデポジットが最低1回必要です。USD 125を2回では満たしません。他の免除方法は別条件です。' },
      { question: 'ZelleはChaseやWells Fargoで対象になりますか？', answer: '確認した公表条件では、Zelleはこれらの口座の対象電子入金に含まれません。口座に入金されたことだけで免除条件を満たすわけではありません。' },
      { question: '月額維持手数料が0なら費用はありませんか？', answer: '月額手数料の免除は、その項目の免除です。ATM・overdraft・その他サービスの費用は別に確認してください。' }
    ]
  }
};

export const US_CHECKING_PRESENTATION = {
  en: { scope: 'United States · Checking', comparison: 'Three checking accounts: base fees and deposit waivers', compare: 'Compare US checking accounts', compareBody: 'Browse published US checking accounts and compare their conditions. Read verification dates and confirm current fees with the bank. Not every account discussed here is necessarily listed.', action: 'Explore US checking', about: 'US checking account monthly fees, deposit waivers and ATM costs' },
  ko: { scope: '미국 · 체킹계좌', comparison: '체킹계좌 세 가지: 기본 수수료와 입금 면제 조건', compare: '미국 체킹계좌를 비교하세요', compareBody: '공개된 미국 체킹계좌의 조건을 비교하세요. 확인일을 살펴보고 최신 수수료는 은행에서 확인하세요. 이 글의 계좌가 모두 목록에 있는 것은 아닙니다.', action: '미국 체킹계좌 살펴보기', about: '미국 체킹계좌의 월 수수료·입금 면제 조건·ATM 비용 비교' },
  ja: { scope: '米国 · 当座口座', comparison: '三つの当座口座：基本手数料と入金による免除', compare: '米国の当座口座を比較', compareBody: '公開中の米国当座口座の条件を比較できます。確認日を読み、最新手数料は銀行で確認してください。本文の口座がすべて掲載されているとは限りません。', action: '米国の当座口座を見る', about: '米国当座口座の月額手数料・入金免除条件・ATM費用の比較' }
} satisfies Record<EditorialLocale, object>;
