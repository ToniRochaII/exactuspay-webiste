# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Django 5.2 website for ExactusPay — a global payroll platform. Python 3.11, pip, SQLite (dev), Gunicorn + WhiteNoise (production on Render.com).

## Commands

```bash
# Dev
python manage.py runserver
python manage.py migrate
python manage.py test                        # all tests
python manage.py test home accounts          # specific apps
python manage.py collectstatic               # required before every Render deploy

# Dependencies
pip install -r requirements.txt
```

No CSS/JS build step — static files are plain CSS/JS in `static/`.

## Required env vars

Copy `.env.example` to `.env`. Keys:

- `SECRET_KEY` — required in production
- `DEBUG` — `1` for dev, `0` for prod
- `RESEND_API_KEY` — if absent, email falls back to console backend
- `DEFAULT_FROM_EMAIL`, `DEMO_REQUEST_TO_EMAIL`
- `EXTERNAL_PAYROLL_LOGIN_URL`, `BOOK_DEMO_EXTERNAL_URL`

## Email backend

Controlled by `ExactusPay/runtime_config.py` — not python-dotenv. The backend is selected dynamically:
- `RESEND_API_KEY` set + `DEBUG=0` → Resend API (real sends)
- `DEBUG=1` or missing key → console backend (prints to stdout)

Do not set `EMAIL_BACKEND` in `.env` unless overriding this logic intentionally.

## i18n

12 languages: `ar de en es fr id it pl pt ru sw th`. All URL routes use Django `i18n_patterns()` — every URL has a language prefix (e.g. `/en/`, `/ar/`). Translation files live in `locale/`. Country-specific page variations are handled by `home/country_catalog.py` and `home/country_localization*.py` — separate from standard Django i18n.

## Deployment (Render)

Always run before pushing:
1. `python manage.py migrate`
2. `python manage.py collectstatic --noinput`
3. Verify all required env vars are set in Render dashboard

WhiteNoise serves compressed static files — `collectstatic` must complete successfully or the deployed app will 404 on assets.

## Commit style

Conventional commits: `feat:`, `fix:`, `style:`, `refactor:`, `docs:`, `chore:`.
