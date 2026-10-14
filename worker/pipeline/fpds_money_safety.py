"""Currency-owned heuristic fee limits, separate from exact source validation."""
from decimal import Decimal


def fee_plausibility_limit(field_name, currency):
    # The historical bands were calibrated in CAD/USD. Reusing those numbers
    # as pesos/yen invents an exchange rate and rejects exact official prices.
    # Other explicitly supported currencies retain finite/nonnegative native
    # typing and all exact-source/ownership/acceptance gates, without an invented
    # currency conversion or a new unevidenced plausibility band.
    from worker.pipeline.fpds_collection_accuracy import CURRENCY_PATTERNS
    code = str(currency or '').strip().upper()
    if code in CURRENCY_PATTERNS and code not in {'CAD', 'USD'}:
        return None
    return Decimal('2000') if field_name == 'annual_fee' else Decimal('500')
