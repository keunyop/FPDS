# Prototype App Surface

Use this area for the read-only internal result viewer required by the TD Savings prototype.

Why separate from `admin/`:
- prototype scope explicitly does not require full admin login or review queue operations
- the viewer only needs minimal read-only reviewability before WBS `4.x`

Current implementation:
- `index.html` provides the Stripe-benchmarked read-only viewer shell
- `viewer.js` renders run, candidate, payload, and evidence panels from a generated payload file
- `viewer-payload.js` is the default local payload loaded by the static page
- `viewer-payload.json` keeps the same exported payload in raw JSON form for inspection or evidence-pack reuse

Refresh the viewer payload from a live run:

```powershell
python -m worker.pipeline.fpds_result_viewer `
  --env-file .env.dev `
  --run-id run_20260410_3701
```

Open the prototype viewer:
- open [index.html](/d:/10%20Development/10%20개인프로젝트/70.%20Mybank/workspace/app/prototype/index.html) in a browser
- or serve `app/prototype/` from a lightweight static server if you prefer an `http://` URL

Current boundary:
- read-only run and candidate inspection
- evidence excerpt and anchor visibility
- no admin auth, write actions, queue mutation, or full trace viewer yet
