const GOOGLE_ANALYTICS_ID_PATTERN = /^G-[A-Z0-9]{6,20}$/;

export function getGoogleAnalyticsMeasurementId() {
  const measurementId = process.env.NEXT_PUBLIC_GOOGLE_ANALYTICS_ID?.trim();

  return measurementId && GOOGLE_ANALYTICS_ID_PATTERN.test(measurementId)
    ? measurementId
    : null;
}
