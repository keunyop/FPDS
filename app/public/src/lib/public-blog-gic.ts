import type { BlogContent } from './public-blog-content.ts';
import type { PublicLocale } from './public-locale.ts';

export const GIC_SOURCES = [
  {
    "id": "cibc-gic",
    "title": "CIBC — Flexible GIC (non-registered)",
    "href": "https://www.cibc.com/en/personal-banking/investments/gics/flexible.html"
  },
  {
    "id": "rbc-gic",
    "title": "RBC — Guaranteed-Return GICs / One-Year Cashable GIC",
    "href": "https://www.rbcroyalbank.com/investments/guaranteed-return-gics.html"
  },
  {
    "id": "td-gic",
    "title": "TD — Non-Cashable GICs",
    "href": "https://www.td.com/ca/en/personal-banking/personal-investing/products/gic/non-cashable-gic"
  },
  {
    "id": "fcac-gic",
    "title": "FCAC — GIC and term-deposit information",
    "href": "https://www.canada.ca/en/financial-consumer-agency/services/rights-responsibilities/rights-investing/rights-guaranteed-investment-certificates.html"
  }
] as const;
export const GIC_CONTENT: Record<PublicLocale, BlogContent> = {
  "en": {
    "title": "Cashable vs non-cashable GICs in Canada: compare access before rates",
    "description": "Compare Canadian cashable and non-cashable GICs using CIBC, RBC and TD examples. Understand the 30-day interest condition, maturity dates and a CAD 10,000 example.",
    "intro": "A higher GIC rate is useful only if the withdrawal rules fit your plans. Before locking away savings for a home purchase, tuition or another dated expense, compare when you can get your money back and what happens to the interest if you leave early.",
    "takeaway": "Start with the date you need the money. Compare GICs with the same currency, term and withdrawal conditions, then compare rates. Cashable does not automatically mean that interest is paid from day one on an early withdrawal.",
    "tableHeaders": [
      "Product",
      "Access",
      "What to check"
    ],
    "rows": [
      {
        "bank": "CIBC",
        "code": "CIBC",
        "name": "Flexible GIC · non-registered",
        "fee": "Cashable",
        "detail": "One-year term. No interest on redemption in the first 29 days; from day 30, interest runs to withdrawal. Minimum early-withdrawal amounts depend on the investment.",
        "source": "cibc-gic"
      },
      {
        "bank": "RBC",
        "code": "RBC",
        "name": "One-Year Cashable GIC",
        "fee": "Cashable",
        "detail": "Full or partial early access. No interest in the first 29 days; daily interest for early redemption after at least 30 days. The checked product is non-registered.",
        "source": "rbc-gic"
      },
      {
        "bank": "TD",
        "code": "TD",
        "name": "Non-Cashable GIC",
        "fee": "Until maturity",
        "detail": "The official page states that the investment cannot be cashed before maturity. Do not compare its rate as though it offers the same access as a cashable GIC.",
        "source": "td-gic"
      }
    ],
    "sections": [
      {
        "id": "choose-the-date",
        "title": "1. Put the withdrawal date ahead of the headline rate",
        "paragraphs": [
          "Write down the earliest date you may need the money, not just the date you hope to spend it. If a home purchase could move forward, an extra fraction of interest may be less useful than having funds available for the deposit. This is a planning question, not a promise that one GIC suits everyone.",
          "Separate money you may need unexpectedly from money with a firm horizon. For each GIC, record the purchase date, maturity date and earliest permitted withdrawal date. A one-year term describes maturity; it does not, by itself, tell you whether you can leave early."
        ]
      },
      {
        "id": "cashable-conditions",
        "title": "2. Cashable: read access and interest as two separate rules",
        "paragraphs": [
          "CIBC Flexible and RBC One-Year Cashable illustrate why a cashable label needs a second line. Both checked pages distinguish withdrawal during the first 29 days from withdrawal after at least 30 days. Read the product’s full withdrawal conditions before treating the quoted rate as interest you will keep.",
          "Partial withdrawals can have minimum amounts or remaining-balance requirements. The CIBC row above covers its non-registered option; registered versions can have different account and transfer conditions. Do not copy a rule from one account wrapper into another."
        ],
        "sources": [
          "cibc-gic",
          "rbc-gic"
        ]
      },
      {
        "id": "non-cashable-conditions",
        "title": "3. Non-cashable: do not assume you can pay a penalty and leave",
        "paragraphs": [
          "TD’s checked non-cashable page says funds cannot be cashed before maturity. A product that forbids early access is different from one that allows access at a lower interest rate. Compare the actual rule, not an assumed cancellation fee.",
          "For every offer, request the exact maturity, rate calculation, payment schedule and early-redemption terms. The FCAC information page is a useful checklist for the disclosures to read before purchasing."
        ],
        "sources": [
          "td-gic",
          "fcac-gic"
        ]
      },
      {
        "id": "worked-example",
        "title": "4. Turn a rate difference into dollars",
        "paragraphs": [
          "A hypothetical one-year comparison helps put the extra return in perspective. The calculation below assumes both investments stay in place for the entire year. It does not price the value of early access or reproduce any bank’s current offer."
        ]
      },
      {
        "id": "compare-on-switchabank",
        "title": "5. Build a shortlist with matching conditions",
        "paragraphs": [
          "Open the GIC catalog and read the available products’ terms and withdrawal conditions before adding them to a comparison. Keep CAD and other currencies separate. A 100-day GIC, a one-year cashable GIC and a five-year non-redeemable GIC are different comparisons.",
          "Record whether interest is simple or compounded and when it is paid. Check the official quote and maturity instructions before buying, including what will happen if you give no renewal instructions. SwitchaBank may not list every product discussed here; an absent listing is not evidence that a product has been discontinued."
        ],
        "sources": [
          "fcac-gic"
        ]
      }
    ],
    "example": {
      "title": "What does an extra 0.5 percentage point pay on CAD 10,000?",
      "intro": "Fictional annual simple rates, the same principal and a full 12 months.",
      "headers": [
        "Scenario",
        "Calculation",
        "Interest"
      ],
      "rows": [
        [
          "A: annual simple rate 3.0%",
          "10,000 × 0.03 × 1",
          "CAD 300"
        ],
        [
          "B: annual simple rate 3.5%",
          "10,000 × 0.035 × 1",
          "CAD 350"
        ]
      ],
      "note": "The difference is CAD 50 over one full year. These are fictional rates, not current bank offers or APYs. No compounding, tax, fee or early withdrawal is included. Actual redemption interest follows the product agreement."
    },
    "checklist": [
      "Match currency, exact term and redemption category.",
      "Check the earliest withdrawal date and interest lost on early access.",
      "Read minimum withdrawal and remaining-balance conditions.",
      "Compare the same deposit amount and interest-payment basis.",
      "Confirm maturity and renewal instructions with the bank."
    ],
    "faq": [
      {
        "question": "Are cashable and redeemable GICs always the same?",
        "answer": "Do not rely on the name alone. Compare the actual access date, early-redemption rate and minimum withdrawal conditions for each product."
      },
      {
        "question": "Is a non-cashable GIC always better because of its rate?",
        "answer": "A rate cannot answer an access question. Compare the extra dollars over the same term with the need to keep that money available; the worked example is illustrative, not a recommendation."
      },
      {
        "question": "Does a one-year cashable GIC pay a full year of interest if I leave early?",
        "answer": "Check the agreement. The checked cashable examples describe interest to the redemption date once their holding-period condition is met, not an automatic full year of interest."
      }
    ]
  },
  "ko": {
    "title": "캐나다 Cashable·Non-cashable GIC 비교: 금리 전에 확인할 인출 조건",
    "description": "CIBC·RBC·TD 사례로 캐나다 GIC의 중도 인출과 30일 이자 조건을 비교합니다. 만기·재예치 확인법과 CAD 10,000 가상 이자 계산을 확인하세요.",
    "intro": "GIC 금리가 높아도 돈이 필요한 날 인출할 수 없다면 선택을 다시 생각해야 합니다. 주택 구입비나 학비처럼 사용 시점이 있는 돈을 맡기기 전, 언제 찾을 수 있는지와 중도 인출 시 이자가 어떻게 달라지는지를 함께 살펴보세요.",
    "takeaway": "돈이 필요한 날짜부터 정하세요. 같은 통화·기간·인출 조건의 상품끼리 금리를 비교해야 합니다. Cashable이라는 이름만으로 가입 직후 인출해도 이자를 받는다고 판단하면 안 됩니다.",
    "tableHeaders": [
      "상품",
      "인출 방식",
      "확인할 조건"
    ],
    "rows": [
      {
        "bank": "CIBC",
        "code": "CIBC",
        "name": "Flexible GIC · non-registered",
        "fee": "중도 인출 가능",
        "detail": "1년 만기입니다. 첫 29일 이내 인출하면 이자가 없고 30일째부터는 인출일까지의 이자를 지급합니다. 중도 인출 최소 금액은 투자액에 따라 달라집니다.",
        "source": "cibc-gic"
      },
      {
        "bank": "RBC",
        "code": "RBC",
        "name": "One-Year Cashable GIC",
        "fee": "중도 인출 가능",
        "detail": "전액 또는 일부 인출이 가능합니다. 첫 29일에는 이자가 없으며 최소 30일 보유 후 중도 인출하면 일별 이자를 계산합니다. 확인한 상품은 비등록 계좌용입니다.",
        "source": "rbc-gic"
      },
      {
        "bank": "TD",
        "code": "TD",
        "name": "Non-Cashable GIC",
        "fee": "만기까지 보유",
        "detail": "공식 안내상 만기 전 인출할 수 없습니다. Cashable 상품과 자금 접근성이 같다고 보고 금리만 비교하면 안 됩니다.",
        "source": "td-gic"
      }
    ],
    "sections": [
      {
        "id": "choose-the-date",
        "title": "1. 광고 금리보다 돈이 필요한 날짜를 먼저 정하세요",
        "paragraphs": [
          "예정한 지출일뿐 아니라 가장 빨리 돈이 필요할 수 있는 날을 적어보세요. 주택 구입 일정이 앞당겨질 수 있다면 추가 이자보다 계약금을 제때 마련하는 일이 더 중요할 수 있습니다. 모든 사람에게 같은 상품이 맞는다는 뜻은 아닙니다.",
          "갑자기 필요할 수 있는 돈과 사용 시점이 확실한 돈을 구분하세요. 상품별 가입일·만기일·최초 인출 가능일을 적으면 비교가 쉬워집니다. 1년 만기라는 설명만으로 중도 인출 가능 여부를 알 수는 없습니다."
        ]
      },
      {
        "id": "cashable-conditions",
        "title": "2. Cashable은 인출 가능 여부와 이자 조건을 나눠 읽으세요",
        "paragraphs": [
          "CIBC Flexible과 RBC One-Year Cashable의 확인한 안내는 첫 29일과 최소 30일 보유 후 인출을 구분합니다. 표시 금리를 실제로 받을 이자로 생각하기 전에 해당 상품의 인출 조건 전체를 확인하세요.",
          "일부 인출에는 최소 인출액이나 남겨둘 잔액 조건이 있을 수 있습니다. 위 CIBC 표는 비등록 상품을 설명합니다. 등록 계좌용 상품은 계좌·이전 조건이 다를 수 있으므로 다른 계좌의 규칙을 그대로 적용하지 마세요."
        ],
        "sources": [
          "cibc-gic",
          "rbc-gic"
        ]
      },
      {
        "id": "non-cashable-conditions",
        "title": "3. Non-cashable은 위약금을 내면 해지할 수 있다고 가정하지 마세요",
        "paragraphs": [
          "확인한 TD Non-Cashable 안내는 만기 전 인출이 불가능하다고 설명합니다. 인출 자체가 금지된 상품과 낮은 이율로 중도 인출할 수 있는 상품은 다릅니다. 예상한 해지 수수료가 아니라 실제 약정을 비교하세요.",
          "가입 전 정확한 만기·이자 계산 방식·지급 주기·중도 인출 조건을 확인하세요. FCAC 안내는 어떤 정보를 읽어야 하는지 점검하는 데 도움이 됩니다."
        ],
        "sources": [
          "td-gic",
          "fcac-gic"
        ]
      },
      {
        "id": "worked-example",
        "title": "4. 금리 차이를 실제 금액으로 바꿔보세요",
        "paragraphs": [
          "아래 가상 계산은 두 상품을 모두 1년 동안 유지한다고 가정합니다. 인출 가능성의 가치를 계산한 것도, 은행의 현재 금리를 옮긴 것도 아닙니다."
        ]
      },
      {
        "id": "compare-on-switchabank",
        "title": "5. SwitchaBank에서 같은 조건끼리 비교하세요",
        "paragraphs": [
          "GIC 목록에서 공개된 기간·인출 조건을 읽고 비교 목록에 추가하세요. CAD와 다른 통화는 구분해야 합니다. 100일 GIC, 1년 Cashable GIC, 5년 중도 인출 불가 GIC는 각각 다른 비교입니다.",
          "단리·복리 여부와 이자 지급일도 적어두세요. 가입 전 현재 조건과 만기 처리 방법, 별도 지시가 없을 때 재예치되는지를 은행에서 확인하세요. 이 글의 모든 상품이 SwitchaBank에 공개되어 있다는 뜻은 아니며, 목록에 없다고 판매 종료로 판단해서는 안 됩니다."
        ],
        "sources": [
          "fcac-gic"
        ]
      }
    ],
    "example": {
      "title": "CAD 10,000에서 연 0.5%포인트 차이는 얼마일까요?",
      "intro": "같은 원금, 12개월 보유, 가상의 연 단리로 계산합니다.",
      "headers": [
        "가정",
        "계산식",
        "이자"
      ],
      "rows": [
        [
          "A: 연 단리 3.0%",
          "10,000 × 0.03 × 1",
          "CAD 300"
        ],
        [
          "B: 연 단리 3.5%",
          "10,000 × 0.035 × 1",
          "CAD 350"
        ]
      ],
      "note": "1년 전체의 차이는 CAD 50입니다. 가상 금리이며 현재 은행 금리나 APY가 아닙니다. 복리·세금·수수료·중도 인출은 제외했습니다. 실제 중도 인출 이자는 상품 약정을 따릅니다."
    },
    "checklist": [
      "통화·정확한 기간·인출 유형을 맞추세요.",
      "최초 인출 가능일과 중도 인출 시 이자 손실을 확인하세요.",
      "최소 인출액과 유지 잔액 조건을 읽으세요.",
      "같은 예치액과 이자 지급 기준으로 비교하세요.",
      "만기 처리와 재예치 지시를 은행에서 확인하세요."
    ],
    "faq": [
      {
        "question": "Cashable과 Redeemable은 항상 같은 뜻인가요?",
        "answer": "이름만으로 판단하지 마세요. 상품별 최초 인출 가능일·중도 인출 이율·최소 인출액을 비교해야 합니다."
      },
      {
        "question": "금리가 높으면 Non-cashable이 더 좋은가요?",
        "answer": "금리만으로 자금 접근성을 판단할 수는 없습니다. 같은 기간의 추가 이자와 돈을 사용할 필요를 함께 비교하세요. 계산 예시는 이해를 위한 가정이며 추천이 아닙니다."
      },
      {
        "question": "1년 Cashable GIC를 중도 인출하면 1년치 이자를 받나요?",
        "answer": "약정을 확인해야 합니다. 확인한 Cashable 사례는 보유 기간 조건을 충족하면 인출일까지의 이자를 설명하며, 자동으로 1년치 이자를 지급한다는 뜻이 아닙니다."
      }
    ]
  },
  "ja": {
    "title": "カナダのCashable・Non-cashable GIC比較：金利より先に確認する解約条件",
    "description": "CIBC・RBC・TDの例でカナダGICの中途解約、30日の利息条件、満期を比較。CAD 10,000の仮定計算と更新前のチェック項目も紹介します。",
    "intro": "GICの金利が高くても、必要な日に資金を引き出せなければ計画に合いません。住宅購入や学費など使う時期があるお金は、解約できる日と中途解約時の利息を一緒に確認しましょう。",
    "takeaway": "最初に資金が必要な日を決めましょう。同じ通貨・期間・解約条件の商品で金利を比べます。Cashableという名称だけでは、購入直後の解約でも利息が付くとは判断できません。",
    "tableHeaders": [
      "商品",
      "引き出し",
      "確認する条件"
    ],
    "rows": [
      {
        "bank": "CIBC",
        "code": "CIBC",
        "name": "Flexible GIC · non-registered",
        "fee": "中途解約可",
        "detail": "期間は1年。最初の29日以内の解約は無利息で、30日目以降は引き出し日までの利息を受け取れます。最低引き出し額は投資額によって異なります。",
        "source": "cibc-gic"
      },
      {
        "bank": "RBC",
        "code": "RBC",
        "name": "One-Year Cashable GIC",
        "fee": "中途解約可",
        "detail": "全額または一部を引き出せます。最初の29日は無利息で、30日以上保有して中途解約すると日割りで利息を計算します。確認した商品は非登録口座向けです。",
        "source": "rbc-gic"
      },
      {
        "bank": "TD",
        "code": "TD",
        "name": "Non-Cashable GIC",
        "fee": "満期まで保有",
        "detail": "公式案内では満期前の解約はできません。Cashable商品と同じ資金アクセスがあると考えて金利だけを比べないようにしましょう。",
        "source": "td-gic"
      }
    ],
    "sections": [
      {
        "id": "choose-the-date",
        "title": "1. 金利より先に資金が必要な日を決める",
        "paragraphs": [
          "予定した支出日だけでなく、最も早く資金が必要になる可能性がある日を記録しましょう。住宅購入が早まるなら、追加利息より手付金を用意できることが重要な場合があります。全員に同じ商品が合うという意味ではありません。",
          "急に必要になるお金と、使用時期が決まっているお金を分けます。商品ごとに購入日・満期日・最初の解約可能日を記録しましょう。1年満期という説明だけでは中途解約の可否はわかりません。"
        ]
      },
      {
        "id": "cashable-conditions",
        "title": "2. Cashableは解約と利息を別の条件として読む",
        "paragraphs": [
          "確認したCIBC FlexibleとRBC One-Year Cashableの案内は、最初の29日と30日以上保有した後の解約を区別しています。表示金利を受け取れる利息と考える前に、解約条件全体を確認しましょう。",
          "一部解約には最低引き出し額や残すべき残高が設定される場合があります。表のCIBCは非登録商品です。登録口座版には異なる口座・移管条件があり得るため、別の口座の条件をそのまま当てはめないでください。"
        ],
        "sources": [
          "cibc-gic",
          "rbc-gic"
        ]
      },
      {
        "id": "non-cashable-conditions",
        "title": "3. Non-cashableは違約金を払えば解約できるとは限らない",
        "paragraphs": [
          "確認したTD Non-Cashableの案内では、満期前に資金を引き出せません。解約そのものができない商品と、低い利率で解約できる商品は異なります。想定した解約手数料ではなく契約内容を比較しましょう。",
          "購入前に満期・利息計算方法・支払頻度・中途解約条件を確認します。FCACの案内は、読むべき開示情報を確認する際のチェックリストになります。"
        ],
        "sources": [
          "td-gic",
          "fcac-gic"
        ]
      },
      {
        "id": "worked-example",
        "title": "4. 金利差を金額に置き換える",
        "paragraphs": [
          "下の仮定計算は、両商品を1年間保有する場合です。中途解約できる価値を計算したものでも、銀行の現在の金利を示したものでもありません。"
        ]
      },
      {
        "id": "compare-on-switchabank",
        "title": "5. SwitchaBankで条件をそろえて比較する",
        "paragraphs": [
          "GIC一覧で公開中の期間・解約条件を読み、比較リストに追加しましょう。CADと他通貨は分けます。100日GIC、1年Cashable GIC、5年の中途解約不可GICはそれぞれ異なる比較です。",
          "単利か複利か、利息の支払日も記録します。購入前に最新条件と満期時の扱い、指示をしない場合の更新方法を銀行で確認してください。この記事の全商品がSwitchaBankに掲載されているとは限らず、未掲載だけで販売終了とは判断できません。"
        ],
        "sources": [
          "fcac-gic"
        ]
      }
    ],
    "example": {
      "title": "CAD 10,000で年0.5パーセントポイントの差はいくら？",
      "intro": "同じ元本、12か月保有、仮定の年単利で計算します。",
      "headers": [
        "仮定",
        "計算式",
        "利息"
      ],
      "rows": [
        [
          "A：年単利3.0%",
          "10,000 × 0.03 × 1",
          "CAD 300"
        ],
        [
          "B：年単利3.5%",
          "10,000 × 0.035 × 1",
          "CAD 350"
        ]
      ],
      "note": "1年間の差はCAD 50です。仮定の金利であり、銀行の現在の金利やAPYではありません。複利・税金・手数料・中途解約は含みません。実際の中途解約利息は商品契約に従います。"
    },
    "checklist": [
      "通貨・正確な期間・解約区分をそろえる。",
      "最初の解約可能日と失う利息を確認する。",
      "最低引き出し額と残高条件を読む。",
      "同じ預入額と利息支払基準で比較する。",
      "満期時と更新時の指示を銀行で確認する。"
    ],
    "faq": [
      {
        "question": "CashableとRedeemableは常に同じ意味ですか？",
        "answer": "名称だけで判断せず、商品ごとの解約可能日・中途解約利率・最低引き出し額を確認してください。"
      },
      {
        "question": "金利が高ければNon-cashableの方がよいですか？",
        "answer": "金利だけでは資金アクセスを判断できません。同じ期間の追加利息と、そのお金を使う必要性を比較しましょう。計算例は説明用の仮定であり推奨ではありません。"
      },
      {
        "question": "1年Cashable GICを途中解約すると1年分の利息を受け取れますか？",
        "answer": "契約の確認が必要です。確認したCashableの例は、保有日数条件を満たした場合の解約日までの利息を説明しており、自動的に1年分の利息を受け取れる意味ではありません。"
      }
    ]
  }
};
export const GIC_PRESENTATION = {
  "en": {
    "scope": "Canada · GICs",
    "comparison": "Three GIC examples: read the access conditions",
    "compare": "Compare GIC terms and access",
    "compareBody": "Browse published Canadian GICs, select available products and compare matching terms. Confirm current rates and redemption rules at the bank.",
    "action": "Compare GICs",
    "about": "Canadian cashable and non-cashable GIC comparison"
  },
  "ko": {
    "scope": "캐나다 · GIC",
    "comparison": "세 GIC 사례로 읽는 인출 조건",
    "compare": "GIC 기간과 인출 조건을 비교하세요",
    "compareBody": "캐나다 GIC 목록에서 공개 중인 상품을 선택하고 같은 기간끼리 비교하세요. 현재 금리와 인출 조건은 은행에서 확인하세요.",
    "action": "GIC 비교하기",
    "about": "캐나다 Cashable·Non-cashable GIC 비교"
  },
  "ja": {
    "scope": "カナダ · GIC",
    "comparison": "3つのGICで見る解約条件",
    "compare": "GICの期間と解約条件を比較",
    "compareBody": "カナダGIC一覧の公開商品を選び、同じ期間で比較しましょう。最新金利と解約条件は銀行で確認してください。",
    "action": "GICを比較する",
    "about": "カナダのCashable・Non-cashable GIC比較"
  }
};
