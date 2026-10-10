# Five US banks: direct collection diagnosis and generic corrections

Date: 2026-10-09 (America/Vancouver). Environment: existing `.env.dev`
PostgreSQL/object storage and the existing US Public projection. No Admin
collection API, provider calls, runtime restart or deployment.

## Latest stored results

| Bank | Latest relevant execution | Stored candidates | Approved |
| --- | --- | ---: | ---: |
| Fifth Third | Sep 1, 20:58 PDT; five scopes, discovery failed | 0 | 0 |
| First Citizens | Oct 9, 11:35 PDT; five current scopes | 18 | 2 |
| Goldman Sachs Bank USA | Oct 9, 11:35 PDT; savings and CD | 2 | 0 |
| HSBC USA | Oct 9, 11:35 PDT; six scopes | 10 | 0 |
| Huntington | Oct 9, 11:35 PDT; seven scopes | 16 | 0 |

The 27 latest-per-type records include First Citizens' older CD execution and
Goldman's older personal-loan execution, each with zero candidates. These are
historical diagnoses, not fresh publication inputs. Original 27 Runs, 46
candidates, 129 Run/source joins and 134 bank documents are preserved.
The current four-bank executions used process v13. Their losses cannot be
attributed simply to an old serving deployment.

## Confirmed first losses and common fixes

- Typed CMS records contain a GUID, `displayName`, nonempty `fields`, and a
  content-tree `url`. The public route is in the nested link `href`. Treating
  internal content paths as financial sources wasted capture budgets and
  produced HTTP-200 error pages. Discovery now skips only this structural URL,
  preserving nested public hrefs, ordinary links and JSON-LD Product URLs.
- A prominent error H1 plus its adjacent explicit missing-page message now
  fails source parsing. General help text elsewhere cannot mark a bank product
  unavailable. The Fifth Third current responses were error pages; no historical
  prices or error-response facts were published.
- Marcus' actual account label/APY is separate from its marketing H1s. Its CMS
  tooltips use `tooltip-data-id`, not HTML `id`. The parser now retains the full
  locally owned panel and resolved complete notes, including the current date,
  variable APY basis and maximum-balance notice. Responsive copies must agree;
  conflicting/missing notes and conditional/multiple rates remain excluded.
- First Citizens' named single-card pricing PDF continues onto page two. The
  prior multi-card-column parser did not retain this format. The common parser
  now requires one named pricing disclosure, an explicit purchase APR interval,
  the grace rule, and every nonempty continuation page. It preserves the dated
  Prime Rate/margin calculations, payment allocation/default and application
  conditions. An issuer prefix is corroborated by the exact official hostname;
  full remaining card names must match. A cash-rewards card cannot donate its
  terms to a rewards card. Unconditional base annual-fee rows are independent;
  a first-year waiver never becomes the regular zero fee. Current detail-to-PDF
  links are retained as literal captured evidence. A native H1 corroborated by
  SEO and that exact named PDF can resolve a descriptive SEO qualifier or alias
  route (the Smart Option/Low Interest case); metadata or a missing current
  link cannot establish this association. Financial records and notes remain
  atomic through real 900-character chunking; no summary loses its conditions.
- Huntington's complete paragraph explicitly requires insurance on the real
  property securing the account. This proves collateral. A separate title-
  insurance cost sentence containing "may" does not negate that explicit
  collateral; all dollar thresholds and costs remain in evidence. Uncertain or
  contradictory collateral continues to fail. Its newly attempted current
  HELOC capture timed out, so this preserved diagnostic fixture is not a
  publication source.

The fixes use structure, literal financial meaning, exact product ownership and
current selected snapshot/parse origins, without bank-specific runtime rules,
manual approval, confidence overrides or additional optional-only research.
Parser v23, process v14 and shared extraction/normalization instructions move
together. Ordinary collection must deploy API/Worker together to use the change.

## Bounded direct operation and verification

Operation: `us-five-direct-20261009`. Private execution artifacts are under
`tmp/us-five-20261009` and the existing private operations storage prefix. The
operation is a one-off, not a menu, feature or scheduler. Existing Chase jobs
were left running. Required current captured inputs were reused by SHA256;
no price was supplied manually. Ordinary extraction, artifact loading,
normalization, automatic validation/promotion and Public refresh are used.

Current same-input assessment: 43 candidates, five automatic passes and 38
exclusions. The four First Citizens cards and Marcus Online Savings pass. The
newly eligible products are First Citizens Rewards/Cash Rewards and Marcus
Online Savings; Smart Option and Travel Rewards already existed in Public.
Fifth Third has no usable current product response. HSBC's ten and Huntington's
thirteen currently captured candidates remain excluded under unchanged
comparison essentials. Failed current captures are not historical fallbacks.

The initial per-file CLI uploads were slow. Connection reuse is confined to
this ignored one-off operation folder, using the same configured bucket,
credentials, keys, bytes and ContentType. A private baseline download verified
SHA256 before switching. The interruption checkpoint contained 17 started Runs
and one completed source join, with no candidates, versions, promotions or
canonical change. That state and initial plan were preserved. Resume requires
identical Run IDs, current checksums, references and expected automatic
candidate IDs, exclusively owned started Runs, zero candidates and unchanged
canonical data. It performs no new research or paid call.

Local verification: focused 128 and API 650 pass. Full Worker 973: 969 pass,
four pre-existing failures. All four reproduce under an isolated exact HEAD
checkout: the admin-collection-parity and owned-deposit-tables source-hash
checks, plus two named-annual-records card checks. Expected source hashes were
not edited. The new official-byte/boundary regressions all pass, including real
chunking, complete continuation preservation, missing current links, differing
issuer/product names, ambiguous notes and conditional/contradictory fees.

## Actual publication and readback

Completed through ordinary automatic promotion and `phase1_public` refresh
`agg_t8_O581hmTdC4-Wk`: 17 completed one-off Runs, 43 candidates, five approved
and 38 automatically rejected, zero review tasks, provider calls or Admin API
calls. Stored-origin validation and the rollback rehearsal both passed. All
47 actual stored original SHA256 values and parsed-text bytes match the direct
current captures. Eighteen current financial/identity field-evidence joins pass
exact ownership, meaning, snapshot/parse/Run and character-span checks.

| Bank/product | Before Public | Result |
| --- | --- | --- |
| Goldman Sachs / Marcus Online Savings Account | Hidden | Newly public, fresh verified version 6 |
| First Citizens Rewards Credit Card | Absent | Newly public, version 1 |
| First Citizens Cash Rewards Credit Card | Absent | Newly public, version 1 |
| First Citizens Smart Option Credit Card | Public | Current proof/complete conditions, version 4 |
| First Citizens Travel Rewards Credit Card | Public | Current proof/complete conditions, version 2 |

Marcus' existing inactive canonical row was activated with freshly captured
facts and a new ordinary approved version; historical financial facts were not
restored to fill Public. Two canonical rows were newly created. Three prior
approved versions were normally superseded, with every prior financial fact
unchanged. All other 471 canonical rows remain unchanged. Original 27 Runs,
46 candidates, 129 source joins, 134 bank documents and 241 source snapshots
are byte/value unchanged in the DB comparisons. All 1,559 prior version facts
are preserved; five ordinary versions were added.

Anonymous Public list/readback: **US 38 -> 41; CA 120 -> 120**. All five
product detail APIs and actual website pages return 200 with matching identity,
values and full account/card rate conditions. Unrelated list rows remain
unchanged. No private evidence fields, storage keys, capture receipts, origin
mappings or retrieval internals appear in API/site responses.

Published pages:

- [Marcus Online Savings Account](https://www.switchabank.com/products/prod_hiJANQ-L5-J0pziJ?country_code=US)
- [First Citizens Rewards Credit Card](https://www.switchabank.com/products/prod_lKPAbX8v7SFKgeQB?country_code=US)
- [First Citizens Cash Rewards Credit Card](https://www.switchabank.com/products/prod_w3HCiF6JlzYyn9un?country_code=US)
- [First Citizens Smart Option Credit Card](https://www.switchabank.com/products/prod_xM3RkQYZTkTTBOjU?country_code=US)
- [First Citizens Travel Rewards Credit Card](https://www.switchabank.com/products/prod_rGhyVx4lpDg0fi0C?country_code=US)

## Serving deployment and remaining limits

The serving health endpoint remains process v13; this work publishes data using
the corrected local worker and does not deploy API/Worker code. Deploy the
shared API/Worker runtime together to make future ordinary Admin collections
use parser v23/process v14, then confirm health/cache identity and one bounded
current-source smoke. No migration, Admin UI change or permanent recovery
feature is needed. Existing account/security approval controls are unchanged.

Fifth Third's failed current responses and Huntington's failed current HELOC/CD
captures remain excluded. Other current candidates lack or conflict on required
price, rate/term, ordinary transaction-cost, withdrawal-consequence or security
proof. These are not converted into zero/false or manual-review work. All four
pre-existing full-Worker test failures remain documented above.
