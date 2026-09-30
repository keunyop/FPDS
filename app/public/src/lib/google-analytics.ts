const GOOGLE_ANALYTICS_ID_PATTERN = /^G-[A-Z0-9]{6,20}$/;

export function getGoogleAnalyticsMeasurementId() {
  const measurementId = process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID?.trim();

  return measurementId && GOOGLE_ANALYTICS_ID_PATTERN.test(measurementId)
    ? measurementId
    : null;
}

// Never forward browser URLs, query strings, dynamic identifiers or document titles.
export function getAnalyticsPage(pathname: string) {
  const routes: Record<string, string> = {
    '/': 'Home', '/products': 'Products', '/cards': 'Cards', '/loans': 'Loans',
    '/compare': 'Comparison', '/calculator': 'Calculator', '/methodology': 'Methodology',
    '/guides': 'Guides', '/blog': 'Blog'
  };
  let path = pathname;
  let title = routes[path];
  if (!title && /^\/products\/[^/]+$/.test(pathname)) {
    path = '/products/detail'; title = 'Product detail';
  } else if (!title && /^\/blog\/[^/]+$/.test(pathname)) {
    path = '/blog/article'; title = 'Blog article';
  } else if (!title && /^\/guides\/[^/]+$/.test(pathname)) {
    path = '/guides/article'; title = 'Guide';
  } else if (!title && /^\/ca\/[^/]+$/.test(pathname)) {
    path = '/ca/comparison'; title = 'Canadian comparison';
  }
  if (!title) return null;
  return { page_location: `https://www.switchabank.com${path}`, page_title: `${title} | SwitchaBank`, page_referrer: '' };
}
