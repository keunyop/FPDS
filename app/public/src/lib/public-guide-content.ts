import type { PublicLocale } from './public-locale.ts';
import type { GuideSlug } from './public-guides.ts';

type GuideText = { intro: string; sections: { title: string; body: string }[]; comparison: string };
export const GUIDE_SOURCES: Record<GuideSlug, { title: string; href: string }[]> = {
  'base-and-promotional-rates': [{ title: 'FCAC · Savings accounts', href: 'https://www.canada.ca/en/financial-consumer-agency/services/banking/bank-accounts/savings-account.html' }],
  'monthly-fee-waivers': [{ title: 'FCAC · Chequing accounts', href: 'https://www.canada.ca/en/financial-consumer-agency/services/banking/bank-accounts/chequing-accounts.html' }],
  'gic-maturity-and-withdrawals': [{ title: 'FCAC · Guaranteed investment certificates and term deposits', href: 'https://www.canada.ca/en/financial-consumer-agency/services/rights-responsibilities/rights-investing/rights-guaranteed-investment-certificates.html' }],
  'switching-bank-accounts': [{ title: 'FCAC · Transferring your products or services', href: 'https://www.canada.ca/en/financial-consumer-agency/services/banking/transferring-products-services.html' }]
};
const CONTENT: Record<PublicLocale, Record<GuideSlug, GuideText>> = {
  en: {
    'base-and-promotional-rates': {
      intro: 'A headline rate needs a time period and conditions to be useful.',
      sections: [
        { title: 'Read the rate after the offer', body: 'An introductory rate lasts for a limited time. Check the ongoing rate that follows; it may be lower and can change.' },
        { title: 'Check which balance earns it', body: 'Read the offer’s dates and qualifying conditions. Check whether a rate applies to the whole balance or only part of it.' },
        { title: 'Match the basis', body: 'An annual rate is not the return for a short offer. Check how interest is calculated and compounded.' }
      ],
      comparison: 'In the Savings table, read the base rate and offer separately. Our calculator excludes promotional rates and APY; an unavailable result does not mean zero interest.'
    },
    'monthly-fee-waivers': {
      intro: 'A waived monthly fee still has conditions to meet.',
      sections: [
        { title: 'Start with the standard fee', body: 'Record the monthly fee before any waiver. Check the included transactions and additional charges separately.' },
        { title: 'Read the balance rule', body: 'Check the required balance and how long it must be maintained. Some accounts charge the full fee if the balance falls short for even one day.' },
        { title: 'Check other requirements', body: 'A discount may depend on other products held with the bank. Confirm whether you meet the published conditions.' }
      ],
      comparison: 'The Chequing table separates zero monthly fees from conditional waivers. Compare the original waiver text. The calculator does not assume that you qualify for a waiver.'
    },
    'gic-maturity-and-withdrawals': {
      intro: 'For a GIC, the term and access to your money matter alongside the rate.',
      sections: [
        { title: 'Match the maturity', body: 'Check when principal is repaid and when interest is paid. Compare products with the same term and rate basis.' },
        { title: 'Read the early withdrawal terms', body: 'Check whether early withdrawal is allowed, and its effect on interest or charges. Do not infer access from the rate alone.' },
        { title: 'Check what happens at maturity', body: 'Read the renewal instructions, including whether the bank may automatically reinvest your funds.' }
      ],
      comparison: 'The 1-year GIC table separates disclosed withdrawal categories. The calculator uses the selected maturity row and does not model early withdrawal. Missing terms require bank confirmation.'
    },
    'switching-bank-accounts': {
      intro: 'Compare the new account, then plan the move before closing the old one.',
      sections: [
        { title: 'List recurring transactions', body: 'Review statements for direct deposits, automatic payments and outstanding cheques.' },
        { title: 'Confirm the new setup', body: 'Check account access and transfer arrangements. Update deposit and payment details with the relevant providers, and keep enough funds for pending payments.' },
        { title: 'Close only after checking', body: 'Confirm that recurring transactions have moved. Ask the old bank about closure steps and fees, and retain confirmation.' }
      ],
      comparison: 'Start with the Chequing table for everyday banking, then select accounts to compare. This checklist covers ordinary chequing and savings accounts; registered-plan transfers need separate checks with the provider.'
    }
  },
  ko: {
    'base-and-promotional-rates': {
      intro: '표시 금리는 적용 기간과 조건을 함께 읽어야 합니다.',
      sections: [
        { title: '혜택 종료 후 금리', body: '프로모션 금리는 정해진 기간에 적용됩니다. 이후 적용되는 기본 금리는 더 낮을 수 있고 변경될 수 있습니다.' },
        { title: '적용되는 잔액', body: '혜택 기간과 적용 조건을 읽으세요. 전체 잔액에 적용되는지, 일부 금액에만 적용되는지도 확인합니다.' },
        { title: '같은 기준으로 비교', body: '연 금리는 짧은 혜택 기간의 수익률과 다릅니다. 이자 계산 방식과 복리 주기를 확인하세요.' }
      ],
      comparison: 'Savings 비교 표에서 기본 금리와 혜택을 구분해 보세요. 계산기는 프로모션 금리와 APY를 계산하지 않습니다. 계산 불가는 이자가 0이라는 뜻이 아닙니다.'
    },
    'monthly-fee-waivers': {
      intro: '월 수수료 면제에는 충족해야 할 조건이 있습니다.',
      sections: [
        { title: '기본 수수료부터 확인', body: '면제 전 월 수수료를 확인하세요. 포함된 거래 횟수와 추가 비용은 따로 살펴봅니다.' },
        { title: '잔액 유지 기준', body: '필요한 잔액과 유지 기간을 읽으세요. 하루라도 기준에 미달하면 월 수수료 전액이 부과되는 계좌도 있습니다.' },
        { title: '다른 요건도 확인', body: '같은 은행의 다른 상품 보유 여부에 따라 할인이 달라질 수 있습니다. 공개된 조건을 충족하는지 확인하세요.' }
      ],
      comparison: 'Chequing 비교 표는 월 수수료 0인 상품과 조건부 면제를 구분합니다. 면제 조건 원문을 비교하세요. 계산기는 면제 자격을 충족한다고 가정하지 않습니다.'
    },
    'gic-maturity-and-withdrawals': {
      intro: 'GIC는 금리와 함께 만기와 자금 인출 가능 여부를 비교해야 합니다.',
      sections: [
        { title: '만기를 맞춰 비교', body: '원금 반환일과 이자 지급 시점을 확인하세요. 같은 만기와 금리 기준의 상품을 비교합니다.' },
        { title: '중도 인출 조건', body: '만기 전 인출이 가능한지, 이자나 비용에 어떤 영향이 있는지 읽으세요. 금리만으로 인출 가능 여부를 판단하지 않습니다.' },
        { title: '만기 후 처리', body: '자동 재예치 여부를 포함해 만기 시 처리 방법을 확인하세요.' }
      ],
      comparison: '1년 GIC 비교 표는 공개된 인출 조건별로 구분합니다. 계산기는 선택한 만기 행을 사용하며 중도 인출을 반영하지 않습니다. 누락된 조건은 은행에 확인하세요.'
    },
    'switching-bank-accounts': {
      intro: '새 계좌를 비교하고 이전을 준비한 뒤 기존 계좌를 해지하세요.',
      sections: [
        { title: '정기 거래 목록', body: '명세서에서 급여 등 자동 입금, 자동 납부, 아직 결제되지 않은 수표를 확인하세요.' },
        { title: '새 계좌 설정 확인', body: '계좌 이용과 자금 이체 방법을 확인하세요. 관련 기관에 입출금 계좌 변경을 알리고 예정된 결제에 필요한 잔액을 유지합니다.' },
        { title: '해지 전 최종 확인', body: '정기 거래가 이전됐는지 확인하세요. 기존 은행에 해지 절차와 비용을 확인하고 해지 확인서를 보관합니다.' }
      ],
      comparison: '일상 거래용 계좌는 Chequing 표에서 시작해 상품을 선택하고 비교하세요. 이 목록은 일반 Chequing·Savings 계좌용입니다. 등록형 절세 계좌 이전은 해당 기관에 별도로 확인해야 합니다.'
    }
  },
  ja: {
    'base-and-promotional-rates': {
      intro: '表示金利は、適用期間と条件を合わせて読みましょう。',
      sections: [
        { title: '特典終了後の金利', body: 'キャンペーン金利には適用期間があります。その後の基本金利は低くなる場合があり、変更されることもあります。' },
        { title: '対象となる残高', body: '特典の期間と適用条件を読みましょう。残高全体に適用されるか、一部だけに適用されるかも確認します。' },
        { title: '同じ基準で比較', body: '年利は短い特典期間の収益率とは異なります。利息の計算方法と複利の頻度を確認してください。' }
      ],
      comparison: 'Savings比較表では基本金利と特典を分けて確認できます。計算ツールはキャンペーン金利とAPYを扱いません。計算できない場合も、利息がゼロという意味ではありません。'
    },
    'monthly-fee-waivers': {
      intro: '月額手数料の免除には、満たすべき条件があります。',
      sections: [
        { title: '通常の手数料を確認', body: '免除前の月額手数料を確認しましょう。含まれる取引回数と追加料金も別に確認します。' },
        { title: '残高の維持条件', body: '必要な残高と維持期間を読みましょう。1日でも基準を下回ると月額手数料が全額かかる口座もあります。' },
        { title: 'その他の条件', body: '同じ銀行の別の商品を利用していることが割引の条件になる場合があります。公開された条件を満たすか確認してください。' }
      ],
      comparison: 'Chequing比較表は月額手数料ゼロと条件付き免除を分けています。免除条件は原文で比較できます。計算ツールは免除条件を満たすとは仮定しません。'
    },
    'gic-maturity-and-withdrawals': {
      intro: 'GICは金利とともに、満期と資金を引き出せる条件を比較します。',
      sections: [
        { title: '満期をそろえる', body: '元本の返還日と利息の支払時期を確認しましょう。同じ期間と金利基準の商品を比較します。' },
        { title: '中途解約の条件', body: '満期前の引き出しが可能か、利息や費用にどう影響するかを確認してください。金利だけで判断しないようにしましょう。' },
        { title: '満期後の扱い', body: '自動再投資の有無を含め、満期時の手続きを確認してください。' }
      ],
      comparison: '1年GICの比較表は公開された引き出し条件ごとに分けています。計算ツールは選んだ満期の行を使い、中途解約は反映しません。不明な条件は銀行で確認してください。'
    },
    'switching-bank-accounts': {
      intro: '新しい口座を比較して移行を準備し、その後に旧口座を解約しましょう。',
      sections: [
        { title: '定期的な取引を整理', body: '明細から給与などの自動入金、口座引き落とし、未決済の小切手を確認してください。' },
        { title: '新口座の設定を確認', body: '口座の利用と資金移動の方法を確認しましょう。関係する事業者に口座変更を伝え、支払い予定に必要な残高を確保します。' },
        { title: '解約前に最終確認', body: '定期的な取引の移行を確認しましょう。旧銀行に解約手続きと費用を確認し、解約の記録を保管してください。' }
      ],
      comparison: '日常の取引用口座はChequing表から商品を選んで比較できます。このチェックリストは通常のChequing・Savings口座向けです。税制優遇の登録口座の移管は、金融機関に別途確認してください。'
    }
  }
};
export function guideContent(slug: GuideSlug, locale: string): GuideText {
  return CONTENT[locale === 'ko' || locale === 'ja' ? locale : 'en'][slug];
}
