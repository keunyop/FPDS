-- Backfill canonical Canada deposit subtype rows that can be lost when an
-- operator-managed product type is deleted and recreated.

WITH subtype_seed(product_type, subtype_code, display_order, notes) AS (
    VALUES
        ('chequing', 'standard', 10, 'Canada deposit taxonomy v1'),
        ('chequing', 'package', 20, 'Canada deposit taxonomy v1'),
        ('chequing', 'interest_bearing', 30, 'Canada deposit taxonomy v1'),
        ('chequing', 'premium', 40, 'Canada deposit taxonomy v1'),
        ('chequing', 'other', 99, 'Canada deposit taxonomy v1'),
        ('savings', 'standard', 10, 'Canada deposit taxonomy v1'),
        ('savings', 'high_interest', 20, 'Canada deposit taxonomy v1'),
        ('savings', 'youth', 30, 'Canada deposit taxonomy v1'),
        ('savings', 'foreign_currency', 40, 'Canada deposit taxonomy v1'),
        ('savings', 'other', 99, 'Canada deposit taxonomy v1'),
        ('gic', 'redeemable', 10, 'Canada deposit taxonomy v1'),
        ('gic', 'non_redeemable', 20, 'Canada deposit taxonomy v1'),
        ('gic', 'market_linked', 30, 'Canada deposit taxonomy v1'),
        ('gic', 'other', 99, 'Canada deposit taxonomy v1')
)
INSERT INTO taxonomy_registry (
    taxonomy_id,
    country_code,
    product_family,
    product_type,
    subtype_code,
    display_order,
    active_flag,
    notes,
    created_at,
    updated_at
)
SELECT
    'tax-ca-deposit-' || subtype_seed.product_type || '-' || replace(subtype_seed.subtype_code, '_', '-'),
    'CA',
    'deposit',
    subtype_seed.product_type,
    subtype_seed.subtype_code,
    subtype_seed.display_order,
    COALESCE(product_type_registry.status = 'active', true),
    subtype_seed.notes,
    now(),
    now()
FROM subtype_seed
LEFT JOIN product_type_registry
  ON product_type_registry.product_family = 'deposit'
 AND product_type_registry.product_type_code = subtype_seed.product_type
ON CONFLICT (country_code, product_family, product_type, subtype_code) DO UPDATE SET
    display_order = EXCLUDED.display_order,
    active_flag = EXCLUDED.active_flag,
    notes = EXCLUDED.notes,
    updated_at = EXCLUDED.updated_at;

