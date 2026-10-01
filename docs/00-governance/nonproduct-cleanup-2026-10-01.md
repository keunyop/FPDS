# Confirmed non-product cleanup

The Product Owner explicitly authorized deleting excluded records with no publication prospect. Five records were proven by fresh official pages to describe tools, enrollment, legal material or a category, rather than individual financial products. Missing evidence, disabled sources and validator failures were not used as proof of permanent unpublishability.

| Removed record | Official evidence |
|---|---|
| Account options made simple | Bank of America CD page links this label to an educational article on Better Money Habits. |
| Short-Term Savings Calculator | Bank of America Savings page identifies a savings-goal calculator. |
| Online Banking enrollment | Bank of America Checking page links to the online-banking enrollment flow. |
| Online Banking Service Agreement | Bank of America Advantage Banking page links this label to legal terms. |
| Guaranteed Investment Certificates (GICs) | CIBC category page lists distinct Flexible, Bonus Rate and other GIC products. |

## Applied data change

Deleted 5 canonical products, 10 associated product versions, 24 version evidence links, 11 product change events and 59 historical product projection rows in one transaction. Five historical review tasks were retained with their product references cleared. Original candidates, source evidence, registry entries and review decisions remain private; legitimate products sharing those sources remain eligible for future collection. No externally published items, customer feedback or engagement rows referenced these products.

All 429 surviving canonical rows were unchanged. The original 355-product manifest now comprises **7 active, 343 inactive and 5 deleted**. Public API/BFF return CA 7 / US 0; card catalogue and detail checks pass. Other historical aggregate summaries were not rewritten; they describe earlier snapshots.

## Verification and recovery

A transaction rollback rehearsal passed before execution. Execution checked exact identities, status/version, original-manifest membership, fresh source hashes, linked non-product destinations, dependent rows and unchanged survivor/registry/candidate state. Independent readback verified the final original-manifest counts and Public routes. No collection model calls or runtime changes; no deployment needed.

Private artifacts: `tmp/nonproduct-delete-evidence.json`, source captures, `tmp/nonproduct-delete-backup.json`, `tmp/nonproduct-delete-dryrun.json`, `tmp/nonproduct-delete-result.json`, and `tmp/nonproduct-delete-readback.json`. These preserve deleted records and operation evidence for rollback/audit. The legacy `audit_event` view discards writes under migration 0040; do not claim that an insert there persisted or change its retention behavior for this operation.

Remaining exclusions have not been proven permanently unpublishable. Retain them for evidence strengthening or correction of automatic validation errors.
