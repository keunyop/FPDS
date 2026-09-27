# Public bank handoff

Date: 2026-09-26
Authority: FR-PUB-026 / D-083 / WBS 5.69; selected proposal P1-4.

## Public experience

Detail replaces its former header official action with a compact inline
confirmation section next to the disclosed terms. Each comparison product
replaces its former official button with the same domain section. There is no
modal, acknowledgment checkbox, eligibility judgment or application promise.
The action says to check current terms at the bank and identifies a new external
tab. The existing country/product/official_bank_click event stays unchanged.

- Detail includes currency, qualified rate text, known monthly/annual cost,
  product verification date/status and the approved destination hostname.
  Comparison retains those facts in its existing adjacent ledger.
- Minimum deposit and minimum balance remain separate. Zero is explicit; null,
  invalid and negative values remain unknown. GIC term-specific minimums keep
  their own term labels, including differences from the overall minimum.
- Fee waivers retain their approved source language and never replace a positive
  base fee with zero. Published GIC redemption flags and early-withdrawal
  penalties remain separate. Contradictory flags are unknown.
- Transaction allowances never imply free or unrestricted withdrawals.
  Undisclosed minimum/waiver/withdrawal facts say to check with the bank.
  No application documents, personal eligibility or unapproved facts are generated.
- The domain comes from the approved public product_url, not from a guessed bank
  homepage. This is the reviewed destination, not a claim that its content was
  checked live during the visit. Unsafe/missing URLs have no external action.

All UI-owned labels support EN/KO/JA. Source-derived conditions keep their
original language. Existing verification expiry warnings remain visible.

## Mobile action

Below 768px, detail and selected comparisons show product name plus a direct
bank action. Comparison follows the product at the reading position; removing a
product immediately removes it as a destination. The same action is available
inline on each product.

Only one bottom action is visible. The bank action takes precedence over the
comparison return dock; comparison remains reachable in the header. The measured
dock height plus spacing is reserved after page content, with safe-area padding.
Consent, open modal surfaces, input/select focus and a shortened visual viewport
hide the action. No action appears for a missing, failed or unsafe product.

## Operator URL report

Run manually from the repository root:

```powershell
uv run python scripts/maintenance/public_official_link_report.py --country CA --limit 25 --output tmp/official-links-ca
uv run python scripts/maintenance/public_official_link_report.py --country US --product-id PRODUCT_ID --output tmp/official-product
uv run python -m unittest scripts.maintenance.test_public_official_link_report -v
```

Replace PRODUCT_ID with an active public ID; repeat --product-id for a bounded
selection. Runs allow 1–50 products. The default selects 25 products in bank/name
order. JSON contains exact per-product times, HTTP status, original/final URL,
redirect hops, title/H1 hints and result. Markdown provides the review table.
The latest snapshot must be complete and stable across pages before any bank
checks begin. Reports are local operator artifacts, outside the Public bundle.

| Result | Meaning and operator action |
|---|---|
| reachable_identity_observed | HTTP HTML response contains the product name in title/H1; this is an identity hint, not financial verification |
| redirect_review / canonical_review | Path/query or declared canonical differs; compare original product with destination |
| external_redirect_review | Host changed outside exact www/apex pair; destination recorded, not fetched |
| identity_review | Product name absent from title/H1; inspect product identity manually |
| client_redirect_review | HTML requests a client redirect; inspect manually |
| http_failure | HTTP failure; verify availability with an ordinary bank visit |
| access_unverified / blocked_or_unreachable | Access challenge, rate limit, timeout, network or safety failure; no conclusion about product retirement |
| missing_url / content_review / redirect_loop / redirect_limit / unexpected_status | Missing or unsupported destination/response; inspect before correction |

Only HTTPS on the approved destination's exact host/www-apex pair is followed.
Every hop uses the existing private-network/DNS and allowlist checks; credentials,
nonstandard ports, whitespace and malformed URLs are rejected. Requests are
GET-only, 10 seconds per hop, at most five redirects, with a 512 KiB identity
read cap. No browser/JavaScript fallback, third-party assets, scheduler, raw
evidence storage, canonical writes or automatic URL repair.

A report does not renew product verification. Review a suspected wrong-product
redirect through the existing source/review process before correcting and
publishing. Recheck affected links after a bank-site change or user error report.
An inaccessible source requires human verification, not automatic withdrawal.

## Verification boundaries

Regression tests cover disclosed zero/missing amounts, source-language waivers,
GIC minimums/redemption conflicts, URL syntax, redirect/failure/challenge states,
DNS safety, bounded reads, stable snapshot pagination and report rendering.
Browser checks cover EN/KO/JA at 390×844, 768 and 1440px, existing comparison/
calculator flows, consent/input coexistence and published CA/US values.

The dated [initial operator sample](../00-governance/public-bank-link-check-2026-09-26.md)
is a bounded observation, not an all-product link or financial-data certification.
