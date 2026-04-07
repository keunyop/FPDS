# FPDS Object Storage Baseline

This directory holds the object storage and evidence bucket baseline for WBS `2.4`.

Current decisions:
- storage stays vendor-neutral but assumes an S3-compatible model
- storage is private by default
- browser surfaces never receive direct raw object access
- `dev` and `prod` are separated by bucket or top-level environment prefix
- object keys follow the approved evidence lineage shape from the design docs

Files:
- `object-layout.example.json`: placeholder-only storage layout and access contract

How to use this baseline:
- provision a private bucket or container for `dev`
- provision a separate private bucket or container for `prod`, or use a strictly separated top-level prefix if the provider forces one container
- map the real bucket names and credentials into the env keys from `.env.dev.example` and `.env.prod.example`

Notes:
- exact lifecycle rules, encryption settings, and retention days are still placeholders
- object storage provisioning itself is not performed from this repo
- follow-on implementation should consume this contract instead of hard-coding object paths
