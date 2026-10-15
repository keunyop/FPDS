import type { BlogContent } from './public-blog-content.ts';
import type { EditorialLocale } from './public-locale.ts';

export const CA_CARD_REWARDS_SOURCES = [
  {
    "id": "ca-card-tangerine",
    "title": "Tangerine — Money-Back Credit Card and offer terms",
    "href": "https://www.tangerine.ca/en/personal/spend/credit-cards/money-back-credit-card"
  },
  {
    "id": "ca-card-fcac",
    "title": "FCAC — How credit cards work",
    "href": "https://www.canada.ca/en/financial-consumer-agency/services/credit-cards/credit-card-work.html"
  }
] as const;

export const US_CARD_REWARDS_SOURCES = [
  {
    "id": "us-card-chase",
    "title": "Chase — Freedom Unlimited and offer details",
    "href": "https://creditcards.chase.com/cash-back-credit-cards/freedom/unlimited"
  },
  {
    "id": "us-card-wells",
    "title": "Wells Fargo — Active Cash and reward exclusions",
    "href": "https://creditcards.wellsfargo.com/active-cash-credit-card/"
  },
  {
    "id": "us-card-cfpb",
    "title": "CFPB — Credit card grace periods",
    "href": "https://www.consumerfinance.gov/ask-cfpb/what-is-a-grace-period-for-a-credit-card-en-47/"
  }
] as const;

export const CA_CARD_REWARDS_CONTENT: Record<EditorialLocale, BlogContent> = {
  "en": {
    "title": "Cash back and welcome bonuses: a Canadian credit card guide",
    "description": "Two ways to get value from Canadian credit cards: everyday cash back and welcome offers. Check Tangerine categories, bonus deadlines, exclusions and costs.",
    "intro": "Use spending you already planned to earn cash back, then check whether a welcome offer adds value. Here are two practical approaches for Canada, with one verified card example.",
    "takeaway": "Rewards are savings on eligible spending. Keep regular cash back, a one-time bonus and borrowing costs on separate lines.",
    "tableHeaders": [
      "Card example",
      "Annual fee",
      "Regular rewards"
    ],
    "rows": [
      {
        "bank": "Tangerine",
        "code": "TANGERINE",
        "name": "Money-Back Credit Card",
        "fee": "CAD 0",
        "detail": "2% in two chosen categories; a third when rewards go to a Tangerine Savings Account. 0.5% on other eligible net purchases. Rewards are paid monthly.",
        "source": "ca-card-tangerine"
      }
    ],
    "sections": [
      {
        "id": "everyday-cashback",
        "title": "1. Put everyday spending in the right categories",
        "paragraphs": [
          "Start with groceries, transport and bills already in your budget. Tangerine’s 2% applies to your selected categories, not every purchase. Merchant classification matters; check the posted rewards before treating a shop as eligible."
        ],
        "sources": [
          "ca-card-tangerine"
        ]
      },
      {
        "id": "welcome-offer",
        "title": "2. Fit the welcome offer to your existing budget",
        "paragraphs": [
          "Offer checked October 15, 2026: new Tangerine Credit Card account holders can earn an extra 10%, up to CAD 100, on the first CAD 1,000 in eligible net purchases posted within 60 days of activation. Apply by November 30, 2026 and activate within 45 days of approval. This bonus is on top of regular rewards.",
          "One offer per eligible client. The account must be open and in good standing at payout; the bonus is credited 1–2 statement cycles after the 60-day period. Offers can change. Check approval requirements and the current terms before applying."
        ],
        "sources": [
          "ca-card-tangerine"
        ]
      },
      {
        "id": "excluded-spending",
        "title": "Gift cards and cash-like transactions need a separate check",
        "paragraphs": [
          "Do not assume a gift-card purchase or resale will qualify. Tangerine excludes cash advances, balance transfers and cash-like transactions from rewards and this offer’s eligible spending. FCAC notes that cash-like transactions may attract fees and interest from the transaction date. Read the exact transaction rules first."
        ],
        "sources": [
          "ca-card-tangerine",
          "ca-card-fcac"
        ]
      },
      {
        "id": "worked-example",
        "title": "Compare the first year with the year after",
        "paragraphs": [
          "Regular cash back + a separate welcome bonus − annual fees − interest − other charges = value retained. Keep the statement balance paid in full by the due date under your card’s purchase grace-period terms. Minimum payments alone do not prevent interest."
        ],
        "sources": [
          "ca-card-fcac"
        ]
      }
    ],
    "checklist": [
      "Confirm the category, eligible net spending and bonus deadline.",
      "Use planned purchases; record when the bonus is paid.",
      "Compare the next year without a new bonus, and deduct actual costs."
    ],
    "faq": [
      {
        "question": "Does the third Tangerine 2% category come automatically?",
        "answer": "It requires choosing a Tangerine Savings Account as the rewards destination. Two categories apply when rewards go to the credit card account."
      },
      {
        "question": "Does paying the minimum preserve the cash back advantage?",
        "answer": "Minimum payments can leave a balance that attracts interest. Check the full statement balance and the purchase grace-period conditions."
      },
      {
        "question": "Can I repeat the welcome offer every month?",
        "answer": "The checked Tangerine offer is limited to one per eligible client and new credit card account holders. Do not assume repeat eligibility."
      }
    ],
    "infographic": {
      "title": "Keep the value in three steps",
      "steps": [
        {
          "title": "Planned spending",
          "text": "Earn on purchases you already need."
        },
        {
          "title": "Eligible bonus",
          "text": "Check exclusions and the exact deadline."
        },
        {
          "title": "Full payment",
          "text": "Protect your purchase grace period."
        }
      ]
    },
    "example": {
      "title": "A one-time bonus changes the first year",
      "intro": "Fictional scenario: CAD 12,000 in eligible purchases each year, 2% cash back and a separate CAD 100 bonus paid in year one.",
      "headers": [
        "Period",
        "Calculation",
        "Rewards"
      ],
      "rows": [
        [
          "First year: bonus included",
          "CAD 12,000 × 2% + CAD 100",
          "CAD 340"
        ],
        [
          "Next year: no new bonus",
          "CAD 12,000 × 2%",
          "CAD 240"
        ]
      ],
      "chart": {
        "values": [
          340,
          240
        ],
        "difference": "One-time difference: CAD 100"
      },
      "note": "Method illustration, not either card’s quoted return. Assumes all bonus conditions are met, no returns or extra spending, and zero annual fee, interest and other charges. Rates and spending stay unchanged; the bonus is added only once and is separate from regular rewards. Deduct actual costs."
    },
    "inspiration": {
      "href": "https://www.banksalad.com/articles/신용카드로-돈벌기-집에서-돈버는-방법",
      "label": "Topic inspiration: Banksalad’s card-rewards explainer"
    }
  },
  "ko": {
    "title": "캐나다 카드테크: 캐시백·웰컴 보너스 받는 두 가지 방법",
    "description": "캐나다 신용카드로 혜택 받는 두 가지 방법. 일상 캐시백과 웰컴 보너스를 Tangerine 사례로 살펴보고 적립 카테고리, 신청 기한, 제외 거래와 실제 비용을 확인하세요.",
    "intro": "원래 쓸 생활비로 캐시백을 받고, 조건이 맞는 웰컴 보너스를 더하세요. 캐나다에서 활용할 두 가지 방법을 실제 카드 사례와 함께 정리했습니다.",
    "takeaway": "카드 혜택은 인정되는 소비에서 돌려받는 금액입니다. 기본 캐시백, 일회성 보너스, 빌리는 비용을 따로 계산하세요.",
    "tableHeaders": [
      "카드 사례",
      "연회비",
      "기본 적립 조건"
    ],
    "rows": [
      {
        "bank": "Tangerine",
        "code": "TANGERINE",
        "name": "Money-Back Credit Card",
        "fee": "CAD 0",
        "detail": "선택한 두 카테고리 2%. 캐시백을 Tangerine Savings Account로 받으면 세 번째 카테고리가 추가됩니다. 그 외 인정되는 순구매액은 0.5%이며 매월 지급됩니다.",
        "source": "ca-card-tangerine"
      }
    ],
    "sections": [
      {
        "id": "everyday-cashback",
        "title": "1. 생활비를 적립 카테고리에 맞추세요",
        "paragraphs": [
          "식료품·교통·공과금 등 이미 예산에 잡힌 지출부터 살펴보세요. Tangerine의 2%는 모든 결제가 아닌 선택한 카테고리에 적용됩니다. 가맹점 분류가 중요하므로 실제 적립 내역을 확인하세요."
        ],
        "sources": [
          "ca-card-tangerine"
        ]
      },
      {
        "id": "welcome-offer",
        "title": "2. 원래 쓸 돈으로 웰컴 보너스를 채우세요",
        "paragraphs": [
          "2026년 10월 15일 확인한 Tangerine 제안은 신규 신용카드 계좌 고객에게 활성화 후 60일 안에 반영된 인정 순구매액 첫 CAD 1,000까지 추가 10%, 최대 CAD 100을 제공합니다. 2026년 11월 30일까지 신청하고 승인 후 45일 안에 활성화해야 합니다. 기본 적립에 더해지는 보너스입니다.",
          "자격을 갖춘 고객당 1회이며, 지급 시 계좌가 열려 있고 정상 상태여야 합니다. 60일 프로모션이 끝난 뒤 명세 1~2주기 안에 지급됩니다. 제안은 바뀔 수 있으므로 신청 전 승인 요건과 최신 약관을 확인하세요."
        ],
        "sources": [
          "ca-card-tangerine"
        ]
      },
      {
        "id": "excluded-spending",
        "title": "상품권·현금성 거래는 별도로 확인하세요",
        "paragraphs": [
          "상품권 구매나 재판매가 적립 조건에 맞는다고 가정하지 마세요. Tangerine은 현금서비스·잔액 이체·현금성 거래를 적립과 해당 프로모션의 인정 지출에서 제외합니다. FCAC는 현금성 거래에 거래일부터 이자와 수수료가 붙을 수 있다고 안내합니다. 거래별 약관부터 확인하세요."
        ],
        "sources": [
          "ca-card-tangerine",
          "ca-card-fcac"
        ]
      },
      {
        "id": "worked-example",
        "title": "첫해와 그다음 해를 나눠 계산하세요",
        "paragraphs": [
          "기본 캐시백 + 별도 웰컴 보너스 − 연회비 − 이자 − 기타 비용 = 남는 혜택입니다. 카드의 구매 유예기간 조건에 맞춰 결제일까지 명세 잔액 전액을 갚으세요. 최소 금액만 납부하면 이자가 생길 수 있습니다."
        ],
        "sources": [
          "ca-card-fcac"
        ]
      }
    ],
    "checklist": [
      "적립 카테고리·인정 순구매액·보너스 기한을 확인합니다.",
      "계획한 지출로 채우고 보너스 지급 시점을 기록합니다.",
      "새 보너스가 없는 다음 해도 비교하고 실제 비용을 뺍니다."
    ],
    "faq": [
      {
        "question": "Tangerine의 세 번째 2% 카테고리는 자동으로 생기나요?",
        "answer": "캐시백 수령 계좌를 Tangerine Savings Account로 선택해야 합니다. 신용카드 계좌로 받으면 두 카테고리가 적용됩니다."
      },
      {
        "question": "최소 결제액만 내도 캐시백의 이점이 유지되나요?",
        "answer": "최소 금액만 내면 잔액에 이자가 붙을 수 있습니다. 명세 잔액 전액과 구매 유예기간 조건을 확인하세요."
      },
      {
        "question": "웰컴 보너스를 매달 반복해서 받을 수 있나요?",
        "answer": "확인한 Tangerine 제안은 신규 신용카드 계좌 고객 중 자격을 갖춘 고객당 1회입니다. 반복 참여가 가능하다고 가정하지 마세요."
      }
    ],
    "infographic": {
      "title": "혜택을 남기는 세 단계",
      "steps": [
        {
          "title": "계획한 소비",
          "text": "원래 필요한 구매에서 적립합니다."
        },
        {
          "title": "보너스 자격",
          "text": "제외 거래와 정확한 기한을 확인합니다."
        },
        {
          "title": "전액 결제",
          "text": "구매 유예기간 조건을 지킵니다."
        }
      ]
    },
    "example": {
      "title": "일회성 보너스가 첫해 숫자를 바꿉니다",
      "intro": "가상 조건: 매년 인정 구매 CAD 12,000, 캐시백 2%, 첫해 지급되는 별도 보너스 CAD 100입니다.",
      "headers": [
        "기간",
        "계산",
        "혜택"
      ],
      "rows": [
        [
          "첫해: 보너스 포함",
          "CAD 12,000 × 2% + CAD 100",
          "CAD 340"
        ],
        [
          "다음 해: 새 보너스 없음",
          "CAD 12,000 × 2%",
          "CAD 240"
        ]
      ],
      "chart": {
        "values": [
          340,
          240
        ],
        "difference": "일회성 차이: CAD 100"
      },
      "note": "계산 방법을 위한 가상 예시이며 위 카드의 수익 견적이 아닙니다. 보너스 조건 충족, 반품·추가 소비 없음, 연회비·이자·기타 비용 0을 가정합니다. 적립률과 소비액은 같고 기본 적립과 별개인 보너스는 한 번만 더합니다. 실제 비용은 차감하세요."
    },
    "inspiration": {
      "href": "https://www.banksalad.com/articles/신용카드로-돈벌기-집에서-돈버는-방법",
      "label": "주제 참고: 뱅크샐러드 카드테크 글"
    }
  },
  "ja": {
    "title": "カナダのカード活用術：キャッシュバックと入会特典の二つの方法",
    "description": "カナダのクレジットカードで日常の還元と入会特典を活用。Tangerineの分類、申込期限、対象外取引と費用を図とともに確認できます。",
    "intro": "予定していた生活費で還元を受け、条件に合う入会特典を加えましょう。カナダで使える二つの方法を、確認済みのカード例で紹介します。",
    "takeaway": "特典は対象の支出から戻る金額です。通常還元、一度限りの特典、借入費用を分けて計算しましょう。",
    "tableHeaders": [
      "カード例",
      "年会費",
      "通常還元の条件"
    ],
    "rows": [
      {
        "bank": "Tangerine",
        "code": "TANGERINE",
        "name": "Money-Back Credit Card",
        "fee": "CAD 0",
        "detail": "選択した二つのカテゴリーで2%。還元の受取先をTangerine Savings Accountにすると三つ目が追加されます。他の対象純購入額は0.5%で、毎月支払われます。",
        "source": "ca-card-tangerine"
      }
    ],
    "sections": [
      {
        "id": "everyday-cashback",
        "title": "1. 生活費を還元カテゴリーに合わせる",
        "paragraphs": [
          "食料品・交通・公共料金など予算にある支出から確認します。Tangerineの2%は全決済ではなく、選択したカテゴリーが対象です。加盟店の分類が影響するため、実際の還元明細を確認しましょう。"
        ],
        "sources": [
          "ca-card-tangerine"
        ]
      },
      {
        "id": "welcome-offer",
        "title": "2. 予定した支出で入会特典を満たす",
        "paragraphs": [
          "2026年10月15日に確認したTangerineの特典は、新規カード口座の対象者に、利用開始後60日以内に計上された対象純購入額の最初のCAD 1,000まで追加10%、最大CAD 100を提供します。2026年11月30日までに申し込み、承認後45日以内に利用開始が必要です。通常還元に加わる特典です。",
          "対象者1人につき1回。支払い時に口座が開設中で正常な状態である必要があり、60日の特典期間後、明細1〜2サイクル以内に付与されます。条件は変わり得るため、申込前に審査要件と最新規約を確認してください。"
        ],
        "sources": [
          "ca-card-tangerine"
        ]
      },
      {
        "id": "excluded-spending",
        "title": "ギフトカード・現金同等取引は別に確認",
        "paragraphs": [
          "ギフトカードの購入や転売が対象になるとは限りません。Tangerineはキャッシング・残高移行・現金同等取引を通常還元とこの特典の対象支出から除外します。FCACは現金同等取引に取引日から利息や手数料が発生し得ると説明しています。取引ごとの規約を確認しましょう。"
        ],
        "sources": [
          "ca-card-tangerine",
          "ca-card-fcac"
        ]
      },
      {
        "id": "worked-example",
        "title": "初年度と翌年を分けて計算する",
        "paragraphs": [
          "通常還元 + 別途の入会特典 − 年会費 − 利息 − その他費用 = 手元に残る特典です。購入の猶予期間の条件に従い、期日までに明細残高を全額支払いましょう。最低額だけでは利息が発生し得ます。"
        ],
        "sources": [
          "ca-card-fcac"
        ]
      }
    ],
    "checklist": [
      "カテゴリー・対象純購入額・特典期限を確認する。",
      "予定した支出で満たし、付与時期を記録する。",
      "新しい特典のない翌年も比較し、実際の費用を差し引く。"
    ],
    "faq": [
      {
        "question": "Tangerineの三つ目の2%カテゴリーは自動で追加されますか？",
        "answer": "還元の受取先をTangerine Savings Accountにする必要があります。カード口座への還元では二つが対象です。"
      },
      {
        "question": "最低支払額だけでも還元の利点は残りますか？",
        "answer": "残った残高に利息が発生し得ます。明細残高全額と購入の猶予期間の条件を確認してください。"
      },
      {
        "question": "入会特典を毎月繰り返し受けられますか？",
        "answer": "確認したTangerineの特典は新規カード口座の対象者1人につき1回です。繰り返し対象になるとは限りません。"
      }
    ],
    "infographic": {
      "title": "特典を残す三つの手順",
      "steps": [
        {
          "title": "予定した支出",
          "text": "もともと必要な購入で還元。"
        },
        {
          "title": "特典の条件",
          "text": "対象外取引と正確な期限を確認。"
        },
        {
          "title": "全額支払い",
          "text": "購入の猶予期間の条件を守る。"
        }
      ]
    },
    "example": {
      "title": "一度限りの特典で初年度の数字は変わる",
      "intro": "仮の条件：毎年の対象購入CAD 12,000、還元2%、初年度に支払われる別途の特典CAD 100。",
      "headers": [
        "期間",
        "計算",
        "特典"
      ],
      "rows": [
        [
          "初年度：特典あり",
          "CAD 12,000 × 2% + CAD 100",
          "CAD 340"
        ],
        [
          "翌年：新たな特典なし",
          "CAD 12,000 × 2%",
          "CAD 240"
        ]
      ],
      "chart": {
        "values": [
          340,
          240
        ],
        "difference": "一度限りの差：CAD 100"
      },
      "note": "計算方法の仮定で、上記カードの還元見積もりではありません。特典条件を満たし、返品・追加支出なし、年会費・利息・その他費用ゼロを想定。還元率と支出は同じで、通常還元と別の特典は一度だけ加えます。実費は差し引いてください。"
    },
    "inspiration": {
      "href": "https://www.banksalad.com/articles/신용카드로-돈벌기-집에서-돈버는-방법",
      "label": "テーマ参考：Banksaladのカード特典記事"
    }
  }
};

export const US_CARD_REWARDS_CONTENT: Record<EditorialLocale, BlogContent> = {
  "en": {
    "title": "US credit card rewards: cash back and welcome bonuses",
    "description": "Get more from US credit card rewards through everyday cash back and welcome bonuses. Compare Chase and Wells Fargo examples, eligible spending and net value.",
    "intro": "Cash back on planned spending and a welcome bonus are two ways to make a US credit card work harder. The useful number is what remains after fees and interest.",
    "takeaway": "Choose rewards for purchases already in your budget. Verify bonus eligibility before applying, and compare ongoing value without a new bonus.",
    "tableHeaders": [
      "Card example",
      "Annual fee",
      "Regular rewards"
    ],
    "rows": [
      {
        "bank": "Chase",
        "code": "JCBN",
        "name": "Freedom Unlimited",
        "fee": "USD 0",
        "detail": "1.5% on other eligible purchases; 3% on dining and drugstores; 5% on travel purchased through Chase Travel. Category rules apply.",
        "source": "us-card-chase"
      },
      {
        "bank": "Wells Fargo",
        "code": "WFBN",
        "name": "Active Cash",
        "fee": "USD 0",
        "detail": "Unlimited 2% cash rewards on eligible net purchases, meaning purchases less returns and credits. Excluded transactions earn no rewards.",
        "source": "us-card-wells"
      }
    ],
    "sections": [
      {
        "id": "everyday-cashback",
        "title": "1. Match everyday purchases to the earn rate",
        "paragraphs": [
          "A flat rate can be easier to track; category rewards may pay more on qualifying spending. Compare your actual mix of purchases. For Chase, 3% dining is the total rate, not an extra 3% added to the 1.5% base. Redeem at the cash value you actually receive."
        ],
        "sources": [
          "us-card-chase",
          "us-card-wells"
        ]
      },
      {
        "id": "welcome-offer",
        "title": "2. Meet a welcome bonus with spending already planned",
        "paragraphs": [
          "Offer checked October 15, 2026: Chase Freedom Unlimited offers 20,000 bonus points redeemable for USD 200 cash back after USD 500 in eligible purchases in the first 3 months from account opening. It excludes current holders of this card and previous holders who received its new-cardmember bonus within the past 24 months.",
          "The account must be open and not in default at fulfillment. Allow 6–8 weeks after qualifying for points to post. Offers vary by application channel and can change. Check the actual offer and approval terms before applying."
        ],
        "sources": [
          "us-card-chase"
        ]
      },
      {
        "id": "excluded-spending",
        "title": "Check gift-card and cash-equivalent exclusions",
        "paragraphs": [
          "Do not treat gift-card resale as guaranteed qualifying spend. Wells Fargo Active Cash explicitly excludes pre-paid gift cards and other cash equivalents from both rewards and its welcome-offer spending. Chase also excludes cash-like transactions, cash advances and balance transfers. Buying more than you need can cost more than the bonus."
        ],
        "sources": [
          "us-card-wells",
          "us-card-chase"
        ]
      },
      {
        "id": "worked-example",
        "title": "Separate the first-year boost from ongoing value",
        "paragraphs": [
          "Regular rewards + a separate welcome bonus − annual fees − interest − other charges = value retained. When you qualify for a purchase grace period, paying the full statement balance by the due date can avoid purchase interest. Cash advances generally do not get that grace period."
        ],
        "sources": [
          "us-card-cfpb"
        ]
      }
    ],
    "checklist": [
      "Read the current offer, application channel and prior-cardholder restrictions.",
      "Count eligible net purchases that post within the exact deadline.",
      "Compare the next year without a bonus; subtract fees, interest and unnecessary spending."
    ],
    "faq": [
      {
        "question": "Is a USD 200 bonus available whenever I reopen the Chase card?",
        "answer": "No. The checked offer excludes current cardholders and previous holders who received this card’s new-cardmember bonus within the past 24 months. Approval and other offer conditions still apply."
      },
      {
        "question": "Do pre-paid gift cards count toward Active Cash rewards?",
        "answer": "The checked Wells Fargo terms exclude pre-paid gift cards and other cash equivalents from rewards and welcome-offer qualifying purchases."
      },
      {
        "question": "Does a cash back statement credit replace my required payment?",
        "answer": "Follow the payment amount and due date on your statement. A reward redemption is not a reason to skip a required payment; check your issuer’s payment rules."
      }
    ],
    "infographic": {
      "title": "Keep the value in three steps",
      "steps": [
        {
          "title": "Planned spending",
          "text": "Earn on purchases you already need."
        },
        {
          "title": "Eligible bonus",
          "text": "Check exclusions and the exact deadline."
        },
        {
          "title": "Full payment",
          "text": "Protect your purchase grace period."
        }
      ]
    },
    "example": {
      "title": "A one-time bonus changes the first year",
      "intro": "Fictional scenario: USD 12,000 in eligible purchases each year, 2% cash back and a separate USD 200 bonus paid in year one.",
      "headers": [
        "Period",
        "Calculation",
        "Rewards"
      ],
      "rows": [
        [
          "First year: bonus included",
          "USD 12,000 × 2% + USD 200",
          "USD 440"
        ],
        [
          "Next year: no new bonus",
          "USD 12,000 × 2%",
          "USD 240"
        ]
      ],
      "chart": {
        "values": [
          440,
          240
        ],
        "difference": "One-time difference: USD 200"
      },
      "note": "Method illustration, not either card’s quoted return. Assumes all bonus conditions are met, no returns or extra spending, and zero annual fee, interest and other charges. Rates and spending stay unchanged; the bonus is added only once and is separate from regular rewards. Deduct actual costs."
    },
    "inspiration": {
      "href": "https://www.banksalad.com/articles/신용카드로-돈벌기-집에서-돈버는-방법",
      "label": "Topic inspiration: Banksalad’s card-rewards explainer"
    }
  },
  "ko": {
    "title": "미국 카드테크: 캐시백·가입 보너스 제대로 받는 법",
    "description": "미국 신용카드 혜택을 일상 캐시백과 가입 보너스로 나눠 비교하세요. Chase·Wells Fargo 사례, 인정 지출, 기존 고객 제한과 비용 차감 후 혜택을 확인합니다.",
    "intro": "원래 계획한 소비의 캐시백과 가입 보너스는 미국 신용카드를 활용하는 두 가지 방법입니다. 비교할 숫자는 수수료와 이자를 빼고 남는 혜택입니다.",
    "takeaway": "예산에 있는 소비에 맞는 적립을 고르세요. 신청 전 보너스 자격을 확인하고, 새 보너스가 없는 다음 해도 비교합니다.",
    "tableHeaders": [
      "카드 사례",
      "연회비",
      "기본 적립 조건"
    ],
    "rows": [
      {
        "bank": "Chase",
        "code": "JCBN",
        "name": "Freedom Unlimited",
        "fee": "USD 0",
        "detail": "그 외 인정 구매 1.5%, 식당·약국 3%, Chase Travel을 통한 여행 구매 5%. 카테고리별 조건이 적용됩니다.",
        "source": "us-card-chase"
      },
      {
        "bank": "Wells Fargo",
        "code": "WFBN",
        "name": "Active Cash",
        "fee": "USD 0",
        "detail": "반품·환불 등을 뺀 인정 순구매액에 한도 없는 2% cash rewards. 제외 거래에는 적립되지 않습니다.",
        "source": "us-card-wells"
      }
    ],
    "sections": [
      {
        "id": "everyday-cashback",
        "title": "1. 생활비와 적립률을 맞추세요",
        "paragraphs": [
          "단일 적립률은 관리하기 쉽고, 카테고리 적립은 해당 소비에서 더 높을 수 있습니다. 실제 지출 비중으로 비교하세요. Chase의 식당 3%는 기본 1.5%에 추가 3%를 더하는 것이 아닌 총 적립률입니다. 실제로 교환받는 현금 가치도 확인하세요."
        ],
        "sources": [
          "us-card-chase",
          "us-card-wells"
        ]
      },
      {
        "id": "welcome-offer",
        "title": "2. 계획한 지출로 가입 보너스를 채우세요",
        "paragraphs": [
          "2026년 10월 15일 확인한 Chase Freedom Unlimited 제안은 계좌 개설 후 첫 3개월에 인정 구매 USD 500을 채우면 USD 200 캐시백으로 교환할 수 있는 20,000 보너스 포인트를 제공합니다. 현재 이 카드 보유자나, 과거 보유자 중 지난 24개월 안에 해당 신규 보너스를 받은 고객은 제외됩니다.",
          "지급 시 계좌가 열려 있고 채무불이행 상태가 아니어야 하며, 조건 충족 후 포인트 반영까지 6~8주가 걸릴 수 있습니다. 신청 경로별 제안이 다르거나 변경될 수 있으므로 실제 제안과 승인 요건을 확인하세요."
        ],
        "sources": [
          "us-card-chase"
        ]
      },
      {
        "id": "excluded-spending",
        "title": "상품권·현금성 거래의 제외 조건을 보세요",
        "paragraphs": [
          "상품권을 되팔아도 인정 지출이 된다고 가정하지 마세요. Wells Fargo Active Cash는 선불 상품권과 기타 현금성 거래를 기본 적립과 가입 보너스 인정 구매에서 명시적으로 제외합니다. Chase도 현금성 거래·현금서비스·잔액 이체를 제외합니다. 필요 없는 소비를 늘리면 보너스보다 비용이 커질 수 있습니다."
        ],
        "sources": [
          "us-card-wells",
          "us-card-chase"
        ]
      },
      {
        "id": "worked-example",
        "title": "첫해 보너스와 지속 혜택을 분리하세요",
        "paragraphs": [
          "기본 적립 + 별도 가입 보너스 − 연회비 − 이자 − 기타 비용 = 남는 혜택입니다. 구매 유예기간을 적용받는 조건이라면 결제일까지 명세 잔액 전액을 갚아 구매 이자를 피할 수 있습니다. 현금서비스에는 일반적으로 이 유예기간이 없습니다."
        ],
        "sources": [
          "us-card-cfpb"
        ]
      }
    ],
    "checklist": [
      "최신 제안·신청 경로·과거 카드 보유자 제한을 읽습니다.",
      "정확한 기한 안에 반영되는 인정 순구매액을 셉니다.",
      "보너스 없는 다음 해도 비교하고 수수료·이자·불필요한 지출을 뺍니다."
    ],
    "faq": [
      {
        "question": "Chase 카드를 다시 만들 때마다 USD 200을 받나요?",
        "answer": "아닙니다. 확인한 제안은 현재 보유자와 지난 24개월 안에 해당 신규 보너스를 받은 과거 보유자를 제외합니다. 승인과 다른 제안 조건도 적용됩니다."
      },
      {
        "question": "선불 상품권도 Active Cash 적립 대상인가요?",
        "answer": "확인한 Wells Fargo 약관은 선불 상품권과 기타 현금성 거래를 기본 적립과 가입 보너스 인정 구매에서 제외합니다."
      },
      {
        "question": "캐시백을 명세 차감으로 받으면 결제를 생략해도 되나요?",
        "answer": "명세서의 납부 금액과 결제일을 따르세요. 리워드를 사용했다는 이유로 필요한 납부를 건너뛰지 말고 발급사의 납부 규정을 확인하세요."
      }
    ],
    "infographic": {
      "title": "혜택을 남기는 세 단계",
      "steps": [
        {
          "title": "계획한 소비",
          "text": "원래 필요한 구매에서 적립합니다."
        },
        {
          "title": "보너스 자격",
          "text": "제외 거래와 정확한 기한을 확인합니다."
        },
        {
          "title": "전액 결제",
          "text": "구매 유예기간 조건을 지킵니다."
        }
      ]
    },
    "example": {
      "title": "일회성 보너스가 첫해 숫자를 바꿉니다",
      "intro": "가상 조건: 매년 인정 구매 USD 12,000, 캐시백 2%, 첫해 지급되는 별도 보너스 USD 200입니다.",
      "headers": [
        "기간",
        "계산",
        "혜택"
      ],
      "rows": [
        [
          "첫해: 보너스 포함",
          "USD 12,000 × 2% + USD 200",
          "USD 440"
        ],
        [
          "다음 해: 새 보너스 없음",
          "USD 12,000 × 2%",
          "USD 240"
        ]
      ],
      "chart": {
        "values": [
          440,
          240
        ],
        "difference": "일회성 차이: USD 200"
      },
      "note": "계산 방법을 위한 가상 예시이며 위 카드의 수익 견적이 아닙니다. 보너스 조건 충족, 반품·추가 소비 없음, 연회비·이자·기타 비용 0을 가정합니다. 적립률과 소비액은 같고 기본 적립과 별개인 보너스는 한 번만 더합니다. 실제 비용은 차감하세요."
    },
    "inspiration": {
      "href": "https://www.banksalad.com/articles/신용카드로-돈벌기-집에서-돈버는-방법",
      "label": "주제 참고: 뱅크샐러드 카드테크 글"
    }
  },
  "ja": {
    "title": "米国のカード活用術：キャッシュバックと入会ボーナス",
    "description": "米国カードの通常還元と入会特典を比較。Chase・Wells Fargoの例で対象支出、既存会員の制限、費用を差し引いた価値を確認できます。",
    "intro": "予定した支出の還元と入会ボーナスは、米国カードを活用する二つの方法です。比較するのは、手数料と利息を差し引いて残る特典です。",
    "takeaway": "予算にある支出に合う還元を選び、申込前に特典の対象条件を確認します。新しい特典のない翌年も比較しましょう。",
    "tableHeaders": [
      "カード例",
      "年会費",
      "通常還元の条件"
    ],
    "rows": [
      {
        "bank": "Chase",
        "code": "JCBN",
        "name": "Freedom Unlimited",
        "fee": "USD 0",
        "detail": "他の対象購入1.5%、飲食店・ドラッグストア3%、Chase Travel経由の旅行購入5%。カテゴリー別の条件があります。",
        "source": "us-card-chase"
      },
      {
        "bank": "Wells Fargo",
        "code": "WFBN",
        "name": "Active Cash",
        "fee": "USD 0",
        "detail": "返品・返金などを差し引いた対象純購入額に上限なしの2% cash rewards。対象外取引には還元されません。",
        "source": "us-card-wells"
      }
    ],
    "sections": [
      {
        "id": "everyday-cashback",
        "title": "1. 生活費と還元率を合わせる",
        "paragraphs": [
          "一律還元は管理しやすく、カテゴリー還元は対象の支出で高くなる場合があります。実際の支出割合で比較しましょう。Chaseの飲食店3%は基本1.5%に追加3%ではなく合計還元率です。実際に受け取る現金価値も確認してください。"
        ],
        "sources": [
          "us-card-chase",
          "us-card-wells"
        ]
      },
      {
        "id": "welcome-offer",
        "title": "2. 予定した支出で入会ボーナスを満たす",
        "paragraphs": [
          "2026年10月15日に確認したChase Freedom Unlimitedの特典は、開設後最初の3か月に対象購入USD 500で、USD 200の還元に交換できる20,000ボーナスポイントです。現在の同カード会員と、過去24か月以内に同カードの新規会員ボーナスを受けた元会員は対象外です。",
          "付与時に口座が開設中で債務不履行でないことが必要で、条件達成後の付与には6〜8週間かかり得ます。申込経路によって条件が異なり、変更もあり得ます。実際の特典と審査要件を確認しましょう。"
        ],
        "sources": [
          "us-card-chase"
        ]
      },
      {
        "id": "excluded-spending",
        "title": "ギフトカード・現金同等取引の除外条件を読む",
        "paragraphs": [
          "ギフトカードの転売で対象支出になるとは限りません。Wells Fargo Active Cashはプリペイドギフトカードと現金同等取引を、通常還元と入会特典の対象購入から明示的に除外します。Chaseも現金同等取引・キャッシング・残高移行を除外します。不要な支出を増やすと特典を上回る費用になり得ます。"
        ],
        "sources": [
          "us-card-wells",
          "us-card-chase"
        ]
      },
      {
        "id": "worked-example",
        "title": "初年度の上乗せと継続価値を分ける",
        "paragraphs": [
          "通常還元 + 別途の入会ボーナス − 年会費 − 利息 − その他費用 = 残る特典です。購入の猶予期間が適用される場合、期日までに明細残高を全額支払えば購入利息を避けられます。キャッシングには通常この猶予はありません。"
        ],
        "sources": [
          "us-card-cfpb"
        ]
      }
    ],
    "checklist": [
      "最新特典・申込経路・過去会員の制限を読む。",
      "正確な期限内に計上される対象純購入額を数える。",
      "ボーナスなしの翌年も比較し、手数料・利息・不要な支出を差し引く。"
    ],
    "faq": [
      {
        "question": "Chaseを再開設するたびにUSD 200を受け取れますか？",
        "answer": "いいえ。確認した特典は現在の会員と、過去24か月以内に同カードの新規会員ボーナスを受けた元会員を除外します。審査や他の条件も適用されます。"
      },
      {
        "question": "プリペイドギフトカードはActive Cashの還元対象ですか？",
        "answer": "確認したWells Fargoの規約は、プリペイドギフトカードと現金同等取引を通常還元と入会特典の対象購入から除外しています。"
      },
      {
        "question": "還元を明細への充当に使えば支払いを省略できますか？",
        "answer": "明細の必要支払額と期日に従ってください。還元利用を理由に必要な支払いを省略せず、発行会社の支払規定を確認しましょう。"
      }
    ],
    "infographic": {
      "title": "特典を残す三つの手順",
      "steps": [
        {
          "title": "予定した支出",
          "text": "もともと必要な購入で還元。"
        },
        {
          "title": "特典の条件",
          "text": "対象外取引と正確な期限を確認。"
        },
        {
          "title": "全額支払い",
          "text": "購入の猶予期間の条件を守る。"
        }
      ]
    },
    "example": {
      "title": "一度限りの特典で初年度の数字は変わる",
      "intro": "仮の条件：毎年の対象購入USD 12,000、還元2%、初年度に支払われる別途の特典USD 200。",
      "headers": [
        "期間",
        "計算",
        "特典"
      ],
      "rows": [
        [
          "初年度：特典あり",
          "USD 12,000 × 2% + USD 200",
          "USD 440"
        ],
        [
          "翌年：新たな特典なし",
          "USD 12,000 × 2%",
          "USD 240"
        ]
      ],
      "chart": {
        "values": [
          440,
          240
        ],
        "difference": "一度限りの差：USD 200"
      },
      "note": "計算方法の仮定で、上記カードの還元見積もりではありません。特典条件を満たし、返品・追加支出なし、年会費・利息・その他費用ゼロを想定。還元率と支出は同じで、通常還元と別の特典は一度だけ加えます。実費は差し引いてください。"
    },
    "inspiration": {
      "href": "https://www.banksalad.com/articles/신용카드로-돈벌기-집에서-돈버는-방법",
      "label": "テーマ参考：Banksaladのカード特典記事"
    }
  }
};

export const CA_CARD_REWARDS_PRESENTATION = {
  "en": {
    "scope": "Canadian · Credit card rewards",
    "comparison": "Verified card examples: read the reward rules",
    "compare": "Explore Canadian credit cards",
    "compareBody": "Compare published cards and their verification dates. Confirm fees, interest, eligibility and the current offer with the issuer. Examples here may not all be listed.",
    "action": "Browse Canadian cards",
    "about": "Canadian credit card cash back and welcome bonuses"
  },
  "ko": {
    "scope": "캐나다 · 신용카드 혜택",
    "comparison": "공식 자료로 확인한 카드 사례",
    "compare": "캐나다 신용카드를 살펴보세요",
    "compareBody": "공개된 카드와 확인일을 비교하세요. 연회비·이자·자격·최신 제안은 발급사에서 확인하세요. 위 카드가 모두 목록에 있는 것은 아닙니다.",
    "action": "캐나다 카드 살펴보기",
    "about": "캐나다 신용카드 캐시백과 가입 보너스"
  },
  "ja": {
    "scope": "カナダ · クレジットカード特典",
    "comparison": "公式情報で確認したカード例",
    "compare": "カナダのカードを見る",
    "compareBody": "公開カードと確認日を比較し、費用・利息・対象条件・最新特典は発行会社で確認してください。上記カードがすべて掲載されているとは限りません。",
    "action": "カナダのカードを探す",
    "about": "カナダのカード還元と入会特典"
  }
} satisfies Record<EditorialLocale, object>;

export const US_CARD_REWARDS_PRESENTATION = {
  "en": {
    "scope": "US · Credit card rewards",
    "comparison": "Verified card examples: read the reward rules",
    "compare": "Explore US credit cards",
    "compareBody": "Compare published cards and their verification dates. Confirm fees, interest, eligibility and the current offer with the issuer. Examples here may not all be listed.",
    "action": "Browse US cards",
    "about": "US credit card cash back and welcome bonuses"
  },
  "ko": {
    "scope": "미국 · 신용카드 혜택",
    "comparison": "공식 자료로 확인한 카드 사례",
    "compare": "미국 신용카드를 살펴보세요",
    "compareBody": "공개된 카드와 확인일을 비교하세요. 연회비·이자·자격·최신 제안은 발급사에서 확인하세요. 위 카드가 모두 목록에 있는 것은 아닙니다.",
    "action": "미국 카드 살펴보기",
    "about": "미국 신용카드 캐시백과 가입 보너스"
  },
  "ja": {
    "scope": "米国 · クレジットカード特典",
    "comparison": "公式情報で確認したカード例",
    "compare": "米国のカードを見る",
    "compareBody": "公開カードと確認日を比較し、費用・利息・対象条件・最新特典は発行会社で確認してください。上記カードがすべて掲載されているとは限りません。",
    "action": "米国のカードを探す",
    "about": "米国のカード還元と入会特典"
  }
} satisfies Record<EditorialLocale, object>;

