---
name: deploy
description: Pre-deployment checklist for pushing the ExactusPay website to Render.com. Run before every deploy to avoid broken static files, missing migrations, or misconfigured env vars.
disable-model-invocation: true
---

Run through this checklist before every Render deployment:

1. **Run migrations locally** to verify they apply cleanly:
   ```bash
   python manage.py migrate --run-syncdb
   ```

2. **Collect static files** (required — WhiteNoise serves from staticfiles/):
   ```bash
   python manage.py collectstatic --noinput
   ```
   Confirm it completes without errors.

3. **Check required env vars** are set in the Render dashboard:
   - `SECRET_KEY`
   - `DEBUG=0`
   - `RESEND_API_KEY`
   - `DEFAULT_FROM_EMAIL`
   - `DEMO_REQUEST_TO_EMAIL`
   - `EXTERNAL_PAYROLL_LOGIN_URL`
   - `BOOK_DEMO_EXTERNAL_URL`

4. **Run the test suite** to confirm nothing is broken:
   ```bash
   python manage.py test home accounts
   ```

5. **Commit and push** using conventional commit format (`feat:`, `fix:`, etc.).

Report any step that fails before proceeding.
