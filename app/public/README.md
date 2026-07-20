# Public App Surface

Use this area for the public Product Grid and Insight Dashboard experience.

Planned scope:
- anonymous browser UI
- public product grid
- public dashboard
- locale-aware public rendering

Current scaffold:
- `routes.manifest.json` lists the reserved public routes.
- `route-shells/` holds route-by-route placeholders for the future public runtime.
- the future public runtime should follow the Next.js + Shadcnblocks template-first baseline from `docs/03-design/fpds-design-system.md` and `docs/03-design/fpds_design_system_stripe_benchmark.md`.

Current runtime:
- a live Next.js public package now lives under `src/`
- `/` redirects to `/dashboard` so FPDS opens on the public Home view
- `/dashboard` renders a concise Deposit market snapshot with direct Deposit and Loan entry actions, Banks and Visible products KPIs, a decision-useful deposit rate ranking, bank-share bars that render without client hydration, and an optional like-for-like scatter only when the selected product type supports it; repeated purpose cards and low-value `Recently Changed`, `Top Interest Rate`, `Products by type`, inline methodology, and inline data-note panels are not rendered on Home
- `/products` renders the Deposit catalog against `GET /api/public/products` and `GET /api/public/filters`, with result count and freshness in the hero, progressively disclosed filters, a compact active-scope/sort toolbar, and no duplicate Top 5 block. Product cards retain visible bank identity, one primary metric plus at most two secondary facts, Compare and Details actions, and no Changed/Verified footer or repeated official-page action. The compare control stays compact until a user selects a product, then reveals type-aware mobile cards and a desktop table for up to four products
- `/loans` uses the same catalog, filter, sort, compare, and product-detail path for review-approved `mortgage`, `personal-loan`, and `line-of-credit` products. Loan-specific rate, rate type, term, amortization, payment, and prepayment fields are public only after canonical review approval.
- `/products/[productId]` renders public product facts from `GET /api/public/products/:productId`, keeps visible bank identity, presents three decision-relevant metrics first, and then only available product facts. Deposit details may include an estimated-interest calculator and approved period-rate table; every detail keeps a compact snapshot disclosure, a Methodology link, the official bank action, and a same-bank catalog action without recommendation-style summary language
- bank logo assets live under `public/bank-logos/`; RBC, CIBC, Scotiabank, and TD use official-site assets, BMO uses a small SVG logo asset with BMO identified as the author/source on Wikimedia Commons, and those Big 5 logos are served locally to avoid repeated remote image fetches
- recognized Canada bank/credit-union additions use verified official logo URLs in the `BankLogo` mapping where available; the remaining official favicon entries are retained only as a resilient fallback for brands whose full public logo asset is blocked, retired, or not safely discoverable
- bank marks are shown without a card, border, or background frame on Public and fall back to an unframed bank-code identifier only when a logo cannot load; the accessible label always retains the bank name
- logo source paths: RBC `https://www.rbcroyalbank.com/dvl/assets/images/logos/rbc-logo-shield.svg`, CIBC `https://www.cibc.com/content/dam/global-assets/logos/cibc-logos/no-tagline/cibc-logo-colour-142x36.svg`, Scotiabank `https://www.scotiabank.com/content/dam/scotiabank/images/logos/2019/scotiabank-logo-red-desktop-200px.svg`, TD `https://www.td.com/content/dam/tdct/images/navigation-header-and-footer/td-logo-mobile.png`, BMO `https://commons.wikimedia.org/wiki/File:BMO_Logo.svg`
- public API reads use a short server-side timeout so a slow or stuck API call renders the existing unavailable state instead of leaving a sort/navigation request pending indefinitely
- `/methodology` renders the public data-boundary and metric notes without exposing evidence traces or source excerpts
- the public header shows a simple FPDS logo mark, a medium-weight `FPDS` brand title, Home, Deposit, Loan, and a compact locale menu; Methodology remains available by route but is no longer a top-level header or Home action
- the public footer is a compact verification and navigation surface with Home, Deposit, Loan, and Methodology links plus the same locale control used by the header; non-actionable coverage/data link groups are omitted
- `WBS 5.11` is now implemented with URL-based shared scope preservation across sibling navigation plus dashboard-to-grid drill-in links from ranking rows
- `WBS 5.12` is now implemented with EN/KO/JA locale switching, locale-preserving sibling navigation, locale-aware page metadata, and locale-aware labels or freshness copy while keeping source-derived product content in its original language
- `WBS 5.13` is now implemented with locale-aware methodology/freshness wording on the public surface, while `/products` now keeps catalog chrome minimal and leaves detailed data-boundary copy to `/methodology`
- `WBS 5.14` responsive QA is complete for the current Public surface: production-rendered Home, Deposit, Loan, compare, and detail states were checked at desktop, tablet, and exact 390px mobile widths with no horizontal document overflow
- public-owned date and freshness timestamp displays use fixed `yyyy-mm-dd` and `yyyy-mm-dd hh:mm` formatting instead of locale-specific long date strings
- the public app uses the same `radix-nova` style family as the admin app, with `@shadcnblocks/dashboard10`-installed chart/table primitives adapted through FPDS-owned domain components
