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
  dashboard: {
    pageTitle: string;
    pageDescription: string;
    title: string;
    description: string;
    marketSnapshot: string;
    kpiSubtitle: string;
    composition: string;
    compositionSubtitle: string;
    productsByBank: string;
    productsByType: string;
    rankings: string;
    rankingsSubtitle: string;
    comparisonMap: string;
    comparisonSubtitle: string;
    coverageTable: string;
    coverageSubtitle: string;
    dataNotes: string;
    dataNotesBody: string;
    freshness: string;
    openProducts: string;
    clearScope: string;
    noActiveFilters: string;
    noRankingWidgets: string;
    chartUnavailable: string;
    chartSingleTypeHint: string;
    visibleProducts: string;
    activeProducts: string;
    banksInScope: string;
    peakRate: string;
    openInProducts: string;
    apiUnavailableTitle: string;
    apiUnavailableBody: string;
    retryDashboard: string;
    mixedMarket: string;
    rankedBy: string;
    trailingDays: string;
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
      brand: "FPDS Public",
      tagline: "Canada deposit products"
    },
    nav: {
      dashboard: "Dashboard",
      products: "Products",
      methodology: "Methodology",
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
      notDisclosed: "Not disclosed",
      open: "Open",
      pageLabel: "Page",
      previous: "Previous",
      next: "Next",
      verifiedOn: "Verified"
    },
    grid: {
      pageTitle: "FPDS Products",
      pageDescription: "Filterable Canada deposit product catalog.",
      title: "Product catalog",
      description: "Filter active chequing, savings, and GIC products from the latest public snapshot.",
      currentScope: "Current scope",
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
      noActiveFilters: "Full Canada public scope.",
      noResultTitle: "No products matched this scope.",
      noResultBody: "Clear filters or return to the dashboard for a broader market view.",
      retryTitle: "Products could not load.",
      retryBody: "The public API is not reachable.",
      retryButton: "Retry products",
      openDashboard: "Open dashboard",
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
      sortDefault: "Default",
      sortDisplayRate: "Display rate",
      sortMonthlyFee: "Monthly fee",
      sortMinimumBalance: "Minimum balance",
      sortMinimumDeposit: "Minimum deposit",
      sortLastChange: "Last change",
      sortBankName: "Bank",
      sortProductName: "Product"
    },
    dashboard: {
      pageTitle: "FPDS Dashboard",
      pageDescription: "Canada deposit market dashboard.",
      title: "Deposit market dashboard",
      description: "Rates, fees, coverage, and recent changes from the latest public snapshot.",
      marketSnapshot: "Market snapshot",
      kpiSubtitle: "Current public scope",
      composition: "Market composition",
      compositionSubtitle: "Active product coverage by bank and product type.",
      productsByBank: "Products by bank",
      productsByType: "Products by type",
      rankings: "Top comparisons",
      rankingsSubtitle: "Eligible products ranked by the approved public metrics.",
      comparisonMap: "Comparison map",
      comparisonSubtitle: "Select one product type for a like-for-like chart.",
      coverageTable: "Coverage table",
      coverageSubtitle: "Public products currently represented in the snapshot.",
      dataNotes: "Data notes",
      dataNotesBody: "Metrics use public aggregate fields. Products missing required numeric values are excluded from affected comparisons.",
      freshness: "Freshness",
      openProducts: "Open products",
      clearScope: "Clear scope",
      noActiveFilters: "No filters active.",
      noRankingWidgets: "No ranking is eligible for this scope.",
      chartUnavailable: "Not enough eligible products for this chart.",
      chartSingleTypeHint: "Choose one product type to unlock the comparison map.",
      visibleProducts: "Visible products",
      activeProducts: "active products",
      banksInScope: "banks",
      peakRate: "Peak rate",
      openInProducts: "Open in products",
      apiUnavailableTitle: "Dashboard could not load.",
      apiUnavailableBody: "The public aggregate API is not reachable.",
      retryDashboard: "Retry dashboard",
      mixedMarket: "All product types",
      rankedBy: "Ranked by",
      trailingDays: "trailing {days} days"
    },
    methodology: {
      pageTitle: "FPDS Methodology",
      pageDescription: "Public data notes and metric boundaries.",
      title: "Methodology",
      description: "How FPDS prepares the public Canada deposit-product view.",
      sections: [
        {
          title: "Snapshot source",
          body: "Public pages read from the latest successful aggregate snapshot, not live bank pages."
        },
        {
          title: "Metric eligibility",
          body: "Rates, fees, balances, deposits, and terms are shown only when the canonical public field is available."
        },
        {
          title: "Product text",
          body: "Product names and source-derived conditions stay in the original source language."
        },
        {
          title: "Evidence boundary",
          body: "Raw evidence, source excerpts, and internal review traces are not exposed on FPDS Public."
        }
      ]
    }
  },
  ko: {
    localeName: "한국어",
    shell: {
      brand: "FPDS Public",
      tagline: "캐나다 예금 상품"
    },
    nav: {
      dashboard: "대시보드",
      products: "상품",
      methodology: "방법론",
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
      notDisclosed: "미공개",
      open: "열기",
      pageLabel: "페이지",
      previous: "이전",
      next: "다음",
      verifiedOn: "검증"
    },
    grid: {
      pageTitle: "FPDS 상품",
      pageDescription: "캐나다 예금 상품 카탈로그입니다.",
      title: "상품 카탈로그",
      description: "최신 공개 스냅샷의 입출금, 저축, GIC 상품을 필터링합니다.",
      currentScope: "현재 범위",
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
      noActiveFilters: "캐나다 전체 공개 범위입니다.",
      noResultTitle: "현재 범위에 맞는 상품이 없습니다.",
      noResultBody: "필터를 해제하거나 대시보드에서 더 넓은 시장을 확인하세요.",
      retryTitle: "상품을 불러오지 못했습니다.",
      retryBody: "공개 API에 연결할 수 없습니다.",
      retryButton: "상품 다시 불러오기",
      openDashboard: "대시보드 열기",
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
      sortProductName: "상품"
    },
    dashboard: {
      pageTitle: "FPDS 대시보드",
      pageDescription: "캐나다 예금 시장 대시보드입니다.",
      title: "예금 시장 대시보드",
      description: "최신 공개 스냅샷 기준 금리, 수수료, 커버리지, 최근 변경을 확인합니다.",
      marketSnapshot: "시장 스냅샷",
      kpiSubtitle: "현재 공개 범위",
      composition: "시장 구성",
      compositionSubtitle: "은행과 상품 유형별 활성 상품 커버리지입니다.",
      productsByBank: "은행별 상품",
      productsByType: "유형별 상품",
      rankings: "상위 비교",
      rankingsSubtitle: "공개 지표 기준으로 비교 가능한 상품만 정렬합니다.",
      comparisonMap: "비교 맵",
      comparisonSubtitle: "상품 유형 하나를 선택하면 같은 기준으로 비교합니다.",
      coverageTable: "커버리지 표",
      coverageSubtitle: "현재 스냅샷에 포함된 공개 상품입니다.",
      dataNotes: "데이터 기준",
      dataNotesBody: "지표는 공개 aggregate 필드를 사용하며, 필요한 숫자 값이 없는 상품은 해당 비교에서 제외됩니다.",
      freshness: "최신성",
      openProducts: "상품 열기",
      clearScope: "범위 해제",
      noActiveFilters: "활성 필터 없음",
      noRankingWidgets: "현재 범위에서 표시할 순위가 없습니다.",
      chartUnavailable: "차트를 그릴 수 있는 상품 수가 부족합니다.",
      chartSingleTypeHint: "상품 유형 하나를 선택하면 비교 맵이 열립니다.",
      visibleProducts: "표시 상품",
      activeProducts: "활성 상품",
      banksInScope: "은행",
      peakRate: "최고 금리",
      openInProducts: "상품에서 열기",
      apiUnavailableTitle: "대시보드를 불러오지 못했습니다.",
      apiUnavailableBody: "공개 aggregate API에 연결할 수 없습니다.",
      retryDashboard: "대시보드 다시 불러오기",
      mixedMarket: "전체 상품 유형",
      rankedBy: "정렬 기준",
      trailingDays: "최근 {days}일"
    },
    methodology: {
      pageTitle: "FPDS 방법론",
      pageDescription: "공개 데이터 기준과 지표 경계입니다.",
      title: "방법론",
      description: "FPDS가 캐나다 예금 상품 공개 화면을 준비하는 방식입니다.",
      sections: [
        {
          title: "스냅샷 기준",
          body: "공개 화면은 은행 페이지를 실시간으로 읽지 않고 최신 성공 aggregate 스냅샷을 사용합니다."
        },
        {
          title: "지표 포함 기준",
          body: "금리, 수수료, 잔액, 예치금, 기간은 공개 canonical 필드가 있을 때만 표시합니다."
        },
        {
          title: "상품 텍스트",
          body: "상품명과 원문에서 온 조건 문구는 출처 언어를 유지합니다."
        },
        {
          title: "증거 경계",
          body: "원문 증거, 출처 발췌, 내부 검토 trace는 FPDS Public에 공개하지 않습니다."
        }
      ]
    }
  },
  ja: {
    localeName: "日本語",
    shell: {
      brand: "FPDS Public",
      tagline: "カナダ預金商品"
    },
    nav: {
      dashboard: "ダッシュボード",
      products: "商品",
      methodology: "方法",
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
      notDisclosed: "非公開",
      open: "開く",
      pageLabel: "ページ",
      previous: "前へ",
      next: "次へ",
      verifiedOn: "確認"
    },
    grid: {
      pageTitle: "FPDS 商品",
      pageDescription: "カナダ預金商品のカタログです。",
      title: "商品カタログ",
      description: "最新の公開スナップショットから chequing、savings、GIC 商品を絞り込みます。",
      currentScope: "現在の範囲",
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
      noActiveFilters: "カナダ全体の公開範囲です。",
      noResultTitle: "現在の範囲に一致する商品はありません。",
      noResultBody: "フィルターを解除するか、ダッシュボードで広い市場を確認してください。",
      retryTitle: "商品を読み込めませんでした。",
      retryBody: "公開 API に接続できません。",
      retryButton: "商品を再読み込み",
      openDashboard: "ダッシュボードを開く",
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
      sortProductName: "商品"
    },
    dashboard: {
      pageTitle: "FPDS ダッシュボード",
      pageDescription: "カナダ預金市場のダッシュボードです。",
      title: "預金市場ダッシュボード",
      description: "最新の公開スナップショットから金利、手数料、カバレッジ、最近の変更を確認します。",
      marketSnapshot: "市場スナップショット",
      kpiSubtitle: "現在の公開範囲",
      composition: "市場構成",
      compositionSubtitle: "銀行別、商品タイプ別の有効商品数です。",
      productsByBank: "銀行別商品",
      productsByType: "タイプ別商品",
      rankings: "上位比較",
      rankingsSubtitle: "公開指標で比較できる商品のみを順位付けします。",
      comparisonMap: "比較マップ",
      comparisonSubtitle: "商品タイプを 1 つ選ぶと同じ意味の軸で比較します。",
      coverageTable: "カバレッジ表",
      coverageSubtitle: "現在のスナップショットに含まれる公開商品です。",
      dataNotes: "データ基準",
      dataNotesBody: "指標は公開 aggregate フィールドを使います。必要な数値がない商品は該当比較から除外されます。",
      freshness: "鮮度",
      openProducts: "商品を開く",
      clearScope: "範囲を解除",
      noActiveFilters: "有効なフィルターなし",
      noRankingWidgets: "現在の範囲で表示できる順位はありません。",
      chartUnavailable: "チャートに必要な商品数が不足しています。",
      chartSingleTypeHint: "商品タイプを 1 つ選ぶと比較マップを表示します。",
      visibleProducts: "表示商品",
      activeProducts: "有効商品",
      banksInScope: "銀行",
      peakRate: "最高金利",
      openInProducts: "商品で開く",
      apiUnavailableTitle: "ダッシュボードを読み込めませんでした。",
      apiUnavailableBody: "公開 aggregate API に接続できません。",
      retryDashboard: "ダッシュボードを再読み込み",
      mixedMarket: "全商品タイプ",
      rankedBy: "順位基準",
      trailingDays: "直近 {days} 日"
    },
    methodology: {
      pageTitle: "FPDS 方法",
      pageDescription: "公開データの基準と指標の境界です。",
      title: "方法",
      description: "FPDS がカナダ預金商品の公開画面を作る方法です。",
      sections: [
        {
          title: "スナップショット",
          body: "公開画面は銀行ページをリアルタイムで読まず、最新の成功 aggregate スナップショットを使います。"
        },
        {
          title: "指標の対象",
          body: "金利、手数料、残高、預入額、期間は公開 canonical フィールドがある場合だけ表示します。"
        },
        {
          title: "商品テキスト",
          body: "商品名とソース由来の条件文は元の言語のまま表示します。"
        },
        {
          title: "証拠の境界",
          body: "原文証拠、ソース抜粋、内部レビュー trace は FPDS Public では公開しません。"
        }
      ]
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
  return Object.entries(values).reduce((output, [key, value]) => output.replace(`{${key}}`, String(value)), template);
}
