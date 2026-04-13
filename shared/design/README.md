# Shared Design

This directory holds cross-surface design-system artifacts reused by public and admin UI implementation.

Current boundary:
- benchmark-linked design notes for public/admin UI work
- bridge token and CSS-variable exports for non-template consumers
- shared UI vocabulary that future frontend code should preserve across public and admin surfaces

Current baseline files:
- `fpds-design-tokens.json` as the current bridge token export
- `fpds-theme.css` as the current bridge CSS-variable export

Design rules:
- keep Stripe as the structural benchmark and `docs/03-design/fpds_design_system_stripe_benchmark.md` as the more specific design authority
- keep future frontend implementation template-first with Shadcnblocks rather than inventing a second bespoke primitive system
- keep public and admin surfaces on one shared style family with `public = balanced` and `admin = compact`
- treat `fpds-design-tokens.json` and `fpds-theme.css` as bridge/reference artifacts until the frontend fully standardizes on `components.json` plus app-level shadcn semantic variables
- note that `app/admin` has now crossed that boundary and uses `components.json` plus app-local `globals.css` as its active theme source of truth
- keep the active benchmark aligned to `docs/03-design/fpds_design_system_stripe_benchmark.md`
- keep the system `light-only` for now
- keep `public = balanced` and `admin = compact`
