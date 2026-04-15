# Shared I18n

Use this area for shared locale resources, glossary seed data, and fallback policy scaffolds.

Current scaffold:
- `locale-config.json` defines the supported locales and fallback chains.
- `locales/` contains starter EN/KO/JA UI resource files.
- `glossary.seed.json` contains the first shared taxonomy and admin-term glossary entries.
- public and admin runtime helpers now consume the same EN/KO/JA baseline and preserve `locale` through route transitions.

Rules:
- `en` is the default resource locale.
- UI labels, navigation, helper text, and status copy live here.
- Source-derived content such as product names, evidence excerpts, and source conditions do not get duplicated into per-locale files.
- `ko` and `ja` can remain draft while runtime fallback resolves to `en`.

WBS follow-on:
- `2.6` i18n scaffold
- `5.12` trilingual UI rollout completed for the live public and admin shells
