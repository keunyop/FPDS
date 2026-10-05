import type { BlogContent } from './public-blog-content.ts';
import type { PublicLocale } from './public-locale.ts';

export const CHEQUING_SOURCES = [
  { id: 'tangerine-chequing', title: 'Tangerine — No-fee daily Chequing Account', href: 'https://www.tangerine.ca/en/personal/spend/chequing-account-benefits' },
  { id: 'simplii-chequing', title: 'Simplii Financial — No Fee Chequing Account', href: 'https://www.simplii.com/en/bank-accounts/no-fee-chequing.html' },
  { id: 'cibc-smart', title: 'CIBC — Smart Account', href: 'https://www.cibc.com/en/personal-banking/bank-accounts/chequing-accounts/smart-account.html' },
  { id: 'tangerine-fees', title: 'Tangerine — Bank Fee Schedule', href: 'https://www.tangerine.ca/en/legal/fee-schedule/bank-fee-schedule' },
  { id: 'cibc-accounts', title: 'CIBC — Chequing accounts and banking tiers', href: 'https://www.cibc.com/en/personal-banking/bank-accounts/chequing-accounts.html' },
  { id: 'fcac-chequing', title: 'FCAC — Chequing accounts', href: 'https://www.canada.ca/en/financial-consumer-agency/services/banking/bank-accounts/chequing-accounts.html' },
  { id: 'fcac-switching', title: 'FCAC — Transferring products or services', href: 'https://www.canada.ca/en/financial-consumer-agency/services/banking/transferring-products-services.html' },
  { id: 'fcac-atm', title: 'FCAC — ATM fees', href: 'https://www.canada.ca/en/financial-consumer-agency/services/banking/atm-fees.html' }
] as const;

export const CHEQUING_PRESENTATION = {
  en: {
    scope: 'Canada · Chequing accounts', comparison: 'Tangerine, Simplii and CIBC at a glance',
    compare: 'Turn your fee check into a comparison',
    compareBody: 'Open SwitchaBank’s Canadian chequing catalog, ordered by monthly fee. Choose available products for your comparison list, then read transaction costs, fee-waiver conditions and verification dates together. The catalog may not include every account discussed here.',
    action: 'Compare chequing accounts',
    relatedArticle: 'Next: compare EQ Bank, Tangerine and TD savings accounts',
    about: 'Canadian chequing account fees and fee-waiver conditions'
  },
  ko: {
    scope: '캐나다 · 체킹계좌', comparison: 'Tangerine·Simplii·CIBC 한눈에 비교',
    compare: '명세서를 확인했다면, SwitchaBank에서 비교하세요',
    compareBody: 'SwitchaBank의 캐나다 체킹상품 목록은 월 수수료가 낮은 순서로 열립니다. 공개 중인 상품을 비교 목록에 담고 거래 비용·수수료 면제 조건·확인일을 나란히 읽어 보세요. 이 글에서 다룬 모든 계좌가 목록에 포함되어 있는 것은 아닙니다.',
    action: '체킹계좌 수수료 비교하기',
    relatedArticle: '이어서 읽기: EQ Bank·Tangerine·TD 저축계좌 비교',
    about: '캐나다 체킹계좌 수수료와 면제 조건'
  },
  ja: {
    scope: 'カナダ · 当座口座', comparison: 'Tangerine・Simplii・CIBCを比較',
    compare: '明細を確認したら、SwitchaBankで比較しましょう',
    compareBody: 'SwitchaBankのカナダ当座口座一覧を、月額手数料の低い順で開きます。公開中の商品を比較リストに追加し、取引費用・免除条件・確認日を並べて読んでください。この記事で紹介したすべての口座が掲載されているとは限りません。',
    action: '当座口座の手数料を比較する',
    relatedArticle: '次に読む：EQ Bank・Tangerine・TDの貯蓄口座比較',
    about: 'カナダの当座口座手数料と免除条件'
  }
} satisfies Record<PublicLocale, object>;

export const CHEQUING_CONTENT: Record<PublicLocale, BlogContent> = {
  en: {
    title: 'Tangerine vs Simplii vs CIBC: Canadian chequing fees compared',
    description: 'Compare Canadian chequing accounts from Tangerine, Simplii and CIBC: monthly fees, minimum-balance rebates, ATM costs and a worked annual-cost example.',
    intro: 'A small charge on your bank statement becomes a bigger number over a year. But replacing it with a “free” account takes more than finding a zero in a fee column. Here is how to compare everyday banking costs, using three Canadian chequing accounts and the way you actually use your money.',
    takeaway: 'Separate a zero base monthly fee from a fee rebate you must qualify for. Compare included transactions and the services you use, then calculate annual fees and the value of money held for a rebate. Use that shortlist to compare current products on SwitchaBank.',
    rows: [
      { bank: 'Tangerine', code: 'TANGERINE', name: 'No-fee daily Chequing Account', fee: 'CAD 0', detail: 'No minimum balance for the monthly fee. Unlimited everyday debit purchases, bill payments and pre-authorized transactions; free Interac e-Transfer. Non-standard services can cost extra.', source: 'tangerine-chequing' },
      { bank: 'Simplii Financial', code: 'SIMPLII', name: 'No Fee Chequing Account', fee: 'CAD 0', detail: 'Unlimited debit purchases, bill payments and withdrawals. Free use of CIBC ATMs; special requests and additional services have their own charges.', source: 'simplii-chequing' },
      { bank: 'CIBC', code: 'CIBC', name: 'Smart Account · Tier 1', fee: 'CAD 16.95', detail: 'Unlimited transactions, including Interac e-Transfer. A CAD 4,000 end-of-day balance each day of the month in one Smart Account qualifies for the monthly fee rebate on up to three Smart Accounts. Other eligibility and tier benefits may apply.', source: 'cibc-smart' }
    ],
    sections: [
      { id: 'start-with-your-statement', title: '1. Start with a statement, not an opening bonus', paragraphs: [
        'Take one recent month of banking activity and mark four things: account fees, cash withdrawals, payments and your lowest balance. If that month was unusual, add two ordinary months. You are building a picture of the services you need, rather than trying to choose a bank from its headline offer.',
        'Keep a one-time opening bonus in a separate column. Record its eligibility, deadline and required actions only after checking the live terms. A bonus does not tell you what the account costs in year two. This article covers Canadian-dollar personal chequing accounts, not business or US-dollar accounts.'
      ], sources: ['fcac-chequing'] },
      { id: 'free-versus-rebated', title: '2. Read “no monthly fee” and “fee rebated” differently', paragraphs: [
        'For Tangerine and Simplii, the comparison starts with a zero base monthly fee. CIBC’s Tier 1 starts with a payable fee and a separate rebate condition. That distinction matters if your balance moves around payday or rent day.',
        'For the CIBC balance route, check the end-of-day amount throughout the month; a healthy month-end balance alone is not the test. Other routes can change the result, including eligible banking tiers and customer programs. Confirm which rule applies to your account before assigning an annual cost.',
        'A useful comparison note has two lines: “fee before any rebate” and “the condition I can meet.” Keeping both prevents a conditional zero from looking like an unconditional price.'
      ], sources: ['cibc-smart', 'cibc-accounts'] },
      { id: 'check-the-extra-costs', title: '3. Match the ATM network and extra services to your routine', paragraphs: [
        'Unlimited everyday transactions still leaves room for charges on specific services. On Tangerine’s checked fee schedule, a withdrawal at another bank’s ATM in Canada costs CAD 1.50; the ATM operator may charge separately. Use the current schedule for exceptions and other services.',
        'For each candidate, list the cash machines you would use near home and work. Then check whether you need bank drafts, extra cheque books, paper statements or overdraft. A free transaction allowance does not price every one of those services.',
        'For CIBC, read ATM rebates alongside the banking tier rather than assuming every ATM is included. Compare the services you will use regularly, and give a separate value only to benefits you would otherwise pay for.'
      ], sources: ['tangerine-fees', 'cibc-accounts', 'fcac-atm'] },
      { id: 'worked-example', title: '4. Turn monthly fees and a held balance into annual numbers', paragraphs: [
        'The examples below use the checked CAD 16.95 monthly fee and CAD 4,000 balance threshold as inputs. They describe possible situations for one account, not your bill. All twelve fee months, or three missed-rebate months, are assumptions; any applicable exemption changes the calculation.',
        'A balance kept for a rebate can also have an opportunity cost: interest it could have earned elsewhere. The third line assumes no interest on that balance in one account and a fictional 3% annual simple rate in another. It is a separate comparison of foregone interest, not an additional bank fee.',
        'Do not add all three lines together. First choose the fee situation that matches your assumptions. Then consider any realistic difference in interest, plus the services you value. Money needed for bills may not be available to hold elsewhere all year.'
      ] },
      { id: 'compare-on-switchabank', title: '5. Build a shortlist on SwitchaBank', paragraphs: [
        'Open the chequing catalog using the comparison button below. Start with monthly fees, then open the details of the available products you want to investigate. Add candidates to the comparison list so you can read their published conditions together instead of comparing screenshots from different dates.',
        'Check currency, included transactions and costs when you go beyond them. Read any disclosed fee-waiver condition in full and check the product’s verification date. If a condition is absent, confirm it with the bank; a missing value is not proof of a free service.',
        'You can save the comparison list on your device to revisit it with current data. Before applying, use the official bank link and recheck eligibility and fees. SwitchaBank helps organize the comparison; the final choice depends on the services and conditions you need.'
      ] },
      { id: 'switch-with-a-plan', title: '6. Move payments in an order you can verify', paragraphs: [
        'Prepare a list of salary deposits, rent, utilities, subscriptions and other automatic payments. Set up the new account and access to it, update each payment instruction, then check that the changes actually appear in account activity.',
        'Leave enough time and money for pending transactions in the old account. Check outstanding cheques, transfer timing and any closure charge before closing it. Keep records of completed changes so a missed payment is easier to trace.'
      ], sources: ['fcac-switching'] },
      { id: 'finish-the-comparison', title: '7. Give spending money and savings separate jobs', paragraphs: [
        'A chequing account comparison answers how much daily banking costs. A savings comparison asks what money can earn while you do not need it. Those are two different questions, even when one institution offers both.',
        'Once you have identified your payment needs, read our EQ Bank, Tangerine and TD savings comparison below. It explains regular and promotional rates, transaction costs and how to compare the same amount over the same period. Together, the two comparisons give you a clearer basis for checking your banking setup.'
      ] }
    ],
    example: {
      title: 'One monthly fee, three different calculations',
      intro: 'Illustrative situations for one account over 12 months. CAD 16.95 and CAD 4,000 are checked CIBC inputs; 3% is a fictional savings rate.',
      headers: ['Situation', 'Calculation', 'Annual amount'],
      rows: [
        ['No rebate or exemption for 12 months', 'CAD 16.95 × 12', 'CAD 203.40'],
        ['Rebate missed in 3 months; granted in the other 9', 'CAD 16.95 × 3', 'CAD 50.85'],
        ['Foregone interest on a constant CAD 4,000 balance', 'CAD 4,000 × 3% × 12 / 12', 'CAD 120']
      ],
      note: 'The rows describe separate scenarios and are not added together. The 3% rate is hypothetical, not a current offer or APY. Simple interest excludes compounding, tax, fees and changing balances; the interest difference assumes zero interest in the account holding the rebate balance. No return or rebate is guaranteed.'
    },
    checklist: [
      'Write down ordinary monthly transactions, ATM locations and your lowest end-of-day balance.',
      'Keep the base fee and any rebate or customer-program condition in separate lines.',
      'Price only the extra services you expect to use, with current official fee schedules.',
      'Use SwitchaBank to compare available chequing products and their verification dates.',
      'Confirm eligibility with the bank, then verify deposits and automatic payments before closing the old account.'
    ],
    faq: [
      { question: 'Which Canadian chequing account has no monthly fee?', answer: 'The checked Tangerine and Simplii accounts have zero base monthly fees. CIBC Smart’s Tier 1 fee can be rebated under the stated conditions, and other eligible benefits may apply. Monthly fee alone does not cover every service charge; use the comparison table and official terms together.' },
      { question: 'Is a minimum-balance rebate worth it?', answer: 'Calculate the fees avoided in the months you can meet the condition. Compare that with any realistic interest difference on the held balance and the services you use. A balance available only on payday is different from one you can maintain throughout the month.' },
      { question: 'Does unlimited banking include every ATM withdrawal?', answer: 'Check the named ATM network, the account’s fee schedule and any operator surcharge. An unlimited transaction allowance and an ATM fee rebate are separate conditions.' },
      { question: 'Can I compare these accounts on SwitchaBank?', answer: 'Use the Canadian chequing catalog to select currently published products. Availability changes, so every account in this article may not be listed. Compare the available choices, read their verification dates and confirm final conditions on the bank’s official page.' }
    ]
  },
  ko: {
    title: '캐나다 체킹계좌 비교: Tangerine·Simplii·CIBC 수수료와 면제 조건',
    description: '캐나다 체킹계좌를 비교할 때 확인할 Tangerine·Simplii·CIBC의 월 수수료, 최소 잔액 면제 조건, ATM 비용과 연간 비용 계산을 정리했습니다. SwitchaBank에서 실제 상품 비교로 이어가세요.',
    intro: '매달 명세서에 찍히는 작은 수수료도 1년을 합치면 이야기가 달라집니다. 그렇다고 ‘무료 계좌’라는 문구만 보고 은행을 바꾸기는 어렵습니다. Tangerine·Simplii·CIBC의 체킹계좌를 예로 들어, 생활비를 관리하는 방식에 맞춰 비용과 조건을 비교하는 순서를 정리했습니다.',
    takeaway: '기본 월 수수료가 0달러인 계좌와 조건을 충족하면 수수료를 돌려주는 계좌를 구분하세요. 자주 쓰는 거래와 부가 서비스를 확인한 뒤, 연간 수수료와 면제를 위해 유지할 돈의 가치를 계산하세요. 그 기준으로 SwitchaBank에서 현재 공개 중인 상품을 비교할 수 있습니다.',
    rows: [
      { bank: 'Tangerine', code: 'TANGERINE', name: 'No-fee daily Chequing Account', fee: 'CAD 0', detail: '월 수수료를 피하기 위한 최소 잔액이 없습니다. 일상 직불카드 결제·청구서 납부·사전 승인 거래는 무제한이며 Interac e-Transfer는 무료입니다. 비표준 서비스는 별도 비용이 들 수 있습니다.', source: 'tangerine-chequing' },
      { bank: 'Simplii Financial', code: 'SIMPLII', name: 'No Fee Chequing Account', fee: 'CAD 0', detail: '직불카드 결제·청구서 납부·인출은 무제한입니다. CIBC ATM을 무료로 이용할 수 있으며, 특별 요청과 부가 서비스에는 별도 요금이 적용됩니다.', source: 'simplii-chequing' },
      { bank: 'CIBC', code: 'CIBC', name: 'Smart Account · Tier 1', fee: 'CAD 16.95', detail: 'Interac e-Transfer를 포함한 거래가 무제한입니다. 한 Smart Account에서 그 달 매일 마감 잔액 CAD 4,000을 유지하면 최대 세 Smart Account의 월 수수료 환급 대상이 됩니다. 별도 자격·등급 혜택도 확인하세요.', source: 'cibc-smart' }
    ],
    sections: [
      { id: 'start-with-your-statement', title: '1. 가입 보너스보다 최근 명세서를 먼저 보세요', paragraphs: [
        '최근 한 달의 거래 내역에서 계좌 수수료, 현금 인출, 결제, 가장 낮았던 잔액을 표시해 보세요. 이사나 여행으로 평소와 다른 달이었다면 보통의 두 달을 더 살펴보면 좋습니다. 이 작업의 목적은 내가 반복해서 쓰는 서비스를 확인하는 것입니다.',
        '가입 보너스는 별도 칸에 적으세요. 공식 페이지에서 대상·마감일·필수 행동을 확인한 뒤 따로 계산해야 합니다. 일회성 혜택은 2년 차 계좌 비용을 설명하지 못합니다. 이 글은 캐나다 달러 개인 체킹계좌를 다루며 사업자·미국 달러 계좌 비교와는 구분합니다.'
      ], sources: ['fcac-chequing'] },
      { id: 'free-versus-rebated', title: '2. ‘월 수수료 없음’과 ‘조건부 환급’은 다릅니다', paragraphs: [
        'Tangerine과 Simplii는 기본 월 수수료 0달러에서 비교가 시작됩니다. CIBC Tier 1은 기본 요금과 환급 조건을 함께 읽어야 합니다. 급여일에는 잔액이 충분하지만 월세를 내면 줄어드는 경우라면 이 차이가 중요합니다.',
        'CIBC의 잔액 조건은 한 달 동안의 매일 마감 잔액을 기준으로 봅니다. 월말에만 돈을 채워 놓는 것으로 판단하면 안 됩니다. 별도 등급 혜택과 고객 프로그램도 비용을 바꿀 수 있으므로, 본인 계좌에 적용되는 규칙을 먼저 확인하세요.',
        '비교 메모에는 ‘환급 전 기본 요금’과 ‘내가 충족할 조건’을 두 줄로 적으세요. 조건이 붙은 0달러를 아무 조건 없는 가격처럼 읽는 실수를 줄일 수 있습니다.'
      ], sources: ['cibc-smart', 'cibc-accounts'] },
      { id: 'check-the-extra-costs', title: '3. 무료 거래 범위와 자주 쓰는 ATM을 확인하세요', paragraphs: [
        '일상 거래가 무제한이어도 특정 서비스에 요금이 붙을 수 있습니다. 확인한 Tangerine 수수료표에서 캐나다 내 다른 은행 ATM 인출 요금은 CAD 1.50이며, ATM 운영자가 별도 요금을 부과할 수도 있습니다. 예외와 다른 서비스는 최신 수수료표를 확인하세요.',
        '집과 직장 주변에서 실제로 쓸 ATM부터 적어 보세요. 은행 수표 발행, 추가 수표책, 종이 명세서, 초과인출 서비스를 쓰는지도 확인하세요. 무료 거래 횟수만으로 이 모든 항목의 가격을 알 수는 없습니다.',
        'CIBC의 ATM 환급은 계좌 등급 혜택과 함께 읽어야 합니다. 모든 ATM이 포함된다고 가정하지 마세요. 자주 쓰는 서비스끼리 비교하고, 다른 곳에서 실제로 돈을 내고 썼을 혜택에만 별도 가치를 부여하면 비교가 명확해집니다.'
      ], sources: ['tangerine-fees', 'cibc-accounts', 'fcac-atm'] },
      { id: 'worked-example', title: '4. 월 수수료와 유지 잔액을 1년 기준으로 계산하세요', paragraphs: [
        '아래 예시는 확인한 CIBC 월 수수료 CAD 16.95와 잔액 기준 CAD 4,000을 계산 입력으로 사용합니다. 한 계좌에서 생길 수 있는 상황을 가정한 것으로, 실제 청구서가 아닙니다. 12개월 모두 수수료를 내거나 3개월만 환급을 못 받는 것은 예시의 가정이며, 다른 면제 혜택이 적용되면 결과가 달라집니다.',
        '환급을 받으려고 유지하는 돈에는 다른 곳에서 얻을 수 있었던 이자라는 기회비용도 생길 수 있습니다. 세 번째 줄은 그 잔액이 한 계좌에서는 이자를 받지 않고, 다른 계좌에서는 가상의 연 3% 단리 이자를 받는다고 가정합니다. 이는 받지 못한 이자의 비교이며 추가 은행 수수료가 아닙니다.',
        '세 줄을 모두 더하지 마세요. 먼저 자신의 가정에 맞는 수수료 상황을 하나 고르고, 현실적인 이자 차이와 필요한 서비스의 가치를 함께 보세요. 생활비로 곧 쓸 돈이라면 1년 내내 다른 곳에 맡겨 둘 수 있다는 가정부터 맞지 않을 수 있습니다.'
      ] },
      { id: 'compare-on-switchabank', title: '5. SwitchaBank에서 비교 후보를 좁히세요', paragraphs: [
        '아래 버튼으로 체킹상품 목록을 여세요. 월 수수료를 먼저 살펴보고, 더 알아볼 공개 상품의 상세 정보를 읽으세요. 후보를 비교 목록에 추가하면 서로 다른 날짜의 화면 캡처를 번갈아 보는 대신 공개된 조건을 나란히 확인할 수 있습니다.',
        '통화, 포함된 거래, 허용 횟수를 넘었을 때의 비용을 확인하세요. 공개된 수수료 면제 조건은 끝까지 읽고 상품 확인일도 살펴보세요. 조건이 적혀 있지 않다면 은행에 확인해야 합니다. 정보가 없다는 사실은 무료라는 근거가 아닙니다.',
        '비교 목록은 기기에 저장해 두고 다시 방문해 현재 정보로 확인할 수 있습니다. 신청 전에는 은행 공식 링크에서 자격과 요금을 다시 확인하세요. SwitchaBank는 비교 정보를 정리하는 도구이며, 최종 선택은 필요한 서비스와 충족할 조건을 기준으로 판단하세요.'
      ] },
      { id: 'switch-with-a-plan', title: '6. 급여와 자동이체가 옮겨졌는지 확인한 뒤 정리하세요', paragraphs: [
        '급여 입금, 월세, 공과금, 구독료 등 자동으로 들어오고 나가는 거래를 목록으로 만드세요. 새 계좌와 접근 수단을 준비하고, 각 입금·납부 정보를 변경한 다음 실제 거래 내역에서 반영 여부를 확인하세요.',
        '기존 계좌에는 미처리 거래를 감당할 시간과 잔액을 남겨 두세요. 미결제 수표, 이체 소요 시간, 해지 비용을 확인하고 계좌를 닫으세요. 변경 완료 기록을 보관하면 누락된 납부가 생겼을 때 원인을 찾기 쉽습니다.'
      ], sources: ['fcac-switching'] },
      { id: 'finish-the-comparison', title: '7. 생활비 계좌와 저축계좌는 질문부터 나누세요', paragraphs: [
        '체킹계좌 비교는 ‘일상 거래에 얼마를 쓰는가’를 답하는 작업입니다. 저축계좌 비교는 ‘당장 쓰지 않을 돈이 얼마를 벌 수 있는가’를 살펴봅니다. 한 은행에서 둘 다 제공하더라도 확인할 조건은 다릅니다.',
        '결제에 필요한 서비스를 정했다면 아래의 EQ Bank·Tangerine·TD 저축계좌 비교도 읽어 보세요. 기본·프로모션 금리, 거래 비용, 같은 금액과 기간으로 비교하는 방법을 다룹니다. 두 글을 함께 읽으면 현재 은행 이용 방식을 점검할 기준이 더 분명해집니다.'
      ] }
    ],
    example: {
      title: '한 가지 월 요금, 서로 다른 세 가지 계산',
      intro: '한 계좌의 12개월 이용을 가정한 예시입니다. CAD 16.95와 CAD 4,000은 확인한 CIBC 조건이며, 3%는 가상의 저축 금리입니다.',
      headers: ['상황', '계산', '연간 금액'],
      rows: [
        ['12개월 모두 환급·면제 없이 이용', 'CAD 16.95 × 12', 'CAD 203.40'],
        ['3개월은 환급을 못 받고, 나머지 9개월은 환급', 'CAD 16.95 × 3', 'CAD 50.85'],
        ['CAD 4,000을 계속 유지할 때 얻지 못한 이자', 'CAD 4,000 × 3% × 12 / 12', 'CAD 120']
      ],
      note: '각 줄은 별도 상황을 설명하며 합산하지 않습니다. 연 3%는 현재 제안이나 APY가 아닌 가정입니다. 단리 계산으로 복리·세금·수수료·잔액 변동은 제외하며, 이자 차이는 환급용 잔액을 둔 계좌에서 이자가 0이라는 가정을 사용합니다. 수익이나 환급을 보장하지 않습니다.'
    },
    checklist: [
      '평소 한 달의 거래 종류·횟수, ATM 위치, 가장 낮은 일 마감 잔액을 적는다.',
      '기본 수수료와 잔액 환급·고객 프로그램 조건을 두 줄로 구분한다.',
      '실제로 쓸 부가 서비스만 최신 공식 수수료표로 계산한다.',
      'SwitchaBank에서 공개 중인 체킹상품과 상품별 확인일을 비교한다.',
      '은행에서 자격을 확인하고, 급여·자동납부의 이전 완료를 확인한 뒤 기존 계좌를 정리한다.'
    ],
    faq: [
      { question: '캐나다에서 월 수수료 없는 체킹계좌는 무엇인가요?', answer: '확인한 Tangerine과 Simplii 계좌의 기본 월 수수료는 0달러입니다. CIBC Smart Tier 1은 명시된 조건을 충족하면 월 요금 환급을 받을 수 있고 별도 혜택도 적용될 수 있습니다. 월 수수료가 모든 서비스 비용을 포함하지는 않으므로 비교표와 공식 약관을 함께 읽으세요.' },
      { question: '최소 잔액을 유지해 수수료를 면제받는 것이 유리한가요?', answer: '조건을 충족할 수 있는 달의 절약액을 계산한 뒤, 유지 잔액에서 발생할 현실적인 이자 차이와 필요한 서비스의 가치를 비교하세요. 급여일에만 있는 잔액과 한 달 내내 유지할 수 있는 잔액은 다릅니다.' },
      { question: '무제한 거래이면 모든 ATM 인출도 무료인가요?', answer: '대상 ATM 네트워크, 해당 계좌의 수수료표, 운영자의 별도 요금을 확인해야 합니다. 무제한 거래 횟수와 ATM 수수료 환급은 서로 다른 조건입니다.' },
      { question: '이 계좌들을 SwitchaBank에서 비교할 수 있나요?', answer: '캐나다 체킹상품 목록에서 현재 공개 중인 상품을 선택해 비교하세요. 공개 범위는 바뀌며 이 글의 모든 계좌가 등록되어 있는 것은 아닙니다. 비교 가능한 후보의 확인일을 읽고 최종 조건은 은행 공식 페이지에서 확인하세요.' }
    ]
  },
  ja: {
    title: 'カナダの当座口座比較：Tangerine・Simplii・CIBCの手数料と免除条件',
    description: 'Tangerine・Simplii・CIBCのカナダ当座口座を比較。月額手数料、最低残高による返金、ATM費用と年間費用の計算例を整理し、SwitchaBankの商品比較につなげます。',
    intro: '明細にある小さな手数料も、1年分を足すと違って見えます。ただし「無料口座」という言葉だけでは銀行を変更する判断はできません。カナダの3つの当座口座を例に、日々のお金の使い方に合わせて費用と条件を比較する手順を説明します。',
    takeaway: '基本の月額手数料ゼロと、条件を満たした場合の手数料返金を分けて読みましょう。普段の取引と追加サービスを確認し、年間手数料と返金のために維持する資金の価値を計算します。その基準でSwitchaBankの公開中の商品を比較できます。',
    rows: [
      { bank: 'Tangerine', code: 'TANGERINE', name: 'No-fee daily Chequing Account', fee: 'CAD 0', detail: '月額手数料を避けるための最低残高は不要です。日常のデビット決済・請求書払い・事前承認取引は無制限で、Interac e-Transferは無料です。通常以外のサービスは別料金の場合があります。', source: 'tangerine-chequing' },
      { bank: 'Simplii Financial', code: 'SIMPLII', name: 'No Fee Chequing Account', fee: 'CAD 0', detail: 'デビット決済・請求書払い・引き出しは無制限です。CIBCのATMを無料で利用できます。特別な依頼や追加サービスには個別の料金があります。', source: 'simplii-chequing' },
      { bank: 'CIBC', code: 'CIBC', name: 'Smart Account · Tier 1', fee: 'CAD 16.95', detail: 'Interac e-Transferを含む取引が無制限です。1つのSmart Accountで、その月の毎日の終業時残高CAD 4,000を維持すると、最大3つのSmart Accountの月額手数料が返金対象となります。別の対象条件・階層特典も確認してください。', source: 'cibc-smart' }
    ],
    sections: [
      { id: 'start-with-your-statement', title: '1. 入会特典より先に、最近の明細を確認する', paragraphs: [
        '最近1か月の明細で、口座手数料、現金引き出し、支払い、最も低かった残高を確認します。引っ越しや旅行などで普段と違う月なら、通常の2か月も加えてください。繰り返し使うサービスを把握するための作業です。',
        '一度だけの入会特典は別の欄に記録します。現在の公式条件で対象、期限、必要な手続きを確認してから計算しましょう。特典額だけでは2年目の費用がわかりません。この記事はカナダドルの個人当座口座を扱い、事業用・米ドル口座は含みません。'
      ], sources: ['fcac-chequing'] },
      { id: 'free-versus-rebated', title: '2. 月額無料と条件付き返金を分けて読む', paragraphs: [
        'TangerineとSimpliiは基本の月額手数料ゼロから比較を始められます。CIBCのTier 1では基本料金と返金条件を一緒に読みます。給与日には残高があっても、家賃の支払いで減る場合にこの違いが大切です。',
        'CIBCの残高による条件は、月を通した毎日の終業時残高で確認します。月末だけ資金を補充して判断しないでください。階層特典や顧客プログラムでも費用は変わるため、自分の口座に適用される規則を確認しましょう。',
        '比較メモは「返金前の基本料金」と「満たせる条件」の2行にすると、条件付きのゼロを無条件の価格と読み違えにくくなります。'
      ], sources: ['cibc-smart', 'cibc-accounts'] },
      { id: 'check-the-extra-costs', title: '3. 普段のATMと追加サービスの費用を調べる', paragraphs: [
        '日常の取引が無制限でも、特定のサービスは有料の場合があります。確認したTangerineの手数料表では、カナダ国内の他行ATMでの引き出しはCAD 1.50で、ATM運営者の料金が別途かかる場合もあります。例外や他のサービスは最新の料金表で確認してください。',
        '自宅や職場の近くで実際に使うATMを書き出します。銀行振出小切手、追加の小切手帳、紙の明細、当座貸越が必要かも確認しましょう。無料の取引回数だけでは、これらすべての料金はわかりません。',
        'CIBCのATM返金は銀行の階層特典と合わせて読み、すべてのATMが対象と仮定しないでください。普段使うサービスを比較し、他で実際にお金を払っていた特典にだけ別の価値を付けると整理しやすくなります。'
      ], sources: ['tangerine-fees', 'cibc-accounts', 'fcac-atm'] },
      { id: 'worked-example', title: '4. 月額料金と維持する残高を年間額に換算する', paragraphs: [
        '以下は確認したCIBCの月額CAD 16.95と残高基準CAD 4,000を計算に使った例です。1口座で起こり得る状況を仮定しており、実際の請求ではありません。12か月すべて有料、または3か月だけ返金なしという前提は、別の免除が適用されれば変わります。',
        '返金のために維持する資金には、他で得られたはずの利息という機会費用も考えられます。3行目は、ある口座ではその残高の利息がゼロで、別の口座では仮の年3%単利を得るとします。得られなかった利息の比較であり、追加の銀行手数料ではありません。',
        '3行をすべて足さないでください。まず自分の前提に合う料金の状況を選び、現実的な利息の差と必要なサービスの価値を考えます。生活費に使う資金なら、別口座に1年間置けるという前提自体が合わない場合があります。'
      ] },
      { id: 'compare-on-switchabank', title: '5. SwitchaBankで比較候補を絞る', paragraphs: [
        '下のボタンから当座口座一覧を開きます。月額手数料を確認し、詳しく調べたい公開商品の詳細を読みましょう。候補を比較リストに追加すると、異なる日付のスクリーンショットではなく、公開された条件を並べて確認できます。',
        '通貨、含まれる取引と、許容回数を超えた場合の費用を確認します。記載された免除条件は最後まで読み、商品の確認日も見てください。条件が見当たらない場合は銀行に確認します。情報がないことは、無料の証拠ではありません。',
        '比較リストは端末に保存し、再訪時に現在の情報で確認できます。申込前に公式銀行リンクで対象条件と料金を再確認してください。SwitchaBankは比較情報を整理する道具であり、最終的な選択は必要なサービスと満たせる条件に基づいて行いましょう。'
      ] },
      { id: 'switch-with-a-plan', title: '6. 給与・自動支払いの移行を確認してから整理する', paragraphs: [
        '給与、家賃、公共料金、定期購読など、自動で入出金される取引を一覧にします。新口座とアクセス手段を用意し、各支払い・入金情報を変更したら、実際の取引履歴で反映を確認しましょう。',
        '旧口座には未処理の取引に必要な時間と残高を残します。未決済の小切手、送金時間、解約料金を確認してから閉鎖してください。変更完了の記録があると、支払い漏れの原因を追いやすくなります。'
      ], sources: ['fcac-switching'] },
      { id: 'finish-the-comparison', title: '7. 日常の支払いと貯蓄を別の問いとして考える', paragraphs: [
        '当座口座の比較は「日々の取引にいくらかかるか」を調べます。貯蓄口座の比較は「すぐに使わない資金がどれだけ増えるか」を考えます。同じ銀行が両方を提供していても、確認する条件は違います。',
        '支払いに必要なサービスを整理したら、下のEQ Bank・Tangerine・TDの貯蓄口座比較も読んでみてください。基本金利と特典金利、取引費用、同じ金額・期間での比較を説明しています。2つの記事で、現在の銀行の使い方を確認する基準が明確になります。'
      ] }
    ],
    example: {
      title: '1つの月額料金、3つの異なる計算',
      intro: '1口座を12か月使う仮定です。CAD 16.95とCAD 4,000は確認したCIBCの条件、3%は仮の貯蓄金利です。',
      headers: ['状況', '計算', '年間額'],
      rows: [
        ['12か月すべて返金・免除なし', 'CAD 16.95 × 12', 'CAD 203.40'],
        ['3か月は返金なし、残り9か月は返金あり', 'CAD 16.95 × 3', 'CAD 50.85'],
        ['CAD 4,000を維持する場合の得られなかった利息', 'CAD 4,000 × 3% × 12 / 12', 'CAD 120']
      ],
      note: '各行は別の状況で、合算しません。年3%は現在の提案やAPYではなく仮定です。単利計算で複利・税金・料金・残高変動を除き、利息差は返金用の残高を置く口座の利息がゼロという仮定を使います。収益や返金は保証しません。'
    },
    checklist: [
      '通常の月の取引種類・回数、ATMの場所、最低の終業時残高を書く。',
      '基本料金と残高返金・顧客プログラムの条件を2行に分ける。',
      '利用する追加サービスだけ、最新の公式料金表で計算する。',
      'SwitchaBankで公開中の当座口座と商品の確認日を比較する。',
      '銀行で対象条件を確認し、給与・自動支払いの移行を確認してから旧口座を整理する。'
    ],
    faq: [
      { question: 'カナダで月額手数料無料の当座口座はありますか？', answer: '確認したTangerineとSimpliiの口座は基本の月額手数料がゼロです。CIBC SmartのTier 1は条件を満たすと返金され、別の対象特典も適用される場合があります。月額料金だけでは全サービス費用がわからないため、比較表と公式条件を一緒に読んでください。' },
      { question: '最低残高を維持して返金を受ける方がお得ですか？', answer: '条件を満たせる月の節約額を計算し、維持する資金の現実的な利息差と利用サービスの価値を比べます。給与日だけある残高と、月を通して維持できる残高は違います。' },
      { question: '無制限なら、どのATMでも引き出し無料ですか？', answer: '対象ATMネットワーク、口座の手数料表、運営者の追加料金を確認します。無制限の取引回数とATM手数料返金は別の条件です。' },
      { question: 'これらの口座をSwitchaBankで比較できますか？', answer: 'カナダ当座口座一覧で現在公開中の商品を選んでください。掲載範囲は変わり、この記事の全口座が載っているとは限りません。比較可能な候補の確認日を読み、最終条件は銀行の公式ページで確認しましょう。' }
    ]
  }
};
