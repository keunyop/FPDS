export type PublicLocale = "en" | "ko" | "ja";

type PublicMessages = {
  localeName: string;
  shell: {
    brand: string;
    tagline: string;
  };
  nav: {
    products: string;
    dashboard: string;
    localeLabel: string;
  };
  common: {
    applyFilters: string;
    clearFilters: string;
    clearAllFilters: string;
    previous: string;
    next: string;
    all: string;
    noDate: string;
    noRecentChange: string;
    noSuccessfulSnapshot: string;
    notDisclosed: string;
    noOptions: string;
    sourceLanguage: string;
    verifiedOn: string;
    changedOn: string;
    pageLabel: string;
  };
  grid: {
    pageTitle: string;
    pageDescription: string;
    eyebrow: string;
    title: string;
    description: string;
    currentScope: string;
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
    filterHint: string;
    resultSummary: string;
    noActiveFilters: string;
    noResultEyebrow: string;
    noResultTitle: string;
    noResultBody: string;
    retryTitle: string;
    retryBody: string;
    retryButton: string;
    openDashboard: string;
    goToDashboard: string;
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
  dashboard: {
    pageTitle: string;
    pageDescription: string;
    eyebrow: string;
    title: string;
    description: string;
    scopeSummary: string;
    scopeTitle: string;
    noActiveFilters: string;
    adjustScope: string;
    clearScope: string;
    rankingWidgets: string;
    rankingTitle: string;
    rankingDescription: string;
    insufficientData: string;
    noRankingWidgets: string;
    breakdownByBank: string;
    breakdownByBankDescription: string;
    breakdownByType: string;
    breakdownByTypeDescription: string;
    comparativeChart: string;
    chartTitleFallback: string;
    chartDescription: string;
    interpretation: string;
    visiblePoints: string;
    openInGrid: string;
    methodology: string;
    methodologyTitle: string;
    freshness: string;
    freshnessTitle: string;
    openProductGrid: string;
    retryDashboard: string;
    apiUnavailableTitle: string;
    apiUnavailableBody: string;
    mixedMarket: string;
    peakRate: string;
    selectOneProductType: string;
    singleTypeOnly: string;
    chartInsufficient: string;
    resetDashboardScope: string;
    morePoints: string;
    productsAcrossBanks: string;
    activeProducts: string;
    topComparisons: string;
    rankedBy: string;
    trailingDays: string;
    noRecentChangeDate: string;
    noProductsInScope: string;
  };
};

const PUBLIC_MESSAGES: Record<PublicLocale, PublicMessages> = {
  en: {
    localeName: "English",
    shell: {
      brand: "FPDS Public",
      tagline: "Canada deposit product catalog and comparison surface"
    },
    nav: {
      products: "Products",
      dashboard: "Insights",
      localeLabel: "Language"
    },
    common: {
      applyFilters: "Apply filters",
      clearFilters: "Clear filters",
      clearAllFilters: "Clear all filters",
      previous: "Previous",
      next: "Next",
      all: "All",
      noDate: "No date",
      noRecentChange: "No recent change timestamp",
      noSuccessfulSnapshot: "No successful aggregate snapshot is available yet.",
      notDisclosed: "Not disclosed",
      noOptions: "No options available yet.",
      sourceLanguage: "Source language",
      verifiedOn: "Verified",
      changedOn: "Changed",
      pageLabel: "Page"
    },
    grid: {
      pageTitle: "FPDS Public Products",
      pageDescription: "Locale-aware public product grid for Canada deposit products.",
      eyebrow: "WBS 5.12 Locale Rollout",
      title: "Compare Canada deposit products with one shared public filter vocabulary.",
      description:
        "Browse active chequing, savings, and GIC products from the latest successful aggregate snapshot. Product names stay source-derived, while labels, bucket filters, and freshness notes stay UI-owned.",
      currentScope: "Current scope",
      primaryFilter: "Primary filter",
      banks: "Banks",
      productTypes: "Product types",
      targetTags: "Target tags",
      feeBucket: "Fee bucket",
      minimumBalance: "Minimum balance",
      minimumDeposit: "Minimum deposit",
      termBucket: "Term bucket",
      sortBy: "Sort by",
      direction: "Direction",
      filterHint: "Apply filters to refresh the grid. Pagination resets to page one when scope changes.",
      resultSummary: "Result summary",
      noActiveFilters: "No active filters. You are viewing the full public Canada scope.",
      noResultEyebrow: "No result",
      noResultTitle: "No products matched the current filter scope.",
      noResultBody: "Clear the active chips or move to the insight dashboard if you want a higher-level market view for this slice.",
      retryTitle: "Product Grid could not load because the public aggregate API is not reachable.",
      retryBody: "Start the FastAPI service and refresh this page. The public Product Grid depends on `GET /api/public/products` and `GET /api/public/filters`.",
      retryButton: "Retry Product Grid",
      openDashboard: "Open insight dashboard",
      goToDashboard: "Go to insight dashboard",
      metricMonthlyFee: "Monthly fee",
      metricMinBalance: "Min. balance",
      metricMinDeposit: "Min. deposit",
      metricDisplayRate: "Display rate",
      metricTerm: "Term",
      metricKeyDetail: "Key detail",
      metricLastChange: "Last change",
      metricRateNote: "Rate note",
      ascending: "Ascending",
      descending: "Descending",
      sortDefault: "Default order",
      sortDisplayRate: "Display rate",
      sortMonthlyFee: "Monthly fee",
      sortMinimumBalance: "Minimum balance",
      sortMinimumDeposit: "Minimum deposit",
      sortLastChange: "Last change",
      sortBankName: "Bank name",
      sortProductName: "Product name"
    },
    dashboard: {
      pageTitle: "FPDS Insight Dashboard",
      pageDescription: "Locale-aware public insight dashboard for Canada deposit products.",
      eyebrow: "WBS 5.12 Locale Rollout",
      title: "Read the Canada deposit market at a glance before diving back into product-level detail.",
      description:
        "The dashboard uses the same public filter vocabulary as the Product Grid, but reframes the current scope through KPI cards, composition views, ranking widgets, and a comparative chart when one product type is in focus.",
      scopeSummary: "Scope summary",
      scopeTitle: "Dashboarding the current public filter scope",
      noActiveFilters: "No active filters. You are reading the full Canada public dashboard scope.",
      adjustScope: "Adjust scope on product grid",
      clearScope: "Clear scope",
      rankingWidgets: "Ranking widgets",
      rankingTitle: "Top comparisons for this scope",
      rankingDescription:
        "Widget order follows the approved product-type emphasis rules and only renders when enough eligible products remain. Each row can reopen the Product Grid with a narrowed matching scope.",
      insufficientData: "Insufficient data",
      noRankingWidgets: "No ranking widgets are eligible for the current scope.",
      breakdownByBank: "Products by bank",
      breakdownByBankDescription: "Composition of active products in the current scope.",
      breakdownByType: "Products by product type",
      breakdownByTypeDescription: "Mix of chequing, savings, and GIC exposure after filtering.",
      comparativeChart: "Comparative chart",
      chartTitleFallback: "Comparative chart unlocks when one product type is in focus",
      chartDescription: "When exactly one product type is selected, the dashboard can compare trade-offs within that meaningfully similar scope.",
      interpretation: "Interpretation",
      visiblePoints: "Visible points",
      openInGrid: "Open in grid",
      methodology: "Methodology",
      methodologyTitle: "How to read this dashboard",
      freshness: "Freshness",
      freshnessTitle: "Snapshot handling",
      openProductGrid: "Open product grid with this scope",
      retryDashboard: "Retry dashboard",
      apiUnavailableTitle: "Insight Dashboard could not load because the public aggregate API is not reachable.",
      apiUnavailableBody:
        "Start the FastAPI service and refresh this page. The public dashboard depends on `GET /api/public/dashboard-summary`, `GET /api/public/dashboard-rankings`, `GET /api/public/dashboard-scatter`, and `GET /api/public/filters`.",
      mixedMarket: "Mixed market",
      peakRate: "Peak rate",
      selectOneProductType: "Select one product type",
      singleTypeOnly: "Comparative plotting is reserved for single-type scope.",
      chartInsufficient: "There are not enough eligible products to render this chart.",
      resetDashboardScope: "Reset dashboard scope",
      morePoints: "more points in the chart.",
      productsAcrossBanks: "active products across {banks} banks",
      activeProducts: "active products",
      topComparisons: "Top {count}",
      rankedBy: "Ranked by",
      trailingDays: "over the trailing {days} days.",
      noRecentChangeDate: "No recent change date",
      noProductsInScope: "No products are available in the current scope."
    }
  },
  ko: {
    localeName: "한국어",
    shell: {
      brand: "FPDS 공개 화면",
      tagline: "캐나다 예금 상품 카탈로그 및 비교 화면"
    },
    nav: {
      products: "상품",
      dashboard: "인사이트",
      localeLabel: "언어"
    },
    common: {
      applyFilters: "필터 적용",
      clearFilters: "필터 초기화",
      clearAllFilters: "모든 필터 초기화",
      previous: "이전",
      next: "다음",
      all: "전체",
      noDate: "날짜 없음",
      noRecentChange: "최근 변경 시각 없음",
      noSuccessfulSnapshot: "아직 성공한 집계 스냅샷이 없습니다.",
      notDisclosed: "공개되지 않음",
      noOptions: "아직 선택 가능한 항목이 없습니다.",
      sourceLanguage: "원문 언어",
      verifiedOn: "검증일",
      changedOn: "변경일",
      pageLabel: "페이지"
    },
    grid: {
      pageTitle: "FPDS 공개 상품",
      pageDescription: "캐나다 예금 상품을 위한 로케일 지원 공개 상품 그리드입니다.",
      eyebrow: "WBS 5.12 Locale 적용",
      title: "공통 공개 필터 체계로 캐나다 예금 상품을 비교하세요.",
      description:
        "최신 성공 집계 스냅샷을 기준으로 활성화된 입출금, 저축, GIC 상품을 탐색할 수 있습니다. 상품명은 원문을 유지하고, 라벨·버킷 필터·신선도 안내는 UI 리소스로 제공합니다.",
      currentScope: "현재 범위",
      primaryFilter: "주요 필터",
      banks: "은행",
      productTypes: "상품 유형",
      targetTags: "대상 태그",
      feeBucket: "수수료 구간",
      minimumBalance: "최소 잔액",
      minimumDeposit: "최소 예치금",
      termBucket: "기간 구간",
      sortBy: "정렬 기준",
      direction: "정렬 방향",
      filterHint: "필터를 적용하면 그리드가 새로고침됩니다. 범위가 바뀌면 페이지는 1로 돌아갑니다.",
      resultSummary: "결과 요약",
      noActiveFilters: "활성 필터가 없습니다. 캐나다 전체 공개 범위를 보고 있습니다.",
      noResultEyebrow: "결과 없음",
      noResultTitle: "현재 필터 범위와 일치하는 상품이 없습니다.",
      noResultBody: "활성 칩을 지우거나 더 상위 시장 관점을 보려면 인사이트 대시보드로 이동하세요.",
      retryTitle: "공개 집계 API에 연결할 수 없어 상품 그리드를 불러오지 못했습니다.",
      retryBody: "FastAPI 서비스를 시작한 뒤 이 페이지를 새로고침하세요. 공개 상품 그리드는 `GET /api/public/products` 와 `GET /api/public/filters` 에 의존합니다.",
      retryButton: "상품 그리드 다시 시도",
      openDashboard: "인사이트 대시보드 열기",
      goToDashboard: "인사이트 대시보드로 이동",
      metricMonthlyFee: "월 수수료",
      metricMinBalance: "최소 잔액",
      metricMinDeposit: "최소 예치금",
      metricDisplayRate: "표시 금리",
      metricTerm: "기간",
      metricKeyDetail: "핵심 포인트",
      metricLastChange: "최근 변경",
      metricRateNote: "금리 메모",
      ascending: "오름차순",
      descending: "내림차순",
      sortDefault: "기본 순서",
      sortDisplayRate: "표시 금리",
      sortMonthlyFee: "월 수수료",
      sortMinimumBalance: "최소 잔액",
      sortMinimumDeposit: "최소 예치금",
      sortLastChange: "최근 변경",
      sortBankName: "은행명",
      sortProductName: "상품명"
    },
    dashboard: {
      pageTitle: "FPDS 인사이트 대시보드",
      pageDescription: "캐나다 예금 상품을 위한 로케일 지원 공개 인사이트 대시보드입니다.",
      eyebrow: "WBS 5.12 Locale 적용",
      title: "상품 세부 비교로 돌아가기 전에 캐나다 예금 시장을 한눈에 읽어보세요.",
      description:
        "이 대시보드는 Product Grid와 같은 공개 필터 체계를 사용하지만, 현재 범위를 KPI 카드, 구성 비율, 랭킹 위젯, 단일 상품 유형 비교 차트로 다시 보여줍니다.",
      scopeSummary: "범위 요약",
      scopeTitle: "현재 공개 필터 범위 대시보드",
      noActiveFilters: "활성 필터가 없습니다. 캐나다 전체 공개 대시보드 범위를 보고 있습니다.",
      adjustScope: "상품 그리드에서 범위 조정",
      clearScope: "범위 초기화",
      rankingWidgets: "랭킹 위젯",
      rankingTitle: "현재 범위의 상위 비교",
      rankingDescription: "위젯 순서는 승인된 상품 유형 우선순위를 따르며, 충분한 데이터가 있을 때만 표시됩니다. 각 행은 더 좁은 범위의 Product Grid를 다시 열 수 있습니다.",
      insufficientData: "데이터 부족",
      noRankingWidgets: "현재 범위에서 표시 가능한 랭킹 위젯이 없습니다.",
      breakdownByBank: "은행별 상품 수",
      breakdownByBankDescription: "현재 범위에서 활성 상품이 은행별로 어떻게 구성되는지 보여줍니다.",
      breakdownByType: "상품 유형별 상품 수",
      breakdownByTypeDescription: "필터 적용 후 입출금, 저축, GIC 비중을 보여줍니다.",
      comparativeChart: "비교 차트",
      chartTitleFallback: "상품 유형 하나를 선택하면 비교 차트가 열립니다",
      chartDescription: "정확히 한 개의 상품 유형을 선택했을 때만 의미가 비슷한 범위 안에서 트레이드오프를 비교할 수 있습니다.",
      interpretation: "해석 가이드",
      visiblePoints: "표시 중인 포인트",
      openInGrid: "그리드에서 열기",
      methodology: "방법론",
      methodologyTitle: "이 대시보드 읽는 법",
      freshness: "신선도",
      freshnessTitle: "스냅샷 처리",
      openProductGrid: "이 범위로 상품 그리드 열기",
      retryDashboard: "대시보드 다시 시도",
      apiUnavailableTitle: "공개 집계 API에 연결할 수 없어 인사이트 대시보드를 불러오지 못했습니다.",
      apiUnavailableBody:
        "FastAPI 서비스를 시작한 뒤 이 페이지를 새로고침하세요. 공개 대시보드는 `GET /api/public/dashboard-summary`, `GET /api/public/dashboard-rankings`, `GET /api/public/dashboard-scatter`, `GET /api/public/filters` 에 의존합니다.",
      mixedMarket: "혼합 시장",
      peakRate: "최고 금리",
      selectOneProductType: "상품 유형 1개 선택",
      singleTypeOnly: "비교 차트는 단일 상품 유형 범위에서만 제공됩니다.",
      chartInsufficient: "이 차트를 그리기에 충분한 적격 상품이 없습니다.",
      resetDashboardScope: "대시보드 범위 초기화",
      morePoints: "개의 추가 포인트가 차트에 있습니다.",
      productsAcrossBanks: "{banks}개 은행의 활성 상품",
      activeProducts: "활성 상품",
      topComparisons: "상위 {count}",
      rankedBy: "정렬 기준",
      trailingDays: "최근 {days}일 기준.",
      noRecentChangeDate: "최근 변경일 없음",
      noProductsInScope: "현재 범위에 표시할 상품이 없습니다."
    }
  },
  ja: {
    localeName: "日本語",
    shell: {
      brand: "FPDS 公開画面",
      tagline: "カナダ預金商品のカタログと比較画面"
    },
    nav: {
      products: "商品",
      dashboard: "インサイト",
      localeLabel: "言語"
    },
    common: {
      applyFilters: "フィルターを適用",
      clearFilters: "フィルターをクリア",
      clearAllFilters: "すべてのフィルターをクリア",
      previous: "前へ",
      next: "次へ",
      all: "すべて",
      noDate: "日付なし",
      noRecentChange: "最近の変更日時なし",
      noSuccessfulSnapshot: "まだ成功した集計スナップショットがありません。",
      notDisclosed: "未開示",
      noOptions: "まだ選択できる項目がありません。",
      sourceLanguage: "原文言語",
      verifiedOn: "検証日",
      changedOn: "変更日",
      pageLabel: "ページ"
    },
    grid: {
      pageTitle: "FPDS 公開商品",
      pageDescription: "カナダ預金商品のロケール対応公開商品グリッドです。",
      eyebrow: "WBS 5.12 Locale 対応",
      title: "共通の公開フィルター語彙でカナダの預金商品を比較できます。",
      description:
        "最新の成功した集計スナップショットを基に、当座預金、貯蓄預金、GIC 商品を閲覧できます。商品名は原文を維持し、ラベル・バケットフィルター・鮮度メモは UI リソースとして提供します。",
      currentScope: "現在の範囲",
      primaryFilter: "主要フィルター",
      banks: "銀行",
      productTypes: "商品タイプ",
      targetTags: "対象タグ",
      feeBucket: "手数料区分",
      minimumBalance: "最低残高",
      minimumDeposit: "最低預入額",
      termBucket: "期間区分",
      sortBy: "並び替え",
      direction: "順序",
      filterHint: "フィルターを適用するとグリッドが更新されます。範囲が変わるとページは 1 に戻ります。",
      resultSummary: "結果サマリー",
      noActiveFilters: "有効なフィルターはありません。カナダ全体の公開範囲を表示しています。",
      noResultEyebrow: "結果なし",
      noResultTitle: "現在のフィルター範囲に一致する商品がありません。",
      noResultBody: "アクティブチップを解除するか、より高い粒度の市場ビューを見るためにインサイトダッシュボードへ移動してください。",
      retryTitle: "公開集計 API に接続できないため Product Grid を読み込めませんでした。",
      retryBody: "FastAPI サービスを起動してページを更新してください。公開 Product Grid は `GET /api/public/products` と `GET /api/public/filters` に依存します。",
      retryButton: "Product Grid を再試行",
      openDashboard: "インサイトダッシュボードを開く",
      goToDashboard: "インサイトダッシュボードへ移動",
      metricMonthlyFee: "月額手数料",
      metricMinBalance: "最低残高",
      metricMinDeposit: "最低預入額",
      metricDisplayRate: "表示金利",
      metricTerm: "期間",
      metricKeyDetail: "主要ポイント",
      metricLastChange: "最近の変更",
      metricRateNote: "金利メモ",
      ascending: "昇順",
      descending: "降順",
      sortDefault: "標準順",
      sortDisplayRate: "表示金利",
      sortMonthlyFee: "月額手数料",
      sortMinimumBalance: "最低残高",
      sortMinimumDeposit: "最低預入額",
      sortLastChange: "最近の変更",
      sortBankName: "銀行名",
      sortProductName: "商品名"
    },
    dashboard: {
      pageTitle: "FPDS インサイトダッシュボード",
      pageDescription: "カナダ預金商品のロケール対応公開インサイトダッシュボードです。",
      eyebrow: "WBS 5.12 Locale 対応",
      title: "商品詳細へ戻る前に、カナダ預金市場をひと目で把握できます。",
      description:
        "このダッシュボードは Product Grid と同じ公開フィルター語彙を使い、現在の範囲を KPI カード、構成比、ランキング、単一タイプ比較チャートとして再構成します。",
      scopeSummary: "範囲サマリー",
      scopeTitle: "現在の公開フィルター範囲をダッシュボード表示",
      noActiveFilters: "有効なフィルターはありません。カナダ全体の公開ダッシュボード範囲を表示しています。",
      adjustScope: "Product Grid で範囲を調整",
      clearScope: "範囲をクリア",
      rankingWidgets: "ランキングウィジェット",
      rankingTitle: "この範囲の上位比較",
      rankingDescription: "ウィジェットの順序は承認済みの商品タイプ優先ルールに従い、十分なデータがある場合のみ表示されます。各行からより絞り込んだ Product Grid を開けます。",
      insufficientData: "データ不足",
      noRankingWidgets: "現在の範囲では表示可能なランキングウィジェットがありません。",
      breakdownByBank: "銀行別商品数",
      breakdownByBankDescription: "現在の範囲にある有効商品の銀行別構成です。",
      breakdownByType: "商品タイプ別商品数",
      breakdownByTypeDescription: "フィルター適用後の当座、貯蓄、GIC の構成比です。",
      comparativeChart: "比較チャート",
      chartTitleFallback: "商品タイプを 1 つ選ぶと比較チャートが有効になります",
      chartDescription: "商品タイプをちょうど 1 つ選択すると、意味の近い範囲の中でトレードオフを比較できます。",
      interpretation: "読み解き",
      visiblePoints: "表示ポイント",
      openInGrid: "グリッドで開く",
      methodology: "方法論",
      methodologyTitle: "このダッシュボードの読み方",
      freshness: "鮮度",
      freshnessTitle: "スナップショット処理",
      openProductGrid: "この範囲で Product Grid を開く",
      retryDashboard: "ダッシュボードを再試行",
      apiUnavailableTitle: "公開集計 API に接続できないため Insight Dashboard を読み込めませんでした。",
      apiUnavailableBody:
        "FastAPI サービスを起動してページを更新してください。公開ダッシュボードは `GET /api/public/dashboard-summary`, `GET /api/public/dashboard-rankings`, `GET /api/public/dashboard-scatter`, `GET /api/public/filters` に依存します。",
      mixedMarket: "混合市場",
      peakRate: "最高金利",
      selectOneProductType: "商品タイプを 1 つ選択",
      singleTypeOnly: "比較チャートは単一商品タイプの範囲でのみ利用できます。",
      chartInsufficient: "このチャートを描画するのに十分な適格商品がありません。",
      resetDashboardScope: "ダッシュボード範囲をリセット",
      morePoints: "件の追加ポイントがチャートにあります。",
      productsAcrossBanks: "{banks}行の有効商品",
      activeProducts: "有効商品",
      topComparisons: "上位 {count}",
      rankedBy: "指標",
      trailingDays: "直近 {days} 日。",
      noRecentChangeDate: "最近の変更日なし",
      noProductsInScope: "現在の範囲に表示できる商品がありません。"
    }
  }
};

export function getPublicMessages(locale: string): PublicMessages {
  return PUBLIC_MESSAGES[normalizePublicLocale(locale)];
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
  return Object.entries(values).reduce(
    (output, [key, value]) => output.replace(`{${key}}`, String(value)),
    template
  );
}
