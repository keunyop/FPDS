# Shared Design

This directory holds cross-surface design-system artifacts reused by public and admin UI implementation.

Current boundary:
- design-system tokens
- CSS variable exports
- component and surface vocabulary shared by future frontend code

Current baseline files:
- `fpds-design-tokens.json` for implementation-neutral tokens
- `fpds-theme.css` for CSS variable export

Design rules:
- keep tokens semantic first, not page-specific
- keep public and admin surfaces on one shared system with different density and layout usage
- route implementation should consume these artifacts instead of inventing one-off page styles
- keep the active benchmark aligned to `docs/03-design/fpds_design_system_stripe_benchmark.md`
- keep the system `light-only` for now
- keep `public = balanced` and `admin = compact`
