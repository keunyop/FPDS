# Admin Signup Route Shell

Route: `/admin/signup`

Purpose:
- anonymous access-request entrypoint
- creates a pending signup request instead of an active account
- an existing `admin` must approve the request and assign a role before first login

Current scaffold:
- live implementation now exists in `app/admin/src/app/admin/signup/`
