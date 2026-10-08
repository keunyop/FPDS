# FPDS Technical References

Start with the **[Admin development guide](../descent/FPDS_Admin_개발_가이드.md)**,
which also explains the task-specific AI skills. Read additional documents only
for the area being changed.

| Need | Reference |
|---|---|
| Country, language or feature work | [Development guide](../descent/FPDS_Admin_개발_가이드.md) |
| Runtime setup and commands | [Repository source map](../README.md#source-map) |
| Financial evidence and automatic acceptance | [Accuracy policy](03-design/collection-accuracy-policy.md), [field contract](03-design/financial-product-field-contract.md) |
| Authentication, access and private evidence | [Security contract](03-design/security-access-control-design.md) |
| UI, API, data or infrastructure details | [Design index](03-design/README.md) |
| CI and repository validation | [Harness](00-governance/harness-engineering-baseline.md), [CI baseline](00-governance/foundation-ci-cd-baseline.md) |
| Operations and environment transfer | [Operational handover](../descent/README.md) |
| Incident/change investigation | [Journal](00-governance/development-journal.md), [decisions](00-governance/decision-log.md), [risks](00-governance/raid-log.md) |

Dated collection, cutover and recovery reports remain in governance because they
record real operational outcomes. Use the journal to find the relevant report;
local implementation, deployment and publication are distinct results.

Completed MVP plans, initial requirements, stage gates, superseded drafts and
prototype/manual archives were removed in the post-MVP cleanup. Historical
citations use Git revision/path references. They are not mandatory reading for
new work. Current code, tests, source fixtures, migrations, financial/security
contracts and private evidence retention rules remain in effect.
