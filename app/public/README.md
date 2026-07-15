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
- `/dashboard` renders a simplified public Home view with product-neutral FPDS copy for future non-deposit coverage, a premium fintech-style hero, purpose-based entry cards, Banks and Visible products KPI cards, decision-useful ranking cards with simplified rank numerals, bank coverage, and optional like-for-like scatter only when the selected product type supports it; low-value public `Recently Changed`, `Top Interest Rate`, `Products by type`, inline methodology action, and inline data-note panels are not rendered on the Home surface
- `/products` renders the simplified Deposit catalog against `GET /api/public/products` and `GET /api/public/filters`, with purpose-based entry cards, compact collapsible filter controls, sort controls between search conditions and the product list, a sort-aware Top 5 list fetched from the same products API with `page_size=5`, a client-side compare table for up to four currently rendered products, locally served real bank logos without redundant visible bank-name chrome, official bank-page actions placed in the top-right of product cards when available, comparison-focused metric cards, and no product-card Changed/Verified date footer
- `/loans` uses the same catalog, filter, sort, compare, and product-detail path for review-approved `mortgage`, `personal-loan`, and `line-of-credit` products. Loan-specific rate, rate type, term, amortization, payment, and prepayment fields are public only after canonical review approval.
- `/products/[productId]` renders public product facts from `GET /api/public/products/:productId`, includes a locally served real bank logo without redundant visible bank-name chrome, an estimated-interest calculator, source-derived signup/application facts, an optional period-rate table, a compact disclosure note, direct official bank product-page and similar-product actions, and no Decision Summary card
- bank logo assets live under `public/bank-logos/`; RBC, CIBC, Scotiabank, and TD use official-site assets, BMO uses a small SVG logo asset with BMO identified as the author/source on Wikimedia Commons, and those Big 5 logos are served locally to avoid repeated remote image fetches
- recognized Canada bank/credit-union additions use verified official logo URLs in the `BankLogo` mapping where available; the remaining official favicon entries are retained only as a resilient fallback for brands whose full public logo asset is blocked, retired, or not safely discoverable
- bank marks are shown without a card, border, or background frame on Public and fall back to an unframed bank-code identifier only when a logo cannot load; the accessible label always retains the bank name
- logo source paths: RBC `https://www.rbcroyalbank.com/dvl/assets/images/logos/rbc-logo-shield.svg`, CIBC `https://www.cibc.com/content/dam/global-assets/logos/cibc-logos/no-tagline/cibc-logo-colour-142x36.svg`, Scotiabank `https://www.scotiabank.com/content/dam/scotiabank/images/logos/2019/scotiabank-logo-red-desktop-200px.svg`, TD `https://www.td.com/content/dam/tdct/images/navigation-header-and-footer/td-logo-mobile.png`, BMO `https://commons.wikimedia.org/wiki/File:BMO_Logo.svg`
- public API reads use a short server-side timeout so a slow or stuck API call renders the existing unavailable state instead of leaving a sort/navigation request pending indefinitely
- `/methodology` renders the public data-boundary and metric notes without exposing evidence traces or source excerpts
- the public header shows a simple FPDS logo mark, a medium-weight `FPDS` brand title, Home, Deposit, Loan, and a compact locale menu; Methodology remains available by route but is no longer a top-level header or Home action
- the public footer uses a Revolut-inspired structure with a compact brand row, route, coverage, and data-boundary link groups, plus the same compact locale menu pattern used by the header
- `WBS 5.11` is now implemented with URL-based shared scope preservation across sibling navigation plus dashboard-to-grid drill-in links from ranking rows
- `WBS 5.12` is now implemented with EN/KO/JA locale switching, locale-preserving sibling navigation, locale-aware page metadata, and locale-aware labels or freshness copy while keeping source-derived product content in its original language
- `WBS 5.13` is now implemented with locale-aware methodology/freshness wording on the public surface, while `/products` now keeps catalog chrome minimal and leaves detailed data-boundary copy to `/methodology`
- public-owned date and freshness timestamp displays use fixed `yyyy-mm-dd` and `yyyy-mm-dd hh:mm` formatting instead of locale-specific long date strings
- the public app uses the same `radix-nova` style family as the admin app, with `@shadcnblocks/dashboard10`-installed chart/table primitives adapted through FPDS-owned domain components
