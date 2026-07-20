export type PublicLocale = "en" | "ko" | "ja";

type PublicMessages = {
  localeName: string;
  shell: {
    brand: string;
    tagline: string;
  };
  nav: {
    dashboard: string;
    products: string;
    methodology: string;
    loan: string;
    localeLabel: string;
  };
  common: {
    active: string;
    all: string;
    applyFilters: string;
    clearAllFilters: string;
    clearFilters: string;
    changedOn: string;
    noDate: string;
    noOptions: string;
    noRecentChange: string;
    noSuccessfulSnapshot: string;
    notDisclosed: string;
    bankPage: string;
    more: string;
    open: string;
    pageLabel: string;
    previous: string;
    next: string;
    verifiedOn: string;
  };
  grid: {
    pageTitle: string;
    pageDescription: string;
    title: string;
    description: string;
    currentScope: string;
    compareDetails: string;
    productCount: string;
    snapshotUpdated: string;
    primaryFilter: string;
    banks: string;
    productTypes: string;
    targetTags: string;
    feeBucket: string;
    minimumBalance: string;
    minimumDeposit: string;
    termBucket: string;
    sortBy: string;
    direction: string;
    resultSummary: string;
    searchConditions: string;
    noActiveFilters: string;
    noResultTitle: string;
    noResultBody: string;
    retryTitle: string;
    retryBody: string;
    retryButton: string;
    openDashboard: string;
    metricMonthlyFee: string;
    metricMinBalance: string;
    metricMinDeposit: string;
    metricDisplayRate: string;
    metricTerm: string;
    metricKeyDetail: string;
    metricLastChange: string;
    metricRateNote: string;
    ascending: string;
    descending: string;
    sortDefault: string;
    sortDisplayRate: string;
    sortMonthlyFee: string;
    sortMinimumBalance: string;
    sortMinimumDeposit: string;
    sortLastChange: string;
    sortBankName: string;
    sortProductName: string;
  };
  detail: {
    backToList: string;
    compareAtGlance: string;
    decisionSummary: string;
    disclosureTitle: string;
    keyConditions: string;
    officialPage: string;
    productFacts: string;
    similarProducts: string;
    sourceLanguage: string;
    termRates: string;
    whatToCheck: string;
  };
  dashboard: {
    pageTitle: string;
    pageDescription: string;
    title: string;
    description: string;
    marketGreeting: string;
    kpiSubtitle: string;
    composition: string;
    compositionSubtitle: string;
    productsByBank: string;
    productsByType: string;
    comparisonMap: string;
    comparisonSubtitle: string;
    coverageTable: string;
    coverageSubtitle: string;
    dataNotes: string;
    dataNotesBody: string;
    freshness: string;
    openProducts: string;
    noActiveFilters: string;
    noRankingWidgets: string;
    chartUnavailable: string;
    chartSingleTypeHint: string;
    visibleProducts: string;
    activeProducts: string;
    banksInScope: string;
    peakRate: string;
    topInterestRateTitle: string;
    openInProducts: string;
    apiUnavailableTitle: string;
    apiUnavailableBody: string;
    retryDashboard: string;
    mixedMarket: string;
  };
  purpose: {
    eyebrow: string;
    title: string;
    everydayTitle: string;
    everydayBody: string;
    everydayAction: string;
    savingsTitle: string;
    savingsBody: string;
    savingsAction: string;
    termTitle: string;
    termBody: string;
    termAction: string;
    lowEntryTitle: string;
    lowEntryBody: string;
    lowEntryAction: string;
  };
  compare: {
    eyebrow: string;
    title: string;
    subtitle: string;
    select: string;
    selected: string;
    selectedCount: string;
    limit: string;
    clear: string;
    remove: string;
    emptyTitle: string;
    emptyBody: string;
    tableProduct: string;
    tableWhy: string;
    entryAmount: string;
    application: string;
    officialPage: string;
    reasonNoMonthlyFee: string;
    reasonFeeKnown: string;
    reasonRateKnown: string;
    reasonTermRate: string;
    reasonLowEntry: string;
    reasonFallback: string;
  };
  methodology: {
    pageTitle: string;
    pageDescription: string;
    title: string;
    description: string;
    sections: Array<{
      title: string;
      body: string;
    }>;
  };
};

const PUBLIC_MESSAGES: Record<PublicLocale, PublicMessages> = {
  en: {
    localeName: "English",
    shell: {
      brand: "FPDS",
      tagline: ""
    },
    nav: {
      dashboard: "Home",
      products: "Deposit",
      methodology: "Methodology",
      loan: "Loan",
      localeLabel: "Language"
    },
    common: {
      active: "Active",
      all: "All",
      applyFilters: "Apply",
      clearAllFilters: "Clear all",
      clearFilters: "Clear",
      changedOn: "Changed",
      noDate: "No date",
      noOptions: "No options",
      noRecentChange: "No recent change",
      noSuccessfulSnapshot: "No successful public snapshot is available yet.",
      notDisclosed: "Unavailable",
      bankPage: "Bank page",
      more: "More",
      open: "Open",
      pageLabel: "Page",
      previous: "Previous",
      next: "Next",
      verifiedOn: "Verified"
    },
    grid: {
      pageTitle: "FPDS Deposits",
      pageDescription: "Compare Canadian chequing, savings, and GIC products.",
      title: "Compare deposits",
      description: "Chequing, savings, and GIC products from the latest public snapshot.",
      currentScope: "Current scope",
      compareDetails: "Compare details",
      productCount: "{count} products",
      snapshotUpdated: "Snapshot {date}",
      primaryFilter: "Primary",
      banks: "Banks",
      productTypes: "Product types",
      targetTags: "Customer tags",
      feeBucket: "Fee",
      minimumBalance: "Min. balance",
      minimumDeposit: "Min. deposit",
      termBucket: "Term",
      sortBy: "Sort",
      direction: "Direction",
      resultSummary: "Results",
      searchConditions: "Search conditions",
      noActiveFilters: "All available products",
      noResultTitle: "No products matched this scope.",
      noResultBody: "Clear filters or return to the dashboard for a broader market view.",
      retryTitle: "Products could not load.",
      retryBody: "The public API is not reachable.",
      retryButton: "Retry products",
      openDashboard: "Home",
      metricMonthlyFee: "Monthly fee",
      metricMinBalance: "Min. balance",
      metricMinDeposit: "Min. deposit",
      metricDisplayRate: "Interest rate",
      metricTerm: "Term",
      metricKeyDetail: "Key detail",
      metricLastChange: "Last change",
      metricRateNote: "Rate note",
      ascending: "Ascending",
      descending: "Descending",
      sortDefault: "Default",
      sortDisplayRate: "Interest rate",
      sortMonthlyFee: "Monthly fee",
      sortMinimumBalance: "Minimum balance",
      sortMinimumDeposit: "Minimum deposit",
      sortLastChange: "Last change",
      sortBankName: "Bank",
      sortProductName: "Product",
    },
    detail: {
      backToList: "Back to deposit list",
      compareAtGlance: "Compare at a glance",
      decisionSummary: "Decision summary",
      disclosureTitle: "Important note",
      keyConditions: "Key conditions",
      officialPage: "Open official bank page",
      productFacts: "Product facts",
      similarProducts: "More from this bank",
      sourceLanguage: "Source language",
      termRates: "Rates by term",
      whatToCheck: "What to check"
    },
    dashboard: {
      pageTitle: "FPDS Home",
      pageDescription: "Public financial product comparison snapshot.",
      title: "Compare the market, then the product",
      description: "",
      marketGreeting: "Compare {products} deposit products from {banks} banks in the latest public snapshot.",
      kpiSubtitle: "Deposit market snapshot",
      composition: "Market composition",
      compositionSubtitle: "Share of deposit products in the current snapshot.",
      productsByBank: "Products by bank",
      productsByType: "Products by type",
      comparisonMap: "Comparison map",
      comparisonSubtitle: "Select one product type for a like-for-like chart.",
      coverageTable: "Coverage table",
      coverageSubtitle: "Public products currently represented in the snapshot.",
      dataNotes: "Data notes",
      dataNotesBody: "Metrics use public aggregate fields. Products missing required numeric values are excluded from affected comparisons.",
      freshness: "Freshness",
      openProducts: "Deposit",
      noActiveFilters: "No filters active.",
      noRankingWidgets: "No ranking is eligible for this scope.",
      chartUnavailable: "Not enough eligible products for this chart.",
      chartSingleTypeHint: "Choose one product type to unlock the comparison map.",
      visibleProducts: "Visible products",
      activeProducts: "active products",
      banksInScope: "Banks",
      peakRate: "Top Interest Rate",
      topInterestRateTitle: "Top 5 Interest Rate",
      openInProducts: "Open in products",
      apiUnavailableTitle: "Dashboard could not load.",
      apiUnavailableBody: "The public aggregate API is not reachable.",
      retryDashboard: "Retry dashboard",
      mixedMarket: "All products"
    },
    purpose: {
      eyebrow: "Start by purpose",
      title: "What are you trying to compare?",
      everydayTitle: "Keep everyday banking costs low",
      everydayBody: "Start with chequing products sorted by lower monthly fee.",
      everydayAction: "Compare low-fee accounts",
      savingsTitle: "Grow cash with a visible rate",
      savingsBody: "Start with savings products sorted by public display rate.",
      savingsAction: "Compare savings rates",
      termTitle: "Lock a fixed-term return",
      termBody: "Start with GIC and term products sorted by public display rate.",
      termAction: "Compare term rates",
      lowEntryTitle: "Start with a lower entry amount",
      lowEntryBody: "Scan products where minimum balance or deposit matters most.",
      lowEntryAction: "Compare entry amounts"
    },
    compare: {
      eyebrow: "Side-by-side",
      title: "Compare up to 4 products",
      subtitle: "Choose product cards to compare available public fields.",
      select: "Compare",
      selected: "Selected",
      selectedCount: "{count}/{limit} selected",
      limit: "You can compare up to 4 products at a time.",
      clear: "Clear",
      remove: "Remove",
      emptyTitle: "No products selected yet.",
      emptyBody: "Use Compare on any product card to build a focused table. FPDS does not score personal eligibility or submit applications.",
      tableProduct: "Product",
      tableWhy: "Why compare",
      entryAmount: "Entry amount",
      application: "Application",
      officialPage: "Official page",
      reasonNoMonthlyFee: "Monthly fee is disclosed as zero.",
      reasonFeeKnown: "Monthly fee is available for direct cost comparison.",
      reasonRateKnown: "A public display rate is available for rate comparison.",
      reasonTermRate: "Term and public display rate are both available.",
      reasonLowEntry: "Minimum balance or deposit is available for entry-cost comparison.",
      reasonFallback: "Comparable public fields are available."
    },
    methodology: {
      pageTitle: "FPDS Methodology",
      pageDescription: "Public data notes and metric boundaries.",
      title: "Methodology",
      description: "What the public snapshot includes, excludes, and may leave unavailable.",
      sections: [
        {
          title: "Snapshot source",
          body: "Public pages use the latest successful aggregate snapshot, not live bank pages."
        },
        {
          title: "Metric eligibility",
          body: "A rate, fee, amount, or term appears only when its approved public field is available."
        },
        {
          title: "Product text",
          body: "Product names and source-derived conditions stay in the original source language."
        },
        {
          title: "Evidence boundary",
          body: "Raw evidence, source excerpts, and internal review traces are not exposed on FPDS."
        }
      ]
    }
  },
  ko: {
    localeName: "한국어",
    shell: {
      brand: "FPDS",
      tagline: ""
    },
    nav: {
      dashboard: "홈",
      products: "예금",
      methodology: "방법론",
      loan: "대출",
      localeLabel: "언어"
    },
    common: {
      active: "활성",
      all: "전체",
      applyFilters: "적용",
      clearAllFilters: "전체 해제",
      clearFilters: "해제",
      changedOn: "변경",
      noDate: "날짜 없음",
      noOptions: "옵션 없음",
      noRecentChange: "최근 변경 없음",
      noSuccessfulSnapshot: "아직 사용 가능한 공개 스냅샷이 없습니다.",
      notDisclosed: "정보 없음",
      bankPage: "은행 페이지",
      more: "더보기",
      open: "열기",
      pageLabel: "페이지",
      previous: "이전",
      next: "다음",
      verifiedOn: "검증"
    },
    grid: {
      pageTitle: "FPDS 예금",
      pageDescription: "캐나다 입출금, 저축, GIC 상품을 비교합니다.",
      title: "예금 비교",
      description: "최신 공개 스냅샷의 입출금, 저축, GIC 상품입니다.",
      currentScope: "현재 범위",
      compareDetails: "상세 비교",
      productCount: "{count}개 상품",
      snapshotUpdated: "스냅샷 {date}",
      primaryFilter: "주요",
      banks: "은행",
      productTypes: "상품 유형",
      targetTags: "고객 태그",
      feeBucket: "수수료",
      minimumBalance: "최소 잔액",
      minimumDeposit: "최소 예치금",
      termBucket: "기간",
      sortBy: "정렬",
      direction: "방향",
      resultSummary: "결과",
      searchConditions: "검색조건",
      noActiveFilters: "전체 상품",
      noResultTitle: "현재 범위에 맞는 상품이 없습니다.",
      noResultBody: "필터를 해제하거나 대시보드에서 더 넓은 시장을 확인하세요.",
      retryTitle: "상품을 불러오지 못했습니다.",
      retryBody: "공개 API에 연결할 수 없습니다.",
      retryButton: "상품 다시 불러오기",
      openDashboard: "홈",
      metricMonthlyFee: "월 수수료",
      metricMinBalance: "최소 잔액",
      metricMinDeposit: "최소 예치금",
      metricDisplayRate: "표시 금리",
      metricTerm: "기간",
      metricKeyDetail: "핵심 정보",
      metricLastChange: "최근 변경",
      metricRateNote: "금리 메모",
      ascending: "오름차순",
      descending: "내림차순",
      sortDefault: "기본",
      sortDisplayRate: "표시 금리",
      sortMonthlyFee: "월 수수료",
      sortMinimumBalance: "최소 잔액",
      sortMinimumDeposit: "최소 예치금",
      sortLastChange: "최근 변경",
      sortBankName: "은행",
      sortProductName: "상품",
    },
    detail: {
      backToList: "예금 목록으로 돌아가기",
      compareAtGlance: "한눈에 비교",
      decisionSummary: "판단 요약",
      disclosureTitle: "중요 안내",
      keyConditions: "주요 조건",
      officialPage: "은행 공식 페이지 열기",
      productFacts: "상품 정보",
      similarProducts: "이 은행의 다른 상품",
      sourceLanguage: "원문 언어",
      termRates: "기간별 금리",
      whatToCheck: "확인할 내용"
    },
    dashboard: {
      pageTitle: "FPDS 대시보드",
      pageDescription: "공개 금융상품 비교 스냅샷입니다.",
      title: "시장부터 보고, 상품을 비교하세요",
      description: "최신 공개 스냅샷 기준으로 현재 상품 범위를 빠르게 비교합니다.",
      marketGreeting: "최신 공개 스냅샷에서 {banks}개 은행의 예금 상품 {products}개를 비교하세요.",
      kpiSubtitle: "예금 시장 스냅샷",
      composition: "시장 구성",
      compositionSubtitle: "현재 스냅샷의 은행별 예금 상품 비중입니다.",
      productsByBank: "은행별 상품",
      productsByType: "유형별 상품",
      comparisonMap: "비교 맵",
      comparisonSubtitle: "상품 유형 하나를 선택하면 같은 기준으로 비교합니다.",
      coverageTable: "커버리지 표",
      coverageSubtitle: "현재 스냅샷에 포함된 공개 상품입니다.",
      dataNotes: "데이터 기준",
      dataNotesBody: "지표는 공개 aggregate 필드를 사용하며, 필요한 숫자 값이 없는 상품은 해당 비교에서 제외됩니다.",
      freshness: "최신성",
      openProducts: "상품 열기",
      noActiveFilters: "활성 필터 없음",
      noRankingWidgets: "현재 범위에서 표시할 순위가 없습니다.",
      chartUnavailable: "차트를 그릴 수 있는 상품 수가 부족합니다.",
      chartSingleTypeHint: "상품 유형 하나를 선택하면 비교 맵이 열립니다.",
      visibleProducts: "표시 상품",
      activeProducts: "활성 상품",
      banksInScope: "은행",
      peakRate: "최고 금리",
      topInterestRateTitle: "상위 5개 금리",
      openInProducts: "상품에서 열기",
      apiUnavailableTitle: "대시보드를 불러오지 못했습니다.",
      apiUnavailableBody: "공개 aggregate API에 연결할 수 없습니다.",
      retryDashboard: "대시보드 다시 불러오기",
      mixedMarket: "전체 상품 유형"
    },
    purpose: {
      eyebrow: "목적부터 시작",
      title: "무엇을 비교하고 싶으신가요?",
      everydayTitle: "일상 은행 비용 줄이기",
      everydayBody: "월 수수료가 낮은 입출금 상품부터 비교합니다.",
      everydayAction: "저수수료 계좌 비교",
      savingsTitle: "보이는 금리로 현금 굴리기",
      savingsBody: "공개 표시 금리가 높은 저축 상품부터 비교합니다.",
      savingsAction: "저축 금리 비교",
      termTitle: "정해진 기간 수익 고정하기",
      termBody: "공개 표시 금리가 높은 GIC와 정기예금 상품부터 비교합니다.",
      termAction: "기간 상품 금리 비교",
      lowEntryTitle: "낮은 가입 금액부터 보기",
      lowEntryBody: "최소 잔액이나 예치금이 중요한 상품을 먼저 훑어봅니다.",
      lowEntryAction: "가입 금액 비교"
    },
    compare: {
      eyebrow: "나란히 비교",
      title: "최대 4개 상품 비교",
      subtitle: "상품 카드에서 선택해 제공된 공개 필드를 비교하세요.",
      select: "비교",
      selected: "선택됨",
      selectedCount: "{count}/{limit}개 선택",
      limit: "한 번에 최대 4개 상품까지 비교할 수 있습니다.",
      clear: "비우기",
      remove: "제거",
      emptyTitle: "아직 선택한 상품이 없습니다.",
      emptyBody: "상품 카드의 비교 버튼으로 표를 구성하세요. FPDS는 개인별 가입 가능성 점수나 신청 대행을 제공하지 않습니다.",
      tableProduct: "상품",
      tableWhy: "비교 이유",
      entryAmount: "가입 금액",
      application: "신청",
      officialPage: "공식 페이지",
      reasonNoMonthlyFee: "월 수수료가 0으로 공시되어 있습니다.",
      reasonFeeKnown: "월 수수료가 있어 비용을 직접 비교할 수 있습니다.",
      reasonRateKnown: "공개 표시 금리로 금리를 비교할 수 있습니다.",
      reasonTermRate: "기간과 공개 표시 금리가 모두 제공됩니다.",
      reasonLowEntry: "최소 잔액 또는 예치금으로 가입 비용을 비교할 수 있습니다.",
      reasonFallback: "비교 가능한 공개 필드가 제공됩니다."
    },
    methodology: {
      pageTitle: "FPDS 방법론",
      pageDescription: "공개 데이터 기준과 지표 경계입니다.",
      title: "방법론",
      description: "공개 스냅샷에 포함되는 정보, 제외되는 정보, 정보가 없을 때의 기준입니다.",
      sections: [
        {
          title: "스냅샷 기준",
          body: "공개 화면은 은행 페이지를 실시간으로 읽지 않고 최신 성공 집계 스냅샷을 사용합니다."
        },
        {
          title: "지표 포함 기준",
          body: "금리, 수수료, 금액, 기간은 승인된 공개 필드가 있을 때만 표시합니다."
        },
        {
          title: "상품 텍스트",
          body: "상품명과 원문에서 온 조건 문구는 출처 언어를 유지합니다."
        },
        {
          title: "증거 경계",
          body: "원문 증거, 출처 발췌, 내부 검토 trace는 FPDS에 공개하지 않습니다."
        }
      ]
    }
  },
  ja: {
    localeName: "日本語",
    shell: {
      brand: "FPDS",
      tagline: ""
    },
    nav: {
      dashboard: "ホーム",
      products: "預金",
      methodology: "データ基準",
      loan: "ローン",
      localeLabel: "言語"
    },
    common: {
      active: "有効",
      all: "すべて",
      applyFilters: "適用",
      clearAllFilters: "すべて解除",
      clearFilters: "解除",
      changedOn: "変更",
      noDate: "日付なし",
      noOptions: "選択肢なし",
      noRecentChange: "最近の変更なし",
      noSuccessfulSnapshot: "利用できる公開スナップショットはまだありません。",
      notDisclosed: "情報なし",
      bankPage: "銀行ページ",
      more: "もっと見る",
      open: "開く",
      pageLabel: "ページ",
      previous: "前へ",
      next: "次へ",
      verifiedOn: "確認"
    },
    grid: {
      pageTitle: "FPDS 預金",
      pageDescription: "カナダの当座、普通預金、GIC 商品を比較します。",
      title: "預金を比較",
      description: "最新の公開スナップショットにある当座、普通預金、GIC 商品です。",
      currentScope: "現在の範囲",
      compareDetails: "詳細比較",
      productCount: "{count} 件の商品",
      snapshotUpdated: "スナップショット {date}",
      primaryFilter: "主要",
      banks: "銀行",
      productTypes: "商品タイプ",
      targetTags: "顧客タグ",
      feeBucket: "手数料",
      minimumBalance: "最低残高",
      minimumDeposit: "最低預入額",
      termBucket: "期間",
      sortBy: "並び替え",
      direction: "方向",
      resultSummary: "結果",
      searchConditions: "検索条件",
      noActiveFilters: "すべての商品",
      noResultTitle: "現在の範囲に一致する商品はありません。",
      noResultBody: "フィルターを解除するか、ダッシュボードで広い市場を確認してください。",
      retryTitle: "商品を読み込めませんでした。",
      retryBody: "公開 API に接続できません。",
      retryButton: "商品を再読み込み",
      openDashboard: "ホーム",
      metricMonthlyFee: "月額手数料",
      metricMinBalance: "最低残高",
      metricMinDeposit: "最低預入額",
      metricDisplayRate: "表示金利",
      metricTerm: "期間",
      metricKeyDetail: "要点",
      metricLastChange: "最近の変更",
      metricRateNote: "金利メモ",
      ascending: "昇順",
      descending: "降順",
      sortDefault: "標準",
      sortDisplayRate: "表示金利",
      sortMonthlyFee: "月額手数料",
      sortMinimumBalance: "最低残高",
      sortMinimumDeposit: "最低預入額",
      sortLastChange: "最近の変更",
      sortBankName: "銀行",
      sortProductName: "商品",
    },
    detail: {
      backToList: "預金一覧に戻る",
      compareAtGlance: "比較の要点",
      decisionSummary: "判断サマリー",
      disclosureTitle: "重要な注記",
      keyConditions: "主な条件",
      officialPage: "銀行公式ページを開く",
      productFacts: "商品情報",
      similarProducts: "この銀行の他の商品",
      sourceLanguage: "ソース言語",
      termRates: "期間別金利",
      whatToCheck: "確認ポイント"
    },
    dashboard: {
      pageTitle: "FPDS ダッシュボード",
      pageDescription: "公開金融商品の比較スナップショットです。",
      title: "市場を見てから、商品を比較",
      description: "最新の公開スナップショットをもとに現在の掲載範囲をすばやく比較します。",
      marketGreeting: "最新の公開スナップショットで {banks} 行の預金商品 {products} 件を比較できます。",
      kpiSubtitle: "預金市場スナップショット",
      composition: "市場構成",
      compositionSubtitle: "現在のスナップショットにおける銀行別の預金商品比率です。",
      productsByBank: "銀行別商品",
      productsByType: "タイプ別商品",
      comparisonMap: "比較マップ",
      comparisonSubtitle: "商品タイプを 1 つ選ぶと同じ意味の軸で比較します。",
      coverageTable: "カバレッジ表",
      coverageSubtitle: "現在のスナップショットに含まれる公開商品です。",
      dataNotes: "データ基準",
      dataNotesBody: "指標は公開 aggregate フィールドを使います。必要な数値がない商品は該当比較から除外されます。",
      freshness: "鮮度",
      openProducts: "商品を開く",
      noActiveFilters: "有効なフィルターなし",
      noRankingWidgets: "現在の範囲で表示できる順位はありません。",
      chartUnavailable: "チャートに必要な商品数が不足しています。",
      chartSingleTypeHint: "商品タイプを 1 つ選ぶと比較マップを表示します。",
      visibleProducts: "表示商品",
      activeProducts: "有効商品",
      banksInScope: "銀行",
      peakRate: "最高金利",
      topInterestRateTitle: "金利トップ5",
      openInProducts: "商品で開く",
      apiUnavailableTitle: "ダッシュボードを読み込めませんでした。",
      apiUnavailableBody: "公開 aggregate API に接続できません。",
      retryDashboard: "ダッシュボードを再読み込み",
      mixedMarket: "全商品タイプ"
    },
    purpose: {
      eyebrow: "目的から始める",
      title: "何を比較しますか？",
      everydayTitle: "日常の銀行コストを抑える",
      everydayBody: "月額手数料が低い chequing 商品から比較します。",
      everydayAction: "低手数料口座を比較",
      savingsTitle: "表示金利で資金を増やす",
      savingsBody: "公開表示金利が高い savings 商品から比較します。",
      savingsAction: "預金金利を比較",
      termTitle: "固定期間のリターンを見る",
      termBody: "公開表示金利が高い GIC と term 商品から比較します。",
      termAction: "期間商品の金利を比較",
      lowEntryTitle: "少ない加入金額から見る",
      lowEntryBody: "最低残高や最低預入額が重要な商品を確認します。",
      lowEntryAction: "加入金額を比較"
    },
    compare: {
      eyebrow: "横並び比較",
      title: "最大4件の商品を比較",
      subtitle: "商品カードから選び、利用できる公開項目を比較します。",
      select: "比較",
      selected: "選択済み",
      selectedCount: "{count}/{limit} 件選択",
      limit: "一度に比較できる商品は最大4件です。",
      clear: "クリア",
      remove: "削除",
      emptyTitle: "まだ商品が選択されていません。",
      emptyBody: "商品カードの比較ボタンで表を作成します。FPDS は個人別の加入可能性スコアや申込代行を提供しません。",
      tableProduct: "商品",
      tableWhy: "比較理由",
      entryAmount: "加入金額",
      application: "申込",
      officialPage: "公式ページ",
      reasonNoMonthlyFee: "月額手数料がゼロとして公開されています。",
      reasonFeeKnown: "月額手数料があり、費用を直接比較できます。",
      reasonRateKnown: "公開表示金利で金利を比較できます。",
      reasonTermRate: "期間と公開表示金利の両方があります。",
      reasonLowEntry: "最低残高または最低預入額で加入コストを比較できます。",
      reasonFallback: "比較可能な公開フィールドがあります。"
    },
    methodology: {
      pageTitle: "FPDS データ基準",
      pageDescription: "公開データの基準と指標の境界です。",
      title: "データ基準",
      description: "公開スナップショットに含む情報、除外する情報、情報がない場合の扱いです。",
      sections: [
        {
          title: "スナップショット",
          body: "公開画面は銀行ページをリアルタイムで読まず、最新の成功集計スナップショットを使います。"
        },
        {
          title: "指標の対象",
          body: "金利、手数料、金額、期間は承認済みの公開項目がある場合だけ表示します。"
        },
        {
          title: "商品テキスト",
          body: "商品名とソース由来の条件文は元の言語のまま表示します。"
        },
        {
          title: "証拠の境界",
          body: "原文証拠、ソース抜粋、内部レビュー trace は FPDS では公開しません。"
        }
      ]
    }
  }
};

export function getPublicMessages(locale: string): PublicMessages {
  return PUBLIC_MESSAGES[normalizePublicLocale(locale)];
}

export function getPublicCatalogCopy(locale: string, catalog: "deposit" | "loan") {
  const copy = getPublicMessages(locale);
  if (catalog === "deposit") {
    return {
      pageDescription: copy.grid.pageDescription,
      pageTitle: copy.grid.pageTitle,
      title: copy.grid.title,
      description: copy.grid.description,
    };
  }
  if (normalizePublicLocale(locale) === "ko") {
    return {
      pageTitle: "FPDS 대출",
      pageDescription: "캐나다 대출 상품 카탈로그입니다.",
      title: "대출 상품",
      description: "최신 공개 스냅샷에서 활성 모기지, 개인 대출, 신용한도 대출 상품을 조회합니다.",
    };
  }
  if (normalizePublicLocale(locale) === "ja") {
    return {
      pageTitle: "FPDS ローン",
      pageDescription: "カナダのローン商品のカタログです。",
      title: "ローン商品",
      description: "最新の公開スナップショットから、有効な住宅ローン、個人ローン、ライン・オブ・クレジット商品を絞り込みます。",
    };
  }
  return {
    pageTitle: "FPDS Loan",
    pageDescription: "Compare Canadian mortgage, personal loan, and line of credit products.",
    title: "Compare loans",
    description: "Mortgage, personal loan, and line of credit products from the latest public snapshot.",
  };
}

export function normalizePublicLocale(locale: string): PublicLocale {
  return locale === "ko" || locale === "ja" ? locale : "en";
}

export function getIntlLocale(locale: string) {
  switch (normalizePublicLocale(locale)) {
    case "ko":
      return "ko-KR";
    case "ja":
      return "ja-JP";
    default:
      return "en-CA";
  }
}

export function formatPublicMessage(template: string, values: Record<string, string | number>) {
  return Object.entries(values).reduce((output, [key, value]) => output.replace(`{${key}}`, String(value)), template);
}
