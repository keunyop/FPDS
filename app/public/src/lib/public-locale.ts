export type PublicLocale = "en" | "ko" | "ja";

type PublicDesignCopy = {
  asOf: string;
  availableFacts: string;
  compareBoundary: string;
  compareDifferences: string;
  coverage: string;
  cardCoverage: string;
  depositCoverage: string;
  evidenceBoundary: string;
  fresh: string;
  freshness: string;
  homeBody: string;
  homeKicker: string;
  homeTitle: string;
  loanCoverage: string;
  methodologyIntro: string;
  methodologySteps: Array<{ body: string; label: string; title: string }>;
  monthlyPayment: string;
  officialRecord: string;
  publicSnapshot: string;
  recordPath: string;
  recordPathBody: string;
  reviewedRecord: string;
  securityRequirement: string;
  snapshotCoverage: string;
  sourceChecked: string;
  sourceLanguage: string;
  stale: string;
  unavailable: string;
  verified: string;
};

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
    card: string;
    localeLabel: string;
    primaryLabel: string;
    footerLabel: string;
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
    viewMode: string;
    gridView: string;
    listView: string;
    sortDisplayRate: string;
    sortAnnualFee: string;
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
    rateSnapshotsLabel: string;
    depositTopTitle: string;
    depositTopSubtitle: string;
    depositTopEmpty: string;
    depositTopUnavailable: string;
    moreDeposits: string;
    loanTopTitle: string;
    loanTopSubtitle: string;
    loanTopEmpty: string;
    loanTopUnavailable: string;
    moreLoans: string;
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
      brand: "Bankoompare",
      tagline: "Look into bank products. Compare the facts."
    },
    nav: {
      dashboard: "Home",
      products: "Deposits",
      methodology: "Methodology",
      loan: "Loans",
      card: "Credit cards",
      localeLabel: "Language",
      primaryLabel: "Main navigation",
      footerLabel: "Footer navigation"
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
      bankPage: "View at bank",
      more: "More",
      open: "Open",
      pageLabel: "Page",
      previous: "Previous",
      next: "Next",
      verifiedOn: "Verified"
    },
    grid: {
      pageTitle: "Deposits",
      pageDescription: "Look into chequing, savings, and GIC products across banks.",
      title: "Compare deposit products across banks",
      description: "Look into rates, fees, and entry requirements from the latest public snapshot.",
      currentScope: "Current scope",
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
      noResultBody: "Clear filters or return Home for a broader view.",
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
      viewMode: "View",
      gridView: "Grid view",
      listView: "List view",
      sortDisplayRate: "Interest rate",
      sortAnnualFee: "Annual fee",
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
      pageTitle: "Home",
      pageDescription: "Look into reviewed deposit, credit card, and loan facts across banks.",
      title: "Look into bank products. Compare what matters.",
      description: "",
      marketGreeting: "Compare {products} deposit products from {banks} banks in the latest public snapshot.",
      kpiSubtitle: "Deposit market snapshot",
      composition: "Market composition",
      compositionSubtitle: "Share of deposit products in the current snapshot.",
      productsByType: "Products by type",
      comparisonMap: "Comparison map",
      comparisonSubtitle: "Select one product type for a like-for-like chart.",
      coverageTable: "Coverage table",
      coverageSubtitle: "Public products currently represented in the snapshot.",
      dataNotes: "Data notes",
      dataNotesBody: "Metrics use public aggregate fields. Products missing required numeric values are excluded from affected comparisons.",
      freshness: "Freshness",
      openProducts: "Browse deposits",
      noActiveFilters: "No filters active.",
      noRankingWidgets: "No ranking is eligible for this scope.",
      chartUnavailable: "Not enough eligible products for this chart.",
      chartSingleTypeHint: "Choose one product type to unlock the comparison map.",
      visibleProducts: "Visible products",
      activeProducts: "active products",
      banksInScope: "Banks",
      peakRate: "Top Interest Rate",
      topInterestRateTitle: "Top 5 Interest Rate",
      rateSnapshotsLabel: "Deposit and loan rate snapshots",
      depositTopTitle: "Deposit Top 5",
      depositTopSubtitle: "Highest disclosed numeric rates. Fees, terms, and eligibility still apply.",
      depositTopEmpty: "No deposit products with a disclosed numeric rate are available in this scope.",
      depositTopUnavailable: "Deposit rates could not be loaded right now.",
      moreDeposits: "More deposits",
      loanTopTitle: "Loan Top 5",
      loanTopSubtitle: "Lowest disclosed numeric rates. Full terms and eligibility still apply.",
      loanTopEmpty: "No loan products with a disclosed numeric rate are available in this scope.",
      loanTopUnavailable: "Loan rates could not be loaded right now.",
      moreLoans: "More loans",
      openInProducts: "Open in products",
      apiUnavailableTitle: "Home could not load.",
      apiUnavailableBody: "The latest public snapshot is temporarily unavailable.",
      retryDashboard: "Try again",
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
      emptyBody: "Use Compare on any product card to compare published facts. Bankoompare does not score eligibility or submit applications.",
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
      pageTitle: "Methodology",
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
          body: "Raw evidence, source excerpts, and internal review traces are not exposed on Bankoompare."
        },
        {
          title: "Comparison and rankings",
          body: "Rankings use only eligible public numeric fields. Missing values are excluded, never estimated."
        },
        {
          title: "Freshness and verification",
          body: "Snapshot status shows when the public dataset was refreshed. Current rates and conditions must still be confirmed with the institution."
        }
      ]
    }
  },
  ko: {
    localeName: "한국어",
    shell: {
      brand: "Bankoompare",
      tagline: "은행 상품을 들여다보고, 사실을 비교하세요."
    },
    nav: {
      dashboard: "홈",
      products: "예금",
      methodology: "방법론",
      loan: "대출",
      card: "신용카드",
      localeLabel: "언어",
      primaryLabel: "주요 메뉴",
      footerLabel: "하단 메뉴"
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
      bankPage: "은행에서 보기",
      more: "더보기",
      open: "열기",
      pageLabel: "페이지",
      previous: "이전",
      next: "다음",
      verifiedOn: "검증"
    },
    grid: {
      pageTitle: "예금",
      pageDescription: "은행별 입출금, 저축, GIC 상품을 살펴보고 비교합니다.",
      title: "은행별 예금 상품 비교",
      description: "최신 공개 스냅샷에서 금리·수수료·가입 조건을 살펴보세요.",
      currentScope: "현재 범위",
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
      noResultBody: "필터를 해제하거나 홈에서 더 넓은 범위를 확인하세요.",
      retryTitle: "상품을 불러오지 못했습니다.",
      retryBody: "공개 API에 연결할 수 없습니다.",
      retryButton: "상품 다시 불러오기",
      openDashboard: "홈",
      metricMonthlyFee: "월 수수료",
      metricMinBalance: "최소 잔액",
      metricMinDeposit: "최소 예치금",
      metricDisplayRate: "금리",
      metricTerm: "기간",
      metricKeyDetail: "핵심 정보",
      metricLastChange: "최근 변경",
      metricRateNote: "금리 메모",
      ascending: "오름차순",
      descending: "내림차순",
      viewMode: "보기 방식",
      gridView: "그리드 보기",
      listView: "리스트 보기",
      sortDisplayRate: "금리",
      sortAnnualFee: "연회비",
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
      pageTitle: "홈",
      pageDescription: "여러 은행의 검토된 예금·신용카드·대출 정보를 살펴보고 비교합니다.",
      title: "은행 상품을 들여다보고, 중요한 차이를 비교하세요.",
      description: "",
      marketGreeting: "최신 공개 스냅샷에서 {banks}개 은행의 예금 상품 {products}개를 비교하세요.",
      kpiSubtitle: "예금 시장 스냅샷",
      composition: "시장 구성",
      compositionSubtitle: "현재 스냅샷의 은행별 예금 상품 비중입니다.",
      productsByType: "유형별 상품",
      comparisonMap: "비교 맵",
      comparisonSubtitle: "상품 유형 하나를 선택하면 같은 기준으로 비교합니다.",
      coverageTable: "커버리지 표",
      coverageSubtitle: "현재 스냅샷에 포함된 공개 상품입니다.",
      dataNotes: "데이터 기준",
      dataNotesBody: "지표는 공개 aggregate 필드를 사용하며, 필요한 숫자 값이 없는 상품은 해당 비교에서 제외됩니다.",
      freshness: "최신성",
      openProducts: "예금 둘러보기",
      noActiveFilters: "활성 필터 없음",
      noRankingWidgets: "현재 범위에서 표시할 순위가 없습니다.",
      chartUnavailable: "차트를 그릴 수 있는 상품 수가 부족합니다.",
      chartSingleTypeHint: "상품 유형 하나를 선택하면 비교 맵이 열립니다.",
      visibleProducts: "표시 상품",
      activeProducts: "활성 상품",
      banksInScope: "은행",
      peakRate: "최고 금리",
      topInterestRateTitle: "상위 5개 금리",
      rateSnapshotsLabel: "예금·대출 금리 비교",
      depositTopTitle: "예금 Top 5",
      depositTopSubtitle: "공개된 숫자 금리가 높은 순입니다. 수수료·기간·가입 조건도 확인하세요.",
      depositTopEmpty: "현재 범위에는 숫자 금리가 공개된 예금 상품이 없습니다.",
      depositTopUnavailable: "현재 예금 금리를 불러올 수 없습니다.",
      moreDeposits: "예금 더보기",
      loanTopTitle: "대출 Top 5",
      loanTopSubtitle: "공개된 숫자 금리가 낮은 순입니다. 전체 조건과 가입 요건도 확인하세요.",
      loanTopEmpty: "현재 범위에는 숫자 금리가 공개된 대출 상품이 없습니다.",
      loanTopUnavailable: "현재 대출 금리를 불러올 수 없습니다.",
      moreLoans: "대출 더보기",
      openInProducts: "상품에서 열기",
      apiUnavailableTitle: "홈을 불러오지 못했습니다.",
      apiUnavailableBody: "최신 공개 스냅샷을 일시적으로 불러올 수 없습니다.",
      retryDashboard: "다시 시도",
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
      emptyBody: "상품 카드의 비교 버튼으로 공개된 정보를 나란히 보세요. Bankoompare는 가입 가능성 점수나 신청 대행을 제공하지 않습니다.",
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
      pageTitle: "방법론",
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
          body: "원문 증거, 출처 발췌, 내부 검토 이력은 Bankoompare에 공개하지 않습니다."
        },
        {
          title: "비교와 순위",
          body: "순위는 조건을 충족한 공개 숫자 필드만 사용합니다. 없는 값은 추정하지 않고 비교에서 제외합니다."
        },
        {
          title: "최신성과 재확인",
          body: "스냅샷 상태는 공개 데이터가 갱신된 시점을 보여줍니다. 현재 금리와 조건은 금융기관에서 다시 확인해야 합니다."
        }
      ]
    }
  },
  ja: {
    localeName: "日本語",
    shell: {
      brand: "Bankoompare",
      tagline: "銀行商品を見比べて、事実を比較。"
    },
    nav: {
      dashboard: "ホーム",
      products: "預金",
      methodology: "データ基準",
      loan: "ローン",
      card: "クレジットカード",
      localeLabel: "言語",
      primaryLabel: "メインナビゲーション",
      footerLabel: "フッターナビゲーション"
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
      bankPage: "銀行サイトで見る",
      more: "もっと見る",
      open: "開く",
      pageLabel: "ページ",
      previous: "前へ",
      next: "次へ",
      verifiedOn: "確認"
    },
    grid: {
      pageTitle: "預金",
      pageDescription: "銀行ごとの当座、普通預金、GIC 商品を見比べます。",
      title: "銀行ごとに預金商品を比較",
      description: "最新の公開スナップショットで金利・手数料・利用条件を確認できます。",
      currentScope: "現在の範囲",
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
      noResultBody: "フィルターを解除するか、ホームでより広い範囲を確認してください。",
      retryTitle: "商品を読み込めませんでした。",
      retryBody: "公開 API に接続できません。",
      retryButton: "商品を再読み込み",
      openDashboard: "ホーム",
      metricMonthlyFee: "月額手数料",
      metricMinBalance: "最低残高",
      metricMinDeposit: "最低預入額",
      metricDisplayRate: "金利",
      metricTerm: "期間",
      metricKeyDetail: "要点",
      metricLastChange: "最近の変更",
      metricRateNote: "金利メモ",
      ascending: "昇順",
      descending: "降順",
      viewMode: "表示方法",
      gridView: "グリッド表示",
      listView: "リスト表示",
      sortDisplayRate: "金利",
      sortAnnualFee: "年会費",
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
      pageTitle: "ホーム",
      pageDescription: "複数の銀行の確認済み預金・クレジットカード・ローン情報を見比べます。",
      title: "銀行商品を見比べて、大切な違いを確かめる。",
      description: "",
      marketGreeting: "最新の公開スナップショットで {banks} 行の預金商品 {products} 件を比較できます。",
      kpiSubtitle: "預金市場スナップショット",
      composition: "市場構成",
      compositionSubtitle: "現在のスナップショットにおける銀行別の預金商品比率です。",
      productsByType: "タイプ別商品",
      comparisonMap: "比較マップ",
      comparisonSubtitle: "商品タイプを 1 つ選ぶと同じ意味の軸で比較します。",
      coverageTable: "カバレッジ表",
      coverageSubtitle: "現在のスナップショットに含まれる公開商品です。",
      dataNotes: "データ基準",
      dataNotesBody: "指標は公開 aggregate フィールドを使います。必要な数値がない商品は該当比較から除外されます。",
      freshness: "鮮度",
      openProducts: "預金を見る",
      noActiveFilters: "有効なフィルターなし",
      noRankingWidgets: "現在の範囲で表示できる順位はありません。",
      chartUnavailable: "チャートに必要な商品数が不足しています。",
      chartSingleTypeHint: "商品タイプを 1 つ選ぶと比較マップを表示します。",
      visibleProducts: "表示商品",
      activeProducts: "有効商品",
      banksInScope: "銀行",
      peakRate: "最高金利",
      topInterestRateTitle: "金利トップ5",
      rateSnapshotsLabel: "預金・ローン金利比較",
      depositTopTitle: "預金 Top 5",
      depositTopSubtitle: "公開された数値金利が高い順です。手数料・期間・利用条件も確認してください。",
      depositTopEmpty: "現在の範囲には数値金利が公開された預金商品がありません。",
      depositTopUnavailable: "現在、預金金利を読み込めません。",
      moreDeposits: "預金をもっと見る",
      loanTopTitle: "ローン Top 5",
      loanTopSubtitle: "公開された数値金利が低い順です。条件全体と利用要件も確認してください。",
      loanTopEmpty: "現在の範囲には数値金利が公開されたローン商品がありません。",
      loanTopUnavailable: "現在、ローン金利を読み込めません。",
      moreLoans: "ローンをもっと見る",
      openInProducts: "商品で開く",
      apiUnavailableTitle: "ホームを読み込めませんでした。",
      apiUnavailableBody: "最新の公開スナップショットを一時的に読み込めません。",
      retryDashboard: "もう一度試す",
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
      emptyBody: "商品カードの比較ボタンで公開情報を並べて確認できます。Bankoompare は加入可能性の採点や申込代行を行いません。",
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
      pageTitle: "データ基準",
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
          body: "原文証拠、ソース抜粋、内部レビュー履歴は Bankoompare では公開しません。"
        },
        {
          title: "比較とランキング",
          body: "ランキングは対象となる公開数値項目だけを使います。欠損値は推定せず、比較から除外します。"
        },
        {
          title: "鮮度と再確認",
          body: "スナップショット状態は公開データの更新時点を示します。現在の金利と条件は金融機関で再確認してください。"
        }
      ]
    }
  }
};

const PUBLIC_DESIGN_COPY: Record<PublicLocale, PublicDesignCopy> = {
  en: {
    asOf: "As of",
    availableFacts: "Available product facts",
    compareBoundary: "Bankoompare compares published facts. It does not choose a product for you.",
    compareDifferences: "Differences are emphasized only where a public field is available.",
    coverage: "Current coverage",
    cardCoverage: "Credit cards",
    depositCoverage: "Chequing, savings and GIC",
    evidenceBoundary: "Raw evidence and internal review traces stay private.",
    fresh: "Current snapshot",
    freshness: "Snapshot freshness",
    homeBody: "Compare reviewed rates, fees, and key terms across banks—then confirm the latest details with the bank.",
    homeKicker: "Reviewed public product data",
    homeTitle: "Look into bank products. Compare what matters.",
    loanCoverage: "Mortgage, personal loan and line of credit",
    methodologyIntro: "How official product facts become comparable public records—and where Bankoompare stops.",
    methodologySteps: [
      { label: "01", title: "Official source", body: "Product facts begin with public institution sources." },
      { label: "02", title: "Reviewed record", body: "Only approved public fields enter the comparable product record." },
      { label: "03", title: "Public snapshot", body: "The latest successful aggregate snapshot powers every public view." },
      { label: "04", title: "Your verification", body: "Rates and conditions can change. Recheck the institution page before acting." }
    ],
    monthlyPayment: "Monthly payment",
    officialRecord: "Official product record",
    publicSnapshot: "Public snapshot",
    recordPath: "From source to shortlist",
    recordPathBody: "Every visible comparison follows the same bounded record path.",
    reviewedRecord: "Reviewed fields",
    securityRequirement: "Security requirement",
    snapshotCoverage: "products across",
    sourceChecked: "Official page available",
    sourceLanguage: "Source language",
    stale: "Snapshot needs refresh",
    unavailable: "Snapshot unavailable",
    verified: "Verified record"
  },
  ko: {
    asOf: "기준일",
    availableFacts: "확인 가능한 상품 정보",
    compareBoundary: "Bankoompare는 공개된 사실을 비교하며, 사용자 대신 상품을 선택하지 않습니다.",
    compareDifferences: "공개 필드가 있는 항목만 차이를 강조합니다.",
    coverage: "현재 제공 범위",
    cardCoverage: "신용카드",
    depositCoverage: "입출금·저축·GIC",
    evidenceBoundary: "원문 증거와 내부 검토 이력은 공개하지 않습니다.",
    fresh: "최신 스냅샷",
    freshness: "스냅샷 최신성",
    homeBody: "여러 은행의 검토된 금리·수수료·핵심 조건을 한곳에서 비교하고, 최신 정보는 은행에서 확인하세요.",
    homeKicker: "검토된 공개 상품 데이터",
    homeTitle: "은행 상품을 들여다보고, 중요한 차이를 비교하세요.",
    loanCoverage: "모기지·개인대출·신용한도",
    methodologyIntro: "공식 상품 정보가 비교 가능한 공개 기록이 되는 과정과 Bankoompare의 정보 제공 경계입니다.",
    methodologySteps: [
      { label: "01", title: "공식 출처", body: "금융기관이 공개한 상품 정보에서 기록이 시작됩니다." },
      { label: "02", title: "검토된 기록", body: "승인된 공개 필드만 비교 가능한 상품 기록에 포함됩니다." },
      { label: "03", title: "공개 스냅샷", body: "가장 최근 성공한 집계 스냅샷이 모든 공개 화면에 사용됩니다." },
      { label: "04", title: "사용자 재확인", body: "금리와 조건은 바뀔 수 있으므로 결정 전 공식 페이지를 다시 확인합니다." }
    ],
    monthlyPayment: "월 납입액",
    officialRecord: "공식 상품 기록",
    publicSnapshot: "공개 스냅샷",
    recordPath: "출처에서 후보 목록까지",
    recordPathBody: "모든 비교 정보는 같은 제한된 기록 경로를 따릅니다.",
    reviewedRecord: "검토된 필드",
    securityRequirement: "담보 조건",
    snapshotCoverage: "개 상품 ·",
    sourceChecked: "공식 페이지 확인 가능",
    sourceLanguage: "원문 언어",
    stale: "갱신 필요",
    unavailable: "스냅샷 없음",
    verified: "검증된 기록"
  },
  ja: {
    asOf: "基準日",
    availableFacts: "確認できる商品情報",
    compareBoundary: "Bankoompare は公開された事実を比較し、利用者の代わりに商品を選びません。",
    compareDifferences: "公開項目がある場合だけ差を強調します。",
    coverage: "現在の掲載範囲",
    cardCoverage: "クレジットカード",
    depositCoverage: "当座・普通預金・GIC",
    evidenceBoundary: "原文証拠と内部レビュー履歴は公開しません。",
    fresh: "最新スナップショット",
    freshness: "スナップショットの鮮度",
    homeBody: "複数の銀行の確認済み金利・手数料・主な条件をひとつの場所で比べ、最新情報は銀行で確認してください。",
    homeKicker: "レビュー済み公開商品データ",
    homeTitle: "銀行商品を見比べて、大切な違いを確かめる。",
    loanCoverage: "住宅ローン・個人ローン・与信枠",
    methodologyIntro: "公式商品情報が比較可能な公開レコードになる流れと、Bankoompare の情報提供範囲です。",
    methodologySteps: [
      { label: "01", title: "公式ソース", body: "金融機関が公開した商品情報からレコードが始まります。" },
      { label: "02", title: "レビュー済みレコード", body: "承認された公開項目だけが比較可能な商品レコードに入ります。" },
      { label: "03", title: "公開スナップショット", body: "最新の成功集計スナップショットがすべての公開画面を支えます。" },
      { label: "04", title: "利用者の再確認", body: "金利や条件は変わるため、判断前に公式ページで再確認します。" }
    ],
    monthlyPayment: "月々の支払額",
    officialRecord: "公式商品レコード",
    publicSnapshot: "公開スナップショット",
    recordPath: "ソースから候補まで",
    recordPathBody: "すべての比較情報は同じ限定されたレコード経路を通ります。",
    reviewedRecord: "レビュー済み項目",
    securityRequirement: "担保条件",
    snapshotCoverage: "商品・",
    sourceChecked: "公式ページを確認可能",
    sourceLanguage: "ソース言語",
    stale: "更新が必要",
    unavailable: "スナップショットなし",
    verified: "検証済みレコード"
  }
};

export function getPublicMessages(locale: string): PublicMessages {
  return PUBLIC_MESSAGES[normalizePublicLocale(locale)];
}

export function getPublicDesignCopy(locale: string): PublicDesignCopy {
  return PUBLIC_DESIGN_COPY[normalizePublicLocale(locale)];
}

export function getPublicCatalogCopy(locale: string, catalog: "deposit" | "card" | "loan") {
  const copy = getPublicMessages(locale);
  const designCopy = getPublicDesignCopy(locale);
  if (catalog === "deposit") {
    return {
      pageDescription: copy.grid.pageDescription,
      pageTitle: copy.grid.pageTitle,
      title: copy.grid.title,
      description: copy.grid.description,
      coverage: designCopy.depositCoverage,
    };
  }
  if (catalog === "card") {
    if (normalizePublicLocale(locale) === "ko") {
      return {
        pageTitle: "신용카드",
        pageDescription: "은행별 검증된 신용카드 상품을 살펴보고 비교합니다.",
        title: "은행별 신용카드 비교",
        description: "최신 공개 스냅샷에서 연회비와 구매 금리를 살펴보세요.",
        coverage: designCopy.cardCoverage,
      };
    }
    if (normalizePublicLocale(locale) === "ja") {
      return {
        pageTitle: "クレジットカード",
        pageDescription: "銀行ごとの確認済みクレジットカード商品を見比べます。",
        title: "銀行ごとにクレジットカードを比較",
        description: "最新の公開スナップショットで年会費とショッピング金利を確認できます。",
        coverage: designCopy.cardCoverage,
      };
    }
    return {
      pageTitle: "Credit Cards",
      pageDescription: "Look into verified credit card products across banks.",
      title: "Compare credit cards across banks",
      description: "Look into annual fees and purchase interest rates from the latest public snapshot.",
      coverage: designCopy.cardCoverage,
    };
  }
  if (normalizePublicLocale(locale) === "ko") {
    return {
      pageTitle: "대출",
      pageDescription: "은행별 모기지·개인대출·신용한도 상품을 살펴보고 비교합니다.",
      title: "은행별 대출 상품 비교",
      description: "최신 공개 스냅샷에서 금리와 주요 대출 조건을 살펴보세요.",
      coverage: designCopy.loanCoverage,
    };
  }
  if (normalizePublicLocale(locale) === "ja") {
    return {
      pageTitle: "ローン",
      pageDescription: "銀行ごとの住宅ローン・個人ローン・与信枠商品を見比べます。",
      title: "銀行ごとにローン商品を比較",
      description: "最新の公開スナップショットで金利と主なローン条件を確認できます。",
      coverage: designCopy.loanCoverage,
    };
  }
  return {
    pageTitle: "Loans",
    pageDescription: "Look into mortgage, personal loan, and line of credit products across banks.",
    title: "Compare loans across banks",
    description: "Look into interest rates and key loan terms from the latest public snapshot.",
    coverage: designCopy.loanCoverage,
  };
}

export function normalizePublicLocale(locale: string): PublicLocale {
  return locale === "ko" || locale === "ja" ? locale : "en";
}

type PublicDiscoveryCopy = {
  allProductsLoaded: string;
  loadMoreError: string;
  loadingMore: string;
  retryLoadMore: string;
  searchChip: string;
  searchLabel: string;
  searchPlaceholder: string;
  updatingResults: string;
};

type PublicInformationNoticeCopy = {
  paragraphs: string[];
  title: string;
};

const PUBLIC_DISCOVERY_COPY: Record<PublicLocale, PublicDiscoveryCopy> = {
  en: {
    allProductsLoaded: "All {count} products are loaded.",
    loadMoreError: "More products could not be loaded.",
    loadingMore: "Loading more products…",
    retryLoadMore: "Try again",
    searchChip: "Search: {query}",
    searchLabel: "Search bank or product",
    searchPlaceholder: "Bank or product name",
    updatingResults: "Updating results…"
  },
  ko: {
    allProductsLoaded: "상품 {count}개를 모두 불러왔습니다.",
    loadMoreError: "추가 상품을 불러오지 못했습니다.",
    loadingMore: "상품을 더 불러오는 중…",
    retryLoadMore: "다시 시도",
    searchChip: "검색: {query}",
    searchLabel: "은행 또는 상품 검색",
    searchPlaceholder: "은행명 또는 상품명",
    updatingResults: "검색 결과를 반영하는 중…"
  },
  ja: {
    allProductsLoaded: "全{count}商品を読み込みました。",
    loadMoreError: "追加の商品を読み込めませんでした。",
    loadingMore: "商品をさらに読み込み中…",
    retryLoadMore: "再試行",
    searchChip: "検索: {query}",
    searchLabel: "銀行または商品を検索",
    searchPlaceholder: "銀行名または商品名",
    updatingResults: "検索結果を更新中…"
  }
};

const PUBLIC_INFORMATION_NOTICE_COPY: Record<PublicLocale, PublicInformationNoticeCopy> = {
  en: {
    title: "Information notice",
    paragraphs: [
      "The information on this page is collected and organized from public sources with the help of AI agents. It is not a financial product advertisement.",
      "Bankoompare independently created this content for information purposes without compensation from the financial institutions shown, and works to keep it current.",
      "Rates, fees, eligibility, and other terms may change by the time you apply. Before applying, confirm the product information and conditions on the financial institution’s official website."
    ]
  },
  ko: {
    title: "정보 이용 안내",
    paragraphs: [
      "본 페이지의 정보는 AI 에이전트를 활용해 공개 자료를 수집·정리한 것으로, 금융상품 광고가 아닙니다.",
      "표시된 금융회사와의 대가 관계 없이 정보 제공을 목적으로 자체 제작했으며, 최신 정보 반영을 위해 노력하고 있습니다.",
      "금리·수수료·가입 조건 등은 신청 시점에 달라질 수 있습니다. 신청 전 해당 금융회사의 공식 홈페이지에서 상품 정보와 이용 조건을 반드시 다시 확인해 주세요."
    ]
  },
  ja: {
    title: "情報利用に関するご案内",
    paragraphs: [
      "本ページの情報は、AI エージェントを活用して公開資料を収集・整理したもので、金融商品の広告ではありません。",
      "掲載する金融機関から対価を受けず、情報提供を目的として独自に作成しており、最新情報の反映に努めています。",
      "金利・手数料・申込条件などは申込時点で変わる場合があります。申込前に、金融機関の公式サイトで商品情報と利用条件を必ず再確認してください。"
    ]
  }
};

export function getPublicDiscoveryCopy(locale: string): PublicDiscoveryCopy {
  return PUBLIC_DISCOVERY_COPY[normalizePublicLocale(locale)];
}

export function getPublicInformationNotice(locale: string): PublicInformationNoticeCopy {
  return PUBLIC_INFORMATION_NOTICE_COPY[normalizePublicLocale(locale)];
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
