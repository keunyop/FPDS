"""Applied Vancity correction, retained for historical identification.

Original transaction: 2eb1eb45fe78:scripts/maintenance/correct_reference_rate_20260916.py.
"""

PRODUCT_ID = "prod_dGBpyMydkwGWu30L"
SOURCE_URL = "https://www.vancity.com/borrow/loans-lines-of-credit/planet-wise-renovation"
SUMMARY = (
    "Term loan: Vancity Prime + 0.75% for qualifying renovations. "
    "APR assumes no fees or charges; additional fees or charges increase "
    "the total cost of credit and APR."
)
CORRECTION_ID = "public-rate-semantics-2026-09-16-vancity"


if __name__ == "__main__":
    raise SystemExit("The 2026-09-16 correction is complete and has no active execution path.")
